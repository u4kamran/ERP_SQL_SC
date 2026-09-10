const API = '/api/v1/fin-item-classic';
let isExisting = false;
let searchModal;
let loadingItem = false;
let historyLoadedFor = null;

document.addEventListener('DOMContentLoaded', async () => {
    await Auth.requireAuth();
    if (!Auth.hasPermission('inventory.fin_item.view')) {
        document.getElementById('item-app').innerHTML = '<div class="alert alert-danger">Access denied.</div>';
        return;
    }

    searchModal = new bootstrap.Modal(document.getElementById('searchModal'));
    bindEvents();
    bindVb6Keyboard();
    bindSsTabs();
    loadStats();
    updateActionButtons();
    document.getElementById('manual_id').focus();
    document.getElementById('manual_id').select?.();
});

function bindEvents() {
    document.getElementById('btn-save').addEventListener('click', saveItem);
    document.getElementById('btn-clear').addEventListener('click', clearForm);
    document.getElementById('btn-delete').addEventListener('click', deleteItem);
    document.getElementById('btn-manual').addEventListener('click', applyManualDefaults);
    document.getElementById('btn-view').addEventListener('click', () => openSearch());
    document.getElementById('btn-search-item').addEventListener('click', () => openSearch());
    document.getElementById('btn-copy-gl').addEventListener('click', copyGlSalesToAll);

    document.getElementById('btn-load-item').addEventListener('click', loadByItemId);
    document.getElementById('btn-load-manual').addEventListener('click', loadByManualId);
    document.getElementById('btn-load-barcode').addEventListener('click', loadByBarcode);
    document.getElementById('btn-load-ws-barcode').addEventListener('click', loadByWsBarcode);

    bindEnterKey('item_id', loadByItemId);
    bindEnterKey('manual_id', loadByManualId);
    bindEnterKey('barcodeid', loadByBarcode);
    bindEnterKey('barcodeid_ws', loadByWsBarcode);
    document.getElementById('sales_rate').addEventListener('input', recalcSalesWoGst);
    bindAmountFields();

    document.getElementById('search-query').addEventListener('input', debounce(searchItems, 300));
    document.getElementById('search-query').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); searchItems(); }
    });

    ['uom_id', 'country_id', 'co_id'].forEach(id => {
        document.getElementById(id).addEventListener('change', () => validateLookup(id));
    });
    document.querySelectorAll('.gl-field').forEach(el => {
        el.addEventListener('change', () => validateGl(el.id.replace('gl_', '').replace('_id', '')));
    });

    document.querySelector('[data-bs-target="#tab-pur"]')?.addEventListener('shown.bs.tab', () => loadHistory());
    document.querySelector('[data-bs-target="#tab-sales"]')?.addEventListener('shown.bs.tab', () => loadHistory());

    const noOfPur = document.getElementById('no_of_pur');
    noOfPur.addEventListener('change', onHistoryLimitChange);
    noOfPur.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            onHistoryLimitChange();
        }
    });
    document.getElementById('btn-refresh-history').addEventListener('click', refreshHistory);

    bindPrintButtons();
}

/** VB6-like Enter moves to next control; Shift+Enter goes back (except ID load fields). */
function bindVb6Keyboard() {
    const form = document.querySelector('.vb6-form');
    form.addEventListener('keydown', (e) => {
        if (e.key !== 'Enter' || e.target.closest('.modal')) return;
        const id = e.target.id;
        // ID load fields keep Enter = validate/load (bound separately)
        if (['item_id', 'manual_id', 'barcodeid', 'barcodeid_ws'].includes(id)) return;
        if (e.target.tagName === 'TEXTAREA') return;
        e.preventDefault();
        focusNav(e.target, e.shiftKey ? -1 : 1);
    });
}

