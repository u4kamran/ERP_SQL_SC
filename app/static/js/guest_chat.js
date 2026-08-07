const GUEST_CHAT_API = '/api/v1/public/whatsapp/offline-chat';
const OTP_SEND_API = '/api/v1/public/whatsapp/mobile-otp/send';
const OTP_VERIFY_API = '/api/v1/public/whatsapp/mobile-otp/verify';
const STORAGE_KEY = 'guest-chat-conversation-id';
const PROFILE_KEY = 'guest-chat-profile';

// Fresh chat thread each page load (avoid stale order/price lists).
localStorage.removeItem(STORAGE_KEY);
let conversationId = '';
let recognition = null;
let listening = false;
let sending = false;
const OTP_REQUIRED = window.GUEST_MOBILE_OTP_REQUIRED === true;
let phoneVerified = !OTP_REQUIRED;
let pendingMessageAfterVerify = '';

const MAIN_MENU = [
    { title: '1 Delivery', payload: '1', style: 'chip' },
    { title: '2 Store info', payload: '2', style: 'chip' },
    { title: '3 Price list', payload: '3', style: 'chip' },
    { title: '4 Place order', payload: '4', style: 'chip' },
    { title: '5 Staff', payload: '5', style: 'chip' },
    { title: '6 My order', payload: '6', style: 'chip' },
];

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('guest-chat-form').addEventListener('submit', sendMessage);
    document.getElementById('btn-mic').addEventListener('click', toggleVoice);
    document.getElementById('btn-location').addEventListener('click', shareLocation);
    document.getElementById('btn-phone-hint').addEventListener('click', choosePhoneNumber);
    document.getElementById('btn-phone-manual').addEventListener('click', showManualPhoneInput);
    document.getElementById('btn-otp-verify').addEventListener('click', verifyMobileOtp);
    document.getElementById('btn-otp-resend').addEventListener('click', () => sendMobileOtp(true));
    document.getElementById('btn-otp-change').addEventListener('click', changeMobileNumber);
    document.getElementById('guest-otp-code').addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            verifyMobileOtp();
        }
    });
    document.getElementById('guest-quick-replies').addEventListener('click', onQuickReplyClick);
    document.getElementById('guest-messages').addEventListener('click', onQuickReplyClick);
    applyPhoneFromUrl();
    restoreProfileFields();
    updateIdentityBar();
    setupSpeech();
    if (!OTP_REQUIRED) {
        showOtpPanel(false);
        const otpPanel = document.getElementById('guest-otp-panel');
        if (otpPanel) otpPanel.classList.add('d-none');
        appendBubble(
            'out',
            'Assalam-o-Alaikum! OTP is temporarily off.\nTap a menu button to begin.',
            'bot',
        );
        renderQuickReplies(MAIN_MENU);
        if (document.getElementById('guest-phone').value.trim()) {
            const input = document.getElementById('guest-message');
            input.value = 'MENU';
            sendMessage(new Event('submit'));
        }
    } else if (document.getElementById('guest-phone').value.trim()) {
        if (phoneVerified) {
            const input = document.getElementById('guest-message');
            input.value = 'MENU';
            sendMessage(new Event('submit'));
        } else {
            appendBubble(
                'out',
                'Assalam-o-Alaikum!\nPlease verify your mobile with the OTP code to continue web chat.',
                'bot',
            );
            sendMobileOtp(false);
        }
    } else {
        appendBubble(
            'out',
            'Assalam-o-Alaikum!\nWeb chat requires mobile authentication.\n1) Choose your number\n2) Enter the OTP sent on WhatsApp\n\n(On WhatsApp Business chat, Meta already authenticates you.)',
            'bot',
        );
        renderQuickReplies([
            { title: 'Choose & verify phone', payload: '__PHONE_HINT__', style: 'action' },
            ...MAIN_MENU,
        ]);
        maybeAutoOfferPhoneHint();
    }
});

function applyPhoneFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const raw = params.get('phone') || params.get('mobile') || '';
    if (!raw) return;
    setPhoneNumber(raw, { welcome: false });
}

