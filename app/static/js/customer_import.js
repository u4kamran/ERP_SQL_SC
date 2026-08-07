const CUSTOMER_IMPORT_API = '/api/v1/marketing/customer-import';
const IMPORT_STORAGE_KEY = 'customer-import-reviewed-records-v1';

let importRecords = [];
let nextRecordId = 1;
let previewUrl = '';

const URDU_TRANSLATIONS = [
    ['واپڈا کالونی', 'WAPDA Colony'],
    ['مدینہ ٹاؤن', 'Madina Town'],
    ['دانش سکیم', 'Danish Scheme'],
    ['فیصل پارک', 'Faisal Park'],
    ['جناح پارک', 'Jinnah Park'],
    ['سمن آباد', 'Samanabad'],
    ['البدر روڈ', 'Al-Badar Road'],
    ['ملک پورہ', 'Malik Pura'],
    ['اکبر پارک', 'Akbar Park'],
    ['شاد باغ', 'Shad Bagh'],
    ['نذیر شہید روڈ', 'Nazir Shaheed Road'],
    ['فوجی پورہ', 'Fauji Pura'],
    ['گول باغ', 'Gol Bagh'],
    ['اصلاح معاشرہ', 'Islah-e-Muashra'],
    ['شاہین چوک', 'Shaheen Chowk'],
    ['مال روڈ', 'Mall Road'],
    ['روڈ', 'Road'],
    ['پارک', 'Park'],
    ['کالونی', 'Colony'],
    ['سکیم', 'Scheme'],
    ['چوک', 'Chowk'],
    ['گلی', 'Street'],
    ['مکان', 'House'],
    ['منزل', 'House'],
    ['نمبر', 'No.'],
    ['نزد', 'Near'],
    ['ٹاؤن', 'Town'],
    ['پورہ', 'Pura'],
    ['باغ', 'Garden'],
];

document.addEventListener('DOMContentLoaded', async () => {
    const profile = await Auth.requireAuth();
    if (!profile) return;
    if (!Auth.hasPermission('marketing.cust_sms.create')) {
        Auth.showAlert(
            'import-alert',
            'You do not have permission to import customers into CUST_SMS.',
            'warning',
        );
        return;
    }

    restoreRecords();
    renderRecords();
    document.getElementById('import-file').addEventListener('change', previewFile);
    document.getElementById('btn-ai-extract').addEventListener('click', extractWithGemini);
    document.getElementById('btn-extract-mobiles').addEventListener('click', extractMobileRows);
    document.getElementById('btn-parse-text').addEventListener('click', parseOcrText);
    document.getElementById('btn-add-record').addEventListener('click', () => addRecord());
    document.getElementById('btn-finalize-import').addEventListener('click', finalizeImport);
});

function previewFile() {
    const file = document.getElementById('import-file').files[0];
    const preview = document.getElementById('file-preview');
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    if (!file) {
        preview.classList.add('d-none');
        preview.removeAttribute('src');
        return;
    }
    previewUrl = URL.createObjectURL(file);
    preview.src = previewUrl;
    preview.classList.remove('d-none');
}

async function extractWithGemini() {
    const file = document.getElementById('import-file').files[0];
    if (!file) {
        showImportAlert('Choose an image file first.', 'warning');
        return;
    }
    if (file.size > 10 * 1024 * 1024) {
        showImportAlert('Image size must not exceed 10 MB.', 'warning');
        return;
    }
    if (
        importRecords.length
        && !window.confirm('Replace the current review records with the AI extraction?')
    ) return;

    const button = document.getElementById('btn-ai-extract');
    const originalHtml = button.innerHTML;
    const progressWrap = document.getElementById('ocr-progress-wrap');
    button.disabled = true;
    progressWrap.classList.remove('d-none');
    setOcrProgress(10, 'Uploading securely');

    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 240000);
    try {
        const form = new FormData();
        form.append('file', file);
        const headers = {};
        const token = Api.getToken();
        if (token) headers.Authorization = `Bearer ${token}`;
        setOcrProgress(30, 'AI reading handwriting');
        const response = await fetch(`${CUSTOMER_IMPORT_API}/extract`, {
            method: 'POST',
            headers,
            body: form,
            credentials: 'include',
            signal: controller.signal,
        });
        const raw = await response.text();
        let result;
        try {
            result = raw ? JSON.parse(raw) : {};
        } catch {
            result = { detail: `Server returned an unreadable response (${response.status}).` };
        }
        if (!response.ok) {
            throw new Error(result.detail || result.message || 'AI extraction failed.');
        }
        if (!Array.isArray(result.records) || !result.records.length) {
            throw new Error('AI could not find any delivery records in this image.');
        }

        importRecords = result.records.map((record) => newRecord({
            source_row: record.source_row,
            name: record.name,
            mobile: record.mobile,
            original_address: record.original_address,
            english_address: record.english_address,
            auto_translation: false,
        }));
        document.getElementById('ocr-text').value = [
            `Model: ${result.model}`,
            ...(result.warnings || []),
        ].join('\n');
        saveRecords();
        renderRecords();
        setOcrProgress(100, 'AI extraction complete');
        showImportAlert(
            `${importRecords.length} record(s) extracted and translated. Verify all uncertain values before finalizing.`,
            'success',
        );
    } catch (error) {
        setOcrProgress(0, 'Failed');
        showImportAlert(
            error.name === 'AbortError'
                ? 'AI extraction timed out after 4 minutes.'
                : error.message,
            'danger',
        );
    } finally {
        window.clearTimeout(timer);
        button.disabled = false;
        button.innerHTML = originalHtml;
    }
}

