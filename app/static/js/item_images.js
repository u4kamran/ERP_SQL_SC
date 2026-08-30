const IIMG_API = '/api/v1/inventory/item-images';

let page = 1;
let pageSize = 25;
let selectedItemId = null;
let activeJobId = null;
let jobTimer = null;
let settingsCache = {};

document.addEventListener('DOMContentLoaded', async () => {
  const profile = await Auth.requireAuth();
  if (!profile) return;
  if (!Auth.hasPermission('inventory.item_images.view')) {
    Auth.showAlert('iimg-alert', 'No permission to view item images.', 'warning');
    return;
  }
  if (!Auth.hasPermission('inventory.item_images.manage')) {
    document.querySelectorAll('#btn-settings, #settings-form input, #settings-form button').forEach((el) => {
      el.disabled = true;
    });
  }
  if (!Auth.hasPermission('inventory.item_images.bulk')) {
    const bulk = document.getElementById('btn-bulk');
    if (bulk) bulk.disabled = true;
  }

  document.getElementById('btn-refresh').addEventListener('click', () => refreshAll());
  document.getElementById('btn-filter').addEventListener('click', () => { page = 1; loadItems(); });
  document.getElementById('btn-prev').addEventListener('click', () => { if (page > 1) { page -= 1; loadItems(); } });
  document.getElementById('btn-next').addEventListener('click', () => { page += 1; loadItems(); });
  document.getElementById('chk-all').addEventListener('change', (e) => {
    document.querySelectorAll('.chk-item').forEach((c) => { c.checked = e.target.checked; });
  });
  document.getElementById('btn-settings').addEventListener('click', openSettings);
  document.getElementById('settings-form').addEventListener('submit', saveSettings);
  document.getElementById('btn-bulk').addEventListener('click', () => {
    new bootstrap.Modal(document.getElementById('bulkModal')).show();
  });
  document.getElementById('bulk-scope').addEventListener('change', (e) => {
    document.getElementById('test-limit-wrap').hidden = e.target.value !== 'test';
  });
  document.getElementById('bulk-form').addEventListener('submit', startBulk);
  document.getElementById('btn-job-pause').addEventListener('click', () => controlJob('pause'));
  document.getElementById('btn-job-resume').addEventListener('click', () => controlJob('resume'));
  document.getElementById('btn-job-cancel').addEventListener('click', () => controlJob('cancel'));

  await refreshAll();
  pollJob();

  const pending = sessionStorage.getItem('iimg_open_item');
  if (pending) {
    sessionStorage.removeItem('iimg_open_item');
    const id = Number(pending);
    if (id) openDetail(id);
  }
});

async function refreshAll() {
  await Promise.all([loadDashboard(), loadItems(), loadActiveJob()]);
}

async function loadDashboard() {
  try {
    const d = await Api.get(`${IIMG_API}/dashboard`);
    document.getElementById('d-total').textContent = fmt(d.total_items);
    document.getElementById('d-approved').textContent = fmt(d.approved);
    document.getElementById('d-review').textContent = fmt(d.needs_review);
    document.getElementById('d-coverage').textContent = `${d.coverage_pct ?? 0}%`;
  } catch (error) {
    Auth.showAlert('iimg-alert', error.message || 'Dashboard failed. Run setup_item_images.py?', 'danger');
  }
}

async function loadItems() {
  const q = document.getElementById('filter-q').value.trim();
  const status = document.getElementById('filter-status').value;
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize), status });
  if (q) params.set('q', q);
  try {
    const data = await Api.get(`${IIMG_API}/items?${params}`);
    const body = document.getElementById('items-body');
    const rows = data.items || [];
    body.innerHTML = rows.length ? rows.map(renderRow).join('') : '<tr><td colspan="7" class="text-muted">No items.</td></tr>';
    body.querySelectorAll('[data-open]').forEach((btn) => {
      btn.addEventListener('click', () => openDetail(Number(btn.getAttribute('data-open'))));
    });
    document.getElementById('page-info').textContent =
      `Page ${data.page} · ${fmt(data.total)} items`;
    document.getElementById('btn-next').disabled = !data.has_more;
    document.getElementById('btn-prev').disabled = page <= 1;
  } catch (error) {
    Auth.showAlert('iimg-alert', error.message || 'Failed to load items.', 'danger');
  }
}

