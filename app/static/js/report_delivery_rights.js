/** Report delivery rights helpers — each report has its own Email / WhatsApp permission. */

window.ReportDeliveryRights = (() => {
    function hasAny(codes) {
        return (codes || []).some((code) => Auth.hasPermission(code));
    }

    function canEmail(codes) {
        return hasAny(codes);
    }

    function canWhatsApp(codes) {
        return hasAny(codes);
    }

    // Convenience aliases used by pages
    function canEmailGl() {
        return canEmail(['reports.gl_ledger.email']);
    }

    function canWhatsAppGl() {
        return canWhatsApp(['reports.gl_ledger.whatsapp']);
    }

    function canEmailGlDetailed() {
        return canEmail(['reports.gl_ledger_detailed.email']);
    }

    function canWhatsAppGlDetailed() {
        return canWhatsApp(['reports.gl_ledger_detailed.whatsapp']);
    }

    function canEmailGlMobile() {
        return canEmail(['reports.gl_ledger_mobile.email']);
    }

    function canWhatsAppGlMobile() {
        return canWhatsApp(['reports.gl_ledger_mobile.whatsapp']);
    }

    function canEmailCredit() {
        return canEmail(['reports.gl_credit_summary.email']);
    }

    function canEmailTrial() {
        return canEmail(['reports.trial_balance_d2d.email']);
    }

    function canWhatsAppTrial() {
        return canWhatsApp(['reports.trial_balance_d2d.whatsapp']);
    }

    function canEmailTrialMobile() {
        return canEmail(['reports.trial_balance_d2d_mobile.email']);
    }

    function canWhatsAppTrialMobile() {
        return canWhatsApp(['reports.trial_balance_d2d_mobile.whatsapp']);
    }

    function canEmailStock() {
        return canEmail(['reports.stock_balance_d2d.email']);
    }

    function canEmailSales() {
        return canEmail(['reports.sales_dashboard.email']);
    }

    function _setDisabled(root, disabled) {
        if (!root) return;
        root.querySelectorAll('input, textarea, button, select').forEach((el) => {
            el.disabled = !!disabled;
        });
    }

    function applyEmailGate({ fieldsetId = 'email-fieldset', hintId = 'email-smtp-hint', allowed } = {}) {
        const fieldset = document.getElementById(fieldsetId);
        const hint = document.getElementById(hintId);
        if (!fieldset) return !!allowed;
        if (allowed) return true;

        _setDisabled(fieldset, true);
        if (hint) {
            hint.classList.remove('d-none');
            hint.className = 'alert alert-secondary py-2 small';
            hint.innerHTML = '<strong>Email</strong> — Not permitted for your role.';
        }
        return false;
    }

    function applyWhatsAppGate({
        fieldsetId = 'whatsapp-fieldset',
        hintId = 'whatsapp-config-hint',
        allowed,
    } = {}) {
        const fieldset = document.getElementById(fieldsetId);
        const hint = document.getElementById(hintId);
        if (!fieldset) return !!allowed;
        if (allowed) return true;

        _setDisabled(fieldset, true);
        if (hint) {
            hint.classList.remove('d-none');
            hint.className = 'alert alert-secondary py-2 small mb-2';
            hint.innerHTML = '<strong>WhatsApp</strong> — Not permitted for your role.';
        }
        return false;
    }

    function applySalesEmailGate({ sectionId = 'sales-email-panel', allowed } = {}) {
        const section = document.getElementById(sectionId);
        if (!section) return !!allowed;
        if (allowed) return true;

        section.querySelectorAll('input, textarea, button, select').forEach((el) => {
            el.disabled = true;
        });
        let note = section.querySelector('[data-delivery-denied]');
        if (!note) {
            note = document.createElement('div');
            note.className = 'alert alert-secondary py-2 small';
            note.setAttribute('data-delivery-denied', '1');
            note.innerHTML = '<strong>Email</strong> — Not permitted for your role.';
            section.prepend(note);
        }
        return false;
    }

    return {
        hasAny,
        canEmail,
        canWhatsApp,
        canEmailGl,
        canWhatsAppGl,
        canEmailGlDetailed,
        canWhatsAppGlDetailed,
        canEmailGlMobile,
        canWhatsAppGlMobile,
        canEmailCredit,
        canEmailTrial,
        canWhatsAppTrial,
        canEmailTrialMobile,
        canWhatsAppTrialMobile,
        canEmailStock,
        canEmailSales,
        applyEmailGate,
        applyWhatsAppGate,
        applySalesEmailGate,
    };
})();
