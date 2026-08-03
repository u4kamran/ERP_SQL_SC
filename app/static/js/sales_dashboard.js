/** Sales Dashboard — full page with KPIs, chart, comparison. */
const SALES_API = '/api/v1/reports/sales-dashboard';
let trendChart = null;

function initSalesDashboard() {
    setDefaultDates();
    document.getElementById('btn-refresh-sales').addEventListener('click', () => {
        extendRangeToNow();
        loadAll();
    });
    document.getElementById('sales-date-from').addEventListener('change', loadAll);
    document.getElementById('sales-date-to').addEventListener('change', loadAll);
    document.querySelectorAll('.preset-btn').forEach((btn) => {
        btn.addEventListener('click', () => applyPreset(btn.dataset.preset));
    });
    loadAll();
}

function canViewSalesDashboard() {
    return Auth.hasPermission('reports.sales_dashboard.view')
        || Auth.hasPermission('inventory.fin_item.view')
        || Auth.hasPermission('auth.admin.full');
}

function setDefaultDates() {
    applyPreset('this-month', false);
}

function applyPreset(preset, reload = true) {
    const range = applyBusinessPreset(preset);
    if (!range) return;

    document.getElementById('sales-date-from').value = toLocalInput(range.start);
    document.getElementById('sales-date-to').value = toLocalInput(range.end);

    document.querySelectorAll('.preset-btn').forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.preset === preset);
    });

    if (reload) loadAll();
}

function extendRangeToNow() {
    const activePreset = document.querySelector('.preset-btn.active')?.dataset.preset;
    if (['today', 'this-month', 'last-7', 'last-30'].includes(activePreset)) {
        document.getElementById('sales-date-to').value = toLocalInput(new Date());
    }
}

function pad(n) {
    return String(n).padStart(2, '0');
}

