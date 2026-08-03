const API = '/api/v1/vouchers';

let config = null;
let currentBook = null;
let lines = [];
let editingLineIndex = -1;
let isEditingVoucher = false;
let searchModal = null;
let searchMode = 'book';
let booksCache = [];
let isSystemEntry = false;

document.addEventListener('DOMContentLoaded', async () => {
    await Auth.requireAuth();
    if (!Auth.hasPermission('gl.voucher.view')) {
        document.getElementById('voucher-app').innerHTML = '<div class="alert alert-danger">Access denied.</div>';
        return;
    }

    searchModal = new bootstrap.Modal(document.getElementById('searchModal'));
    document.getElementById('voucher_date').value = new Date().toISOString().slice(0, 10);
    bindEvents();
    await loadConfig();
    await loadBooks();
});

function bindEvents() {
    document.getElementById('btn-save').addEventListener('click', saveVoucher);
    document.getElementById('btn-clear').addEventListener('click', clearForm);
    document.getElementById('btn-delete').addEventListener('click', deleteVoucher);
    document.getElementById('btn-add-line').addEventListener('click', addOrUpdateLine);
    document.getElementById('btn-clear-line').addEventListener('click', () => clearLineForm({ keepNarRef: false }));
    document.getElementById('btn-copy-nar').addEventListener('click', copyNarToAll);
    document.getElementById('btn-system-entry').addEventListener('click', () => systemEntry());
    document.getElementById('btn-repeat-last').addEventListener('click', repeatLast);
    document.getElementById('btn-load-voucher').addEventListener('click', loadVoucher);
    document.getElementById('btn-book-search').addEventListener('click', () => openSearch('book'));
    document.getElementById('btn-account-search').addEventListener('click', () => openSearch('account'));

    document.getElementById('book_id').addEventListener('change', onBookChange);
    document.getElementById('voucher_date').addEventListener('change', syncFiscalFromDate);
    document.getElementById('book_id').addEventListener('input', () => {
        if (!document.getElementById('book_id').value) {
            currentBook = null;
            setVModeOptions(true, true, true);
            updateSystemEntryButton();
        }
    });
    document.getElementById('line_ac_id').addEventListener('change', validateAccount);
    document.getElementById('line_narration').addEventListener('input', debounce(searchNarrationInline, 250));
    document.getElementById('line_debit').addEventListener('input', onAmountInput);
    document.getElementById('line_credit').addEventListener('input', onAmountInput);

    document.querySelectorAll('input[name="v_mode"]').forEach(el => {
        el.addEventListener('change', () => {
            onModeChange();
            refreshNextNumber();
        });
    });

    document.getElementById('search-query').addEventListener('input', debounce(runSearch, 300));

    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            saveVoucher();
        }
        if (e.key === 'F2') {
            e.preventDefault();
            document.getElementById('line_narration').focus();
            searchNarrationInline();
        }
        if (e.key === 'F6') {
            e.preventDefault();
            systemEntry();
        }
    });
}

