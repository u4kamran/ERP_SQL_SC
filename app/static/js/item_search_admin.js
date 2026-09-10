const ITEM_SEARCH_ADMIN_API = '/api/v1/marketing/item-search';

document.addEventListener('DOMContentLoaded', async () => {
    const profile = await Auth.requireAuth();
    if (!profile) return;
    if (!Auth.hasPermission('marketing.item_search.view')) {
        Auth.showAlert('item-search-alert', 'No permission to view item search.', 'warning');
        return;
    }
    if (!Auth.hasPermission('marketing.item_search.manage')) {
        document.querySelectorAll('#settings-form input, #settings-form button, #alias-form input, #alias-form button').forEach((el) => {
            el.disabled = true;
        });
    }
    document.getElementById('btn-refresh').addEventListener('click', loadDashboard);
    document.getElementById('settings-form').addEventListener('submit', saveSettings);
    document.getElementById('alias-form').addEventListener('submit', saveAlias);
    await loadDashboard();
});

async function loadDashboard() {
    try {
        const data = await Api.get(`${ITEM_SEARCH_ADMIN_API}/dashboard`);
        const s = data.settings || {};
        document.getElementById('min_chars').value = s.min_chars ?? 2;
        document.getElementById('max_results').value = s.max_results ?? 10;
        document.getElementById('debounce_ms').value = s.debounce_ms ?? 250;
        document.getElementById('fuzzy_enabled').checked = !!s.fuzzy_enabled;
        document.getElementById('alias_enabled').checked = !!s.alias_enabled;
        document.getElementById('barcode_enabled').checked = !!s.barcode_enabled;
        renderAliases(data.aliases || []);
        const body = document.getElementById('no-result-body');
        const rows = data.no_results || [];
        body.innerHTML = rows.length
            ? rows.map((row) => `<tr><td>${esc(row.search_term)}</td><td class="text-end">${Number(row.searches || 0)}</td></tr>`).join('')
            : '<tr><td colspan="2" class="text-muted">No empty searches yet.</td></tr>';
    } catch (error) {
        Auth.showAlert('item-search-alert', error.message || 'Failed to load.', 'danger');
    }
}

function renderAliases(rows) {
    const body = document.getElementById('alias-body');
    body.innerHTML = rows.length
        ? rows.map((row) => `
            <tr>
                <td>${esc(row.alias_text)}</td>
                <td>${esc(row.expand_text)}</td>
                <td class="text-end">
                    <button class="btn btn-outline-danger btn-sm" type="button" data-del="${row.id}">×</button>
                </td>
            </tr>
        `).join('')
        : '<tr><td colspan="3" class="text-muted">No aliases.</td></tr>';
    body.querySelectorAll('[data-del]').forEach((btn) => {
        btn.addEventListener('click', async () => {
            try {
                const data = await Api.delete(`${ITEM_SEARCH_ADMIN_API}/aliases/${btn.getAttribute('data-del')}`);
                renderAliases(data.aliases || []);
            } catch (error) {
                Auth.showAlert('item-search-alert', error.message || 'Delete failed.', 'danger');
            }
        });
    });
}

async function saveSettings(event) {
    event.preventDefault();
    try {
        await Api.put(`${ITEM_SEARCH_ADMIN_API}/settings`, {
            min_chars: Number(document.getElementById('min_chars').value),
            max_results: Number(document.getElementById('max_results').value),
            debounce_ms: Number(document.getElementById('debounce_ms').value),
            fuzzy_enabled: document.getElementById('fuzzy_enabled').checked,
            alias_enabled: document.getElementById('alias_enabled').checked,
            barcode_enabled: document.getElementById('barcode_enabled').checked,
        });
        Auth.showAlert('item-search-alert', 'Search settings saved.', 'success');
        await loadDashboard();
    } catch (error) {
        Auth.showAlert('item-search-alert', error.message || 'Save failed.', 'danger');
    }
}

async function saveAlias(event) {
    event.preventDefault();
    try {
        const data = await Api.post(`${ITEM_SEARCH_ADMIN_API}/aliases`, {
            alias_text: document.getElementById('alias_text').value.trim(),
            expand_text: document.getElementById('expand_text').value.trim(),
        });
        document.getElementById('alias_text').value = '';
        document.getElementById('expand_text').value = '';
        renderAliases(data.aliases || []);
        Auth.showAlert('item-search-alert', 'Alias saved.', 'success');
    } catch (error) {
        Auth.showAlert('item-search-alert', error.message || 'Alias save failed.', 'danger');
    }
}

function esc(value) {
    return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
