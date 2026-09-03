const API = '/api/v1/reports/stock-balance-d2d';
const SEARCH_NOT_FOUND = 'not found';
let searchModal;
let searchTarget = 'start';
let lastPdfUrl = null;
let endFollowsStart = true;

function canView() {
    return Auth.hasPermission('reports.stock_balance_d2d.view') ||
        Auth.hasPermission('inventory.fin_item.view') ||
        Auth.hasPermission('auth.admin.full');
}

document.addEventListener('DOMContentLoaded', async () => {
    await Auth.requireAuth();
    if (!canView()) {
        document.querySelector('.gl-report-form').innerHTML =
            '<div class="alert alert-danger">Access denied. You need inventory or report permission.</div>';
        return;
    }

    searchModal = new bootstrap.Modal(document.getElementById('searchModal'));
    setDefaultDates();
    setDefaultItems();
    const canEmail = ReportDeliveryRights.applyEmailGate({
        allowed: ReportDeliveryRights.canEmailStock(),
    });
    if (canEmail) {
        await loadUserEmail();
        await loadEmailStatus();
    }
    bindEvents();
});

function bindEvents() {
    document.getElementById('btn-print').addEventListener('click', printPdf);
    document.getElementById('btn-email').addEventListener('click', emailPdf);
    document.getElementById('btn-open-pdf').addEventListener('click', (e) => {
        e.preventDefault();
        if (lastPdfUrl) window.open(lastPdfUrl, '_blank');
    });
    document.getElementById('btn-clear').addEventListener('click', clearForm);
    document.getElementById('btn-search-start').addEventListener('click', () => openSearch('start'));
    document.getElementById('btn-search-end').addEventListener('click', () => openSearch('end'));
    document.getElementById('search-query').addEventListener('input', debounce(searchItems, 300));
    document.getElementById('complete_report').addEventListener('change', toggleCompleteReport);

    const start = document.getElementById('start_item_id');
    const end = document.getElementById('end_item_id');
    start.addEventListener('change', () => {
        validateItem('start');
        if (endFollowsStart) {
            end.value = start.value;
            validateItem('end');
        }
    });
    end.addEventListener('input', () => {
        endFollowsStart = false;
    });
    end.addEventListener('change', () => validateItem('end'));
}

function setDefaultDates() {
    const today = new Date();
    const yearStart = new Date(today.getFullYear(), 0, 1);
    document.getElementById('date_from').value = formatDateInput(yearStart);
    document.getElementById('date_to').value = formatDateInput(today);
}

function setDefaultItems() {
    document.getElementById('start_item_id').value = '1000010001';
    document.getElementById('end_item_id').value = '1000019999';
    endFollowsStart = true;
    validateItem('start');
    validateItem('end');
}

async function loadUserEmail() {
    try {
        const profile = await Api.get('/api/v1/profile/');
        if (profile?.email) {
            const emailInput = document.getElementById('email_to');
            if (!emailInput.value) emailInput.value = profile.email;
        }
    } catch { /* optional */ }
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
        }
    } catch (e) {
        hintEl.classList.remove('d-none');
        hintEl.className = 'alert alert-warning py-2 small';
        hintEl.innerHTML = `<strong>Could not check email settings.</strong> ${esc(e.message)}`;
    }
}

function formatDateInput(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
}

function esc(s) {
    return String(s ?? '').replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    }[c]));
}

function debounce(fn, ms) {
    let t;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), ms);
    };
}

function setStatus(message, isError = false) {
    const el = document.getElementById('report-status');
    el.textContent = message;
    el.className = 'report-status mt-3';
    if (isError) el.classList.add('is-error');
    else if (message) el.classList.add('is-success');
}

function toggleCompleteReport() {
    const on = document.getElementById('complete_report').checked;
    document.getElementById('start_item_id').disabled = on;
    document.getElementById('end_item_id').disabled = on;
    document.getElementById('btn-search-start').disabled = on;
    document.getElementById('btn-search-end').disabled = on;
}

function buildPayload() {
    const start = parseInt(document.getElementById('start_item_id').value, 10);
    const end = parseInt(document.getElementById('end_item_id').value, 10);
    const dateFrom = document.getElementById('date_from').value;
    const dateTo = document.getElementById('date_to').value;
    if (!dateFrom || !dateTo) throw new Error('Select Date From and Date To.');
    if (dateTo < dateFrom) throw new Error('Invalid date range: From date must be on or before To date.');
    if (!document.getElementById('complete_report').checked) {
        if (!start || !end) throw new Error('Enter Starting and Ending Item ID.');
        if (end < start) throw new Error('Ending ID must be greater than or equal to Starting ID.');
    }
    return {
        start_item_id: start || 1,
        end_item_id: end || start || 1,
        date_from: dateFrom,
        date_to: dateTo,
        suppress_zero_bal: document.getElementById('suppress_zero_bal').checked,
        complete_report: document.getElementById('complete_report').checked,
        show_manual_id: document.getElementById('show_manual_id').checked,
        store_ledger: document.getElementById('store_ledger').checked,
        print_amount: document.getElementById('print_amount').checked,
        sort_by: document.getElementById('sort_by').value,
        sort_order: document.getElementById('sort_order').value,
    };
}

async function validateItem(which) {
    const id = document.getElementById(`${which}_item_id`).value.trim();
    const titleEl = document.getElementById(`${which}_item_title`);
    if (!id) {
        titleEl.textContent = `${which === 'start' ? 'Starting' : 'Ending'} ID Title`;
        return;
    }
    try {
        const data = await Api.get(`${API}/items/${encodeURIComponent(id)}`);
        titleEl.textContent = data.item_title;
    } catch {
        titleEl.textContent = `${which === 'start' ? 'Starting' : 'Ending'} ID not found ...`;
    }
}

