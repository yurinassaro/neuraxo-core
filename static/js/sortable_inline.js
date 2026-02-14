(function() {
    'use strict';

    function initSortable() {
        // Django admin uses id like "subtarefatemplate_set-group"
        var inlineGroup = document.getElementById('subtarefatemplate_set-group');
        if (!inlineGroup) {
            // Fallback: try any inline with subtarefa in the id
            var all = document.querySelectorAll('[id*="subtarefatemplate"]');
            for (var i = 0; i < all.length; i++) {
                if (all[i].querySelector('tbody')) {
                    inlineGroup = all[i];
                    break;
                }
            }
        }
        if (!inlineGroup) return;

        var tbody = inlineGroup.querySelector('tbody');
        if (!tbody) return;

        var rows = tbody.querySelectorAll('tr.form-row');
        rows.forEach(function(row) {
            if (row.classList.contains('empty-form')) return;
            if (row.querySelector('.drag-handle')) return;

            var firstTd = row.querySelector('td');
            if (!firstTd) return;

            var handle = document.createElement('td');
            handle.className = 'drag-handle';
            handle.style.cssText = 'cursor: grab; width: 30px; text-align: center; color: #666; font-size: 20px; vertical-align: middle; user-select: none;';
            handle.innerHTML = '&#9776;';
            handle.title = 'Arrastar para reordenar';
            row.insertBefore(handle, firstTd);

            row.setAttribute('draggable', 'true');
            row.style.transition = 'background-color 0.2s';
        });

        // Add header cell
        var thead = inlineGroup.querySelector('thead tr');
        if (thead && !thead.querySelector('.drag-header')) {
            var th = document.createElement('th');
            th.className = 'drag-header';
            th.style.width = '30px';
            thead.insertBefore(th, thead.firstChild);
        }

        var dragRow = null;

        tbody.addEventListener('dragstart', function(e) {
            dragRow = e.target.closest('tr.form-row');
            if (!dragRow) return;
            dragRow.style.opacity = '0.4';
            dragRow.style.backgroundColor = '#fffde7';
            e.dataTransfer.effectAllowed = 'move';
        });

        tbody.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            var target = e.target.closest('tr.form-row');
            if (!target || target === dragRow) return;

            var rect = target.getBoundingClientRect();
            var mid = rect.top + rect.height / 2;
            if (e.clientY < mid) {
                tbody.insertBefore(dragRow, target);
            } else {
                tbody.insertBefore(dragRow, target.nextSibling);
            }
        });

        tbody.addEventListener('dragend', function() {
            if (dragRow) {
                dragRow.style.opacity = '1';
                dragRow.style.backgroundColor = '';
                dragRow = null;
            }
            updateOrdem();
        });

        function updateOrdem() {
            var allRows = tbody.querySelectorAll('tr.form-row:not(.empty-form)');
            allRows.forEach(function(row, index) {
                var ordemInput = row.querySelector('input[name$="-ordem"]');
                if (ordemInput) {
                    ordemInput.value = index;
                }
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSortable);
    } else {
        initSortable();
    }

    // Re-init when Django adds a new inline row
    document.addEventListener('DOMContentLoaded', function() {
        var group = document.getElementById('subtarefatemplate_set-group');
        if (group) {
            var tbody = group.querySelector('tbody');
            if (tbody) {
                new MutationObserver(function() { initSortable(); })
                    .observe(tbody, { childList: true });
            }
        }
    });
})();
