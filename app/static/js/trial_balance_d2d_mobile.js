const API = '/api/v1/reports/trial-balance-d2d';
const WHATSAPP_PHONE_KEY = 'tb_d2d_whatsapp_phone';
const SEARCH_NOT_FOUND = 'not found';
const APP_NAME = document.querySelector('.ledger-mobile-sub')?.textContent?.trim() || 'ERP';
const REPORT_TITLE = 'Trial Balance Date to Date';

let searchModal;
let whatsappSearchModal;
let searchTarget = 'start';
let lastPayload = null;
let lastViewUrl = null;
let lastFilename = null;
let lastPdfBlob = null;
let whatsappConfigured = false;

function canViewGlLedger() {
    return Auth.hasPermission('reports.trial_balance_d2d_mobile.view') ||
        Auth.hasPermission('inventory.fin_item.view') ||
        Auth.hasPermission('auth.admin.full');
}

document.addEventListener('DOMContentLoaded', async () => {
    await Auth.requireAuth();
    if (!canViewGlLedger()) {
        document.querySelector('.ledger-mobile-main').innerHTML =
            '<div class="alert alert-danger">Access denied.</div>';
        return;
    }

    searchModal = new bootstrap.Modal(document.getElementById('searchModal'));
    whatsappSearchModal = new bootstrap.Modal(document.getElementById('whatsappSearchModal'));
    setDefaultDates();
    setDefaultAccounts();
    const canEmail = ReportDeliveryRights.applyEmailGate({
        allowed: ReportDeliveryRights.canEmailTrialMobile(),
    });
    const canWhatsApp = ReportDeliveryRights.applyWhatsAppGate({
        allowed: ReportDeliveryRights.canWhatsAppTrialMobile(),
    });
    if (canWhatsApp) {
        loadSavedWhatsAppPhone();
        await loadWhatsAppStatus();
    }
    if (canEmail) {
        await loadUserEmail();
        await loadEmailStatus();
    }
    bindEvents();
    AccountRangeSync.bind(validateAccount);
    wireSearchModalFocus('searchModal', 'search-query');
    wireSearchModalFocus('whatsappSearchModal', 'whatsapp-search-query');
    updateShareReadyState();
});

function bindEvents() {
    document.getElementById('btn-generate').addEventListener('click', generatePdf);
    document.getElementById('btn-email').addEventListener('click', emailPdf);
    document.getElementById('btn-whatsapp-auto').addEventListener('click', sendWhatsAppAuto);
    document.getElementById('btn-whatsapp-link').addEventListener('click', openWhatsAppLink);
    document.getElementById('btn-whatsapp-share').addEventListener('click', sharePdfOnWhatsApp);
    document.getElementById('btn-copy-whatsapp-msg').addEventListener('click', copyWhatsAppMessage);
    document.getElementById('btn-search-whatsapp').addEventListener('click', openWhatsAppSearch);
    document.getElementById('whatsapp-search-query').addEventListener('input', debounce(searchWhatsAppContacts, 300));
    document.getElementById('btn-new-report').addEventListener('click', resetReport);
    document.getElementById('btn-search-start').addEventListener('click', () => openSearch('start'));
    document.getElementById('btn-search-end').addEventListener('click', () => openSearch('end'));
    document.getElementById('search-query').addEventListener('input', debounce(searchAccounts, 300));
    document.getElementById('complete_report').addEventListener('change', toggleCompleteReport);

    document.querySelectorAll('.date-preset').forEach((btn) => {
        btn.addEventListener('click', () => applyDatePreset(btn.dataset.preset, btn));
    });
}

function setDefaultDates() {
    applyDatePreset('ytd');
}

function setDefaultAccounts() {
    const start = document.getElementById('start_ac_id');
    const end = document.getElementById('end_ac_id');
    if (!start.value) start.value = '12010001';
    if (!end.value) end.value = '12999999';
    AccountRangeSync.reset();
    validateAccount('start');
    validateAccount('end');
}

function formatDateInput(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
}