function formatLocalMobile(value) {
    const digits = String(value || '').replace(/\D/g, '');
    if (!digits) return '';
    if (digits.startsWith('92') && digits.length >= 12) return `0${digits.slice(2, 12)}`;
    if (digits.length >= 10) return digits.startsWith('0') ? digits.slice(0, 11) : `0${digits.slice(-10)}`;
    return digits;
}

function restoreProfileFields() {
    try {
        const raw = localStorage.getItem(PROFILE_KEY);
        if (!raw) return;
        const profile = JSON.parse(raw);
        if (profile.name && !document.getElementById('guest-name').value) {
            document.getElementById('guest-name').value = profile.name;
        }
        if (profile.phone && !document.getElementById('guest-phone').value) {
            document.getElementById('guest-phone').value = formatLocalMobile(profile.phone);
        }
        // Client hint only — server is source of truth for OTP verification.
        phoneVerified = OTP_REQUIRED ? !!profile.verified : true;
    } catch (error) {
        /* ignore */
    }
}

function saveProfileFields() {
    const name = document.getElementById('guest-name').value.trim();
    const phone = formatLocalMobile(document.getElementById('guest-phone').value.trim());
    if (phone) document.getElementById('guest-phone').value = phone;
    localStorage.setItem(
        PROFILE_KEY,
        JSON.stringify({ name, phone, verified: !!phoneVerified }),
    );
    updateIdentityBar();
}

function setPhoneNumber(raw, { welcome = true } = {}) {
    const phone = formatLocalMobile(raw);
    if (!phone) return false;
    const previous = formatLocalMobile(document.getElementById('guest-phone').value);
    document.getElementById('guest-phone').value = phone;
    if (previous !== phone) phoneVerified = false;
    saveProfileFields();
    document.getElementById('mic-status').textContent = `Mobile selected: ${phone}`;
    if (OTP_REQUIRED && welcome && !phoneVerified) {
        sendMobileOtp(false);
    } else if (welcome && phoneVerified && !sending) {
        const input = document.getElementById('guest-message');
        input.value = 'MENU';
        sendMessage(new Event('submit'));
    }
    return true;
}

function updateIdentityBar() {
    const name = document.getElementById('guest-name').value.trim();
    const phone = formatLocalMobile(document.getElementById('guest-phone').value.trim());
    const box = document.getElementById('guest-identity');
    const picker = document.getElementById('guest-phone-picker');
    if (!phone && !name) {
        box.classList.add('d-none');
        box.innerHTML = '';
        picker.classList.remove('is-locked');
        return;
    }
    const chips = [];
    if (name) chips.push(`<span class="guest-identity-chip">${esc(name)}</span>`);
    if (phone) {
        const verifiedClass = phoneVerified ? ' verified' : '';
        const mark = phoneVerified ? ' ✓' : '';
        chips.push(
            `<span class="guest-identity-chip${verifiedClass}"><i class="bi bi-phone"></i> ${esc(phone)}${mark}</span>`,
        );
        if (phoneVerified) picker.classList.add('is-locked');
        else picker.classList.remove('is-locked');
    } else {
        picker.classList.remove('is-locked');
    }
    box.innerHTML = chips.join('');
    box.classList.toggle('d-none', !chips.length);
}

function showOtpPanel(show) {
    document.getElementById('guest-otp-panel').classList.toggle('d-none', !show);
    if (show) document.getElementById('guest-otp-code').focus();
}

function changeMobileNumber() {
    phoneVerified = false;
    pendingMessageAfterVerify = '';
    document.getElementById('guest-phone').value = '';
    showOtpPanel(false);
    document.getElementById('guest-phone-picker').classList.remove('is-locked');
    showManualPhoneInput();
    saveProfileFields();
    document.getElementById('mic-status').textContent = 'Enter a new mobile number to verify.';
}

