(function() {
    'use strict';

    function toggleRecorrenciaFields() {
        var recorrencia = document.getElementById('id_recorrencia');
        if (!recorrencia) return;

        var valor = recorrencia.value;

        // Encontrar as rows dos campos
        var diasSemanaRow = document.querySelector('.field-dias_semana_checkbox');
        var diaSemanaRow = document.querySelector('.field-dia_semana');
        var diaMesRow = document.querySelector('.field-dia_mes');

        // Esconder todos primeiro
        if (diasSemanaRow) diasSemanaRow.style.display = 'none';
        if (diaSemanaRow) diaSemanaRow.style.display = 'none';
        if (diaMesRow) diaMesRow.style.display = 'none';

        // Mostrar conforme recorrência selecionada
        switch(valor) {
            case 'diaria':
                // Diária: mostrar checkboxes de dias da semana
                if (diasSemanaRow) diasSemanaRow.style.display = '';
                break;
            case 'semanal':
                // Semanal: mostrar dropdown de dia da semana
                if (diaSemanaRow) diaSemanaRow.style.display = '';
                break;
            case 'mensal':
            case 'trimestral':
            case 'semestral':
            case 'anual':
                // Mensal+: mostrar dia do mês
                if (diaMesRow) diaMesRow.style.display = '';
                break;
            // quinzenal: não precisa de campo extra (dias 1 e 15)
        }
    }

    // Executar quando DOM carregar
    document.addEventListener('DOMContentLoaded', function() {
        var recorrencia = document.getElementById('id_recorrencia');
        if (recorrencia) {
            // Executar ao carregar
            toggleRecorrenciaFields();
            // Executar ao mudar
            recorrencia.addEventListener('change', toggleRecorrenciaFields);
        }
    });
})();
