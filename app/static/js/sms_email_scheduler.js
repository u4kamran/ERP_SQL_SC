const API = '/api/v1/reports/sms-email';

document.addEventListener('DOMContentLoaded', async () => {
    await Auth.requireAuth();
    if (!canManage()) {
        document.querySelector('.sms-scheduler-form').innerHTML =
            '<div class="alert alert-danger">Access denied. Admin permission required.</div>';
        return;
    }

    bindEvents();
    await loadAll();
    setInterval(loadStatus, 60000);
});

function canManage() {
    return Auth.hasPermission('reports.sms_email.manage')
        || Auth.hasPermission('reports.gl_ledger.view')
        || Auth.hasPermission('inventory.fin_item.view')
        || Auth.hasPermission('auth.admin.full');
}

function bindEvents() {
    document.getElementById('btn-save').addEventListener('click', saveConfig);
    document.getElementById('btn-test').addEventListener('click', sendTest);
    document.getElementById('btn-run-now').addEventListener('click', runNow);
}

async function loadAll() {
    await Promise.all([loadConfig(), loadStatus()]);
}

async function loadConfig() {
    try {
        const config = await Api.get(`${API}/config`);
        document.getElementById('enabled').checked = config.enabled;
        document.getElementById('recipients').value = config.recipients || '';
        document.getElementById('body_keyword').value = config.body_keyword || 'Total Sales';
        document.getElementById('window_start').value = toTimeInput(config.window_start || '08:00');
        document.getElementById('window_end').value = toTimeInput(config.window_end || '01:30');
        document.getElementById('check_interval_minutes').value = String(config.check_interval_minutes || 30);
        document.getElementById('email_subject').value = config.email_subject || 'Sales Summary Alert';
    } catch (e) {
        Auth.showAlert('alert-area', e.message || 'Could not load settings.');
    }
}

async function loadStatus() {
    try {
        const status = await Api.get(`${API}/status`);
        setCard('card-scheduler', 'status-scheduler', status.scheduler_running ? 'Running' : 'Stopped',
            status.scheduler_running ? 'is-ok' : 'is-warn');
        setCard('card-window', 'status-window',
            status.within_window ? 'Inside window' : 'Outside window',
            status.within_window ? 'is-ok' : 'is-warn');
        setCard('card-smtp', 'status-smtp',
            status.smtp_configured ? 'Configured' : 'Not configured',
            status.smtp_configured ? 'is-ok' : 'is-bad');
        setCard('card-pending', 'status-pending',
            status.pending_send ? 'Yes — new record' : 'No',
            status.pending_send ? 'is-warn' : 'is-ok');

        document.getElementById('latest-id').textContent = status.latest_record_id ?? '—';
        document.getElementById('last-emailed-id').textContent = status.last_emailed_id ?? '0';
        document.getElementById('last-check').textContent = formatDateTime(status.last_check_at);
        document.getElementById('next-check').textContent = formatDateTime(status.next_check_at);
        document.getElementById('last-email').textContent = formatDateTime(status.last_email_at);
        document.getElementById('last-check-message').textContent =
            status.last_check_message || 'No check run yet.';
        document.getElementById('latest-preview').textContent =
            status.latest_record_preview || 'No matching SMS_DB_ record found.';

        const errEl = document.getElementById('last-error');
        if (status.last_error) {
            errEl.textContent = status.last_error;
            errEl.classList.remove('d-none');
        } else {
            errEl.classList.add('d-none');
        }
    } catch (e) {
        Auth.showAlert('alert-area', e.message || 'Could not load status.');
    }
}

function setCard(cardId, valueId, text, stateClass) {
    const card = document.getElementById(cardId);
    card.classList.remove('is-ok', 'is-warn', 'is-bad');
    if (stateClass) card.classList.add(stateClass);
    document.getElementById(valueId).textContent = text;
}

function buildPayload() {
    return {
        enabled: document.getElementById('enabled').checked,
        recipients: document.getElementById('recipients').value.trim(),
        body_keyword: document.getElementById('body_keyword').value.trim() || 'Total Sales',
        window_start: fromTimeInput(document.getElementById('window_start').value),
        window_end: fromTimeInput(document.getElementById('window_end').value),
        check_interval_minutes: parseInt(document.getElementById('check_interval_minutes').value, 10) || 30,
        email_subject: document.getElementById('email_subject').value.trim() || 'Sales Summary Alert',
    };
}

async function saveConfig() {
    const btn = document.getElementById('btn-save');
    btn.disabled = true;
    Auth.showAlert('alert-area', 'Saving settings...', 'info');
    try {
        await Api.put(`${API}/config`, buildPayload());
        Auth.showAlert('alert-area', 'Settings saved.', 'success');
        await loadStatus();
    } catch (e) {
        Auth.showAlert('alert-area', e.message || 'Could not save settings.');
    } finally {
        btn.disabled = false;
    }
}

async function sendTest() {
    const recipients = document.getElementById('recipients').value.trim();
    const email = recipients.split(',')[0]?.trim();
    if (!email) {
        Auth.showAlert('alert-area', 'Enter at least one email address first.');
        return;
    }

    const btn = document.getElementById('btn-test');
    btn.disabled = true;
    Auth.showAlert('alert-area', 'Sending test email...', 'info');
    try {
        const result = await Api.post(`${API}/test`, { to_email: email });
        Auth.showAlert('alert-area', result.message, result.success ? 'success' : 'danger');
        await loadStatus();
    } catch (e) {
        Auth.showAlert('alert-area', e.message || 'Test email failed.');
    } finally {
        btn.disabled = false;
    }
}

async function runNow() {
    const btn = document.getElementById('btn-run-now');
    btn.disabled = true;
    Auth.showAlert('alert-area', 'Running check...', 'info');
    try {
        const result = await Api.post(`${API}/run-now`, {});
        Auth.showAlert('alert-area', result.message, result.success ? 'success' : 'danger');
        await loadStatus();
    } catch (e) {
        Auth.showAlert('alert-area', e.message || 'Run failed.');
    } finally {
        btn.disabled = false;
    }
}

function toTimeInput(value) {
    const parts = (value || '08:00').split(':');
    return `${parts[0].padStart(2, '0')}:${(parts[1] || '00').padStart(2, '0')}`;
}

function fromTimeInput(value) {
    if (!value) return '08:00';
    const parts = value.split(':');
    return `${parts[0]}:${parts[1] || '00'}`;
}

function formatDateTime(value) {
    return formatUtcDateTime(value);
}
