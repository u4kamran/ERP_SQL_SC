/**
 * Customer Marketing Contacts — powered by dbo.CUST_SMS.
 */
const API = '/api/v1/marketing/customer-contacts';

let currentPage = 1;
let pageSize = 50;
let totalItems = 0;
let canManage = false;
let editModal;
let editingCustSmsId = null;
let lookupType = 'phone';

document.addEventListener('DOMContentLoaded', async () => {
    const profile = await Auth.requireAuth();
    if (!profile) return;

    canManage = Auth.hasPermission('marketing.customer_contacts.manage')
        || Auth.hasPermission('auth.admin.full');

    if (!Auth.hasPermission('marketing.customer_contacts.view')
        && !Auth.hasPermission('support.phone_osint.view')
        && !Auth.hasPermission('auth.admin.full')) {
        Auth.showAlert('alert-area', 'You do not have permission to view customer contacts.', 'warning');
        return;
    }

    editModal = new bootstrap.Modal(document.getElementById('editModal'));

    setupLookupTabs();
    document.getElementById('btn-lookup').addEventListener('click', runLookup);
    document.getElementById('lookup-phone').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); runLookup(); }
    });
    document.getElementById('lookup-email').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); runLookup(); }
    });

    document.getElementById('btn-search').addEventListener('click', () => {
        currentPage = 1;
        loadContacts();
    });
    document.getElementById('search-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            currentPage = 1;
            loadContacts();
        }
    });
    document.getElementById('filter-select').addEventListener('change', () => {
        currentPage = 1;
        loadContacts();
    });
    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage -= 1;
            loadContacts();
        }
    });
    document.getElementById('next-page').addEventListener('click', () => {
        const maxPage = Math.ceil(totalItems / pageSize) || 1;
        if (currentPage < maxPage) {
            currentPage += 1;
            loadContacts();
        }
    });
    document.getElementById('btn-export-csv').addEventListener('click', exportCsv);
    document.getElementById('btn-save-contact').addEventListener('click', saveContact);

    await loadStats();
    await loadContacts();
});

function setupLookupTabs() {
    document.querySelectorAll('#lookup-tabs [data-lookup-type]').forEach((btn) => {
        btn.addEventListener('click', () => {
            lookupType = btn.dataset.lookupType;
            document.querySelectorAll('#lookup-tabs .nav-link').forEach((el) => el.classList.remove('active'));
            btn.classList.add('active');

            const isPhone = lookupType === 'phone';
            document.getElementById('lookup-label').textContent = isPhone ? 'Mobile Number' : 'Email Address';
            document.getElementById('lookup-phone-wrap').classList.toggle('d-none', !isPhone);
            document.getElementById('lookup-phone').classList.toggle('d-none', !isPhone);
            document.getElementById('lookup-email').classList.toggle('d-none', isPhone);
        });
    });
}

