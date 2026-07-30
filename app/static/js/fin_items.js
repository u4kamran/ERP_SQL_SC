/** FIN_ITEM inventory CRUD page. */
let itemModal, viewModal;
let currentSkip = 0;
const pageLimit = 50;
let currentSearch = '';

const FIELD_IDS = [
    'item_title','item_short','item_oem','barcodeid','barcodeid_ws','uom_id','country_id',
    'ac_level','ed_status','item_nature','co_id','remarks','sales_rate','cost_rate',
    'visacard_rate','disc_p1','disc_p2','disc_p3','disc_p4','min_level','max_level',
    'ro_qty','critical_level','min_level1','max_level1','ro_qty1','critical_level1',
    'gl_sales_id','gl_pur_id','gl_cons_id','gl_disc_id','gl_stax_id','stax_reg','stax_unreg'
];

document.addEventListener('DOMContentLoaded', async () => {
    await Auth.requireAuth();
    if (!Auth.hasPermission('inventory.fin_item.view')) {
        Auth.showAlert('alert-container', 'You do not have permission to view items.', 'warning');
        return;
    }

    itemModal = new bootstrap.Modal(document.getElementById('itemModal'));
    viewModal = new bootstrap.Modal(document.getElementById('viewModal'));

    if (!Auth.hasPermission('inventory.fin_item.create')) {
        document.getElementById('btn-create-item').style.display = 'none';
    }

    document.getElementById('btn-create-item').addEventListener('click', openCreateModal);
    document.getElementById('itemForm').addEventListener('submit', handleSubmit);
    document.getElementById('search-btn').addEventListener('click', () => { currentSkip = 0; currentSearch = document.getElementById('search-input').value.trim(); loadItems(); });
    document.getElementById('search-input').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); document.getElementById('search-btn').click(); }});
    document.getElementById('prev-page').addEventListener('click', () => { currentSkip = Math.max(0, currentSkip - pageLimit); loadItems(); });
    document.getElementById('next-page').addEventListener('click', () => { currentSkip += pageLimit; loadItems(); });

    await loadItems();
});

async function loadItems() {
    const tbody = document.getElementById('items-table-body');
    try {
        const params = new URLSearchParams({ skip: currentSkip, limit: pageLimit });
        if (currentSearch) params.set('search', currentSearch);
        const data = await Api.get(`/api/v1/fin-items/?${params}`);

        document.getElementById('pagination-info').textContent =
            `Showing ${currentSkip + 1}–${Math.min(currentSkip + data.items.length, data.total)} of ${data.total}`;
        document.getElementById('prev-page').disabled = currentSkip === 0;
        document.getElementById('next-page').disabled = currentSkip + pageLimit >= data.total;

        if (!data.items.length) {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center py-4 text-muted">No items found.</td></tr>';
            return;
        }

        tbody.innerHTML = data.items.map(i => `
            <tr>
                <td>${i.item_id}</td>
                <td>${i.manualid}</td>
                <td>${esc(i.item_title)}</td>
                <td>${esc(i.item_short || '—')}</td>
                <td>${esc(i.barcodeid || '—')}</td>
                <td class="text-end">${fmt(i.sales_rate)}</td>
                <td class="text-end">${fmt(i.oqty, 0)}</td>
                <td class="text-end">${fmt(i.cqty, 0)}</td>
                <td>${i.ed_status === 0 ? '<span class="badge bg-success">Active</span>' : '<span class="badge bg-secondary">Inactive</span>'}</td>
                <td class="text-end table-actions">
                    <button class="btn btn-sm btn-outline-info" onclick='viewItem(${i.item_id})' title="View"><i class="bi bi-eye"></i></button>
                    ${Auth.hasPermission('inventory.fin_item.update') ? `<button class="btn btn-sm btn-outline-primary" onclick='editItem(${i.item_id})' title="Edit"><i class="bi bi-pencil"></i></button>` : ''}
                    ${Auth.hasPermission('inventory.fin_item.delete') ? `<button class="btn btn-sm btn-outline-danger" onclick='deleteItem(${i.item_id}, "${esc(i.item_title)}")' title="Delete"><i class="bi bi-trash"></i></button>` : ''}
                </td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="10" class="text-center text-danger py-4">${esc(err.message)}</td></tr>`;
    }
}

function getFormData() {
    const data = {};
    FIELD_IDS.forEach(f => {
        const el = document.getElementById(`f-${f}`);
        if (!el) return;
        const val = el.value;
        if (el.type === 'number') data[f] = val === '' ? 0 : Number(val);
        else data[f] = val || null;
    });
    return data;
}

function setFormData(item) {
    FIELD_IDS.forEach(f => {
        const el = document.getElementById(`f-${f}`);
        if (el && item[f] !== undefined && item[f] !== null) el.value = item[f];
    });
}

function openCreateModal() {
    document.getElementById('itemModalTitle').textContent = 'New Item';
    document.getElementById('item-id').value = '';
    document.getElementById('itemForm').reset();
    document.getElementById('f-uom_id').value = 1;
    document.getElementById('f-country_id').value = 1;
    document.getElementById('f-ac_level').value = 4;
    document.getElementById('item-form-error').classList.add('d-none');
    itemModal.show();
}

async function editItem(itemId) {
    try {
        const item = await Api.get(`/api/v1/fin-items/${itemId}`);
        document.getElementById('itemModalTitle').textContent = `Edit Item #${item.item_id}`;
        document.getElementById('item-id').value = item.item_id;
        setFormData(item);
        document.getElementById('item-form-error').classList.add('d-none');
        itemModal.show();
    } catch (err) {
        Auth.showAlert('alert-container', err.message, 'danger');
    }
}

async function viewItem(itemId) {
    try {
        const item = await Api.get(`/api/v1/fin-items/${itemId}`);
        document.getElementById('view-detail').textContent = JSON.stringify(item, null, 2);
        viewModal.show();
    } catch (err) {
        Auth.showAlert('alert-container', err.message, 'danger');
    }
}

async function handleSubmit(e) {
    e.preventDefault();
    const errEl = document.getElementById('item-form-error');
    errEl.classList.add('d-none');
    const itemId = document.getElementById('item-id').value;
    const payload = getFormData();

    try {
        if (itemId) {
            await Api.put(`/api/v1/fin-items/${itemId}`, payload);
            Auth.showAlert('alert-container', 'Item updated successfully.', 'success');
        } else {
            await Api.post('/api/v1/fin-items/', payload);
            Auth.showAlert('alert-container', 'Item created successfully.', 'success');
        }
        itemModal.hide();
        await loadItems();
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('d-none');
    }
}

async function deleteItem(itemId, title) {
    if (!confirm(`Delete item "${title}" (ID: ${itemId})? This cannot be undone.`)) return;
    try {
        await Api.delete(`/api/v1/fin-items/${itemId}`);
        Auth.showAlert('alert-container', 'Item deleted.', 'success');
        await loadItems();
    } catch (err) {
        Auth.showAlert('alert-container', err.message, 'danger');
    }
}

function esc(s) { const d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }
function fmt(n, decimals = 2) {
    return n != null && n !== '' ? formatAmount(n, decimals) : '—';
}
