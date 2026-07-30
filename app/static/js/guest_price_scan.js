(function () {
    'use strict';

    const API_BARCODE = '/api/v1/public/price-lookup/by-barcode';
    const API_MANUAL = '/api/v1/public/price-lookup/by-manual-id';
    const SCAN_COOLDOWN_MS = 2000;

    let scanning = false;
    let zxingReader = null;
    let html5Scanner = null;
    let lastKey = '';
    let lastScanAt = 0;

    const el = {
        reader: document.getElementById('reader'),
        cameraPreview: document.getElementById('camera-preview'),
        btnStart: document.getElementById('btn-start-scan'),
        btnStop: document.getElementById('btn-stop-scan'),
        btnLookupBarcode: document.getElementById('btn-lookup-barcode'),
        btnLookupManual: document.getElementById('btn-lookup-manual'),
        manualBarcode: document.getElementById('manual-barcode'),
        manualId: document.getElementById('manual-id'),
        btnScanAnother: document.getElementById('btn-scan-another'),
        resultSection: document.getElementById('result-section'),
        loadingSection: document.getElementById('loading-section'),
        alertContainer: document.getElementById('alert-container'),
        alertBox: document.getElementById('alert-box'),
        scanStatus: document.getElementById('scan-status'),
        resultPrice: document.getElementById('result-price'),
        resultGstNote: document.getElementById('result-gst-note'),
        resultTitle: document.getElementById('result-title'),
        resultManualId: document.getElementById('result-manual-id'),
        resultBarcode: document.getElementById('result-barcode'),
        resultShort: document.getElementById('result-short'),
        resultUom: document.getElementById('result-uom'),
        resultBrand: document.getElementById('result-brand'),
        resultMrp: document.getElementById('result-mrp'),
        rowShort: document.getElementById('row-short'),
        rowUom: document.getElementById('row-uom'),
        rowBrand: document.getElementById('row-brand'),
        rowMrp: document.getElementById('row-mrp'),
        promoBadge: document.getElementById('promo-badge'),
    };

    function isIOS() {
        return /iPad|iPhone|iPod/i.test(navigator.userAgent)
            || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    }

    function fmtMoney(value) {
        if (typeof formatAmount === 'function') return formatAmount(value);
        const n = Number(value);
        return Number.isNaN(n) ? '0.00' : n.toFixed(2);
    }

    function showAlert(message, type) {
        el.alertBox.className = `alert alert-${type} mb-0`;
        el.alertBox.textContent = message;
        el.alertContainer.classList.remove('d-none');
    }

    function hideAlert() {
        el.alertContainer.classList.add('d-none');
    }

    function setScanStatus(text) {
        if (el.scanStatus) el.scanStatus.textContent = text;
    }

    function setCameraUi(active) {
        if (el.btnStart) el.btnStart.classList.toggle('d-none', active);
        if (el.btnStop) el.btnStop.classList.toggle('d-none', !active);
    }

    function setLoading(on) {
        el.loadingSection.classList.toggle('d-none', !on);
        if (on) el.resultSection.classList.add('d-none');
    }

    function setOverlayVisible(on) {
        const overlay = document.getElementById('scan-overlay');
        if (overlay) overlay.classList.toggle('d-none', !on);
    }

    function prepareReader() {
        if (!el.reader) return;
        el.reader.classList.add('scanning');
        setOverlayVisible(true);
        if (el.cameraPreview) {
            el.cameraPreview.classList.remove('d-none');
        }
    }

    function resetReader() {
        if (!el.reader) return;
        el.reader.classList.remove('scanning');
        setOverlayVisible(false);
        if (el.cameraPreview) {
            el.cameraPreview.srcObject = null;
            el.cameraPreview.classList.add('d-none');
        }
        const injected = el.reader.querySelector('video:not(#camera-preview)');
        if (injected) injected.remove();
    }

    function toggleOptionalRow(rowEl, valueEl, value) {
        if (value !== null && value !== undefined && String(value).trim() !== '' && value !== 0) {
            valueEl.textContent = value;
            rowEl.classList.remove('d-none');
        } else {
            rowEl.classList.add('d-none');
        }
    }

    function renderResult(data, label) {
        const price = data.sales_rate;
        el.resultPrice.textContent = price != null ? `Rs. ${fmtMoney(price)}` : '—';

        const gst = data.gst_amount;
        const woGst = data.sales_price_wo_gst;
        if (gst > 0 && woGst != null) {
            el.resultGstNote.textContent = `Excl. GST: Rs. ${fmtMoney(woGst)} + GST Rs. ${fmtMoney(gst)}`;
            el.resultGstNote.classList.remove('d-none');
        } else {
            el.resultGstNote.classList.add('d-none');
        }

        el.resultTitle.textContent = data.item_title || '—';
        el.resultManualId.textContent = data.manual_id ?? '—';
        el.resultBarcode.textContent = label || data.barcodeid || '—';

        toggleOptionalRow(el.rowShort, el.resultShort, data.item_short);
        toggleOptionalRow(el.rowUom, el.resultUom, data.uom_title);
        toggleOptionalRow(el.rowBrand, el.resultBrand, data.co_title);

        if (data.market_price > 0) {
            el.resultMrp.textContent = `Rs. ${fmtMoney(data.market_price)}`;
            el.rowMrp.classList.remove('d-none');
        } else {
            el.rowMrp.classList.add('d-none');
        }

        el.promoBadge.classList.toggle('d-none', !data.promotion);
        el.resultSection.classList.remove('d-none');
        el.resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        if (navigator.vibrate) navigator.vibrate(80);
    }

    async function fetchItem(url) {
        const res = await fetch(url);
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            const msg = data.detail || 'Item not found.';
            throw new Error(typeof msg === 'string' ? msg : 'Item not found.');
        }
        return data;
    }

    async function lookupBarcode(barcode) {
        const code = (barcode || '').trim();
        if (!code || code === '0') {
            showAlert('Please enter a valid barcode.', 'warning');
            return;
        }
        const key = `b:${code}`;
        if (key === lastKey && Date.now() - lastScanAt < SCAN_COOLDOWN_MS) return;

        hideAlert();
        setLoading(true);
        setScanStatus('Looking up item…');

        try {
            const data = await fetchItem(`${API_BARCODE}/${encodeURIComponent(code)}`);
            lastKey = key;
            lastScanAt = Date.now();
            el.manualBarcode.value = code;
            renderResult(data, code);
            setScanStatus(scanning ? 'Scan next item or search below' : 'Tap Start Camera Scan');
        } catch (err) {
            showAlert(err.message || 'Item not found.', 'danger');
            setScanStatus(scanning ? 'Point camera at barcode' : 'Tap Start Camera Scan');
        } finally {
            setLoading(false);
        }
    }

    async function lookupManualId(manualId) {
        const id = parseInt(String(manualId || '').trim(), 10);
        if (!id || id <= 0) {
            showAlert('Please enter a valid Manual ID (number on price tag).', 'warning');
            return;
        }
        const key = `m:${id}`;
        if (key === lastKey && Date.now() - lastScanAt < SCAN_COOLDOWN_MS) return;

        hideAlert();
        setLoading(true);
        setScanStatus('Looking up item…');

        try {
            const data = await fetchItem(`${API_MANUAL}/${id}`);
            lastKey = key;
            lastScanAt = Date.now();
            el.manualId.value = String(id);
            if (data.barcodeid && data.barcodeid !== '0') {
                el.manualBarcode.value = data.barcodeid;
            }
            renderResult(data, data.barcodeid && data.barcodeid !== '0' ? data.barcodeid : '—');
            setScanStatus(scanning ? 'Scan next item or search below' : 'Tap Start Camera Scan');
        } catch (err) {
            showAlert(err.message || 'Manual ID not found.', 'danger');
            setScanStatus(scanning ? 'Point camera at barcode' : 'Tap Start Camera Scan');
        } finally {
            setLoading(false);
        }
    }

    function onCodeDetected(code) {
        if (!scanning || !code) return;
        lookupBarcode(String(code).trim());
    }

    function stopZxing() {
        if (!zxingReader) return;
        try {
            zxingReader.reset();
        } catch (err) {
            /* ignore */
        }
        zxingReader = null;
    }

    async function startZxingScanner() {
        if (!window.ZXingBrowser || !window.ZXingBrowser.BrowserMultiFormatReader) {
            throw new Error('ZXing scanner not loaded');
        }
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Camera not supported');
        }

        prepareReader();
        zxingReader = new ZXingBrowser.BrowserMultiFormatReader();

        const onResult = (result, err) => {
            if (result && scanning) {
                onCodeDetected(result.getText());
            }
            if (err && !(err.name === 'NotFoundException' || err.name === 'ChecksumException'
                || err.name === 'FormatException')) {
                /* decode errors while scanning are normal */
            }
        };

        const constraintsList = [
            { video: { facingMode: { ideal: 'environment' } }, audio: false },
            { video: { facingMode: 'environment' }, audio: false },
            { video: true, audio: false },
        ];

        let lastErr;
        for (const constraints of constraintsList) {
            try {
                await zxingReader.decodeFromConstraints(constraints, 'reader', onResult);
                const video = el.reader.querySelector('video');
                if (video) {
                    video.setAttribute('playsinline', 'true');
                    video.setAttribute('webkit-playsinline', 'true');
                    video.muted = true;
                    video.style.width = '100%';
                    video.style.height = 'auto';
                    video.style.minHeight = '280px';
                    video.style.objectFit = 'cover';
                }
                return;
            } catch (err) {
                lastErr = err;
                stopZxing();
                zxingReader = new ZXingBrowser.BrowserMultiFormatReader();
            }
        }

        try {
            const listFn = ZXingBrowser.BrowserMultiFormatReader.listVideoInputDevices
                || ZXingBrowser.BrowserCodeReader.listVideoInputDevices;
            const devices = listFn ? await listFn.call(ZXingBrowser.BrowserMultiFormatReader) : [];
            if (devices && devices.length) {
                const back = devices.find((d) => /back|rear|environment/i.test(d.label || ''));
                const device = back || devices[devices.length - 1];
                await zxingReader.decodeFromVideoDevice(device.deviceId, 'reader', onResult);
                return;
            }
        } catch (err) {
            lastErr = err;
        }

        throw lastErr || new Error('Camera failed to start');
    }

    async function destroyHtml5Scanner() {
        if (!html5Scanner) return;
        try { await html5Scanner.stop(); } catch (err) { /* ignore */ }
        try { await html5Scanner.clear(); } catch (err) { /* ignore */ }
        html5Scanner = null;
    }

    async function startHtml5Scanner() {
        if (!window.Html5Qrcode) throw new Error('Html5Qrcode not loaded');

        stopZxing();
        await destroyHtml5Scanner();
        if (el.reader) {
            el.reader.innerHTML = '';
            el.reader.classList.add('scanning');
        }
        setOverlayVisible(true);

        const viewWidth = Math.min(window.innerWidth - 32, 480);
        const config = {
            fps: 10,
            qrbox: (w, h) => ({ width: Math.floor(w * 0.9), height: Math.floor(h * 0.45) }),
            disableFlip: false,
        };

        html5Scanner = new Html5Qrcode('reader', { verbose: false });
        const attempts = [
            { facingMode: 'environment' },
            { facingMode: 'user' },
        ];

        let lastErr;
        for (const cam of attempts) {
            try {
                await html5Scanner.start(cam, config, onCodeDetected, () => {});
                const video = el.reader.querySelector('video');
                if (video) {
                    video.setAttribute('playsinline', 'true');
                    video.setAttribute('webkit-playsinline', 'true');
                    video.muted = true;
                }
                return;
            } catch (err) {
                lastErr = err;
                await destroyHtml5Scanner();
                prepareReader();
                html5Scanner = new Html5Qrcode('reader', { verbose: false });
            }
        }
        throw lastErr || new Error('Camera failed');
    }

    function cameraErrorMessage(err) {
        const msg = (err && err.message ? err.message : String(err || '')).toLowerCase();
        if (msg.includes('notallowed') || msg.includes('permission') || msg.includes('denied')) {
            return isIOS()
                ? 'Camera blocked. iPhone Settings → Safari → Camera → Allow. Then reload this page.'
                : 'Camera permission denied. Allow camera access in browser settings.';
        }
        if (msg.includes('not supported') || msg.includes('not found')) {
            return 'Camera not available. Use Manual ID search below.';
        }
        return 'Camera could not start. Use Manual ID or type barcode below.';
    }

    async function startScanner() {
        if (scanning) return;
        if (!window.isSecureContext && location.hostname !== 'localhost') {
            showAlert('Camera needs HTTPS. Open https://erp.ahsteellab.com/guest/scan', 'warning');
            return;
        }

        hideAlert();
        setScanStatus('Starting camera…');
        setCameraUi(true);
        scanning = true;

        try {
            try {
                await startZxingScanner();
            } catch (zxingErr) {
                await startHtml5Scanner();
            }
            setScanStatus('Point camera at barcode');
        } catch (err) {
            scanning = false;
            stopZxing();
            await destroyHtml5Scanner();
            resetReader();
            setCameraUi(false);
            showAlert(cameraErrorMessage(err), 'warning');
            setScanStatus('Use Manual ID or Barcode search below');
        }
    }

    async function stopScanner() {
        scanning = false;
        stopZxing();
        await destroyHtml5Scanner();
        resetReader();
        setCameraUi(false);
        setScanStatus('Tap Start Camera Scan');
    }

    function resetForAnother() {
        lastKey = '';
        lastScanAt = 0;
        el.manualBarcode.value = '';
        el.manualId.value = '';
        el.resultSection.classList.add('d-none');
        hideAlert();
        setScanStatus(scanning ? 'Point camera at barcode' : 'Tap Start Camera Scan');
    }

    function bindEvents() {
        if (!el.btnStart || !el.btnLookupManual) {
            showAlert('Page did not load correctly. Please refresh.', 'danger');
            return;
        }

        el.btnStart.addEventListener('click', startScanner);
        el.btnStop.addEventListener('click', stopScanner);
        el.btnLookupBarcode.addEventListener('click', () => lookupBarcode(el.manualBarcode.value));
        el.btnLookupManual.addEventListener('click', () => lookupManualId(el.manualId.value));
        el.manualBarcode.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') { e.preventDefault(); lookupBarcode(el.manualBarcode.value); }
        });
        el.manualId.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') { e.preventDefault(); lookupManualId(el.manualId.value); }
        });
        el.btnScanAnother.addEventListener('click', resetForAnother);
        window.addEventListener('beforeunload', () => { if (scanning) stopScanner(); });
        setScanStatus('Tap Start Camera Scan');
    }

    bindEvents();
})();