function renderRow(row) {
  const thumb = row.preview_url
    ? `<img class="iimg-thumb" src="${escAttr(row.preview_url)}" alt="">`
    : '<div class="iimg-thumb d-flex align-items-center justify-content-center text-muted small">—</div>';
  const st = row.image_status || 'NO_IMAGE';
  return `
    <tr>
      <td><input type="checkbox" class="chk-item" value="${escAttr(row.item_id)}"></td>
      <td>${thumb}</td>
      <td>
        <div class="fw-semibold">${esc(row.item_title || '')}</div>
        <div class="small text-muted">ID ${esc(String(row.item_id))} · Manual ${esc(String(row.manual_id ?? ''))}</div>
      </td>
      <td class="small">${esc(row.barcodeid || '')}</td>
      <td><span class="iimg-badge ${escAttr(st)}">${esc(st)}</span></td>
      <td>${row.match_score != null ? esc(String(row.match_score)) : '—'}</td>
      <td><button type="button" class="btn btn-sm btn-outline-primary" data-open="${escAttr(row.item_id)}">Open</button></td>
    </tr>`;
}

async function openDetail(itemId) {
  selectedItemId = itemId;
  const el = document.getElementById('detail-body');
  el.innerHTML = '<p class="text-muted">Loading…</p>';
  try {
    const data = await Api.get(`${IIMG_API}/items/${itemId}`);
    renderDetail(data);
  } catch (error) {
    el.innerHTML = `<p class="text-danger">${esc(error.message || 'Failed')}</p>`;
  }
}

function renderDetail(data) {
  const item = data.item || {};
  const st = (data.status && data.status.status) || 'NO_IMAGE';
  const images = data.images || [];
  const cands = data.candidates || [];
  const primary = images.find((i) => i.is_primary) || images[0];
  const preview = primary
    ? `<img class="iimg-thumb-lg mb-2" src="${escAttr(primary.preview_url || primary.image_url || '')}" alt="">`
    : '<div class="iimg-thumb-lg mb-2 d-flex align-items-center justify-content-center text-muted">No image</div>';

  let html = `
    <div class="d-flex gap-3 mb-3">
      ${preview}
      <div>
        <div class="fw-semibold">${esc(item.item_title || '')}</div>
        <div class="small text-muted">Barcode: ${esc(item.barcodeid || '—')}</div>
        <div class="small text-muted">Brand: ${esc(item.brand || '—')}</div>
        <div class="mt-1"><span class="iimg-badge ${escAttr(st)}">${esc(st)}</span></div>
      </div>
    </div>
    <div class="d-flex flex-wrap gap-1 mb-3">
      <button type="button" class="btn btn-sm btn-primary" id="btn-search">Search</button>
      <button type="button" class="btn btn-sm btn-outline-primary" id="btn-search-again">Search Again</button>
      <button type="button" class="btn btn-sm btn-outline-secondary" id="btn-dry">Dry Run</button>
      <label class="btn btn-sm btn-outline-success mb-0">
        Upload<input type="file" id="file-upload" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" hidden>
      </label>
    </div>
    <h6 class="small text-uppercase text-muted">Candidates</h6>
    <div id="cand-list">`;

  if (!cands.length) {
    html += '<p class="text-muted small">No candidates yet.</p>';
  } else {
    html += cands.map((c) => `
      <div class="iimg-cand">
        <div class="d-flex gap-2">
          <img class="iimg-thumb" src="${escAttr(c.image_url)}" alt="">
          <div class="flex-grow-1">
            <div class="small fw-semibold">${esc(c.product_title || 'Untitled')}</div>
            <div class="small text-muted">${esc(c.source_name || '')} · score ${esc(String(c.match_score ?? 0))}</div>
            <div class="small text-truncate">${esc(c.source_url || '')}</div>
            <div class="mt-1 d-flex flex-wrap gap-1">
              <button type="button" class="btn btn-sm btn-success" data-use="${c.candidate_id}">Use This Image</button>
              <button type="button" class="btn btn-sm btn-outline-danger" data-reject="${c.candidate_id}">Reject</button>
              ${c.source_url ? `<a class="btn btn-sm btn-outline-secondary" href="${escAttr(c.source_url)}" target="_blank" rel="noopener">Open Source</a>` : ''}
            </div>
          </div>
        </div>
      </div>`).join('');
  }
  html += '</div>';

  if (images.length) {
    html += '<h6 class="small text-uppercase text-muted mt-3">Linked images</h6>';
    html += images.map((img) => `
      <div class="d-flex align-items-center gap-2 mb-2">
        <img class="iimg-thumb" src="${escAttr(img.preview_url || img.image_url || '')}" alt="">
        <div class="small flex-grow-1">
          ${esc(img.source_name || '')} · ${esc(img.status || '')}
          ${img.is_primary ? ' · primary' : ''}
        </div>
        ${img.status !== 'APPROVED' ? `<button type="button" class="btn btn-sm btn-outline-success" data-approve="${img.image_id}">Approve</button>` : ''}
        <button type="button" class="btn btn-sm btn-outline-danger" data-del="${img.image_id}">Delete</button>
      </div>`).join('');
  }

  document.getElementById('detail-body').innerHTML = html;

  document.getElementById('btn-search')?.addEventListener('click', () => runSearch(false, false));
  document.getElementById('btn-search-again')?.addEventListener('click', () => runSearch(true, false));
  document.getElementById('btn-dry')?.addEventListener('click', () => runSearch(true, true));
  document.getElementById('file-upload')?.addEventListener('change', uploadFile);
  document.querySelectorAll('[data-use]').forEach((b) => b.addEventListener('click', () => useCand(b.getAttribute('data-use'))));
  document.querySelectorAll('[data-reject]').forEach((b) => b.addEventListener('click', () => rejectCand(b.getAttribute('data-reject'))));
  document.querySelectorAll('[data-approve]').forEach((b) => b.addEventListener('click', () => approveImg(b.getAttribute('data-approve'))));
  document.querySelectorAll('[data-del]').forEach((b) => b.addEventListener('click', () => deleteImg(b.getAttribute('data-del'))));
}

