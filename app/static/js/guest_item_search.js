const ITEM_SEARCH_API = '/api/v1/public/price-lookup/search';
const ITEM_SEARCH_CONFIG_API = '/api/v1/public/price-lookup/search-config';
const RECENT_SEARCH_KEY = 'guest-item-recent-searches';

let searchDebounceMs = 250;
let searchMinChars = 2;
let searchMaxResults = 10;
let searchTimer = 0;
let searchSeq = 0;
let searchIndex = -1;
let searchItems = [];
let searchQty = {};

document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('guest-message');
    const panel = document.getElementById('guest-search-panel');
    if (!input || !panel) return;
    loadSearchConfig();
    input.addEventListener('input', onSearchInput);
    input.addEventListener('keydown', onSearchKeyDown);
    input.addEventListener('blur', () => {
        window.setTimeout(hideSearchPanel, 180);
    });
    document.getElementById('guest-chat-form')?.addEventListener('submit', hideSearchPanel);
});

async function loadSearchConfig() {
    try {
        const { response, data } = await fetchJson(ITEM_SEARCH_CONFIG_API, { method: 'GET' }, 8000);
        if (!response.ok) return;
        searchMinChars = Number(data.min_chars || 2);
        searchMaxResults = Number(data.max_results || 10);
        searchDebounceMs = Number(data.debounce_ms || 250);
    } catch (error) {
        /* keep defaults */
    }
}

function shouldLiveSearch(text) {
    const t = String(text || '').trim();
    if (typeof otpRequired !== 'undefined' && otpRequired && !phoneVerified) return false;
    const inCategory = Boolean(window.GUEST_SHOP_CATEGORY_ID)
        && (window.GUEST_SHOP_VIEW === 'products' || window.GUEST_SHOP_VIEW === 'offers');
    if (t.length < (inCategory ? 1 : searchMinChars)) return false;
    if (/^(menu|help|confirm|clear|cart|new|more|skip|keep|update|yes|no|back|categories|offers|search)$/i.test(t)) return false;
    if (/^\d{1,2}$/.test(t)) return false;
    if (/^additem\s/i.test(t)) return false;
    return true;
}

function onSearchInput() {
    const input = document.getElementById('guest-message');
    const q = (input?.value || '').trim();
    window.clearTimeout(searchTimer);
    if (!shouldLiveSearch(q)) {
        hideSearchPanel();
        return;
    }
    searchTimer = window.setTimeout(() => runLiveSearch(q), searchDebounceMs);
}

function onSearchKeyDown(event) {
    const panel = document.getElementById('guest-search-panel');
    if (!panel || panel.classList.contains('d-none') || !searchItems.length) {
        if (event.key === 'Escape') hideSearchPanel();
        return;
    }
    if (event.key === 'ArrowDown') {
        event.preventDefault();
        searchIndex = Math.min(searchItems.length - 1, searchIndex + 1);
        paintSearchActive();
    } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        searchIndex = Math.max(0, searchIndex - 1);
        paintSearchActive();
    } else if (event.key === 'Enter' && searchIndex >= 0) {
        event.preventDefault();
        addSearchItem(searchItems[searchIndex], qtyFor(searchIndex));
    } else if (event.key === 'Escape') {
        event.preventDefault();
        hideSearchPanel();
    }
}

async function runLiveSearch(q) {
    const seq = ++searchSeq;
    const categoryId = window.GUEST_SHOP_CATEGORY_ID;
    const inCategory = Boolean(categoryId)
        && (window.GUEST_SHOP_VIEW === 'products' || window.GUEST_SHOP_VIEW === 'offers');
    try {
        const url = inCategory
            ? `/api/v1/public/catalog/items?q=${encodeURIComponent(q)}&category_id=${encodeURIComponent(categoryId)}&page=1&page_size=${searchMaxResults}`
            : `${ITEM_SEARCH_API}?q=${encodeURIComponent(q)}&limit=${searchMaxResults}`;
        const { response, data } = await fetchJson(url, { method: 'GET' }, 12000);
        if (seq !== searchSeq) return;
        if (!response.ok) {
            renderSearchEmpty('Could not search right now. Please try again.');
            return;
        }
        rememberRecentSearch(q);
        const items = (data.items || []).map(normalizeSearchItem);
        if (!items.length) {
            const scope = inCategory ? (window.GUEST_SHOP_CATEGORY_TITLE || 'this category') : '';
            renderSearchEmpty(
                data.empty_hint
                || data.message
                || (scope
                    ? `No products matching "${q}" in ${scope}.`
                    : 'No matching products found.'),
            );
            return;
        }
        renderSearchItems(items, data.suggested_qty);
    } catch (error) {
        if (seq !== searchSeq) return;
        renderSearchEmpty(error.message || 'Search failed.');
    }
}

function normalizeSearchItem(item) {
    return {
        ...item,
        stock_label: item.stock_label || (item.in_stock === false ? 'out_of_stock' : 'in_stock'),
        suggested_qty: item.suggested_qty || 1,
    };
}

function qtyFor(idx, suggestedQty) {
    if (searchQty[idx] == null) {
        searchQty[idx] = Math.max(1, Number(suggestedQty || 1) || 1);
    }
    return searchQty[idx];
}

