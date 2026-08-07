const DELIVERY_API = '/api/v1/delivery';
const DELIVERY_PAGE_SIZE = 50;
const DELIVERY_STATUSES = [
    'Pending', 'On The Way', 'Arrived', 'Delivered',
    'Failed Delivery', 'Cancelled', 'Returned',
];

let deliverySkip = 0;
let deliveryTotal = 0;
let deliveryRiders = [];
let assignModal;
let statusModal;
let riderModal;
let refreshTimer;
let requestInFlight = false;
let capturedPosition = null;

document.addEventListener('DOMContentLoaded', async () => {
    const profile = await Auth.requireAuth();
    if (!profile) return;

    if (!Auth.hasPermission('delivery.orders.view')) {
        Auth.showAlert('delivery-alert', 'You do not have permission to view deliveries.', 'warning');
        return;
    }

    assignModal = new bootstrap.Modal(document.getElementById('assignModal'));
    statusModal = new bootstrap.Modal(document.getElementById('statusModal'));
    riderModal = new bootstrap.Modal(document.getElementById('riderModal'));

    document.getElementById('btn-sync').addEventListener('click', syncInvoices);
    document.getElementById('btn-new-rider').addEventListener('click', createRider);
    document.getElementById('btn-filter').addEventListener('click', applyFilters);
    document.getElementById('filter-search').addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            applyFilters();
        }
    });
    document.getElementById('filter-status').addEventListener('change', applyFilters);
    document.getElementById('filter-rider').addEventListener('change', applyFilters);
    document.getElementById('delivery-prev').addEventListener('click', () => changePage(-1));
    document.getElementById('delivery-next').addEventListener('click', () => changePage(1));
    document.getElementById('assign-form').addEventListener('submit', submitAssignment);
    document.getElementById('status-form').addEventListener('submit', (event) => event.preventDefault());
    document.getElementById('btn-save-status').addEventListener('click', submitStatus);
    document.getElementById('rider-form').addEventListener('submit', saveRider);
    document.getElementById('btn-capture-gps').addEventListener('click', captureGps);
    document.getElementById('btn-bulk-assign').addEventListener('click', bulkAssignOrders);
    document.getElementById('btn-bulk-deliver-rider').addEventListener('click', bulkDeliverRider);
    document.getElementById('btn-bulk-deliver-all').addEventListener('click', bulkDeliverAll);

    applyPermissionVisibility();
    await loadRiders();
    await refreshDeliveryData();
    refreshTimer = window.setInterval(refreshDeliveryData, 5000);
});

window.addEventListener('beforeunload', () => {
    if (refreshTimer) window.clearInterval(refreshTimer);
});

function applyPermissionVisibility() {
    const canAssign = Auth.hasPermission('delivery.orders.assign');
    const canUpdate = Auth.hasPermission('delivery.orders.update');
    if (!Auth.hasPermission('delivery.orders.sync')) {
        document.getElementById('btn-sync').classList.add('d-none');
    }
    if (!Auth.hasPermission('delivery.riders.manage')) {
        document.getElementById('btn-new-rider').classList.add('d-none');
    }
    if (canAssign || canUpdate) {
        document.getElementById('bulk-actions').classList.remove('d-none');
    }
    if (!canAssign) {
        document.getElementById('bulk-assign-container').classList.add('d-none');
    }
    if (!canUpdate) {
        document.getElementById('bulk-rider-deliver-container').classList.add('d-none');
        document.getElementById('bulk-all-deliver-container').classList.add('d-none');
    }
}

async function refreshDeliveryData() {
    if (requestInFlight || document.hidden) return;
    requestInFlight = true;
    try {
        await Promise.all([loadSummary(), loadOrders()]);
    } finally {
        requestInFlight = false;
    }
}

async function loadSummary() {
    try {
        const summary = await Api.get(`${DELIVERY_API}/summary`);
        const counts = summary.status_counts || {};
        setText('sum-pending', counts.Pending);
        setText('sum-assigned', counts.Assigned);
        setText('sum-route', (counts['On The Way'] || 0) + (counts.Arrived || 0));
        setText('sum-delivered', summary.delivered_today);
        setText('sum-failed', counts['Failed Delivery']);
    } catch (error) {
        console.error('Delivery summary refresh failed:', error);
    }
}

