/**
 * Format API datetimes stored as UTC in SQL Server.
 * Appends Z when the API omits timezone info (legacy responses).
 */
function formatUtcDateTime(value, options) {
    if (!value) return '—';
    const text = String(value).trim();
    const hasTimezone = /[zZ]$|[+-]\d{2}:\d{2}$/.test(text);
    const normalized = hasTimezone ? text : `${text}Z`;
    const date = new Date(normalized);
    if (Number.isNaN(date.getTime())) return text;
    return date.toLocaleString(undefined, options);
}