function toLocalInput(d) {
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function toApiDateTime(localValue) {
    if (!localValue) return '';
    return localValue.length === 16 ? `${localValue}:00` : localValue;
}

function buildParams() {
    const start = toApiDateTime(document.getElementById('sales-date-from').value);
    const end = toApiDateTime(document.getElementById('sales-date-to').value);
    return new URLSearchParams({ start_date: start, end_date: end });
}

async function loadAll() {
    const btn = document.getElementById('btn-refresh-sales');
    const errEl = document.getElementById('sales-dashboard-error');
    errEl.classList.add('d-none');
    btn.disabled = true;

    try {
        const params = buildParams();
        params.set('_', String(Date.now()));
        const [summary, trend, topInvoices, dayWise] = await Promise.all([
            Api.get(`${SALES_API}/summary?${params}`),
            Api.get(`${SALES_API}/daily-trend?${params}`),
            Api.get(`${SALES_API}/top-invoices?${params}&limit=10`),
            Api.get(`${SALES_API}/day-wise?${params}`),
        ]);
        renderSummary(summary);
        renderTrendChart(trend);
        renderTopInvoices(topInvoices);
        renderDayWise(dayWise);
    } catch (e) {
        errEl.textContent = e.message || 'Could not load sales dashboard.';
        errEl.classList.remove('d-none');
    } finally {
        btn.disabled = false;
    }
}

function renderSummary(data) {
    const current = data.current;
    const previous = data.previous;

    document.getElementById('kpi-total-sale').textContent = formatAmount(current.total_sale);
    document.getElementById('kpi-total-cost').textContent = formatAmount(current.total_cost);
    document.getElementById('kpi-profit').textContent = formatAmount(current.profit);
    document.getElementById('kpi-profit-pct').textContent =
        current.profit_percent != null ? `${formatAmount(current.profit_percent)}%` : '—';
    document.getElementById('kpi-avg-sale').textContent = formatAmount(current.avg_sale_per_day);

    document.getElementById('sales-period-text').textContent =
        `${formatReportDateTime(current.start_date)} → ${formatReportDateTime(current.end_date)}`;
    document.getElementById('sales-total-days').textContent =
        `${current.total_days} day${current.total_days === 1 ? '' : 's'}`;
    document.getElementById('sales-compare-period-text').textContent =
        `Compared with last month: ${formatReportDateTime(previous.start_date)} → ${formatReportDateTime(previous.end_date)}`;

    renderCompareLine('cmp-total-sale', data.total_sale, false);
    renderCompareLine('cmp-total-cost', data.total_cost, true);
    renderCompareLine('cmp-profit', data.profit, false);
    renderCompareLine('cmp-avg-sale', data.avg_sale_per_day, false);
    renderCompareLine('cmp-profit-pct', data.profit_percent, false, true);
    renderCompareTable(data);
    renderCompareTransposedTable(data);
}

function formatMetricValue(metric, isPercent) {
    if (!metric) return '—';
    return isPercent ? `${formatAmount(metric)}%` : formatAmount(metric);
}

function formatChangeValue(metric, isPercent) {
    if (!metric) return '—';
    const prefix = metric.change > 0 ? '+' : '';
    if (isPercent) return `${prefix}${formatAmount(metric.change)} pts`;
    return `${prefix}${formatAmount(metric.change)}`;
}

function formatChangePercentValue(metric, isPercent) {
    if (isPercent || !metric || metric.change_percent == null) return '—';
    const prefix = metric.change_percent > 0 ? '+' : '';
    return `${prefix}${formatAmount(metric.change_percent)}%`;
}

function renderCompareTransposedTable(data) {
    const tbody = document.getElementById('sales-compare-transposed-body');
    if (!tbody) return;

    const metrics = [
        { key: 'total_sale', label: 'Total Sale', percent: false },
        { key: 'total_cost', label: 'Total Cost', percent: false },
        { key: 'profit', label: 'Profit', percent: false },
        { key: 'profit_percent', label: 'Profit %', percent: true },
        { key: 'avg_sale_per_day', label: 'Avg Sale / Day', percent: false },
    ];

    const rows = [
        {
            label: 'Current',
            className: 'row-current',
            values: metrics.map((m) => formatMetricValue(data[m.key]?.current, m.percent)),
        },
        {
            label: 'Last Month',
            className: 'row-previous',
            values: metrics.map((m) => formatMetricValue(data[m.key]?.previous, m.percent)),
        },
        {
            label: 'Change',
            className: 'row-change',
            values: metrics.map((m) => formatChangeValue(data[m.key], m.percent)),
        },
        {
            label: 'Change %',
            className: 'row-change-pct',
            values: metrics.map((m) => formatChangePercentValue(data[m.key], m.percent)),
        },
    ];

    tbody.innerHTML = rows.map((row) => `
        <tr class="${row.className}">
            <td><strong>${row.label}</strong></td>
            ${row.values.map((v) => `<td class="num">${v}</td>`).join('')}
        </tr>
    `).join('');
}

function renderCompareLine(elementId, metric, lowerIsBetter = false, isPercent = false) {
    const el = document.getElementById(elementId);
    if (!el || !metric) {
        if (el) el.innerHTML = '';
        return;
    }
    const prevText = isPercent ? `${formatAmount(metric.previous)}%` : formatAmount(metric.previous);
    el.innerHTML = `
        <div class="prev-value">Last month: ${prevText}</div>
        <div>${formatChangeBadge(metric, lowerIsBetter, isPercent)}</div>
    `;
}

function formatChangeBadge(metric, lowerIsBetter, isPercent) {
    const change = metric.change;
    const cls = change > 0 ? (lowerIsBetter ? 'down' : 'up') : change < 0 ? (lowerIsBetter ? 'up' : 'down') : 'flat';
    const arrow = change > 0 ? '▲' : change < 0 ? '▼' : '■';
    let changeText;
    if (isPercent) {
        changeText = `${change > 0 ? '+' : ''}${formatAmount(change)} pts`;
    } else {
        changeText = `${change > 0 ? '+' : ''}${formatAmount(change)}`;
    }
    let pctText = '';
    if (!isPercent && metric.change_percent != null) {
        pctText = ` (${metric.change_percent > 0 ? '+' : ''}${formatAmount(metric.change_percent)}%)`;
    }
    return `<span class="kpi-change ${cls}">${arrow} ${changeText}${pctText}</span>`;
}

function renderCompareTable(data) {
    const tbody = document.getElementById('sales-compare-table-body');
    const rows = [
        { label: 'Total Sale', metric: data.total_sale, percent: false },
        { label: 'Total Cost', metric: data.total_cost, percent: false },
        { label: 'Profit', metric: data.profit, percent: false },
        { label: 'Profit %', metric: data.profit_percent, percent: true },
        { label: 'Avg Sale / Day', metric: data.avg_sale_per_day, percent: false },
    ];
    tbody.innerHTML = rows.map((row) => {
        const currentText = row.percent ? `${formatAmount(row.metric.current)}%` : formatAmount(row.metric.current);
        const previousText = row.percent ? `${formatAmount(row.metric.previous)}%` : formatAmount(row.metric.previous);
        const changeText = row.percent
            ? `${row.metric.change > 0 ? '+' : ''}${formatAmount(row.metric.change)} pts`
            : `${row.metric.change > 0 ? '+' : ''}${formatAmount(row.metric.change)}`;
        const pctText = row.percent || row.metric.change_percent == null
            ? '—'
            : `${row.metric.change_percent > 0 ? '+' : ''}${formatAmount(row.metric.change_percent)}%`;
        return `<tr>
            <td>${row.label}</td>
            <td class="num">${currentText}</td>
            <td class="num">${previousText}</td>
            <td class="num">${changeText}</td>
            <td class="num">${pctText}</td>
        </tr>`;
    }).join('');
}

function chartLabelForBusinessDate(isoDate) {
    const d = new Date(isoDate);
    if (Number.isNaN(d.getTime())) return isoDate;
    return d.toLocaleDateString(undefined, { day: '2-digit', month: 'short' });
}

function renderTrendChart(trend) {
    const canvas = document.getElementById('sales-trend-chart');
    if (!canvas || typeof Chart === 'undefined') return;

    const currentMap = new Map(trend.current.map((p) => [p.sale_date, p.total_sale]));
    const previousMap = new Map(
        trend.previous.map((p) => [shiftIsoDateMonths(p.sale_date, 1), p.total_sale]),
    );
    const days = [...currentMap.keys()].sort();

    const labels = days.map((d) => chartLabelForBusinessDate(d));
    const currentData = days.map((d) => currentMap.get(d) ?? null);
    const previousData = days.map((d) => previousMap.get(d) ?? null);

    if (trendChart) trendChart.destroy();
    trendChart = new Chart(canvas, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Current',
                    data: currentData,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110,  253, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2,
                },
                {
                    label: 'Last Month',
                    data: previousData,
                    borderColor: '#6c757d',
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    tension: 0.3,
                    pointRadius: 2,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label(ctx) {
                            return `${ctx.dataset.label}: ${formatAmount(ctx.parsed.y)}`;
                        },
                    },
                },
            },
            scales: {
                y: {
                    ticks: {
                        callback: (v) => formatAmount(v, 0),
                    },
                },
            },
        },
    });
}

