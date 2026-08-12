const WA_BOT_API = '/api/v1/marketing/whatsapp-bot';

let selectedConversationId = null;
let refreshTimer = null;

document.addEventListener('DOMContentLoaded', async () => {
    const profile = await Auth.requireAuth();
    if (!profile) return;
    if (!Auth.hasPermission('marketing.whatsapp_bot.view')) {
        Auth.showAlert('wa-bot-alert', 'You do not have permission to view the chatbot.', 'warning');
        return;
    }

    document.getElementById('btn-refresh').addEventListener('click', refreshAll);
    document.getElementById('staff-reply-form').addEventListener('submit', sendStaffReply);
    document.getElementById('bot-config-form').addEventListener('submit', saveConfig);
    document.getElementById('btn-status-bot').addEventListener('click', () => setStatus('bot'));
    document.getElementById('btn-status-human').addEventListener('click', () => setStatus('human'));
    document.getElementById('btn-status-closed').addEventListener('click', () => setStatus('closed'));
    document.getElementById('order-status-filter').addEventListener('change', loadOrders);
    document.getElementById('btn-print-receipt').addEventListener('click', printOrderReceipt);

    if (!Auth.hasPermission('marketing.whatsapp_bot.manage')) {
        document.getElementById('bot-config-form').querySelectorAll('input, textarea, button').forEach((el) => {
            el.disabled = true;
        });
        document.getElementById('btn-staff-reply').disabled = true;
        document.getElementById('staff-reply').disabled = true;
    }

    await refreshAll();
    refreshTimer = window.setInterval(refreshAll, 8000);
});

window.addEventListener('beforeunload', () => {
    if (refreshTimer) window.clearInterval(refreshTimer);
});

async function refreshAll() {
    await Promise.all([loadStatus(), loadConversations(), loadConfig(), loadOrders()]);
    if (selectedConversationId) {
        await loadConversation(selectedConversationId, false);
    }
}

async function loadStatus() {
    try {
        const status = await Api.get(`${WA_BOT_API}/status`);
        document.getElementById('st-mode').textContent = status.online_mode ? 'Online' : 'Offline';
        document.getElementById('st-wa').textContent = status.whatsapp_configured ? 'Ready' : 'Not set';
        document.getElementById('st-chats').textContent = status.conversation_count;
        document.getElementById('st-unread').textContent = status.unread_total;
        document.getElementById('st-orders').textContent = status.pending_orders ?? 0;
        const hint = document.getElementById('config-hint');
        hint.textContent = status.configuration_hint;
        hint.className = status.whatsapp_configured && status.online_mode
            ? 'alert alert-success py-2 small'
            : 'alert alert-warning py-2 small';
        document.getElementById('webhook-url').textContent = status.webhook_url;
    } catch (error) {
        Auth.showAlert('wa-bot-alert', error.message, 'danger');
    }
}

async function loadConfig() {
    if (!Auth.hasPermission('marketing.whatsapp_bot.manage')) return;
    try {
        const config = await Api.get(`${WA_BOT_API}/config`);
        document.getElementById('cfg-online').checked = !!config.online_mode;
        document.getElementById('cfg-auto').checked = !!config.auto_reply;
        document.getElementById('cfg-phone').value = config.store_phone || '';
        document.getElementById('cfg-address').value = config.store_address || '';
        document.getElementById('cfg-hours').value = config.store_hours || '';
        document.getElementById('cfg-welcome').value = config.welcome_message || '';
        document.getElementById('cfg-handoff').value = config.human_handoff_message || '';
    } catch (error) {
        console.error(error);
    }
}

async function saveConfig(event) {
    event.preventDefault();
    try {
        await Api.put(`${WA_BOT_API}/config`, {
            online_mode: document.getElementById('cfg-online').checked,
            auto_reply: document.getElementById('cfg-auto').checked,
            store_phone: document.getElementById('cfg-phone').value.trim(),
            store_address: document.getElementById('cfg-address').value.trim(),
            store_hours: document.getElementById('cfg-hours').value.trim(),
            welcome_message: document.getElementById('cfg-welcome').value.trim(),
            human_handoff_message: document.getElementById('cfg-handoff').value.trim(),
        });
        Auth.showAlert('wa-bot-alert', 'Bot settings saved.', 'success');
        await loadStatus();
    } catch (error) {
        Auth.showAlert('wa-bot-alert', error.message, 'danger');
    }
}

