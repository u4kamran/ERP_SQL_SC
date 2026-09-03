const API = '/api/v1/reports/gl-ledger-detailed';
const WHATSAPP_PHONE_KEY = 'gl_ledger_detailed_whatsapp_phone';
const SEARCH_NOT_FOUND = 'not found';
let searchModal;
let whatsappSearchModal;
let searchTarget = 'start';
let lastPdfUrl = null;
let lastPdfFilename = null;
let lastPdfViewUrl = null;
let lastPayload = null;
let lastMobileShareUrl = null;
let lastPdfBlob = null;
let whatsappConfigured = false;

function canViewGlLedger() {
    return Auth.hasPermission('reports.gl_ledger_detailed.view') ||
        Auth.hasPermission('inventory.fin_item.view') ||
        Auth.hasPermission('auth.admin.full');
}

function isMobileDevice() {
    return /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent) ||
        (window.matchMedia && window.matchMedia('(max-width: 768px)').matches);
}

document.addEventListener('DOMContentLoaded', async () => {
    await Auth.requireAuth();
    if (!canViewGlLedger()) {
        document.querySelector('.gl-report-form').innerHTML =
            '<div class="alert alert-danger">Access denied. You need inventory or report permission.</div>';
        return;
    }

    searchModal = new bootstrap.Modal(document.getElementById('searchModal'));
    whatsappSearchModal = new bootstrap.Modal(document.getElementById('whatsappSearchModal'));
    setDefaultDates();
    setDefaultAccounts();
    const canEmail = ReportDeliveryRights.applyEmailGate({
        allowed: ReportDeliveryRights.canEmailGlDetailed(),
    });
    const canWhatsApp = ReportDeliveryRights.applyWhatsAppGate({
        allowed: ReportDeliveryRights.canWhatsAppGlDetailed(),
    });
    if (canEmail) {
        await loadUserEmail();
        await loadEmailStatus();
    }
    if (canWhatsApp) {
        await loadWhatsAppStatus();
        loadSavedWhatsAppPhone();
    }
    bindEvents();
    AccountRangeSync.bind(validateAccount);
    wireSearchModalFocus('searchModal', 'search-query');
    wireSearchModalFocus('whatsappSearchModal', 'whatsapp-search-query');
    updateShareReadyState();
});

function bindEvents() {
    document.getElementById('btn-print').addEventListener('click', printPdf);
    document.getElementById('btn-email').addEventListener('click', emailPdf);
    document.getElementById('btn-whatsapp-auto')?.addEventListener('click', sendWhatsAppAuto);
    document.getElementById('btn-whatsapp-link')?.addEventListener('click', openWhatsAppLink);
    document.getElementById('btn-whatsapp-share')?.addEventListener('click', sharePdfOnWhatsApp);
    document.getElementById('btn-copy-whatsapp-msg')?.addEventListener('click', copyWhatsAppMessage);
    document.getElementById('btn-search-whatsapp')?.addEventListener('click', openWhatsAppSearch);
    document.getElementById('whatsapp-search-query')?.addEventListener('input', debounce(searchWhatsAppContacts, 300));
    document.getElementById('btn-open-pdf').addEventListener('click', (e) => {
        e.preventDefault();
        openLastPdf();
    });
    document.getElementById('btn-clear').addEventListener('click', clearForm);
    document.getElementById('btn-search-start').addEventListener('click', () => openSearch('start'));
    document.getElementById('btn-search-end').addEventListener('click', () => openSearch('end'));
    document.getElementById('search-query').addEventListener('input', debounce(searchAccounts, 300));
    document.getElementById('complete_report').addEventListener('change', toggleCompleteReport);
}

function setDefaultDates() {
    const today = new Date();
    const yearStart = new Date(today.getFullYear(), 0, 1);
    document.getElementById('date_from').value = formatDateInput(yearStart);
    document.getElementById('date_to').value = formatDateInput(today);
}

function setDefaultAccounts() {
    const start = document.getElementById('start_ac_id');
    const end = document.getElementById('end_ac_id');
    if (!start.value) start.value = '12010090';
    if (!end.value) end.value = start.value;
    AccountRangeSync.reset();
    validateAccount('start');
    validateAccount('end');
}