async function extractMobileRows() {
    const file = document.getElementById('import-file').files[0];
    const rowCount = Number(document.getElementById('form-row-count').value);
    if (!file) {
        showImportAlert('Choose an image file first.', 'warning');
        return;
    }
    if (!Number.isInteger(rowCount) || rowCount < 1 || rowCount > 50) {
        showImportAlert('Form rows must be between 1 and 50.', 'warning');
        return;
    }
    if (typeof Tesseract === 'undefined') {
        showImportAlert('Local OCR library could not load.', 'danger');
        return;
    }

    const button = document.getElementById('btn-extract-mobiles');
    const originalHtml = button.innerHTML;
    const progressWrap = document.getElementById('ocr-progress-wrap');
    button.disabled = true;
    progressWrap.classList.remove('d-none');
    setOcrProgress(1, 'Loading form');

    let worker;
    try {
        const image = await loadImportImage(file);
        worker = await withTimeout(
            Tesseract.createWorker('eng', 1, {
                workerPath: '/static/vendor/tesseract/worker.min.js',
                corePath: '/static/vendor/tesseract/tesseract-core-lstm.js',
                langPath: '/static/vendor/tesseract',
                workerBlobURL: false,
                errorHandler: (error) => console.error('Mobile OCR error:', error),
            }),
            120000,
            'Mobile-number OCR could not initialize within 2 minutes.',
        );
        await worker.setParameters({
            tessedit_char_whitelist: '0123456789',
            tessedit_pageseg_mode: '6',
            user_defined_dpi: '300',
        });

        const existingKeys = new Set(
            importRecords.map((record) => mobileKey(record.mobile)).filter(Boolean),
        );
        const diagnosticLines = [];
        let added = 0;
        for (let rowIndex = 0; rowIndex < rowCount; rowIndex += 1) {
            setOcrProgress(
                Math.round(5 + ((rowIndex + 1) / rowCount) * 90),
                `Reading contact row ${rowIndex + 1}/${rowCount}`,
            );
            const cellCanvas = cropContactCell(image, rowIndex, rowCount);
            try {
                const result = await withTimeout(
                    worker.recognize(cellCanvas),
                    30000,
                    `Contact row ${rowIndex + 1} timed out.`,
                );
                const raw = String(result.data.text || '').trim();
                diagnosticLines.push(`Row ${rowIndex + 1}: ${raw || '(blank)'}`);
                const mobile = mobileFromOcr(raw);
                const key = mobileKey(mobile);
                if (!key || existingKeys.has(key)) continue;
                importRecords.push(newRecord({
                    mobile,
                    source_row: rowIndex + 1,
                }));
                existingKeys.add(key);
                added += 1;
            } catch (error) {
                diagnosticLines.push(`Row ${rowIndex + 1}: ${error.message}`);
            }
        }

        document.getElementById('ocr-text').value = diagnosticLines.join('\n');
        saveRecords();
        renderRecords();
        setOcrProgress(100, 'Mobile extraction complete');
        showImportAlert(
            `${added} unique mobile number(s) extracted. Verify every digit and enter customer names and addresses.`,
            added ? 'success' : 'warning',
        );
    } catch (error) {
        setOcrProgress(0, 'Failed');
        showImportAlert(error.message || String(error), 'danger');
    } finally {
        if (worker) await worker.terminate().catch(() => {});
        button.disabled = false;
        button.innerHTML = originalHtml;
    }
}

