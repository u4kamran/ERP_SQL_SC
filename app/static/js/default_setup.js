/** Default Setup — business day configuration. */
const SETUP_API = '/api/v1/settings/default-setup/business-day';

function showSetupAlert(message, type = 'success') {
    const el = document.getElementById('default-setup-alert');
    el.innerHTML = `<div class="alert alert-${type} py-2">${message}</div>`;
    if (type === 'success') {
        setTimeout(() => { el.innerHTML = ''; }, 4000);
    }
}

function formatDisplayTime(hhmm) {
    if (!hhmm) return '—';
    const [h, m] = hhmm.split(':').map(Number);
    const d = new Date(2000, 0, 1, h, m || 0);
    return d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
}

function updatePreview() {
    const start = document.getElementById('day-start-time').value;
    const end = document.getElementById('day-end-time').value;
    const preview = document.getElementById('business-day-preview');
    if (!start || !end) {
        preview.textContent = 'Enter start and end times.';
        return;
    }
    preview.innerHTML =
        `Each business day: <strong>${formatDisplayTime(start)}</strong> today`
        + ` → <strong>${formatDisplayTime(end)}</strong> next morning.`;
}

function canManageDefaultSetup() {
    return Auth.hasPermission('auth.admin.full');
}

async function loadBusinessDayConfig() {
    try {
        const data = await Api.get(SETUP_API);
        document.getElementById('day-start-time').value = data.business_day_start_time;
        document.getElementById('day-end-time').value = data.business_day_end_time;
        document.getElementById('cfg-start').textContent = formatDisplayTime(data.business_day_start_time);
        document.getElementById('cfg-end').textContent = formatDisplayTime(data.business_day_end_time);
        document.getElementById('cfg-note').textContent = data.business_hours_note || '—';
        document.getElementById('cfg-updated').textContent = data.updated_at || 'Default (not saved yet)';
        document.getElementById('cfg-updated-by').textContent = data.updated_by_username || '—';
        updatePreview();
    } catch (err) {
        showSetupAlert(err.message || 'Could not load Default Setup.', 'danger');
    }
}

async function saveBusinessDayConfig(event) {
    event.preventDefault();
    if (!canManageDefaultSetup()) {
        showSetupAlert('You need admin permission to save Default Setup.', 'warning');
        return;
    }
    const body = {
        business_day_start_time: document.getElementById('day-start-time').value,
        business_day_end_time: document.getElementById('day-end-time').value,
    };
    try {
        await Api.put(SETUP_API, body);
        showSetupAlert('Business day settings saved.');
        await loadBusinessDayConfig();
    } catch (err) {
        showSetupAlert(err.message || 'Save failed.', 'danger');
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    const profile = await Auth.requireAuth();
    if (!profile) return;
    if (!Auth.hasMenuPath('/admin/default-setup')) {
        Auth.requireMenuPath('/admin/default-setup');
        return;
    }
    if (!canManageDefaultSetup()) {
        document.querySelectorAll('#business-day-form input, #business-day-form button').forEach((el) => {
            el.disabled = true;
        });
        showSetupAlert('View only — admin permission is required to change settings.', 'warning');
    }
    document.getElementById('business-day-form').addEventListener('submit', saveBusinessDayConfig);
    document.getElementById('btn-refresh-setup').addEventListener('click', loadBusinessDayConfig);
    document.getElementById('day-start-time').addEventListener('change', updatePreview);
    document.getElementById('day-end-time').addEventListener('change', updatePreview);
    await loadBusinessDayConfig();
});