async function sendMobileOtp(isResend) {
    const phone = formatLocalMobile(document.getElementById('guest-phone').value);
    const status = document.getElementById('mic-status');
    if (!phone) {
        status.textContent = 'Choose or type a mobile number first.';
        return;
    }
    status.textContent = isResend ? 'Resending OTP…' : 'Sending OTP to your WhatsApp…';
    showOtpPanel(true);
    document.getElementById('otp-panel-help').textContent =
        `Sending a 6-digit code to ${phone} on WhatsApp…`;
    try {
        const response = await fetch(OTP_SEND_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone }),
        });
        const data = await response.json();
        if (!response.ok) {
            const detail = data.detail;
            throw new Error(
                typeof detail === 'string'
                    ? detail
                    : (detail && detail.message) || 'Could not send OTP.',
            );
        }
        let help = data.message || `Code sent to ${phone}.`;
        if (data.dev_code) help += ` Dev code: ${data.dev_code}`;
        document.getElementById('otp-panel-help').textContent = help;
        status.textContent = 'Enter the OTP to authenticate your mobile.';
        appendBubble('out', help, 'bot');
    } catch (error) {
        status.textContent = error.message || 'OTP send failed.';
        document.getElementById('otp-panel-help').textContent = status.textContent;
        appendBubble('out', status.textContent, 'system');
    }
}

async function verifyMobileOtp() {
    const phone = formatLocalMobile(document.getElementById('guest-phone').value);
    const code = document.getElementById('guest-otp-code').value.trim();
    const status = document.getElementById('mic-status');
    if (!phone || code.length < 4) {
        status.textContent = 'Enter the 6-digit code from WhatsApp.';
        return;
    }
    status.textContent = 'Verifying OTP…';
    try {
        const response = await fetch(OTP_VERIFY_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, code }),
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(typeof data.detail === 'string' ? data.detail : 'Invalid code.');
        }
        phoneVerified = true;
        saveProfileFields();
        showOtpPanel(false);
        document.getElementById('guest-otp-code').value = '';
        status.textContent = data.message || 'Mobile verified.';
        appendBubble('out', `✓ ${status.textContent}`, 'bot');
        const next = pendingMessageAfterVerify || 'MENU';
        pendingMessageAfterVerify = '';
        document.getElementById('guest-message').value = next;
        sendMessage(new Event('submit'));
    } catch (error) {
        status.textContent = error.message || 'Verification failed.';
        appendBubble('out', status.textContent, 'system');
    }
}

function showManualPhoneInput() {
    const input = document.getElementById('guest-phone');
    input.classList.remove('d-none');
    input.focus();
    document.getElementById('mic-status').textContent = 'Type your mobile, then tap a menu button.';
}

function maybeAutoOfferPhoneHint() {
    // Only auto-offer on Android-like devices; still requires a tap for privacy.
    const android = /Android/i.test(navigator.userAgent);
    if (!android) return;
    const help = document.getElementById('phone-hint-help');
    help.textContent = 'Android detected — tap the button to pick your SIM / Google number.';
}

/**
 * Google Phone Number Hint (Android Play Services) via WebView bridge when present,
 * otherwise Chrome Contact Picker / tel autofill — user chooses, never silent read.
 */
async function choosePhoneNumber() {
    const status = document.getElementById('mic-status');
    status.textContent = 'Opening phone number picker…';
    try {
        const phone = await requestPhoneNumberHint();
        if (!phone) {
            status.textContent = 'No number selected. You can try again or type it.';
            showManualPhoneInput();
            return;
        }
        setPhoneNumber(phone, { welcome: true });
    } catch (error) {
        status.textContent = error.message || 'Could not open phone picker. Type your number.';
        showManualPhoneInput();
    }
}

async function requestPhoneNumberHint() {
    // 1) Native Google Phone Number Hint bridge (Android WebView / TWA / WTN / custom).
    const fromBridge = await tryNativeGooglePhoneHint();
    if (fromBridge) return fromBridge;

    // 2) Chrome Contact Picker — pick a phone without typing (Android Chrome).
    const fromContacts = await tryContactPickerPhone();
    if (fromContacts) return fromContacts;

    // 3) Fall back: focus tel field so Chrome/Google autofill can suggest numbers.
    showManualPhoneInput();
    throw new Error(
        'Phone Number Hint needs Android Google Play Services (app/WebView) or Chrome Contact Picker. '
        + 'Type your number, or open this page inside the Android app.',
    );
}