function loadImportImage(file) {
    return new Promise((resolve, reject) => {
        const url = URL.createObjectURL(file);
        const image = new Image();
        image.onload = () => {
            URL.revokeObjectURL(url);
            resolve(image);
        };
        image.onerror = () => {
            URL.revokeObjectURL(url);
            reject(new Error('The selected image could not be opened.'));
        };
        image.src = url;
    });
}

function cropContactCell(image, rowIndex, rowCount) {
    // Stock Delivery Report layout: Contact # is approximately 18.2%-30.2%
    // across the page; data rows occupy approximately 8.4%-95.5% vertically.
    const sourceX = image.naturalWidth * 0.182;
    const sourceWidth = image.naturalWidth * 0.12;
    const dataTop = image.naturalHeight * 0.084;
    const dataHeight = image.naturalHeight * 0.871;
    const rowHeight = dataHeight / rowCount;
    const insetX = sourceWidth * 0.05;
    const insetY = rowHeight * 0.08;
    const cropX = sourceX + insetX;
    const cropY = dataTop + rowIndex * rowHeight + insetY;
    const cropWidth = sourceWidth - insetX * 2;
    const cropHeight = rowHeight - insetY * 2;
    const scale = 4;

    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(cropWidth * scale));
    canvas.height = Math.max(1, Math.round(cropHeight * scale));
    const context = canvas.getContext('2d', { willReadFrequently: true });
    context.fillStyle = '#ffffff';
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(
        image,
        cropX,
        cropY,
        cropWidth,
        cropHeight,
        0,
        0,
        canvas.width,
        canvas.height,
    );

    const pixels = context.getImageData(0, 0, canvas.width, canvas.height);
    for (let index = 0; index < pixels.data.length; index += 4) {
        const grey = (
            pixels.data[index] * 0.299
            + pixels.data[index + 1] * 0.587
            + pixels.data[index + 2] * 0.114
        );
        const value = grey < 185 ? 0 : 255;
        pixels.data[index] = value;
        pixels.data[index + 1] = value;
        pixels.data[index + 2] = value;
        pixels.data[index + 3] = 255;
    }
    context.putImageData(pixels, 0, 0);
    return canvas;
}

function mobileFromOcr(value) {
    const digits = convertUrduDigits(value).replace(/\D/g, '');
    const fullMatch = digits.match(/03\d{9}/);
    if (fullMatch) return normalizePakistanMobile(fullMatch[0]);
    const nationalMatch = digits.match(/3\d{9}/);
    if (nationalMatch) return normalizePakistanMobile(nationalMatch[0]);
    return '';
}

async function readFile() {
    const file = document.getElementById('import-file').files[0];
    if (!file) {
        showImportAlert('Choose an image file first.', 'warning');
        return;
    }
    if (typeof Tesseract === 'undefined') {
        showImportAlert('OCR library could not load. Check internet access and retry.', 'danger');
        return;
    }

    const button = document.getElementById('btn-read-file');
    const progressWrap = document.getElementById('ocr-progress-wrap');
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Reading…';
    progressWrap.classList.remove('d-none');
    setOcrProgress(0, 'Starting OCR');

    let worker;
    try {
        setOcrProgress(2, 'Downloading OCR files');
        const workerPromise = Tesseract.createWorker(['eng', 'urd'], 1, {
            workerPath: '/static/vendor/tesseract/worker.min.js',
            corePath: '/static/vendor/tesseract/tesseract-core-lstm.js',
            langPath: '/static/vendor/tesseract',
            workerBlobURL: false,
            logger: updateOcrProgress,
            errorHandler: (error) => console.error('OCR worker error:', error),
        });
        try {
            worker = await withTimeout(
                workerPromise,
                120000,
                'OCR language files could not load within 2 minutes.',
            );
        } catch (error) {
            workerPromise
                .then((lateWorker) => lateWorker.terminate())
                .catch(() => {});
            throw error;
        }
        setOcrProgress(10, 'Recognizing image');
        const result = await withTimeout(
            worker.recognize(file),
            240000,
            'Image recognition took longer than 4 minutes.',
        );
        document.getElementById('ocr-text').value = result.data.text || '';
        setOcrProgress(100, 'Complete');
        parseOcrText();
        showImportAlert(
            'OCR completed. Correct every record before finalizing.',
            'success',
        );
    } catch (error) {
        setOcrProgress(0, 'Failed');
        showImportAlert(
            `Could not read this image: ${error.message || error}. You can enter records manually below.`,
            'danger',
        );
    } finally {
        if (worker) await worker.terminate().catch(() => {});
        button.disabled = false;
        button.innerHTML = '<i class="bi bi-file-earmark-text me-1"></i> Read and Translate';
    }
}

