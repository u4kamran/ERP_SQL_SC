/**
 * Business day helpers — day starts 08:00, ends next day 05:00.
 * Keep in sync with app/utils/business_day.py
 */
const BUSINESS_DAY_START_HOUR = 8;
const BUSINESS_DAY_END_HOUR = 5;

function businessDateFor(d) {
    if (d.getHours() < BUSINESS_DAY_START_HOUR) {
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
        0,
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
        0,
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
    const startH = BUSINESS_DAY_START_HOUR;
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
        start = new Date(y, m, 1, startH, 0, 0, 0);
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
        start = new Date(now.getFullYear(), now.getMonth(), 1, startH, 0, 0, 0);
        end = new Date(now);
        if (end < start) {
            const pm = now.getMonth() === 0 ? 11 : now.getMonth() - 1;
            const py = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear();
            start = new Date(py, pm, 1, startH, 0, 0, 0);
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
    return `${fmt(d)} ${String(BUSINESS_DAY_START_HOUR).padStart(2, '0')}:00 → ${fmt(end)} ${String(BUSINESS_DAY_END_HOUR).padStart(2, '0')}:00`;
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