function applyDatePreset(preset, activeBtn) {
    const today = new Date();
    let from;
    const to = today;

    if (preset === 'today') {
        from = today;
    } else if (preset === 'month') {
        from = new Date(today.getFullYear(), today.getMonth(), 1);
    } else {
        from = new Date(today.getFullYear(), 0, 1);
    }

    document.getElementById('date_from').value = formatDateInput(from);
    document.getElementById('date_to').value = formatDateInput(to);

    document.querySelectorAll('.date-preset').forEach((b) => b.classList.remove('active'));
    if (activeBtn) activeBtn.classList.add('active');
}

function loadSavedWhatsAppPhone() {
    const saved = WhatsAppShare.loadPhonePreference(WHATSAPP_PHONE_KEY);
    if (saved) {
        const digits = saved.replace(/\D/g, '');
        document.getElementById('whatsapp_phone').value = digits.startsWith('92')
            ? digits.slice(2)
            : digits.startsWith('0') ? digits.slice(1) : digits;
    }
}

function updateShareReadyState() {
    const canWa = typeof ReportDeliveryRights === 'undefined' || ReportDeliveryRights.canWhatsAppTrialMobile();
    const canEmail = typeof ReportDeliveryRights === 'undefined' || ReportDeliveryRights.canEmailTrialMobile();
    const ready = Boolean(lastViewUrl && lastPayload);
    const shareHint = document.getElementById('share-not-ready');
    if (shareHint) shareHint.classList.toggle('d-none', ready);

    const emailHint = document.getElementById('email-not-ready');
    if (emailHint) emailHint.classList.toggle('d-none', ready);

    if (canWa) {
        const autoBtn = document.getElementById('btn-whatsapp-auto');
        if (autoBtn) autoBtn.disabled = !ready || !whatsappConfigured;

        ['btn-whatsapp-link', 'btn-copy-whatsapp-msg'].forEach((id) => {
            const el = document.getElementById(id);
            if (el) el.disabled = !ready;
        });
        updateShareFileSupport();
    }
    if (canEmail) {
        const emailBtn = document.getElementById('btn-email');
        if (emailBtn) emailBtn.disabled = !ready;
    }
}

async function loadWhatsAppStatus() {
    const hintEl = document.getElementById('whatsapp-config-hint');
    try {
        const status = await Api.get(`${API}/whatsapp/status`);
        whatsappConfigured = status.configured;
        if (!status.configured && hintEl) {
            hintEl.classList.remove('d-none');
            hintEl.textContent = status.hint || 'WhatsApp auto-send is not configured on server.';
        } else if (hintEl) {
            hintEl.classList.add('d-none');
        }
    } catch {
        whatsappConfigured = false;
    }
    updateShareReadyState();
}

async function sendWhatsAppAuto() {
    if (!lastPayload) {
        showAlert('Generate the PDF first.', 'warning');
        return;
    }
    const phoneRaw = getWhatsAppPhoneRaw();
    if (!phoneRaw) {
        showAlert('Enter a WhatsApp number.', 'warning');
        document.getElementById('whatsapp_phone').focus();
        return;
    }

    const btn = document.getElementById('btn-whatsapp-auto');
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Sending...';

    try {
        const result = await Api.post(`${API}/whatsapp`, {
            ...lastPayload,
            to_phone: phoneRaw,
            message: null,
        }, { timeoutMs: 600000 });
        WhatsAppShare.savePhonePreference(WHATSAPP_PHONE_KEY, phoneRaw);
        showAlert(result.message || 'PDF sent on WhatsApp.', 'success');
    } catch (e) {
        showAlert(e.message || 'Could not send on WhatsApp.', 'danger');
    } finally {
        btn.innerHTML = original;
        updateShareReadyState();
    }
}

function updateShareFileSupport() {
    const shareBtn = document.getElementById('btn-whatsapp-share');
    const hintEl = document.getElementById('share-file-hint');
    if (!shareBtn || !hintEl) return;

    const ready = Boolean(lastViewUrl && lastPayload);
    const mobile = WhatsAppShare.isMobile();
    const canShare = WhatsAppShare.canAttemptFileShare();

    if (!ready) {
        shareBtn.disabled = true;
        return;
    }

    if (canShare && (mobile || lastPdfBlob)) {
        shareBtn.disabled = !lastPdfBlob;
        if (!lastPdfBlob) {
            hintEl.textContent = 'Preparing PDF for file share…';
            hintEl.classList.remove('d-none');
        } else {
            hintEl.classList.add('d-none');
        }
    } else {
        shareBtn.disabled = true;
        hintEl.textContent = 'Plan B works on phone browsers. On PC use Plan A.';
        hintEl.classList.remove('d-none');
    }
}

