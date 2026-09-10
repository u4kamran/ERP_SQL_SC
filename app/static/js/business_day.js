/**
 * Business day helpers — loads configured hours from Default Setup API.
 * Keep logic aligned with app/utils/business_day.py
 */
let BUSINESS_DAY_START_HOUR = 8;
let BUSINESS_DAY_END_HOUR = 5;
let BUSINESS_DAY_START_MINUTE = 0;
let BUSINESS_DAY_END_MINUTE = 0;
let businessDayConfigLoaded = false;
let businessDayConfigPromise = null;

const BUSINESS_DAY_API = '/api/v1/settings/default-setup/business-day';

function parseTimeParts(hhmm) {
    const [h, m] = (hhmm || '00:00').split(':').map(Number);
    return { hour: h || 0, minute: m || 0 };
}

function applyBusinessDayConfig(data) {
    const start = parseTimeParts(data.business_day_start_time);
    const end = parseTimeParts(data.business_day_end_time);
    BUSINESS_DAY_START_HOUR = start.hour;
    BUSINESS_DAY_START_MINUTE = start.minute;
    BUSINESS_DAY_END_HOUR = end.hour;
    BUSINESS_DAY_END_MINUTE = end.minute;
    businessDayConfigLoaded = true;
    if (typeof updateBusinessDayNote === 'function') {
        updateBusinessDayNote(data);
    }
}

async function loadBusinessDayConfig() {
    if (businessDayConfigPromise) return businessDayConfigPromise;
    businessDayConfigPromise = (async () => {
        try {
            const data = await Api.get(BUSINESS_DAY_API);
            applyBusinessDayConfig(data);
            return;
        } catch (_err) {
            /* use defaults */
        }
        businessDayConfigLoaded = true;
    })();
    return businessDayConfigPromise;
}

function isBeforeBusinessStart(d) {
    const mins = d.getHours() * 60 + d.getMinutes();
    const startMins = BUSINESS_DAY_START_HOUR * 60 + BUSINESS_DAY_START_MINUTE;
    return mins < startMins;
}

function businessDateFor(d) {
    if (isBeforeBusinessStart(d)) {
        return new Date(d.getFullYear(), d.getMonth(), d.getDate() - 1);
    }
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function businessDayStart(dateObj) {
    return new Date(
        dateObj.getFullYear(),
        dateObj.getMonth(),
        dateObj.getDate(),
        BUSINESS_DAY_START_HOUR,
        BUSINESS_DAY_START_MINUTE,
        0,
        0,
    );
}

function businessDayEnd(dateObj) {
    return new Date(
        dateObj.getFullYear(),
        dateObj.getMonth(),
        dateObj.getDate() + 1,
        BUSINESS_DAY_END_HOUR,
        BUSINESS_DAY_END_MINUTE,
        0,
        0,
    );
}

function lastDayOfMonth(year, month) {
    return new Date(year, month + 1, 0).getDate();
}

function currentBusinessDayStart(now = new Date()) {
    return businessDayStart(businessDateFor(now));
}

function applyBusinessPreset(preset, now = new Date()) {
    let start;
    let end;

    if (preset === 'today') {
        start = currentBusinessDayStart(now);
        end = new Date(now);
    } else if (preset === 'yesterday') {
        const bd = businessDateFor(now);
        bd.setDate(bd.getDate() - 1);
        start = businessDayStart(bd);
        end = businessDayEnd(bd);
    } else if (preset === 'last-month') {
        const y = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear();
        const m = now.getMonth() === 0 ? 11 : now.getMonth() - 1;
        const lastD = lastDayOfMonth(y, m);
        start = businessDayStart(new Date(y, m, 1));
        end = businessDayEnd(new Date(y, m, lastD));
    } else if (preset === 'last-7') {
        const bd = businessDateFor(now);
        start = businessDayStart(new Date(bd.getFullYear(), bd.getMonth(), bd.getDate() - 6));
        end = new Date(now);
    } else if (preset === 'last-30') {
        const bd = businessDateFor(now);
        start = businessDayStart(new Date(bd.getFullYear(), bd.getMonth(), bd.getDate() - 29));
        end = new Date(now);
    } else if (preset === 'this-month') {
        start = new Date(
            now.getFullYear(),
            now.getMonth(),
            1,
            BUSINESS_DAY_START_HOUR,
            BUSINESS_DAY_START_MINUTE,
            0,
            0,
        );
        end = new Date(now);
        if (end < start) {
            const pm = now.getMonth() === 0 ? 11 : now.getMonth() - 1;
            const py = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear();
            start = new Date(py, pm, 1, BUSINESS_DAY_START_HOUR, BUSINESS_DAY_START_MINUTE, 0, 0);
        }
    } else {
        return null;
    }
    return { start, end };
}

function formatBusinessDayLabel(isoDate) {
    const d = new Date(isoDate);
    if (Number.isNaN(d.getTime())) return isoDate;
    const end = new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1);
    const fmt = (dt) => dt.toLocaleDateString(undefined, { day: '2-digit', month: 'short' });
    const pad = (n) => String(n).padStart(2, '0');
    const startLabel = `${pad(BUSINESS_DAY_START_HOUR)}:${pad(BUSINESS_DAY_START_MINUTE)}`;
    const endLabel = `${pad(BUSINESS_DAY_END_HOUR)}:${pad(BUSINESS_DAY_END_MINUTE)}`;
    return `${fmt(d)} ${startLabel} → ${fmt(end)} ${endLabel}`;
}

/** Shift YYYY-MM-DD by calendar months (for MoM chart alignment). */
function shiftIsoDateMonths(isoDate, months) {
    if (!isoDate) return isoDate;
    const [y, m, d] = isoDate.split('-').map(Number);
    if (!y || !m || !d) return isoDate;
    const shifted = new Date(y, m - 1 + months, d);
    const yy = shifted.getFullYear();
    const mm = String(shifted.getMonth() + 1).padStart(2, '0');
    const dd = String(shifted.getDate()).padStart(2, '0');
    return `${yy}-${mm}-${dd}`;
}

function formatConfiguredTime(hour, minute) {
    const d = new Date(2000, 0, 1, hour, minute || 0);
    return d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
}

function businessDayDisplayNote() {
    return `Business day: ${formatConfiguredTime(BUSINESS_DAY_START_HOUR, BUSINESS_DAY_START_MINUTE)} today → ${formatConfiguredTime(BUSINESS_DAY_END_HOUR, BUSINESS_DAY_END_MINUTE)} next morning`;
}
