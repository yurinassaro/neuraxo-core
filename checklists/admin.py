from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import path
from django.contrib import messages
from django import forms
from .models import (
    ChecklistTemplate, ChecklistItem, StatusItem, SubTarefa, SubTarefaTemplate,
    Demanda, SubTarefaDemanda, AnexoDemanda, ComentarioDemanda,
    StatusDemanda, PrioridadeDemanda, Projeto, StatusProjeto,
    ProjetoTemplate, EtapaTemplate, TipoEtapa, MapaMentalNo,
)
from core.models import Pessoa

DIAS_SEMANA_CHOICES = [
    ('0', 'Seg'), ('1', 'Ter'), ('2', 'Qua'), ('3', 'Qui'),
    ('4', 'Sex'), ('5', 'Sáb'), ('6', 'Dom'),
]


class DiasSemanaWidget(forms.CheckboxSelectMultiple):
    template_name = 'django/forms/widgets/checkbox_select.html'


class ChecklistTemplateForm(forms.ModelForm):
    dias_semana_checkbox = forms.MultipleChoiceField(
        choices=DIAS_SEMANA_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Dias da semana',
        help_text='Selecione os dias em que a rotina deve ser gerada',
    )

    class Meta:
        model = ChecklistTemplate
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.dias_semana_ativos:
            self.initial['dias_semana_checkbox'] = [
                d.strip() for d in self.instance.dias_semana_ativos.split(',') if d.strip()
            ]
        else:
            self.initial['dias_semana_checkbox'] = ['0', '1', '2', '3', '4']

    def clean(self):
        cleaned_data = super().clean()
        responsavel = cleaned_data.get('responsavel')
        cargo_responsavel = cleaned_data.get('cargo_responsavel')
        responsavel_todos = cleaned_data.get('responsavel_todos', False)

        if not responsavel and not cargo_responsavel and not responsavel_todos:
            raise forms.ValidationError(
                'Você deve definir um Responsável, um Cargo responsável, ou marcar "Todos". '
                'Não é possível salvar sem atribuição.'
            )
        return cleaned_data

    def save(self, commit=True):
        dias = self.cleaned_data.get('dias_semana_checkbox', [])
        self.instance.dias_semana_ativos = ','.join(sorted(dias))
        return super().save(commit=commit)