async function loadUserEmail() {
    try {
        const profile = await Api.get('/api/v1/profile/');
        if (profile?.email) {
            const emailInput = document.getElementById('email_to');
            if (!emailInput.value) emailInput.value = profile.email;
        }
    } catch {
        /* profile email optional */
    }
}

async function loadEmailStatus() {
    const hintEl = document.getElementById('email-smtp-hint');
    const emailBtn = document.getElementById('btn-email');
    try {
        const status = await Api.get(`${API}/email/status`);
        if (status.configured) {
            hintEl.classList.add('d-none');
            emailBtn.title = `Send from ${status.from_email}`;
        } else {
            hintEl.classList.remove('d-none');
            hintEl.className = 'alert alert-warning py-2 small';
            hintEl.innerHTML = `<strong>Email setup needed:</strong> ${esc(status.hint)}`;
            emailBtn.title = status.hint;
        }
    } catch (e) {
        hintEl.classList.remove('d-none');
        hintEl.className = 'alert alert-warning py-2 small';
        hintEl.innerHTML = `<strong>Could not check email settings.</strong> ${esc(e.message)}`;
    }
}

function loadSavedWhatsAppPhone() {
    const input = document.getElementById('whatsapp_phone');
    if (!input || typeof WhatsAppShare === 'undefined') return;
    const saved = WhatsAppShare.loadPhonePreference(WHATSAPP_PHONE_KEY);
    if (saved) {
        const digits = saved.replace(/\D/g, '');
        input.value = digits.startsWith('92')
            ? digits.slice(2)
            : digits.startsWith('0') ? digits.slice(1) : digits;
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
        appName: document.title.replace(' - ', ' ').split(' - ')[0] || 'ERP',
        dateFrom: formatDisplayDate(lastPayload?.date_from),
        dateTo: formatDisplayDate(lastPayload?.date_to),
        accountLabel: buildAccountLabel(lastPayload),
        viewUrl: lastMobileShareUrl,
        expiresMinutes: 15,
    });
}

async function loadWhatsAppStatus() {
    const hintEl = document.getElementById('whatsapp-config-hint');
    try {
        const status = await Api.get(`${API}/whatsapp/status`);
        whatsappConfigured = status.configured;
        if (!status.configured && hintEl) {
            hintEl.classList.remove('d-none');
            hintEl.innerHTML = `<strong>WhatsApp auto-send not configured:</strong> ${esc(status.hint)}`;
        } else if (hintEl) {
            hintEl.classList.add('d-none');
        }
    } catch {
        whatsappConfigured = false;
    }
    updateShareReadyState();
}

function updateShareReadyState() {
    if (typeof ReportDeliveryRights !== 'undefined' && !ReportDeliveryRights.canWhatsAppGl()) {
        return;
    }
    const ready = Boolean(lastMobileShareUrl && lastPayload);
    const hint = document.getElementById('wa-not-ready');
    if (hint) hint.classList.toggle('d-none', ready);

    const autoBtn = document.getElementById('btn-whatsapp-auto');
    if (autoBtn) autoBtn.disabled = !ready || !whatsappConfigured;

    const linkBtn = document.getElementById('btn-whatsapp-link');
    const copyBtn = document.getElementById('btn-copy-whatsapp-msg');
    const shareBtn = document.getElementById('btn-whatsapp-share');
    if (linkBtn) linkBtn.disabled = !ready;
    if (copyBtn) copyBtn.disabled = !ready;
    if (shareBtn) {
        shareBtn.disabled = !ready || !lastPdfBlob
            || (typeof WhatsAppShare !== 'undefined' && !WhatsAppShare.canAttemptFileShare());
    }
}

async function sendWhatsAppAuto() {
    if (!lastPayload) {
        Auth.showAlert('alert-area', 'Generate PDF first (Print PDF).', 'warning');
        return;
    }
    const phoneRaw = document.getElementById('whatsapp_phone')?.value.trim();
    if (!phoneRaw) {
        Auth.showAlert('alert-area', 'Enter a WhatsApp number.', 'warning');
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
        Auth.showAlert('alert-area', result.message || 'PDF sent on WhatsApp.', 'success');
    } catch (e) {
        Auth.showAlert('alert-area', e.message || 'Could not send on WhatsApp.', 'danger');
    } finally {
        btn.innerHTML = original;
        updateShareReadyState();
    }
}