function openSearch(target) {
    searchTarget = target;
    document.getElementById('search-query').value = '';
    document.getElementById('search-results').innerHTML = '';
    searchModal.show();
    setTimeout(() => document.getElementById('search-query').focus(), 200);
}

async function searchItems() {
    const q = document.getElementById('search-query').value.trim();
    const container = document.getElementById('search-results');
    if (q.length < 1) {
        container.innerHTML = '';
        return;
    }
    try {
        const results = await Api.get(`${API}/items/search?q=${encodeURIComponent(q)}`);
        if (!results.length) {
            container.innerHTML = `<div class="text-muted p-2">${SEARCH_NOT_FOUND}</div>`;
            return;
        }
        const rows = results.map(r => `
            <tr class="search-row" style="cursor:pointer"
                data-id="${r.item_id}" data-title="${esc(r.item_title)}">
                <td>${esc(r.item_id_display)}</td>
                <td>${esc(String(r.item_id))}</td>
                <td>${esc(r.manualid ?? '')}</td>
                <td>${esc(r.item_title)}</td>
            </tr>`).join('');
        container.innerHTML = `
            <table class="table table-sm table-hover mb-0">
                <thead><tr><th>Display</th><th>Item ID</th><th>Manual</th><th>Title</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>`;
        container.querySelectorAll('.search-row').forEach(row => {
            row.addEventListener('click', () => {
                const id = row.dataset.id;
                const title = row.dataset.title;
                document.getElementById(`${searchTarget}_item_id`).value = id;
                document.getElementById(`${searchTarget}_item_title`).textContent = title;
                if (searchTarget === 'start' && endFollowsStart) {
                    document.getElementById('end_item_id').value = id;
                    document.getElementById('end_item_title').textContent = title;
                }
                if (searchTarget === 'end') endFollowsStart = false;
                searchModal.hide();
            });
        });
    } catch (e) {
        container.innerHTML = `<div class="text-danger p-2">${esc(e.message)}</div>`;
    }
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
        if (!blob || blob.size < 100) throw new Error('Server returned an empty PDF.');
        return blob;
    } catch (err) {
        if (err?.name === 'AbortError') {
            throw new Error('PDF generation timed out. Try a smaller item range.');
        }
        if (err instanceof Error && err.message && err.message !== 'Failed to fetch') throw err;
        throw new Error('Cannot reach server. Wait a few seconds and try again.');
    } finally {
        clearTimeout(timer);
    }
}

async function printPdf() {
    const btn = document.getElementById('btn-print');
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Generating...';
    setStatus('Generating Stock Balance PDF...');
    try {
        const payload = buildPayload();
        const blob = await fetchPdfBlob(payload);
        const filename = `Stock_Balance_${payload.print_amount ? 'Amt_' : ''}${payload.date_from}_to_${payload.date_to}.pdf`;
        if (lastPdfUrl) URL.revokeObjectURL(lastPdfUrl);
        lastPdfUrl = URL.createObjectURL(blob);
        window.open(lastPdfUrl, '_blank');
        const openBtn = document.getElementById('btn-open-pdf');
        openBtn.href = lastPdfUrl;
        openBtn.download = filename;
        openBtn.classList.remove('d-none');
        setStatus(`PDF ready (${(blob.size / 1024).toFixed(1)} KB).`);
        Auth.showAlert('alert-area', 'Stock Balance PDF generated.', 'success');
    } catch (e) {
        setStatus(e.message || 'PDF failed.', true);
        Auth.showAlert('alert-area', e.message || 'PDF failed.', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = original;
    }
}

async function emailPdf() {
    const to = document.getElementById('email_to').value.trim();
    if (!to) {
        Auth.showAlert('alert-area', 'Enter at least one email address.', 'warning');
        return;
    }
    const btn = document.getElementById('btn-email');
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Sending...';
    try {
        const payload = {
            ...buildPayload(),
            to_email: to,
            subject: document.getElementById('email_subject').value.trim() || null,
            message: document.getElementById('email_message').value.trim() || null,
        };
        const result = await Api.post(`${API}/email`, payload, { timeoutMs: 600000 });
        Auth.showAlert('alert-area', result.message || 'Email sent.', 'success');
        setStatus(result.message || 'Email sent.');
    } catch (e) {
        Auth.showAlert('alert-area', e.message || 'Email failed.', 'danger');
        setStatus(e.message || 'Email failed.', true);
    } finally {
        btn.disabled = false;
        btn.innerHTML = original;
    }
}

function clearForm() {
    document.getElementById('suppress_zero_bal').checked = false;
    document.getElementById('complete_report').checked = false;
    document.getElementById('show_manual_id').checked = true;
    document.getElementById('store_ledger').checked = false;
    document.getElementById('print_amount').checked = false;
    document.getElementById('sort_by').value = 'ac_id';
    document.getElementById('sort_order').value = 'asc';
    document.getElementById('email_subject').value = '';
    document.getElementById('email_message').value = '';
    toggleCompleteReport();
    setDefaultDates();
    setDefaultItems();
    if (lastPdfUrl) URL.revokeObjectURL(lastPdfUrl);
    lastPdfUrl = null;
    document.getElementById('btn-open-pdf').classList.add('d-none');
    setStatus('');
}