async function tryNativeGooglePhoneHint() {
    // Custom bridge we document for Android WebView embedding this page.
    if (window.GooglePhoneHint && typeof window.GooglePhoneHint.requestPhoneNumber === 'function') {
        const value = await window.GooglePhoneHint.requestPhoneNumber();
        return value || null;
    }
    if (window.AndroidPhoneHint && typeof window.AndroidPhoneHint.request === 'function') {
        const value = window.AndroidPhoneHint.request();
        if (value && typeof value.then === 'function') return value;
        return value || null;
    }
    // WebToNative / similar wrappers that expose Google Hint.
    if (window.WTN && typeof window.WTN.getDevicePhoneNumber === 'function') {
        return new Promise((resolve) => {
            try {
                window.WTN.getDevicePhoneNumber({
                    callback(response) {
                        if (response && response.success && response.phoneNumber) {
                            resolve(response.phoneNumber);
                        } else {
                            resolve(null);
                        }
                    },
                });
            } catch (error) {
                resolve(null);
            }
        });
    }
    return null;
}

async function tryContactPickerPhone() {
    if (!('contacts' in navigator) || !('ContactsManager' in window)) {
        return null;
    }
    try {
        const supported = await navigator.contacts.getProperties();
        if (!supported.includes('tel')) return null;
        const selected = await navigator.contacts.select(['tel'], { multiple: false });
        if (!selected || !selected.length) return null;
        const tels = selected[0].tel || [];
        const first = Array.isArray(tels) ? tels[0] : tels;
        const raw = typeof first === 'string' ? first : (first && first.value) || '';
        return raw || null;
    } catch (error) {
        // User cancelled or permission denied.
        return null;
    }
}

function setupSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const status = document.getElementById('mic-status');
    const micBtn = document.getElementById('btn-mic');
    if (!SpeechRecognition) {
        micBtn.disabled = true;
        status.textContent = 'Voice not supported. Tap menu buttons or type item names.';
        return;
    }
    recognition = new SpeechRecognition();
    recognition.lang = 'en-PK';
    recognition.interimResults = false;
    recognition.maxAlternatives = 3;
    recognition.onstart = () => {
        listening = true;
        micBtn.classList.add('active');
        status.textContent = 'Listening… speak item name (Urdu/English).';
    };
    recognition.onend = () => {
        listening = false;
        micBtn.classList.remove('active');
        status.textContent = 'Tap a choice, type an item name, or use the mic.';
    };
    recognition.onerror = () => {
        listening = false;
        micBtn.classList.remove('active');
        status.textContent = 'Could not hear clearly. Tap a choice or type instead.';
    };
    recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map((result) => result[0].transcript)
            .join(' ')
            .trim();
        if (!transcript) return;
        const input = document.getElementById('guest-message');
        input.value = /^(\d|menu|help|price|rate|delivery|store|order)/i.test(transcript)
            ? transcript
            : `price ${transcript}`;
        sendMessage(new Event('submit'));
    };
}

function toggleVoice() {
    if (!recognition) return;
    if (listening) {
        recognition.stop();
        return;
    }
    try {
        recognition.start();
    } catch (error) {
        document.getElementById('mic-status').textContent = 'Mic busy. Try again.';
    }
}

function onQuickReplyClick(event) {
    const btn = event.target.closest('[data-payload]');
    if (!btn || sending) return;
    const payload = btn.getAttribute('data-payload') || '';
    if (!payload) return;
    if (payload === '__PHONE_HINT__') {
        choosePhoneNumber();
        return;
    }
    const input = document.getElementById('guest-message');
    input.value = payload;
    sendMessage(new Event('submit'));
}

function shareLocation() {
    const status = document.getElementById('mic-status');
    if (!navigator.geolocation) {
        status.textContent = 'Location not supported in this browser.';
        return;
    }
    status.textContent = 'Getting your GPS pin for Google Maps…';
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            const input = document.getElementById('guest-message');
            input.value = 'LOCATION';
            sendMessage(new Event('submit'), {
                latitude: pos.coords.latitude,
                longitude: pos.coords.longitude,
                accuracy: pos.coords.accuracy,
            });
        },
        () => {
            status.textContent = 'Could not get location. Paste a Google Maps link instead.';
        },
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 },
    );
}

