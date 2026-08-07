/** CUST_SMS master CRUD page. */
const API = '/api/v1/cust-sms';
let editModal, viewModal;
let currentSkip = 0;
const pageLimit = 50;
let currentSearch = '';

const FIELD_IDS = [
    'cust_name', 'mobile_no', 'mobile_no_tmp', 'cust_address', 'status',
    'star_rating', 'star_rating_value', 'star_rating_visit', 'star_rating_visit_value',
    'star_rating_tsales', 'star_rating_tsales_value',
];

document.addEventListener('DOMContentLoaded', async () => {
    await Auth.requireAuth();
    if (!Auth.hasPermission('marketing.cust_sms.view') && !Auth.hasPermission('auth.admin.full')) {
        Auth.showAlert('alert-container', 'You do not have permission to view CUST_SMS.', 'warning');
        return;
    }

    editModal = new bootstrap.Modal(document.getElementById('editModal'));
    viewModal = new bootstrap.Modal(document.getElementById('viewModal'));

    const canCreate = Auth.hasPermission('marketing.cust_sms.create') || Auth.hasPermission('auth.admin.full');
    if (!canCreate) document.getElementById('btn-create').style.display = 'none';

    document.getElementById('btn-create').addEventListener('click', openCreateModal);
    document.getElementById('edit-form').addEventListener('submit', handleSubmit);
    document.getElementById('search-btn').addEventListener('click', () => {
        currentSkip = 0;
        currentSearch = document.getElementById('search-input').value.trim();
        loadRows();
    });
    document.getElementById('search-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            document.getElementById('search-btn').click();
        }
    });
    document.getElementById('prev-page').addEventListener('click', () => {
        currentSkip = Math.max(0, currentSkip - pageLimit);
        loadRows();
    });
    document.getElementById('next-page').addEventListener('click', () => {
        currentSkip += pageLimit;
        loadRows();
    });

    await loadRows();
});

async function loadRows() {
    const tbody = document.getElementById('table-body');
    try {
        const params = new URLSearchParams({ skip: currentSkip, limit: pageLimit });
        if (currentSearch) params.set('search', currentSearch);
        const data = await Api.get(`${API}/?${params}`);

        document.getElementById('pagination-info').textContent =
            data.total
                ? `Showing ${currentSkip + 1}–${Math.min(currentSkip + data.items.length, data.total)} of ${data.total}`
                : 'No records';
        document.getElementById('prev-page').disabled = currentSkip === 0;
        document.getElementById('next-page').disabled = currentSkip + pageLimit >= data.total;

        if (!data.items.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-muted">No CUST_SMS records found.</td></tr>';
            return;
        }

        const canUpdate = Auth.hasPermission('marketing.cust_sms.update') || Auth.hasPermission('auth.admin.full');
        const canDelete = Auth.hasPermission('marketing.cust_sms.delete') || Auth.hasPermission('auth.admin.full');

        tbody.innerHTML = data.items.map((r) => `
            <tr>
                <td>${r.cust_id}</td>
                <td>${esc(r.cust_name || '—')}</td>
                <td>${esc(r.mobile_no || '—')}</td>
                <td>${esc(r.mobile_no_tmp || '—')}</td>
                <td class="text-truncate" style="max-width:220px" title="${esc(r.cust_address || '')}">${esc(r.cust_address || '—')}</td>
                <td>${r.status == null ? '—' : r.status}</td>
                <td class="small">${fmtDate(r.added_datetime)}</td>
                <td class="text-end table-actions text-nowrap">
                    <button class="btn btn-sm btn-outline-info" data-view="${r.cust_id}" title="View"><i class="bi bi-eye"></i></button>
                    ${canUpdate ? `<button class="btn btn-sm btn-outline-primary" data-edit="${r.cust_id}" title="Edit"><i class="bi bi-pencil"></i></button>` : ''}
                    ${canDelete ? `<button class="btn btn-sm btn-outline-danger" data-del="${r.cust_id}" data-name="${esc(r.cust_name || '')}" title="Delete"><i class="bi bi-trash"></i></button>` : ''}
                </td>
            </tr>
        `).join('');

        tbody.querySelectorAll('[data-view]').forEach((btn) => {
            btn.addEventListener('click', () => viewRow(Number(btn.dataset.view)));
        });
        tbody.querySelectorAll('[data-edit]').forEach((btn) => {
            btn.addEventListener('click', () => editRow(Number(btn.dataset.edit)));
        });
        tbody.querySelectorAll('[data-del]').forEach((btn) => {
            btn.addEventListener('click', () => deleteRow(Number(btn.dataset.del), btn.dataset.name || ''));
        });
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger py-4">${esc(err.message)}</td></tr>`;
    }
}

