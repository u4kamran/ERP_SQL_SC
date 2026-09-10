const GUEST_CHAT_API = '/api/v1/public/whatsapp/offline-chat';
const OTP_SEND_API = '/api/v1/public/whatsapp/mobile-otp/send';
const OTP_VERIFY_API = '/api/v1/public/whatsapp/mobile-otp/verify';
const OTP_STATUS_API = '/api/v1/public/whatsapp/mobile-otp/status';
const VOICE_TRANSCRIBE_API = '/api/v1/public/whatsapp/voice-transcribe';
const STORAGE_KEY = 'guest-chat-conversation-id';
const PROFILE_KEY = 'guest-chat-profile';
const VOICE_LANGS = [
    { code: 'en-US', label: 'EN', hint: 'English (Pakistan/US), product names' },
    { code: 'ur-PK', label: 'UR', hint: 'Urdu and Roman Urdu (Pakistan)' },
    { code: 'en-GB', label: 'EN-GB', hint: 'English, product brand names' },
];
let recordStartedAt = 0;

// Fresh chat thread each page load (avoid stale order/price lists).
localStorage.removeItem(STORAGE_KEY);
let conversationId = '';
let recognition = null;
let listening = false;
let sending = false;
let voiceLangIndex = 0;
let mediaRecorder = null;
let mediaStream = null;
let mediaChunks = [];
let recording = false;
let voiceBusy = false;
let otpRequired = window.GUEST_MOBILE_OTP_REQUIRED !== false;
const VOICE_CLOUD_ENABLED = window.GUEST_VOICE_CLOUD_ENABLED === true;
const VOICE_PROVIDER = String(window.GUEST_VOICE_PROVIDER || '');
const VOICE_CLOUD_BLOCK_KEY = 'guest-voice-cloud-blocked';
let phoneVerified = !otpRequired;
let pendingMessageAfterVerify = '';
let otpSendInFlight = false;
const shelfQty = {};
const shelfAddedManualIds = new Set();
let lastShelfAddedManualId = '';

function isVoiceCloudBlocked() {
    try { return sessionStorage.getItem(VOICE_CLOUD_BLOCK_KEY) === '1'; }
    catch (error) { return false; }
}

function markVoiceCloudBlocked() {
    try { sessionStorage.setItem(VOICE_CLOUD_BLOCK_KEY, '1'); }
    catch (error) { /* ignore */ }
}

function clearVoiceCloudBlocked() {
    try { sessionStorage.removeItem(VOICE_CLOUD_BLOCK_KEY); }
    catch (error) { /* ignore */ }
}

const MAIN_MENU = [
    { title: '1 Delivery', payload: '1', style: 'chip' },
    { title: '2 Store info', payload: '2', style: 'chip' },
    { title: '3 Price list', payload: '3', style: 'chip' },
    { title: '4 Place order', payload: '4', style: 'chip' },
    { title: '5 Staff', payload: '5', style: 'chip' },
    { title: '6 My order', payload: '6', style: 'chip' },
];

document.addEventListener('DOMContentLoaded', async () => {
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
    const phoneField = document.getElementById('guest-phone');
    phoneField.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            requestOtpIfPhoneReady();
        }
    });
    phoneField.addEventListener('blur', requestOtpIfPhoneReady);
    phoneField.addEventListener('input', () => {
        const phone = formatLocalMobile(phoneField.value);
        if (isCompleteLocalMobile(phone)) requestOtpIfPhoneReady();
    });
    document.getElementById('guest-quick-replies').addEventListener('click', onQuickReplyClick);
    document.getElementById('guest-messages').addEventListener('click', onQuickReplyClick);
    const cartSticky = document.getElementById('guest-cart-sticky');
    if (cartSticky) {
        const openCart = () => {
            if (sending) return;
            const input = document.getElementById('guest-message');
            input.value = 'CART';
            sendMessage(new Event('submit'));
        };
        cartSticky.addEventListener('click', openCart);
        cartSticky.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                openCart();
            }
        });
    }
    document.getElementById('btn-voice-send').addEventListener('click', sendConfirmedVoice);
    document.getElementById('btn-voice-retry').addEventListener('click', () => {
        hideVoiceConfirm();
        toggleVoice();
    });
    document.getElementById('btn-voice-cancel').addEventListener('click', hideVoiceConfirm);
    document.getElementById('btn-voice-lang').addEventListener('click', cycleVoiceLang);
    document.getElementById('btn-voice-hud-stop').addEventListener('click', () => {
        if (recording) stopMediaRecording();
        else if (listening && recognition) {
            try { recognition.stop(); } catch (error) { /* ignore */ }
            setVoiceStatus('Stopped.');
            hideVoiceHud();
        }
    });
    applyPhoneFromUrl();
    restoreProfileFields();
    await loadOtpPolicy();
    // Never trust browser "verified" — server OTP status is required.
    phoneVerified = !otpRequired;
    if (otpRequired) {
        await refreshServerOtpStatus();
    }
    updateIdentityBar();
    updateChatMessageRequired();
    setupSpeech();
    if (!otpRequired) {
        showOtpPanel(false);
        const otpPanel = document.getElementById('guest-otp-panel');
        if (otpPanel) otpPanel.classList.add('d-none');
        appendBubble(
            'out',
            'Assalam-o-Alaikum! OTP is temporarily off.\nTap a menu button to begin.',
            'bot',
        );
        renderQuickReplies(MAIN_MENU);
        applyInputPrompt(
            'Tap a menu option, or type 1–6…',
            'Main menu — Delivery · Price · Order · My order',
            MAIN_MENU,
        );
        if (document.getElementById('guest-phone').value.trim()) {
            const input = document.getElementById('guest-message');
            input.value = 'MENU';
            sendMessage(new Event('submit'));
        }
    } else if (phoneVerified) {
        appendBubble(
            'out',
            'Assalam-o-Alaikum! Mobile already verified.\nTap a menu button to begin.',
            'bot',
        );
        renderQuickReplies(MAIN_MENU);
        applyInputPrompt(
            'Tap a menu option, or type 1–6…',
            'Main menu — Delivery · Price · Order · My order',
            MAIN_MENU,
        );
    } else {
        appendBubble(
            'out',
            'Assalam-o-Alaikum!\nWeb chat requires mobile registration and OTP.\n1) Choose or type your number\n2) Enter the OTP sent to your mobile',
            'bot',
        );
        renderQuickReplies([
            { title: 'Choose & verify phone', payload: '__PHONE_HINT__', style: 'action' },
        ]);
        applyInputPrompt(
            'Enter mobile, then verify OTP…',
            'OTP is required before menu / order / price.',
            [],
        );
        showManualPhoneInput();
        const savedPhone = formatLocalMobile(document.getElementById('guest-phone').value);
        if (savedPhone) {
            document.getElementById('mic-status').textContent =
                `Confirm ${savedPhone} with OTP to continue.`;
            sendMobileOtp(false);
        } else {
            document.getElementById('mic-status').textContent =
                'Register your mobile number, then enter the OTP.';
            maybeAutoOfferPhoneHint();
        }
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

function isCompleteLocalMobile(value) {
    const phone = formatLocalMobile(value);
    return phone.length === 11 && phone.startsWith('03');
}

function updateChatMessageRequired() {
    const input = document.getElementById('guest-message');
    if (!input) return;
    if (otpRequired && !phoneVerified) input.removeAttribute('required');
    else input.setAttribute('required', 'required');
}

function requestOtpIfPhoneReady() {
    if (!otpRequired || phoneVerified || otpSendInFlight) return;
    if (!isCompleteLocalMobile(document.getElementById('guest-phone').value)) return;
    sendMobileOtp(false);
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
        // Do not restore verified from localStorage — that skipped OTP on reload.
    } catch (error) {
        /* ignore */
    }
}