async function loadConfig() {
    try {
        config = await Api.get(`${API}/config`);
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

async function loadBooks() {
    try {
        booksCache = await Api.get(`${API}/books`);
    } catch (err) {
        showAlert(err.message, 'warning');
    }
}

async function onBookChange() {
    const bookId = parseInt(document.getElementById('book_id').value, 10);
    if (!bookId) {
        currentBook = null;
        return;
    }
    try {
        currentBook = await Api.get(`${API}/books/${bookId}`);
        document.getElementById('book_title').value = currentBook.book_title || '';
        document.getElementById('book_balance').value = formatMoney(currentBook.book_balance || 0);
        document.getElementById('book_ac_label').textContent = currentBook.ac_id
            ? `Book A/C: ${currentBook.ac_id}`
            : 'Book A/C: — (JV book)';
        applyBookRules();
        await refreshNextNumber();
    } catch (err) {
        showAlert(err.message, 'danger');
        currentBook = null;
    }
}

function applyBookRules() {
    if (!currentBook) {
        setVModeOptions(true, true, true);
        updateSystemEntryButton();
        return;
    }

    const isJvBook = currentBook.book_type === 2;
    const isCombine = currentBook.v_combination === 1;

    if (isJvBook || isCombine) {
        // JV book, or Cash/Bank with Combine numbering → JV only
        setVModeOptions(true, false, false);
        document.getElementById('v_mode_1').checked = true;
    } else {
        // Cash/Bank with Separate numbering → Payment / Receipt only
        setVModeOptions(false, true, true);
        document.getElementById('v_mode_2').checked = true;
    }

    if (currentBook.v_numbering === 1) {
        document.getElementById('fiscal').value = '0';
        document.getElementById('fiscal').readOnly = true;
    } else {
        document.getElementById('fiscal').readOnly = false;
        const m = new Date(document.getElementById('voucher_date').value).getMonth() + 1;
        if (!document.getElementById('fiscal').value || document.getElementById('fiscal').value === '0') {
            document.getElementById('fiscal').value = String(m);
        }
    }
    onModeChange();
    updateSystemEntryButton();
    refreshNextNumber();
}

function setVModeOptions(jvEnabled, paymentEnabled, receiptEnabled) {
    setModeOption('v_mode_1', jvEnabled);
    setModeOption('v_mode_2', paymentEnabled);
    setModeOption('v_mode_3', receiptEnabled);
}

function setModeOption(inputId, enabled) {
    const input = document.getElementById(inputId);
    const label = document.querySelector(`label[for="${inputId}"]`);
    if (!input) return;
    input.disabled = !enabled;
    if (label) {
        label.classList.toggle('disabled', !enabled);
        label.classList.toggle('voucher-mode-off', !enabled);
    }
}

function updateSystemEntryButton() {
    const btn = document.getElementById('btn-system-entry');
    if (!btn) return;
    btn.disabled = !(currentBook && currentBook.book_type !== 2 && currentBook.ac_id);
}

function getGridTotalsExcludingEdit() {
    let debit = 0;
    let credit = 0;
    lines.forEach((line, index) => {
        if (index === editingLineIndex) return;
        debit += parseFloat(line.debit) || 0;
        credit += parseFloat(line.credit) || 0;
    });
    return { debit, credit };
}

function roundMoney(value) {
    return Math.round((value + Number.EPSILON) * 100) / 100;
}

function lockSystemEntryAmounts() {
    const debitEl = document.getElementById('line_debit');
    const creditEl = document.getElementById('line_credit');
    debitEl.readOnly = true;
    creditEl.readOnly = true;
    debitEl.classList.add('vbc-readonly');
    creditEl.classList.add('vbc-readonly');
}

function unlockLineAmounts() {
    const debitEl = document.getElementById('line_debit');
    const creditEl = document.getElementById('line_credit');
    debitEl.readOnly = false;
    creditEl.readOnly = false;
    debitEl.classList.remove('vbc-readonly');
    creditEl.classList.remove('vbc-readonly');
}

/** VB6 CmdSystem_Click — fill book account + balancing amount only; user clicks Add Line. */
async function systemEntry() {
    if (editingLineIndex >= 0) {
        showAlert('Cancel line edit (Clear) before using S-Entry.', 'warning');
        return;
    }
    if (!currentBook || !currentBook.ac_id || currentBook.book_type === 2) {
        showAlert('S-Entry needs a Cash or Bank book with a linked book account.', 'warning');
        return;
    }

    const totals = getGridTotalsExcludingEdit();
    const balance = roundMoney(totals.debit - totals.credit);
    if (balance === 0 && lines.length === 0) {
        showAlert('Add other transaction lines first, then use S-Entry for the book balancing line.', 'warning');
        return;
    }

    isSystemEntry = true;
    document.getElementById('line_ac_id').value = String(currentBook.ac_id);
    await validateAccount();

    const debitEl = document.getElementById('line_debit');
    const creditEl = document.getElementById('line_credit');
    debitEl.value = '';
    creditEl.value = '';

    if (balance >= 0) {
        if (balance > 0) creditEl.value = balance.toFixed(2);
    } else {
        debitEl.value = Math.abs(balance).toFixed(2);
    }

    lockSystemEntryAmounts();
    document.getElementById('line_narration').focus();
}

function onModeChange(preserveAmounts = false) {
    if (isSystemEntry) return;
    unlockLineAmounts();
    const mode = getVMode();
    const debit = document.getElementById('line_debit');
    const credit = document.getElementById('line_credit');
    if (mode === 2) {
        if (!preserveAmounts) credit.value = '';
        credit.disabled = true;
        debit.disabled = false;
    } else if (mode === 3) {
        if (!preserveAmounts) debit.value = '';
        debit.disabled = true;
        credit.disabled = false;
    } else {
        debit.disabled = false;
        credit.disabled = false;
    }
}

function getVMode() {
    const checked = document.querySelector('input[name="v_mode"]:checked');
    return checked ? parseInt(checked.value, 10) : 1;
}

function getFiscal() {
    return parseInt(document.getElementById('fiscal').value || '0', 10);
}

function syncFiscalFromDate() {
    if (!currentBook || currentBook.v_numbering !== 2 || isEditingVoucher) return;
    const m = new Date(document.getElementById('voucher_date').value).getMonth() + 1;
    if (m >= 1 && m <= 12) {
        document.getElementById('fiscal').value = String(m);
        refreshNextNumber();
    }
}

/** Cash/Bank monthly books use MM-voucher_no (e.g. 07-537). */
function parseVoucherInput(raw) {
    const text = String(raw || '').trim();
    const match = text.match(/^(\d{1,2})-(\d+)$/);
    if (match) {
        return {
            fiscal: parseInt(match[1], 10),
            voucherId: parseInt(match[2], 10),
        };
    }
    const voucherId = parseInt(text.replace(/\D/g, ''), 10);
    return {
        fiscal: null,
        voucherId: Number.isFinite(voucherId) ? voucherId : NaN,
    };
}

async function refreshNextNumber() {
    if (!currentBook || isEditingVoucher) return;
    try {
        const data = await Api.get(
            `${API}/next-number?book_id=${currentBook.book_id}&v_mode=${getVMode()}&fiscal=${getFiscal()}`
        );
        document.getElementById('voucher_id').placeholder = data.voucher_display || String(data.voucher_id);
    } catch (_) { /* ignore */ }
}

function onAmountInput(e) {
    if (isSystemEntry) return;
    const mode = getVMode();
    if (mode === 2 && e.target.id === 'line_debit' && parseFloat(e.target.value) > 0) {
        document.getElementById('line_credit').value = '';
    }
    if (mode === 3 && e.target.id === 'line_credit' && parseFloat(e.target.value) > 0) {
        document.getElementById('line_debit').value = '';
    }
}

async function validateAccount() {
    const raw = document.getElementById('line_ac_id').value.replace(/\D/g, '');
    if (!raw) {
        document.getElementById('line_ac_title').textContent = '—';
        return;
    }
    const acId = parseInt(raw, 10);
    try {
        const acct = await Api.get(`${API}/accounts/${acId}`);
        document.getElementById('line_ac_id').value = acct.ac_id;
        document.getElementById('line_ac_title').textContent = `${acct.ac_title} (Bal: ${formatMoney(acct.cbal || 0)})`;
        if (!isSystemEntry) {
            const last = await Api.get(`${API}/narrations/last/${acId}`);
            if (last.narration && !document.getElementById('line_narration').value) {
                document.getElementById('line_narration').value = last.narration;
            }
        }
    } catch (err) {
        document.getElementById('line_ac_title').textContent = err.message;
    }
}

async function searchNarrationInline() {
    const q = document.getElementById('line_narration').value.trim();
    const dropdown = document.getElementById('nar-dropdown');
    if (q.length < 2) {
        dropdown.classList.add('d-none');
        return;
    }
    const acRaw = document.getElementById('line_ac_id').value.replace(/\D/g, '');
    const acId = acRaw ? parseInt(acRaw, 10) : null;
    let url = `${API}/narrations/search?q=${encodeURIComponent(q)}`;
    if (acId) url += `&ac_id=${acId}`;
    try {
        const rows = await Api.get(url);
        if (!rows.length) {
            dropdown.classList.add('d-none');
            return;
        }
        dropdown.innerHTML = rows.map((r, i) =>
            `<div class="nar-item${i === 0 ? ' active' : ''}" data-nar="${escapeAttr(r.narration)}">${escapeHtml(r.narration)} <small class="text-muted">(${r.source})</small></div>`
        ).join('');
        dropdown.classList.remove('d-none');
        dropdown.querySelectorAll('.nar-item').forEach(el => {
            el.addEventListener('click', () => {
                document.getElementById('line_narration').value = el.dataset.nar;
                dropdown.classList.add('d-none');
            });
        });
    } catch (_) {
        dropdown.classList.add('d-none');
    }
}

function addOrUpdateLine() {
    const acRaw = document.getElementById('line_ac_id').value.replace(/\D/g, '');
    if (!acRaw) {
        showAlert('Account ID required.', 'warning');
        return;
    }
    const line = {
        ac_id: parseInt(acRaw, 10),
        narration: document.getElementById('line_narration').value.trim() || 'Nil',
        debit: parseFloat(document.getElementById('line_debit').value) || 0,
        credit: parseFloat(document.getElementById('line_credit').value) || 0,
        reference: document.getElementById('line_reference').value.trim(),
        ac_title: document.getElementById('line_ac_title').textContent,
        is_system_entry: Boolean(isSystemEntry),
    };
    if (line.debit === 0 && line.credit === 0) {
        showAlert('Enter debit or credit amount.', 'warning');
        return;
    }
    if (editingLineIndex >= 0) {
        lines[editingLineIndex] = line;
        editingLineIndex = -1;
        document.getElementById('btn-add-line').textContent = 'Add Line';
    } else {
        if (config && lines.length >= config.max_entries) {
            showAlert(`Maximum ${config.max_entries} lines allowed.`, 'warning');
            return;
        }
        lines.push(line);
    }
    renderLines();
    clearLineForm({ keepNarRef: true });
}

/** VB6 ClearTrans — account and amounts clear; narration & reference kept for next line. */
function clearLineForm({ keepNarRef = false } = {}) {
    isSystemEntry = false;
    unlockLineAmounts();
    document.getElementById('line_ac_id').value = '';
    document.getElementById('line_debit').value = '';
    document.getElementById('line_credit').value = '';
    document.getElementById('line_ac_title').textContent = '—';
    if (!keepNarRef) {
        document.getElementById('line_narration').value = '';
        document.getElementById('line_reference').value = '';
    }
    editingLineIndex = -1;
    document.getElementById('btn-add-line').textContent = 'Add Line';
    onModeChange();
    document.getElementById('line_ac_id').focus();
}

function renderLines() {
    const tbody = document.getElementById('lines-body');
    tbody.innerHTML = lines.map((line, idx) => `
        <tr data-idx="${idx}">
            <td>${idx + 1}</td>
            <td>${line.ac_id}</td>
            <td>${escapeHtml(line.narration)}</td>
            <td class="text-end">${line.debit ? formatMoney(line.debit) : ''}</td>
            <td class="text-end">${line.credit ? formatMoney(line.credit) : ''}</td>
            <td>${escapeHtml(line.reference || '')}</td>
            <td>
                ${line.is_system_entry ? '<span class="text-muted small">S-Entry</span>' : `<button class="btn btn-link btn-sm p-0 me-1" onclick="editLine(${idx})">Edit</button>`}
                <button class="btn btn-link btn-sm p-0 text-danger" onclick="removeLine(${idx})">Del</button>
            </td>
        </tr>
    `).join('');
    updateTotals();
}

window.editLine = function (idx) {
    const line = lines[idx];
    if (line.is_system_entry) {
        showAlert('System entry line cannot be edited. Delete it and use S-Entry again.', 'warning');
        return;
    }
    editingLineIndex = idx;
    isSystemEntry = false;
    document.getElementById('line_ac_id').value = line.ac_id;
    document.getElementById('line_narration').value = line.narration;
    document.getElementById('line_debit').value = line.debit || '';
    document.getElementById('line_credit').value = line.credit || '';
    document.getElementById('line_reference').value = line.reference || '';
    document.getElementById('line_ac_title').textContent = line.ac_title || '—';
    document.getElementById('btn-add-line').textContent = 'Update Line';
    onModeChange(true);
    validateAccount();
};

window.removeLine = function (idx) {
    lines.splice(idx, 1);
    renderLines();
};

function updateTotals() {
    const dr = lines.reduce((s, l) => s + (parseFloat(l.debit) || 0), 0);
    const cr = lines.reduce((s, l) => s + (parseFloat(l.credit) || 0), 0);
    document.getElementById('totals').value = `${formatMoney(dr)} / ${formatMoney(cr)}`;
    const badge = document.getElementById('balance-badge');
    if (Math.abs(dr - cr) < 0.005 && dr > 0) {
        badge.textContent = 'Balanced';
        badge.className = 'badge balanced';
    } else {
        badge.textContent = `Diff: ${formatMoney(dr - cr)}`;
        badge.className = 'badge unbalanced';
    }
}

function copyNarToAll() {
    if (!lines.length) return;
    const nar = lines[0].narration;
    lines.forEach(l => { l.narration = nar; });
    renderLines();
    showAlert('Narration copied to all lines.', 'success');
}

async function repeatLast() {
    const bookId = parseInt(document.getElementById('book_id').value, 10);
    if (!bookId) {
        showAlert('Select a book first.', 'warning');
        return;
    }
    try {
        const rows = await Api.get(`${API}/repeat-last/${bookId}`);
        lines = rows.map(r => ({
            ac_id: r.ac_id,
            narration: r.narration,
            debit: r.debit,
            credit: r.credit,
            reference: r.reference || '',
            ac_title: r.ac_title || '',
        }));
        isEditingVoucher = false;
        document.getElementById('serial_no').value = '';
        document.getElementById('voucher_id').value = '';
        document.getElementById('btn-delete').disabled = true;
        renderLines();
        showAlert('Last voucher lines loaded as template. Save to create new voucher.', 'info');
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

async function loadVoucher() {
    const bookId = parseInt(document.getElementById('book_id').value, 10);
    const parsed = parseVoucherInput(document.getElementById('voucher_id').value);
    if (!bookId || !parsed.voucherId) {
        showAlert('Enter Book ID and Voucher number (e.g. 07-537 for July voucher 537).', 'warning');
        return;
    }
    if (parsed.fiscal !== null) {
        document.getElementById('fiscal').value = String(parsed.fiscal);
    }
    const fiscal = getFiscal();
    try {
        const data = await Api.get(
            `${API}/load?book_id=${bookId}&voucher_id=${parsed.voucherId}&v_mode=${getVMode()}&fiscal=${fiscal}`
        );
        await fillVoucher(data);
        showAlert('Voucher loaded.', 'success');
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

async function fillVoucher(data) {
    isEditingVoucher = true;
    document.getElementById('serial_no').value = data.serial_no;
    document.getElementById('voucher_id').value = data.voucher_id;
    document.getElementById('book_id').value = data.book_id;
    document.getElementById('voucher_date').value = data.voucher_date;
    document.getElementById('fiscal').value = data.fiscal;
    document.getElementById('remarks').value = data.remarks || '';
    await onBookChange();
    const modeInput = document.querySelector(`input[name="v_mode"][value="${data.v_mode}"]`);
    if (modeInput && !modeInput.disabled) {
        modeInput.checked = true;
    }
    lines = (data.lines || []).map(l => ({
        ac_id: l.ac_id,
        narration: l.narration,
        debit: l.debit,
        credit: l.credit,
        reference: l.reference || '',
        ac_title: l.ac_title || '',
    }));
    document.getElementById('btn-delete').disabled = !Auth.hasPermission('gl.voucher.delete');
    document.getElementById('mode-badge').textContent = 'Editing';
    renderLines();
    onModeChange(true);
}

function buildPayload() {
    return {
        book_id: parseInt(document.getElementById('book_id').value, 10),
        v_mode: getVMode(),
        fiscal: getFiscal(),
        voucher_date: document.getElementById('voucher_date').value,
        remarks: document.getElementById('remarks').value,
        voucher_id: parseVoucherInput(document.getElementById('voucher_id').value).voucherId || null,
        serial_no: parseFloat(document.getElementById('serial_no').value) || null,
        lines: lines.map(l => ({
            ac_id: l.ac_id,
            narration: l.narration,
            debit: l.debit,
            credit: l.credit,
            reference: l.reference || '',
        })),
    };
}

async function saveVoucher() {
    if (!Auth.hasPermission(isEditingVoucher ? 'gl.voucher.edit' : 'gl.voucher.create')) {
        showAlert('No permission to save.', 'danger');
        return;
    }
    if (!lines.length) {
        showAlert('Add at least one line.', 'warning');
        return;
    }
    const payload = buildPayload();
    try {
        let result;
        const serial = document.getElementById('serial_no').value;
        if (isEditingVoucher && serial) {
            result = await Api.put(`${API}/${serial}`, payload);
        } else {
            result = await Api.post(API, payload);
        }
        showAlert(result.message, 'success');
        clearForm();
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

async function deleteVoucher() {
    const serial = document.getElementById('serial_no').value;
    if (!serial || !confirm('Delete this voucher?')) return;
    try {
        const result = await Api.delete(`${API}/${serial}`);
        showAlert(result.message, 'success');
        clearForm();
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function clearForm() {
    isEditingVoucher = false;
    lines = [];
    document.getElementById('serial_no').value = '';
    document.getElementById('voucher_id').value = '';
    document.getElementById('remarks').value = '';
    document.getElementById('book_balance').value = '';
    document.getElementById('btn-delete').disabled = true;
    document.getElementById('mode-badge').textContent = 'Ready';
    document.getElementById('voucher_date').value = new Date().toISOString().slice(0, 10);
    renderLines();
    clearLineForm();
    if (currentBook) refreshNextNumber();
}

function openSearch(mode) {
    searchMode = mode;
    document.getElementById('search-modal-title').textContent = mode === 'book' ? 'Select Book' : 'Select Account';
    document.getElementById('search-head').innerHTML = mode === 'book'
        ? '<tr><th>ID</th><th>Title</th><th>Type</th></tr>'
        : '<tr><th>ID</th><th>Title</th><th>Balance</th></tr>';
    document.getElementById('search-query').value = '';
    document.getElementById('search-results').innerHTML = '';
    searchModal.show();
    if (mode === 'book' && booksCache.length) {
        renderBookResults(booksCache);
    }
    setTimeout(() => document.getElementById('search-query').focus(), 300);
}

async function runSearch() {
    const q = document.getElementById('search-query').value.trim();
    if (searchMode === 'book') {
        const filtered = booksCache.filter(b =>
            String(b.book_id).includes(q) || (b.book_title || '').toLowerCase().includes(q.toLowerCase())
        );
        renderBookResults(filtered);
        return;
    }
    if (q.length < 1) return;
    try {
        const rows = await Api.get(`${API}/accounts/search?q=${encodeURIComponent(q)}`);
        document.getElementById('search-results').innerHTML = rows.map(r => `
            <tr style="cursor:pointer" onclick="pickAccount(${r.ac_id})">
                <td>${r.ac_id}</td>
                <td>${escapeHtml(r.ac_title)}</td>
                <td class="text-end">${formatMoney(r.cbal || 0)}</td>
            </tr>
        `).join('');
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function renderBookResults(rows) {
    document.getElementById('search-results').innerHTML = rows.map(b => `
        <tr style="cursor:pointer" onclick="pickBook(${b.book_id})">
            <td>${b.book_id}</td>
            <td>${escapeHtml(b.book_title)}</td>
            <td>${b.book_type === 2 ? 'JV' : b.book_type === 1 ? 'Cash' : 'Bank'}</td>
        </tr>
    `).join('');
}

window.pickBook = function (bookId) {
    document.getElementById('book_id').value = bookId;
    searchModal.hide();
    onBookChange();
};

window.pickAccount = function (acId) {
    document.getElementById('line_ac_id').value = acId;
    searchModal.hide();
    validateAccount();
};

function showAlert(message, type = 'info') {
    const area = document.getElementById('alert-area');
    area.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show py-2" role="alert">
        ${escapeHtml(message)}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>`;
}

function debounce(fn, ms) {
    let t;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), ms);
    };
}

function escapeHtml(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function escapeAttr(s) {
    return String(s || '').replace(/"/g, '&quot;');
}

function formatMoney(n) {
    if (typeof formatAmount === 'function') return formatAmount(n, 2);
    return Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