async function runSearch(force, dryRun) {
  if (!selectedItemId) return;
  try {
    Auth.showAlert('iimg-alert', dryRun ? 'Dry run searching…' : 'Searching…', 'info');
    const params = new URLSearchParams({ force: force ? 'true' : 'false', dry_run: dryRun ? 'true' : 'false' });
    const data = await Api.post(`${IIMG_API}/items/${selectedItemId}/search?${params}`, {});
    if (dryRun) {
      const cands = data.candidates || [];
      Auth.showAlert('iimg-alert', `Dry run: ${cands.length} candidate(s), best score ${data.best_score ?? 0}. Not saved.`, 'success');
      const fake = {
        item: (await Api.get(`${IIMG_API}/items/${selectedItemId}`)).item,
        status: { status: 'NO_IMAGE' },
        images: [],
        candidates: cands.map((c, i) => ({ ...c, candidate_id: `dry-${i}` })),
      };
      // Dry-run candidates are not persisted — show inline without use buttons
      const el = document.getElementById('detail-body');
      renderDetail({
        item: fake.item,
        status: { status: 'DRY_RUN' },
        images: [],
        candidates: [],
      });
      const list = document.getElementById('cand-list');
      if (list) {
        list.innerHTML = cands.length
          ? cands.map((c) => `
              <div class="iimg-cand">
                <div class="d-flex gap-2">
                  <img class="iimg-thumb" src="${escAttr(c.image_url)}" alt="">
                  <div>
                    <div class="small fw-semibold">${esc(c.product_title || '')}</div>
                    <div class="small text-muted">${esc(c.source_name || '')} · ${esc(String(c.match_score ?? 0))}</div>
                    ${c.source_url ? `<a class="small" href="${escAttr(c.source_url)}" target="_blank" rel="noopener">Open Source</a>` : ''}
                  </div>
                </div>
              </div>`).join('')
          : '<p class="text-muted small">No candidates.</p>';
      }
    } else {
      Auth.showAlert('iimg-alert', data.skipped ? data.reason : (data.found ? `Found · decision ${data.decision}` : (data.hint || 'No image found')), data.found || data.skipped ? 'success' : 'warning');
      renderDetail(data.detail || await Api.get(`${IIMG_API}/items/${selectedItemId}`));
      await loadItems();
      await loadDashboard();
    }
  } catch (error) {
    Auth.showAlert('iimg-alert', error.message || 'Search failed.', 'danger');
  }
}