async function loadOtpPolicy() {
    try {
        const { response, data } = await fetchJson(
            OTP_STATUS_API,
            { method: 'GET' },
            10000,
        );
        if (!response.ok) {
            otpRequired = true;
            return;
        }
        if (typeof data.otp_required === 'boolean') otpRequired = data.otp_required;
        else if (typeof data.required === 'boolean') otpRequired = data.required;
        else otpRequired = true;
    } catch (error) {
        otpRequired = true;
    }
}

async function refreshServerOtpStatus() {
    if (!otpRequired) {
        phoneVerified = true;
        return;
    }
    phoneVerified = false;
    const phone = formatLocalMobile(document.getElementById('guest-phone').value);
    if (!phone) return;
    try {
        const { response, data } = await fetchJson(
            `${OTP_STATUS_API}?mobile=${encodeURIComponent(phone)}`,
            { method: 'GET' },
            10000,
        );
        if (response.ok) phoneVerified = !!data.verified;
    } catch (error) {
        phoneVerified = false;
    }
    saveProfileFields();
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
    if (otpRequired && welcome && !phoneVerified) {
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

async function fetchJson(url, options = {}, timeoutMs = 20000) {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
        const response = await fetch(url, { ...options, signal: controller.signal });
        let data = {};
        try {
            data = await response.json();
        } catch (error) {
            data = {};
        }
        return { response, data };
    } catch (error) {
        if (error && error.name === 'AbortError') {
            throw new Error('Request timed out. Please try again.');
        }
        throw error;
    } finally {
        window.clearTimeout(timer);
    }
}

async function sendMobileOtp(isResend) {
    const phone = formatLocalMobile(document.getElementById('guest-phone').value);
    const status = document.getElementById('mic-status');
    if (!phone) {
        status.textContent = 'Choose or type a mobile number first.';
        return;
    }
    if (!isCompleteLocalMobile(phone)) {
        status.textContent = 'Enter a full mobile 03XXXXXXXXX, then OTP will send.';
        showManualPhoneInput();
        return;
    }
    if (otpSendInFlight) return;
    otpSendInFlight = true;
    status.textContent = isResend ? 'Resending OTP…' : 'Sending OTP…';
    showOtpPanel(true);
    document.getElementById('otp-panel-help').textContent =
        `Sending a 6-digit code to ${phone}…`;
    try {
        const { response, data } = await fetchJson(OTP_SEND_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone }),
        }, 15000);
        if (!response.ok) {
            const detail = data.detail;
            throw new Error(
                typeof detail === 'string'
                    ? detail
                    : (detail && detail.message) || 'Could not send OTP.',
            );
        }
        if (data.otp_required === false) {
            otpRequired = false;
            showOtpPanel(false);
            status.textContent = 'OTP is not required.';
            document.getElementById('otp-panel-help').textContent = '';
            updateChatMessageRequired();
            return;
        }
        let help = data.message || `Code sent to ${phone}.`;
        if (data.dev_code) help += ` Dev code: ${data.dev_code}`;
        document.getElementById('otp-panel-help').textContent = help;
        status.textContent = 'Enter the OTP from your mobile.';
        appendBubble('out', help, 'bot');
    } catch (error) {
        status.textContent = error.message || 'OTP send failed.';
        document.getElementById('otp-panel-help').textContent = status.textContent;
        appendBubble('out', status.textContent, 'system');
    } finally {
        otpSendInFlight = false;
    }
}

async function verifyMobileOtp() {
    const phone = formatLocalMobile(document.getElementById('guest-phone').value);
    const code = document.getElementById('guest-otp-code').value.trim();
    const status = document.getElementById('mic-status');
    if (!phone || code.length < 4) {
        status.textContent = 'Enter the 6-digit code from your mobile.';
        return;
    }
    status.textContent = 'Verifying OTP…';
    try {
        const { response, data } = await fetchJson(OTP_VERIFY_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, code }),
        }, 15000);
        if (!response.ok) {
            throw new Error(typeof data.detail === 'string' ? data.detail : 'Invalid code.');
        }
        phoneVerified = true;
        saveProfileFields();
        updateChatMessageRequired();
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
    document.getElementById('mic-status').textContent =
        'Type your mobile 03XXXXXXXXX, then verify OTP.';
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

function currentVoiceLang() {
    return VOICE_LANGS[voiceLangIndex] || VOICE_LANGS[0];
}

function cycleVoiceLang() {
    voiceLangIndex = (voiceLangIndex + 1) % VOICE_LANGS.length;
    const lang = currentVoiceLang();
    const btn = document.getElementById('btn-voice-lang');
    if (btn) btn.textContent = `Lang: ${lang.label}`;
    if (recognition) recognition.lang = lang.code;
    setVoiceStatus(`Voice language: ${lang.label} (${lang.code})`);
}

