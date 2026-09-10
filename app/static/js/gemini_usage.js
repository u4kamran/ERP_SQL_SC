const GEMINI_USAGE_API = '/api/v1/marketing/gemini-usage';

document.addEventListener('DOMContentLoaded', async () => {
    const profile = await Auth.requireAuth();
    if (!profile) return;
    if (!Auth.hasPermission('marketing.gemini_usage.view')) {
        Auth.showAlert('gemini-usage-alert', 'No permission to view Gemini usage.', 'warning');
        return;
    }
    if (!Auth.hasPermission('marketing.gemini_usage.manage')) {
        document.querySelectorAll('#budget-form input, #budget-form button').forEach((el) => {
            el.disabled = true;
        });
    }
    document.getElementById('btn-refresh').addEventListener('click', loadSummary);
    document.getElementById('budget-form').addEventListener('submit', saveBudget);
    await loadSummary();
});

function money(value) {
    const n = Number(value || 0);
    return `$${n.toFixed(n >= 1 ? 2 : 4)}`;
}

function num(value) {
    return Number(value || 0).toLocaleString();
}

async function loadSummary() {
    try {
        const data = await Api.get(`${GEMINI_USAGE_API}/summary`);
        document.getElementById('usage-note').textContent = data.note || '';
        document.getElementById('kpi-spent').textContent = money(data.spent_usd);
        document.getElementById('kpi-remaining').textContent =
            data.remaining_usd == null ? 'Set budget' : money(data.remaining_usd);
        document.getElementById('kpi-tokens').textContent = num(data.total_tokens);
        document.getElementById('kpi-token-split').textContent =
            `in ${num(data.prompt_tokens)} / out ${num(data.output_tokens)}`;
        document.getElementById('kpi-calls').textContent =
            `${num(data.calls_total)} / ${num(data.calls_failed)}`;
        document.getElementById('kpi-today').textContent =
            `Today: ${num(data.today_calls)} calls · ${num(data.today_tokens)} tokens · ${money(data.today_cost_usd)}`;

        document.getElementById('budget-usd').value =
            data.budget_usd ? Number(data.budget_usd).toFixed(2) : '';
        document.getElementById('budget-note').value = data.budget_note || '';
        document.getElementById('budget-meta').textContent = data.budget_updated_at
            ? `Budget updated: ${data.budget_updated_at}`
            : 'No budget saved yet.';

        const featureBody = document.getElementById('feature-body');
        const features = data.by_feature || [];
        featureBody.innerHTML = features.length
            ? features.map((row) => `
                <tr>
                    <td class="text-capitalize">${esc(row.feature)}</td>
                    <td class="text-end">${num(row.calls)}</td>
                    <td class="text-end">${num(row.total_tokens)}</td>
                    <td class="text-end">${money(row.estimated_cost_usd)}</td>
                </tr>
            `).join('')
            : '<tr><td colspan="4" class="text-muted">No usage yet.</td></tr>';

        const recentBody = document.getElementById('recent-body');
        const recent = data.recent || [];
        recentBody.innerHTML = recent.length
            ? recent.map((row) => `
                <tr>
                    <td class="small">${esc((row.created_at || '').replace('T', ' ').slice(0, 19))}</td>
                    <td class="text-capitalize">${esc(row.feature || '')}</td>
                    <td class="small">${esc(row.model || '')}</td>
                    <td class="text-end">${num(row.prompt_tokens)}</td>
                    <td class="text-end">${num(row.output_tokens)}</td>
                    <td class="text-end">${money(row.estimated_cost_usd)}</td>
                    <td>${row.ok
                        ? '<span class="badge text-bg-success">ok</span>'
                        : '<span class="badge text-bg-danger">fail</span>'}</td>
                </tr>
            `).join('')
            : '<tr><td colspan="7" class="text-muted">No calls recorded yet. Use voice or vision once.</td></tr>';
    } catch (error) {
        Auth.showAlert('gemini-usage-alert', error.message || 'Failed to load usage.', 'danger');
    }
}

async function saveBudget(event) {
    event.preventDefault();
    try {
        await Api.put(`${GEMINI_USAGE_API}/budget`, {
            budget_usd: Number(document.getElementById('budget-usd').value || 0),
            note: document.getElementById('budget-note').value.trim(),
        });
        Auth.showAlert('gemini-usage-alert', 'Budget saved.', 'success');
        await loadSummary();
    } catch (error) {
        Auth.showAlert('gemini-usage-alert', error.message || 'Save failed.', 'danger');
    }
}

function esc(value) {
    return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
