const API = '/api/v1/purchase-automation';
const PUR_API = '/api/v1/fin-pur';

let selectedFile = null;
let review = null;
let lines = [];
let supplierMeta = {
    stax_type: 0,
    address: '',
    stax_id: '',
    city_id: 0,
};
let searchModal = null;
let searchMode = 'supplier';
let searchLineIndex = -1;

document.addEventListener('DOMContentLoaded', async () => {
    await Auth.requireAuth();
    if (!Auth.hasPermission('inventory.fin_pur.create') && !Auth.hasPermission('inventory.fin_pur.view')) {
        document.getElementById('pa-app').innerHTML = '<div class="alert alert-danger">Access denied.</div>';
        return;
    }
    searchModal = new bootstrap.Modal(document.getElementById('searchModal'));
    bindEvents();
    await loadInstructions();
});

function on(id, event, handler) {
    const el = document.getElementById(id);
    if (!el) {
        console.warn(`[purchase-automation] element #${id} not found — hard refresh the page (Ctrl+F5).`);
        return null;
    }
    el.addEventListener(event, handler);
    return el;
}

function bindEvents() {
    const drop = document.getElementById('drop-zone');
    const fileInput = document.getElementById('invoice-file');

    drop.addEventListener('click', () => fileInput.click());
    drop.addEventListener('dragover', (e) => {
        e.preventDefault();
        drop.classList.add('dragover');
    });
    drop.addEventListener('dragleave', () => drop.classList.remove('dragover'));
    drop.addEventListener('drop', (e) => {
        e.preventDefault();
        drop.classList.remove('dragover');
        if (e.dataTransfer.files?.[0]) setFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', () => {
        if (fileInput.files?.[0]) setFile(fileInput.files[0]);
    });

    on('btn-process', 'click', processInvoice);
    on('btn-save', 'click', savePurchase);
    on('btn-reset', 'click', resetAll);
    on('btn-save-instructions', 'click', saveInstructions);
    on('btn-import-json', 'click', importJson);
    on('btn-clear-json', 'click', () => {
        document.getElementById('paste-json').value = '';
        document.getElementById('json-status').textContent = '';
    });
    on('btn-supplier-search', 'click', () => openSearch('supplier'));
    on('supplier_id', 'change', loadSupplier);
    on('search-query', 'input', debounce(runSearch, 250));
    on('fetch-instructions', 'change', () => {
        document.getElementById('instructions-status').textContent = 'Unsaved changes — Save or Process to keep.';
    });

    document.getElementById('lines-body').addEventListener('click', (e) => {
        const btn = e.target.closest('[data-action]');
        if (!btn) return;
        const idx = Number(btn.closest('tr')?.dataset.index);
        const action = btn.getAttribute('data-action');
        if (action === 'item-search') {
            searchLineIndex = idx;
            openSearch('item');
        } else if (action === 'delete') {
            if (!confirm('Remove this line from review?')) return;
            lines.splice(idx, 1);
            renderLines();
        }
    });
    document.getElementById('lines-body').addEventListener('change', (e) => {
        const tr = e.target.closest('tr');
        if (!tr) return;
        const idx = Number(tr.dataset.index);
        if (!Number.isFinite(idx) || !lines[idx]) return;
        const field = e.target.dataset.field;
        if (!field) return;
        if (field === 'item_id') {
            lines[idx].item_id = num(e.target.value) || null;
            resolveItem(idx);
            return;
        }
        lines[idx][field] = ['source_description', 'item_title', 'remarks'].includes(field)
            ? e.target.value
            : num(e.target.value);
        recalcLine(idx);
        renderLines();
    });
}