function getSpeechRecognitionCtor() {
    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

function setVoiceStatus(message) {
    const status = document.getElementById('mic-status');
    if (status) status.textContent = message;
    const hudText = document.getElementById('guest-voice-hud-text');
    if (hudText) hudText.textContent = message;
}

function showVoiceHud(message) {
    const hud = document.getElementById('guest-voice-hud');
    if (!hud) return;
    setVoiceStatus(message);
    hud.classList.remove('d-none');
}

function hideVoiceHud() {
    const hud = document.getElementById('guest-voice-hud');
    if (hud) hud.classList.add('d-none');
}

function setMicActive(active) {
    const micBtn = document.getElementById('btn-mic');
    if (!micBtn) return;
    micBtn.classList.toggle('active', !!active);
}

function pickRecorderMime() {
    if (!window.MediaRecorder) return '';
    const candidates = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/mp4',
        'audio/ogg;codecs=opus',
    ];
    for (let i = 0; i < candidates.length; i += 1) {
        if (MediaRecorder.isTypeSupported(candidates[i])) return candidates[i];
    }
    return '';
}

function releaseMediaStream() {
    if (mediaStream) {
        mediaStream.getTracks().forEach((track) => {
            try { track.stop(); } catch (error) { /* ignore */ }
        });
    }
    mediaStream = null;
}

function bindRecognitionHandlers(instance) {
    instance.interimResults = true;
    instance.continuous = false;
    instance.maxAlternatives = 3;
    instance.onstart = () => {
        listening = true;
        setMicActive(true);
        showVoiceHud('Listening… speak now.');
    };
    instance.onspeechstart = () => {
        setVoiceStatus('Hearing you… keep speaking.');
    };
    instance.onend = () => {
        listening = false;
        setMicActive(false);
        if (!document.getElementById('guest-voice-confirm').classList.contains('d-none')) {
            hideVoiceHud();
            return;
        }
        hideVoiceHud();
        if ((document.getElementById('mic-status').textContent || '').match(
            /^(Listening|Hearing|Starting)/,
        )) {
            setVoiceStatus('Stopped. Tap mic again if nothing was captured.');
        }
    };
    instance.onerror = (event) => {
        listening = false;
        setMicActive(false);
        hideVoiceHud();
        const err = (event && event.error) || '';
        if (err === 'not-allowed' || err === 'service-not-allowed') {
            setVoiceStatus('Mic blocked. Chrome → Site settings → Microphone → Allow.');
        } else if (err === 'no-speech') {
            setVoiceStatus('No speech heard. Tap mic and speak again.');
        } else if (err === 'network') {
            setVoiceStatus('Chrome speech network failed. Tap mic to use record mode.');
        } else if (err === 'audio-capture') {
            setVoiceStatus('No mic found. Check phone microphone.');
        } else if (err !== 'aborted') {
            setVoiceStatus(`Voice error: ${err || 'unknown'}. Tap mic again.`);
        }
    };
    instance.onresult = (event) => {
        let interim = '';
        let finalText = '';
        for (let i = event.resultIndex; i < event.results.length; i += 1) {
            const result = event.results[i];
            const text = (result[0] && result[0].transcript || '').trim();
            if (!text) continue;
            if (result.isFinal) finalText += `${text} `;
            else interim += `${text} `;
        }
        finalText = finalText.trim();
        interim = interim.trim();
        if (finalText) {
            hideVoiceHud();
            showVoiceConfirm(finalText);
            try { instance.stop(); } catch (error) { /* ignore */ }
            return;
        }
        if (interim) setVoiceStatus(`Hearing: ${interim}`);
    };
}

function setupSpeech() {
    const micBtn = document.getElementById('btn-mic');
    if (!window.isSecureContext) {
        micBtn.disabled = true;
        setVoiceStatus('Voice needs HTTPS. Open https://erp.ahsteellab.com/guest/chat');
        return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        if (!getSpeechRecognitionCtor()) {
            micBtn.disabled = true;
            setVoiceStatus('This browser cannot use the microphone. Please type.');
            return;
        }
    }
    micBtn.disabled = false;
    if (VOICE_CLOUD_ENABLED) {
        micBtn.title = 'Tap mic, speak, tap again to stop';
        setVoiceStatus('Tap mic → speak → tap STOP.');
    } else {
        micBtn.title = 'Tap mic and speak item name';
        setVoiceStatus('Tap mic and speak the item name.');
    }
}

function showVoiceConfirm(transcript) {
    const panel = document.getElementById('guest-voice-confirm');
    const input = document.getElementById('guest-voice-text');
    hideVoiceHud();
    input.value = transcript;
    panel.classList.remove('d-none');
    setVoiceStatus('Check the text, edit if wrong, then Send.');
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
}

function hideVoiceConfirm() {
    document.getElementById('guest-voice-confirm').classList.add('d-none');
    document.getElementById('guest-voice-text').value = '';
    if (VOICE_CLOUD_ENABLED) {
        setVoiceStatus('Tap mic → speak → tap STOP.');
    } else {
        setVoiceStatus('Tap mic and speak the item name.');
    }
}

function sendConfirmedVoice() {
    const raw = document.getElementById('guest-voice-text').value.trim();
    if (!raw) {
        setVoiceStatus('Nothing to send. Retry voice or type.');
        return;
    }
    hideVoiceConfirm();
    const ordering = !!document.querySelector('.guest-inline-cart')
        || !!document.querySelector('.guest-cart-line')
        || Array.from(document.querySelectorAll('[data-payload]')).some((el) =>
            ['CART', 'CONFIRM', 'NEW', 'CLEAR'].includes(
                (el.getAttribute('data-payload') || '').toUpperCase(),
            ));
    const isCommand = /^(?:\d+|menu|help|price|rate|delivery|store|order|buy|cart|confirm)\b/i
        .test(raw);
    const input = document.getElementById('guest-message');
    input.value = (!ordering && !isCommand) ? `price ${raw}` : raw;
    sendMessage(new Event('submit'));
}