async function loadOrders() {
    const tbody = document.getElementById('delivery-body');
    const params = new URLSearchParams({
        skip: String(deliverySkip),
        limit: String(DELIVERY_PAGE_SIZE),
    });
    const search = document.getElementById('filter-search').value.trim();
    const status = document.getElementById('filter-status').value;
    const riderId = document.getElementById('filter-rider').value;
    if (search) params.set('search', search);
    if (status) params.set('status', status);
    if (riderId) params.set('rider_id', riderId);

    try {
        const data = await Api.get(`${DELIVERY_API}/orders?${params}`);
        deliveryTotal = data.total;
        updatePagination(data.items.length);
        if (!data.items.length) {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted py-5">No delivery orders match the filters.</td></tr>';
            return;
        }

        const canAssign = Auth.hasPermission('delivery.orders.assign');
        const canUpdate = Auth.hasPermission('delivery.orders.update');
        tbody.innerHTML = data.items.map((order) => `
            <tr>
                <td class="fw-semibold">${esc(order.invoice_id)}</td>
                <td class="text-nowrap">${formatDate(order.invoice_date)}</td>
                <td class="delivery-customer">${esc(order.customer_title || 'Walk-in Customer')}</td>
                <td class="text-nowrap">
                    <a href="tel:${escAttr(order.customer_mobile_no || '')}">${esc(order.customer_mobile_no || '—')}</a>
                    ${order.customer_alternate_mobile ? `
                        <div class="small text-muted">
                            Alt: <a href="tel:${escAttr(order.customer_alternate_mobile)}">${esc(order.customer_alternate_mobile)}</a>
                        </div>` : ''}
                </td>
                <td class="delivery-address text-truncate" title="${escAttr(order.address || '')}">
                    ${esc(order.address || '—')}
                </td>
                <td class="text-end text-nowrap">${formatMoney(order.total_amount)}</td>
                <td>${esc(order.rider_name || 'Unassigned')}</td>
                <td><span class="badge status-badge ${statusClass(order.status)}">${esc(order.status)}</span></td>
                <td class="text-nowrap small">${formatDate(order.updated_at)}</td>
                <td class="text-end delivery-actions text-nowrap">
                    ${canAssign && !isTerminal(order.status) ? `
                        <button class="btn btn-sm btn-outline-primary" data-assign="${order.id}" title="Assign rider">
                            <i class="bi bi-person-check"></i>
                        </button>` : ''}
                    ${canUpdate ? `
                        <button class="btn btn-sm btn-outline-success" data-status="${order.id}" data-current="${escAttr(order.status)}" title="Update status">
                            <i class="bi bi-check2-circle"></i>
                        </button>` : ''}
                    ${mapLinks(
                        order.customer_latitude ?? order.delivered_latitude,
                        order.customer_longitude ?? order.delivered_longitude,
                        'Customer location',
                        'bi-house-geo',
                    )}
                    ${mapLinks(
                        order.rider_latitude,
                        order.rider_longitude,
                        'Rider last location',
                        'bi-person-walking',
                    )}
                </td>
            </tr>
        `).join('');

        tbody.querySelectorAll('[data-assign]').forEach((button) => {
            button.addEventListener('click', () => openAssign(Number(button.dataset.assign)));
        });
        tbody.querySelectorAll('[data-status]').forEach((button) => {
            button.addEventListener('click', () => openStatus(
                Number(button.dataset.status),
                button.dataset.current || 'Pending',
            ));
        });
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="10" class="text-center text-danger py-5">${esc(error.message)}</td></tr>`;
    }
}

async function loadRiders() {
    try {
        const data = await Api.get(`${DELIVERY_API}/riders`);
        deliveryRiders = Array.isArray(data) ? data : (data.items || []);
        const filter = document.getElementById('filter-rider');
        const assign = document.getElementById('assign-rider-id');
        const bulk = document.getElementById('bulk-rider-id');
        const options = deliveryRiders
            .filter((rider) => rider.is_active !== false)
            .map((rider) => `<option value="${rider.id}">${esc(rider.name)}${rider.phone ? ` — ${esc(rider.phone)}` : ''}</option>`)
            .join('');
        filter.innerHTML = `<option value="">All riders</option>${options}`;
        assign.innerHTML = options || '<option value="">Create an active rider first</option>';
        bulk.innerHTML = options || '<option value="">Create an active rider first</option>';
        renderRiders();
    } catch (error) {
        Auth.showAlert('delivery-alert', error.message, 'danger');
    }
}

async function syncInvoices() {
    const button = document.getElementById('btn-sync');
    button.disabled = true;
    try {
        const result = await Api.post(`${DELIVERY_API}/sync?lookback_hours=24&limit=500`, {});
        Auth.showAlert(
            'delivery-alert',
            `${result.created ?? 0} new order(s) created and ${result.refreshed ?? 0} existing order(s) refreshed.`,
            'success',
        );
        deliverySkip = 0;
        await refreshDeliveryData();
    } catch (error) {
        Auth.showAlert('delivery-alert', error.message, 'danger');
    } finally {
        button.disabled = false;
    }
}

function createRider() {
    document.getElementById('rider-form').reset();
    document.getElementById('rider-edit-id').value = '';
    document.getElementById('btn-save-rider').textContent = 'Add Rider';
    document.getElementById('rider-error').classList.add('d-none');
    renderRiders();
    riderModal.show();
}

async function saveRider(event) {
    event.preventDefault();
    const riderId = Number(document.getElementById('rider-edit-id').value || 0);
    const name = document.getElementById('rider-name').value.trim();
    const phone = document.getElementById('rider-phone').value.trim();
    const existing = deliveryRiders.find((rider) => rider.id === riderId);
    const error = document.getElementById('rider-error');
    error.classList.add('d-none');
    try {
        const payload = {
            name,
            phone: phone || null,
            is_active: existing ? existing.is_active : true,
        };
        if (riderId) {
            await Api.put(`${DELIVERY_API}/riders/${riderId}`, payload);
        } else {
            await Api.post(`${DELIVERY_API}/riders`, payload);
        }
        await loadRiders();
        document.getElementById('rider-form').reset();
        document.getElementById('rider-edit-id').value = '';
        document.getElementById('btn-save-rider').textContent = 'Add Rider';
    } catch (error) {
        const target = document.getElementById('rider-error');
        target.textContent = error.message;
        target.classList.remove('d-none');
    }
}

function renderRiders() {
    const tbody = document.getElementById('rider-body');
    if (!tbody) return;
    tbody.innerHTML = deliveryRiders.length
        ? deliveryRiders.map((rider) => `
            <tr>
                <td>${esc(rider.name)}</td>
                <td>${esc(rider.phone || '—')}</td>
                <td><span class="badge ${rider.is_active ? 'text-bg-success' : 'text-bg-secondary'}">${rider.is_active ? 'Active' : 'Inactive'}</span></td>
                <td>
                    ${mapLinks(rider.latitude, rider.longitude, 'Rider last location', 'bi-person-walking') || '—'}
                    ${rider.location_updated_at ? `<div class="small text-muted">${formatDate(rider.location_updated_at)}</div>` : ''}
                </td>
                <td class="text-end text-nowrap">
                    <button class="btn btn-sm btn-outline-primary" data-rider-edit="${rider.id}" title="Edit rider">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm ${rider.is_active ? 'btn-outline-danger' : 'btn-outline-success'}"
                            data-rider-toggle="${rider.id}" title="${rider.is_active ? 'Deactivate' : 'Activate'} rider">
                        <i class="bi ${rider.is_active ? 'bi-person-x' : 'bi-person-check'}"></i>
                    </button>
                </td>
            </tr>
        `).join('')
        : '<tr><td colspan="5" class="text-center text-muted py-3">No riders created.</td></tr>';

    tbody.querySelectorAll('[data-rider-edit]').forEach((button) => {
        button.addEventListener('click', () => editRider(Number(button.dataset.riderEdit)));
    });
    tbody.querySelectorAll('[data-rider-toggle]').forEach((button) => {
        button.addEventListener('click', () => toggleRider(Number(button.dataset.riderToggle)));
    });
}

function editRider(riderId) {
    const rider = deliveryRiders.find((item) => item.id === riderId);
    if (!rider) return;
    document.getElementById('rider-edit-id').value = rider.id;
    document.getElementById('rider-name').value = rider.name || '';
    document.getElementById('rider-phone').value = rider.phone || '';
    document.getElementById('btn-save-rider').textContent = 'Update Rider';
}

async function toggleRider(riderId) {
    const rider = deliveryRiders.find((item) => item.id === riderId);
    if (!rider) return;
    try {
        if (rider.is_active) {
            await Api.delete(`${DELIVERY_API}/riders/${riderId}`);
        } else {
            await Api.put(`${DELIVERY_API}/riders/${riderId}`, {
                name: rider.name,
                phone: rider.phone || null,
                is_active: true,
            });
        }
        await loadRiders();
    } catch (error) {
        const target = document.getElementById('rider-error');
        target.textContent = error.message;
        target.classList.remove('d-none');
    }
}

function openAssign(orderId) {
    if (!deliveryRiders.length) {
        Auth.showAlert('delivery-alert', 'Create an active rider before assigning an order.', 'warning');
        return;
    }
    document.getElementById('assign-order-id').value = orderId;
    assignModal.show();
}

async function submitAssignment(event) {
    event.preventDefault();
    const orderId = Number(document.getElementById('assign-order-id').value);
    const riderId = Number(document.getElementById('assign-rider-id').value);
    if (!orderId || !riderId) return;
    try {
        await Api.put(`${DELIVERY_API}/orders/${orderId}/assign`, { rider_id: riderId });
        assignModal.hide();
        Auth.showAlert('delivery-alert', 'Rider assigned.', 'success');
        await refreshDeliveryData();
    } catch (error) {
        Auth.showAlert('delivery-alert', error.message, 'danger');
    }
}

async function bulkAssignOrders() {
    const riderId = Number(document.getElementById('bulk-rider-id').value);
    const rider = deliveryRiders.find((item) => item.id === riderId);
    if (!rider) {
        Auth.showAlert('delivery-alert', 'Select an active rider first.', 'warning');
        return;
    }
    if (!window.confirm(
        `Assign ${rider.name} to every Pending, Assigned, and Failed Delivery order?`,
    )) return;
    await runBulkAction(
        'btn-bulk-assign',
        `${DELIVERY_API}/orders/bulk-assign`,
        { rider_id: riderId },
    );
}

async function bulkDeliverRider() {
    const riderId = Number(document.getElementById('bulk-rider-id').value);
    const rider = deliveryRiders.find((item) => item.id === riderId);
    if (!rider) {
        Auth.showAlert('delivery-alert', 'Select a rider first.', 'warning');
        return;
    }
    if (!window.confirm(
        `Mark every order currently Assigned to ${rider.name} as Delivered without GPS?`,
    )) return;
    await runBulkAction(
        'btn-bulk-deliver-rider',
        `${DELIVERY_API}/orders/bulk-deliver`,
        { rider_id: riderId },
    );
}

async function bulkDeliverAll() {
    if (!window.confirm(
        'Mark EVERY Assigned delivery order as Delivered without GPS? This cannot be undone from this button.',
    )) return;
    await runBulkAction(
        'btn-bulk-deliver-all',
        `${DELIVERY_API}/orders/bulk-deliver`,
        { rider_id: null },
    );
}

async function runBulkAction(buttonId, url, payload) {
    const button = document.getElementById(buttonId);
    const originalHtml = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Working…';
    try {
        const result = await Api.post(url, payload);
        Auth.showAlert('delivery-alert', result.message, 'success');
        deliverySkip = 0;
        await refreshDeliveryData();
    } catch (error) {
        Auth.showAlert('delivery-alert', error.message, 'danger');
    } finally {
        button.disabled = false;
        button.innerHTML = originalHtml;
    }
}

function openStatus(orderId, currentStatus) {
    capturedPosition = null;
    document.getElementById('status-order-id').value = orderId;
    document.getElementById('status-remarks').value = '';
    document.getElementById('gps-result').classList.add('d-none');
    document.getElementById('btn-capture-gps').disabled = false;
    document.getElementById('btn-capture-gps').innerHTML =
        '<i class="bi bi-crosshair me-1"></i> Capture Current GPS';
    document.getElementById('status-current').textContent = currentStatus;
    const error = document.getElementById('status-error');
    error.textContent = '';
    error.classList.add('d-none');

    const statuses = DELIVERY_STATUSES.filter((status) => status !== currentStatus);
    document.getElementById('status-value').innerHTML = statuses
        .map((status) => `<option value="${escAttr(status)}">${esc(status)}</option>`)
        .join('');
    document.getElementById('btn-save-status').disabled = statuses.length === 0;
    statusModal.show();
}

async function submitStatus(event) {
    event?.preventDefault();
    const button = document.getElementById('btn-save-status');
    const originalButtonText = button.textContent;
    const orderId = Number(document.getElementById('status-order-id').value);
    const status = document.getElementById('status-value').value;
    const remarks = document.getElementById('status-remarks').value.trim();
    const payload = { status, remarks: remarks || null };

    const error = document.getElementById('status-error');
    error.textContent = '';
    error.classList.add('d-none');
    if (!orderId || !status) {
        showStatusError('Choose a valid next status and try again.');
        return;
    }
    if (status === 'Delivered' && !capturedPosition) {
        showStatusProgress('Save tapped. Getting the required GPS location…');
        const captured = await captureGps();
        if (!captured) return;
    }
    if (capturedPosition) {
        payload.latitude = capturedPosition.coords.latitude;
        payload.longitude = capturedPosition.coords.longitude;
        payload.accuracy = capturedPosition.coords.accuracy;
    }

    button.disabled = true;
    button.textContent = 'Saving…';
    try {
        showStatusProgress(`Saving ${status}…`);
        await Api.put(`${DELIVERY_API}/orders/${orderId}/status`, payload);
        statusModal.hide();
        Auth.showAlert('delivery-alert', `Delivery status changed to ${status}.`, 'success');
        await refreshDeliveryData();
    } catch (error) {
        showStatusError(error.message || 'Could not update delivery status.');
    } finally {
        button.disabled = false;
        button.textContent = originalButtonText;
    }
}

async function captureGps() {
    const button = document.getElementById('btn-capture-gps');
    const gps = document.getElementById('gps-result');
    const error = document.getElementById('status-error');
    error.classList.add('d-none');
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Waiting for GPS…';
    gps.textContent = 'Keep this page open while the phone obtains a location fix.';
    gps.className = 'small mt-2 text-primary';
    try {
        capturedPosition = await getCurrentPosition();
        const { latitude, longitude, accuracy } = capturedPosition.coords;
        gps.textContent = `GPS ready: ${latitude.toFixed(6)}, ${longitude.toFixed(6)} (±${Math.round(accuracy)} m)`;
        gps.className = 'small mt-2 text-success';
        button.innerHTML = '<i class="bi bi-check-circle me-1"></i> GPS Captured';
        return true;
    } catch (locationError) {
        capturedPosition = null;
        gps.classList.add('d-none');
        showStatusError(locationError.message);
        button.innerHTML = '<i class="bi bi-arrow-repeat me-1"></i> Retry GPS';
        return false;
    } finally {
        button.disabled = false;
    }
}

function showStatusProgress(message) {
    const error = document.getElementById('status-error');
    error.textContent = message;
    error.className = 'alert alert-info';
}

function showStatusError(message) {
    const error = document.getElementById('status-error');
    error.textContent = message;
    error.className = 'alert alert-danger';
    error.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function getCurrentPosition() {
    return new Promise((resolve, reject) => {
        if (!window.isSecureContext) {
            reject(new Error('GPS requires HTTPS. Open the public ERP website in Safari or Chrome.'));
            return;
        }
        if (!navigator.geolocation) {
            reject(new Error('This browser does not support GPS location.'));
            return;
        }
        const fail = (error) => {
            const inAppBrowser = /GSA|FBAN|FBAV|Instagram/i.test(navigator.userAgent);
            const messages = {
                1: inAppBrowser
                    ? 'This in-app browser denied GPS. Open the ERP link in Safari or Chrome and allow Location.'
                    : 'Location permission was denied. Enable Location for this browser in phone settings, then retry.',
                2: 'The phone could not determine its location. Turn on GPS and mobile data, then retry.',
                3: 'GPS timed out. Move near a window or outdoors, then retry.',
            };
            reject(new Error(messages[error.code] || `GPS failed: ${error.message}`));
        };
        const fallback = (firstError) => {
            if (firstError.code === 1) {
                fail(firstError);
                return;
            }
            navigator.geolocation.getCurrentPosition(
                resolve,
                fail,
                { enableHighAccuracy: false, timeout: 20000, maximumAge: 300000 },
            );
        };
        navigator.geolocation.getCurrentPosition(
            resolve,
            fallback,
            { enableHighAccuracy: true, timeout: 20000, maximumAge: 10000 },
        );
    });
}

function applyFilters() {
    deliverySkip = 0;
    refreshDeliveryData();
}

function changePage(direction) {
    deliverySkip = Math.max(0, deliverySkip + (direction * DELIVERY_PAGE_SIZE));
    refreshDeliveryData();
}

function updatePagination(itemCount) {
    document.getElementById('delivery-page-info').textContent = deliveryTotal
        ? `Showing ${deliverySkip + 1}–${deliverySkip + itemCount} of ${deliveryTotal}`
        : 'No delivery orders';
    document.getElementById('delivery-prev').disabled = deliverySkip === 0;
    document.getElementById('delivery-next').disabled =
        deliverySkip + DELIVERY_PAGE_SIZE >= deliveryTotal;
}

function isTerminal(status) {
    return ['Delivered', 'Cancelled', 'Returned'].includes(status);
}

function statusClass(status) {
    const classes = {
        Pending: 'text-bg-secondary',
        Assigned: 'text-bg-primary',
        'On The Way': 'text-bg-info',
        Arrived: 'text-bg-warning',
        Delivered: 'text-bg-success',
        Cancelled: 'text-bg-dark',
        'Failed Delivery': 'text-bg-danger',
        Returned: 'text-bg-dark',
    };
    return classes[status] || 'text-bg-secondary';
}

function mapLinks(latitude, longitude, label, iconClass) {
    if (latitude == null || longitude == null) return '';
    const lat = encodeURIComponent(latitude);
    const lon = encodeURIComponent(longitude);
    const safeLabel = escAttr(label);
    return `
        <a class="btn btn-sm btn-outline-danger" target="_blank" rel="noopener"
           href="https://www.google.com/maps/search/?api=1&query=${lat}%2C${lon}"
           title="${safeLabel} in Google Maps">
            <i class="bi bi-google"></i>
        </a>
        <a class="btn btn-sm btn-outline-secondary" target="_blank" rel="noopener"
           href="https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=18/${lat}/${lon}"
           title="${safeLabel} in OpenStreetMap">
            <i class="bi ${escAttr(iconClass)}"></i>
        </a>`;
}

function setText(id, value) {
    document.getElementById(id).textContent = Number(value || 0).toLocaleString();
}

function formatDate(value) {
    if (!value) return '—';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? esc(String(value)) : date.toLocaleString();
}

function formatMoney(value) {
    const number = Number(value || 0);
    return new Intl.NumberFormat('en-PK', {
        style: 'currency',
        currency: 'PKR',
        maximumFractionDigits: 0,
    }).format(number);
}

function esc(value) {
    const element = document.createElement('div');
    element.textContent = value == null ? '' : String(value);
    return element.innerHTML;
}

function escAttr(value) {
    return esc(value).replace(/"/g, '&quot;');
}