function setFile(file) {
    const okTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/webp'];
    const name = (file.name || '').toLowerCase();
    const typeOk = okTypes.includes(file.type)
        || name.endsWith('.pdf') || name.endsWith('.jpg') || name.endsWith('.jpeg')
        || name.endsWith('.png') || name.endsWith('.webp');
    if (!typeOk) {
        showAlert('Upload a PDF, JPG, PNG, or WebP file.', 'danger');
        return;
    }
    if (file.size > 15 * 1024 * 1024) {
        showAlert('File size must not exceed 15 MB.', 'danger');
        return;
    }
    selectedFile = file;
    document.getElementById('file-meta').classList.remove('d-none');
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-size').textContent = `${(file.size / 1024).toFixed(1)} KB`;
    document.getElementById('btn-process').disabled = !Auth.hasPermission('inventory.fin_pur.create')
        && !Auth.hasPermission('auth.admin.full');

    const img = document.getElementById('img-preview');
    const pdf = document.getElementById('pdf-preview');
    img.classList.add('d-none');
    pdf.classList.add('d-none');
    const url = URL.createObjectURL(file);
    if (file.type === 'application/pdf' || name.endsWith('.pdf')) {
        pdf.src = url;
        pdf.classList.remove('d-none');
    } else {
        img.src = url;
        img.classList.remove('d-none');
    }
}

async function loadInstructions() {
    try {
        const data = await Api.get(`${API}/instructions`);
        document.getElementById('fetch-instructions').value = data.instructions || '';
        document.getElementById('instructions-status').textContent =
            data.instructions ? 'Saved instructions loaded (Manual ID first · items only).' : 'No saved instructions yet.';
    } catch (err) {
        document.getElementById('instructions-status').textContent = 'Could not load saved instructions.';
    }
}

async function saveInstructions() {
    const instructions = document.getElementById('fetch-instructions').value || '';
    try {
        const data = await Api.put(`${API}/instructions`, { instructions });
        document.getElementById('instructions-status').textContent = data.message || 'Saved.';
        showAlert(data.message || 'Instructions saved.', 'success');
    } catch (err) {
        showAlert(err.message || 'Could not save instructions.', 'danger');
    }
}

async function importJson() {
    const text = (document.getElementById('paste-json').value || '').trim();
    const statusEl = document.getElementById('json-status');
    if (!text) {
        showAlert('Paste the invoice JSON first.', 'warning');
        return;
    }
    if (!Auth.hasPermission('inventory.fin_pur.create') && !Auth.hasPermission('auth.admin.full')) {
        showAlert('Create permission required to fill the grid.', 'danger');
        return;
    }
    const btn = document.getElementById('btn-import-json');
    btn.disabled = true;
    statusEl.textContent = 'Matching items by manual ID...';
    try {
        const result = await Api.post(`${API}/import-json`, { json_text: text });
        applyReview(result);
        const unmatched = (result.lines || []).filter((l) => !l.item_id).length;
        statusEl.textContent = unmatched
            ? `${result.lines.length} line(s) filled · ${unmatched} need an item.`
            : `${result.lines.length} line(s) filled · all matched by manual ID.`;
        showAlert(
            unmatched
                ? `Grid filled from JSON. ${unmatched} line(s) had no manual ID match — pick items before Save.`
                : 'Grid filled from JSON. Every line matched on manual ID.',
            unmatched ? 'warning' : 'success',
        );
        document.getElementById('step-review').scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
        statusEl.textContent = 'Import failed.';
        showAlert(err.message || 'Could not import JSON.', 'danger');
    } finally {
        btn.disabled = false;
    }
}