async function loadConversations() {
    const list = document.getElementById('conversation-list');
    try {
        const items = await Api.get(`${WA_BOT_API}/conversations`);
        if (!items.length) {
            list.innerHTML = '<div class="list-group-item text-muted">No conversations yet.</div>';
            return;
        }
        list.innerHTML = items.map((item) => `
            <button type="button"
                    class="list-group-item list-group-item-action ${item.conversation_id === selectedConversationId ? 'active' : ''}"
                    data-id="${escAttr(item.conversation_id)}">
                <div class="d-flex justify-content-between">
                    <strong>${esc(item.display_name || item.phone || 'Guest')}</strong>
                    <span class="badge text-bg-${item.channel === 'whatsapp' ? 'success' : 'secondary'}">${esc(item.channel)}</span>
                </div>
                <div class="small ${item.conversation_id === selectedConversationId ? '' : 'text-muted'} text-truncate">
                    ${esc(item.last_message || '—')}
                </div>
                <div class="small d-flex justify-content-between mt-1">
                    <span>${esc(item.status)}</span>
                    ${item.unread ? `<span class="badge text-bg-danger">${item.unread}</span>` : ''}
                </div>
            </button>
        `).join('');
        list.querySelectorAll('[data-id]').forEach((button) => {
            button.addEventListener('click', () => loadConversation(button.dataset.id, true));
        });
    } catch (error) {
        list.innerHTML = `<div class="list-group-item text-danger">${esc(error.message)}</div>`;
    }
}

async function loadConversation(conversationId, focusInput) {
    selectedConversationId = conversationId;
    const box = document.getElementById('chat-messages');
    try {
        const conversation = await Api.get(`${WA_BOT_API}/conversations/${conversationId}`);
        document.getElementById('chat-title').textContent =
            conversation.display_name || conversation.phone || 'Conversation';
        const canManage = Auth.hasPermission('marketing.whatsapp_bot.manage');
        document.getElementById('staff-reply').disabled = !canManage;
        document.getElementById('btn-staff-reply').disabled = !canManage;
        box.innerHTML = (conversation.messages || []).map((message) => `
            <div class="wa-bubble ${message.direction === 'out' ? 'out' : 'in'}">
                ${esc(message.text)}
                <span class="meta">${esc(message.sender || message.direction)} · ${formatDate(message.created_at)}</span>
            </div>
        `).join('') || '<div class="text-muted text-center py-5">No messages.</div>';
        box.scrollTop = box.scrollHeight;
        await loadConversations();
        if (focusInput) document.getElementById('staff-reply').focus();
    } catch (error) {
        box.innerHTML = `<div class="text-danger text-center py-5">${esc(error.message)}</div>`;
    }
}

async function sendStaffReply(event) {
    event.preventDefault();
    if (!selectedConversationId) return;
    const input = document.getElementById('staff-reply');
    const message = input.value.trim();
    if (!message) return;
    try {
        await Api.post(`${WA_BOT_API}/conversations/${selectedConversationId}/reply`, { message });
        input.value = '';
        await loadConversation(selectedConversationId, true);
        await loadStatus();
    } catch (error) {
        Auth.showAlert('wa-bot-alert', error.message, 'danger');
    }
}

async function setStatus(statusValue) {
    if (!selectedConversationId) return;
    try {
        await Api.put(`${WA_BOT_API}/conversations/${selectedConversationId}/status`, {
            status: statusValue,
        });
        await loadConversation(selectedConversationId, false);
        await loadStatus();
    } catch (error) {
        Auth.showAlert('wa-bot-alert', error.message, 'danger');
    }
}

async function loadOrders() {
    const body = document.getElementById('orders-table-body');
    const filter = document.getElementById('order-status-filter').value;
    try {
        const query = filter ? `?status=${encodeURIComponent(filter)}` : '';
        let items = await Api.get(`${WA_BOT_API}/orders${query}`);
        if (!filter) {
            items = items.filter((item) =>
                ['pending', 'confirmed', 'preparing', 'ready'].includes(item.status)
            );
        }
        if (!items.length) {
            body.innerHTML = '<tr><td colspan="6" class="text-muted">No orders yet.</td></tr>';
            return;
        }
        const canManage = Auth.hasPermission('marketing.whatsapp_bot.manage');
        body.innerHTML = items.map((item) => `
            <tr>
                <td>
                    <strong>${esc(item.order_no)}</strong>
                    <div class="small text-muted">${formatDate(item.created_at)}</div>
                </td>
                <td>
                    ${esc(item.customer_name || 'Guest')}
                    <div class="small text-muted">${esc(item.customer_mobile || item.phone || '')}</div>
                </td>
                <td><span class="badge text-bg-${item.channel === 'whatsapp' ? 'success' : 'secondary'}">${esc(item.channel)}</span></td>
                <td class="text-end fw-semibold">Rs ${Number(item.order_total || 0).toLocaleString()}</td>
                <td>
                    ${canManage ? `
                    <select class="form-select form-select-sm order-status-select" data-id="${escAttr(item.order_id)}">
                        ${['pending','confirmed','preparing','ready','completed','cancelled'].map((status) =>
                            `<option value="${status}" ${status === item.status ? 'selected' : ''}>${status}</option>`
                        ).join('')}
                    </select>` : esc(item.status)}
                </td>
                <td class="text-end">
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-primary btn-order-view" data-id="${escAttr(item.order_id)}">Receipt</button>
                        <button type="button" class="btn btn-outline-dark btn-order-print" data-id="${escAttr(item.order_id)}">Print</button>
                    </div>
                </td>
            </tr>
        `).join('');
        body.querySelectorAll('.btn-order-view').forEach((button) => {
            button.addEventListener('click', () => viewOrder(button.dataset.id, false));
        });
        body.querySelectorAll('.btn-order-print').forEach((button) => {
            button.addEventListener('click', () => viewOrder(button.dataset.id, true));
        });
        body.querySelectorAll('.order-status-select').forEach((select) => {
            select.addEventListener('change', () => updateOrderStatus(select.dataset.id, select.value));
        });
    } catch (error) {
        body.innerHTML = `<tr><td colspan="6" class="text-danger">${esc(error.message)}</td></tr>`;
    }
}