function openWhatsAppLink() {
    if (!lastMobileShareUrl || !lastPayload) {
        Auth.showAlert('alert-area', 'Generate PDF first (Print PDF).', 'warning');
        return;
    }
    const phoneRaw = document.getElementById('whatsapp_phone')?.value.trim();
    if (!phoneRaw) {
        Auth.showAlert('alert-area', 'Enter a WhatsApp number.', 'warning');
        return;
    }
    try {
        WhatsAppShare.openChat(phoneRaw, buildWhatsAppMessage());
        WhatsAppShare.savePhonePreference(WHATSAPP_PHONE_KEY, phoneRaw);
    } catch (e) {
        Auth.showAlert('alert-area', e.message || 'Could not open WhatsApp.');
    }
}

async function sharePdfOnWhatsApp() {
    if (!lastPdfBlob || !lastPayload) {
        Auth.showAlert('alert-area', 'Generate PDF first (Print PDF).', 'warning');
        return;
    }
    try {
        await WhatsAppShare.sharePdfBlob(lastPdfBlob, lastPdfFilename || 'customer-ledger-detailed.pdf', {
            title: 'Customer Ledger (Detailed)',
        });
        Auth.showAlert('alert-area', 'Select WhatsApp in the share menu.', 'success');
    } catch (e) {
        if (e?.name !== 'AbortError') {
            Auth.showAlert('alert-area', e.message || 'Could not share PDF.');
        }
    }
}

async function copyWhatsAppMessage() {
    if (!lastMobileShareUrl || !lastPayload) {
        Auth.showAlert('alert-area', 'Generate PDF first (Print PDF).', 'warning');
        return;
    }
    const text = buildWhatsAppMessage();
    try {
        await navigator.clipboard.writeText(text);
        Auth.showAlert('alert-area', 'Message copied. Paste into WhatsApp.', 'success');
    } catch {
        window.prompt('Copy this message:', text);
    }
}

function formatDateInput(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
}

function toggleCompleteReport() {
    const complete = document.getElementById('complete_report').checked;
    document.getElementById('start_ac_id').disabled = complete;
    document.getElementById('end_ac_id').disabled = complete;
    document.getElementById('btn-search-start').disabled = complete;
    document.getElementById('btn-search-end').disabled = complete;
}

function clearForm() {
    AccountRangeSync.reset();
    document.getElementById('start_ac_id').value = '';
    document.getElementById('end_ac_id').value = '';
    document.getElementById('suppress_zero_bal').checked = false;
    document.getElementById('complete_report').checked = false;
    document.getElementById('page_wise').checked = false;
    const detailCb = document.getElementById('include_invoice_detail');
    if (detailCb) detailCb.checked = true;
    toggleCompleteReport();
    setDefaultDates();
    document.getElementById('start_ac_title').textContent = 'Starting ID Title';
    document.getElementById('end_ac_title').textContent = 'Ending ID Title';
    setStatus('');
    hidePdfPreview();
}

function setStatus(message, isError = false) {
    const el = document.getElementById('report-status');
    el.textContent = message;
    el.className = 'report-status mt-3';
    if (isError) el.classList.add('is-error');
    else if (message) el.classList.add('is-success');
}

function buildPdfFilename(payload) {
    return `customer-ledger-detailed-${payload.date_from}-${payload.date_to}.pdf`;
}

function buildPdfViewUrl(payload) {
    const params = new URLSearchParams({
        start_ac_id: String(payload.start_ac_id),
        end_ac_id: String(payload.end_ac_id),
        date_from: payload.date_from,
        date_to: payload.date_to,
        suppress_zero_bal: String(payload.suppress_zero_bal),
        complete_report: String(payload.complete_report),
        page_wise: String(payload.page_wise),
        include_invoice_detail: String(payload.include_invoice_detail !== false),
        inline: 'true',
    });
    return `${API}/pdf?${params.toString()}`;
}

function buildPdfDownloadUrl(payload) {
    const params = new URLSearchParams({
        start_ac_id: String(payload.start_ac_id),
        end_ac_id: String(payload.end_ac_id),
        date_from: payload.date_from,
        date_to: payload.date_to,
        suppress_zero_bal: String(payload.suppress_zero_bal),
        complete_report: String(payload.complete_report),
        page_wise: String(payload.page_wise),
        include_invoice_detail: String(payload.include_invoice_detail !== false),
        inline: 'false',
    });
    return `${API}/pdf?${params.toString()}`;
}

