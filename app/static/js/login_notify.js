const LOGIN_NOTIFY_API = '/api/v1/auth/login-notify';

document.addEventListener('DOMContentLoaded', async () => {
    const profile = await Auth.requireAuth();
    if (!profile) return;
    if (!Auth.hasPermission('auth.login_notify.view')) {
        Auth.showAlert('login-notify-alert', 'No permission to view login alerts.', 'warning');
        return;
    }
    if (!Auth.hasPermission('auth.login_notify.manage')) {
        document.querySelectorAll('#settings-form input, #settings-form button').forEach((el) => {
            el.disabled = true;
        });
    }
    document.getElementById('btn-refresh').addEventListener('click', loadDashboard);
    document.getElementById('settings-form').addEventListener('submit', saveSettings);
    document.getElementById('btn-test').addEventListener('click', sendTest);
    await loadDashboard();
});

async function loadDashboard() {
    try {
        const data = await Api.get(`${LOGIN_NOTIFY_API}/dashboard`);
        const hint = document.getElementById('smtp-hint');
        hint.className = data.smtp_configured
            ? 'alert alert-success py-2 small'
            : 'alert alert-warning py-2 small';
        hint.textContent = data.smtp_hint || '';

        const today = data.today || {};
        document.getElementById('kpi-sent').textContent = Number(today.sent || 0).toLocaleString();
        document.getElementById('kpi-failed').textContent = Number(today.failed || 0).toLocaleString();
        document.getElementById('kpi-email').textContent =
            (data.settings && data.settings.notify_email) || 'Not set';

        const s = data.settings || {};
        document.getElementById('enabled').checked = !!s.enabled;
        document.getElementById('notify_email').value = s.notify_email || '';
        document.getElementById('notes').value = s.notes || '';

        const body = document.getElementById('log-body');
        const recent = data.recent || [];
        body.innerHTML = recent.length
            ? recent.map((row) => `
                <tr>
                    <td class="small">${esc((row.created_at || '').replace('T', ' ').slice(0, 19))}</td>
                    <td>
                        <div>${esc(row.username || '—')}</div>
                        <div class="small text-muted">${esc(row.full_name || '')}</div>
                    </td>
                    <td class="small">${esc(row.ip || '—')}</td>
                    <td class="small">${esc([row.browser, row.device, row.os].filter(Boolean).join(' · ') || '—')}</td>
                    <td class="small">${esc(row.sent_to || '—')}</td>
                    <td>${row.status === 'sent'
                        ? '<span class="badge text-bg-success">sent</span>'
                        : `<span class="badge text-bg-danger" title="${esc(row.detail || '')}">failed</span>`}</td>
                </tr>
            `).join('')
            : '<tr><td colspan="6" class="text-muted">No login emails yet. Sign in once after saving the address.</td></tr>';
    } catch (error) {
        Auth.showAlert('login-notify-alert', error.message || 'Failed to load.', 'danger');
    }
}

async function saveSettings(event) {
    event.preventDefault();
    try {
        await Api.put(`${LOGIN_NOTIFY_API}/settings`, {
            enabled: document.getElementById('enabled').checked,
            notify_email: document.getElementById('notify_email').value.trim(),
            notes: document.getElementById('notes').value.trim(),
        });
        Auth.showAlert('login-notify-alert', 'Login alert settings saved.', 'success');
        await loadDashboard();
    } catch (error) {
        Auth.showAlert('login-notify-alert', error.message || 'Save failed.', 'danger');
    }
}

async function sendTest() {
    try {
        await Api.post(`${LOGIN_NOTIFY_API}/test`, {});
        Auth.showAlert('login-notify-alert', 'Test email sent to the default address.', 'success');
        await loadDashboard();
    } catch (error) {
        Auth.showAlert('login-notify-alert', error.message || 'Test email failed.', 'danger');
        await loadDashboard();
    }
}

function esc(value) {
    return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