async function runLookup() {
    const btn = document.getElementById('btn-lookup');
    const phone = document.getElementById('lookup-phone').value.trim();
    const email = document.getElementById('lookup-email').value.trim();
    const query = lookupType === 'phone' ? phone : email;

    if (!query) {
        Auth.showAlert('alert-area', lookupType === 'phone' ? 'Enter a mobile number.' : 'Enter an email address.', 'warning');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Searching…';

    try {
        const params = new URLSearchParams();
        if (lookupType === 'phone') params.set('phone', phone);
        else params.set('email', email);

        const data = await Api.get(`${API}/lookup?${params.toString()}`);
        renderLookupResults(data);
        document.getElementById('lookup-results').classList.remove('d-none');

        if (data.contacts?.length) {
            document.getElementById('search-input').value = query;
            currentPage = 1;
            await loadContacts();
        }
    } catch (err) {
        Auth.showAlert('alert-area', esc(err.message), 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-search me-1"></i> Find Contact';
    }
}

function renderPlatformCards(cards) {
    if (!cards?.length) {
        return '<p class="text-muted small mb-0">No platform links available.</p>';
    }
    return `<div class="platform-grid">${cards.map((card) => `
        <div class="platform-card" style="background:${esc(card.color)}">
            ${card.confidence ? `<span class="confidence-pill">${esc(card.confidence)}</span>` : ''}
            <div>
                <div class="platform-icon"><i class="bi ${esc(card.icon)}"></i></div>
                <div class="platform-name mt-2">${esc(card.platform)}</div>
                <div class="platform-label">${esc(card.label)}</div>
                ${card.description ? `<div class="platform-desc">${esc(card.description)}</div>` : ''}
            </div>
            <div class="card-actions">
                <a href="${esc(card.url)}" target="_blank" rel="noopener noreferrer" class="btn btn-card">
                    <i class="bi bi-box-arrow-up-right"></i> ${card.confidence === 'search' ? 'Search' : 'Open'}
                </a>
            </div>
        </div>
    `).join('')}</div>`;
}

function renderLookupResults(data) {
    const el = document.getElementById('lookup-results');
    const hasContacts = data.contacts?.length > 0;
    const hasCards = data.platform_cards?.length > 0;
    const hasDiscovered = data.discovered_profiles?.length > 0;
    const isSuccess = hasContacts || hasDiscovered || hasCards;
    const cardClass = isSuccess ? 'lookup-result-card' : 'lookup-result-card not-found';

    const contactsHtml = hasContacts
        ? data.contacts.map((row) => `
            <div class="border rounded p-3 mb-2 bg-light">
                <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
                    <div>
                        <h6 class="mb-1">${esc(row.name)} <span class="badge bg-secondary">SMS ${row.cust_sms_id}</span></h6>
                        <div class="small text-muted">
                            ${row.phone_display ? `<span class="profile-chip"><i class="bi bi-phone"></i>${esc(row.phone_display)}</span>` : ''}
                            ${row.email_display ? `<span class="profile-chip"><i class="bi bi-envelope"></i>${esc(row.email_display)}</span>` : ''}
                            ${row.address ? `<span class="profile-chip"><i class="bi bi-geo-alt"></i>${esc(row.address)}</span>` : ''}
                        </div>
                        ${renderSavedSocial(row)}
                    </div>
                    <div class="contact-actions">
                        ${renderContactButtons(row)}
                        ${canManage ? `<button type="button" class="btn btn-sm btn-primary ms-1" data-edit-sms="${row.cust_sms_id}">
                            <i class="bi bi-pencil me-1"></i> Save Social
                        </button>
                        <a href="/admin/promotion-hub?${row.email_display ? 'email=' + encodeURIComponent(row.email_display) : 'phone=' + encodeURIComponent(row.phone_display)}&sms=${row.cust_sms_id}" class="btn btn-sm btn-success ms-1" title="Send promotion">
                            <i class="bi bi-megaphone"></i> Promote
                        </a>` : ''}
                    </div>
                </div>
            </div>
        `).join('')
        : `<div class="alert alert-info py-2 small mb-0">
            <i class="bi bi-info-circle me-1"></i>
            Email is not saved in <code>CUST_SMS</code> yet. Mobile numbers come from VB6 Customer SMS No.
            ${data.lookup_type === 'email' ? ' Check auto-discovered profiles and search links below.' : ''}
           </div>`;

    const platformCardsHtml = hasCards ? `
        <div class="mb-3">
            <h6 class="fw-semibold mb-2"><i class="bi bi-grid-3x3-gap me-1"></i> Platforms &amp; Social Profiles</h6>
            <p class="small text-muted">Open profiles to verify, then save confirmed links with <strong>Save Social</strong>. Use <strong>Promote</strong> to send offers.</p>
            ${renderPlatformCards(data.platform_cards)}
        </div>
    ` : '';

    const title = hasContacts
        ? 'Contact Found in System'
        : hasDiscovered
            ? 'Social Profiles Found'
            : 'Search Social Media';

    el.innerHTML = `
        <div class="card border-0 shadow-sm ${cardClass}">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2 flex-wrap gap-2">
                    <h5 class="mb-0">
                        <i class="bi bi-${hasContacts || hasDiscovered ? 'person-check' : 'search'} me-2"></i>
                        ${title}
                    </h5>
                    <span class="badge ${hasContacts || hasDiscovered ? 'bg-success' : 'bg-primary'}">${esc(data.message)}</span>
                </div>
                ${data.help_note ? `<p class="small text-muted mb-3">${esc(data.help_note)}</p>` : ''}
                ${contactsHtml}
                ${platformCardsHtml}
                ${hasContacts && canManage ? '' : (hasCards ? '' : `<p class="small text-muted mb-0">Facebook and Instagram block automatic search — use the platform cards above, then save confirmed profiles.</p>`)}
            </div>
        </div>
    `;

    el.querySelectorAll('[data-edit-sms]').forEach((btn) => {
        btn.addEventListener('click', () => openEditModal(Number(btn.dataset.editSms)));
    });
}

function confidenceBadge(level) {
    if (level === 'verified') return 'bg-success';
    if (level === 'strong') return 'bg-primary';
    if (level === 'likely') return 'bg-info text-dark';
    return 'bg-secondary';
}

function renderSavedSocial(row) {
    const items = [];
    if (row.facebook) items.push(`<a href="${esc(row.facebook)}" target="_blank" rel="noopener">Facebook</a>`);
    if (row.instagram) items.push(`<a href="${esc(row.instagram)}" target="_blank" rel="noopener">Instagram</a>`);
    if (row.tiktok) items.push(`<a href="${esc(row.tiktok)}" target="_blank" rel="noopener">TikTok</a>`);
    if (row.youtube) items.push(`<a href="${esc(row.youtube)}" target="_blank" rel="noopener">YouTube</a>`);
    if (row.website) items.push(`<a href="${esc(row.website)}" target="_blank" rel="noopener">Website</a>`);
    if (!items.length) return '';
    return `<div class="small mt-2"><strong>Saved:</strong> ${items.join(' · ')}</div>`;
}

async function loadStats() {
    try {
        const stats = await Api.get(`${API}/stats`);
        document.getElementById('stat-total').textContent = stats.total_accounts ?? '0';
        document.getElementById('stat-phone').textContent = stats.with_phone ?? '0';
        document.getElementById('stat-email').textContent = stats.with_email ?? '0';
        document.getElementById('stat-gl-linked').textContent = stats.gl_linked ?? '0';
    } catch (err) {
        Auth.showAlert('alert-area', esc(err.message), 'warning');
    }
}

async function loadContacts() {
    const tbody = document.getElementById('contacts-body');
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">Loading...</td></tr>';

    const q = document.getElementById('search-input').value.trim();
    const filter = document.getElementById('filter-select').value;
    const params = new URLSearchParams({
        page: String(currentPage),
        page_size: String(pageSize),
    });
    if (q) params.set('q', q);
    if (filter === 'phone') params.set('only_with_phone', 'true');
    if (filter === 'email') params.set('only_with_email', 'true');
    if (filter === 'social') params.set('only_with_social', 'true');
    if (filter === 'missing') params.set('only_missing', 'true');

    try {
        const data = await Api.get(`${API}/list?${params.toString()}`);
        totalItems = data.total || 0;
        renderTable(data.items || []);
        updatePagination();
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">${esc(err.message)}</td></tr>`;
    }
}

function renderTable(items) {
    const tbody = document.getElementById('contacts-body');
    if (!items.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">No customers found in CUST_SMS.</td></tr>';
        return;
    }

    tbody.innerHTML = items.map((row) => `
        <tr>
            <td><code>${row.cust_sms_id}</code></td>
            <td>
                <div class="fw-semibold">${esc(row.name)}</div>
                ${row.ac_id_display ? `<div class="small text-muted">GL ${esc(row.ac_id_display)}</div>` : '<div class="small text-muted">No GL link</div>'}
            </td>
            <td>
                ${row.phone_display ? esc(row.phone_display) : '<span class="missing-contact">—</span>'}
                ${row.phone_alt_display ? `<div class="small text-muted">${esc(row.phone_alt_display)}</div>` : ''}
            </td>
            <td class="small">${row.address ? esc(row.address) : '<span class="missing-contact">—</span>'}</td>
            <td class="small text-muted">${row.added_at ? esc(row.added_at) : '—'}</td>
            <td>
                ${row.email_display ? `<div class="small"><a href="mailto:${esc(row.email_display)}">${esc(row.email_display)}</a></div>` : ''}
                <div class="social-badges">${renderSocialBadges(row)}</div>
            </td>
            <td class="text-end contact-actions">
                ${renderContactButtons(row)}
            </td>
        </tr>
    `).join('');

    tbody.querySelectorAll('[data-edit-sms]').forEach((btn) => {
        btn.addEventListener('click', () => openEditModal(Number(btn.dataset.editSms)));
    });
}

function renderSocialBadges(row) {
    const badges = [];
    if (row.facebook) badges.push('<span class="badge bg-primary">FB</span>');
    if (row.instagram) badges.push('<span class="badge bg-danger">IG</span>');
    if (row.whatsapp) badges.push('<span class="badge bg-success">WA</span>');
    if (row.tiktok) badges.push('<span class="badge bg-dark">TT</span>');
    if (row.youtube) badges.push('<span class="badge bg-danger">YT</span>');
    if (row.website) badges.push('<span class="badge bg-secondary">Web</span>');
    if (!row.email_display && !badges.length) {
        return '<span class="missing-contact">—</span>';
    }
    return badges.join(' ') || '';
}

function renderContactButtons(row) {
    const parts = [];
    if (row.whatsapp) {
        parts.push(`<a class="btn btn-outline-success btn-sm" href="${esc(row.whatsapp)}" target="_blank" rel="noopener" title="WhatsApp"><i class="bi bi-whatsapp"></i></a>`);
    }
    if (row.email_display) {
        parts.push(`<a class="btn btn-outline-primary btn-sm" href="mailto:${esc(row.email_display)}" title="Email"><i class="bi bi-envelope"></i></a>`);
    }
    if (row.facebook) {
        parts.push(`<a class="btn btn-outline-primary btn-sm" href="${esc(row.facebook)}" target="_blank" rel="noopener" title="Facebook"><i class="bi bi-facebook"></i></a>`);
    }
    if (row.instagram) {
        parts.push(`<a class="btn btn-outline-danger btn-sm" href="${esc(row.instagram)}" target="_blank" rel="noopener" title="Instagram"><i class="bi bi-instagram"></i></a>`);
    }
    if (canManage) {
        parts.push(`<button type="button" class="btn btn-outline-secondary btn-sm" data-edit-sms="${row.cust_sms_id}" title="Edit / save social links"><i class="bi bi-pencil"></i></button>`);
    }
    return parts.join(' ') || '<span class="missing-contact small">—</span>';
}

function updatePagination() {
    const maxPage = Math.ceil(totalItems / pageSize) || 1;
    const from = totalItems ? (currentPage - 1) * pageSize + 1 : 0;
    const to = Math.min(currentPage * pageSize, totalItems);
    document.getElementById('pagination-info').textContent = `Showing ${from}–${to} of ${totalItems}`;
    document.getElementById('prev-page').disabled = currentPage <= 1;
    document.getElementById('next-page').disabled = currentPage >= maxPage;
}

async function openEditModal(custSmsId) {
    try {
        const row = await Api.get(`${API}/sms/${custSmsId}`);
        editingCustSmsId = custSmsId;
        document.getElementById('edit-account-label').textContent =
            `${row.name} (SMS ID ${row.cust_sms_id}) · ${row.phone_display || 'no phone'}`;
        document.getElementById('fld-email').value = row.marketing_email || '';
        document.getElementById('fld-website').value = row.website || '';
        document.getElementById('fld-facebook').value = row.facebook || '';
        document.getElementById('fld-instagram').value = row.instagram || '';
        document.getElementById('fld-whatsapp').value = row.whatsapp || '';
        document.getElementById('fld-tiktok').value = row.tiktok || '';
        document.getElementById('fld-youtube').value = row.youtube || '';
        document.getElementById('fld-notes').value = row.notes || '';
        editModal.show();
    } catch (err) {
        Auth.showAlert('alert-area', esc(err.message || 'Could not load customer.'), 'danger');
    }
}

async function saveContact() {
    if (!editingCustSmsId) return;
    const body = {
        email: document.getElementById('fld-email').value.trim(),
        website: document.getElementById('fld-website').value.trim(),
        facebook: document.getElementById('fld-facebook').value.trim(),
        instagram: document.getElementById('fld-instagram').value.trim(),
        whatsapp: document.getElementById('fld-whatsapp').value.trim(),
        tiktok: document.getElementById('fld-tiktok').value.trim(),
        youtube: document.getElementById('fld-youtube').value.trim(),
        notes: document.getElementById('fld-notes').value.trim(),
    };

    try {
        await Api.put(`${API}/sms/${editingCustSmsId}/marketing`, body);
        editModal.hide();
        Auth.showAlert('alert-area', 'Marketing contact saved.', 'success');
        await loadStats();
        await loadContacts();
    } catch (err) {
        Auth.showAlert('alert-area', esc(err.message), 'danger');
    }
}

async function exportCsv() {
    const q = document.getElementById('search-input').value.trim();
    const filter = document.getElementById('filter-select').value;
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (filter === 'phone') params.set('only_with_phone', 'true');
    if (filter === 'email') params.set('only_with_email', 'true');
    if (filter === 'social') params.set('only_with_social', 'true');

    try {
        const token = Api.getToken();
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        const response = await fetch(`${API}/export.csv?${params.toString()}`, {
            credentials: 'include',
            headers,
        });
        if (!response.ok) throw new Error('Export failed.');
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'customer-contacts.csv';
        a.click();
        URL.revokeObjectURL(url);
    } catch (err) {
        Auth.showAlert('alert-area', esc(err.message || 'Export failed.'), 'danger');
    }
}

function esc(value) {
    if (value == null) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
