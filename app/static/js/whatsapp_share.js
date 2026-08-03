/**
 * Free WhatsApp sharing — Plan A (wa.me link) and Plan B (Web Share PDF file).
 */

const WhatsAppShare = {
    isMobile() {
        return /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent || '');
    },

    /**
     * Normalize Pakistani numbers to 92XXXXXXXXXX.
     * Accepts: 03001234567, 3001234567, 923001234567, +92 300 1234567
     */
    normalizePkPhone(raw) {
        let digits = String(raw || '').replace(/\D/g, '');
        if (!digits) return '';

        if (digits.startsWith('00')) {
            digits = digits.slice(2);
        }
        if (digits.startsWith('92')) {
            // already international
        } else if (digits.startsWith('0')) {
            digits = `92${digits.slice(1)}`;
        } else {
            digits = `92${digits}`;
        }

        // Pakistan mobile: 92 + 10 digits (3XX XXXXXXX)
        if (!digits.startsWith('92') || digits.length < 12 || digits.length > 13) {
            return '';
        }
        return digits;
    },

    buildUrl(phoneDigits, message) {
        const phone = this.normalizePkPhone(phoneDigits);
        if (!phone) {
            throw new Error('Enter a valid WhatsApp number (e.g. 3001234567 or 03001234567).');
        }
        const text = encodeURIComponent(message);
        return `https://api.whatsapp.com/send?phone=${phone}&text=${text}`;
    },

    openChat(phoneDigits, message) {
        const url = this.buildUrl(phoneDigits, message);
        // Mobile: direct navigation (popup blockers break window.open)
        if (this.isMobile()) {
            window.location.href = url;
        } else {
            const popup = window.open(url, '_blank', 'noopener,noreferrer');
            if (!popup) {
                window.location.href = url;
            }
        }
        return url;
    },

    buildLedgerMessage({
        appName,
        dateFrom,
        dateTo,
        accountLabel,
        viewUrl,
        expiresMinutes = 15,
        reportTitle = 'GL Ledger Report',
    }) {
        const lines = [
            appName || 'ERP Report',
            reportTitle,
            `Period: ${dateFrom} to ${dateTo}`,
        ];
        if (accountLabel) {
            lines.push(`Accounts: ${accountLabel}`);
        }
        lines.push(
            '',
            `PDF link (valid ${expiresMinutes} min):`,
            viewUrl,
        );
        return lines.join('\n');
    },

    canAttemptFileShare() {
        return typeof navigator !== 'undefined' && typeof navigator.share === 'function';
    },

    async sharePdfBlob(blob, filename, { title = 'GL Ledger Report' } = {}) {
        if (!this.canAttemptFileShare()) {
            throw new Error('PDF file share is not supported on this browser. Use Plan A.');
        }
        if (!blob || blob.size === 0) {
            throw new Error('PDF is not ready. Generate the report again.');
        }

        const file = new File([blob], filename || 'gl-ledger.pdf', {
            type: blob.type || 'application/pdf',
        });

        const filePayload = { files: [file] };
        if (navigator.canShare && navigator.canShare(filePayload)) {
            await navigator.share(filePayload);
            return;
        }

        const titledPayload = { title, files: [file] };
        if (navigator.canShare && navigator.canShare(titledPayload)) {
            await navigator.share(titledPayload);
            return;
        }

        // Some mobile browsers omit canShare but still support file share
        if (this.isMobile()) {
            await navigator.share({ files: [file] });
            return;
        }

        throw new Error('This device cannot share PDF files. Use Plan A (WhatsApp link).');
    },

    async fetchPdfBlob(url) {
        const response = await fetch(url, {
            credentials: 'include',
            cache: 'no-store',
        });
        if (!response.ok) {
            throw new Error(`Could not load PDF (${response.status}). Generate again.`);
        }
        const blob = await response.blob();
        if (!blob || blob.size === 0) {
            throw new Error('PDF file is empty. Generate again.');
        }
        return blob;
    },

    savePhonePreference(key, phone) {
        try {
            const normalized = this.normalizePkPhone(phone);
            if (normalized) {
                localStorage.setItem(key, phone.trim());
            }
        } catch {
            /* ignore */
        }
    },

    loadPhonePreference(key) {
        try {
            return localStorage.getItem(key) || '';
        } catch {
            return '';
        }
    },
};
