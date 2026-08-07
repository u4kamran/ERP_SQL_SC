const DELIVERY_REGISTRATION_API = '/api/v1/delivery/registration';

let qrScanner = null;
let scannerRunning = false;
let selectedInvoice = null;
let customerLookupMobile = '';

document.addEventListener('DOMContentLoaded', async () => {
    const profile = await Auth.requireAuth();
    if (!profile) return;
    if (!Auth.hasPermission('delivery.orders.update')) {
        Auth.showAlert(
            'registration-alert',
            'You do not have permission to register invoices for delivery.',
            'warning',
        );
        return;
    }

    document.getElementById('btn-start-scan').addEventListener('click', startScanner);
    document.getElementById('btn-stop-scan').addEventListener('click', stopScanner);
    document.getElementById('btn-search-invoice').addEventListener('click', searchInvoices);
    document.getElementById('btn-lookup-customer').addEventListener('click', lookupCustomer);
    document.getElementById('registration-form').addEventListener('submit', registerDelivery);
    document.getElementById('btn-clear-registration').addEventListener('click', clearRegistration);
    document.getElementById('customer-mobile').addEventListener('blur', normalizeMobileField);
    document.getElementById('gp-time').addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            searchInvoices();
        }
    });
});

window.addEventListener('beforeunload', () => {
    if (scannerRunning && qrScanner) qrScanner.stop().catch(() => {});
});

async function startScanner() {
    if (!window.isSecureContext) {
        showRegistrationError('The QR camera requires HTTPS.');
        return;
    }
    if (typeof Html5Qrcode === 'undefined') {
        showRegistrationError('QR scanner could not load. Enter GP_TIME manually.');
        return;
    }

    const startButton = document.getElementById('btn-start-scan');
    startButton.disabled = true;
    try {
        qrScanner = qrScanner || new Html5Qrcode('qr-reader');
        await qrScanner.start(
            { facingMode: 'environment' },
            { fps: 10, qrbox: { width: 240, height: 240 } },
            async (decodedText) => {
                const value = String(decodedText || '').trim();
                if (!value) return;
                document.getElementById('gp-time').value = value;
                await stopScanner();
                await searchInvoices();
            },
            () => {},
        );
        scannerRunning = true;
        document.getElementById('btn-stop-scan').classList.remove('d-none');
    } catch (error) {
        showRegistrationError(
            cameraErrorMessage(error),
        );
    } finally {
        startButton.disabled = false;
    }
}

async function stopScanner() {
    if (scannerRunning && qrScanner) {
        try {
            await qrScanner.stop();
        } catch {
            // Scanner may already be stopping after a successful decode.
        }
    }
    scannerRunning = false;
    document.getElementById('btn-stop-scan').classList.add('d-none');
}

async function searchInvoices() {
    const gpTime = document.getElementById('gp-time').value.trim();
    if (!gpTime) {
        showRegistrationError('Scan or enter a GP_TIME value first.');
        return;
    }

    const body = document.getElementById('invoice-results');
    body.innerHTML = '<tr><td colspan="5" class="text-center py-4">Searching…</td></tr>';
    try {
        const invoices = await Api.get(
            `${DELIVERY_REGISTRATION_API}/invoices?gp_time=${encodeURIComponent(gpTime)}`,
        );
        if (!invoices.length) {
            body.innerHTML = '<tr><td colspan="5" class="text-center text-warning py-4">No invoice found for this GP_TIME.</td></tr>';
            return;
        }
        body.innerHTML = invoices.map((invoice) => `
            <tr>
                <td class="fw-semibold">${esc(invoice.invoice_id)}</td>
                <td class="text-nowrap">${formatDate(invoice.invoice_date)}</td>
                <td>${esc(invoice.customer_title || 'Cash Sale')}</td>
                <td class="text-end text-nowrap">${formatMoney(invoice.total_amount)}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-primary invoice-select"
                            data-serial="${invoice.source_serial_no}" type="button">
                        Select
                    </button>
                </td>
            </tr>
        `).join('');
        body.querySelectorAll('[data-serial]').forEach((button) => {
            button.addEventListener('click', () => {
                const invoice = invoices.find(
                    (item) => item.source_serial_no === Number(button.dataset.serial),
                );
                selectInvoice(invoice);
            });
        });
    } catch (error) {
        body.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-4">${esc(error.message)}</td></tr>`;
    }
}

async function selectInvoice(invoice) {
    if (!invoice) return;
    selectedInvoice = invoice;
    customerLookupMobile = '';
    document.getElementById('source-serial-no').value = invoice.source_serial_no;
    document.getElementById('customer-mobile').value =
        invoice.current_mobile && invoice.current_mobile !== '.'
            ? normalizePakistanMobile(invoice.current_mobile)
            : '+92';
    document.getElementById('customer-name').value = invoice.customer_title || '';
    document.getElementById('customer-address').value = invoice.address || '';
    setCustomerFieldsReadonly(false);
    setCustomerState('', '');
    document.getElementById('selected-invoice').textContent =
        `Invoice ${invoice.invoice_id} · ${formatDate(invoice.invoice_date)} · ${formatMoney(invoice.total_amount)}`;
    const card = document.getElementById('registration-card');
    card.classList.remove('d-none');
    card.scrollIntoView({ behavior: 'smooth', block: 'start' });

    if (
        document.getElementById('customer-mobile').value.replace(/\D/g, '').length >= 10
    ) {
        await lookupCustomer();
    } else {
        document.getElementById('customer-mobile').focus();
    }
}