let currentOrderReceipt = '';
let currentOrderMapsUrl = '';

async function viewOrder(orderId, autoPrint = false) {
    const receipt = document.getElementById('order-receipt');
    const actions = document.getElementById('order-receipt-actions');
    const mapsBtn = document.getElementById('btn-order-maps');
    const meta = document.getElementById('order-receipt-meta');
    try {
        const order = await Api.get(`${WA_BOT_API}/orders/${orderId}`);
        currentOrderReceipt = order.receipt_text || '';
        currentOrderMapsUrl = order.maps_url || '';
        if (!currentOrderMapsUrl && order.latitude != null && order.longitude != null) {
            currentOrderMapsUrl = `https://www.google.com/maps?q=${order.latitude},${order.longitude}`;
        }
        receipt.textContent = currentOrderReceipt;
        receipt.classList.remove('d-none');
        actions.classList.remove('d-none');
        meta.textContent = [
            order.customer_address ? `Address: ${order.customer_address}` : '',
            order.customer_name ? order.customer_name : '',
        ].filter(Boolean).join(' · ');
        if (currentOrderMapsUrl) {
            mapsBtn.href = currentOrderMapsUrl;
            mapsBtn.classList.remove('d-none');
        } else {
            mapsBtn.classList.add('d-none');
        }
        receipt.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        if (autoPrint) printOrderReceipt();
    } catch (error) {
        Auth.showAlert('wa-bot-alert', error.message, 'danger');
    }
}

function printOrderReceipt() {
    const text = currentOrderReceipt || document.getElementById('order-receipt').textContent || '';
    if (!text.trim()) {
        Auth.showAlert('wa-bot-alert', 'Open a receipt first.', 'warning');
        return;
    }
    const win = window.open('', '_blank', 'width=480,height=720');
    if (!win) {
        Auth.showAlert('wa-bot-alert', 'Allow popups to print the receipt.', 'warning');
        return;
    }
    const mapsLine = currentOrderMapsUrl
        ? `<p style="font:12px Consolas,monospace;margin:8px 0;">Maps: <a href="${escAttr(currentOrderMapsUrl)}">${esc(currentOrderMapsUrl)}</a></p>`
        : '';
    win.document.write(`<!DOCTYPE html><html><head><title>Order Receipt</title>
<style>
body{font-family:Consolas,"Courier New",monospace;padding:16px;color:#111}
pre{white-space:pre-wrap;font:13px Consolas,"Courier New",monospace;margin:0}
@media print{body{padding:0}}
</style></head><body>
<pre>${esc(text)}</pre>
${mapsLine}
<script>window.onload=function(){window.focus();window.print();}</script>
</body></html>`);
    win.document.close();
}

async function updateOrderStatus(orderId, statusValue) {
    try {
        await Api.put(`${WA_BOT_API}/orders/${orderId}/status`, { status: statusValue });
        Auth.showAlert('wa-bot-alert', `Order marked ${statusValue}.`, 'success');
        await Promise.all([loadOrders(), loadStatus()]);
    } catch (error) {
        Auth.showAlert('wa-bot-alert', error.message, 'danger');
    }
}

function formatDate(value) {
    if (!value) return '';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
}

function esc(value) {
    const element = document.createElement('div');
    element.textContent = value == null ? '' : String(value);
    return element.innerHTML;
}

function escAttr(value) {
    return esc(value).replace(/"/g, '&quot;');
}
