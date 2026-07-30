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

function pad(n) {
    return String(n).padStart(2, '0');
}

function toLocalInput(d) {
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function applyPreset(preset, reload = true) {
    const now = new Date();
    let start;
    let end;

    if (preset === 'this-month') {
        start = new Date(now.getFullYear(), now.getMonth(), 1, 6, 0, 0);
        end = new Date(now);
    } else if (preset === 'last-month') {
        start = new Date(now.getFullYear(), now.getMonth() - 1, 1, 6, 0, 0);
        end = new Date(now.getFullYear(), now.getMonth(), 0, 23, 59, 59);
    } else if (preset === 'last-7') {
        end = new Date(now);
        start = new Date(end);
        start.setDate(start.getDate() - 7);
        start.setHours(6, 0, 0, 0);
    } else if (preset === 'last-30') {
        end = new Date(now);
        start = new Date(end);
        start.setDate(start.getDate() - 30);
        start.setHours(6, 0, 0, 0);
    } else {
        return;
    }

    document.getElementById('sales-date-from').value = toLocalInput(start);
    document.getElementById('sales-date-to').value = toLocalInput(end);

    document.querySelectorAll('.preset-btn').forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.preset === preset);
    });

    if (reload) loadAll();
}

function extendRangeToNow() {
    const activePreset = document.querySelector('.preset-btn.active')?.dataset.preset;
    if (activePreset === 'this-month' || activePreset === 'last-7' || activePreset === 'last-30') {
        document.getElementById('sales-date-to').value = toLocalInput(new Date());
    }
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
        const [summary, trend, topInvoices] = await Promise.all([
            Api.get(`${SALES_API}/summary?${params}`),
            Api.get(`${SALES_API}/daily-trend?${params}`),
            Api.get(`${SALES_API}/top-invoices?${params}&limit=10`),
        ]);
        renderSummary(summary);
        renderTrendChart(trend);
        renderTopInvoices(topInvoices);
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
        `${formatDisplayDate(current.start_date)} → ${formatDisplayDate(current.end_date)}`;
    document.getElementById('sales-total-days').textContent =
        `${current.total_days} day${current.total_days === 1 ? '' : 's'}`;
    document.getElementById('sales-compare-period-text').textContent =
        `Compared with last month: ${formatDisplayDate(previous.start_date)} → ${formatDisplayDate(previous.end_date)}`;

    renderCompareLine('cmp-total-sale', data.total_sale, false);
    renderCompareLine('cmp-total-cost', data.total_cost, true);
    renderCompareLine('cmp-profit', data.profit, false);
    renderCompareLine('cmp-avg-sale', data.avg_sale_per_day, false);
    renderCompareLine('cmp-profit-pct', data.profit_percent, false, true);
    renderCompareTable(data);
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

function dayOfMonth(dateStr) {
    return new Date(dateStr).getDate();
}

function renderTrendChart(trend) {
    const canvas = document.getElementById('sales-trend-chart');
    if (!canvas || typeof Chart === 'undefined') return;

    const currentMap = new Map(trend.current.map((p) => [dayOfMonth(p.sale_date), p.total_sale]));
    const previousMap = new Map(trend.previous.map((p) => [dayOfMonth(p.sale_date), p.total_sale]));
    const days = [...new Set([...currentMap.keys(), ...previousMap.keys()])].sort((a, b) => a - b);

    const labels = days.map((d) => `Day ${d}`);
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

function formatDisplayDate(value) {
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleString(undefined, {
        year: 'numeric', month: 'short', day: '2-digit',
        hour: '2-digit', minute: '2-digit',
    });
}