class SubTarefaTemplateInline(admin.TabularInline):
    model = SubTarefaTemplate
    extra = 1
    ordering = ['ordem', 'id']


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'empresa', 'ordem_execucao', 'recorrencia', 'responsavel_display', 'prioridade_badge', 'ativo', 'duplicar_link']
    list_filter = ['empresa', 'recorrencia', 'prioridade', 'ativo']
    search_fields = ['titulo', 'descricao', 'processo']
    raw_id_fields = ['responsavel']
    list_editable = ['ordem_execucao']
    ordering = ['ordem_execucao']
    form = ChecklistTemplateForm
    inlines = [SubTarefaTemplateInline]

    def duplicar_link(self, obj):
        return format_html(
            '<a href="duplicar/{}/" class="button" style="padding:2px 8px; font-size:11px;">Duplicar</a>',
            obj.pk
        )
    duplicar_link.short_description = 'Ações'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('duplicar/<int:template_id>/', self.admin_site.admin_view(self.duplicar_rotina_view), name='duplicar_rotina'),
        ]
        return custom_urls + urls

    def duplicar_rotina_view(self, request, template_id):
        from core.models import Empresa
        template = get_object_or_404(ChecklistTemplate, pk=template_id)
        empresas = Empresa.objects.all().order_by('nome')

        if request.method == 'POST':
            empresas_ids = request.POST.getlist('empresas')
            manter_responsavel = request.POST.get('manter_responsavel') == 'on'
            criar_itens = request.POST.get('criar_itens') == 'on'

            if empresas_ids:
                from django.utils import timezone
                from .services import deve_gerar_hoje, calcular_data_limite, obter_responsaveis

                hoje = timezone.localdate()
                count_templates = 0
                count_itens = 0

                for empresa_id in empresas_ids:
                    empresa = get_object_or_404(Empresa, pk=empresa_id)

                    # Determinar responsável
                    responsavel = None
                    cargo_responsavel = None
                    if manter_responsavel:
                        if template.responsavel:
                            # Tentar encontrar a mesma pessoa na empresa destino
                            responsavel = Pessoa.objects.filter(
                                empresas=empresa,
                                nome=template.responsavel.nome,
                                ativo=True
                            ).first()
                        if template.cargo_responsavel:
                            cargo_responsavel = template.cargo_responsavel

                    # Duplicar o template
                    novo_template = ChecklistTemplate.objects.create(
                        empresa=empresa,
                        titulo=template.titulo,
                        descricao=template.descricao,
                        processo=template.processo,
                        recorrencia=template.recorrencia,
                        dia_semana=template.dia_semana,
                        dia_mes=template.dia_mes,
                        dias_semana_ativos=template.dias_semana_ativos,
                        responsavel=responsavel,
                        responsavel_todos=template.responsavel_todos if not manter_responsavel else False,
                        cargo_responsavel=cargo_responsavel,
                        ordem_execucao=template.ordem_execucao,
                        tempo_estimado=template.tempo_estimado,
                        prioridade=template.prioridade,
                        ativo=template.ativo,
                        enviar_lembrete=template.enviar_lembrete,
                    )

                    # Duplicar subtarefas do template
                    for st in template.subtarefas_template.all():
                        SubTarefaTemplate.objects.create(
                            template=novo_template,
                            titulo=st.titulo,
                            ordem=st.ordem,
                        )
                    count_templates += 1

                    # Criar itens de checklist se solicitado
                    if criar_itens and deve_gerar_hoje(novo_template, hoje):
                        responsaveis = obter_responsaveis(novo_template)
                        data_limite = calcular_data_limite(novo_template, hoje)

                        for pessoa in responsaveis:
                            item = ChecklistItem.objects.create(
                                template=novo_template,
                                responsavel=pessoa,
                                data_referencia=hoje,
                                data_limite=data_limite,
                                descricao=novo_template.descricao,
                                processo=novo_template.processo,
                            )
                            # Copiar subtarefas
                            for st in novo_template.subtarefas_template.all():
                                SubTarefa.objects.create(
                                    checklist_item=item,
                                    titulo=st.titulo,
                                    ordem=st.ordem,
                                )
                            count_itens += 1

                msg = f'Rotina duplicada para {count_templates} empresa(s)!'
                if count_itens > 0:
                    msg += f' {count_itens} item(ns) de checklist criado(s).'
                messages.success(request, msg)
                return redirect('admin:checklists_checklisttemplate_changelist')

        return render(request, 'admin/checklists/duplicar_rotina.html', {
            'template': template,
            'empresas': empresas,
            'opts': self.model._meta,
        })

    fieldsets = (
        ('Informações', {
            'fields': ('empresa', 'titulo', 'descricao', 'processo')
        }),
        ('Recorrência', {
            'fields': ('recorrencia', 'dias_semana_checkbox', 'dia_semana', 'dia_mes')
        }),
        ('Atribuição', {
            'fields': ('responsavel', 'responsavel_todos', 'cargo_responsavel'),
            'description': 'Selecione UM responsável específico, OU marque "Todos", OU selecione um cargo.'
        }),
        ('Configurações', {
            'fields': ('ordem_execucao', 'prioridade', 'tempo_estimado', 'enviar_lembrete', 'ativo')
        }),
    )

    class Media:
        css = {'all': ('admin/css/custom_admin.css',)}
        js = ('admin/js/recorrencia_fields.js',)

    def responsavel_display(self, obj):
        if obj.responsavel:
            return obj.responsavel.nome
        if obj.responsavel_todos:
            return "TODOS os funcionários"
        if obj.cargo_responsavel:
            return f"Cargo: {obj.cargo_responsavel.nome}"
        return "-"
    responsavel_display.short_description = 'Responsável'

    def prioridade_badge(self, obj):
        cores = {1: '#28a745', 2: '#ffc107', 3: '#dc3545'}
        nomes = {1: 'Baixa', 2: 'Média', 3: 'Alta'}
        return format_html(
            '<span style="background:{}; padding:3px 8px; border-radius:3px; color:white;">{}</span>',
            cores[obj.prioridade], nomes[obj.prioridade]
        )
    prioridade_badge.short_description = 'Prioridade'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['empresa'].required = True
        return form

    def save_related(self, request, form, formsets, change):
        """Após salvar as subtarefas do template, gera itens do dia e sincroniza subtarefas"""
        super().save_related(request, form, formsets, change)
        obj = form.instance

        from django.utils import timezone
        from .services import deve_gerar_hoje, obter_responsaveis, calcular_data_limite

        hoje = timezone.localdate()

        # 1. Se template ativo e deve gerar hoje, cria itens que não existem
        if obj.ativo and obj.empresa and deve_gerar_hoje(obj, hoje):
            responsaveis = obter_responsaveis(obj)
            data_limite = calcular_data_limite(obj, hoje)
            for pessoa in responsaveis:
                item, created = ChecklistItem.objects.get_or_create(
                    template=obj,
                    responsavel=pessoa,
                    data_referencia=hoje,
                    defaults={
                        'data_limite': data_limite,
                        'descricao': obj.descricao,
                        'processo': obj.processo,
                    }
                )
                if created:
                    # Copia subtarefas do template para o novo item
                    for st in obj.subtarefas_template.all():
                        SubTarefa.objects.create(
                            checklist_item=item,
                            titulo=st.titulo,
                            ordem=st.ordem,
                        )

        # 2. Sincroniza subtarefas com ChecklistItems existentes (pendentes/em andamento)
        items = ChecklistItem.objects.filter(
            template=obj,
            status__in=[StatusItem.PENDENTE, StatusItem.EM_ANDAMENTO],
            data_referencia__gte=hoje
        )
        for item in items:
            subtarefas_existentes = set(item.subtarefas.values_list('titulo', flat=True))
            for st in obj.subtarefas_template.all():
                if st.titulo not in subtarefas_existentes:
                    SubTarefa.objects.create(
                        checklist_item=item,
                        titulo=st.titulo,
                        ordem=st.ordem,
                    )