async function startMediaRecording() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setVoiceStatus('Microphone API missing. Use Chrome and HTTPS.');
        return;
    }
    if (!window.MediaRecorder) {
        setVoiceStatus('Recording not supported. Please type the item.');
        return;
    }
    showVoiceHud('Allow microphone…');
    try {
        mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
            },
        });
    } catch (error) {
        hideVoiceHud();
        setMicActive(false);
        recording = false;
        const name = (error && error.name) || '';
        if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
            setVoiceStatus('Mic blocked. Chrome → Site settings → Microphone → Allow, reload.');
        } else if (name === 'NotFoundError') {
            setVoiceStatus('No microphone found on this phone.');
        } else {
            setVoiceStatus(`Mic open failed: ${name || (error && error.message) || 'error'}`);
        }
        return;
    }

    mediaChunks = [];
    const mime = pickRecorderMime();
    try {
        mediaRecorder = mime
            ? new MediaRecorder(mediaStream, { mimeType: mime })
            : new MediaRecorder(mediaStream);
    } catch (error) {
        releaseMediaStream();
        hideVoiceHud();
        setVoiceStatus('Could not start recorder. Please type.');
        return;
    }

    mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) mediaChunks.push(event.data);
    };
    mediaRecorder.onerror = () => {
        recording = false;
        setMicActive(false);
        hideVoiceHud();
        releaseMediaStream();
        setVoiceStatus('Recorder error. Tap mic and try again.');
    };
    mediaRecorder.onstop = () => {
        recording = false;
        setMicActive(false);
        const blobType = (mediaRecorder && mediaRecorder.mimeType) || mime || 'audio/webm';
        releaseMediaStream();
        mediaRecorder = null;
        uploadRecordedVoice(new Blob(mediaChunks, { type: blobType }));
        mediaChunks = [];
    };

    try {
        // timeslice helps Android deliver audio chunks reliably
        mediaRecorder.start(250);
    } catch (error) {
        try {
            mediaRecorder.start();
        } catch (retryErr) {
            releaseMediaStream();
            mediaRecorder = null;
            hideVoiceHud();
            setVoiceStatus('Recorder start failed. Please type.');
            return;
        }
    }
    recording = true;
    recordStartedAt = Date.now();
    setMicActive(true);
    showVoiceHud('Recording… speak item name (~2s), then tap STOP');
}

function stopMediaRecording() {
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        recording = false;
        setMicActive(false);
        releaseMediaStream();
        hideVoiceHud();
        return;
    }
    showVoiceHud('Processing voice…');
    try {
        if (typeof mediaRecorder.requestData === 'function') {
            mediaRecorder.requestData();
        }
    } catch (error) { /* ignore */ }
    try {
        mediaRecorder.stop();
    } catch (error) {
        recording = false;
        setMicActive(false);
        releaseMediaStream();
        hideVoiceHud();
        setVoiceStatus('Stop failed. Tap mic again.');
    }
}

function friendlyVoiceError(raw) {
    const msg = String(raw || '');
    if (/quota|rate.?limit|billing|credits are empty/i.test(msg)) {
        markVoiceCloudBlocked();
        return {
            note: 'Cloud voice unavailable. Using phone mic — speak now.',
            fallbackChrome: true,
        };
    }
    if (/API key rejected|GEMINI_API_KEY|not configured|AI is not configured/i.test(msg)) {
        markVoiceCloudBlocked();
        return {
            note: 'Cloud voice unavailable. Using phone mic — speak now.',
            fallbackChrome: true,
        };
    }
    if (/too short/i.test(msg)) {
        return {
            note: 'Hold mic 1–2 seconds and speak the item name, then STOP.',
            fallbackChrome: false,
        };
    }
    if (/No speech|No words/i.test(msg)) {
        return {
            note: 'No speech heard. Speak closer, then tap STOP.',
            fallbackChrome: false,
        };
    }
    return {
        note: msg || 'Voice failed. Tap mic to retry, or type the item.',
        fallbackChrome: false,
    };
}

async function uploadRecordedVoice(blob) {
    if (voiceBusy) return;
    if (!blob || !blob.size) {
        hideVoiceHud();
        setVoiceStatus('No audio captured. Hold mic longer and speak.');
        return;
    }
    const elapsed = recordStartedAt ? (Date.now() - recordStartedAt) : 0;
    if (elapsed > 0 && elapsed < 900) {
        hideVoiceHud();
        setVoiceStatus('Too short. Hold mic ~2 seconds, speak, then STOP.');
        return;
    }
    voiceBusy = true;
    showVoiceHud('Converting voice…');
    try {
        const form = new FormData();
        const ext = (blob.type || '').includes('mp4') ? 'm4a' : 'webm';
        form.append('file', blob, `voice.${ext}`);
        const mobile = formatLocalMobile(
            document.getElementById('guest-phone').value.trim(),
        );
        if (mobile) form.append('mobile', mobile);
        const lang = currentVoiceLang();
        const hint = encodeURIComponent(lang.hint || 'Urdu or English (Pakistan)');
        const { response, data } = await fetchJson(`${VOICE_TRANSCRIBE_API}?language_hint=${hint}`, {
            method: 'POST',
            body: form,
        }, 25000);
        if (!response.ok) {
            const detail = data.detail;
            const msg = typeof detail === 'string'
                ? detail
                : (detail && detail.message) || 'Voice convert failed.';
            throw new Error(msg);
        }
        const text = (data.text || '').trim();
        if (!text) throw new Error('No words detected. Speak clearly and retry.');
        clearVoiceCloudBlocked();
        hideVoiceHud();
        showVoiceConfirm(text);
        setVoiceStatus(`Heard: ${text}`);
    } catch (error) {
        voiceBusy = false;
        hideVoiceHud();
        const info = friendlyVoiceError(error && error.message);
        setVoiceStatus(info.note);
        // Only auto-switch to on-device speech when cloud voice is unavailable.
        if (info.fallbackChrome && getSpeechRecognitionCtor()) {
            window.setTimeout(() => startWebSpeech(), 250);
            return;
        }
    } finally {
        voiceBusy = false;
        recordStartedAt = 0;
    }
}

function startWebSpeech() {
    const SpeechRecognition = getSpeechRecognitionCtor();
    if (!SpeechRecognition) {
        setVoiceStatus('Chrome speech missing. Trying record mode…');
        startMediaRecording();
        return;
    }
    hideVoiceConfirm();
    try {
        recognition = new SpeechRecognition();
        recognition.lang = currentVoiceLang().code;
        bindRecognitionHandlers(recognition);
        recognition.start();
        setMicActive(true);
        showVoiceHud('Listening… speak item name now (free).');
    } catch (error) {
        listening = false;
        setMicActive(false);
        hideVoiceHud();
        const msg = (error && error.message) || String(error || '');
        setVoiceStatus(`Speech start failed: ${msg || 'unknown'}. Please type.`);
    }
}