function hidePdfPreview() {
    if (lastPdfUrl) {
        URL.revokeObjectURL(lastPdfUrl);
    }
    lastPdfUrl = null;
    lastPdfFilename = null;
    lastPdfViewUrl = null;
    lastPayload = null;
    lastMobileShareUrl = null;
    lastPdfBlob = null;
    updateShareReadyState();

    document.getElementById('pdf-mobile-panel').classList.add('d-none');
    document.getElementById('pdf-preview-panel').classList.add('d-none');
    document.getElementById('pdf-preview-frame').removeAttribute('src');
    document.getElementById('pdf-preview-meta').textContent = '';
    document.getElementById('pdf-mobile-meta').textContent = '';

    const openBtn = document.getElementById('btn-open-pdf');
    openBtn.classList.add('d-none');
    openBtn.removeAttribute('href');
    openBtn.removeAttribute('download');
}

function showDesktopPdfPreview(blob, filename) {
    if (lastPdfUrl) {
        URL.revokeObjectURL(lastPdfUrl);
    }
    lastPdfUrl = URL.createObjectURL(blob);
    lastPdfFilename = filename;

    window.open(lastPdfUrl, '_blank');

    const openBtn = document.getElementById('btn-open-pdf');
    openBtn.href = lastPdfUrl;
    openBtn.download = filename;
    openBtn.classList.remove('d-none');
}

async function fetchPdfBlob(payload) {
    const headers = { 'Content-Type': 'application/json' };
    const token = Api.getToken();
    if (token) headers.Authorization = `Bearer ${token}`;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 600000);

    try {
        const response = await fetch(`${API}/pdf`, {
            method: 'POST',
            headers,
            credentials: 'include',
            body: JSON.stringify(payload),
            signal: controller.signal,
        });

        if (!response.ok) {
            let message = 'Failed to generate PDF.';
            try {
                const data = await response.json();
                message = typeof data.detail === 'string' ? data.detail : message;
            } catch { /* ignore */ }
            throw new Error(message);
        }

        const blob = await response.blob();
        if (!blob || blob.size < 100) {
            throw new Error('Server returned an empty PDF.');
        }
        return blob;
    } catch (err) {
        if (err?.name === 'AbortError') {
            throw new Error('PDF generation timed out after 10 minutes. Try again or use a shorter date range.');
        }
        if (err instanceof Error && err.message && err.message !== 'Failed to fetch') {
            throw err;
        }
        throw new Error('Cannot reach server. Wait a few seconds and try again.');
    } finally {
        clearTimeout(timer);
    }
}

