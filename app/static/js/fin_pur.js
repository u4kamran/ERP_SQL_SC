const API = '/api/v1/fin-pur';

let config = null;
let lines = [];
let selectedRow = -1;
let editRowIndex = -1;
let detailModal = null;
let dedModal = null;
let addrModal = null;
let searchModal = null;
let jsonModal = null;
let searchMode = 'supplier';

document.addEventListener('DOMContentLoaded', async () => {
    await Auth.requireAuth();
    if (!Auth.hasPermission('inventory.fin_pur.view')) {
        document.getElementById('pur-app').innerHTML = '<div class="alert alert-danger">Access denied.</div>';
        return;
    }

    detailModal = new bootstrap.Modal(document.getElementById('detailModal'));
    dedModal = new bootstrap.Modal(document.getElementById('dedModal'));
    addrModal = new bootstrap.Modal(document.getElementById('addrModal'));
    searchModal = new bootstrap.Modal(document.getElementById('searchModal'));
    jsonModal = new bootstrap.Modal(document.getElementById('jsonModal'));

    document.getElementById('TxtDocDAte').value = todayISO();
    document.getElementById('d_TxtExpDate').value = todayISO();
    bindEvents();
    await loadConfig();
    clearForm();
    document.getElementById('TxtDocID').focus();
});

function todayISO() {
    return new Date().toISOString().slice(0, 10);
}

function money(n) {
    const v = Number(n) || 0;
    return v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function num(n) {
    const v = parseFloat(n);
    return Number.isFinite(v) ? v : 0;
}

function showAlert(msg, type = 'info') {
    const el = document.getElementById('alert-area');
    el.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show py-2" role="alert">${msg}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>`;
}

function setStatus(text) {
    document.getElementById('status-label').textContent = text;
}

function bindEvents() {
    document.getElementById('btn-load-doc').addEventListener('click', loadDocument);
    document.getElementById('TxtDocID').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); loadDocument(); }
    });
    document.getElementById('TxtID').addEventListener('change', validateSupplier);
    document.getElementById('TxtID').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); validateSupplier(); }
    });
    document.getElementById('btn-search-supplier').addEventListener('click', () => openSearch('supplier'));

    document.getElementById('CmdAddTrans').addEventListener('click', () => openDetail(false));
    document.getElementById('CmdSave').addEventListener('click', saveDocument);
    document.getElementById('CmdClear').addEventListener('click', clearForm);
    document.getElementById('CmdDelete').addEventListener('click', deleteDocument);
    document.getElementById('CmdClose').addEventListener('click', () => { window.location.href = '/dashboard'; });
    document.getElementById('CmdShowAddr').addEventListener('click', () => addrModal.show());
    document.getElementById('CmdDiscount').addEventListener('click', openDedModal);
    document.getElementById('CmdShowItem').addEventListener('click', () => showAlert('Show Item grid — use Item Master (VB6) for full stock browse.', 'info'));
    document.getElementById('cmdPurOrder').addEventListener('click', () => { window.location.href = '/admin/fin-inv-order'; });
    document.getElementById('CmdPasteJson').addEventListener('click', openJsonModal);
    document.getElementById('json-fill').addEventListener('click', fillGridFromJson);
    document.getElementById('json-clear').addEventListener('click', () => {
        document.getElementById('json-input').value = '';
        document.getElementById('json-report').innerHTML = '';
    });
    document.getElementById('cmdAssignCo').addEventListener('click', assignCo);

    document.getElementById('VGrid-body').addEventListener('dblclick', (e) => {
        if (e.target.closest('.pur-row-actions')) return;
        const tr = e.target.closest('tr');
        if (!tr) return;
        selectedRow = Number(tr.dataset.index);
        openDetail(true);
    });
    document.getElementById('VGrid-body').addEventListener('click', (e) => {
        const actionBtn = e.target.closest('[data-grid-action]');
        if (actionBtn) {
            e.preventDefault();
            e.stopPropagation();
            const idx = Number(actionBtn.closest('tr')?.dataset.index);
            if (!Number.isFinite(idx) || idx < 0) return;
            selectedRow = idx;
            const action = actionBtn.getAttribute('data-grid-action');
            if (action === 'modify') {
                openDetail(true);
            } else if (action === 'delete') {
                deleteGridRow(idx);
            }
            return;
        }
        const tr = e.target.closest('tr');
        if (!tr) return;
        selectedRow = Number(tr.dataset.index);
        renderGrid();
    });
    document.getElementById('VGrid').addEventListener('keydown', (e) => {
        if (e.key === 'Delete' && selectedRow >= 0 && !e.target.matches('input, textarea')) {
            e.preventDefault();
            deleteGridRow(selectedRow);
        }
    });

    // Ded modal — Fin_PurDed
    ['TxtDiscount', 'TxtClaim', 'TxtOtherDed', 'TxtCarriage', 'TxtLoading', 'TxtOtherCharges'].forEach((id) => {
        document.getElementById(id).addEventListener('input', mTotalsDed);
    });
    document.getElementById('ded-save').addEventListener('click', saveDed);
    document.getElementById('ded-clear').addEventListener('click', clearDed);

    // Detail modal
    document.getElementById('d_CmdSave').addEventListener('click', saveDetailLine);
    document.getElementById('d_CmdClear').addEventListener('click', clearDetail);
    document.getElementById('d_CmdItem').addEventListener('click', () => openSearch('item'));
    document.getElementById('d_btn_item_search').addEventListener('click', () => openSearch('item'));
    document.getElementById('d_CmdBalance').addEventListener('click', () => showAlert(`Stock: ${document.getElementById('d_lblStock').textContent}`, 'info'));

    document.getElementById('d_TxtID').addEventListener('change', () => loadItemBy('id'));
    document.getElementById('d_Text1').addEventListener('change', () => loadItemBy('manual'));
    document.getElementById('d_txtBarcode').addEventListener('change', () => loadItemBy('barcode'));
    document.getElementById('d_txtBarcodeWS').addEventListener('change', () => loadItemBy('ws'));
    document.getElementById('d_txtCoID').addEventListener('change', validateCoId);

    ['d_TxtQty', 'd_TxtRate', 'd_txtDiscAmt', 'd_TxtStaxRate', 'd_TxtStaxAmount', 'd_txtOffInvDiscAmt'].forEach((id) => {
        document.getElementById(id).addEventListener('change', calcRate);
        document.getElementById(id).addEventListener('input', calcRate);
    });

    document.getElementById('search-query').addEventListener('input', debounce(runSearch, 250));

    // Enter key → next field (EnterKeyEnable)
    document.getElementById('pur-app').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.target.matches('input, select') && e.target.id !== 'TxtDocID') {
            e.preventDefault();
            focusNext(e.target);
        }
    });
    document.getElementById('detailModal').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.target.matches('input, select')) {
            e.preventDefault();
            focusNext(e.target, document.getElementById('detailModal'));
        }
    });
}

