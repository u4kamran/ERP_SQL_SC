const API = '/api/v1/fin-inv-order';

/** VB6 grd(0) column semantics */
const F = {
    barcode: 'barcode_id',
    manual: 'manual_id',
    qty: 'qty',
    rate: 'rate',
    disc_per: 'disc_per',
};

const EDIT_FIELDS = [F.barcode, F.manual, F.qty, F.rate, F.disc_per];

let config = null;
let lines = [];
let selectedRow = 0;
let supplierItems = [];
let highlightedManualId = null;
let dedModal = null;
let addrModal = null;
let searchModal = null;
let searchMode = 'supplier';
let docLoaded = false;
let focusAfterRender = null; // { row, field }
let lastItemStock = 0;
let skipNextBlurResolve = false;
let lastValidatedSupplierId = null;

document.addEventListener('DOMContentLoaded', async () => {
    await Auth.requireAuth();
    if (!Auth.hasPermission('inventory.fin_inv_order.view')) {
        document.getElementById('po-app').innerHTML = '<div class="alert alert-danger">Access denied.</div>';
        return;
    }

    dedModal = new bootstrap.Modal(document.getElementById('dedModal'));
    addrModal = new bootstrap.Modal(document.getElementById('addrModal'));
    searchModal = new bootstrap.Modal(document.getElementById('searchModal'));

    document.getElementById('TxtDocDate').value = todayISO();
    bindEvents();
    await loadConfig();
    clearForm(false);
    document.getElementById('TxtDocID').focus();
});

function todayISO() {
    return new Date().toISOString().slice(0, 10);
}

function money(n, dec = 2) {
    const v = Number(n) || 0;
    return v.toLocaleString(undefined, { minimumFractionDigits: dec, maximumFractionDigits: dec });
}

function num(n) {
    const v = parseFloat(String(n).replace(/,/g, ''));
    return Number.isFinite(v) ? v : 0;
}

function manualMode() {
    return document.getElementById('chkBC').checked;
}

function showAlert(msg, type = 'info') {
    const el = document.getElementById('alert-area');
    el.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show py-2" role="alert">${msg.replace(/\n/g, '<br>')}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>`;
}

function setStatus(text) {
    document.getElementById('status-label').textContent = text;
}

function emptyLine() {
    return {
        barcode_id: '', manual_id: '', item_id: 0, item_title: '',
        qty: '', rate: '', amount: 0, disc_per: '', disc_amt: 0, net_amt: 0,
    };
}

function ensureTrailingRow() {
    if (!lines.length) lines.push(emptyLine());
    const last = lines[lines.length - 1];
    if (last.item_id) lines.push(emptyLine());
}

/** VB6: new items go to last row (Rows - 1) */
function targetRowForNewItem() {
    ensureTrailingRow();
    return lines.length - 1;
}