function showMobilePdfOpen(blob, filename) {
    if (lastPdfUrl) {
        URL.revokeObjectURL(lastPdfUrl);
    }
    lastPdfUrl = URL.createObjectURL(blob);
    lastPdfFilename = filename;

    const mobileBtn = document.getElementById('btn-mobile-open-pdf');
    mobileBtn.href = lastPdfUrl;
    document.getElementById('pdf-mobile-meta').textContent = filename;
    document.getElementById('pdf-mobile-panel').classList.remove('d-none');
    document.getElementById('pdf-mobile-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });

    const openBtn = document.getElementById('btn-open-pdf');
    openBtn.href = lastPdfUrl;
    openBtn.download = filename;
    openBtn.target = '_blank';
    openBtn.classList.remove('d-none');
}

function openLastPdf() {
    if (isMobileDevice() && lastPdfViewUrl) {
        window.location.href = lastPdfViewUrl;
        return;
    }
    if (lastPdfUrl) {
        window.open(lastPdfUrl, '_blank');
    } else if (lastPdfViewUrl) {
        window.location.href = lastPdfViewUrl;
    }
}

async function validateAccount(which) {
    const id = document.getElementById(`${which}_ac_id`).value.trim();
    const titleEl = document.getElementById(`${which}_ac_title`);
    if (!id) {
        titleEl.textContent = `${which === 'start' ? 'Starting' : 'Ending'} ID Title`;
        return;
    }
    try {
        const data = await Api.get(`${API}/accounts/${encodeURIComponent(id)}`);
        titleEl.textContent = data.ac_title;
    } catch {
        titleEl.textContent = `${which === 'start' ? 'Starting' : 'Ending'} ID not found ...`;
    }
}


function focusSearchInput(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    input.focus();
    if (input.value && typeof input.select === 'function') {
        input.select();
    }
}

function wireSearchModalFocus(modalId, inputId) {
    const modalEl = document.getElementById(modalId);
    if (!modalEl) return;
    modalEl.addEventListener('shown.bs.modal', () => focusSearchInput(inputId));
}

function formatWhatsAppSearchError(err) {
    const msg = err?.message || 'Search failed.';
    if (msg === 'Not Found') {
        return 'WhatsApp search API not loaded. Restart app: STOP-APP.bat then START-SITE.bat.';
    }
    return msg;
}

function renderWhatsAppSearchResults(results, container) {
    if (!results.length) {
        container.innerHTML = `<div class="text-muted p-2">${SEARCH_NOT_FOUND}</div>`;
        focusSearchInput('whatsapp-search-query');
        return;
    }
    const rows = results.map((r) => {
        const disabled = r.has_mobile === false || !r.phone_raw;
        return `
        <tr class="wa-search-row${disabled ? ' table-secondary' : ''}" style="cursor:${disabled ? 'default' : 'pointer'}"
            data-phone="${esc(r.phone_raw)}" data-name="${esc(r.name)}" data-disabled="${disabled ? '1' : '0'}">
            <td>${esc(r.name)}</td>
            <td>${esc(r.phone_display)}</td>
            <td>${esc(r.source)}${r.ac_id ? ` (${r.ac_id})` : ''}</td>
        </tr>`;
    }).join('');
    container.innerHTML = `
        <table class="table table-sm table-hover mb-0">
            <thead><tr><th>Name</th><th>Mobile</th><th>Source</th></tr></thead>
            <tbody>${rows}</tbody>
        </table>`;
    container.querySelectorAll('.wa-search-row').forEach((row) => {
        if (row.dataset.disabled === '1') return;
        row.addEventListener('click', () => pickWhatsAppContact(row.dataset.phone, row.dataset.name));
    });
}

async function openWhatsAppSearch() {
    const startId = document.getElementById('start_ac_id')?.value.trim();
    const seed = document.getElementById('start_ac_title')?.textContent?.trim();
    const queryEl = document.getElementById('whatsapp-search-query');
    const container = document.getElementById('whatsapp-search-results');
    let query = '';
    if (startId) {
        query = startId;
    } else if (seed && !/not found/i.test(seed)) {
        query = seed;
    }
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
            /* fall through to text search */
        }
    }

    if (queryEl.value.trim()) {
        searchWhatsAppContacts();
    }
}