function renderSearchItems(items, suggestedQty) {
    const visible = (items || []).filter((item) => {
        const title = String(item.item_title || '').trim().toLowerCase();
        return !(title === 'empty' || title.startsWith('empty'));
    });
    searchItems = visible;
    searchIndex = -1;
    searchQty = {};
    const panel = document.getElementById('guest-search-panel');
    const recents = readRecentSearches();
    const chunks = [];
    if (recents.length) {
        chunks.push(`<div class="guest-search-recent">Recent: ${recents.map(esc).join(' · ')}</div>`);
    }
    visible.forEach((item, idx) => {
        const stock = stockText(item.stock_label, item.in_stock);
        const price = money(item.sales_rate);
        const brand = item.co_title ? ` · ${esc(item.co_title)}` : '';
        const barcode = item.barcodeid ? `Barcode ${esc(item.barcodeid)}` : '';
        const qty = qtyFor(idx, item.suggested_qty || suggestedQty);
        chunks.push(`
            <div class="guest-search-card" data-idx="${idx}" role="option">
                <div class="guest-search-card-body">
                    <div class="guest-search-title">${esc(item.item_title || '')}</div>
                    <div class="guest-search-meta">${barcode}${brand}</div>
                    <div class="guest-search-stock ${esc(item.stock_label || 'in_stock')}">${stock}</div>
                </div>
                <div class="guest-search-actions">
                    <div class="guest-search-price">Rs ${price}</div>
                    <div class="guest-search-qty" data-qty-wrap="${idx}">
                        <button type="button" class="guest-search-qty-btn" data-qty-minus="${idx}" aria-label="Decrease quantity">−</button>
                        <span class="guest-search-qty-val" data-qty-val="${idx}">${qty}</span>
                        <button type="button" class="guest-search-qty-btn" data-qty-plus="${idx}" aria-label="Increase quantity">+</button>
                    </div>
                    <button type="button" class="guest-search-add" data-add="${idx}">ADD</button>
                </div>
            </div>
        `);
    });
    if (!visible.length) {
        panel.innerHTML = `<div class="guest-search-empty">${esc('No matching products found.')}</div>`;
        panel.classList.remove('d-none');
        return;
    }
    panel.innerHTML = chunks.join('');
    panel.classList.remove('d-none');
    document.getElementById('guest-message')?.setAttribute('aria-expanded', 'true');
    panel.querySelectorAll('.guest-search-card').forEach((card) => {
        card.addEventListener('mousedown', (event) => {
            if (event.target.closest('[data-add], [data-qty-minus], [data-qty-plus]')) return;
            const idx = Number(card.getAttribute('data-idx'));
            addSearchItem(visible[idx], qtyFor(idx, suggestedQty));
        });
    });
    panel.querySelectorAll('[data-add]').forEach((btn) => {
        btn.addEventListener('mousedown', (event) => {
            event.preventDefault();
            event.stopPropagation();
            const idx = Number(btn.getAttribute('data-add'));
            addSearchItem(visible[idx], qtyFor(idx, suggestedQty));
        });
    });
    panel.querySelectorAll('[data-qty-minus], [data-qty-plus]').forEach((btn) => {
        btn.addEventListener('mousedown', (event) => {
            event.preventDefault();
            event.stopPropagation();
            const plus = btn.hasAttribute('data-qty-plus');
            const idx = Number(btn.getAttribute(plus ? 'data-qty-plus' : 'data-qty-minus'));
            const next = Math.max(1, qtyFor(idx, suggestedQty) + (plus ? 1 : -1));
            searchQty[idx] = next;
            const label = panel.querySelector(`[data-qty-val="${idx}"]`);
            if (label) label.textContent = String(next);
        });
    });
}

function renderSearchEmpty(message) {
    searchItems = [];
    searchIndex = -1;
    const panel = document.getElementById('guest-search-panel');
    panel.innerHTML = `<div class="guest-search-empty">${esc(message)}</div>`;
    panel.classList.remove('d-none');
}

function paintSearchActive() {
    document.querySelectorAll('.guest-search-card').forEach((card, idx) => {
        card.classList.toggle('is-active', idx === searchIndex);
        if (idx === searchIndex) card.scrollIntoView({ block: 'nearest' });
    });
}

function hideSearchPanel() {
    const panel = document.getElementById('guest-search-panel');
    if (!panel) return;
    panel.classList.add('d-none');
    panel.innerHTML = '';
    searchItems = [];
    searchIndex = -1;
    document.getElementById('guest-message')?.setAttribute('aria-expanded', 'false');
}

function addSearchItem(item, qty) {
    if (!item) return;
    const useQty = Math.max(1, Number(qty || item.suggested_qty || 1) || 1);
    hideSearchPanel();
    const input = document.getElementById('guest-message');
    if (!input) return;
    input.value = `ADDITEM ${item.manual_id} ${useQty}`;
    if (typeof sendMessage === 'function') {
        sendMessage({ preventDefault() {} });
    }
}

function stockText(label, inStock) {
    if (label === 'out' || inStock === false) return 'Out of stock';
    if (label === 'low') return 'Low stock';
    return 'In stock';
}

function money(value) {
    const n = Number(value || 0);
    if (!Number.isFinite(n)) return '—';
    return Number.isInteger(n) ? n.toLocaleString() : n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function rememberRecentSearch(q) {
    const clean = String(q || '').trim().toLowerCase();
    if (clean.length < 2) return;
    const list = readRecentSearches().filter((item) => item !== clean);
    list.unshift(clean);
    try {
        localStorage.setItem(RECENT_SEARCH_KEY, JSON.stringify(list.slice(0, 6)));
    } catch (error) {
        /* ignore */
    }
}

function readRecentSearches() {
    try {
        const raw = JSON.parse(localStorage.getItem(RECENT_SEARCH_KEY) || '[]');
        return Array.isArray(raw) ? raw.slice(0, 6) : [];
    } catch (error) {
        return [];
    }
}

function esc(value) {
    return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