class SubTarefaInline(admin.TabularInline):
    model = SubTarefa
    extra = 0


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ['template', 'empresa_display', 'responsavel', 'data_referencia', 'ordem', 'status_badge', 'data_limite', 'concluido_em']
    list_filter = ['status', 'data_referencia', 'template__empresa', 'responsavel']

    def empresa_display(self, obj):
        if obj.template and obj.template.empresa:
            return obj.template.empresa.nome
        return '-'
    empresa_display.short_description = 'Empresa'
    empresa_display.admin_order_field = 'template__empresa__nome'

    search_fields = ['template__titulo', 'responsavel__nome', 'observacoes']
    date_hierarchy = 'data_referencia'
    raw_id_fields = ['template', 'responsavel']
    readonly_fields = ['criado_em', 'lembrete_enviado', 'cobranca_enviada']
    list_editable = ['ordem']
    inlines = [SubTarefaInline]

    class Media:
        css = {'all': ('admin/css/custom_admin.css',)}

    fieldsets = (
        ('Tarefa', {
            'fields': ('template', 'responsavel', 'ordem')
        }),
        ('Detalhes', {
            'fields': ('descricao', 'processo'),
            'description': 'Se vazio, usa os valores do template (Rotina Diária)'
        }),
        ('Período', {
            'fields': ('data_referencia', 'data_limite')
        }),
        ('Status', {
            'fields': ('status', 'concluido_em', 'observacoes', 'anotacoes')
        }),
        ('Dependência', {
            'fields': ('dependente_de', 'motivo_dependencia'),
            'classes': ('collapse',)
        }),
        ('Timer', {
            'fields': ('iniciado_em', 'timer_acumulado'),
            'classes': ('collapse',)
        }),
        ('Notificações', {
            'fields': ('lembrete_enviado', 'cobranca_enviada'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        cores = {
            StatusItem.PENDENTE: '#6c757d',
            StatusItem.EM_ANDAMENTO: '#007bff',
            StatusItem.DEPENDENTE: '#f97316',
            StatusItem.CONCLUIDO: '#28a745',
            StatusItem.ATRASADO: '#dc3545',
            StatusItem.CANCELADO: '#343a40',
        }
        return format_html(
            '<span style="background:{}; padding:3px 8px; border-radius:3px; color:white;">{}</span>',
            cores.get(obj.status, '#6c757d'), obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    actions = ['marcar_concluido', 'marcar_pendente', 'sincronizar_subtarefas']

    @admin.action(description='Marcar como concluído')
    def marcar_concluido(self, request, queryset):
        for item in queryset:
            item.marcar_concluido()
        self.message_user(request, f'{queryset.count()} item(s) marcado(s) como concluído.')

    @admin.action(description='Sincronizar subtarefas do template')
    def sincronizar_subtarefas(self, request, queryset):
        total_criadas = 0
        for item in queryset:
            subtarefas_existentes = set(item.subtarefas.values_list('titulo', flat=True))
            for st in item.template.subtarefas_template.all():
                if st.titulo not in subtarefas_existentes:
                    SubTarefa.objects.create(
                        checklist_item=item,
                        titulo=st.titulo,
                        ordem=st.ordem,
                    )
                    total_criadas += 1
        self.message_user(request, f'{total_criadas} subtarefa(s) sincronizada(s).')

    @admin.action(description='Marcar como pendente')
    def marcar_pendente(self, request, queryset):
        queryset.update(status=StatusItem.PENDENTE, concluido_em=None)
        self.message_user(request, f'{queryset.count()} item(s) marcado(s) como pendente.')


# ============================================
# DEMANDAS
# ============================================

class SubTarefaDemandaInline(admin.TabularInline):
    model = SubTarefaDemanda
    extra = 0


class AnexoDemandaInline(admin.TabularInline):
    model = AnexoDemanda
    extra = 0
    readonly_fields = ['tamanho', 'criado_em']


class ComentarioDemandaInline(admin.TabularInline):
    model = ComentarioDemanda
    extra = 0
    readonly_fields = ['criado_em']


@admin.register(Demanda)
class DemandaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'empresa_badge', 'tipo_etapa_badge', 'responsavel', 'solicitante', 'prazo', 'prioridade_badge', 'status_badge']
    list_filter = ['status', 'prioridade', 'tipo_etapa', 'empresa', 'responsavel', 'solicitante']
    search_fields = ['titulo', 'descricao', 'responsavel__nome', 'solicitante__nome']
    date_hierarchy = 'prazo'
    raw_id_fields = ['responsavel', 'solicitante', 'dependente_de']
    inlines = [SubTarefaDemandaInline, AnexoDemandaInline, ComentarioDemandaInline]

    fieldsets = (
        ('Demanda', {
            'fields': ('empresa', 'projeto', 'titulo', 'descricao', 'instrucoes')
        }),
        ('Atribuição', {
            'fields': ('solicitante', 'responsavel')
        }),
        ('Prazo e Prioridade', {
            'fields': ('prazo', 'prioridade', 'etapa_ordem', 'tipo_etapa')
        }),
        ('Status', {
            'fields': ('status', 'concluido_em', 'anotacoes')
        }),
        ('Dependência', {
            'fields': ('dependente_de', 'motivo_dependencia'),
            'classes': ('collapse',)
        }),
        ('Timer', {
            'fields': ('iniciado_em', 'timer_acumulado'),
            'classes': ('collapse',)
        }),
    )

    def tipo_etapa_badge(self, obj):
        cores = {
            TipoEtapa.DESENVOLVIMENTO: '#3b82f6',
            TipoEtapa.MELHORIA: '#10b981',
        }
        return format_html(
            '<span style="background:{}; padding:2px 6px; border-radius:3px; color:white; font-size:11px;">{}</span>',
            cores.get(obj.tipo_etapa, '#6c757d'), obj.get_tipo_etapa_display()
        )
    tipo_etapa_badge.short_description = 'Tipo'

    def empresa_badge(self, obj):
        return format_html(
            '<span style="background:{}; padding:2px 8px; border-radius:3px; color:white;">{}</span>',
            obj.empresa.cor, obj.empresa.nome
        )
    empresa_badge.short_description = 'Empresa'

    def prioridade_badge(self, obj):
        cores = {
            PrioridadeDemanda.BAIXA: '#28a745',
            PrioridadeDemanda.MEDIA: '#ffc107',
            PrioridadeDemanda.ALTA: '#fd7e14',
            PrioridadeDemanda.URGENTE: '#dc3545',
        }
        return format_html(
            '<span style="background:{}; padding:3px 8px; border-radius:3px; color:white;">{}</span>',
            cores.get(obj.prioridade, '#6c757d'), obj.get_prioridade_display()
        )
    prioridade_badge.short_description = 'Prioridade'

    def status_badge(self, obj):
        cores = {
            StatusDemanda.PENDENTE: '#6c757d',
            StatusDemanda.EM_ANDAMENTO: '#007bff',
            StatusDemanda.DEPENDENTE: '#f97316',
            StatusDemanda.CONCLUIDO: '#28a745',
            StatusDemanda.CANCELADO: '#343a40',
        }
        return format_html(
            '<span style="background:{}; padding:3px 8px; border-radius:3px; color:white;">{}</span>',
            cores.get(obj.status, '#6c757d'), obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    actions = ['marcar_concluido', 'reabrir_demanda']

    @admin.action(description='Marcar como concluído')
    def marcar_concluido(self, request, queryset):
        for demanda in queryset:
            demanda.marcar_concluido()
        self.message_user(request, f'{queryset.count()} demanda(s) marcada(s) como concluída.')

    @admin.action(description='Reabrir demanda')
    def reabrir_demanda(self, request, queryset):
        for demanda in queryset:
            demanda.reabrir()
        self.message_user(request, f'{queryset.count()} demanda(s) reaberta(s).')


# ============================================
# TEMPLATES DE PROJETO
# ============================================

class EtapaTemplateInline(admin.TabularInline):
    model = EtapaTemplate
    extra = 1
    ordering = ['ordem', 'id']
    fields = ['ordem', 'titulo', 'descricao', 'tempo_estimado']


@admin.register(ProjetoTemplate)
class ProjetoTemplateAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'total_etapas', 'cor_display', 'ativo', 'criado_em']
    list_filter = ['ativo']
    search_fields = ['titulo', 'descricao']
    inlines = [EtapaTemplateInline]

    def total_etapas(self, obj):
        return obj.get_total_etapas()
    total_etapas.short_description = 'Etapas'

    def cor_display(self, obj):
        return format_html(
            '<span style="background-color:{}; padding: 2px 10px; border-radius: 3px;">&nbsp;</span>',
            obj.cor
        )
    cor_display.short_description = 'Cor'


# ============================================
# PROJETOS
# ============================================

class MapaMentalNoInline(admin.TabularInline):
    model = MapaMentalNo
    extra = 0
    fields = ['tipo', 'titulo', 'descricao', 'cor', 'conectado_a_etapa']
    raw_id_fields = ['conectado_a_etapa']


@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'empresa', 'cliente_display', 'responsavel', 'status', 'prazo', 'progresso_display', 'criado_em', 'duplicar_link']
    list_filter = ['status', 'empresa', 'cliente', 'responsavel']
    search_fields = ['titulo', 'descricao', 'cliente__nome']
    raw_id_fields = ['responsavel', 'cliente']
    filter_horizontal = ['participantes']
    inlines = [MapaMentalNoInline]

    def cliente_display(self, obj):
        if obj.cliente:
            return obj.cliente.nome
        return '-'
    cliente_display.short_description = 'Cliente'

    def progresso_display(self, obj):
        p = obj.get_progresso()
        cor = '#28a745' if p >= 80 else '#ffc107' if p >= 50 else '#dc3545'
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}%</span> ({}/{})',
            cor, p, obj.etapas_concluidas, obj.total_etapas
        )
    progresso_display.short_description = 'Progresso'

    def duplicar_link(self, obj):
        return format_html(
            '<a href="duplicar/{}/" class="button" style="padding:2px 8px; font-size:11px;">Duplicar</a>',
            obj.pk
        )
    duplicar_link.short_description = 'Ações'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('duplicar/<int:projeto_id>/', self.admin_site.admin_view(self.duplicar_projeto_view), name='duplicar_projeto'),
        ]
        return custom_urls + urls

    def duplicar_projeto_view(self, request, projeto_id):
        from core.models import Empresa
        from datetime import timedelta
        from django.utils import timezone

        projeto = get_object_or_404(Projeto, pk=projeto_id)
        empresas = Empresa.objects.all().order_by('nome')

        if request.method == 'POST':
            empresas_ids = request.POST.getlist('empresas')
            prazo_projeto_str = request.POST.get('prazo_projeto')
            dias_por_etapa = int(request.POST.get('dias_por_etapa', 7))

            if empresas_ids:
                hoje = timezone.localdate()
                count_projetos = 0

                for empresa_id in empresas_ids:
                    empresa = get_object_or_404(Empresa, pk=empresa_id)

                    # Calcular prazo do projeto
                    if prazo_projeto_str:
                        from datetime import datetime
                        prazo_projeto = datetime.strptime(prazo_projeto_str, '%Y-%m-%d').date()
                    else:
                        # Calcular baseado no número de etapas
                        num_etapas = projeto.demandas.count()
                        prazo_projeto = hoje + timedelta(days=dias_por_etapa * max(num_etapas, 1))

                    # Duplicar o projeto
                    novo_projeto = Projeto.objects.create(
                        empresa=empresa,
                        titulo=projeto.titulo,
                        descricao=projeto.descricao,
                        responsavel=None,  # Será definido depois
                        prazo=prazo_projeto,
                        status=StatusProjeto.PLANEJAMENTO,
                        cor=projeto.cor,
                    )

                    # Duplicar as demandas (etapas)
                    for i, demanda in enumerate(projeto.demandas.order_by('etapa_ordem', 'id')):
                        prazo_etapa = timezone.make_aware(
                            timezone.datetime.combine(
                                hoje + timedelta(days=dias_por_etapa * (i + 1)),
                                timezone.datetime.max.time()
                            )
                        )

                        nova_demanda = Demanda.objects.create(
                            empresa=empresa,
                            projeto=novo_projeto,
                            etapa_ordem=i + 1,
                            solicitante=None,
                            responsavel=None,
                            titulo=demanda.titulo,
                            descricao=demanda.descricao,
                            instrucoes=demanda.instrucoes,
                            prazo=prazo_etapa,
                            prioridade=demanda.prioridade,
                            tempo_estimado=demanda.tempo_estimado,
                            status=StatusDemanda.PENDENTE,
                        )

                        # Duplicar subtarefas da demanda
                        for st in demanda.subtarefas_demanda.all():
                            SubTarefaDemanda.objects.create(
                                demanda=nova_demanda,
                                titulo=st.titulo,
                                ordem=st.ordem,
                                concluida=False,
                            )

                    count_projetos += 1

                messages.success(request, f'Projeto duplicado para {count_projetos} empresa(s)!')
                return redirect('admin:checklists_projeto_changelist')

        return render(request, 'admin/checklists/duplicar_projeto.html', {
            'projeto': projeto,
            'empresas': empresas,
            'opts': self.model._meta,
        })