async function useCand(id) {
  try {
    const data = await Api.post(`${IIMG_API}/candidates/${id}/use?approve=true`, {});
    Auth.showAlert('iimg-alert', 'Image linked and approved.', 'success');
    renderDetail(data);
    await loadItems();
    await loadDashboard();
  } catch (error) {
    Auth.showAlert('iimg-alert', error.message || 'Failed.', 'danger');
  }
}

async function rejectCand(id) {
  try {
    const data = await Api.post(`${IIMG_API}/candidates/${id}/reject`, {});
    renderDetail(data);
  } catch (error) {
    Auth.showAlert('iimg-alert', error.message || 'Failed.', 'danger');
  }
}

async function approveImg(id) {
  try {
    const data = await Api.post(`${IIMG_API}/images/${id}/approve`, {});
    Auth.showAlert('iimg-alert', 'Image approved.', 'success');
    renderDetail(data);
    await loadItems();
    await loadDashboard();
  } catch (error) {
    Auth.showAlert('iimg-alert', error.message || 'Failed.', 'danger');
  }
}

async function deleteImg(id) {
  if (!confirm('Delete this image link?')) return;
  try {
    const data = await Api.delete(`${IIMG_API}/images/${id}`);
    Auth.showAlert('iimg-alert', 'Image deleted.', 'success');
    renderDetail(data);
    await loadItems();
    await loadDashboard();
  } catch (error) {
    Auth.showAlert('iimg-alert', error.message || 'Failed.', 'danger');
  }
}

async function uploadFile(ev) {
  const file = ev.target.files && ev.target.files[0];
  if (!file || !selectedItemId) return;
  try {
    const fd = new FormData();
    fd.append('file', file);
    const data = await Api.upload(`${IIMG_API}/items/${selectedItemId}/upload`, fd);
    Auth.showAlert('iimg-alert', 'Manual image uploaded.', 'success');
    renderDetail(data);
    await loadItems();
    await loadDashboard();
  } catch (error) {
    Auth.showAlert('iimg-alert', error.message || 'Upload failed.', 'danger');
  } finally {
    ev.target.value = '';
  }
}

async function openSettings() {
  try {
    const data = await Api.get(`${IIMG_API}/settings`);
    settingsCache = data.settings || {};
    for (const key of [
      'auto_accept_min', 'review_min', 'no_match_min', 'requests_per_minute', 'max_concurrent',
      'timeout_seconds', 'retry_count',
    ]) {
      document.getElementById(key).value = settingsCache[key] ?? '';
    }
    for (const key of [
      'download_enabled', 'naheed_enabled', 'metro_enabled', 'carrefour_enabled',
      'imtiaz_enabled', 'alfatah_enabled', 'open_food_facts_enabled', 'upcitemdb_enabled',
    ]) {
      const el = document.getElementById(key);
      if (el) el.checked = !!settingsCache[key];
    }
    new bootstrap.Modal(document.getElementById('settingsModal')).show();
  } catch (error) {
    Auth.showAlert('iimg-alert', error.message || 'Settings load failed.', 'danger');
  }
}