function toggleVoice(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    setVoiceStatus('Starting mic…');

    if (!window.isSecureContext) {
        setVoiceStatus('Voice needs HTTPS. Open the secure site URL.');
        return;
    }
    if (sending || voiceBusy) {
        setVoiceStatus('Please wait — still working.');
        return;
    }
    if (recording) {
        stopMediaRecording();
        return;
    }
    if (listening && recognition) {
        try { recognition.stop(); } catch (error) { /* ignore */ }
        listening = false;
        setMicActive(false);
        hideVoiceHud();
        setVoiceStatus('Stopped.');
        return;
    }

    hideVoiceConfirm();
    const phoneForVoice = formatLocalMobile(
        document.getElementById('guest-phone').value.trim(),
    );
    if (!phoneForVoice) {
        setVoiceStatus('Enter your mobile number before using voice search.');
        showManualPhoneInput();
        return;
    }
    // If cloud voice is blocked, use on-device speech immediately.
    if (VOICE_CLOUD_ENABLED && !isVoiceCloudBlocked()) {
        startMediaRecording();
        return;
    }
    if (getSpeechRecognitionCtor()) {
        if (isVoiceCloudBlocked()) {
            showVoiceHud('Cloud voice unavailable — phone mic on. Speak now.');
        }
        startWebSpeech();
        return;
    }
    if (VOICE_CLOUD_ENABLED) {
        startMediaRecording();
        return;
    }
    setVoiceStatus('Voice not supported here. Please type the item name.');
}

function onQuickReplyClick(event) {
    if (event.target.closest('[data-shelf-add], [data-shelf-qty-minus], [data-shelf-qty-plus]')) {
        return;
    }
    const btn = event.target.closest('[data-payload]');
    if (!btn || sending) return;
    const payload = btn.getAttribute('data-payload') || '';
    if (!payload) return;
    if (payload === '__PHONE_HINT__') {
        choosePhoneNumber();
        return;
    }
    // Local qty adjust — no server call until user taps Confirm on that line.
    if (btn.hasAttribute('data-local-qty')) {
        adjustLocalCartQty(btn.closest('.guest-cart-line'), payload);
        return;
    }
    if (payload === 'CONFIRM') {
        const pending = document.querySelector(
            '.guest-cart-confirm:not(.d-none)',
        );
        if (pending) {
            document.getElementById('mic-status').textContent =
                'Tap Confirm on the changed item first, then Confirm order.';
            pending.classList.add('guest-cart-confirm-pulse');
            window.setTimeout(
                () => pending.classList.remove('guest-cart-confirm-pulse'),
                1200,
            );
            return;
        }
    }
    const input = document.getElementById('guest-message');
    input.value = payload;
    sendMessage(new Event('submit'));
}