function focusNext(el, root = document) {
    const focusable = [...root.querySelectorAll('input:not([disabled]):not([type=hidden]), select:not([disabled]), button:not([disabled])')];
    const idx = focusable.indexOf(el);
    if (idx >= 0 && idx < focusable.length - 1) focusable[idx + 1].focus();
}

function debounce(fn, ms) {
    let t;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), ms);
    };
}

async function loadConfig() {
    try {
        config = await Api.get(`${API}/config`);
        if (config.company_name) {
            // keep banner as Purchase Receipt; status shows company
            setStatus(config.company_name);
        }
        if (config.is_sa) {
            document.getElementById('sa-buttons').classList.remove('d-none');
        }
        if (!config.book_ok) {
            showAlert(config.book_message || 'Book permission issue', 'warning');
        }
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function clearForm() {
    lines = [];
    selectedRow = -1;
    editRowIndex = -1;
    document.getElementById('TxtDocID').disabled = false;
    document.getElementById('TxtDocID').value = '';
    document.getElementById('TxtID').disabled = false;
    document.getElementById('TxtID').value = '';
    document.getElementById('TxtTitle').textContent = '—';
    document.getElementById('LblRegistration').textContent = '';
    document.getElementById('TxtRemarks').value = '';
    document.getElementById('TxtDocDAte').value = todayISO();
    document.getElementById('TxtGPID').value = '';
    document.getElementById('TxtTime').value = '';
    document.getElementById('CboPayment').value = '0';
    document.getElementById('serial_no').value = '';
    document.getElementById('found_flag').value = '0';
    ['HDiscount', 'HClaim', 'HOtherDed', 'HLoading', 'HCarriage', 'HOtherCharges'].forEach((id) => {
        document.getElementById(id).value = '0';
    });
    document.getElementById('TxtDesc').value = '';
    document.getElementById('TxtAddress').value = '';
    document.getElementById('TxtStaxID').value = '';
    document.getElementById('TxtCityID').value = '';
    document.getElementById('TxtCityTitle').value = '';
    setButtons(false);
    renderGrid();
    updateBalance();
    setStatus('Ready');
}

function setButtons(enabled) {
    document.getElementById('CmdAddTrans').disabled = !enabled;
    document.getElementById('CmdShowAddr').disabled = !enabled;
    document.getElementById('CmdDiscount').disabled = !enabled;
    document.getElementById('CmdSave').disabled = !enabled || lines.length === 0;
    document.getElementById('CmdDelete').disabled = !(enabled && document.getElementById('found_flag').value === '1'
        && Auth.hasPermission('inventory.fin_pur.delete'));
}

async function validateSupplier() {
    const id = parseInt(document.getElementById('TxtID').value, 10);
    if (!id) {
        setButtons(false);
        document.getElementById('TxtID').focus();
        return;
    }
    try {
        const s = await Api.get(`${API}/suppliers/${id}`);
        document.getElementById('TxtTitle').textContent = s.vendor_title;
        document.getElementById('TxtDesc').value = s.vendor_title;
        document.getElementById('TxtAddress').value = s.address || '';
        document.getElementById('TxtStaxID').value = s.stax_id || '';
        document.getElementById('TxtCityID').value = s.city_id || '';
        document.getElementById('TxtCityTitle').value = s.city_title || '';
        document.getElementById('LblRegistration').textContent = s.registration || '';
        setButtons(true);
        document.getElementById('CmdSave').disabled = lines.length === 0;
    } catch (err) {
        showAlert(err.message, 'danger');
        setButtons(false);
        document.getElementById('TxtID').focus();
    }
}

async function loadDocument() {
    const prodId = parseInt(document.getElementById('TxtDocID').value, 10);
    if (!prodId) return;
    if (config && !config.book_ok) {
        showAlert(config.book_message || 'Permission to Book is denied, Consult Administrator ... ', 'warning');
        return;
    }
    try {
        setStatus('Loading...');
        const doc = await Api.get(`${API}/documents/${prodId}`);
        document.getElementById('found_flag').value = '1';
        document.getElementById('serial_no').value = doc.serial_no;
        document.getElementById('TxtDocID').disabled = true;
        document.getElementById('TxtID').value = doc.supplier_id;
        document.getElementById('TxtID').disabled = !Auth.hasPermission('inventory.fin_pur.edit');
        document.getElementById('TxtTitle').textContent = doc.supplier_title;
        document.getElementById('LblRegistration').textContent = doc.registration;
        document.getElementById('TxtRemarks').value = doc.remarks || '';
        document.getElementById('TxtDocDAte').value = doc.doc_date;
        document.getElementById('TxtGPID').value = doc.gp_id || '';
        document.getElementById('TxtTime').value = doc.gp_time || '';
        document.getElementById('CboPayment').value = String(doc.payment_type || 0);
        document.getElementById('TxtDesc').value = doc.vendor_title || '';
        document.getElementById('TxtAddress').value = doc.address || '';
        document.getElementById('TxtStaxID').value = doc.stax_id || '';
        document.getElementById('TxtCityID').value = doc.city_id || '';
        document.getElementById('TxtCityTitle').value = doc.city_title || '';

        const c = doc.charges || {};
        document.getElementById('HDiscount').value = c.discount || 0;
        document.getElementById('HClaim').value = c.claim || 0;
        document.getElementById('HOtherDed').value = c.other_ded || 0;
        document.getElementById('HLoading').value = c.loading || 0;
        document.getElementById('HCarriage').value = c.carriage || 0;
        document.getElementById('HOtherCharges').value = c.other_charges || 0;

        lines = (doc.lines || []).map((l) => ({ ...l }));
        setButtons(true);
        renderGrid();
        updateBalance();
        // VB6 zeros LblDiscount after load adjustments
        document.getElementById('LblDiscount').textContent = '0.00';
        setStatus(`Loaded ${doc.doc_abbr} ${doc.prod_id}`);
    } catch (err) {
        showAlert(err.message, 'danger');
        setStatus('Ready');
    }
}

function renderGrid() {
    const body = document.getElementById('VGrid-body');
    body.innerHTML = lines.map((l, i) => `
        <tr data-index="${i}" class="${i === selectedRow ? 'selected' : ''}" tabindex="0">
            <td class="text-center">${i + 1}</td>
            <td>${l.item_id}</td>
            <td>${escapeHtml(l.item_title || '')}</td>
            <td class="pur-num">${money(l.qty)}</td>
            <td class="pur-num">${money(l.rate)}</td>
            <td class="pur-num">${money(l.pur_amt)}</td>
            <td class="pur-num">${money(l.stax_rate)}</td>
            <td class="pur-num">${money(l.stax_amt)}</td>
            <td class="pur-num">${money(l.disc_per)}</td>
            <td class="pur-num">${money(l.disc_amt)}</td>
            <td class="pur-num">${money(l.disc_per_oi)}</td>
            <td class="pur-num">${money(l.disc_amt_oi)}</td>
            <td class="pur-num">${money(l.total_amt)}</td>
            <td>${escapeHtml(l.remarks || '')}</td>
            <td>${l.exp_date || ''}</td>
            <td class="pur-row-actions">
                <button type="button" class="btn btn-outline-primary btn-sm" data-grid-action="modify" title="Modify line">Modify</button>
                <button type="button" class="btn btn-outline-danger btn-sm" data-grid-action="delete" title="Delete line">Delete</button>
            </td>
        </tr>
    `).join('');
    document.getElementById('CmdSave').disabled = !(num(document.getElementById('TxtID').value) && lines.length > 0);
}

function deleteGridRow(idx) {
    if (!Number.isFinite(idx) || idx < 0 || idx >= lines.length) return;
    const row = lines[idx];
    const label = `${row.item_id || ''} ${row.item_title || ''}`.trim() || `row ${idx + 1}`;
    if (!confirm(`Delete this purchase line?\n\n${label}`)) return;
    lines.splice(idx, 1);
    selectedRow = -1;
    editRowIndex = -1;
    renderGrid();
    updateBalance();
}

function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function updateBalance() {
    let nQty = 0, nAmount = 0, nSTax = 0, nDisc = 0, nOff = 0;
    lines.forEach((l) => {
        nQty += num(l.qty);
        nAmount += num(l.pur_amt);
        nSTax += num(l.stax_amt);
        nDisc += num(l.disc_amt);
        nOff += num(l.disc_amt_oi);
    });
    const nTAmount = nAmount - nDisc + nSTax;
    const mDiscount = num(document.getElementById('HDiscount').value)
        + num(document.getElementById('HClaim').value)
        + num(document.getElementById('HOtherDed').value);
    const mCharges = num(document.getElementById('HLoading').value)
        + num(document.getElementById('HCarriage').value)
        + num(document.getElementById('HOtherCharges').value);

    document.getElementById('mQty').textContent = money(nQty);
    document.getElementById('mAmount').textContent = money(nAmount);
    document.getElementById('mSalesTax').textContent = money(nSTax);
    document.getElementById('LDiscount').textContent = money(nDisc);
    document.getElementById('LStaxExclAmt').textContent = money(nAmount - nDisc);
    document.getElementById('LblOffInvDisc').textContent = money(nOff);
    document.getElementById('mTAmount').textContent = money(nTAmount);
    document.getElementById('LblDiscount').textContent = money(mDiscount);
    document.getElementById('LblCharges').textContent = money(mCharges);
    document.getElementById('LblDiff').textContent = money(mCharges - mDiscount);
    document.getElementById('mNetAmount').textContent = money(nTAmount - nOff - mDiscount + mCharges);
}

function openDedModal() {
    // Fin_PurDed Form_Load mapping
    document.getElementById('TxtDiscount').value = document.getElementById('HDiscount').value;
    document.getElementById('TxtClaim').value = document.getElementById('HClaim').value;
    document.getElementById('TxtOtherDed').value = document.getElementById('HOtherDed').value;
    document.getElementById('TxtCarriage').value = document.getElementById('HLoading').value;
    document.getElementById('TxtLoading').value = document.getElementById('HCarriage').value;
    document.getElementById('TxtOtherCharges').value = document.getElementById('HOtherCharges').value;
    mTotalsDed();
    dedModal.show();
}

function mTotalsDed() {
    const ded = num(document.getElementById('TxtDiscount').value)
        + num(document.getElementById('TxtClaim').value)
        + num(document.getElementById('TxtOtherDed').value);
    const chg = num(document.getElementById('TxtCarriage').value)
        + num(document.getElementById('TxtLoading').value)
        + num(document.getElementById('TxtOtherCharges').value);
    document.getElementById('LblTotalDed').textContent = money(ded);
    document.getElementById('LblTotalCharges').textContent = money(chg);
}

function saveDed() {
    mTotalsDed();
    // Fin_PurDed CmdSave double-swap
    document.getElementById('HDiscount').value = document.getElementById('TxtDiscount').value || 0;
    document.getElementById('HClaim').value = document.getElementById('TxtClaim').value || 0;
    document.getElementById('HOtherDed').value = document.getElementById('TxtOtherDed').value || 0;
    document.getElementById('HLoading').value = document.getElementById('TxtCarriage').value || 0;
    document.getElementById('HCarriage').value = document.getElementById('TxtLoading').value || 0;
    document.getElementById('HOtherCharges').value = document.getElementById('TxtOtherCharges').value || 0;
    document.getElementById('LblDiscount').textContent = document.getElementById('LblTotalDed').textContent;
    document.getElementById('LblCharges').textContent = document.getElementById('LblTotalCharges').textContent;
    dedModal.hide();
    updateBalance();
}

function clearDed() {
    ['TxtDiscount', 'TxtClaim', 'TxtOtherDed', 'TxtCarriage', 'TxtLoading', 'TxtOtherCharges'].forEach((id) => {
        document.getElementById(id).value = '';
    });
    mTotalsDed();
}

function openDetail(isEdit) {
    if (!num(document.getElementById('TxtID').value)) {
        showAlert('You must have a purchase Document.', 'warning');
        return;
    }
    clearDetail();
    editRowIndex = -1;
    if (isEdit && selectedRow >= 0 && lines[selectedRow]) {
        editRowIndex = selectedRow;
        const l = lines[selectedRow];
        document.getElementById('d_TxtID').value = l.item_id;
        document.getElementById('d_TxtTitle').textContent = l.item_title || '';
        document.getElementById('d_TxtQty').value = l.qty;
        document.getElementById('d_TxtRate').value = l.rate;
        document.getElementById('d_TxtAmount').textContent = money(l.pur_amt);
        document.getElementById('d_TxtStaxRate').value = l.stax_rate;
        document.getElementById('d_TxtStaxAmount').value = l.stax_amt;
        document.getElementById('d_txtDiscPer').value = l.disc_per;
        document.getElementById('d_txtDiscAmt').value = l.disc_amt;
        document.getElementById('d_TxtOffInvDiscPer').value = l.disc_per_oi;
        document.getElementById('d_txtOffInvDiscAmt').value = l.disc_amt_oi;
        document.getElementById('d_LblIncludedAmount').textContent = money(l.total_amt);
        document.getElementById('d_TxtsRemarks').value = l.remarks || '';
        document.getElementById('d_TxtExpDate').value = l.exp_date || todayISO();
        loadItemBy('id').then(() => calcRate());
    }
    detailModal.show();
    setTimeout(() => document.getElementById('d_TxtID').focus(), 200);
}

function clearDetail() {
    ['d_TxtID', 'd_TxtQty', 'd_TxtRate', 'd_txtMRP', 'd_txtDiscPer', 'd_TxtOffInvDiscPer',
        'd_TxtStaxRate', 'd_TxtsRemarks', 'd_txtNetCost', 'd_txtBarcode', 'd_txtBarcodeWS',
        'd_Text1', 'd_txtUnit', 'd_txtPQty', 'd_TxtPRate', 'd_txtCoID', 'd_txtDiscAmt',
        'd_TxtStaxAmount', 'd_txtOffInvDiscAmt'].forEach((id) => {
        document.getElementById(id).value = '';
    });
    document.getElementById('d_TxtExpDate').value = todayISO();
    document.getElementById('d_TxtTitle').textContent = 'Item Title';
    document.getElementById('d_TxtUomTitle').textContent = '—';
    document.getElementById('d_lblCoTitle').textContent = '';
    document.getElementById('d_TxtAmount').textContent = '0.00';
    document.getElementById('d_lblExcludAmt').textContent = '0.00';
    document.getElementById('d_LblOffInvIncludedAmt').textContent = '0.00';
    document.getElementById('d_LblIncludedAmount').textContent = '0.00';
    document.getElementById('d_lblSale').textContent = '0.00';
    document.getElementById('d_lblStock').textContent = '0';
}

async function loadItemBy(mode) {
    try {
        let url;
        if (mode === 'manual') {
            const v = num(document.getElementById('d_Text1').value);
            if (!v) return;
            url = `${API}/items/by-manual/${v}`;
        } else if (mode === 'barcode') {
            const v = document.getElementById('d_txtBarcode').value.trim();
            if (!v) return;
            url = `${API}/items/by-barcode/${encodeURIComponent(v)}`;
        } else if (mode === 'ws') {
            const v = document.getElementById('d_txtBarcodeWS').value.trim();
            if (!v) return;
            url = `${API}/items/by-ws-barcode/${encodeURIComponent(v)}`;
        } else {
            const v = document.getElementById('d_TxtID').value.trim();
            if (!v) return;
            if (v.length < 10) {
                showAlert('Invalid ID length ', 'warning');
                return;
            }
            url = `${API}/items/by-id/${v}`;
        }
        const item = await Api.get(url);
        fillItem(item);
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function fillItem(item) {
    document.getElementById('d_TxtID').value = item.item_id;
    document.getElementById('d_Text1').value = item.manual_id || '';
    document.getElementById('d_TxtTitle').textContent = item.item_title || '';
    document.getElementById('d_LblMainTitle').textContent = item.item_title || '';
    document.getElementById('d_txtCoID').value = item.co_id || '';
    document.getElementById('d_lblCoTitle').textContent = item.co_title || '';
    document.getElementById('d_lblSale').textContent = money(item.sales_rate);
    document.getElementById('d_lblStock').textContent = money(item.stock_qty);
    document.getElementById('d_txtMRP').value = item.mrp || 0;
    if (item.tp_rate) document.getElementById('d_TxtRate').value = item.tp_rate;
    document.getElementById('d_TxtStaxRate').value = item.stax_reg || 0;
    document.getElementById('d_TxtUomTitle').textContent = item.uom_abbr || '—';
    if (item.barcodeid) document.getElementById('d_txtBarcode').value = item.barcodeid;
    if (item.barcodeid_ws) document.getElementById('d_txtBarcodeWS').value = item.barcodeid_ws;
}

async function validateCoId() {
    // title filled via item load; leave as-is
}

function calcRate() {
    const rate = num(document.getElementById('d_TxtRate').value);
    const qty = num(document.getElementById('d_TxtQty').value);
    if (!qty) return;
    const mPurAmount = rate * qty;
    document.getElementById('d_TxtAmount').textContent = money(mPurAmount);

    let mDiscAmount = num(document.getElementById('d_txtDiscAmt').value);
    if (mPurAmount) {
        document.getElementById('d_txtDiscPer').value = ((mDiscAmount / mPurAmount) * 100).toFixed(2);
    }
    const mTaxAmount = num(document.getElementById('d_TxtStaxAmount').value);
    let mDiscOffInvAmt = num(document.getElementById('d_txtOffInvDiscAmt').value);
    if (mPurAmount) {
        document.getElementById('d_TxtOffInvDiscPer').value = ((mDiscOffInvAmt / mPurAmount) * 100).toFixed(2);
    }

    const mInclAmount = mPurAmount + mTaxAmount - mDiscAmount;
    const excl = mPurAmount - mDiscAmount;
    document.getElementById('d_lblExcludAmt').textContent = money(excl);
    const offIncl = excl + mTaxAmount;
    document.getElementById('d_LblOffInvIncludedAmt').textContent = money(offIncl);
    document.getElementById('d_LblIncludedAmount').textContent = money(mInclAmount - mDiscOffInvAmt);
    if (mPurAmount > 0 && qty) {
        document.getElementById('d_txtNetCost').value = ((mPurAmount - mDiscAmount - mDiscOffInvAmt) / qty).toFixed(2);
    }
}

async function saveDetailLine() {
    const itemId = num(document.getElementById('d_TxtID').value);
    const qty = num(document.getElementById('d_TxtQty').value);
    const coId = document.getElementById('d_txtCoID').value.trim();
    if (!itemId) {
        document.getElementById('d_TxtID').focus();
        return;
    }
    if (!qty) {
        showAlert('Invalid:  Please enter Quantity ...  ', 'warning');
        document.getElementById('d_TxtQty').focus();
        return;
    }
    if (!coId) {
        showAlert('Invalid:  Please enter Company ID ...  ', 'warning');
        document.getElementById('d_txtCoID').focus();
        return;
    }

    calcRate();
    const rate = num(document.getElementById('d_TxtRate').value);
    const purAmt = num(document.getElementById('d_TxtAmount').textContent.replace(/,/g, ''));
    const staxRate = num(document.getElementById('d_TxtStaxRate').value);
    const staxAmt = num(document.getElementById('d_TxtStaxAmount').value);
    const discPer = num(document.getElementById('d_txtDiscPer').value);
    const discAmt = num(document.getElementById('d_txtDiscAmt').value);
    const doiPer = num(document.getElementById('d_TxtOffInvDiscPer').value);
    const doiAmt = num(document.getElementById('d_txtOffInvDiscAmt').value);
    const totalAmt = num(document.getElementById('d_LblIncludedAmount').textContent.replace(/,/g, ''));
    const title = document.getElementById('d_TxtTitle').textContent;
    const remarks = document.getElementById('d_TxtsRemarks').value;
    const expDate = document.getElementById('d_TxtExpDate').value || todayISO();
    const mrp = num(document.getElementById('d_txtMRP').value);

    try {
        await Api.post(`${API}/detail-item-update`, {
            item_id: itemId,
            mrp,
            stax_rate: staxRate,
            stax_amt: staxAmt,
            qty,
            amount: purAmt,
            disc_amt: discAmt,
            off_inv_disc_amt: doiAmt,
            rate,
            co_id: parseInt(coId, 10) || 0,
        });
    } catch (err) {
        showAlert(err.message, 'warning');
    }

    if (editRowIndex < 0) {
        const dup = lines.some((l) => num(l.item_id) === itemId);
        if (dup) {
            showAlert('Duplicate: Item ID Already Exists .... ', 'warning');
            return;
        }
    }

    const row = {
        item_id: itemId,
        item_title: title,
        qty,
        rate,
        pur_amt: purAmt,
        stax_rate: staxRate,
        stax_amt: staxAmt,
        disc_per: discPer,
        disc_amt: discAmt,
        disc_per_oi: doiPer,
        disc_amt_oi: doiAmt,
        total_amt: totalAmt,
        remarks,
        exp_date: expDate,
    };

    if (editRowIndex >= 0) {
        lines[editRowIndex] = row;
    } else {
        lines.push(row);
    }
    editRowIndex = -1;
    detailModal.hide();
    renderGrid();
    updateBalance();
    clearDetail();
}

function openJsonModal() {
    document.getElementById('json-report').innerHTML = '';
    const hasSupplier = Boolean(num(document.getElementById('TxtID').value));
    document.getElementById('json-need-supplier').classList.toggle('d-none', hasSupplier);
    document.getElementById('json-fill').disabled = !hasSupplier;
    jsonModal.show();
    setTimeout(() => document.getElementById('json-input').focus(), 200);
}

function jsonPick(source, ...keys) {
    if (!source || typeof source !== 'object') return null;
    const lowered = {};
    Object.keys(source).forEach((k) => { lowered[k.trim().toLowerCase()] = source[k]; });
    for (const key of keys) {
        const v = lowered[key.toLowerCase()];
        if (v !== undefined && v !== null && v !== '') return v;
    }
    return null;
}

function jsonNum(v) {
    if (v === undefined || v === null || v === '') return 0;
    const n = parseFloat(String(v).replace(/,/g, '').trim());
    return Number.isFinite(n) ? n : 0;
}

function round2(v) {
    return Number((Number(v) || 0).toFixed(2));
}

function parsePastedJson(raw) {
    let text = (raw || '').trim();
    if (text.startsWith('```')) text = text.replace(/^```[a-zA-Z]*\s*/, '').replace(/\s*```$/, '').trim();
    if (!text) throw new Error('Paste the invoice JSON first.');
    let parsed;
    try {
        parsed = JSON.parse(text);
    } catch (err) {
        throw new Error(`Invalid JSON — ${err.message}`);
    }
    if (Array.isArray(parsed)) return { items: parsed, totals: {} };
    if (!parsed || typeof parsed !== 'object') {
        throw new Error('JSON must be an object with an "items" array, or an array of items.');
    }
    const items = ['items', 'lines', 'products', 'details', 'rows']
        .map((k) => parsed[k])
        .find((v) => Array.isArray(v) && v.length);
    if (!items) throw new Error('JSON has no items. Expected an "items" (or "lines"/"products") array.');
    return { items, totals: parsed.totals || {} };
}

/**
 * Fill the grid from pasted JSON. Every line goes through the same item
 * validation, duplicate check and Calc_Rate math as manual Add Trans. entry.
 * Nothing is written to the purchase document until the operator presses Save.
 */
async function fillGridFromJson() {
    if (!num(document.getElementById('TxtID').value)) {
        showAlert('You must have a purchase Document.', 'warning');
        return;
    }
    if (!Auth.hasPermission('inventory.fin_pur.create') && !Auth.hasPermission('inventory.fin_pur.edit')) {
        showAlert('Acess denied contact with administrator.', 'danger');
        return;
    }

    const report = document.getElementById('json-report');
    const btn = document.getElementById('json-fill');
    let payload;
    try {
        payload = parsePastedJson(document.getElementById('json-input').value);
    } catch (err) {
        report.innerHTML = `<div class="text-danger">${escapeHtml(err.message)}</div>`;
        return;
    }

    btn.disabled = true;
    setStatus('Filling grid from JSON...');
    const expDate = document.getElementById('TxtDocDAte').value || todayISO();
    const added = [];
    const skipped = [];

    for (let i = 0; i < payload.items.length; i += 1) {
        const raw = payload.items[i];
        const lineNo = jsonNum(jsonPick(raw, 'line', 'sr', 'no')) || i + 1;
        const label = String(jsonPick(raw, 'description', 'item_title', 'name') || `line ${lineNo}`);
        if (!raw || typeof raw !== 'object') {
            skipped.push({ lineNo, label, reason: 'Not an object.' });
            continue;
        }

        const manual = jsonNum(jsonPick(raw, 'manual_id', 'manualid', 'manual'));
        if (!manual) {
            skipped.push({ lineNo, label, reason: 'No manual_id in JSON.' });
            continue;
        }

        let item;
        try {
            item = await Api.get(`${API}/items/by-manual/${manual}`);
        } catch (err) {
            skipped.push({ lineNo, label, reason: `Manual ID ${manual}: ${err.message}` });
            continue;
        }
        const itemId = num(item.item_id);
        if (!itemId) {
            skipped.push({ lineNo, label, reason: `Manual ID ${manual} returned no Item ID.` });
            continue;
        }
        if (lines.some((l) => num(l.item_id) === itemId)) {
            skipped.push({ lineNo, label, reason: 'Duplicate: Item ID Already Exists .... ' });
            continue;
        }
        const coId = parseInt(item.co_id, 10) || 0;
        if (!coId) {
            skipped.push({ lineNo, label, reason: 'Invalid:  Please enter Company ID ...  ' });
            continue;
        }

        const qty = jsonNum(jsonPick(raw, 'qty', 'quantity'));
        if (!qty) {
            skipped.push({ lineNo, label, reason: 'Invalid:  Please enter Quantity ...  ' });
            continue;
        }

        const jsonAmount = jsonNum(jsonPick(raw, 'amount', 'value', 'line_total'));
        let rate = jsonNum(jsonPick(raw, 'rate', 'trade_price', 'price'));
        if (!rate && jsonAmount) rate = Number((jsonAmount / qty).toFixed(4));
        if (!rate) rate = num(item.tp_rate);
        if (!rate) {
            skipped.push({ lineNo, label, reason: 'No rate and no amount to derive it from.' });
            continue;
        }

        // Calc_Rate (Fin_PurD) — amount from Qty × Rate, then discount and tax
        const purAmt = round2(qty * rate);
        const discAmt = round2(jsonNum(jsonPick(raw, 'discount', 'disc_amt', 'disc')));
        const discPer = purAmt ? round2((discAmt / purAmt) * 100) : 0;
        const staxRate = num(item.stax_reg);
        const staxAmt = round2(jsonNum(jsonPick(raw, 'tax', 'stax_amt', 'sales_tax', 'gst')));
        const totalAmt = round2(purAmt + staxAmt - discAmt);
        const mrp = num(item.mrp);

        try {
            await Api.post(`${API}/detail-item-update`, {
                item_id: itemId,
                mrp,
                stax_rate: staxRate,
                stax_amt: staxAmt,
                qty,
                amount: purAmt,
                disc_amt: discAmt,
                off_inv_disc_amt: 0,
                rate,
                co_id: coId,
            });
        } catch (err) {
            showAlert(err.message, 'warning');
        }

        lines.push({
            item_id: itemId,
            item_title: item.item_title || label,
            qty,
            rate,
            pur_amt: purAmt,
            stax_rate: staxRate,
            stax_amt: staxAmt,
            disc_per: discPer,
            disc_amt: discAmt,
            disc_per_oi: 0,
            disc_amt_oi: 0,
            total_amt: totalAmt,
            remarks: String(jsonPick(raw, 'remarks', 'note') || ''),
            exp_date: expDate,
        });
        added.push({ lineNo, title: item.item_title, purAmt, jsonAmount });
    }

    selectedRow = -1;
    editRowIndex = -1;
    renderGrid();
    updateBalance();
    btn.disabled = false;
    setStatus('Ready');
    renderJsonReport(report, added, skipped, payload.totals);
}

function renderJsonReport(report, added, skipped, totals) {
    const parts = [];
    parts.push(`<div class="fw-semibold">Added ${added.length} line(s)${skipped.length ? `, skipped ${skipped.length}` : ''}.</div>`);

    const mismatched = added.filter((a) => a.jsonAmount && Math.abs(a.jsonAmount - a.purAmt) > 0.05);
    if (mismatched.length) {
        parts.push('<div class="text-warning-emphasis mt-1">Amount recalculated from Qty × Rate (JSON amount ignored):<ul class="mb-0">'
            + mismatched.map((a) => `<li>Line ${a.lineNo}: ${money(a.purAmt)} vs JSON ${money(a.jsonAmount)}</li>`).join('')
            + '</ul></div>');
    }

    const claimedGross = jsonNum(jsonPick(totals, 'gross_amount', 'gross', 'sub_total'));
    if (claimedGross) {
        const gross = added.reduce((sum, a) => sum + a.purAmt, 0);
        if (Math.abs(gross - claimedGross) > 0.05) {
            parts.push(`<div class="text-danger mt-1">Gross mismatch: grid ${money(gross)} vs JSON ${money(claimedGross)}. Check the skipped lines.</div>`);
        }
    }

    if (skipped.length) {
        parts.push('<div class="text-danger mt-1">Skipped:<ul class="mb-0">'
            + skipped.map((s) => `<li>Line ${s.lineNo} (${escapeHtml(s.label)}): ${escapeHtml(s.reason)}</li>`).join('')
            + '</ul></div>');
    } else {
        parts.push('<div class="text-success mt-1">All items matched on Manual ID. Review the grid, then press Save.</div>');
    }
    report.innerHTML = parts.join('');
}

async function saveDocument() {
    if (!lines.length) {
        showAlert('No transaction to slave ', 'warning');
        return;
    }
    if (!Auth.hasPermission('inventory.fin_pur.create') && !Auth.hasPermission('inventory.fin_pur.edit')) {
        showAlert('Acess denied contact with administrator.', 'danger');
        return;
    }
    const supplierId = parseInt(document.getElementById('TxtID').value, 10);
    if (!supplierId) {
        showAlert('You must have a purchase Document.', 'warning');
        return;
    }
    let remarks = document.getElementById('TxtRemarks').value.trim();
    if (!remarks) remarks = 'Nil';

    const reg = document.getElementById('LblRegistration').textContent;
    const staxType = reg === 'Registered' ? 0 : 1;
    const found = document.getElementById('found_flag').value === '1';
    const prodId = parseInt(document.getElementById('TxtDocID').value, 10) || null;

    const payload = {
        prod_id: found ? prodId : null,
        serial_no: found ? parseInt(document.getElementById('serial_no').value, 10) : null,
        doc_date: document.getElementById('TxtDocDAte').value,
        supplier_id: supplierId,
        remarks,
        payment_type: parseInt(document.getElementById('CboPayment').value, 10) || 0,
        stax_type: staxType,
        gp_id: document.getElementById('TxtGPID').value,
        gp_time: document.getElementById('TxtTime').value,
        vendor_title: document.getElementById('TxtDesc').value,
        address: document.getElementById('TxtAddress').value,
        stax_id: document.getElementById('TxtStaxID').value,
        city_id: parseInt(document.getElementById('TxtCityID').value, 10) || 0,
        charges: {
            discount: num(document.getElementById('HDiscount').value),
            claim: num(document.getElementById('HClaim').value),
            other_ded: num(document.getElementById('HOtherDed').value),
            loading: num(document.getElementById('HLoading').value),
            carriage: num(document.getElementById('HCarriage').value),
            other_charges: num(document.getElementById('HOtherCharges').value),
        },
        lines: lines.map((l) => ({
            item_id: l.item_id,
            item_title: l.item_title,
            qty: l.qty,
            rate: l.rate,
            pur_amt: l.pur_amt,
            stax_rate: l.stax_rate,
            stax_amt: l.stax_amt,
            disc_per: l.disc_per,
            disc_amt: l.disc_amt,
            disc_per_oi: l.disc_per_oi,
            disc_amt_oi: l.disc_amt_oi,
            total_amt: l.total_amt,
            remarks: l.remarks,
            exp_date: l.exp_date,
        })),
    };

    // VB6 CmdSave sets LblDiscount = 0 at start
    document.getElementById('LblDiscount').textContent = '0.00';

    try {
        setStatus('Saving...');
        const res = await Api.post(`${API}/documents`, payload);
        showAlert(res.message, res.needs_resave ? 'warning' : 'success');
        if (res.needs_resave) {
            document.getElementById('TxtDocID').value = res.prod_id;
            await loadDocument();
        } else {
            clearForm();
        }
        setStatus('Ready');
    } catch (err) {
        showAlert(err.message, 'danger');
        setStatus('Error');
    }
}

async function deleteDocument() {
    if (!Auth.hasPermission('inventory.fin_pur.delete')) {
        showAlert('Acess denied contact with administrator.', 'danger');
        return;
    }
    if (document.getElementById('found_flag').value !== '1') return;
    if (!confirm('Discarding voucher, Are you sure ?')) return;
    const prodId = parseInt(document.getElementById('TxtDocID').value, 10);
    try {
        const res = await Api.delete(`${API}/documents/${prodId}`);
        showAlert(res.message, 'success');
        clearForm();
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

async function assignCo() {
    const coId = parseInt(document.getElementById('txtCoID').value, 10);
    if (!coId) return;
    const itemIds = lines.map((l) => l.item_id);
    try {
        const res = await Api.post(`${API}/assign-co`, { co_id: coId, item_ids: itemIds });
        showAlert(res.message, 'success');
    } catch (err) {
        showAlert(err.message, 'danger');
    }
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
        const url = searchMode === 'supplier' ? `${API}/suppliers?q=${encodeURIComponent(q)}` : `${API}/items/search?q=${encodeURIComponent(q)}`;
        const rows = await Api.get(url);
        const body = document.getElementById('search-body');
        body.innerHTML = rows.map((r) => `
            <tr style="cursor:pointer" data-id="${r.id}">
                <td>${r.id}</td><td>${escapeHtml(r.title)}</td><td>${escapeHtml(r.extra || '')}</td>
            </tr>`).join('');
        body.querySelectorAll('tr').forEach((tr) => {
            tr.addEventListener('click', () => {
                const id = tr.dataset.id;
                searchModal.hide();
                if (searchMode === 'supplier') {
                    document.getElementById('TxtID').value = id;
                    validateSupplier();
                } else {
                    document.getElementById('d_TxtID').value = id;
                    loadItemBy('id');
                }
            });
        });
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}
