/** Shared amount formatting: 999,999,999.00 */
function formatAmount(value, decimals = 2) {
    if (value === null || value === undefined || value === '') return '';
    const n = Number(String(value).replace(/,/g, ''));
    if (Number.isNaN(n)) return String(value);
    return n.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
}

function parseAmount(value) {
    if (value === null || value === undefined || value === '') return NaN;
    return Number(String(value).replace(/,/g, ''));
}
