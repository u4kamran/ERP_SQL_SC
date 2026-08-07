/**
 * Promotion Hub — find, discover, send.
 */
const API = '/api/v1/marketing/promotion';
const CONTACTS_API = '/api/v1/marketing/customer-contacts';

let lookupType = 'phone';
let composeData = null;

document.addEventListener('DOMContentLoaded', async () => {
    const profile = await Auth.requireAuth();
    if (!profile) return;

    if (!Auth.hasPermission('marketing.promotion.view')
        && !Auth.hasPermission('marketing.customer_contacts.view')
        && !Auth.hasPermission('auth.admin.full')) {
        Auth.showAlert('alert-area', 'You do not have permission to use Promotion Hub.', 'warning');
        return;
    }

    setupTabs();
    document.getElementById('btn-find').addEventListener('click', findCustomer);
    document.getElementById('input-phone').addEventListener('keydown', (e) => { if (e.key === 'Enter') findCustomer(); });
    document.getElementById('input-email').addEventListener('keydown', (e) => { if (e.key === 'Enter') findCustomer(); });
    document.getElementById('template-select').addEventListener('change', onTemplateChange);
    document.getElementById('btn-send-whatsapp').addEventListener('click', () => sendPromotion('whatsapp'));
    document.getElementById('btn-whatsapp-manual').addEventListener('click', () => sendPromotion('whatsapp_manual'));
    document.getElementById('btn-send-email').addEventListener('click', () => sendPromotion('email'));
    document.getElementById('btn-copy-message').addEventListener('click', copyMessage);

    // Pre-fill from URL ?email= or ?phone= or ?sms=
    const params = new URLSearchParams(window.location.search);
    if (params.get('email')) {
        lookupType = 'email';
        switchTab('email');
        document.getElementById('input-email').value = params.get('email');
        findCustomer();
    } else if (params.get('phone')) {
        lookupType = 'phone';
        document.getElementById('input-phone').value = params.get('phone');
        findCustomer();
    } else if (params.get('sms')) {
        lookupType = 'sms_id';
        switchTab('sms_id');
        document.getElementById('input-sms-id').value = params.get('sms');
        findCustomer();
    }
});

function setupTabs() {
    document.querySelectorAll('#lookup-tabs [data-type]').forEach((btn) => {
        btn.addEventListener('click', () => {
            lookupType = btn.dataset.type;
            document.querySelectorAll('#lookup-tabs .nav-link').forEach((el) => el.classList.remove('active'));
            btn.classList.add('active');
            switchTab(lookupType);
        });
    });
}

function switchTab(type) {
    document.getElementById('input-phone-wrap').classList.toggle('d-none', type !== 'phone');
    document.getElementById('input-email-wrap').classList.toggle('d-none', type !== 'email');
    document.getElementById('input-sms-wrap').classList.toggle('d-none', type !== 'sms_id');
}