async function sendMessage(event, geo = null) {
    event.preventDefault();
    if (sending) return;
    const input = document.getElementById('guest-message');
    const nameInput = document.getElementById('guest-name');
    const phoneInput = document.getElementById('guest-phone');
    const message = input.value.trim();
    if (!message) return;

    // Collect mobile first if missing.
    if (!formatLocalMobile(phoneInput.value) && !geo) {
        const status = document.getElementById('mic-status');
        status.textContent = 'Collecting your mobile number…';
        try {
            const picked = await requestPhoneNumberHint();
            if (picked) setPhoneNumber(picked, { welcome: false });
        } catch (error) {
            /* fall through */
        }
        if (!formatLocalMobile(phoneInput.value)) {
            showManualPhoneInput();
            status.textContent = 'Select or type your mobile, then send again.';
            appendBubble(
                'out',
                'Please choose your mobile number, then authenticate with OTP.',
                'bot',
            );
            renderQuickReplies([
                { title: 'Choose & verify phone', payload: '__PHONE_HINT__', style: 'action' },
            ]);
            return;
        }
    }

    // Web chat OTP authentication (skipped when GUEST_MOBILE_OTP_REQUIRED=false).
    if (OTP_REQUIRED && !phoneVerified && !geo) {
        pendingMessageAfterVerify = message;
        input.value = '';
        appendBubble(
            'out',
            'Authenticate your mobile with the OTP code before chatting on web.',
            'bot',
        );
        await sendMobileOtp(false);
        return;
    }

    sending = true;
    saveProfileFields();
    clearInlineSelection();
    const hideEcho = message.toUpperCase() === 'MENU' && !conversationId;
    if (!hideEcho) {
        const label = geo ? `[location] ${geo.latitude.toFixed(5)}, ${geo.longitude.toFixed(5)}` : message;
        appendBubble('in', label, nameInput.value.trim() || 'You');
    }
    input.value = '';
    input.disabled = true;
    setQuickRepliesEnabled(false);
    try {
        const payload = {
            conversation_id: conversationId || null,
            message,
            display_name: nameInput.value.trim(),
            phone: phoneInput.value.trim(),
        };
        if (geo) {
            payload.latitude = geo.latitude;
            payload.longitude = geo.longitude;
            payload.accuracy = geo.accuracy;
        }
        const response = await fetch(GUEST_CHAT_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok) {
            const detail = data.detail;
            if (
                response.status === 403
                && detail
                && (detail.code === 'mobile_not_verified'
                    || (typeof detail === 'object' && detail.message))
            ) {
                phoneVerified = false;
                saveProfileFields();
                pendingMessageAfterVerify = message;
                appendBubble(
                    'out',
                    (detail && detail.message)
                        || 'Please verify your mobile with OTP first.',
                    'bot',
                );
                await sendMobileOtp(false);
                return;
            }
            throw new Error(
                typeof detail === 'string'
                    ? detail
                    : (detail && detail.message) || data.message || 'Chat failed.',
            );
        }
        conversationId = data.conversation.conversation_id;
        localStorage.setItem(STORAGE_KEY, conversationId);
        if (data.conversation.display_name) {
            nameInput.value = data.conversation.display_name;
        }
        if (data.conversation.phone) {
            phoneInput.value = formatLocalMobile(data.conversation.phone);
        }
        if (data.phone_verified) phoneVerified = true;
        saveProfileFields();
        appendBubble('out', data.reply, 'bot');
        const replies = Array.isArray(data.quick_replies) && data.quick_replies.length
            ? ensureMainMenuChips(data.quick_replies)
            : MAIN_MENU;
        renderQuickReplies(replies);
    } catch (error) {
        appendBubble('out', error.message || 'Could not send message.', 'system');
        renderQuickReplies(MAIN_MENU);
    } finally {
        sending = false;
        input.disabled = false;
        input.focus();
        setQuickRepliesEnabled(true);
    }
}