function formatDisplayDate(value) {
    if (!value) return '—';
    const parts = String(value).split('-');
    if (parts.length === 3) return `${parts[2]}/${parts[1]}/${parts[0]}`;
    return value;
}

function buildAccountLabel(payload) {
    if (!payload) return '';
    if (payload.complete_report) return 'Complete report (all accounts)';
    const startTitle = document.getElementById('start_ac_title').textContent.trim();
    if (payload.start_ac_id === payload.end_ac_id) {
        return `${payload.start_ac_id} — ${startTitle}`;
    }
    return `${payload.start_ac_id} to ${payload.end_ac_id}`;
}

function buildWhatsAppMessage() {
    return WhatsAppShare.buildLedgerMessage({
        appName: APP_NAME,
        dateFrom: formatDisplayDate(lastPayload?.date_from),
        dateTo: formatDisplayDate(lastPayload?.date_to),
        accountLabel: buildAccountLabel(lastPayload),
        viewUrl: lastViewUrl,
        expiresMinutes: 15,
        reportTitle: REPORT_TITLE,
    });
}

function getWhatsAppPhoneRaw() {
    return document.getElementById('whatsapp_phone').value.trim();
}

function openWhatsAppLink() {
    if (!lastViewUrl || !lastPayload) {
        showAlert('Generate the PDF first.', 'warning');
        return;
    }

    const phoneRaw = getWhatsAppPhoneRaw();
    if (!phoneRaw) {
        showAlert('Enter a WhatsApp number.', 'warning');
        document.getElementById('whatsapp_phone').focus();
        return;
    }

    try {
        WhatsAppShare.openChat(phoneRaw, buildWhatsAppMessage());
        WhatsAppShare.savePhonePreference(WHATSAPP_PHONE_KEY, phoneRaw);
        if (!WhatsAppShare.isMobile()) {
            showAlert('WhatsApp opened in a new tab. Tap Send to deliver the PDF link.', 'success');
        }
    } catch (e) {
        showAlert(e.message || 'Could not open WhatsApp.', 'danger');
    }
}

async function sharePdfOnWhatsApp() {
    if (!lastPayload) {
        showAlert('Generate the PDF first.', 'warning');
        return;
    }

    const btn = document.getElementById('btn-whatsapp-share');
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Preparing PDF...';

    try {
        let blob = lastPdfBlob;
        if (!blob && lastViewUrl) {
            blob = await WhatsAppShare.fetchPdfBlob(lastViewUrl);
            lastPdfBlob = blob;
        }
        await WhatsAppShare.sharePdfBlob(blob, lastFilename || 'trial-balance-d2d.pdf', {
            title: REPORT_TITLE,
        });
        showAlert('Select WhatsApp from the share menu to send the PDF.', 'success');
    } catch (e) {
        if (e?.name === 'AbortError') return;
        showAlert(e.message || 'Could not share PDF file.', 'warning');
    } finally {
        updateShareFileSupport();
        btn.innerHTML = original;
    }
}

async function cachePdfForShare(viewUrl) {
    lastPdfBlob = null;
    try {
        lastPdfBlob = await WhatsAppShare.fetchPdfBlob(viewUrl);
    } catch {
        lastPdfBlob = null;
    }
    updateShareFileSupport();
}

async function copyWhatsAppMessage() {
    if (!lastViewUrl || !lastPayload) {
        showAlert('Generate the PDF first.', 'warning');
        return;
    }
    const text = buildWhatsAppMessage();
    try {
        await navigator.clipboard.writeText(text);
        showAlert('Message copied. Paste into WhatsApp manually.', 'success');
    } catch {
        window.prompt('Copy this message:', text);
    }
}