function updateOcrProgress(message) {
    if (typeof message.progress !== 'number') return;
    setOcrProgress(
        Math.max(2, Math.round(message.progress * 100)),
        message.status || 'Reading',
    );
}

function withTimeout(promise, milliseconds, message) {
    let timer;
    const timeout = new Promise((_, reject) => {
        timer = window.setTimeout(() => reject(new Error(message)), milliseconds);
    });
    return Promise.race([promise, timeout]).finally(() => window.clearTimeout(timer));
}

function parseOcrText() {
    const text = convertUrduDigits(document.getElementById('ocr-text').value);
    if (!text.trim()) {
        showImportAlert('There is no OCR text to parse.', 'warning');
        return;
    }

    const phones = extractPakistanMobiles(text);
    if (!phones.length) {
        addRecord();
        showImportAlert(
            'No reliable mobile number was detected. A blank row was added for manual entry.',
            'warning',
        );
        return;
    }

    const existingKeys = new Set(
        importRecords.map((record) => mobileKey(record.mobile)).filter(Boolean),
    );
    let added = 0;
    phones.forEach((mobile) => {
        const key = mobileKey(mobile);
        if (existingKeys.has(key)) return;
        importRecords.push(newRecord({ mobile }));
        existingKeys.add(key);
        added += 1;
    });
    saveRecords();
    renderRecords();
    showImportAlert(
        `${added} mobile number(s) parsed. Enter or correct each customer name and address.`,
        added ? 'info' : 'warning',
    );
}

function addRecord(values = {}) {
    importRecords.push(newRecord(values));
    saveRecords();
    renderRecords();
}

function newRecord(values = {}) {
    return {
        id: nextRecordId++,
        name: values.name || '',
        mobile: normalizeImportedMobile(values.mobile || '+92'),
        original_address: values.original_address || '',
        english_address: values.english_address || '',
        auto_translation: values.auto_translation !== false,
        source_row: values.source_row || null,
    };
}