function getFormData() {
    const data = {};
    FIELD_IDS.forEach((f) => {
        const el = document.getElementById(`f-${f}`);
        if (!el) return;
        const val = el.value.trim();
        if (f === 'status') data[f] = val === '' ? null : Number(val);
        else data[f] = val || null;
    });
    return data;
}

function setFormData(row) {
    FIELD_IDS.forEach((f) => {
        const el = document.getElementById(`f-${f}`);
        if (!el) return;
        const val = row[f];
        el.value = val == null ? '' : val;
    });
}

function openCreateModal() {
    document.getElementById('modal-title').textContent = 'New Customer SMS';
    document.getElementById('cust-id').value = '';
    document.getElementById('edit-form').reset();
    document.getElementById('form-error').classList.add('d-none');
    editModal.show();
}

async function editRow(custId) {
    try {
        const row = await Api.get(`${API}/${custId}`);
        document.getElementById('modal-title').textContent = `Edit CUST_SMS #${row.cust_id}`;
        document.getElementById('cust-id').value = row.cust_id;
        setFormData(row);
        document.getElementById('form-error').classList.add('d-none');
        editModal.show();
    } catch (err) {
        Auth.showAlert('alert-container', err.message, 'danger');
    }
}

async function viewRow(custId) {
    try {
        const row = await Api.get(`${API}/${custId}`);
        const fields = [
            ['CUST_ID', row.cust_id],
            ['Name', row.cust_name],
            ['Mobile', row.mobile_no],
            ['Alt Mobile', row.mobile_no_tmp],
            ['Address', row.cust_address],
            ['Status', row.status],
            ['Added', fmtDate(row.added_datetime)],
            ['Star Rating', row.star_rating],
            ['Star Value', row.star_rating_value],
            ['Visit Rating', row.star_rating_visit],
            ['Visit Value', row.star_rating_visit_value],
            ['TSales Rating', row.star_rating_tsales],
            ['TSales Value', row.star_rating_tsales_value],
        ];
        document.getElementById('view-detail').innerHTML = fields.map(([k, v]) => `
            <dt class="col-sm-4">${esc(k)}</dt>
            <dd class="col-sm-8">${esc(v == null || v === '' ? '—' : String(v))}</dd>
        `).join('');
        viewModal.show();
    } catch (err) {
        Auth.showAlert('alert-container', err.message, 'danger');
    }
}

async function handleSubmit(e) {
    e.preventDefault();
    const errEl = document.getElementById('form-error');
    errEl.classList.add('d-none');
    const custId = document.getElementById('cust-id').value;
    const payload = getFormData();

    if (!payload.cust_name || !payload.mobile_no) {
        errEl.textContent = 'Name and Mobile No are required.';
        errEl.classList.remove('d-none');
        return;
    }

    try {
        if (custId) {
            await Api.put(`${API}/${custId}`, payload);
            Auth.showAlert('alert-container', 'Record updated successfully.', 'success');
        } else {
            await Api.post(`${API}/`, payload);
            Auth.showAlert('alert-container', 'Record created successfully.', 'success');
        }
        editModal.hide();
        await loadRows();
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('d-none');
    }
}

async function deleteRow(custId, name) {
    if (!confirm(`Delete CUST_SMS #${custId}${name ? ' (' + name + ')' : ''}?\n\nThis cannot be undone.`)) return;
    try {
        await Api.delete(`${API}/${custId}`);
        Auth.showAlert('alert-container', 'Record deleted.', 'success');
        await loadRows();
    } catch (err) {
        Auth.showAlert('alert-container', err.message, 'danger');
    }
}

function fmtDate(value) {
    if (!value) return '—';
    try {
        return new Date(value).toLocaleString();
    } catch {
        return String(value);
    }
}

function esc(text) {
    return String(text ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