async function saveSettings(ev) {
  ev.preventDefault();
  try {
    await Api.put(`${IIMG_API}/settings`, {
      auto_accept_min: Number(document.getElementById('auto_accept_min').value),
      review_min: Number(document.getElementById('review_min').value),
      no_match_min: Number(document.getElementById('no_match_min').value),
      requests_per_minute: Number(document.getElementById('requests_per_minute').value),
      max_concurrent: Number(document.getElementById('max_concurrent').value),
      timeout_seconds: Number(document.getElementById('timeout_seconds').value),
      retry_count: Number(document.getElementById('retry_count').value),
      download_enabled: document.getElementById('download_enabled').checked,
      naheed_enabled: document.getElementById('naheed_enabled').checked,
      metro_enabled: document.getElementById('metro_enabled').checked,
      carrefour_enabled: document.getElementById('carrefour_enabled').checked,
      imtiaz_enabled: document.getElementById('imtiaz_enabled').checked,
      alfatah_enabled: document.getElementById('alfatah_enabled').checked,
      open_food_facts_enabled: document.getElementById('open_food_facts_enabled').checked,
      upcitemdb_enabled: document.getElementById('upcitemdb_enabled').checked,
    });
    bootstrap.Modal.getInstance(document.getElementById('settingsModal'))?.hide();
    Auth.showAlert('iimg-alert', 'Settings saved.', 'success');
  } catch (error) {
    Auth.showAlert('iimg-alert', error.message || 'Save failed.', 'danger');
  }
}

async function startBulk(ev) {
  ev.preventDefault();
  const scope = document.getElementById('bulk-scope').value;
  const dry_run = document.getElementById('bulk-dry-run').checked;
  const payload = {
    scope,
    dry_run,
    status_filter: document.getElementById('filter-status').value,
    q: document.getElementById('filter-q').value.trim() || null,
    selected_item_ids: [...document.querySelectorAll('.chk-item:checked')].map((c) => Number(c.value)),
  };
  if (scope === 'test') {
    payload.test_limit = Number(document.getElementById('bulk-test-limit').value);
  }
  try {
    const data = await Api.post(`${IIMG_API}/jobs/bulk`, payload);
    bootstrap.Modal.getInstance(document.getElementById('bulkModal'))?.hide();
    activeJobId = data.job?.job_id;
    Auth.showAlert('iimg-alert', `Job ${activeJobId} started (${data.job?.total_count || 0} items).`, 'success');
    showJob(data.job);
    pollJob();
  } catch (error) {
    Auth.showAlert('iimg-alert', error.message || 'Bulk start failed.', 'danger');
  }
}

async function loadActiveJob() {
  try {
    const data = await Api.get(`${IIMG_API}/jobs/active`);
    if (data.job) {
      activeJobId = data.job.job_id;
      showJob(data.job);
    } else {
      document.getElementById('job-card').hidden = true;
    }
  } catch (_) {
    /* tables may be missing before setup */
  }
}

function showJob(job) {
  if (!job) return;
  document.getElementById('job-card').hidden = false;
  document.getElementById('job-progress').textContent =
    `Processed: ${job.processed_count || 0} / ${job.total_count || 0} (${job.status})`;
  document.getElementById('job-counts').textContent =
    `Found ${job.found_count || 0} · Approved ${job.approved_count || 0} · Review ${job.review_count || 0} · Not found ${job.not_found_count || 0} · Failed ${job.failed_count || 0}`;
}

function pollJob() {
  if (jobTimer) clearInterval(jobTimer);
  jobTimer = setInterval(async () => {
    if (!activeJobId) return;
    try {
      const data = await Api.get(`${IIMG_API}/jobs/${activeJobId}`);
      showJob(data.job);
      if (['COMPLETED', 'CANCELLED', 'FAILED'].includes(data.job?.status)) {
        activeJobId = null;
        await loadDashboard();
        await loadItems();
      }
    } catch (_) { /* ignore */ }
  }, 2000);
}

async function controlJob(action) {
  if (!activeJobId) return;
  try {
    const data = await Api.post(`${IIMG_API}/jobs/${activeJobId}/control`, { action });
    showJob(data.job);
  } catch (error) {
    Auth.showAlert('iimg-alert', error.message || 'Job control failed.', 'danger');
  }
}

function esc(v) {
  return String(v ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function escAttr(v) {
  return esc(v).replace(/'/g, '&#39;');
}

function fmt(n) {
  return Number(n || 0).toLocaleString();
}