function renderRecords() {
    const tbody = document.getElementById('import-records');
    document.getElementById('record-count').textContent =
        `${importRecords.length} record${importRecords.length === 1 ? '' : 's'}`;
    if (!importRecords.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-4">
                    Upload a file or add a record manually.
                </td>
            </tr>`;
        return;
    }

    tbody.innerHTML = importRecords.map((record, index) => `
        <tr data-record-id="${record.id}">
            <td>${record.source_row || index + 1}</td>
            <td>
                <input class="form-control" data-field="name" maxlength="150"
                       value="${escAttr(record.name)}" placeholder="Customer name">
            </td>
            <td>
                <input class="form-control" data-field="mobile" maxlength="30"
                       inputmode="tel" value="${escAttr(record.mobile)}"
                       placeholder="+923xxxxxxxxx">
            </td>
            <td>
                <textarea class="form-control" data-field="original_address"
                          maxlength="500" dir="auto"
                          placeholder="Original Urdu address">${esc(record.original_address)}</textarea>
            </td>
            <td>
                <textarea class="form-control" data-field="english_address"
                          maxlength="500"
                          placeholder="Review English address">${esc(record.english_address)}</textarea>
            </td>
            <td class="text-center">
                <button class="btn btn-sm btn-outline-danger" type="button"
                        data-delete-record="${record.id}" title="Delete record">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');

    tbody.querySelectorAll('[data-field]').forEach((input) => {
        input.addEventListener('input', updateRecord);
        input.addEventListener('blur', finishRecordEdit);
    });
    tbody.querySelectorAll('[data-delete-record]').forEach((button) => {
        button.addEventListener('click', () => {
            importRecords = importRecords.filter(
                (record) => record.id !== Number(button.dataset.deleteRecord),
            );
            saveRecords();
            renderRecords();
        });
    });
}

function updateRecord(event) {
    const row = event.target.closest('[data-record-id]');
    const record = importRecords.find(
        (item) => item.id === Number(row.dataset.recordId),
    );
    if (!record) return;
    record[event.target.dataset.field] = event.target.value;
    if (
        event.target.dataset.field === 'original_address'
        && record.auto_translation
    ) {
        record.english_address = translateUrdu(record.original_address);
        const english = row.querySelector('[data-field="english_address"]');
        english.value = record.english_address;
    }
    if (event.target.dataset.field === 'english_address') {
        record.auto_translation = false;
    }
    saveRecords();
}

function finishRecordEdit(event) {
    if (event.target.dataset.field !== 'mobile') return;
    event.target.value = normalizePakistanMobile(event.target.value);
    updateRecord(event);
}

async function finalizeImport() {
    if (!importRecords.length) {
        showImportAlert('Add at least one record first.', 'warning');
        return;
    }
    const invalid = importRecords.find(
        (record) =>
            !record.name.trim()
            || record.mobile.includes('?')
            || mobileKey(record.mobile).length !== 10
            || !(record.english_address.trim() || record.original_address.trim()),
    );
    if (invalid) {
        showImportAlert(
            'Every record requires a customer name, valid Pakistan mobile, and address.',
            'danger',
        );
        return;
    }
    if (!window.confirm(
        `Finalize ${importRecords.length} reviewed record(s) into CUST_SMS? Existing mobiles will be skipped.`,
    )) return;

    const button = document.getElementById('btn-finalize-import');
    const originalHtml = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Finalizing…';
    try {
        const result = await Api.post(`${CUSTOMER_IMPORT_API}/finalize`, {
            records: importRecords.map((record) => ({
                name: record.name.trim(),
                mobile: normalizePakistanMobile(record.mobile),
                original_address: record.original_address.trim(),
                english_address: record.english_address.trim(),
            })),
        });
        showImportAlert(result.message, 'success');
        importRecords = [];
        saveRecords();
        renderRecords();
    } catch (error) {
        showImportAlert(error.message, 'danger');
    } finally {
        button.disabled = false;
        button.innerHTML = originalHtml;
    }
}

function extractPakistanMobiles(text) {
    const compact = convertUrduDigits(text).replace(/[^\S\r\n]+/g, ' ');
    const matches = compact.match(/(?:\+?92|0)?3(?:[\s().-]*\d){9}/g) || [];
    const result = [];
    const seen = new Set();
    matches.forEach((match) => {
        const normalized = normalizePakistanMobile(match);
        const key = mobileKey(normalized);
        if (key.length === 10 && !seen.has(key)) {
            seen.add(key);
            result.push(normalized);
        }
    });
    return result;
}

function translateUrdu(value) {
    let translated = String(value || '').trim();
    URDU_TRANSLATIONS.forEach(([urdu, english]) => {
        translated = translated.split(urdu).join(english);
    });
    return translated;
}

function convertUrduDigits(value) {
    const digits = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
    };
    return String(value || '').replace(/[۰-۹٠-٩]/g, (digit) => digits[digit]);
}

function normalizePakistanMobile(value) {
    let digits = convertUrduDigits(value).replace(/\D/g, '');
    if (digits.startsWith('0092')) digits = digits.slice(2);
    if (digits.startsWith('92')) digits = digits.slice(2);
    if (digits.startsWith('0')) digits = digits.slice(1);
    return digits ? `+92${digits}` : '+92';
}

function normalizeImportedMobile(value) {
    const text = String(value || '').trim();
    return text.includes('?') ? text : normalizePakistanMobile(text);
}

function mobileKey(value) {
    const digits = normalizePakistanMobile(value).replace(/\D/g, '');
    return digits.length >= 10 ? digits.slice(-10) : '';
}

function setOcrProgress(percent, label) {
    const bar = document.getElementById('ocr-progress');
    bar.style.width = `${percent}%`;
    bar.textContent = `${label} ${percent}%`;
}

function saveRecords() {
    localStorage.setItem(IMPORT_STORAGE_KEY, JSON.stringify(importRecords));
}

function restoreRecords() {
    try {
        const saved = JSON.parse(localStorage.getItem(IMPORT_STORAGE_KEY) || '[]');
        if (!Array.isArray(saved)) return;
        importRecords = saved.map((record) => newRecord(record));
    } catch {
        importRecords = [];
    }
}

function showImportAlert(message, type) {
    Auth.showAlert('import-alert', message, type);
}

function esc(value) {
    const element = document.createElement('div');
    element.textContent = value == null ? '' : String(value);
    return element.innerHTML;
}

function escAttr(value) {
    return esc(value).replace(/"/g, '&quot;');
}
