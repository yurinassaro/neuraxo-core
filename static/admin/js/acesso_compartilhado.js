(function() {
    'use strict';

    function carregarEmpresas() {
        var tenantSelect = document.getElementById('id_tenant_destino');
        if (!tenantSelect) return;

        var tenantId = tenantSelect.value;
        if (!tenantId) return;

        fetch('/api/tenant/' + tenantId + '/empresas/')
            .then(function(response) { return response.json(); })
            .then(function(data) {
                var container = document.querySelector('.field-empresas_escolhidas .readonly, .field-empresas_escolhidas ul');
                if (!container) {
                    // Procurar o fieldset de empresas_escolhidas
                    var labels = document.querySelectorAll('label');
                    for (var i = 0; i < labels.length; i++) {
                        if (labels[i].textContent.trim().indexOf('Empresas Permitidas') !== -1) {
                            container = labels[i].parentElement;
                            break;
                        }
                    }
                }

                // Buscar checkboxes existentes
                var checkboxes = document.querySelectorAll('input[name="empresas_escolhidas"]');
                var checkedValues = [];
                checkboxes.forEach(function(cb) {
                    if (cb.checked) checkedValues.push(cb.value);
                });

                // Encontrar o UL pai
                var ul = document.querySelector('#id_empresas_escolhidas');
                if (!ul) {
                    // Procurar por qualquer ul que contém os checkboxes
                    if (checkboxes.length > 0) {
                        ul = checkboxes[0].closest('ul');
                    }
                }

                if (ul) {
                    ul.innerHTML = '';
                    data.empresas.forEach(function(empresa) {
                        var li = document.createElement('li');
                        var label = document.createElement('label');
                        var input = document.createElement('input');
                        input.type = 'checkbox';
                        input.name = 'empresas_escolhidas';
                        input.value = empresa.id;
                        if (checkedValues.indexOf(String(empresa.id)) !== -1) {
                            input.checked = true;
                        }
                        label.appendChild(input);
                        label.appendChild(document.createTextNode(' ' + empresa.nome));
                        li.appendChild(label);
                        ul.appendChild(li);
                    });

                    if (data.empresas.length === 0) {
                        var li = document.createElement('li');
                        li.textContent = 'Nenhuma empresa encontrada neste tenant.';
                        li.style.color = '#999';
                        ul.appendChild(li);
                    }
                }
            })
            .catch(function(err) {
                console.error('Erro ao carregar empresas:', err);
            });
    }

    document.addEventListener('DOMContentLoaded', function() {
        var tenantSelect = document.getElementById('id_tenant_destino');
        if (tenantSelect) {
            tenantSelect.addEventListener('change', carregarEmpresas);
        }
    });
})();