async function loadUserEmail() {
    try {
        const profile = await Api.get('/api/v1/profile/');
        if (profile?.email && !document.getElementById('email_to').value) {
            document.getElementById('email_to').value = profile.email;
        }
    } catch {
        /* optional */
    }
}

async function loadEmailStatus() {
    const hintEl = document.getElementById('email-smtp-hint');
    const emailBtn = document.getElementById('btn-email');
    try {
        const status = await Api.get(`${API}/email/status`);
        if (status.configured) {
            hintEl.classList.add('d-none');
            if (emailBtn) emailBtn.title = `Send from ${status.from_email}`;
        } else {
            hintEl.classList.remove('d-none');
            hintEl.innerHTML = `<strong>Email setup needed:</strong> ${esc(status.hint || 'Email is not configured on server.')}`;
            if (emailBtn) emailBtn.title = status.hint || 'Email is not configured on server.';
        }
    } catch (e) {
        hintEl.classList.remove('d-none');
        hintEl.innerHTML = `<strong>Could not check email settings.</strong> ${esc(e.message)}`;
    }
}

function toggleCompleteReport() {
    const complete = document.getElementById('complete_report').checked;
    document.getElementById('start_ac_id').disabled = complete;
    document.getElementById('end_ac_id').disabled = complete;
    document.getElementById('btn-search-start').disabled = complete;
    document.getElementById('btn-search-end').disabled = complete;
}

function buildPayload() {
    const complete = document.getElementById('complete_report').checked;
    const startRaw = document.getElementById('start_ac_id').value.trim();
    let endRaw = document.getElementById('end_ac_id').value.trim();
    if (!endRaw) endRaw = startRaw;

    if (!complete && !startRaw) {
        throw new Error('Enter an account ID or tick Complete Report.');
    }

    const startId = parseInt(startRaw, 10);
    const endId = parseInt(endRaw, 10);
    if (!complete && (Number.isNaN(startId) || Number.isNaN(endId))) {
        throw new Error('Account IDs must be valid numbers.');
    }
    if (!complete && endId < startId) {
        throw new Error('Ending ID must be >= Starting ID.');
    }

    return {
        start_ac_id: complete ? 1 : startId,
        end_ac_id: complete ? 99999999 : endId,
        date_from: document.getElementById('date_from').value,
        date_to: document.getElementById('date_to').value,
        suppress_zero_bal: document.getElementById('suppress_zero_bal').checked,
        complete_report: complete,
        short_format: document.getElementById('short_format').checked,
        sort_by: document.getElementById('sort_by').value,
        sort_order: document.getElementById('sort_order').value,
    };
}

function buildPdfFilename(payload) {
    const suffix = payload.short_format ? 'short' : 'full';
    return `trial-balance-d2d-${suffix}-${payload.date_from}-${payload.date_to}.pdf`;
}

function prefillEmailSubject(payload) {
    const subjectEl = document.getElementById('email_subject');
    if (!subjectEl || subjectEl.value.trim()) return;
    subjectEl.value = `Trial Balance Date to Date ${formatDisplayDate(payload.date_from)} - ${formatDisplayDate(payload.date_to)}`;
}