function focusNav(fromEl, dir) {
    const list = [...document.querySelectorAll('.vb6-form [data-nav]')]
        .filter((el) => !el.disabled && !el.readOnly && el.offsetParent !== null)
        .sort((a, b) => Number(a.dataset.nav) - Number(b.dataset.nav));
    const idx = list.indexOf(fromEl);
    if (idx < 0) return;
    const next = list[idx + dir];
    if (!next) return;
    next.focus();
    if (next.select) next.select();
}

function bindSsTabs() {
    document.querySelectorAll('.sstab-headers .sstab').forEach((btn) => {
        btn.addEventListener('shown.bs.tab', () => {
            document.querySelectorAll('.sstab-headers .sstab').forEach((b) => b.classList.remove('active'));
            btn.classList.add('active');
        });
        // Bootstrap Tab needs data-bs-toggle already set; sync active class on click
        btn.addEventListener('click', () => {
            document.querySelectorAll('.sstab-headers .sstab').forEach((b) => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
}

function updateActionButtons() {
    const viewBtn = document.getElementById('btn-view');
    if (viewBtn) viewBtn.disabled = !!isExisting;
    const openBal = document.getElementById('btn-opening-bal');
    if (openBal) openBal.disabled = !isExisting;
}

function bindPrintButtons() {
    const map = {
        'btn-print-rail': 'rail',
        'btn-print-rail-sm': 'rail-sm',
        'btn-print-des-exp': 'des-exp',
        'btn-print-desc': 'desc',
        'btn-print-label': 'label',
    };
    Object.entries(map).forEach(([id, kind]) => {
        document.getElementById(id)?.addEventListener('click', () => printItemLabel(kind));
    });
    document.getElementById('btn-opening-bal')?.addEventListener('click', openOpeningBal);
    document.getElementById('chkBarPrint')?.addEventListener('click', () => {
        const el = document.getElementById('barcodeid');
        el?.focus();
        el?.select?.();
    });
}

function requireLoadedItem() {
    const itemId = (val('item_id') || '').trim();
    if (!itemId || itemId === '0') {
        showAlert('Load an item first (Item ID / Manual ID / Barcode).');
        return null;
    }
    return itemId;
}

function printItemLabel(kind) {
    const itemId = requireLoadedItem();
    if (!itemId) return;

    if (!confirm('Do you want to take a print :  are you sure ? ')) return;

    let hidePrice = false;
    if (kind === 'desc' || kind === 'des-exp') {
        hidePrice = confirm('Do you want to hide price :  are you sure ? ');
    }

    const copies = Math.max(1, parseInt(val('no_of_pur'), 10) || 1);
    const title = (document.getElementById('item_title')?.textContent || '').trim();
    const shortName = val('item_short');
    const barcode = val('barcodeid');
    const sales = hidePrice ? '' : val('sales_rate');
    const cost = hidePrice ? '' : val('cost_rate');
    const company = (document.getElementById('co_title')?.textContent || '').trim();

    const labels = {
        rail: 'Print Rail',
        'rail-sm': 'Print Rail SM',
        'des-exp': 'Print Des Exp',
        desc: 'Print Desc',
        label: 'Print Label',
    };

    const sizeClass = {
        rail: 'rail',
        'rail-sm': 'rail-sm',
        'des-exp': 'des-exp',
        desc: 'desc',
        label: 'label',
    }[kind] || 'desc';

    let cards = '';
    for (let i = 0; i < (kind === 'rail' ? 1 : copies); i++) {
        cards += `
        <div class="card ${sizeClass}">
            <div class="co">${esc(company)}</div>
            <div class="id">${esc(itemId)}</div>
            <div class="title">${esc(title)}</div>
            <div class="short">${esc(shortName)}</div>
            <div class="bc">*${esc(barcode)}*</div>
            ${hidePrice ? '' : `<div class="price">Rs. ${esc(sales || '0.00')}</div>`}
            ${kind === 'des-exp' && !hidePrice ? `<div class="cost">Cost ${esc(cost || '0.00')}</div>` : ''}
        </div>`;
    }

    const html = `<!DOCTYPE html><html><head><title>${labels[kind] || 'Item Print'}</title>
<style>
  body { font-family: "MS Sans Serif", Tahoma, sans-serif; margin: 8px; color: #000; }
  .card { border: 1px solid #000; padding: 6px 8px; margin: 0 0 8px; page-break-inside: avoid; }
  .card.rail { width: 180px; }
  .card.rail-sm { width: 140px; font-size: 10px; }
  .card.desc, .card.des-exp, .card.label { width: 260px; }
  .co { font-size: 10px; font-weight: 700; }
  .id { font-size: 12px; font-weight: 700; }
  .title { font-size: 12px; margin: 2px 0; }
  .short { font-size: 11px; }
  .bc { font-family: "Libre Barcode 39", "Courier New", monospace; font-size: 22px; letter-spacing: 1px; margin-top: 4px; }
  .price { font-size: 16px; font-weight: 700; margin-top: 4px; }
  .cost { font-size: 11px; }
  @media print { body { margin: 0; } }
</style></head><body>${cards}
<script>window.onload=function(){window.print();}</scr` + `ipt>
</body></html>`;

    const w = window.open('', '_blank', 'width=420,height=560');
    if (!w) {
        showAlert('Pop-up blocked. Allow pop-ups to print.');
        return;
    }
    w.document.open();
    w.document.write(html);
    w.document.close();
}

function openOpeningBal() {
    if (!isExisting) {
        showAlert('Opening Bal is available only for existing items.');
        return;
    }
    const itemId = requireLoadedItem();
    if (!itemId) return;
    showAlert(`Opening Balance for item ${itemId} — Fin_OpBal screen is not migrated yet.`, 'warning');
}


function bindEnterKey(id, loader) {
    document.getElementById(id).addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            loader();
        }
    });
}

async function loadStats() {
    try {
        const stats = await Api.get(`${API}/stats`);
        document.getElementById('record-count').textContent = formatAmount(stats.record_count, 0);
        document.getElementById('last-item-id').textContent = stats.last_item_id || '0';
    } catch { /* non-blocking */ }
}

function showAlert(msg, type = 'danger') {
    document.getElementById('alert-area').innerHTML = `<div class="alert alert-${type} py-2">${esc(msg)}</div>`;
    setTimeout(() => { document.getElementById('alert-area').innerHTML = ''; }, 6000);
}

function setStatus(label) {
    const text = label || 'Ready';
    document.getElementById('status-label').textContent = text;
    document.getElementById('form-status').textContent = text;
    const el = document.getElementById('status-label');
    el.classList.toggle('is-edit', /^edit$/i.test(text));
}

function val(id) { return document.getElementById(id).value; }
function numVal(id, fallback = 0) {
    const el = document.getElementById(id);
    if (!el) return fallback;
    const raw = (el.tagName === 'INPUT' || el.tagName === 'SELECT') ? el.value : (el.textContent || '');
    const n = parseAmount(raw);
    return Number.isNaN(n) ? fallback : n;
}
function amountDecimals(id) {
    if (id === 'profit_percent') return 2;
    if (id.includes('qty') || id === 'oqty' || id === 'cqty') return 0;
    return 2;
}
function set(id, v) {
    const el = document.getElementById(id);
    if (!el) return;
    el.value = v === null || v === undefined ? '' : v;
}
function setNumber(id, v, decimals = null) {
    const el = document.getElementById(id);
    if (!el) return;
    let text = '';
    if (!(v === null || v === undefined || v === '')) {
        const n = parseAmount(v);
        if (!Number.isNaN(n)) {
            const places = decimals ?? amountDecimals(id);
            text = formatAmount(n, places);
        }
    }
    if (el.tagName === 'INPUT' || el.tagName === 'SELECT' || el.tagName === 'TEXTAREA') {
        if (el.type === 'number') el.type = 'text';
        el.value = text;
    } else {
        el.textContent = text || '0';
    }
}

const AMOUNT_FIELD_IDS = [
    'visacard_rate', 'min_level', 'max_level', 'ro_qty', 'critical_level',
    'min_level1', 'max_level1', 'ro_qty1', 'critical_level1',
    'sales_rate', 'cost_rate', 'sales_price_wo_gst', 'market_price', 'ws_price',
    'gst_amount', 'cost_wo_gst', 'saved_cost_price', 'tp_rate', 'average_cost',
    'profit_percent', 'oqty', 'cqty', 'oamt', 'camt', 'stax_reg', 'stax_unreg',
];

function bindAmountFields() {
    AMOUNT_FIELD_IDS.forEach((id) => {
        const el = document.getElementById(id);
        if (!el || el.tagName !== 'INPUT' || el.readOnly) return;
        el.addEventListener('focus', () => {
            const n = parseAmount(el.value);
            if (!Number.isNaN(n)) el.value = String(n);
        });
        el.addEventListener('blur', () => {
            if (el.value === '') return;
            const n = parseAmount(el.value);
            if (Number.isNaN(n)) {
                el.value = '';
                return;
            }
            if (el.type === 'number') el.type = 'text';
            el.value = formatAmount(n, amountDecimals(id));
        });
    });
}
function setText(id, v) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = v === null || v === undefined ? '' : v;
}

function fmt(v) {
    if (v === null || v === undefined) return '';
    return v;
}

function fmtNum(v, decimals = 2) {
    return formatAmount(v, decimals);
}

function recalcSalesWoGst() {
    const sales = numVal('sales_rate');
    const gst = numVal('gst_amount');
    setNumber('sales_price_wo_gst', sales - gst);
    recalcProfit();
}

function recalcProfit() {
    const salesWo = numVal('sales_price_wo_gst');
    const costWo = numVal('cost_wo_gst');
    if (salesWo > 0 && costWo > 0) {
        setNumber('profit_percent', ((salesWo - costWo) / salesWo) * 100);
    }
}

async function withItemLoad(fn) {
    if (loadingItem) return;
    loadingItem = true;
    setStatus('Loading...');
    try {
        await fn();
    } finally {
        loadingItem = false;
    }
}

async function loadByItemId() {
    const itemId = val('item_id').trim();
    if (!itemId) {
        showAlert('Enter Item ID (system ID or manual ID).');
        return;
    }
    await withItemLoad(async () => {
        try {
            const data = await Api.get(`${API}/by-item-id/${encodeURIComponent(itemId)}`);
            populateForm(data);
            showAlert(`Loaded item ${data.manual_id} — ${data.item_title}`, 'success');
        } catch (e) { showAlert(e.message); setStatus('Ready'); }
    });
}

async function loadByManualId() {
    const manualId = val('manual_id').trim();
    if (!manualId || manualId === '0') {
        showAlert('Enter Manual ID.');
        return;
    }
    await withItemLoad(async () => {
        try {
            const data = await Api.get(`${API}/by-manual-id/${encodeURIComponent(manualId)}`);
            populateForm(data);
            showAlert(`Loaded #${data.manual_id}: ${data.item_title} | Sales ${fmtNum(pick(data, 'sales_rate', 'SALES_RATE'))} | Cost ${fmtNum(pick(data, 'cost_rate', 'COST_RATE'))}`, 'success');
        } catch (e) { showAlert(e.message); setStatus('Ready'); }
    });
}

async function loadByBarcode() {
    const barcode = val('barcodeid').trim();
    if (!barcode || barcode === '0') {
        showAlert('Enter Barcode ID.');
        return;
    }
    await withItemLoad(async () => {
        try {
            const data = await Api.get(`${API}/by-barcode/${encodeURIComponent(barcode)}`);
            populateForm(data);
            showAlert(`Loaded barcode ${barcode}`, 'success');
        } catch (e) { showAlert(e.message); setStatus('Ready'); }
    });
}

async function loadByWsBarcode() {
    const barcode = val('barcodeid_ws').trim();
    if (!barcode || barcode === '0') {
        showAlert('Enter WS Barcode ID.');
        return;
    }
    await withItemLoad(async () => {
        try {
            const data = await Api.get(`${API}/by-ws-barcode/${encodeURIComponent(barcode)}`);
            populateForm(data);
            showAlert(`Loaded WS barcode ${barcode}`, 'success');
        } catch (e) { showAlert(e.message); setStatus('Ready'); }
    });
}

function pick(d, ...keys) {
    for (const k of keys) {
        if (d[k] !== undefined && d[k] !== null) return d[k];
    }
    return null;
}

function populateForm(d) {
    isExisting = !!d.is_existing;
    historyLoadedFor = null;

    set('item_id', fmt(d.item_id));
    setText('item_title', d.item_title || 'Item Title');
    set('item_short', fmt(d.item_short));
    set('item_oem', fmt(d.item_oem));
    set('manual_id', fmt(d.manual_id));
    set('barcodeid', d.barcodeid ?? '0');
    set('barcodeid_ws', d.barcodeid_ws ?? '0');
    setNumber('visacard_rate', d.visacard_rate);
    set('uom_id', fmt(d.uom_id));
    setText('uom_title', d.uom_title || '');
    set('country_id', fmt(d.country_id));
    setText('country_title', d.country_title || '');
    set('item_nature', d.item_nature ?? 0);
    setNumber('min_level', d.min_level);
    setNumber('max_level', d.max_level);
    setNumber('ro_qty', d.ro_qty);
    setNumber('critical_level', d.critical_level);
    setNumber('min_level1', d.min_level1);
    setNumber('max_level1', d.max_level1);
    setNumber('ro_qty1', d.ro_qty1);
    document.getElementById('promotion').checked = !!d.promotion;

    setNumber('sales_rate', pick(d, 'sales_rate', 'SALES_RATE'));
    setNumber('cost_rate', pick(d, 'cost_rate', 'COST_RATE'));
    setNumber('sales_price_wo_gst', pick(d, 'sales_price_wo_gst'));
    setNumber('market_price', pick(d, 'market_price', 'DISC_P1'));
    setNumber('ws_price', pick(d, 'ws_price', 'DISC_P4'));
    setNumber('gst_amount', pick(d, 'gst_amount', 'OAMT1'));
    setNumber('cost_wo_gst', pick(d, 'cost_wo_gst', 'CAMT1'));
    setNumber('saved_cost_price', pick(d, 'saved_cost_price', 'COST_RATE'));
    setNumber('tp_rate', pick(d, 'tp_rate', 'CQTY1'));
    setNumber('average_cost', d.average_cost);
    setNumber('avg_cost_bal', d.average_cost);
    setNumber('profit_percent', d.profit_percent);
    setNumber('last_pur_pct', 0);
    set('remarks', fmt(d.remarks));
    set('co_id', fmt(d.co_id));
    setText('co_title', d.co_title || '');
    document.getElementById('ed_status').checked = !!d.ed_status;
    set('gl_sales_id', fmt(d.gl_sales_id));
    set('gl_pur_id', fmt(d.gl_pur_id));
    set('gl_cons_id', fmt(d.gl_cons_id));
    set('gl_disc_id', fmt(d.gl_disc_id));
    set('gl_stax_id', fmt(d.gl_stax_id));
    setText('gl_sales_title', d.gl_sales_title || '');
    setText('gl_pur_title', d.gl_pur_title || '');
    setText('gl_cons_title', d.gl_cons_title || '');
    setText('gl_disc_title', d.gl_disc_title || '');
    setText('gl_stax_title', d.gl_stax_title || '');
    setNumber('stax_reg', d.stax_reg);
    setNumber('stax_unreg', d.stax_unreg);
    setNumber('oqty', d.oqty);
    setNumber('cqty', d.cqty);
    setNumber('oamt', d.oamt);
    setNumber('camt', d.camt);
    setNumber('oqty1', d.oqty1);
    setNumber('cqty1', d.cqty1);
    setNumber('store_min_disp', d.min_level1);
    setNumber('store_max_disp', d.max_level1);

    fillGrid('grid-purchases', [], true);
    fillGrid('grid-sales', [], false);

    setStatus(d.status_label || (isExisting ? 'Edit' : 'New'));
    document.getElementById('item_id').readOnly = true;
    document.getElementById('manual_id').readOnly = isExisting;
    updateActionButtons();

    if (document.getElementById('chkSetFocus')?.checked) {
        const focusId = isExisting ? 'sales_rate' : 'item_short';
        const el = document.getElementById(focusId);
        el?.focus();
        el?.select?.();
    }

    if (!isExisting) {
        showAlert('Item category found but no Item Master record yet. Enter details and Save.', 'warning');
    } else {
        loadHistory();
    }
}

async function loadHistory() {
    const itemId = val('item_id').trim();
    if (!itemId || !isExisting) return;
    const limit = getHistoryLimit();
    try {
        const data = await Api.get(`${API}/history/${encodeURIComponent(itemId)}?limit=${limit}`);
        fillGrid('grid-purchases', data.last_purchases || [], true);
        fillGrid('grid-sales', data.last_sales || [], false);
        historyLoadedFor = `${itemId}:${limit}`;
    } catch (e) {
        showAlert(e.message || 'Could not load purchase/sales history.');
    }
}

function getHistoryLimit() {
    const n = parseInt(val('no_of_pur'), 10);
    if (Number.isNaN(n) || n < 1) return 5;
    return Math.min(n, 50);
}

function onHistoryLimitChange() {
    const limit = getHistoryLimit();
    set('no_of_pur', String(limit));
    historyLoadedFor = null;
    if (isExisting && val('item_id').trim()) {
        loadHistory();
    }
}

function refreshHistory() {
    if (!isExisting || !val('item_id').trim()) {
        showAlert('Load an item first to refresh purchase/sales history.');
        return;
    }
    onHistoryLimitChange();
}

function fillGrid(tableId, rows, withExtra) {
    const tbody = document.querySelector(`#${tableId} tbody`);
    tbody.innerHTML = '';
    if (!rows?.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-muted">No records</td></tr>';
        return;
    }
    rows.forEach((r, idx) => {
        const date = r.doc_date ? new Date(r.doc_date).toLocaleDateString() : '';
        const cells = [r.doc_no, date, r.party_title, formatAmount(r.qty, 0), r.rate != null ? fmtNum(r.rate) : ''];
        if (withExtra) cells.push(r.extra || '');
        const sel = idx === 0 ? ' class="selected"' : '';
        tbody.innerHTML += `<tr${sel}>${cells.map(c => `<td>${esc(String(c ?? ''))}</td>`).join('')}</tr>`;
    });
    tbody.querySelectorAll('tr').forEach((tr) => {
        tr.addEventListener('click', () => {
            tbody.querySelectorAll('tr').forEach((x) => x.classList.remove('selected'));
            tr.classList.add('selected');
        });
    });
}

async function applyManualDefaults() {
    if (document.getElementById('manual_id').readOnly) {
        showAlert('Manual option is only available for new items.');
        return;
    }
    try {
        const d = await Api.get(`${API}/defaults`);
        set('manual_id', d.manual_id);
        set('uom_id', d.uom_id);
        setText('uom_title', d.uom_title || '');
        set('country_id', d.country_id);
        setText('country_title', d.country_title || '');
        set('co_id', d.co_id);
        setText('co_title', d.co_title || '');
        set('gl_sales_id', d.gl_sales_id);
        set('gl_pur_id', d.gl_pur_id);
        set('gl_cons_id', d.gl_cons_id);
        set('gl_disc_id', d.gl_disc_id);
        set('gl_stax_id', d.gl_stax_id);
        await Promise.all(['sales', 'pur', 'cons', 'disc', 'stax'].map(validateGl));
    } catch (e) { showAlert(e.message); }
}

function copyGlSalesToAll() {
    const salesId = val('gl_sales_id');
    const salesTitle = document.getElementById('gl_sales_title').textContent;
    ['pur', 'cons', 'disc', 'stax'].forEach(k => {
        set(`gl_${k}_id`, salesId);
        setText(`gl_${k}_title`, salesTitle);
    });
}

async function validateLookup(field) {
    const map = { uom_id: 'uom', country_id: 'country', co_id: 'company' };
    const kind = map[field];
    const id = val(field);
    if (!id) return;
    try {
        const r = await Api.get(`${API}/lookup/${kind}/${id}`);
        setText(field.replace('_id', '_title'), r.title);
    } catch (e) {
        showAlert(e.message);
        document.getElementById(field).focus();
    }
}

async function validateGl(kind) {
    const id = val(`gl_${kind}_id`);
    if (!id) return;
    try {
        const r = await Api.get(`${API}/lookup/gl/${id}`);
        setText(`gl_${kind}_title`, r.title);
    } catch (e) {
        showAlert('Account ID not found, please re-enter.');
        document.getElementById(`gl_${kind}_id`).focus();
    }
}

function buildPayload() {
    let title = (document.getElementById('item_title').textContent || '').trim();
    if (!title || title === 'Item Title' || title === '—') title = (val('item_short') || '').trim();
    return {
        item_id: parseFloat(val('item_id')),
        item_title: title,
        item_short: val('item_short'),
        item_oem: val('item_oem'),
        manual_id: parseInt(val('manual_id'), 10),
        barcodeid: val('barcodeid') || '0',
        barcodeid_ws: val('barcodeid_ws') || '0',
        visacard_rate: numVal('visacard_rate'),
        uom_id: parseInt(val('uom_id'), 10),
        country_id: parseInt(val('country_id'), 10),
        item_nature: parseInt(val('item_nature'), 10),
        min_level: numVal('min_level'),
        max_level: numVal('max_level'),
        ro_qty: numVal('ro_qty'),
        critical_level: numVal('critical_level'),
        min_level1: numVal('min_level1'),
        max_level1: numVal('max_level1'),
        ro_qty1: numVal('ro_qty1'),
        promotion: document.getElementById('promotion').checked,
        sales_rate: numVal('sales_rate'),
        cost_rate: numVal('cost_rate'),
        sales_price_wo_gst: numVal('sales_price_wo_gst'),
        market_price: numVal('market_price'),
        ws_price: numVal('ws_price'),
        gst_amount: numVal('gst_amount'),
        cost_wo_gst: numVal('cost_wo_gst'),
        gl_sales_id: parseInt(val('gl_sales_id'), 10),
        gl_pur_id: parseInt(val('gl_pur_id'), 10),
        gl_cons_id: parseInt(val('gl_cons_id'), 10),
        gl_disc_id: parseInt(val('gl_disc_id'), 10),
        gl_stax_id: parseInt(val('gl_stax_id'), 10),
        stax_reg: numVal('stax_reg'),
        stax_unreg: numVal('stax_unreg'),
        remarks: val('remarks') || 'Nil',
        co_id: parseInt(val('co_id'), 10),
        ed_status: document.getElementById('ed_status').checked,
    };
}

async function saveItem() {
    if (!Auth.hasPermission('inventory.fin_item.create') && !Auth.hasPermission('inventory.fin_item.update')) {
        showAlert('No permission to save.');
        return;
    }
    try {
        const result = await Api.post(`${API}/save`, buildPayload());
        showAlert(result.message, 'success');
        await loadStats();
        clearForm();
    } catch (e) { showAlert(e.message); }
}

async function deleteItem() {
    if (!Auth.hasPermission('inventory.fin_item.delete')) {
        showAlert('No permission to delete.');
        return;
    }
    const itemId = val('item_id');
    if (!itemId || !isExisting) return;
    if (!confirm(`Delete Item ID ${itemId}?`)) return;
    try {
        await Api.delete(`${API}/${itemId}`);
        showAlert('Item deleted.', 'success');
        await loadStats();
        clearForm();
    } catch (e) { showAlert(e.message); }
}

function clearForm() {
    isExisting = false;
    historyLoadedFor = null;
    document.querySelectorAll('.vb6-form input, .vb6-form select').forEach(el => {
        if (el.type === 'checkbox') {
            el.checked = false;
        } else if (!el.readOnly) {
            el.value = '';
        }
    });
    document.querySelectorAll('.vb6-form input[readonly], .vb6-form input.ro').forEach(el => {
        el.value = '';
    });
    set('barcodeid', '0');
    set('barcodeid_ws', '0');
    set('item_nature', '0');
    set('no_of_pur', '5');
    const setFocus = document.getElementById('chkSetFocus');
    if (setFocus) setFocus.checked = true;
    setText('item_title', 'Item Title');
    setText('profit_percent', '%');
    setText('average_cost', '0');
    setText('uom_title', '');
    setText('country_title', 'Country of Origin');
    setText('co_title', 'Title of Company');
    ['gl_sales_title', 'gl_pur_title', 'gl_cons_title', 'gl_disc_title', 'gl_stax_title'].forEach(id => setText(id, ''));
    ['oqty1', 'cqty1', 'store_min_disp', 'store_max_disp', 'avg_cost_bal', 'last_pur_pct'].forEach((id) => setNumber(id, id === 'last_pur_pct' ? 0 : ''));
    fillGrid('grid-purchases', [], true);
    fillGrid('grid-sales', [], false);
    document.getElementById('item_id').readOnly = false;
    document.getElementById('manual_id').readOnly = false;
    updateActionButtons();
    setStatus('Ready');
    document.getElementById('manual_id').focus();
    document.getElementById('manual_id').select?.();
}

function openSearch() {
    document.getElementById('search-query').value = '';
    document.getElementById('search-results').innerHTML = '';
    searchModal.show();
    document.getElementById('search-query').focus();
}

async function searchItems() {
    const q = document.getElementById('search-query').value.trim();
    const container = document.getElementById('search-results');
    if (q.length < 1) {
        container.innerHTML = '';
        return;
    }
    try {
        const results = await Api.get(`${API}/search?q=${encodeURIComponent(q)}`);
        if (!results.length) {
            container.innerHTML = '<div class="text-muted p-2">No items found</div>';
            return;
        }
        const rows = results.map(r => `
            <tr class="search-row" data-id="${esc(String(r.id))}" style="cursor:pointer">
                <td>${esc(String(r.id))}</td>
                <td>${esc(String(r.manual_id ?? ''))}</td>
                <td>${esc(r.title)}</td>
                <td>${esc(r.item_short || '')}</td>
                <td>${esc(r.barcodeid || '')}</td>
            </tr>
        `).join('');
        container.innerHTML = `
            <table class="table table-sm table-hover mb-0">
                <thead><tr><th>Item ID</th><th>Manual ID</th><th>Title</th><th>Short</th><th>Barcode</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>`;
        container.querySelectorAll('.search-row').forEach(row => {
            row.addEventListener('click', async () => {
                searchModal.hide();
                set('item_id', row.dataset.id);
                await loadByItemId();
            });
        });
    } catch (e) {
        container.innerHTML = `<div class="text-danger p-2">${esc(e.message || 'Search failed')}</div>`;
    }
}

function debounce(fn, ms) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
}
