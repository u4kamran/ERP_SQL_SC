/** Customer App Carts — staff review of MOBILE_APP saved baskets (not invoices). */
const API = '/api/v1/marketing/customer-app-carts';
let detailModal;
let page = 1;
const pageSize = 25;
let currentCart = null;

document.addEventListener('DOMContentLoaded', async () => {
    await Auth.requireAuth();
    if (!Auth.hasPermission('marketing.customer_app_carts.view') && !Auth.hasPermission('auth.admin.full')) {
        Auth.showAlert('alert-container', 'You do not have permission to view Customer App Carts.', 'warning');
        return;
    }
    detailModal = new bootstrap.Modal(document.getElementById('detailModal'));
    document.getElementById('btn-filter').addEventListener('click', () => { page = 1; loadRows(); });
    document.getElementById('filter-search').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); page = 1; loadRows(); }
    });
    document.getElementById('prev-page').addEventListener('click', () => {
        page = Math.max(1, page - 1);
        loadRows();
    });
    document.getElementById('next-page').addEventListener('click', () => {
        page += 1;
        loadRows();
    });
    await loadRows();
});

function money(n) {
    const v = Number(n || 0);
    return 'Rs. ' + v.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

function esc(s) {
    return String(s ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function statusBadge(status) {
    const map = {
        SAVED: 'secondary',
        UNDER_REVIEW: 'info',
        CONTACTED: 'primary',
        CONFIRMED: 'success',
        CONVERTED: 'dark',
        CANCELLED: 'danger',
        EXPIRED: 'warning',
    };
    const cls = map[status] || 'secondary';
    return `<span class="badge text-bg-${cls}">${esc(status)}</span>`;
}

async function loadRows() {
    const tbody = document.getElementById('table-body');
    try {
        const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
        const search = document.getElementById('filter-search').value.trim();
        const status = document.getElementById('filter-status').value;
        const source = document.getElementById('filter-source').value;
        const dateFrom = document.getElementById('filter-from').value;
        const dateTo = document.getElementById('filter-to').value;
        if (search) params.set('search', search);
        if (status) params.set('status', status);
        if (source) params.set('source', source);
        if (dateFrom) params.set('date_from', dateFrom);
        if (dateTo) params.set('date_to', dateTo);

        const data = await Api.get(`${API}?${params}`);
        const total = data.total || 0;
        const start = total ? (page - 1) * pageSize + 1 : 0;
        const end = Math.min(page * pageSize, total);
        document.getElementById('pagination-info').textContent =
            total ? `Showing ${start}–${end} of ${total}` : 'No carts';
        document.getElementById('prev-page').disabled = page <= 1;
        document.getElementById('next-page').disabled = !data.has_more;

        if (!data.items.length) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-muted">No customer app carts found.</td></tr>';
            return;
        }

        tbody.innerHTML = data.items.map((r) => {
            const dt = r.created_at ? new Date(r.created_at).toLocaleString() : '—';
            return `
            <tr>
                <td><code>${esc(r.cart_ref)}</code></td>
                <td>${esc(r.customer_name)}</td>
                <td>${esc(r.customer_mobile_no)}</td>
                <td>${esc(dt)}</td>
                <td class="text-end">${r.total_items}</td>
                <td class="text-end">${money(r.estimated_total)}</td>
                <td>${statusBadge(r.status)}</td>
                <td><span class="badge text-bg-light border">${esc(r.source)}</span></td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary" data-id="${r.id}">Open</button>
                </td>
            </tr>`;
        }).join('');

        tbody.querySelectorAll('button[data-id]').forEach((btn) => {
            btn.addEventListener('click', () => openDetail(Number(btn.dataset.id)));
        });
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger py-4">${esc(err.message || err)}</td></tr>`;
    }
}

async function openDetail(cartId) {
    const body = document.getElementById('detail-body');
    const actions = document.getElementById('detail-actions');
    body.innerHTML = '<p class="text-muted">Loading…</p>';
    actions.innerHTML = '';
    detailModal.show();
    try {
        currentCart = await Api.get(`${API}/${cartId}`);
        document.getElementById('detail-title').textContent = currentCart.cart_ref;
        const lines = (currentCart.lines || []).map((ln) => `
            <tr>
                <td>${esc(ln.item_title)}</td>
                <td>${esc(ln.barcode || '—')}</td>
                <td class="text-end">${ln.qty}</td>
                <td>${esc(ln.uom_title || '—')}</td>
                <td class="text-end">${money(ln.unit_price)}</td>
                <td class="text-end">${money(ln.discount_amount)}</td>
                <td class="text-end">${money(ln.line_total)}</td>
            </tr>`).join('');
        const hist = (currentCart.history || []).map((h) => `
            <li class="small text-muted">
                ${esc(h.created_at || '')} — ${esc(h.action_code)}:
                ${esc(h.old_status || '—')} → <strong>${esc(h.new_status)}</strong>
                by ${esc(h.actor_username)}
                ${h.remarks ? `(${esc(h.remarks)})` : ''}
            </li>`).join('');

        body.innerHTML = `
            <div class="row g-3 mb-3">
                <div class="col-md-6">
                    <h6>Customer</h6>
                    <div><strong>${esc(currentCart.customer_name)}</strong></div>
                    <div>Mobile: ${esc(currentCart.customer_mobile_no)}</div>
                    <div>CUST_SMS ID: ${currentCart.cust_sms_id}</div>
                    <div>Address: ${esc(currentCart.customer_address || '—')}</div>
                </div>
                <div class="col-md-6">
                    <h6>Cart</h6>
                    <div>Ref: <code>${esc(currentCart.cart_ref)}</code></div>
                    <div>Status: ${statusBadge(currentCart.status)}</div>
                    <div>Source: ${esc(currentCart.source)}</div>
                    <div>Created: ${esc(currentCart.created_at || '—')}</div>
                    <div>Updated: ${esc(currentCart.updated_at || '—')}</div>
                </div>
            </div>
            <h6>Items</h6>
            <div class="table-responsive mb-3">
                <table class="table table-sm">
                    <thead><tr>
                        <th>Item</th><th>Barcode</th><th class="text-end">Qty</th>
                        <th>Unit</th><th class="text-end">Price</th>
                        <th class="text-end">Discount</th><th class="text-end">Line Total</th>
                    </tr></thead>
                    <tbody>${lines || '<tr><td colspan="7" class="text-muted">No lines</td></tr>'}</tbody>
                </table>
            </div>
            <div class="d-flex justify-content-end gap-4 mb-3">
                <div>Subtotal: <strong>${money(currentCart.estimated_subtotal)}</strong></div>
                <div>Tax (est.): <strong>${money(currentCart.estimated_tax)}</strong></div>
                <div>Estimated Total: <strong>${money(currentCart.estimated_total)}</strong></div>
            </div>
            <h6>History</h6>
            <ul class="mb-0">${hist || '<li class="text-muted small">No history</li>'}</ul>
        `;

        const canUpdate = Auth.hasPermission('marketing.customer_app_carts.update') || Auth.hasPermission('auth.admin.full');
        const canCancel = Auth.hasPermission('marketing.customer_app_carts.cancel') || Auth.hasPermission('auth.admin.full');
        const canConvert = Auth.hasPermission('marketing.customer_app_carts.convert') || Auth.hasPermission('auth.admin.full');
        const st = currentCart.status;

        if (canUpdate && st === 'SAVED') {
            actions.appendChild(actionBtn('Mark Under Review', 'UNDER_REVIEW', 'btn-info'));
            actions.appendChild(actionBtn('Mark Contacted', 'CONTACTED', 'btn-primary'));
            actions.appendChild(actionBtn('Confirm', 'CONFIRMED', 'btn-success'));
        }
        if (canUpdate && st === 'UNDER_REVIEW') {
            actions.appendChild(actionBtn('Mark Contacted', 'CONTACTED', 'btn-primary'));
            actions.appendChild(actionBtn('Confirm', 'CONFIRMED', 'btn-success'));
        }
        if (canUpdate && st === 'CONTACTED') {
            actions.appendChild(actionBtn('Confirm', 'CONFIRMED', 'btn-success'));
        }
        if (canCancel && !['CANCELLED', 'CONVERTED', 'EXPIRED'].includes(st)) {
            actions.appendChild(actionBtn('Cancel', 'CANCELLED', 'btn-outline-danger'));
        }
        if (canConvert && st === 'CONFIRMED') {
            const btn = document.createElement('button');
            btn.className = 'btn btn-dark';
            btn.textContent = 'Convert to Order (Phase 2)';
            btn.addEventListener('click', () => convertCart(currentCart.id));
            actions.appendChild(btn);
        }
    } catch (err) {
        body.innerHTML = `<div class="alert alert-danger">${esc(err.message || err)}</div>`;
    }
}

function actionBtn(label, status, cls) {
    const btn = document.createElement('button');
    btn.className = `btn ${cls}`;
    btn.textContent = label;
    btn.addEventListener('click', () => updateStatus(status));
    return btn;
}

async function updateStatus(newStatus) {
    if (!currentCart) return;
    try {
        await Api.put(`${API}/${currentCart.id}/status`, { status: newStatus });
        Auth.showAlert('alert-container', `Status updated to ${newStatus}.`, 'success');
        await openDetail(currentCart.id);
        await loadRows();
    } catch (err) {
        Auth.showAlert('alert-container', err.message || String(err), 'danger');
    }
}

async function convertCart(cartId) {
    try {
        await Api.post(`${API}/${cartId}/convert`, {});
    } catch (err) {
        Auth.showAlert(
            'alert-container',
            err.message || 'Convert is not available yet (Phase 2). Cart is not an invoice.',
            'warning',
        );
    }
}
