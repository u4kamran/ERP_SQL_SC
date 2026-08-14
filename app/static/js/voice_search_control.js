const VOICE_CONTROL_API = '/api/v1/marketing/voice-control';

document.addEventListener('DOMContentLoaded', async () => {
    const profile = await Auth.requireAuth();
    if (!profile) return;
    if (!Auth.hasPermission('marketing.voice_control.view')) {
        Auth.showAlert('voice-control-alert', 'No permission to view voice control.', 'warning');
        return;
    }
    if (!Auth.hasPermission('marketing.voice_control.manage')) {
        document.querySelectorAll('#settings-form input, #settings-form button').forEach((el) => {
            el.disabled = true;
        });
    }
    document.getElementById('btn-refresh').addEventListener('click', () => loadDashboard());
    document.getElementById('settings-form').addEventListener('submit', saveSettings);
    document.getElementById('filter-form').addEventListener('submit', (event) => {
        event.preventDefault();
        loadDashboard();
    });
    document.getElementById('btn-clear-filter').addEventListener('click', () => {
        document.getElementById('filter-mobile').value = '';
        loadDashboard();
    });
    await loadDashboard();
});

function money(value) {
    const n = Number(value || 0);
    return `$${n.toFixed(n >= 1 ? 2 : 4)}`;
}

function num(value) {
    return Number(value || 0).toLocaleString();
}

function statusBadge(status) {
    const s = String(status || '');
    if (s === 'ok') return '<span class="badge text-bg-success">ok</span>';
    if (s === 'blocked') return '<span class="badge text-bg-warning">blocked</span>';
    return '<span class="badge text-bg-danger">failed</span>';
}

async function loadDashboard() {
    try {
        const mobile = document.getElementById('filter-mobile').value.trim();
        const qs = new URLSearchParams({ limit: '150' });
        if (mobile) qs.set('mobile', mobile);
        const data = await Api.get(`${VOICE_CONTROL_API}/dashboard?${qs}`);
        const today = data.today || {};
        document.getElementById('kpi-ok').textContent = num(today.ok);
        document.getElementById('kpi-blocked').textContent = num(today.blocked);
        document.getElementById('kpi-failed').textContent = num(today.failed);
        const budget = today.budget_usd > 0 ? money(today.budget_usd) : '—';
        document.getElementById('kpi-budget').textContent =
            `${money(today.spent_usd)} / ${budget}`;
        document.getElementById('kpi-tokens').textContent =
            `${num(today.tokens)} tokens` +
            (today.remaining_usd != null ? ` · left ${money(today.remaining_usd)}` : '');

        const s = data.settings || {};
        document.getElementById('cloud_voice_enabled').checked = !!s.cloud_voice_enabled;
        document.getElementById('guest_voice_enabled').checked = !!s.guest_voice_enabled;
        document.getElementById('whatsapp_voice_enabled').checked = !!s.whatsapp_voice_enabled;
        document.getElementById('require_mobile').checked = !!s.require_mobile;
        document.getElementById('daily_limit_per_mobile').value = s.daily_limit_per_mobile ?? 10;
        document.getElementById('minute_limit_per_ip').value = s.minute_limit_per_ip ?? 5;
        document.getElementById('daily_budget_usd').value =
            s.daily_budget_usd != null ? Number(s.daily_budget_usd).toFixed(2) : '2.00';
        document.getElementById('max_clip_seconds').value = s.max_clip_seconds ?? 15;
        document.getElementById('notes').value = s.notes || '';

        const topBody = document.getElementById('top-mobile-body');
        const tops = data.top_mobiles || [];
        topBody.innerHTML = tops.length
            ? tops.map((row) => `
                <tr>
                    <td><button type="button" class="btn btn-link btn-sm p-0 mobile-filter-link">${esc(row.mobile)}</button></td>
                    <td class="text-end">${num(row.ok)}</td>
                    <td class="text-end">${num(row.blocked)}</td>
                    <td class="text-end">${num(row.failed)}</td>
                    <td class="text-end">${money(row.cost_usd)}</td>
                    <td class="small">${esc(row.last_text || '—')}</td>
                </tr>
            `).join('')
            : '<tr><td colspan="6" class="text-muted">No voice activity today.</td></tr>';

        topBody.querySelectorAll('.mobile-filter-link').forEach((btn) => {
            btn.addEventListener('click', () => {
                document.getElementById('filter-mobile').value = btn.textContent.trim();
                loadDashboard();
            });
        });

        const auditBody = document.getElementById('audit-body');
        const recent = data.recent || [];
        auditBody.innerHTML = recent.length
            ? recent.map((row) => `
                <tr>
                    <td class="small">${esc((row.created_at || '').replace('T', ' ').slice(0, 19))}</td>
                    <td class="text-capitalize">${esc(row.channel || '')}</td>
                    <td>${esc(row.mobile || '—')}</td>
                    <td class="small">${esc(row.search_text || '—')}</td>
                    <td>${statusBadge(row.status)}</td>
                    <td class="small">${esc(row.ip || '—')}</td>
                    <td class="text-end">${money(row.estimated_cost_usd)}</td>
                    <td class="small text-muted">${esc(row.block_reason || row.detail || '')}</td>
                </tr>
            `).join('')
            : '<tr><td colspan="8" class="text-muted">No events yet.</td></tr>';
    } catch (error) {
        Auth.showAlert('voice-control-alert', error.message || 'Failed to load.', 'danger');
    }
}

async function saveSettings(event) {
    event.preventDefault();
    try {
        await Api.put(`${VOICE_CONTROL_API}/settings`, {
            cloud_voice_enabled: document.getElementById('cloud_voice_enabled').checked,
            guest_voice_enabled: document.getElementById('guest_voice_enabled').checked,
            whatsapp_voice_enabled: document.getElementById('whatsapp_voice_enabled').checked,
            require_mobile: document.getElementById('require_mobile').checked,
            daily_limit_per_mobile: Number(document.getElementById('daily_limit_per_mobile').value || 0),
            minute_limit_per_ip: Number(document.getElementById('minute_limit_per_ip').value || 0),
            daily_budget_usd: Number(document.getElementById('daily_budget_usd').value || 0),
            max_clip_seconds: Number(document.getElementById('max_clip_seconds').value || 15),
            notes: document.getElementById('notes').value.trim(),
        });
        Auth.showAlert('voice-control-alert', 'Settings saved.', 'success');
        await loadDashboard();
    } catch (error) {
        Auth.showAlert('voice-control-alert', error.message || 'Save failed.', 'danger');
    }
}

function esc(value) {
    return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