function bindEvents() {
    document.getElementById('btn-load-doc').addEventListener('click', loadDocument);
    document.getElementById('TxtDocID').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); loadDocument(); }
    });
    document.getElementById('TxtDocID').addEventListener('click', previewNextId);

    document.getElementById('TxtCustID').addEventListener('change', validateSupplier);
    document.getElementById('TxtCustID').addEventListener('blur', () => {
        const id = parseInt(document.getElementById('TxtCustID').value, 10) || 0;
        if (id !== lastValidatedSupplierId) validateSupplier();
    });
    document.getElementById('TxtCustID').addEventListener('input', () => {
        const id = parseInt(document.getElementById('TxtCustID').value, 10) || 0;
        if (id !== lastValidatedSupplierId) {
            lastValidatedSupplierId = null;
            setButtons(false);
        }
    });
    document.getElementById('TxtCustID').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); validateSupplier(); }
    });
    document.getElementById('btn-search-supplier').addEventListener('click', () => openSearch('supplier'));

    document.getElementById('CmdSave').addEventListener('click', saveDocument);
    document.getElementById('CmdClear').addEventListener('click', () => clearForm(true));
    document.getElementById('CmdDelete').addEventListener('click', deleteDocument);
    document.getElementById('CmdClose').addEventListener('click', () => { window.location.href = '/dashboard'; });
    document.getElementById('CmdPrint').addEventListener('click', printDocument);
    document.getElementById('CmdShowItem').addEventListener('click', toggleSupplierItems);
    document.getElementById('cmdPrintGrid').addEventListener('click', printSupplierGrid);
    document.getElementById('CmdDiscount').addEventListener('click', openDedModal);
    document.getElementById('CmdShowAddr').addEventListener('click', () => addrModal.show());
    document.getElementById('cmdVendor').addEventListener('click', () => showAlert('Vendor maintenance — frmVendor in VB6.', 'info'));
    document.getElementById('cmdItem').addEventListener('click', openItemFromSelection);
    document.getElementById('cmdAddItem').addEventListener('click', addSupplierItem);

    document.getElementById('txtManualID').addEventListener('input', previewManualTitle);
    document.getElementById('txtManualID').addEventListener('keydown', (e) => {
        if (e.key === 'F5') { e.preventDefault(); addSupplierItem(); }
    });

    document.getElementById('TxtCityID').addEventListener('change', () => {});

    ['TxtDiscount', 'TxtClaim', 'TxtOtherDed', 'TxtCarriage', 'TxtLoading', 'TxtOtherCharges'].forEach((id) => {
        document.getElementById(id).addEventListener('input', () => calcTotals());
    });
    document.getElementById('ded-save').addEventListener('click', saveDed);
    document.getElementById('ded-clear').addEventListener('click', clearDed);

    document.getElementById('search-query').addEventListener('input', debounce(runSearch, 250));

    const grd0 = document.getElementById('grd0-body');
    grd0.addEventListener('click', (e) => {
        if (e.target.closest('[data-del]')) return;
        const tr = e.target.closest('tr');
        if (!tr) return;
        selectedRow = Number(tr.dataset.index);
        updateRowSelection();
    });
    grd0.addEventListener('focusin', (e) => {
        const input = e.target.closest('.cell-in');
        if (!input) return;
        selectedRow = Number(input.dataset.row);
        updateRowSelection();
    });
    grd0.addEventListener('keydown', onGridKeydown);
    grd0.addEventListener('blur', onGridBlur, true);
    grd0.addEventListener('input', onGridInput);

    document.getElementById('chkBC').addEventListener('change', () => renderGrid());

    // F4 item search — capture phase so browser does not swallow it
    document.addEventListener('keydown', (e) => {
        if (e.key !== 'F4') return;
        const inGrid = e.target.closest('#grd0, #grd0-wrap');
        if (inGrid) {
            e.preventDefault();
            e.stopPropagation();
            openSearch('item');
        }
    }, true);

    document.getElementById('grd1-body').addEventListener('click', (e) => {
        if (e.target.closest('[data-rm]')) return;
        const tr = e.target.closest('tr[data-manual]');
        if (!tr) return;
        addFromSupplierGrid(tr.dataset.manual);
    });
    document.getElementById('grd1-body').addEventListener('keydown', (e) => {
        if (e.key !== 'Enter') return;
        const tr = e.target.closest('tr[data-manual]');
        if (!tr) return;
        e.preventDefault();
        addFromSupplierGrid(tr.dataset.manual);
    });
    document.getElementById('grd1-body').addEventListener('dblclick', (e) => {
        if (e.target.closest('[data-rm]')) return;
        const tr = e.target.closest('tr[data-manual]');
        if (!tr) return;
        addFromSupplierGrid(tr.dataset.manual);
    });

    document.getElementById('po-app').addEventListener('keydown', (e) => {
        if (e.key === 'F5') {
            e.preventDefault();
            toggleSupplierItems();
            return;
        }
        if (e.key === 'Enter' && e.target.matches('input:not([type=checkbox]), select') && !e.target.closest('#grd0-body')) {
            e.preventDefault();
            focusNext(e.target);
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
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

async function loadConfig() {
    try {
        config = await Api.get(`${API}/config`);
        if (config.company_name) setStatus(config.company_name);
        if (!config.book_ok) showAlert(config.book_message || 'Book permission issue', 'warning');
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function clearForm(confirmFirst = true) {
    if (confirmFirst && lines.some((l) => l.item_id)) {
        if (!window.confirm('Clearing voucher, Are you sure ?')) return;
    }
    lines = [emptyLine()];
    selectedRow = 0;
    docLoaded = false;
    supplierItems = [];
    highlightedManualId = null;
    lastValidatedSupplierId = null;

    document.getElementById('TxtDocID').value = '0';
    document.getElementById('TxtDocID').disabled = false;
    document.getElementById('TxtDocDate').value = todayISO();
    document.getElementById('TxtGPID').value = '';
    document.getElementById('TxtTime').value = '';
    document.getElementById('CboPayment').value = '1';
    document.getElementById('TxtCustID').value = '';
    document.getElementById('TxtCustTitle').textContent = '—';
    document.getElementById('LblRegistration').textContent = '';
    document.getElementById('TxtCustOrder').value = '';
    document.getElementById('TxtCustOrderDate').value = '';
    document.getElementById('TxtDesc').value = '';
    document.getElementById('TxtAddress').value = '';
    document.getElementById('TxtStaxID').value = '';
    document.getElementById('TxtCityID').value = '';
    document.getElementById('TxtCityTitle').value = '';
    document.getElementById('lblItemTitle').textContent = '\u00a0';
    document.getElementById('lblRate').textContent = '—';
    document.getElementById('lblStock').textContent = '—';
    document.getElementById('TxtTitle').textContent = '—';
    document.getElementById('txtManualID').value = '';
    document.getElementById('serial_no').value = '';
    document.getElementById('cFoundFlag').value = '0';

    clearDed(true);
    renderGrid();
    renderSupplierItems();
    clearHistoryGrids();
    calcTotals();
    setButtons(false);
    hideSupplierItems();
}

function setButtons(loaded) {
    const hasSupplier = lastValidatedSupplierId != null
        && parseInt(document.getElementById('TxtCustID').value, 10) === lastValidatedSupplierId;
    const canCreate = Auth.hasPermission('inventory.fin_inv_order.create');
    const canEdit = Auth.hasPermission('inventory.fin_inv_order.edit');
    const canDelete = Auth.hasPermission('inventory.fin_inv_order.delete');
    const canSave = loaded ? canEdit : canCreate;
    document.getElementById('CmdSave').disabled = !hasSupplier || !canSave;
    document.getElementById('CmdDelete').disabled = !loaded || !canDelete;
    document.getElementById('CmdPrint').disabled = !loaded;
    document.getElementById('CmdDiscount').disabled = !hasSupplier || !canSave;
    document.getElementById('CmdShowAddr').disabled = !hasSupplier;
    document.getElementById('cmdAddItem').disabled = !hasSupplier || !canSave;
}

function hideSupplierItems() {
    document.getElementById('supplier-items-panel').classList.add('d-none');
    document.getElementById('CmdShowItem').textContent = 'Show Items';
    document.getElementById('cmdPrintGrid').disabled = true;
}

async function previewNextId() {
    if (docLoaded) return;
    try {
        const data = await Api.get(`${API}/next-id`);
        document.getElementById('TxtDocID').value = String(data.next_inv_id);
    } catch (_) { /* ignore */ }
}

async function loadDocument() {
    const invId = num(document.getElementById('TxtDocID').value);
    if (!invId) return;
    try {
        const doc = await Api.get(`${API}/documents/${invId}`);
        applyDocument(doc);
        showAlert(`Loaded P.O. # ${invId}`, 'success');
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function applyDocument(doc) {
    docLoaded = true;
    document.getElementById('cFoundFlag').value = '1';
    document.getElementById('TxtDocID').value = doc.inv_id;
    document.getElementById('TxtDocID').disabled = true;
    document.getElementById('TxtDocDate').value = doc.doc_date;
    document.getElementById('TxtCustID').value = doc.supplier_id;
    document.getElementById('TxtCustTitle').textContent = doc.supplier_title || '—';
    document.getElementById('LblRegistration').textContent = doc.registration || '';
    document.getElementById('CboPayment').value = String(doc.payment_type);
    document.getElementById('TxtGPID').value = doc.gp_id || '';
    document.getElementById('TxtTime').value = doc.gp_time || '';
    document.getElementById('TxtCustOrder').value = doc.cust_order || '';
    document.getElementById('TxtCustOrderDate').value = doc.cust_order_date || '';
    document.getElementById('TxtDesc').value = doc.customer_title || '';
    document.getElementById('TxtAddress').value = doc.address || '';
    document.getElementById('TxtStaxID').value = doc.stax_id || '';
    document.getElementById('TxtCityID').value = doc.city_id || '';
    document.getElementById('TxtCityTitle').value = doc.city_title || '';
    document.getElementById('serial_no').value = doc.serial_no;

    document.getElementById('HDiscount').value = doc.charges.discount;
    document.getElementById('HClaim').value = doc.charges.claim;
    document.getElementById('HOtherDed').value = doc.charges.other_ded;
    document.getElementById('HLoading').value = doc.charges.loading;
    document.getElementById('HCarriage').value = doc.charges.carriage;
    document.getElementById('HOtherCharges').value = doc.charges.other_charges;

    lines = doc.lines.map((l) => ({
        barcode_id: l.barcode_id || '',
        manual_id: l.manual_id || '',
        item_id: l.item_id,
        item_title: l.item_title,
        qty: l.qty,
        rate: l.rate,
        amount: l.amount,
        disc_per: l.disc_per,
        disc_amt: l.disc_amt,
        net_amt: l.net_amt,
    }));
    lines.push(emptyLine());
    selectedRow = 0;
    renderGrid();
    calcTotals();
    loadPoHistory(doc.supplier_id);
    lastValidatedSupplierId = doc.supplier_id;
    setButtons(true);
}

function clearSupplierDisplay() {
    document.getElementById('TxtCustTitle').textContent = '—';
    document.getElementById('LblRegistration').textContent = '';
    document.getElementById('TxtDesc').value = '';
    document.getElementById('TxtAddress').value = '';
    document.getElementById('TxtStaxID').value = '';
    document.getElementById('TxtCityID').value = '';
    document.getElementById('TxtCityTitle').value = '';
    document.getElementById('TxtCustOrder').value = '';
    document.getElementById('TxtCustOrderDate').value = '';
    clearHistoryGrids();
    hideSupplierItems();
}

async function validateSupplier() {
    const id = parseInt(document.getElementById('TxtCustID').value, 10);
    if (!id) {
        clearSupplierDisplay();
        lastValidatedSupplierId = null;
        setButtons(false);
        document.getElementById('TxtCustID').focus();
        return false;
    }
    try {
        const prevId = lastValidatedSupplierId;
        const s = await Api.get(`${API}/suppliers/${id}`);
        lastValidatedSupplierId = s.supplier_id;
        document.getElementById('TxtCustID').value = String(s.supplier_id);
        document.getElementById('TxtCustTitle').textContent = s.vendor_title || '—';
        document.getElementById('LblRegistration').textContent = s.registration || '';
        document.getElementById('TxtDesc').value = s.vendor_title || '';
        document.getElementById('TxtAddress').value = s.address || '';
        document.getElementById('TxtStaxID').value = s.stax_id || '';
        document.getElementById('TxtCityID').value = s.city_id || '';
        document.getElementById('TxtCityTitle').value = s.city_title || '';
        // VB6 TxtCustID_Validate: TxtCustOrder.Text = Rs!CONTACT_PERSON
        if (!docLoaded || prevId !== s.supplier_id) {
            document.getElementById('TxtCustOrder').value = s.contact_person || '';
        }
        setButtons(docLoaded);
        await loadPoHistory(s.supplier_id);
        if (!document.getElementById('supplier-items-panel').classList.contains('d-none')) {
            await loadSupplierItems(s.supplier_id);
        }
        return true;
    } catch (err) {
        clearSupplierDisplay();
        lastValidatedSupplierId = null;
        setButtons(false);
        showAlert(err.message, 'danger');
        document.getElementById('TxtCustID').focus();
        return false;
    }
}

function renderGrid() {
    const body = document.getElementById('grd0-body');
    body.innerHTML = lines.map((line, i) => {
        const isSel = i === selectedRow;
        const hasItem = !!line.item_id;
        return `
        <tr data-index="${i}" class="${isSel ? 'selected' : ''}">
            <td><input class="cell-in" data-field="${F.barcode}" data-row="${i}" value="${esc(line.barcode_id)}" ${manualMode() ? 'tabindex="-1"' : ''} autocomplete="off"></td>
            <td><input class="cell-in" data-field="${F.manual}" data-row="${i}" value="${esc(line.manual_id)}" ${!manualMode() && !hasItem ? '' : ''} autocomplete="off"></td>
            <td>${esc(line.item_title)}</td>
            <td class="po-num"><input class="cell-in text-end" data-field="${F.qty}" data-row="${i}" value="${esc(cellVal(line.qty))}" inputmode="decimal"></td>
            <td class="po-num"><input class="cell-in text-end" data-field="${F.rate}" data-row="${i}" value="${esc(cellVal(line.rate))}" inputmode="decimal"></td>
            <td class="po-readonly">${money(line.amount)}</td>
            <td class="po-num"><input class="cell-in text-end" data-field="${F.disc_per}" data-row="${i}" value="${esc(cellVal(line.disc_per))}" inputmode="decimal"></td>
            <td class="po-readonly">${money(line.disc_amt)}</td>
            <td class="po-readonly">${money(line.net_amt)}</td>
            <td>${hasItem ? `<button type="button" class="btn btn-sm btn-outline-danger py-0" data-del="${i}">×</button>` : ''}</td>
        </tr>`;
    }).join('');

    body.querySelectorAll('[data-del]').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteGridRow(Number(btn.dataset.del));
        });
    });

    if (focusAfterRender) {
        const { row, field } = focusAfterRender;
        focusAfterRender = null;
        const inp = body.querySelector(`input[data-row="${row}"][data-field="${field}"]`);
        if (inp) { inp.focus(); inp.select?.(); }
    }
}

function esc(s) {
    return String(s ?? '').replace(/"/g, '&quot;');
}

function cellVal(v) {
    return v === 0 || v ? String(v) : '';
}

function normalizeBarcode(v) {
    const trimmed = String(v).trim();
    const n = num(trimmed);
    if (n && String(n) === String(parseFloat(trimmed))) return String(n);
    return trimmed;
}

/** Compute amounts without destroying in-progress typed strings */
function calcLineValues(qty, rate, discPer) {
    const q = num(qty);
    const r = num(rate);
    const d = num(discPer);
    const amount = Math.round(q * r * 1000) / 1000;
    const disc_amt = Math.round(amount * d / 100 * 1000) / 1000;
    const net_amt = Math.round((amount - disc_amt) * 100) / 100;
    return { qty: q, rate: r, disc_per: d, amount, disc_amt, net_amt };
}

function calcLine(line) {
    const v = calcLineValues(line.qty, line.rate, line.disc_per);
    Object.assign(line, v);
    return line;
}

function updateRowCalculatedCells(row) {
    const line = lines[row];
    const v = calcLineValues(line.qty, line.rate, line.disc_per);
    line.amount = v.amount;
    line.disc_amt = v.disc_amt;
    line.net_amt = v.net_amt;

    const tr = document.querySelector(`#grd0-body tr[data-index="${row}"]`);
    if (!tr) return;
    const cells = tr.children;
    if (cells[5]) cells[5].textContent = money(v.amount);
    if (cells[7]) cells[7].textContent = money(v.disc_amt);
    if (cells[8]) cells[8].textContent = money(v.net_amt);
}

function updateRowSelection() {
    document.querySelectorAll('#grd0-body tr').forEach((tr) => {
        tr.classList.toggle('selected', Number(tr.dataset.index) === selectedRow);
    });
}

function focusCell(row, field) {
    selectedRow = row;
    updateRowSelection();
    const inp = document.querySelector(`#grd0-body input[data-row="${row}"][data-field="${field}"]`);
    if (inp) {
        inp.focus();
        inp.select?.();
    } else {
        focusAfterRender = { row, field };
        renderGrid();
    }
}

function calcTotals() {
    const dataLines = lines.filter((l) => l.item_id).map((l) => calcLine({ ...l }));
    let qty = 0, amount = 0, disc = 0, net = 0;
    dataLines.forEach((l) => {
        qty += l.qty;
        amount += l.amount;
        disc += l.disc_amt;
        net += l.net_amt;
    });
    document.getElementById('mQty').textContent = money(qty, 3);
    document.getElementById('mAmount').textContent = money(amount);
    document.getElementById('mDiscAmt').textContent = money(disc);
    document.getElementById('mNetAmt').textContent = money(net);
    calcHeaderTotals(net);
}

function calcHeaderTotals(netOverride) {
    const net = netOverride !== undefined ? netOverride : num(document.getElementById('mNetAmt').textContent.replace(/,/g, ''));
    const hDisc = num(document.getElementById('HDiscount').value) + num(document.getElementById('HClaim').value) + num(document.getElementById('HOtherDed').value);
    const hChg = num(document.getElementById('HLoading').value) + num(document.getElementById('HCarriage').value) + num(document.getElementById('HOtherCharges').value);
    document.getElementById('LblDiscount').textContent = money(hDisc);
    document.getElementById('LblCharges').textContent = money(hChg);
    document.getElementById('LblDiff').textContent = money(hChg - hDisc);
    document.getElementById('LblNetInvoice').textContent = money(net - hDisc + hChg);
}

function qtyInGridForItem(item, excludeRow = -1) {
    let conQty = 0;
    const useManual = manualMode();
    lines.forEach((l, i) => {
        if (i === excludeRow || !l.item_id) return;
        if (useManual) {
            if (String(l.manual_id).trim() === String(item.manual_id).trim()) conQty += num(l.qty);
        } else if (item.barcodeid && String(l.barcode_id) === String(item.barcodeid)) {
            conQty += num(l.qty);
        } else if (String(l.item_id) === String(item.item_id)) {
            conQty += num(l.qty);
        }
    });
    return conQty;
}

function updateStockLabel(item, row) {
    lastItemStock = num(item.stock_qty);
    const conQty = qtyInGridForItem(item, row);
    if (!docLoaded) {
        document.getElementById('lblStock').textContent = money(lastItemStock - conQty, 3);
    } else {
        document.getElementById('lblStock').textContent = money(lastItemStock, 3);
    }
}

function onGridInput(e) {
    const input = e.target;
    if (!input.matches('.cell-in')) return;
    const row = Number(input.dataset.row);
    const field = input.dataset.field;
    lines[row][field] = input.value;
    if ([F.qty, F.rate, F.disc_per].includes(field)) {
        updateRowCalculatedCells(row);
        if (field === F.rate && num(lines[row].rate) === 0 && lines[row].item_id) {
            showAlert('Zero Rate not Allowed Contact with Administrator ...', 'danger');
        }
        if (lines[row].item_id) {
            updateStockLabel({
                item_id: lines[row].item_id,
                manual_id: lines[row].manual_id,
                barcodeid: lines[row].barcode_id,
                stock_qty: lastItemStock,
            }, row);
        }
        calcTotals();
    }
}

async function onGridBlur(e) {
    const input = e.target;
    if (!input.matches('.cell-in')) return;
    const row = Number(input.dataset.row);
    const field = input.dataset.field;
    const val = input.value.trim();

    if ([F.qty, F.rate, F.disc_per].includes(field)) {
        calcLine(lines[row]);
        updateRowCalculatedCells(row);
        calcTotals();
        return;
    }
    if (!val || val === '0') return;
    if (skipNextBlurResolve) {
        skipNextBlurResolve = false;
        return;
    }
    if (field === F.manual) {
        await resolveLineItem(row, 'manual', val);
    } else if (field === F.barcode) {
        await resolveLineItem(row, 'barcode', normalizeBarcode(val));
    }
}

async function onGridKeydown(e) {
    if (e.key === 'F4') {
        e.preventDefault();
        e.stopPropagation();
        openSearch('item');
        return;
    }

    const input = e.target;
    if (!input.matches('.cell-in')) {
        if (e.key === 'Delete' && selectedRow >= 0) {
            e.preventDefault();
            deleteGridRow(selectedRow);
        }
        return;
    }
    const row = Number(input.dataset.row);
    const field = input.dataset.field;

    if (e.key === 'Enter') {
        e.preventDefault();
        if (field === F.manual || field === F.barcode) {
            const val = input.value.trim();
            if (val && val !== '0') {
                skipNextBlurResolve = true;
                const mode = field === F.manual ? 'manual' : 'barcode';
                const lookup = mode === 'barcode' ? normalizeBarcode(val) : val;
                await resolveLineItem(row, mode, lookup);
            } else {
                focusCell(row, F.qty);
            }
            return;
        }
        if ([F.qty, F.rate, F.disc_per].includes(field)) {
            calcLine(lines[row]);
            updateRowCalculatedCells(row);
            calcTotals();
        }
        navigateEnter(row, field);
        return;
    }
    if (e.key === 'ArrowDown' && row === lines.length - 1 && lines[row].item_id) {
        ensureTrailingRow();
        focusCell(lines.length - 1, manualMode() ? F.manual : F.barcode);
    }
    if (e.key === 'Delete' && e.ctrlKey) {
        e.preventDefault();
        deleteGridRow(row);
    }
}

/** VB6 grd_KeyDownEdit Enter navigation */
function navigateEnter(row, field) {
    if (field === F.manual || field === F.barcode) {
        focusCell(row, F.qty);
    } else if (field === F.qty) {
        focusCell(row, F.disc_per);
    } else if (field === F.disc_per) {
        ensureTrailingRow();
        focusCell(lines.length - 1, manualMode() ? F.manual : F.barcode);
    } else if (field === F.rate) {
        focusCell(row, F.disc_per);
    }
}

async function resolveLineItem(row, mode, value) {
    const sid = num(document.getElementById('TxtCustID').value);
    if (!sid) {
        showAlert('Select Supplier.', 'warning');
        clearRow(row);
        return;
    }
    try {
        let item;
        if (mode === 'manual') {
            item = await Api.get(`${API}/items/by-manual/${encodeURIComponent(value)}?supplier_id=${sid}`);
        } else {
            item = await Api.get(`${API}/items/by-barcode/${encodeURIComponent(normalizeBarcode(value))}?supplier_id=${sid}`);
        }
        await applyItemToRow(row, item);
    } catch (err) {
        showAlert(err.message || 'Item not found.', 'danger');
        clearRow(row);
    }
}

async function resolveLineItemById(row, itemId) {
    const sid = num(document.getElementById('TxtCustID').value);
    if (!sid) { showAlert('Select Supplier.', 'warning'); return; }
    try {
        const item = await Api.get(`${API}/items/by-id/${encodeURIComponent(itemId)}?supplier_id=${sid}`);
        await applyItemToRow(row, item);
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

async function applyItemToRow(row, item) {
    if (lines.some((l, i) => i !== row && l.item_id === item.item_id)) {
        showAlert('Item already exist.', 'info');
        clearRow(row);
        return;
    }
    if (!item.in_supplier_catalog) {
        showAlert('Item not exist in Supplier Purchase Order Data.', 'info');
        clearRow(row);
        return;
    }

    lines[row].item_id = item.item_id;
    lines[row].manual_id = item.manual_id != null ? String(item.manual_id) : '';
    lines[row].barcode_id = item.barcodeid || item.barcodeid_ws || '';
    lines[row].item_title = item.item_title;
    lines[row].rate = item.cost_rate;
    lines[row].qty = '';
    lines[row].disc_per = lines[row].disc_per || '';
    calcLine(lines[row]);

    document.getElementById('lblItemTitle').textContent = item.item_title;
    document.getElementById('lblRate').textContent = money(item.sales_rate);
    updateStockLabel(item, row);
    highlightSupplierItem(lines[row].manual_id, true);
    await loadItemHistory(item.item_id);

    ensureTrailingRow();
    renderGrid();
    calcTotals();
    focusCell(row, F.qty);
}

function clearRow(row) {
    if (lines[row]?.manual_id) highlightSupplierItem(lines[row].manual_id, false);
    if (lines.length > 1 && row < lines.length - 1) {
        lines.splice(row, 1);
    } else {
        lines[row] = emptyLine();
    }
    ensureTrailingRow();
    selectedRow = Math.min(selectedRow, lines.length - 1);
    renderGrid();
    calcTotals();
}

function addFromSupplierGrid(manualId) {
    if (!manualId) return;
    const sid = num(document.getElementById('TxtCustID').value);
    if (!sid) { showAlert('Select Supplier.', 'info'); return; }
    const row = targetRowForNewItem();
    selectedRow = row;
    lines[row].manual_id = manualId;
    skipNextBlurResolve = true;
    resolveLineItem(row, 'manual', manualId);
    document.getElementById('grd0-wrap').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function deleteGridRow(idx) {
    if (!lines[idx]?.item_id) return;
    if (!window.confirm('Are you sure to delete.')) return;
    highlightSupplierItem(lines[idx].manual_id, false);
    if (lines.length === 1) {
        lines[0] = emptyLine();
    } else {
        lines.splice(idx, 1);
    }
    ensureTrailingRow();
    selectedRow = Math.min(idx, lines.length - 1);
    renderGrid();
    calcTotals();
}

function highlightSupplierItem(manualId, on) {
    highlightedManualId = on ? String(manualId) : null;
    renderSupplierItems();
}

function openDedModal() {
    document.getElementById('TxtDiscount').value = document.getElementById('HDiscount').value;
    document.getElementById('TxtClaim').value = document.getElementById('HClaim').value;
    document.getElementById('TxtOtherDed').value = document.getElementById('HOtherDed').value;
    document.getElementById('TxtLoading').value = document.getElementById('HLoading').value;
    document.getElementById('TxtCarriage').value = document.getElementById('HCarriage').value;
    document.getElementById('TxtOtherCharges').value = document.getElementById('HOtherCharges').value;
    dedModal.show();
}

function saveDed() {
    document.getElementById('HDiscount').value = num(document.getElementById('TxtDiscount').value);
    document.getElementById('HClaim').value = num(document.getElementById('TxtClaim').value);
    document.getElementById('HOtherDed').value = num(document.getElementById('TxtOtherDed').value);
    document.getElementById('HLoading').value = num(document.getElementById('TxtLoading').value);
    document.getElementById('HCarriage').value = num(document.getElementById('TxtCarriage').value);
    document.getElementById('HOtherCharges').value = num(document.getElementById('TxtOtherCharges').value);
    calcTotals();
    dedModal.hide();
}

function clearDed(silent = false) {
    ['HDiscount', 'HClaim', 'HOtherDed', 'HLoading', 'HCarriage', 'HOtherCharges'].forEach((id) => {
        document.getElementById(id).value = '0';
    });
    ['TxtDiscount', 'TxtClaim', 'TxtOtherDed', 'TxtLoading', 'TxtCarriage', 'TxtOtherCharges'].forEach((id) => {
        document.getElementById(id).value = '0';
    });
    if (!silent) calcTotals();
}

async function saveDocument() {
    const supplierId = parseInt(document.getElementById('TxtCustID').value, 10) || 0;
    if (supplierId !== lastValidatedSupplierId) {
        const ok = await validateSupplier();
        if (!ok) return;
    }
    if (!supplierId) {
        showAlert('Select Supplier.', 'warning');
        document.getElementById('TxtCustID').focus();
        return;
    }
    const payload = buildPayload();
    if (!payload) return;
    try {
        const res = await Api.post(`${API}/documents`, payload);
        showAlert(res.message, 'success');
        if (window.confirm('Do you want to take a print ?')) {
            document.getElementById('TxtDocID').value = res.inv_id;
            await printDocument();
        }
        clearForm(false);
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function buildPayload() {
    const dataLines = lines.filter((l) => l.item_id).map((l) => calcLine({ ...l }));
    if (!dataLines.length) {
        showAlert('Select item first.', 'warning');
        return null;
    }
    for (const l of dataLines) {
        if (!l.qty) { showAlert('Zero quantity not allowed.', 'warning'); return null; }
        if (!l.net_amt) { showAlert('Zero Net Amount not allowed.', 'warning'); return null; }
        if (!l.rate) { showAlert('Zero Rate not Allowed Contact with Administrator ...', 'warning'); return null; }
    }
    const invId = num(document.getElementById('TxtDocID').value);
    const supplierId = parseInt(document.getElementById('TxtCustID').value, 10) || 0;
    if (!supplierId) {
        showAlert('Select Supplier.', 'warning');
        return null;
    }
    return {
        inv_id: docLoaded ? invId : null,
        serial_no: num(document.getElementById('serial_no').value) || null,
        doc_date: document.getElementById('TxtDocDate').value,
        supplier_id: supplierId,
        cust_order: document.getElementById('TxtCustOrder').value,
        cust_order_date: document.getElementById('TxtCustOrderDate').value,
        payment_type: num(document.getElementById('CboPayment').value),
        stax_type: document.getElementById('LblRegistration').textContent === 'Registered' ? 0 : (document.getElementById('LblRegistration').textContent === 'Un-Registered' ? 1 : 2),
        gp_id: document.getElementById('TxtGPID').value,
        gp_time: document.getElementById('TxtTime').value,
        customer_title: document.getElementById('TxtDesc').value,
        address: document.getElementById('TxtAddress').value,
        stax_id: document.getElementById('TxtStaxID').value,
        city_id: num(document.getElementById('TxtCityID').value),
        remarks: '',
        amount_rec: 0,
        bal_amt: 0,
        charges: {
            discount: num(document.getElementById('HDiscount').value),
            claim: num(document.getElementById('HClaim').value),
            other_ded: num(document.getElementById('HOtherDed').value),
            loading: num(document.getElementById('HLoading').value),
            carriage: num(document.getElementById('HCarriage').value),
            other_charges: num(document.getElementById('HOtherCharges').value),
        },
        lines: dataLines,
    };
}

async function deleteDocument() {
    const invId = num(document.getElementById('TxtDocID').value);
    if (!invId || !docLoaded) return;
    if (!window.confirm('Discarding voucher, Are you sure ?')) return;
    try {
        const res = await Api.delete(`${API}/documents/${invId}`);
        showAlert(res.message, 'success');
        clearForm(false);
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

async function printDocument() {
    const invId = num(document.getElementById('TxtDocID').value);
    if (!invId) return;
    const preview = document.getElementById('chkPreview').checked;
    const url = `/admin/fin-inv-order/print/${invId}` + (preview ? '' : '?autoprint=1');
    const w = window.open(url, '_blank', 'noopener,width=900,height=1000');
    if (!w) {
        showAlert('Allow popups to print.', 'warning');
    }
}

function poQty(n) {
    const v = Number(n) || 0;
    return v.toFixed(2);
}

function poEsc(s) {
    return String(s ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

/** Normalize print API: new {header,lines} or legacy row array. */
function normalizePrintData(data) {
    if (data && data.header) {
        const h = { ...data.header };
        if (h.company_name && !String(h.company_name).endsWith('.')) {
            h.company_name = `${h.company_name}.`;
        }
        return { header: h, lines: data.lines || [] };
    }
    const rows = Array.isArray(data) ? data : [];
    const first = rows[0] || {};
    const invId = first.inv_id || num(document.getElementById('TxtDocID').value);
    const totalQty = rows.reduce((s, r) => s + (Number(r.qty) || 0), 0);
    const docDate = document.getElementById('TxtDocDate')?.value || '';
    let docDateDisplay = '';
    if (docDate) {
        const [y, m, d] = docDate.split('-');
        docDateDisplay = `${Number(m)}/${Number(d)}/${y} 12:00 AM`;
    }
    return {
        header: {
            inv_id: invId,
            doc_date_display: docDateDisplay,
            supplier_title: (document.getElementById('TxtCustTitle')?.textContent || '').replace(/^—$/, ''),
            cust_order: document.getElementById('TxtCustOrder')?.value || '',
            full_name: '',
            total_qty: totalQty,
            company_name: 'Shafique Departmental Store.',
            company_address: '193-A, QAMAR PARK SHAD BAGH LAHORE.',
            company_phone: 'Ph No.+92-42-37603151-2',
            company_ntn: '3973706-3',
            company_strn: '0300397370614',
            print_note: 'Goods will be received as per the purchase order and only 18% GST Invoices will be accepted. If the company is exampted from WHT, Provide the examption certificate.',
        },
        lines: rows.map((r) => ({
            serial_order: r.serial_order || 0,
            item_title: r.item_title || '',
            qty: r.qty || 0,
        })),
    };
}

/**
 * Exact PO100.pdf / VB6 LstInvStore_shortOrder layout.
 */
function buildPoPrintHtml(data) {
    const { header: h, lines } = normalizePrintData(data);
    if (!h || h.inv_id == null) {
        throw new Error('Print data incomplete. Restart the app server and try again.');
    }

    const lineHtml = lines.map((r) => `
        <tr>
            <td class="desc">${poEsc(r.item_title)}</td>
            <td class="qty">${poQty(r.qty)}</td>
        </tr>`).join('');

    const note = String(h.print_note || '');
    const noteText = /^Note\s*:/i.test(note) ? note : `Note : ${note}`;

    return `<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>P.O. ${poEsc(h.inv_id)}</title>
<link href="/static/css/fin_inv_order_print.css?v=20260812i" rel="stylesheet">
</head><body class="po-print-body">
<div class="po-print">

    <div class="po-co-box"><span class="po-co-name">${poEsc(h.company_name)}</span></div>

    <div class="po-head-row">
        <div class="po-addr">${poEsc(h.company_address)}</div>
        <div class="po-date">${poEsc(h.doc_date_display)}</div>
    </div>
    <div class="po-phone">${poEsc(h.company_phone)}</div>

    <div class="po-meta1">
        <span class="po-doctype">Purchase Order</span>
        <span>NTN ${poEsc(h.company_ntn)}</span>
        <span>STRN ${poEsc(h.company_strn)}</span>
    </div>

    <div class="po-meta2">
        <span class="po-po">P.O # ${poEsc(h.inv_id)}</span>
        <span class="po-booker">Order Booker: <span class="po-booker-val">${poEsc(h.cust_order)}</span></span>
    </div>

    <div class="po-supplier">${poEsc(h.supplier_title)}</div>

    <table class="po-grid">
        <colgroup>
            <col class="col-desc">
            <col class="col-qty">
        </colgroup>
        <thead>
            <tr>
                <th class="desc">Description</th>
                <th class="qty">Qty.</th>
            </tr>
        </thead>
        <tbody>
            ${lineHtml}
        </tbody>
    </table>

    <div class="po-total-row">
        <span class="po-total-label">Total :</span>
        <span class="po-total-box">${poQty(h.total_qty)}</span>
    </div>

    <hr class="po-sign-rule">
    <div class="po-signed">${poEsc(h.full_name)}</div>
    <div class="po-note">${poEsc(noteText)}</div>

</div>
</body></html>`;
}

async function toggleSupplierItems() {
    const panel = document.getElementById('supplier-items-panel');
    const btn = document.getElementById('CmdShowItem');
    const sid = num(document.getElementById('TxtCustID').value);
    if (!sid) { showAlert('Select Supplier.', 'info'); return; }
    if (panel.classList.contains('d-none')) {
        await loadSupplierItems(sid);
        panel.classList.remove('d-none');
        btn.textContent = 'Hide Items';
        document.getElementById('cmdPrintGrid').disabled = false;
    } else {
        hideSupplierItems();
    }
}

function printSupplierGrid() {
    const panel = document.getElementById('supplier-items-panel');
    if (panel.classList.contains('d-none')) return;
    const w = window.open('', '_blank');
    if (!w) return;
    w.document.write(`<html><head><title>Supplier Items</title>
        <style>table{border-collapse:collapse;width:100%}th,td{border:1px solid #999;padding:4px}</style></head><body>
        <h3>Supplier Items</h3>${panel.querySelector('.po-grid-wrap').innerHTML}</body></html>`);
    w.document.close();
    w.print();
}

async function loadSupplierItems(sid) {
    try {
        supplierItems = await Api.get(`${API}/suppliers/${sid}/items`);
        renderSupplierItems();
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function renderSupplierItems() {
    document.getElementById('grd1-body').innerHTML = supplierItems.map((it) => {
        const hi = highlightedManualId && String(it.manual_id) === String(highlightedManualId);
        return `
        <tr data-manual="${it.manual_id}" data-item="${it.item_id}" class="${hi ? 'supplier-pick' : ''}" tabindex="0">
            <td>${esc(it.supplier_title)}</td><td>${esc(it.manual_id)}</td><td>${esc(it.item_title)}</td>
            <td class="po-num">${money(it.tnot, 0)}</td><td class="po-num">${money(it.stock_qty, 3)}</td>
            <td class="po-num">${money(it.cost_rate)}</td><td class="po-num">${money(it.sales_rate)}</td>
            <td><button type="button" class="btn btn-sm btn-outline-danger py-0" data-rm="${it.item_id}">×</button></td>
        </tr>`;
    }).join('');
    document.getElementById('grd1-body').querySelectorAll('[data-rm]').forEach((btn) => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (!window.confirm('Are you sure to delete.')) return;
            const sid = num(document.getElementById('TxtCustID').value);
            await Api.delete(`${API}/suppliers/${sid}/items/${btn.dataset.rm}`);
            await loadSupplierItems(sid);
        });
    });
}

async function previewManualTitle() {
    const manualId = num(document.getElementById('txtManualID').value);
    const titleEl = document.getElementById('TxtTitle');
    if (!manualId || manualId === 0) { titleEl.textContent = '—'; return; }
    try {
        const item = await Api.get(`${API}/items/by-manual/${manualId}`);
        titleEl.textContent = item.item_title || '—';
    } catch (_) {
        titleEl.textContent = '—';
    }
}

async function addSupplierItem() {
    const sid = num(document.getElementById('TxtCustID').value);
    const manualId = num(document.getElementById('txtManualID').value);
    if (!sid) { showAlert('Select Supplier.', 'info'); return; }
    if (!manualId) { showAlert('Select Item First.', 'info'); return; }
    try {
        await Api.post(`${API}/suppliers/${sid}/items`, { manual_id: manualId });
        document.getElementById('txtManualID').value = '';
        document.getElementById('TxtTitle').textContent = '—';
        if (!document.getElementById('supplier-items-panel').classList.contains('d-none')) {
            await loadSupplierItems(sid);
        }
        showAlert('Item added to supplier catalog.', 'success');
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function openItemFromSelection() {
    const row = selectedRow >= 0 ? selectedRow : 0;
    const manual = lines[row]?.manual_id;
    if (manual) showAlert(`Item master (Fin_Item) — Manual ID ${manual}`, 'info');
    else showAlert('Select a grid row with an item first.', 'info');
}

async function loadPoHistory(sid) {
    try {
        const rows = await Api.get(`${API}/suppliers/${sid}/po-history?limit=5`);
        document.getElementById('grd4-body').innerHTML = rows.map((r) => `
            <tr><td>${r.inv_id}</td><td>${r.doc_date || ''}</td><td>${r.supplier_id}</td><td>${esc(r.supplier_title)}</td><td class="po-num">${money(r.total_amt)}</td></tr>
        `).join('');
    } catch (_) { /* ignore */ }
}

async function loadItemHistory(itemId) {
    try {
        const data = await Api.get(`${API}/items/${itemId}/history?limit=5`);
        document.getElementById('grd2-body').innerHTML = (data.purchase || []).map((r) => `
            <tr><td>${r.doc_id}</td><td>${r.doc_date || ''}</td><td>${esc(r.party)}</td><td class="po-num">${money(r.qty, 3)}</td><td class="po-num">${money(r.rate)}</td><td>${esc(r.extra)}</td></tr>
        `).join('');
        document.getElementById('grd3-body').innerHTML = (data.sales || []).map((r) => `
            <tr><td>${r.doc_id}</td><td>${r.doc_date || ''}</td><td>${esc(r.party)}</td><td class="po-num">${money(r.qty, 3)}</td><td class="po-num">${money(r.rate)}</td></tr>
        `).join('');
    } catch (_) { /* ignore */ }
}

function clearHistoryGrids() {
    ['grd2-body', 'grd3-body', 'grd4-body'].forEach((id) => { document.getElementById(id).innerHTML = ''; });
}

function openSearch(mode) {
    searchMode = mode;
    document.getElementById('search-title').textContent = mode === 'supplier' ? 'Supplier Search' : 'Item Search (F4)';
    document.getElementById('search-query').value = '';
    document.getElementById('search-results').innerHTML = '';
    searchModal.show();
    document.getElementById('search-query').focus();
}

async function runSearch() {
    const q = document.getElementById('search-query').value.trim();
    if (q.length < 1) return;
    const url = searchMode === 'supplier'
        ? `${API}/suppliers?q=${encodeURIComponent(q)}`
        : `${API}/items/search?q=${encodeURIComponent(q)}`;
    try {
        const rows = await Api.get(url);
        document.getElementById('search-results').innerHTML = rows.map((r) => `
            <tr style="cursor:pointer" data-id="${r.id}"><td>${r.id}</td><td>${esc(r.title)}</td><td>${esc(r.extra)}</td></tr>
        `).join('');
        document.getElementById('search-results').querySelectorAll('tr').forEach((tr) => {
            tr.addEventListener('click', async () => {
                if (searchMode === 'supplier') {
                    document.getElementById('TxtCustID').value = tr.dataset.id;
                    await validateSupplier();
                } else {
                    const row = selectedRow >= 0 ? selectedRow : targetRowForNewItem();
                    await resolveLineItemById(row, tr.dataset.id);
                }
                searchModal.hide();
            });
        });
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}