function adjustLocalCartQty(card, action) {
    if (!card) return;
    const qtyEl = card.querySelector('.guest-cart-qty');
    const confirmBtn = card.querySelector('.guest-cart-confirm');
    const priceEl = card.querySelector('.guest-item-price');
    if (!qtyEl || !confirmBtn) return;
    let qty = Number(card.dataset.qty || qtyEl.textContent || 1);
    const saved = Number(card.dataset.savedQty || qty);
    const unit = Number(card.dataset.unitPrice || 0);
    if (action === 'local-dec') qty = Math.max(1, qty - 1);
    if (action === 'local-inc') qty = Math.min(9999, qty + 1);
    card.dataset.qty = String(qty);
    qtyEl.textContent = Number.isInteger(qty) ? String(qty) : qty.toFixed(2);
    if (priceEl && unit > 0) {
        const line = unit * qty;
        priceEl.textContent = `Rs ${Number.isInteger(line) ? line.toLocaleString() : line.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    const dirty = qty !== saved;
    confirmBtn.classList.toggle('d-none', !dirty);
    confirmBtn.disabled = !dirty;
    if (dirty) {
        confirmBtn.setAttribute('data-payload', `QTY ${card.dataset.lineIndex} ${qty}`);
    }
    refreshCartHeader();
    document.getElementById('mic-status').textContent = dirty
        ? 'Quantity changed — tap Confirm on that item to save.'
        : 'Tap − / + to change qty, then Confirm on the item.';
}

function refreshCartHeader() {
    const label = document.querySelector('.guest-inline-cart .guest-select-label');
    const lines = document.querySelectorAll('.guest-inline-cart .guest-cart-line');
    if (!label || !lines.length) return;
    let qtyTotal = 0;
    lines.forEach((line) => {
        qtyTotal += Number(line.dataset.qty || 0);
    });
    const qtyLabel = Number.isInteger(qtyTotal) ? String(qtyTotal) : qtyTotal.toFixed(2);
    label.textContent = `Your cart · ${lines.length} item(s) · Qty ${qtyLabel}`;
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

    // OTP first: typing a mobile and tapping Send must request OTP even with no chat text.
    if (otpRequired && !phoneVerified) {
        if (!isCompleteLocalMobile(phoneInput.value)) {
            showManualPhoneInput();
            document.getElementById('mic-status').textContent =
                'Type your mobile 03XXXXXXXXX, then tap Send for OTP.';
            appendBubble(
                'out',
                'Please type your mobile number, then we will send the OTP.',
                'bot',
            );
            return;
        }
        pendingMessageAfterVerify = message;
        input.value = '';
        await sendMobileOtp(false);
        return;
    }

    if (!message) return;

    // Collect mobile first if missing.
    if (!formatLocalMobile(phoneInput.value)) {
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

    // Web chat OTP authentication (skipped when backend OTP is disabled).
    if (otpRequired && !phoneVerified) {
        pendingMessageAfterVerify = message;
        input.value = '';
        appendBubble(
            'out',
            'Authenticate your mobile with OTP before chatting on web.',
            'bot',
        );
        await sendMobileOtp(false);
        return;
    }

    sending = true;
    saveProfileFields();
    const isShelfAdd = /^ADDITEM\s/i.test(message);
    if (!isShelfAdd) {
        clearInlineSelection();
    }
    const hideEcho = (/^MENU$/i.test(message) && !conversationId) || isShelfAdd;
    if (!hideEcho) {
        const label = geo ? `[location] ${geo.latitude.toFixed(5)}, ${geo.longitude.toFixed(5)}` : message;
        appendBubble('in', label, nameInput.value.trim() || 'You');
    }
    input.value = '';
    input.disabled = true;
    if (!isShelfAdd) {
        setQuickRepliesEnabled(false);
    }
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
        const { response, data } = await fetchJson(GUEST_CHAT_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        }, 25000);
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
        window.GUEST_SHOP_CATEGORY_ID = data.shop_category_id || null;
        window.GUEST_SHOP_CATEGORY_TITLE = data.shop_category_title || '';
        window.GUEST_SHOP_VIEW = data.shop_view || '';
        updateCartSticky(data.cart_count || 0, data.cart_total || 0);
        if ((data.cart_count || 0) <= 0) {
            shelfAddedManualIds.clear();
            lastShelfAddedManualId = '';
        }
        const replies = Array.isArray(data.quick_replies) && data.quick_replies.length
            ? ensureMainMenuChips(data.quick_replies)
            : MAIN_MENU;
        const isStayInShop = !!data.stay_in_shop;
        const isCartUi = !isStayInShop
            && replies.some((item) => (item.style || '') === 'cart');
        const replyText = (data.reply || '').trim();
        if (isStayInShop) {
            if (data.added_manual_id) {
                const id = String(data.added_manual_id);
                shelfAddedManualIds.add(id);
                lastShelfAddedManualId = id;
            }
            renderQuickReplies(replies);
            applyInputPrompt(
                data.input_placeholder,
                data.input_hint || 'Use − / + and ADD — added items stay highlighted.',
                replies,
            );
            highlightShelfAddedRow();
        } else if (isCartUi && !replyText) {
            renderQuickReplies(replies);
            applyInputPrompt(
                data.input_placeholder,
                data.input_hint || 'Cart updated. Change qty with − / +, then Confirm on the item.',
                replies,
            );
        } else if (isCartUi) {
            // First open / add-to-cart: one short summary only (never full receipt).
            appendBubble('out', replyText, 'bot');
            renderQuickReplies(replies);
            applyInputPrompt(data.input_placeholder, data.input_hint, replies);
        } else {
            appendBubble('out', data.reply, 'bot');
            renderQuickReplies(replies);
            applyInputPrompt(data.input_placeholder, data.input_hint, replies);
        }
    } catch (error) {
        appendBubble('out', error.message || 'Could not send message.', 'system');
        renderQuickReplies(MAIN_MENU);
        applyInputPrompt('', '', MAIN_MENU);
    } finally {
        sending = false;
        input.disabled = false;
        input.focus();
        setQuickRepliesEnabled(true);
    }
}

function highlightShelfAddedRow() {
    if (!lastShelfAddedManualId) return;
    const row = document.querySelector(
        `.guest-shelf-product[data-manual-id="${lastShelfAddedManualId}"]`,
    );
    if (row) {
        row.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        row.classList.add('guest-shelf-product-just-added');
    }
    const pulseId = lastShelfAddedManualId;
    window.setTimeout(() => {
        document.querySelectorAll('.guest-shelf-product-just-added').forEach((el) => {
            el.classList.remove('guest-shelf-product-just-added');
        });
        if (lastShelfAddedManualId === pulseId) {
            lastShelfAddedManualId = '';
        }
    }, 1400);
}

function isHiddenShopTitle(title) {
    const text = String(title || '').trim().toLowerCase();
    return text === 'empty' || text.startsWith('empty');
}

function formatCartMoney(amount) {
    const n = Number(amount) || 0;
    return `Rs ${Math.round(n).toLocaleString('en-PK')}`;
}

function updateCartSticky(count, total) {
    const bar = document.getElementById('guest-cart-sticky');
    if (!bar) return;
    const n = Number(count) || 0;
    if (n <= 0) {
        bar.classList.add('d-none');
        return;
    }
    bar.classList.remove('d-none');
    const countEl = bar.querySelector('.guest-cart-sticky-count');
    const totalEl = bar.querySelector('.guest-cart-sticky-total');
    if (countEl) {
        countEl.textContent = `${n} item${n === 1 ? '' : 's'}`;
    }
    if (totalEl) {
        totalEl.textContent = formatCartMoney(total);
    }
}

function ensureMainMenuChips(items) {
    const rows = Array.isArray(items) ? items.slice() : [];
    const hasItems = rows.some((item) => ['item', 'cart'].includes(item.style || 'chip'));
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

function applyInputPrompt(placeholder, hint, replies) {
    const input = document.getElementById('guest-message');
    const subtitle = document.getElementById('guest-subtitle');
    const status = document.getElementById('mic-status');
    const rows = replies || [];
    const payloads = new Set(rows.map((item) => String(item.payload || '').trim().toUpperCase()));
    const hasItems = rows.some((item) => (item.style || '') === 'item');
    const hasCart = rows.some((item) => (item.style || '') === 'cart');
    const looksLikeMainMenu = ['1', '2', '3', '4', '5'].every((p) => payloads.has(p));

    let nextPlaceholder = (placeholder || '').trim();
    let nextHint = (hint || '').trim();

    if (!nextPlaceholder) {
        if (hasCart) {
            nextPlaceholder = 'Change qty below, or type item name to add…';
        } else if (hasItems) {
            nextPlaceholder = 'Set qty and tap ADD on a product, or search…';
        } else if (payloads.has('KEEP') || payloads.has('UPDATE')) {
            nextPlaceholder = 'Tap Keep / Update / Skip, or type address…';
        } else if (looksLikeMainMenu) {
            nextPlaceholder = 'Tap a menu option, or type 1–6…';
        } else if (rows.some((r) => /^Qty\s/i.test(r.title || ''))) {
            nextPlaceholder = 'Type quantity e.g. 1 or 2…';
        } else {
            nextPlaceholder = 'Type brand/item e.g. Dalda…';
        }
    }
    if (!nextHint) {
        if (hasCart) nextHint = 'Your cart — confirm qty, then Confirm order';
        else if (hasItems) nextHint = 'Use − / + and ADD — you stay on this list';
        else if (looksLikeMainMenu) nextHint = 'Main menu — Delivery · Price · Order · My order';
        else nextHint = 'Type your reply, or tap a button';
    }

    if (input) input.placeholder = nextPlaceholder;
    if (subtitle) subtitle.textContent = nextHint;
    // Don't overwrite live mic / GPS status lines.
    if (status) {
        const current = status.textContent || '';
        if (!/^(Listening|Hearing|Starting|Opening|Collecting|Mobile selected|Location)/i.test(current)) {
            status.textContent = nextHint;
        }
    }
}

function renderQuickReplies(items) {
    const box = document.getElementById('guest-quick-replies');
    box.innerHTML = '';
    box.classList.remove('is-selection');
    const rows = ensureMainMenuChips(items || []);
    const cartRows = rows.filter((item) => (item.style || 'chip') === 'cart');
    const itemRows = rows.filter((item) => (item.style || 'chip') === 'item');
    const actionRows = rows.filter(
        (item) => !['item', 'cart'].includes(item.style || 'chip'),
    );
    const subChips = actionRows.filter((item) => /^CAT\s/i.test(String(item.payload || '')));
    const otherActions = actionRows.filter((item) => !/^CAT\s/i.test(String(item.payload || '')));
    const shopNavChips = otherActions.filter((item) =>
        /^(CATEGORIES|BACK|CART|MORE|CLEAR SEARCH)$/i.test(String(item.payload || '')),
    );
    const otherActionsRest = otherActions.filter((item) =>
        !/^(CATEGORIES|BACK|CART|MORE|CLEAR SEARCH)$/i.test(String(item.payload || '')),
    );
    const categoryList = itemRows.length > 0
        && itemRows.every((item) => /^CAT\s/i.test(String(item.payload || '')));
    const visibleItemRows = categoryList
        ? itemRows.filter((item) => !isHiddenShopTitle(item.title))
        : itemRows.filter((item) => !isHiddenShopTitle(item.title));

    if (cartRows.length) {
        appendInlineCart(cartRows.filter((item) => !isHiddenShopTitle(item.title)));
    } else if (visibleItemRows.length || subChips.length) {
        appendShopShelf(visibleItemRows, subChips, categoryList);
    }

    const chipRow = document.createElement('div');
    chipRow.className = 'guest-chip-row';
    if (shopNavChips.length) {
        const navRow = document.createElement('div');
        navRow.className = 'guest-chip-row guest-shop-nav-row';
        shopNavChips.forEach((item) => navRow.appendChild(buildChip(item)));
        box.appendChild(navRow);
    }
    (otherActionsRest.length ? otherActionsRest : (!itemRows.length && !cartRows.length && !subChips.length ? rows : [])).forEach((item) => {
        if (['item', 'cart'].includes(item.style || 'chip')) return;
        if (/^CAT\s/i.test(String(item.payload || ''))) return;
        chipRow.appendChild(buildChip(item));
    });
    if (!otherActionsRest.length && !itemRows.length && !cartRows.length && !subChips.length && !shopNavChips.length) {
        MAIN_MENU.forEach((item) => chipRow.appendChild(buildChip(item)));
    }
    if (chipRow.childNodes.length) box.appendChild(chipRow);
    applyInputPrompt('', '', rows);
}

function clearInlineSelection() {
    document.querySelectorAll('#guest-messages .guest-inline-select').forEach((el) => {
        el.remove();
    });
}

function appendShopShelf(itemRows, subChips, categoryList) {
    clearInlineSelection();
    const box = document.getElementById('guest-messages');
    const panel = document.createElement('div');
    panel.className = 'guest-inline-select guest-shop-shelf';
    if (subChips && subChips.length) {
        const subLabel = document.createElement('div');
        subLabel.className = 'guest-select-label dark';
        subLabel.textContent = 'Shop by subcategory';
        panel.appendChild(subLabel);
        const subRow = document.createElement('div');
        subRow.className = 'guest-chip-row guest-subcat-row';
        subChips.forEach((item) => subRow.appendChild(buildChip({ ...item, style: 'chip' })));
        panel.appendChild(subRow);
    }
    if (itemRows && itemRows.length) {
        const label = document.createElement('div');
        label.className = 'guest-select-label dark';
        label.textContent = categoryList ? 'Shop by category — tap to open' : 'Products — set qty and tap ADD';
        panel.appendChild(label);
        const list = document.createElement('div');
        list.className = 'guest-select-list';
        itemRows.forEach((item, idx) => {
            const row = buildProductShelfRow(item, idx);
            list.appendChild(row);
            if (row.dataset.shelfProduct === '1') {
                wireShelfProductRow(row, item);
            }
        });
        panel.appendChild(list);
    }
    box.appendChild(panel);
    box.scrollTop = box.scrollHeight;
}

function appendInlineSelection(itemRows, labelText) {
    appendShopShelf(itemRows, [], labelText === 'Shop by category — tap to open');
}

function appendInlineCart(cartRows) {
    clearInlineSelection();
    const box = document.getElementById('guest-messages');
    const panel = document.createElement('div');
    panel.className = 'guest-inline-select guest-inline-cart';
    const label = document.createElement('div');
    label.className = 'guest-select-label dark';
    const qtyTotal = cartRows.reduce((sum, item) => sum + (Number(item.qty) || 0), 0);
    const qtyLabel = Number.isInteger(qtyTotal) ? String(qtyTotal) : qtyTotal.toFixed(2);
    label.textContent = `Your cart · ${cartRows.length} item(s) · Qty ${qtyLabel}`;
    panel.appendChild(label);
    const list = document.createElement('div');
    list.className = 'guest-select-list';
    cartRows.forEach((item) => list.appendChild(buildCartLine(item)));
    panel.appendChild(list);
    box.appendChild(panel);
    box.scrollTop = box.scrollHeight;
}

function buildCartLine(item) {
    const idx = item.line_index || parseInt(item.payload, 10) || 1;
    const qty = item.qty == null ? 1 : Number(item.qty);
    const unitPrice = Number(item.unit_price || 0);
    const card = document.createElement('div');
    card.className = 'guest-cart-line';
    card.dataset.lineIndex = String(idx);
    card.dataset.qty = String(qty);
    card.dataset.savedQty = String(qty);
    card.dataset.unitPrice = String(unitPrice);

    const head = document.createElement('div');
    head.className = 'guest-cart-head';
    const num = document.createElement('span');
    num.className = 'guest-item-num';
    num.textContent = String(idx);
    const body = document.createElement('div');
    body.className = 'guest-item-body';
    const title = document.createElement('span');
    title.className = 'guest-item-title';
    title.textContent = item.title || `Item ${idx}`;
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
    head.appendChild(num);
    head.appendChild(body);
    head.appendChild(price);
    card.appendChild(head);

    const controls = document.createElement('div');
    controls.className = 'guest-cart-controls';

    const dec = document.createElement('button');
    dec.type = 'button';
    dec.className = 'guest-cart-btn guest-cart-dec';
    dec.setAttribute('data-payload', 'local-dec');
    dec.setAttribute('data-local-qty', '1');
    dec.setAttribute('aria-label', 'Decrease quantity');
    dec.innerHTML = '<i class="bi bi-dash-lg"></i>';

    const qtyBox = document.createElement('span');
    qtyBox.className = 'guest-cart-qty';
    qtyBox.textContent = Number.isInteger(qty) ? String(qty) : qty.toFixed(2);

    const inc = document.createElement('button');
    inc.type = 'button';
    inc.className = 'guest-cart-btn guest-cart-inc';
    inc.setAttribute('data-payload', 'local-inc');
    inc.setAttribute('data-local-qty', '1');
    inc.setAttribute('aria-label', 'Increase quantity');
    inc.innerHTML = '<i class="bi bi-plus-lg"></i>';

    const confirmQty = document.createElement('button');
    confirmQty.type = 'button';
    confirmQty.className = 'guest-cart-btn guest-cart-confirm d-none';
    confirmQty.setAttribute('data-payload', `QTY ${idx} ${qty}`);
    confirmQty.innerHTML = '<i class="bi bi-check2"></i> Confirm';

    const del = document.createElement('button');
    del.type = 'button';
    del.className = 'guest-cart-btn guest-cart-del';
    del.setAttribute('data-payload', `REMOVE ${idx}`);
    del.setAttribute('aria-label', 'Delete item');
    del.innerHTML = '<i class="bi bi-trash"></i>';

    controls.appendChild(dec);
    controls.appendChild(qtyBox);
    controls.appendChild(inc);
    controls.appendChild(confirmQty);
    controls.appendChild(del);
    card.appendChild(controls);
    return card;
}

function shelfQtyFor(manualId) {
    const key = String(manualId);
    if (!shelfQty[key] || shelfQty[key] < 1) shelfQty[key] = 1;
    return shelfQty[key];
}

function addShelfProduct(item, qty) {
    if (!item || !item.manual_id || sending) return;
    const useQty = Math.max(1, Number(qty) || 1);
    const input = document.getElementById('guest-message');
    input.value = `ADDITEM ${item.manual_id} ${useQty}`;
    sendMessage(new Event('submit'));
}

function buildProductShelfRow(item, index) {
    const isCategory = /^CAT\s/i.test(String(item.payload || ''));
    const manualId = Number(item.manual_id) || 0;
    if (isCategory || !manualId) {
        return buildItemChoice(item);
    }
    const card = document.createElement('div');
    card.className = 'guest-shelf-product';
    card.dataset.shelfProduct = '1';
    card.dataset.manualId = String(manualId);
    card.dataset.shelfIndex = String(index);
    if (shelfAddedManualIds.has(String(manualId))) {
        card.classList.add('guest-shelf-product-added');
    }

    const body = document.createElement('div');
    body.className = 'guest-shelf-product-body';
    const title = document.createElement('div');
    title.className = 'guest-shelf-title';
    title.textContent = item.title || `Item ${manualId}`;
    body.appendChild(title);
    if (shelfAddedManualIds.has(String(manualId))) {
        const badge = document.createElement('span');
        badge.className = 'guest-shelf-added-badge';
        badge.textContent = 'In cart';
        body.appendChild(badge);
    }
    if (item.subtitle) {
        const meta = document.createElement('div');
        meta.className = 'guest-shelf-meta';
        meta.textContent = item.subtitle;
        body.appendChild(meta);
    }

    const actions = document.createElement('div');
    actions.className = 'guest-shelf-actions';
    const price = document.createElement('div');
    price.className = 'guest-shelf-price';
    price.textContent = item.meta || '';
    actions.appendChild(price);

    const qtyWrap = document.createElement('div');
    qtyWrap.className = 'guest-shelf-qty';
    const dec = document.createElement('button');
    dec.type = 'button';
    dec.className = 'guest-shelf-qty-btn';
    dec.setAttribute('data-shelf-qty-minus', String(manualId));
    dec.setAttribute('aria-label', 'Decrease quantity');
    dec.textContent = '−';
    const qtyVal = document.createElement('span');
    qtyVal.className = 'guest-shelf-qty-val';
    qtyVal.setAttribute('data-shelf-qty-val', String(manualId));
    qtyVal.textContent = String(shelfQtyFor(manualId));
    const inc = document.createElement('button');
    inc.type = 'button';
    inc.className = 'guest-shelf-qty-btn';
    inc.setAttribute('data-shelf-qty-plus', String(manualId));
    inc.setAttribute('aria-label', 'Increase quantity');
    inc.textContent = '+';
    qtyWrap.appendChild(dec);
    qtyWrap.appendChild(qtyVal);
    qtyWrap.appendChild(inc);
    actions.appendChild(qtyWrap);

    const addBtn = document.createElement('button');
    addBtn.type = 'button';
    addBtn.className = 'guest-shelf-add';
    addBtn.setAttribute('data-shelf-add', String(manualId));
    addBtn.textContent = 'ADD';
    actions.appendChild(addBtn);

    card.appendChild(body);
    card.appendChild(actions);
    return card;
}

function wireShelfProductRow(card, item) {
    const manualId = Number(item.manual_id) || 0;
    if (!manualId) return;
    const addWithQty = () => addShelfProduct(item, shelfQtyFor(manualId));
    card.querySelector('[data-shelf-add]')?.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopPropagation();
        addWithQty();
    });
    card.querySelector('[data-shelf-qty-minus]')?.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopPropagation();
        shelfQty[String(manualId)] = Math.max(1, shelfQtyFor(manualId) - 1);
        const label = card.querySelector(`[data-shelf-qty-val="${manualId}"]`);
        if (label) label.textContent = String(shelfQty[String(manualId)]);
    });
    card.querySelector('[data-shelf-qty-plus]')?.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopPropagation();
        shelfQty[String(manualId)] = shelfQtyFor(manualId) + 1;
        const label = card.querySelector(`[data-shelf-qty-val="${manualId}"]`);
        if (label) label.textContent = String(shelfQty[String(manualId)]);
    });
    card.querySelector('.guest-shelf-product-body')?.addEventListener('click', (event) => {
        if (event.target.closest('[data-shelf-add], [data-shelf-qty-minus], [data-shelf-qty-plus]')) {
            return;
        }
        addWithQty();
    });
}

function buildItemChoice(item) {
    const btn = document.createElement('button');
    btn.type = 'button';
    const isCategory = /^CAT\s/i.test(String(item.payload || ''));
    btn.className = isCategory ? 'guest-item-choice guest-category-choice' : 'guest-item-choice';
    btn.setAttribute('data-payload', item.payload);
    const num = document.createElement('span');
    num.className = 'guest-item-num';
    num.textContent = isCategory ? '▦' : String(item.payload || '');
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