function ensureMainMenuChips(items) {
    const rows = Array.isArray(items) ? items.slice() : [];
    const hasItems = rows.some((item) => (item.style || 'chip') === 'item');
    if (hasItems) return rows;
    const payloads = new Set(rows.map((item) => String(item.payload || '').trim()));
    // Main-menu responses sometimes omit option 6 from stale server/config builds.
    const looksLikeMainMenu = ['1', '2', '3', '4', '5'].every((p) => payloads.has(p));
    if (!looksLikeMainMenu) return rows;
    MAIN_MENU.forEach((item) => {
        if (!payloads.has(String(item.payload))) {
            rows.push(item);
            payloads.add(String(item.payload));
        }
    });
    return rows;
}

function renderQuickReplies(items) {
    const box = document.getElementById('guest-quick-replies');
    box.innerHTML = '';
    box.classList.remove('is-selection');
    const rows = ensureMainMenuChips(items || []);
    const itemRows = rows.filter((item) => (item.style || 'chip') === 'item');
    const actionRows = rows.filter((item) => (item.style || 'chip') !== 'item');

    if (itemRows.length) {
        appendInlineSelection(itemRows);
    }

    const chipRow = document.createElement('div');
    chipRow.className = 'guest-chip-row';
    (actionRows.length ? actionRows : rows).forEach((item) => {
        if ((item.style || 'chip') === 'item') return;
        chipRow.appendChild(buildChip(item));
    });
    if (!actionRows.length && !itemRows.length) {
        MAIN_MENU.forEach((item) => chipRow.appendChild(buildChip(item)));
    }
    if (chipRow.childNodes.length) box.appendChild(chipRow);
}

function clearInlineSelection() {
    document.querySelectorAll('#guest-messages .guest-inline-select').forEach((el) => {
        el.remove();
    });
}

function appendInlineSelection(itemRows) {
    clearInlineSelection();
    const box = document.getElementById('guest-messages');
    const panel = document.createElement('div');
    panel.className = 'guest-inline-select';
    const label = document.createElement('div');
    label.className = 'guest-select-label dark';
    label.textContent = 'Tap an item to select';
    panel.appendChild(label);
    const list = document.createElement('div');
    list.className = 'guest-select-list';
    itemRows.forEach((item) => list.appendChild(buildItemChoice(item)));
    panel.appendChild(list);
    box.appendChild(panel);
    box.scrollTop = box.scrollHeight;
}

function buildItemChoice(item) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'guest-item-choice';
    btn.setAttribute('data-payload', item.payload);
    const num = document.createElement('span');
    num.className = 'guest-item-num';
    num.textContent = String(item.payload || '');
    const body = document.createElement('span');
    body.className = 'guest-item-body';
    const title = document.createElement('span');
    title.className = 'guest-item-title';
    title.textContent = item.title || `Item ${item.payload || ''}`;
    body.appendChild(title);
    if (item.subtitle) {
        const sub = document.createElement('span');
        sub.className = 'guest-item-sub';
        sub.textContent = item.subtitle;
        body.appendChild(sub);
    }
    const price = document.createElement('span');
    price.className = 'guest-item-price';
    price.textContent = item.meta || '';
    const chevron = document.createElement('span');
    chevron.className = 'guest-item-chevron';
    chevron.textContent = '›';
    btn.appendChild(num);
    btn.appendChild(body);
    btn.appendChild(price);
    btn.appendChild(chevron);
    return btn;
}

function buildChip(item) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = item.style === 'action' ? 'guest-chip guest-chip-action' : 'guest-chip';
    btn.textContent = item.title;
    btn.setAttribute('data-payload', item.payload);
    return btn;
}

function setQuickRepliesEnabled(enabled) {
    document
        .querySelectorAll('#guest-quick-replies [data-payload], #guest-messages [data-payload]')
        .forEach((btn) => {
            btn.disabled = !enabled;
        });
}

function appendBubble(direction, text, sender) {
    const box = document.getElementById('guest-messages');
    const bubble = document.createElement('div');
    bubble.className = `wa-bubble ${direction === 'out' ? 'out' : 'in'}`;
    bubble.innerHTML = `${esc(text)}<span class="meta">${esc(sender)}</span>`;
    box.appendChild(bubble);
    box.scrollTop = box.scrollHeight;
}

function esc(value) {
    const element = document.createElement('div');
    element.textContent = value == null ? '' : String(value);
    return element.innerHTML;
}