async function lookupCustomer() {
    const mobile = normalizeMobileField();
    if (mobile.length < 7) {
        setCustomerState('Enter a proper mobile number.', 'warning');
        return false;
    }
    try {
        const customer = await Api.get(
            `${DELIVERY_REGISTRATION_API}/customer?mobile=${encodeURIComponent(mobile)}`,
        );
        customerLookupMobile = mobile;
        if (customer.exists) {
            document.getElementById('customer-name').value = customer.name || '';
            document.getElementById('customer-address').value = customer.address || '';
            setCustomerFieldsReadonly(true);
            setCustomerState(
                `Existing CUST_SMS customer #${customer.cust_sms_id} found. Existing name and address will be reused.`,
                'success',
            );
        } else {
            setCustomerFieldsReadonly(false);
            setCustomerState(
                'New customer. Enter the name and address; a CUST_SMS record will be created.',
                'info',
            );
        }
        return customer.exists;
    } catch (error) {
        setCustomerState(error.message, 'danger');
        return false;
    }
}

async function registerDelivery(event) {
    event.preventDefault();
    if (!selectedInvoice) {
        showRegistrationError('Select an invoice first.');
        return;
    }

    const mobile = normalizeMobileField();
    const name = document.getElementById('customer-name').value.trim();
    const address = document.getElementById('customer-address').value.trim();
    if (!mobile || !name || !address) {
        setCustomerState('Mobile, customer name, and address are required.', 'danger');
        return;
    }
    if (customerLookupMobile !== mobile) {
        await lookupCustomer();
    }

    const button = document.getElementById('btn-register-delivery');
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Registering…';
    try {
        const result = await Api.post(DELIVERY_REGISTRATION_API, {
            source_serial_no: selectedInvoice.source_serial_no,
            mobile,
            name: document.getElementById('customer-name').value.trim(),
            address: document.getElementById('customer-address').value.trim(),
        });
        Auth.showAlert(
            'registration-alert',
            `${result.message} Invoice ${result.invoice_id}, delivery order #${result.delivery_order_id}.`,
            'success',
        );
        clearRegistration();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error) {
        setCustomerState(error.message, 'danger');
    } finally {
        button.disabled = false;
        button.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Register for Delivery';
    }
}

function clearRegistration() {
    selectedInvoice = null;
    customerLookupMobile = '';
    document.getElementById('registration-form').reset();
    document.getElementById('customer-mobile').value = '+92';
    document.getElementById('source-serial-no').value = '';
    document.getElementById('registration-card').classList.add('d-none');
    setCustomerFieldsReadonly(false);
    setCustomerState('', '');
}

function setCustomerFieldsReadonly(readonly) {
    document.getElementById('customer-name').readOnly = readonly;
    document.getElementById('customer-address').readOnly = readonly;
}

function setCustomerState(message, type) {
    const state = document.getElementById('customer-state');
    if (!message) {
        state.textContent = '';
        state.className = 'alert d-none';
        return;
    }
    state.textContent = message;
    state.className = `alert alert-${type}`;
}

function showRegistrationError(message) {
    Auth.showAlert('registration-alert', message, 'danger');
}

function cameraErrorMessage(error) {
    const text = String(error?.message || error || '');
    if (/permission|denied|notallowed/i.test(text)) {
        return 'Camera permission was denied. Allow Camera for this browser, then retry.';
    }
    return `Could not start QR camera. Enter GP_TIME manually. ${text}`;
}

function normalizeMobileField() {
    const input = document.getElementById('customer-mobile');
    const mobile = normalizePakistanMobile(input.value);
    input.value = mobile;
    return mobile;
}

function normalizePakistanMobile(value) {
    let digits = String(value || '').replace(/\D/g, '');
    if (!digits) return '+92';
    if (digits.startsWith('0092')) digits = digits.slice(2);
    if (digits.startsWith('92')) return `+${digits}`;
    if (digits.startsWith('0')) digits = digits.slice(1);
    return `+92${digits}`;
}

function formatDate(value) {
    if (!value) return '—';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
}

function formatMoney(value) {
    return new Intl.NumberFormat('en-PK', {
        style: 'currency',
        currency: 'PKR',
        maximumFractionDigits: 0,
    }).format(Number(value || 0));
}

function esc(value) {
    const element = document.createElement('div');
    element.textContent = value == null ? '' : String(value);
    return element.innerHTML;
}
