"""
Helpers de autorização multi-tenant.

O isolamento do NeuraxoCheck é por empresa (FK/M2M `empresa`). Carregar um objeto
por `id` direto do banco, sem checar que ele pertence a uma empresa do usuário, é um
IDOR: um gestor da empresa A consegue acessar dados da empresa B só trocando o id na
URL. Estas funções centralizam a checagem para não ficar copiada (e errada) em cada
view.

Use sempre `pessoa.is_gestor_empresa(empresa)` / vínculo por empresa em vez do
`pessoa.is_gestor`/`eh_gestor` global (legado) para decidir acesso a um registro.
"""
from django.http import Http404
from django.shortcuts import get_object_or_404


def get_pessoa_da_minha_equipe(pessoa_id, pessoa_logada):
    """
    Carrega uma Pessoa por id SÓ se ela compartilhar pelo menos uma empresa com
    `pessoa_logada`. Caso contrário levanta Http404 (não revela existência nem dados).

    Use quando uma view de gestor visualiza/edita os dados de outra pessoa
    (aproveitamento, membros da equipe, dependências). Reusa o vínculo M2M
    `pessoa.empresas` — a mesma fonte de verdade de `get_empresas_filtradas`.
    """
    from core.models import Pessoa

    empresas_ids = pessoa_logada.empresas.filter(ativo=True).values_list('id', flat=True)
    return get_object_or_404(
        Pessoa.objects.filter(empresas__id__in=empresas_ids).distinct(),
        id=pessoa_id,
        ativo=True,
    )


def get_objeto_da_empresa(model, pk, empresas, campo_empresa='empresa'):
    """
    Carrega um objeto por pk SÓ se sua empresa estiver em `empresas`
    (tipicamente o retorno de `get_empresas_filtradas(pessoa, request)`).
    Senão, Http404.

    `campo_empresa` permite escopar por relação: ex. 'template__empresa',
    'projeto__empresa', 'cliente__empresa'.
    """
    return get_object_or_404(
        model.objects.filter(**{f'{campo_empresa}__in': empresas}),
        pk=pk,
    )