async function processInvoice() {
    if (!selectedFile) return;
    if (!Auth.hasPermission('inventory.fin_pur.create') && !Auth.hasPermission('auth.admin.full')) {
        showAlert('Create permission required to process invoices.', 'danger');
        return;
    }
    const btn = document.getElementById('btn-process');
    const wrap = document.getElementById('process-progress-wrap');
    const bar = document.getElementById('process-progress');
    btn.disabled = true;
    wrap.classList.remove('d-none');
    setProgress(bar, 15, 'Uploading');
    try {
        const form = new FormData();
        form.append('file', selectedFile);
        form.append('instructions', document.getElementById('fetch-instructions').value || '');
        setProgress(bar, 40, '13-stage pipeline');
        const headers = {};
        const token = Api.getToken();
        if (token) headers.Authorization = `Bearer ${token}`;
        const controller = new AbortController();
        const timer = window.setTimeout(() => controller.abort(), 240000);
        let response;
        try {
            response = await fetch(`${API}/process`, {
                method: 'POST',
                headers,
                body: form,
                credentials: 'include',
                signal: controller.signal,
            });
        } finally {
            clearTimeout(timer);
        }
        const raw = await response.text();
        let result;
        try {
            result = raw ? JSON.parse(raw) : {};
        } catch {
            result = { detail: `Server returned an unreadable response (${response.status}).` };
        }
        if (!response.ok) {
            const detail = typeof result.detail === 'string'
                ? result.detail
                : Array.isArray(result.detail)
                    ? result.detail.map((e) => e.msg || JSON.stringify(e)).join(', ')
                    : result.message || 'Process failed.';
            throw new Error(detail);
        }
        setProgress(bar, 90, 'Matching items');
        applyReview(result);
        document.getElementById('instructions-status').textContent = 'Instructions saved with Process.';
        setProgress(bar, 100, 'Done');
        showAlert('Invoice processed. Review carefully, then click Save Purchase.', 'success');
    } catch (err) {
        showAlert(err.message || 'Process failed.', 'danger');
        setProgress(bar, 0, 'Failed');
    } finally {
        btn.disabled = false;
        setTimeout(() => wrap.classList.add('d-none'), 800);
    }
}