function renderTopInvoices(data) {
    const tbody = document.getElementById('top-invoices-body');
    if (!data.items?.length) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-muted">No invoices in range.</td></tr>';
        return;
    }
    tbody.innerHTML = data.items.map((row, i) => `
        <tr>
            <td><span class="text-muted small me-1">#${i + 1}</span>${row.inv_id}</td>
            <td class="num">${formatAmount(row.total_sale)}</td>
            <td class="num">${formatAmount(row.total_qty, 0)}</td>
        </tr>
    `).join('');
}

function renderDayWise(data) {
    const tbody = document.getElementById('day-wise-body');
    const noteEl = document.getElementById('day-wise-note');
    if (noteEl && data.business_hours_note) {
        noteEl.textContent = data.business_hours_note;
    }
    if (!data.items?.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-muted">No sales in range.</td></tr>';
        return;
    }
    tbody.innerHTML = data.items.map((row) => `
        <tr>
            <td><span class="small">${row.day_label || formatBusinessDayLabel(row.business_date)}</span></td>
            <td class="num">${formatAmount(row.total_sale)}</td>
            <td class="num">${formatAmount(row.total_cost)}</td>
            <td class="num">${formatAmount(row.profit)}</td>
            <td class="num">${row.invoice_count}</td>
        </tr>
    `).join('');
}

function formatDisplayDate(value) {
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleString(undefined, {
        year: 'numeric', month: 'short', day: '2-digit',
        hour: '2-digit', minute: '2-digit',
    });
}

