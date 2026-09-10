const OTP_CONTROL_API = '/api/v1/auth/security/otp-settings';

let currentSettings = null;
let pendingPayload = null;

document.addEventListener('DOMContentLoaded', async () => {
    const profile = await Auth.requireAuth();
    if (!profile) return;
    if (!Auth.hasPermission('auth.otp_sms_control.view')) {
        Auth.showAlert('otp-control-alert', 'No permission to view OTP SMS control.', 'warning');
        return;
    }
    if (!Auth.hasPermission('auth.otp_sms_control.manage')) {
        document.querySelectorAll('#otp-settings-form input, #otp-settings-form button').forEach((el) => {
            el.disabled = true;
        });
    }
    document.getElementById('btn-refresh').addEventListener('click', loadSettings);
    document.getElementById('otp-settings-form').addEventListener('submit', onSave);
    document.getElementById('master_enabled').addEventListener('change', refreshOverrideHints);
    document.getElementById('otp-confirm-yes').addEventListener('click', confirmAndSave);
    await loadSettings();
});

function badge(enabled) {
    return enabled
        ? '<span class="text-success">ENABLED</span>'
        : '<span class="text-danger">DISABLED</span>';
}

function refreshOverrideHints() {
    const masterOn = document.getElementById('master_enabled').checked;
    const webHint = document.getElementById('web-override-hint');
    const mobileHint = document.getElementById('mobile-override-hint');
    if (!masterOn) {
        webHint.textContent = 'Overridden by Master — Web OTP will be OFF after save.';
        mobileHint.textContent = 'Overridden by Master — Mobile OTP will be OFF after save.';
    } else {
        webHint.textContent = 'Guest web chat / public WhatsApp OTP.';
        mobileHint.textContent = 'Customer mobile app OTP (SMS_DB_ queue).';
    }
}

async function loadSettings() {
    try {
        const data = await Api.get(OTP_CONTROL_API);
        currentSettings = data;
        document.getElementById('master_enabled').checked = !!data.master_enabled;
        document.getElementById('web_enabled').checked = !!data.web_enabled;
        document.getElementById('mobile_enabled').checked = !!data.mobile_enabled;
        document.getElementById('row_version').value = String(data.row_version || 1);
        document.getElementById('comment').value = data.comment || '';

        document.getElementById('kpi-master').innerHTML = badge(!!data.master_enabled);
        document.getElementById('kpi-web').innerHTML = badge(!!data.web_effective);
        document.getElementById('kpi-mobile').innerHTML = badge(!!data.mobile_effective);
        document.getElementById('status-web').innerHTML = badge(!!data.web_effective);
        document.getElementById('status-mobile').innerHTML = badge(!!data.mobile_effective);
        document.getElementById('status-sms').innerHTML = badge(!!data.master_enabled);
        document.getElementById('meta-user').textContent = data.updated_by_username || '—';
        document.getElementById('meta-when').textContent = data.updated_at || '—';
        refreshOverrideHints();
        if (data.config_ok === false) {
            Auth.showAlert(
                'otp-control-alert',
                'OTP control table is not available. OTP stays required until setup is run.',
                'warning',
            );
        }
    } catch (error) {
        Auth.showAlert('otp-control-alert', error.message || 'Failed to load OTP settings.', 'danger');
    }
}

function readForm() {
    return {
        master_enabled: document.getElementById('master_enabled').checked,
        web_enabled: document.getElementById('web_enabled').checked,
        mobile_enabled: document.getElementById('mobile_enabled').checked,
        row_version: Number(document.getElementById('row_version').value || 1),
        comment: document.getElementById('comment').value.trim(),
    };
}

function onSave(event) {
    event.preventDefault();
    const payload = readForm();
    const prev = currentSettings || {};
    const turningMasterOff = prev.master_enabled && !payload.master_enabled;
    const turningAnyOff = (
        (prev.web_enabled && !payload.web_enabled)
        || (prev.mobile_enabled && !payload.mobile_enabled)
        || turningMasterOff
    );
    if (turningAnyOff) {
        pendingPayload = payload;
        const title = document.getElementById('otp-confirm-title');
        const body = document.getElementById('otp-confirm-body');
        const yes = document.getElementById('otp-confirm-yes');
        if (turningMasterOff) {
            title.textContent = 'WARNING';
            body.textContent = 'You are disabling OTP verification globally. This will affect Web and Mobile applications. Continue?';
            yes.textContent = 'DISABLE';
        } else {
            title.textContent = 'WARNING';
            body.textContent = 'Disabling OTP SMS will affect customer verification. Are you sure?';
            yes.textContent = 'YES, DISABLE OTP';
        }
        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('otp-confirm-modal'));
        modal.show();
        return;
    }
    saveSettings(payload);
}

async function confirmAndSave() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('otp-confirm-modal'));
    if (modal) modal.hide();
    if (!pendingPayload) return;
    const payload = pendingPayload;
    pendingPayload = null;
    await saveSettings(payload);
}

async function saveSettings(payload) {
    try {
        await Api.put(OTP_CONTROL_API, payload);
        Auth.showAlert('otp-control-alert', 'OTP SMS settings saved.', 'success');
        await loadSettings();
    } catch (error) {
        Auth.showAlert('otp-control-alert', error.message || 'Save failed.', 'danger');
    }
}