function applyReview(data) {
    review = data;
    lines = (data.lines || []).map((l) => ({ ...l }));
    const s = data.supplier || {};
    document.getElementById('step-review').classList.remove('d-none');
    document.getElementById('supplier_id').value = s.supplier_id || '';
    document.getElementById('supplier_title').value = s.vendor_title || '';
    document.getElementById('registration').value = s.registration || '';
    document.getElementById('doc_date').value = data.doc_date || new Date().toISOString().slice(0, 10);
    document.getElementById('gp_id').value = data.gp_id || '';
    document.getElementById('remarks').value = data.remarks || 'Nil';
    document.getElementById('payment_type').value = String(data.payment_type ?? 0);
    document.getElementById('ai_model').value = data.model || '';
    document.getElementById('ocr-text').value = data.ocr_text || '';
    document.getElementById('ocr-engines').textContent =
        (data.ocr_engines && data.ocr_engines.length) ? data.ocr_engines.join(' + ') : '—';
    document.getElementById('document_class').value =
        `${data.document_class || '—'} (${((data.document_class_score || 0) * 100).toFixed(0)}%)`;
    const fin = data.financials || {};
    document.getElementById('financials-box').textContent =
        `Gross ${fmtMoney(fin.gross_amount)} · Disc ${fmtMoney(fin.discount)} · Tax ${fmtMoney(fin.tax)}` +
        ` · AdvTax ${fmtMoney(fin.advance_tax)} · Net ${fmtMoney(fin.net_amount)} · Grand ${fmtMoney(fin.grand_total)}` +
        (fin.claimed_grand_total
            ? `  |  printed claimed Grand ${fmtMoney(fin.claimed_grand_total)}`
            : '');
    const stages = (data.stage_trace || []).filter((t) => t.stage_id > 0);
    document.getElementById('stage-trace-summary').textContent = stages.length
        ? stages.map((t) => `${t.stage_id}${t.ok ? '' : '!'}`).join('→')
        : '—';
    setConfidence(document.getElementById('supplier-conf'), s.match_confidence || 'none');
    if (s.requires_confirmation) {
        document.getElementById('supplier_id').classList.add('pa-needs-confirm');
    } else {
        document.getElementById('supplier_id').classList.remove('pa-needs-confirm');
    }
    supplierMeta = {
        stax_type: s.stax_type || 0,
        address: s.address || '',
        stax_id: s.stax_id || '',
        city_id: s.city_id || 0,
    };

    const box = document.getElementById('warnings-box');
    if (data.warnings?.length) {
        box.classList.remove('d-none');
        box.innerHTML = `<strong>Warnings</strong><ul class="mb-0">${data.warnings.map((w) => `<li>${escapeHtml(w)}</li>`).join('')}</ul>`;
    } else {
        box.classList.add('d-none');
        box.innerHTML = '';
    }
    const vbox = document.getElementById('validation-box');
    const validations = data.validations || [];
    if (validations.length) {
        vbox.classList.remove('d-none');
        vbox.innerHTML = `<strong>Validation (printed totals never trusted)</strong><ul class="mb-0">${
            validations.map((v) => `<li><span class="badge text-bg-${v.severity === 'error' ? 'danger' : 'warning'}">${escapeHtml(v.severity)}</span> ${escapeHtml(v.message)}</li>`).join('')
        }</ul>`;
    } else {
        vbox.classList.add('d-none');
        vbox.innerHTML = '';
    }
    renderLines();
    document.getElementById('step-review').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderLines() {
    const body = document.getElementById('lines-body');
    body.innerHTML = lines.map((l, i) => `
        <tr data-index="${i}" class="${l.requires_confirmation ? 'pa-row-confirm' : ''}">
            <td>${i + 1}</td>
            <td>
                <div class="small">${escapeHtml(l.source_description || '')}</div>
                <div class="text-muted small">code: ${escapeHtml(l.printed_product_code || '—')}
                    · hw: ${escapeHtml(l.handwritten_manual_id || '—')}
                    · bc: ${escapeHtml(l.source_barcode || '—')}</div>
            </td>
            <td><input data-field="item_id" class="${l.requires_confirmation ? 'pa-needs-confirm' : ''}" value="${l.item_id ?? ''}" style="width:110px"></td>
            <td><input data-field="item_title" value="${escapeAttr(l.item_title || '')}" style="width:180px"></td>
            <td><input data-field="qty" type="number" step="0.01" value="${l.qty ?? 0}" style="width:70px"></td>
            <td><input data-field="rate" type="number" step="0.0001" value="${l.rate ?? 0}" style="width:80px"></td>
            <td><input data-field="pur_amt" type="number" step="0.01" value="${l.pur_amt ?? 0}" style="width:80px"></td>
            <td><input data-field="stax_rate" type="number" step="0.01" value="${l.stax_rate ?? 0}" style="width:60px"></td>
            <td><input data-field="stax_amt" type="number" step="0.01" value="${l.stax_amt ?? 0}" style="width:70px"></td>
            <td><input data-field="disc_amt" type="number" step="0.01" value="${l.disc_amt ?? 0}" style="width:70px"></td>
            <td><input data-field="disc_amt_oi" type="number" step="0.01" value="${l.disc_amt_oi ?? 0}" style="width:70px"></td>
            <td><span class="pa-conf-${l.match_confidence || 'none'}">${l.match_confidence || 'none'}</span>
                <div class="tiny text-muted">${escapeHtml(l.match_method || '')} ${(l.match_score != null ? `(${Number(l.match_score).toFixed(2)})` : '')}</div>
                ${l.requires_confirmation ? '<div class="tiny text-danger">confirm</div>' : ''}</td>
            <td class="text-nowrap">
                <button type="button" class="btn btn-outline-secondary btn-sm" data-action="item-search" title="Find item">...</button>
                <button type="button" class="btn btn-outline-danger btn-sm" data-action="delete" title="Remove line">×</button>
            </td>
        </tr>
    `).join('');

    const unmatched = lines.filter((l) => !l.item_id).length;
    const needConfirm = lines.filter((l) => l.requires_confirmation).length;
    document.getElementById('line-summary').textContent =
        `${lines.length} line(s)` +
        (unmatched ? ` · ${unmatched} unmatched` : ' · all matched') +
        (needConfirm ? ` · ${needConfirm} need confirmation` : '');
}

function recalcLine(idx) {
    const l = lines[idx];
    if (!l) return;
    if (!num(l.pur_amt) && num(l.qty) && num(l.rate)) {
        l.pur_amt = round2(num(l.qty) * num(l.rate));
    }
    if (num(l.pur_amt) && num(l.disc_amt)) {
        l.disc_per = round2((num(l.disc_amt) / num(l.pur_amt)) * 100);
    }
    if (num(l.pur_amt) && num(l.disc_amt_oi)) {
        l.disc_per_oi = round2((num(l.disc_amt_oi) / num(l.pur_amt)) * 100);
    }
    l.total_amt = round2(((num(l.pur_amt) + num(l.stax_amt)) - num(l.disc_amt)) - num(l.disc_amt_oi));
}

async function resolveItem(idx) {
    const id = lines[idx]?.item_id;
    if (!id) {
        lines[idx].item_title = lines[idx].source_description || '';
        lines[idx].match_confidence = 'none';
        renderLines();
        return;
    }
    try {
        const item = await Api.get(`${PUR_API}/items/by-id/${id}`);
        lines[idx].item_id = item.item_id;
        lines[idx].item_title = item.item_title;
        lines[idx].co_id = item.co_id;
        lines[idx].match_method = 'manual';
        lines[idx].match_confidence = 'high';
        renderLines();
    } catch (err) {
        showAlert(err.message, 'warning');
    }
}

async function loadSupplier() {
    const id = parseInt(document.getElementById('supplier_id').value, 10);
    if (!id) return;
    try {
        const s = await Api.get(`${PUR_API}/suppliers/${id}`);
        document.getElementById('supplier_title').value = s.vendor_title;
        document.getElementById('registration').value = s.registration || '';
        setConfidence(document.getElementById('supplier-conf'), 'high');
        supplierMeta = {
            stax_type: s.registration === 'Registered' ? 0 : 1,
            address: s.address || '',
            stax_id: s.stax_id || '',
            city_id: s.city_id || 0,
        };
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

async function savePurchase() {
    if (!Auth.hasPermission('inventory.fin_pur.create') && !Auth.hasPermission('auth.admin.full')) {
        showAlert('Create permission required to Save Purchase.', 'danger');
        return;
    }
    const supplierId = parseInt(document.getElementById('supplier_id').value, 10);
    if (!supplierId) {
        showAlert('Select a supplier before Save Purchase.', 'warning');
        return;
    }
    if (!lines.length) {
        showAlert('No lines to save.', 'warning');
        return;
    }
    const bad = lines.find((l) => !l.item_id || !num(l.qty));
    if (bad) {
        showAlert('Every line needs Item ID and Quantity. Fix unmatched lines first.', 'warning');
        return;
    }
    if (!confirm('Save this purchase into Fin_Pur (same as Purchase Receipt Save)?')) return;

    const charges = review?.charges || {};
    const payload = {
        supplier_id: supplierId,
        doc_date: document.getElementById('doc_date').value,
        remarks: document.getElementById('remarks').value || 'Nil',
        payment_type: parseInt(document.getElementById('payment_type').value, 10) || 0,
        stax_type: supplierMeta.stax_type || 0,
        gp_id: document.getElementById('gp_id').value || '',
        gp_time: new Date().toTimeString().slice(0, 5),
        vendor_title: document.getElementById('supplier_title').value || '',
        address: supplierMeta.address || '',
        stax_id: supplierMeta.stax_id || '',
        city_id: supplierMeta.city_id || 0,
        charges: {
            discount: num(charges.discount),
            claim: num(charges.claim),
            other_ded: num(charges.other_ded),
            loading: num(charges.loading),
            carriage: num(charges.carriage),
            other_charges: num(charges.other_charges),
        },
        lines: lines.map((l) => ({
            item_id: l.item_id,
            item_title: l.item_title,
            qty: num(l.qty),
            rate: num(l.rate),
            pur_amt: num(l.pur_amt) || round2(num(l.qty) * num(l.rate)),
            stax_rate: num(l.stax_rate),
            stax_amt: num(l.stax_amt),
            disc_per: num(l.disc_per),
            disc_amt: num(l.disc_amt),
            disc_per_oi: num(l.disc_per_oi),
            disc_amt_oi: num(l.disc_amt_oi),
            total_amt: num(l.total_amt),
            remarks: l.remarks || '',
            exp_date: l.exp_date || document.getElementById('doc_date').value,
            co_id: l.co_id || null,
            printed_description: l.source_description || '',
            printed_product_code: l.printed_product_code || '',
            handwritten_manual_id: l.handwritten_manual_id || '',
            source_barcode: l.source_barcode || '',
        })),
        learn_corrections: true,
    };

    try {
        const res = await Api.post(`${API}/save`, payload);
        showAlert(res.message || 'Purchase saved.', 'success');
        if (!res.needs_resave) {
            setTimeout(() => {
                if (confirm(`${res.doc_display || 'Purchase'} saved.\nOpen Purchase Receipt to view?`)) {
                    window.location.href = `/admin/fin-pur`;
                } else {
                    resetAll();
                }
            }, 300);
        }
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function resetAll() {
    selectedFile = null;
    review = null;
    lines = [];
    document.getElementById('invoice-file').value = '';
    document.getElementById('file-meta').classList.add('d-none');
    document.getElementById('btn-process').disabled = true;
    document.getElementById('step-review').classList.add('d-none');
    document.getElementById('warnings-box').classList.add('d-none');
    document.getElementById('pa-alert').innerHTML = '';
}

function openSearch(mode) {
    searchMode = mode;
    document.getElementById('search-title').textContent = mode === 'supplier' ? 'Supplier Search' : 'Item Search';
    document.getElementById('search-query').value = '';
    document.getElementById('search-body').innerHTML = '';
    searchModal.show();
    setTimeout(() => document.getElementById('search-query').focus(), 200);
}

async function runSearch() {
    const q = document.getElementById('search-query').value.trim();
    if (!q) return;
    try {
        const url = searchMode === 'supplier'
            ? `${PUR_API}/suppliers?q=${encodeURIComponent(q)}`
            : `${PUR_API}/items/search?q=${encodeURIComponent(q)}`;
        const rows = await Api.get(url);
        const body = document.getElementById('search-body');
        body.innerHTML = rows.map((r) => `
            <tr style="cursor:pointer" data-id="${r.id}" data-title="${escapeAttr(r.title)}">
                <td>${r.id}</td><td>${escapeHtml(r.title)}</td><td>${escapeHtml(r.extra || '')}</td>
            </tr>`).join('');
        body.querySelectorAll('tr').forEach((tr) => {
            tr.addEventListener('click', () => {
                const id = tr.dataset.id;
                searchModal.hide();
                if (searchMode === 'supplier') {
                    document.getElementById('supplier_id').value = id;
                    loadSupplier();
                } else if (searchLineIndex >= 0 && lines[searchLineIndex]) {
                    lines[searchLineIndex].item_id = num(id);
                    resolveItem(searchLineIndex);
                }
            });
        });
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function showAlert(msg, type = 'info') {
    document.getElementById('pa-alert').innerHTML =
        `<div class="alert alert-${type} alert-dismissible fade show py-2">${escapeHtml(msg)}
         <button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>`;
}

function setProgress(el, pct, label) {
    el.style.width = `${pct}%`;
    el.textContent = label ? `${pct}% · ${label}` : `${pct}%`;
}

function setConfidence(el, conf) {
    el.className = `pa-conf-${conf || 'none'}`;
    el.textContent = conf || 'none';
}

function num(v) {
    const n = parseFloat(v);
    return Number.isFinite(n) ? n : 0;
}
function round2(v) { return Math.round((v + Number.EPSILON) * 100) / 100; }
function fmtMoney(v) { return Number(v || 0).toFixed(2); }
function escapeHtml(s) {
    return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function escapeAttr(s) { return escapeHtml(s).replace(/`/g, ''); }
function debounce(fn, ms) {
    let t;
    return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}