/** Parse API datetime as local wall-clock (no UTC shift). */
function formatReportDateTime(value) {
    if (!value) return '—';
    const m = String(value).match(/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/);
    if (m) {
        const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]), Number(m[4]), Number(m[5]));
        return d.toLocaleString(undefined, {
            year: 'numeric', month: 'short', day: '2-digit',
            hour: '2-digit', minute: '2-digit',
        });
    }
    return formatDisplayDate(value);
}

const SALES_EMAIL_API = '/api/v1/reports/sales-dashboard/email';

function initSalesDashboardEmail() {
    document.getElementById('btn-sales-email-save')?.addEventListener('click', saveSalesEmailConfig);
    document.getElementById('btn-sales-email-test')?.addEventListener('click', sendSalesEmailTest);
    document.getElementById('btn-sales-email-now')?.addEventListener('click', sendSalesEmailNow);
    loadSalesEmailStatus();
}

function setSalesEmailError(message) {
    const el = document.getElementById('sales-email-error');
    if (!el) return;
    if (!message) {
        el.classList.add('d-none');
        el.textContent = '';
        return;
    }
    el.textContent = message;
    el.classList.remove('d-none');
}

async function loadSalesEmailStatus() {
    try {
        const status = await Api.get(`${SALES_EMAIL_API}/status`);
        const config = await Api.get(`${SALES_EMAIL_API}/config`);
        document.getElementById('sales-email-recipients').value = (config.recipients || '').replace(/, /g, ',');
        document.getElementById('sales-email-interval').value = config.interval_minutes || 30;
        document.getElementById('sales-email-preset').value = config.date_preset || 'this-month';
        document.getElementById('sales-email-enabled').checked = !!config.enabled;

        const badge = document.getElementById('sales-email-status-badge');
        if (!status.smtp_configured) {
            badge.className = 'badge bg-danger';
            badge.textContent = 'SMTP not configured';
        } else if (config.enabled) {
            badge.className = 'badge bg-success';
            badge.textContent = `On — every ${config.interval_minutes} min`;
        } else {
            badge.className = 'badge bg-secondary';
            badge.textContent = 'Off';
        }

        const meta = [];
        if (status.last_email_at) meta.push(`Last email: ${formatDisplayDate(status.last_email_at)}`);
        if (status.next_check_at && config.enabled) meta.push(`Next check: ${formatDisplayDate(status.next_check_at)}`);
        if (status.last_check_message) meta.push(status.last_check_message);
        if (status.last_error) meta.push(`Error: ${status.last_error}`);
        document.getElementById('sales-email-meta').textContent = meta.join(' · ') || 'No emails sent yet.';
        setSalesEmailError(status.smtp_configured ? '' : 'Set SMTP_ENABLED=true in .env and restart the app.');
    } catch (err) {
        setSalesEmailError(err.message || 'Could not load email settings.');
    }
}

function salesEmailPayload() {
    return {
        enabled: document.getElementById('sales-email-enabled').checked,
        recipients: document.getElementById('sales-email-recipients').value.trim(),
        interval_minutes: Number(document.getElementById('sales-email-interval').value) || 30,
        date_preset: document.getElementById('sales-email-preset').value,
        email_subject: 'Sales Dashboard — Month-over-Month',
    };
}

async function saveSalesEmailConfig() {
    setSalesEmailError('');
    try {
        await Api.put(`${SALES_EMAIL_API}/config`, salesEmailPayload());
        await loadSalesEmailStatus();
        alert('Email schedule saved.');
    } catch (err) {
        setSalesEmailError(err.message || 'Save failed.');
    }
}

async function sendSalesEmailTest() {
    const email = document.getElementById('sales-email-recipients').value.split(',')[0]?.trim();
    if (!email) {
        setSalesEmailError('Enter your email address first.');
        return;
    }
    setSalesEmailError('');
    try {
        const result = await Api.post(`${SALES_EMAIL_API}/test`, { to_email: email });
        await loadSalesEmailStatus();
        alert(result.message || 'Test email sent.');
    } catch (err) {
        setSalesEmailError(err.message || 'Test email failed.');
    }
}

async function sendSalesEmailNow() {
    setSalesEmailError('');
    try {
        const result = await Api.post(`${SALES_EMAIL_API}/run-now`, {});
        await loadSalesEmailStatus();
        alert(result.message || 'Done.');
    } catch (err) {
        setSalesEmailError(err.message || 'Send failed.');
    }
}