function pickWhatsAppContact(phoneRaw, name) {
    const input = document.getElementById('whatsapp_phone');
    input.value = phoneRaw;
    WhatsAppShare.savePhonePreference(WHATSAPP_PHONE_KEY, phoneRaw);
    whatsappSearchModal.hide();
    Auth.showAlert('alert-area', `Selected ${name} — ${phoneRaw}`, 'success');
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

function openSearch(target) {
    searchTarget = target;
    document.getElementById('search-query').value = '';
    document.getElementById('search-results').innerHTML = '';
    searchModal.show();
}

async function searchAccounts() {
    const q = document.getElementById('search-query').value.trim();
    const container = document.getElementById('search-results');
    if (q.length < 1) {
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
        const rows = results.map(r => `
            <tr class="search-row" style="cursor:pointer"
                data-id="${r.ac_id}" data-title="${esc(r.ac_title)}">
                <td>${esc(r.ac_id_display)}</td>
                <td>${esc(String(r.ac_id))}</td>
                <td>${esc(r.ac_title)}</td>
            </tr>`).join('');
        container.innerHTML = `
            <table class="table table-sm table-hover mb-0">
                <thead><tr><th>Display</th><th>Ac ID</th><th>Title</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>`;
        container.querySelectorAll('.search-row').forEach(row => {
            row.addEventListener('click', () => {
                AccountRangeSync.pickAccount(searchTarget, row.dataset.id, row.dataset.title, validateAccount);
                searchModal.hide();
            });
        });
    } catch (e) {
        container.innerHTML = `<div class="text-danger p-2">${esc(e.message)}</div>`;
    }
}

function buildPayload() {
    const complete = document.getElementById('complete_report').checked;
    const startRaw = document.getElementById('start_ac_id').value.trim();
    const endRaw = document.getElementById('end_ac_id').value.trim();

    if (!complete && (!startRaw || !endRaw)) {
        throw new Error('Enter Starting ID and Ending ID, or tick Complete Report.');
    }

    const startId = parseInt(startRaw, 10);
    const endId = parseInt(endRaw, 10);
    if (!complete && (Number.isNaN(startId) || Number.isNaN(endId))) {
        throw new Error('Account IDs must be valid numbers.');
    }
    if (!complete && endId < startId) {
        throw new Error('Ending ID must be greater than or equal to Starting ID.');
    }

    return {
        start_ac_id: complete ? 1 : startId,
        end_ac_id: complete ? 99999999 : endId,
        date_from: document.getElementById('date_from').value,
        date_to: document.getElementById('date_to').value,
        suppress_zero_bal: document.getElementById('suppress_zero_bal').checked,
        complete_report: complete,
        page_wise: document.getElementById('page_wise').checked,
        include_invoice_detail: document.getElementById('include_invoice_detail')?.checked !== false,
    };
}

async function printPdf() {
    const btn = document.getElementById('btn-print');
    hidePdfPreview();
    document.getElementById('alert-area').innerHTML = '';

    let payload;
    try {
        payload = buildPayload();
    } catch (e) {
        setStatus(e.message, true);
        Auth.showAlert('alert-area', e.message);
        return;
    }

    if (!payload.date_from || !payload.date_to) {
        const msg = 'Please select From and To dates.';
        setStatus(msg, true);
        Auth.showAlert('alert-area', msg);
        return;
    }

    const filename = buildPdfFilename(payload);
    const originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Generating...';
    setStatus('Generating PDF... please wait (large reports may take 1-2 minutes).');

    try {
        const blob = await fetchPdfBlob(payload);
        lastPayload = payload;
        lastPdfBlob = blob;

        try {
            const mobile = await Api.post(`${API}/pdf/mobile`, payload, { timeoutMs: 600000 });
            lastMobileShareUrl = mobile.view_url.startsWith('http')
                ? mobile.view_url
                : `${window.location.origin}${mobile.view_url}`;
            lastPdfFilename = mobile.filename || filename;
        } catch {
            lastMobileShareUrl = null;
        }
        updateShareReadyState();

        if (isMobileDevice()) {
            showMobilePdfOpen(blob, filename);
            setStatus('Tap "Open PDF Report" to view on your phone.');
            return;
        }

        showDesktopPdfPreview(blob, filename);

        const link = document.createElement('a');
        link.href = lastPdfUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();

        setStatus('PDF opened in a new tab. Download also started.');
    } catch (e) {
        setStatus(e.message || 'Could not generate PDF.', true);
        Auth.showAlert('alert-area', e.message || 'Could not generate PDF.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
    }
}

async function emailPdf() {
    const btn = document.getElementById('btn-email');
    document.getElementById('alert-area').innerHTML = '';

    const toEmail = document.getElementById('email_to').value.trim();
    if (!toEmail) {
        const msg = 'Enter an email address to send the report.';
        setStatus(msg, true);
        Auth.showAlert('alert-area', msg);
        return;
    }

    let payload;
    try {
        payload = buildPayload();
    } catch (e) {
        setStatus(e.message, true);
        Auth.showAlert('alert-area', e.message);
        return;
    }

    const subject = document.getElementById('email_subject').value.trim();
    const message = document.getElementById('email_message').value.trim();
    const requestBody = {
        ...payload,
        to_email: toEmail,
        subject: subject || null,
        message: message || null,
    };

    const originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Sending...';
    setStatus('Sending report by email...');

    try {
        const result = await Api.post(`${API}/email`, requestBody, { timeoutMs: 600000 });
        setStatus(result.message || 'Report sent by email.');
        Auth.showAlert('alert-area', result.message || 'Report sent by email.', 'success');
    } catch (e) {
        setStatus(e.message || 'Could not send email.', true);
        Auth.showAlert('alert-area', e.message || 'Could not send email.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
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