async function findCustomer() {
    const btn = document.getElementById('btn-find');
    const params = new URLSearchParams();
    if (lookupType === 'phone') {
        const phone = document.getElementById('input-phone').value.trim();
        if (!phone) return Auth.showAlert('alert-area', 'Enter mobile number.', 'warning');
        params.set('phone', phone);
    } else if (lookupType === 'email') {
        const email = document.getElementById('input-email').value.trim();
        if (!email) return Auth.showAlert('alert-area', 'Enter email.', 'warning');
        params.set('email', email);
    } else {
        const smsId = document.getElementById('input-sms-id').value.trim();
        if (!smsId) return Auth.showAlert('alert-area', 'Enter SMS ID.', 'warning');
        params.set('cust_sms_id', smsId);
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

    try {
        const data = await Api.get(`${API}/compose?${params.toString()}`);
        composeData = data;
        renderContact(data);
        renderPlatforms(data.platform_cards || []);
        renderComposer(data);
        document.getElementById('contact-panel').classList.remove('d-none');
        document.getElementById('platforms-section').classList.remove('d-none');
        document.getElementById('composer-section').classList.remove('d-none');
        document.getElementById('alert-area').innerHTML = '';
    } catch (err) {
        Auth.showAlert('alert-area', esc(err.message), 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-search me-1"></i> Find';
    }
}

function renderContact(data) {
    const c = data.contact;
    const el = document.getElementById('contact-panel');
    if (!c) {
        el.innerHTML = `
            <div class="card border-0 shadow-sm">
                <div class="card-body">
                    <p class="text-muted mb-0"><i class="bi bi-info-circle me-1"></i>
                    No customer in CUST_SMS — but you can still use platform links and send promotions if you enter phone/email below.</p>
                </div>
            </div>`;
        return;
    }

    el.innerHTML = `
        <div class="card border-0 shadow-sm contact-hero">
            <div class="card-body">
                <div class="d-flex justify-content-between flex-wrap gap-2">
                    <div>
                        <div class="hero-name">${esc(c.name)}</div>
                        <div class="text-muted small">SMS ID ${c.cust_sms_id}${c.ac_id_display ? ` · GL ${esc(c.ac_id_display)}` : ''}</div>
                        <div class="mt-2">
                            ${c.phone_display ? `<span class="channel-pill ok"><i class="bi bi-phone"></i>${esc(c.phone_display)}</span>` : ''}
                            ${c.email_display ? `<span class="channel-pill ok"><i class="bi bi-envelope"></i>${esc(c.email_display)}</span>` : ''}
                            ${c.address ? `<span class="channel-pill ok"><i class="bi bi-geo-alt"></i>${esc(c.address)}</span>` : ''}
                        </div>
                    </div>
                    <div>
                        <a href="/admin/customer-contacts" class="btn btn-sm btn-outline-primary">
                            <i class="bi bi-pencil me-1"></i> Edit Social Links
                        </a>
                    </div>
                </div>
            </div>
        </div>`;
}

function renderPlatforms(cards) {
    const grid = document.getElementById('platform-grid');
    if (!cards.length) {
        grid.innerHTML = '<p class="text-muted">No platform links. Find by email to discover social profiles.</p>';
        return;
    }

    grid.innerHTML = cards.map((card) => `
        <div class="platform-card" style="background:${esc(card.color)}">
            ${card.confidence ? `<span class="confidence-pill">${esc(card.confidence)}</span>` : ''}
            <div>
                <div class="platform-icon"><i class="bi ${esc(card.icon)}"></i></div>
                <div class="platform-name mt-2">${esc(card.platform)}</div>
                <div class="platform-label">${esc(card.label)}</div>
            </div>
            <div class="card-actions">
                <a href="${esc(card.url)}" target="_blank" rel="noopener" class="btn btn-card">
                    <i class="bi bi-box-arrow-up-right"></i> Open
                </a>
                ${card.action === 'share' ? `<button type="button" class="btn btn-card" data-share-url="${esc(card.url)}"><i class="bi bi-link-45deg"></i> Use Link</button>` : ''}
                ${card.action === 'send' && card.platform === 'WhatsApp' ? `<button type="button" class="btn btn-card" data-send-wa="1"><i class="bi bi-send"></i> Send</button>` : ''}
                ${card.action === 'send' && card.platform === 'Email' ? `<button type="button" class="btn btn-card" data-send-email="1"><i class="bi bi-send"></i> Send</button>` : ''}
            </div>
        </div>
    `).join('');

    grid.querySelectorAll('[data-share-url]').forEach((btn) => {
        btn.addEventListener('click', () => {
            document.getElementById('promo-link').value = btn.dataset.shareUrl;
            Auth.showAlert('alert-area', 'Link added to promotion message.', 'success');
        });
    });
    grid.querySelectorAll('[data-send-wa]').forEach((btn) => {
        btn.addEventListener('click', () => sendPromotion('whatsapp'));
    });
    grid.querySelectorAll('[data-send-email]').forEach((btn) => {
        btn.addEventListener('click', () => sendPromotion('email'));
    });
}

function renderComposer(data) {
    const sel = document.getElementById('template-select');
    sel.innerHTML = (data.templates || []).map((t) =>
        `<option value="${esc(t.id)}">${esc(t.name)}</option>`
    ).join('');

    const ch = data.channels || {};
    document.getElementById('channel-status').innerHTML = `
        <div class="small">
            <span class="channel-pill ${ch.whatsapp_configured ? 'ok' : 'no'}">
                <i class="bi bi-whatsapp"></i> WhatsApp ${ch.whatsapp_configured ? 'Ready' : 'Manual'}
            </span>
            <span class="channel-pill ${ch.email_configured ? 'ok' : 'no'}">
                <i class="bi bi-envelope"></i> Email ${ch.email_configured ? 'Ready' : 'Setup needed'}
            </span>
        </div>
        <div class="small text-muted mt-2">
            Price scan: <a href="${esc(ch.guest_price_url)}" target="_blank">${esc(ch.guest_price_url)}</a>
        </div>`;

    document.getElementById('promo-message').value = data.preview_message || '';
    const tpl = (data.templates || [])[0];
    if (tpl) {
        document.getElementById('promo-subject').value = tpl.subject.replace('{company}', ch.guest_price_url ? '' : '');
        document.getElementById('promo-link').value = tpl.link || ch.guest_price_url || '';
    }
}

async function onTemplateChange() {
    if (!composeData) return;
    const templateId = document.getElementById('template-select').value;
    const params = new URLSearchParams();
    if (lookupType === 'phone') params.set('phone', document.getElementById('input-phone').value.trim());
    else if (lookupType === 'email') params.set('email', document.getElementById('input-email').value.trim());
    else params.set('cust_sms_id', document.getElementById('input-sms-id').value.trim());
    params.set('template_id', templateId);

    const data = await Api.get(`${API}/compose?${params.toString()}`);
    composeData = data;
    document.getElementById('promo-message').value = data.preview_message || '';
    const tpl = (data.templates || []).find((t) => t.id === templateId);
    if (tpl) {
        document.getElementById('promo-subject').value = tpl.subject;
        document.getElementById('promo-link').value = tpl.link || data.channels?.guest_price_url || '';
    }
}

async function sendPromotion(channel) {
    if (!composeData) return;
    const c = composeData.contact;
    const body = {
        cust_sms_id: c?.cust_sms_id || null,
        phone: c?.phone_raw || document.getElementById('input-phone').value.trim(),
        email: c?.email_display || document.getElementById('input-email').value.trim(),
        subject: document.getElementById('promo-subject').value.trim(),
        message: document.getElementById('promo-message').value.trim(),
        link: document.getElementById('promo-link').value.trim(),
        channel,
    };

    if (!body.message) {
        return Auth.showAlert('alert-area', 'Write a promotion message first.', 'warning');
    }

    try {
        const result = await Api.post(`${API}/send`, body);
        if (result.manual_url) {
            window.open(result.manual_url, '_blank', 'noopener');
        }
        Auth.showAlert('alert-area', esc(result.message), result.success ? 'success' : 'warning');
    } catch (err) {
        Auth.showAlert('alert-area', esc(err.message), 'danger');
    }
}

function copyMessage() {
    const msg = document.getElementById('promo-message').value;
    const link = document.getElementById('promo-link').value.trim();
    const full = link && !msg.includes(link) ? `${msg}\n\n${link}` : msg;
    navigator.clipboard.writeText(full).then(() => {
        Auth.showAlert('alert-area', 'Promotion copied — paste on Facebook, Instagram, SMS, etc.', 'success');
    });
}

function esc(v) {
    if (v == null) return '';
    return String(v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