async function generatePdf() {
    const btn = document.getElementById('btn-generate');
    const statusEl = document.getElementById('generate-status');
    document.getElementById('alert-area').innerHTML = '';

    let payload;
    try {
        payload = buildPayload();
    } catch (e) {
        showAlert(e.message, 'danger');
        return;
    }

    if (!payload.date_from || !payload.date_to) {
        showAlert('Please select dates.', 'danger');
        return;
    }

    lastPayload = payload;
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Generating...';
    statusEl.textContent = 'Generating trial balance PDF… please wait.';

    try {
        const result = await Api.post(`${API}/pdf/mobile`, payload, { timeoutMs: 600000 });
        const viewUrl = result.view_url.startsWith('http')
            ? result.view_url
            : `${window.location.origin}${result.view_url}`;
        lastViewUrl = viewUrl;
        lastFilename = result.filename || buildPdfFilename(payload);

        document.getElementById('pdf-frame').src = viewUrl;
        document.getElementById('btn-open-pdf').href = viewUrl;

        document.getElementById('step-view').classList.remove('d-none');
        prefillEmailSubject(payload);
        statusEl.textContent = 'PDF ready. Preparing share options…';
        updateShareReadyState();
        await cachePdfForShare(viewUrl);
        document.getElementById('step-view').scrollIntoView({ behavior: 'smooth' });

        statusEl.textContent = 'PDF ready. View below, share on WhatsApp, or email.';
        showAlert('Trial balance PDF generated. View below, share on WhatsApp, or email.', 'success');
    } catch (e) {
        statusEl.textContent = '';
        showAlert(e.message || 'Could not generate PDF.', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = original;
    }
}

async function emailPdf() {
    if (!lastPayload) {
        showAlert('Generate the PDF first.', 'warning');
        return;
    }

    const toEmail = document.getElementById('email_to').value.trim();
    if (!toEmail) {
        showAlert('Enter an email address.', 'warning');
        return;
    }

    const btn = document.getElementById('btn-email');
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Sending...';

    try {
        const result = await Api.post(`${API}/email`, {
            ...lastPayload,
            to_email: toEmail,
            subject: document.getElementById('email_subject').value.trim() || null,
            message: document.getElementById('email_message').value.trim() || null,
        }, { timeoutMs: 600000 });
        showAlert(result.message || 'Email sent.', 'success');
    } catch (e) {
        showAlert(e.message || 'Could not send email.', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = original;
    }
}

function resetReport() {
    lastPayload = null;
    lastViewUrl = null;
    lastFilename = null;
    lastPdfBlob = null;
    document.getElementById('pdf-frame').removeAttribute('src');
    document.getElementById('step-view').classList.add('d-none');
    document.getElementById('generate-status').textContent = '';
    document.getElementById('email_subject').value = '';
    updateShareReadyState();
    document.getElementById('step-request').scrollIntoView({ behavior: 'smooth' });
}

function showAlert(message, type) {
    document.getElementById('alert-area').innerHTML =
        `<div class="alert alert-${type} alert-dismissible fade show" role="alert">${esc(message)}
         <button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>`;
}

async function validateAccount(which) {
    const id = document.getElementById(`${which}_ac_id`).value.trim();
    const titleEl = document.getElementById(`${which}_ac_title`);
    if (!id) {
        titleEl.textContent = 'Account title';
        return;
    }
    try {
        const data = await Api.get(`${API}/accounts/${encodeURIComponent(id)}`);
        titleEl.textContent = data.ac_title;
    } catch {
        titleEl.textContent = 'Account not found';
    }
}

function focusSearchInput(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    input.focus();
    if (input.value && typeof input.select === 'function') input.select();
}

function wireSearchModalFocus(modalId, inputId) {
    const modalEl = document.getElementById(modalId);
    if (!modalEl) return;
    modalEl.addEventListener('shown.bs.modal', () => focusSearchInput(inputId));
}

function openSearch(target) {
    searchTarget = target;
    document.getElementById('search-query').value = '';
    document.getElementById('search-results').innerHTML = '';
    searchModal.show();
}

function formatWhatsAppSearchError(err) {
    const msg = err?.message || 'Search failed.';
    if (msg === 'Not Found') {
        return 'WhatsApp search API not loaded. Restart: STOP-ALL.bat then START-ALL.bat.';
    }
    return msg;
}

function renderWhatsAppSearchResults(results, container) {
    if (!results.length) {
        container.innerHTML = `<div class="text-muted p-2">${SEARCH_NOT_FOUND}</div>`;
        focusSearchInput('whatsapp-search-query');
        return;
    }
    container.innerHTML = results.map((r) => {
        const disabled = r.has_mobile === false || !r.phone_raw;
        const badgeClass = disabled ? 'bg-secondary' : 'bg-success';
        return `
        <button type="button" class="list-group-item list-group-item-action text-start wa-search-pick${disabled ? ' disabled opacity-75' : ''}"
            data-phone="${esc(r.phone_raw)}" data-name="${esc(r.name)}" ${disabled ? 'disabled' : ''}>
            <strong>${esc(r.name)}</strong>
            <span class="badge ${badgeClass} ms-1">${esc(r.phone_display)}</span><br>
            <small class="text-muted">${esc(r.source)}${r.ac_id ? ` · A/C ${r.ac_id}` : ''}</small>
        </button>`;
    }).join('');
    container.className = 'list-group';
    container.querySelectorAll('.wa-search-pick:not([disabled])').forEach((btn) => {
        btn.addEventListener('click', () => pickWhatsAppContact(btn.dataset.phone, btn.dataset.name));
    });
}

async function openWhatsAppSearch() {
    const startId = document.getElementById('start_ac_id')?.value.trim();
    const seed = document.getElementById('start_ac_title')?.textContent?.trim();
    const queryEl = document.getElementById('whatsapp-search-query');
    const container = document.getElementById('whatsapp-search-results');
    let query = '';
    if (startId) query = startId;
    else if (seed && seed !== 'Account title' && !/not found/i.test(seed)) query = seed;
    queryEl.value = query;
    container.innerHTML = '';
    whatsappSearchModal.show();

    if (startId) {
        try {
            const contact = await Api.get(`${API}/whatsapp/contacts/lookup/${encodeURIComponent(startId)}`);
            if (contact?.has_mobile !== false && contact?.phone_raw) {
                pickWhatsAppContact(contact.phone_raw, contact.name);
                return;
            }
            renderWhatsAppSearchResults([contact], container);
            return;
        } catch {
            /* fall through */
        }
    }

    if (queryEl.value.trim()) searchWhatsAppContacts();
}

function pickWhatsAppContact(phoneRaw, name) {
    const input = document.getElementById('whatsapp_phone');
    input.value = phoneRaw;
    WhatsAppShare.savePhonePreference(WHATSAPP_PHONE_KEY, phoneRaw);
    whatsappSearchModal.hide();
    showAlert(`Selected ${name} — ${phoneRaw}`, 'success');
    input.focus();
}

async function searchWhatsAppContacts() {
    const q = document.getElementById('whatsapp-search-query').value.trim();
    const container = document.getElementById('whatsapp-search-results');
    if (!q) {
        container.innerHTML = '';
        return;
    }
    container.innerHTML = '<div class="text-muted p-2">Searching...</div>';
    try {
        let results = await Api.get(`${API}/whatsapp/contacts/search?q=${encodeURIComponent(q)}`);
        if (!results.length) {
            const startId = document.getElementById('start_ac_id')?.value.trim();
            if (startId && startId !== q) {
                results = await Api.get(`${API}/whatsapp/contacts/search?q=${encodeURIComponent(startId)}`);
            }
        }
        renderWhatsAppSearchResults(results, container);
    } catch (e) {
        container.innerHTML = `<div class="text-danger p-2">${esc(formatWhatsAppSearchError(e))}</div>`;
        focusSearchInput('whatsapp-search-query');
    }
}

async function searchAccounts() {
    const q = document.getElementById('search-query').value.trim();
    const container = document.getElementById('search-results');
    if (!q) {
        container.innerHTML = '';
        return;
    }
    try {
        const results = await Api.get(`${API}/accounts/search?q=${encodeURIComponent(q)}`);
        if (!results.length) {
            container.innerHTML = `<div class="text-muted p-2">${SEARCH_NOT_FOUND}</div>`;
            focusSearchInput('search-query');
            return;
        }
        container.innerHTML = results.map((r) => `
            <button type="button" class="list-group-item list-group-item-action text-start search-pick"
                data-id="${r.ac_id}" data-title="${esc(r.ac_title)}">
                <strong>${esc(String(r.ac_id))}</strong><br>
                <small>${esc(r.ac_title)}</small>
            </button>`).join('');
        container.className = 'list-group';
        container.querySelectorAll('.search-pick').forEach((btn) => {
            btn.addEventListener('click', () => {
                AccountRangeSync.pickAccount(searchTarget, btn.dataset.id, btn.dataset.title, validateAccount);
                searchModal.hide();
            });
        });
    } catch (e) {
        container.innerHTML = `<div class="text-danger p-2">${esc(e.message)}</div>`;
    }
}

function debounce(fn, wait) {
    let t;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), wait);
    };
}

function esc(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
