/** Role Management — create / edit / clone / delete custom roles + permissions. */

(() => {
    let roles = [];
    let permissions = [];
    let canManage = false;
    let roleModal;
    let cloneModal;
    let editingId = null;

    const tbody = () => document.getElementById('roles-table-body');

    function esc(s) {
        return String(s ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function showAlert(msg, type = 'success') {
        Auth.showAlert('roles-alert', msg, type);
    }

    function moduleKey(code) {
        const i = String(code || '').indexOf('.');
        return i > 0 ? code.slice(0, i) : 'other';
    }

    function renderPermissions(selectedIds = []) {
        const selected = new Set((selectedIds || []).map(Number));
        const q = (document.getElementById('perm-search').value || '').trim().toLowerCase();
        const groups = {};
        permissions.forEach((p) => {
            const hay = `${p.permission_code} ${p.permission_name} ${p.description || ''}`.toLowerCase();
            if (q && !hay.includes(q)) return;
            const key = moduleKey(p.permission_code);
            if (!groups[key]) groups[key] = [];
            groups[key].push(p);
        });

        const root = document.getElementById('role-permissions');
        const keys = Object.keys(groups).sort();
        if (!keys.length) {
            root.innerHTML = '<div class="text-muted small">No permissions match.</div>';
            return;
        }
        root.innerHTML = keys.map((key) => `
            <div class="role-perm-group" data-group="${esc(key)}">
                <h6>${esc(key)}</h6>
                ${groups[key].map((p) => `
                    <div class="form-check role-perm-item">
                        <input class="form-check-input role-perm-cb" type="checkbox"
                               id="perm-${p.permission_id}" value="${p.permission_id}"
                               ${selected.has(Number(p.permission_id)) ? 'checked' : ''}>
                        <label class="form-check-label" for="perm-${p.permission_id}">
                            <code>${esc(p.permission_code)}</code>
                            <span class="text-muted">— ${esc(p.permission_name)}</span>
                        </label>
                    </div>
                `).join('')}
            </div>
        `).join('');
    }

    function selectedPermissionIds() {
        return [...document.querySelectorAll('.role-perm-cb:checked')].map((el) => Number(el.value));
    }

    function filteredRoles() {
        const q = (document.getElementById('role-search').value || '').trim().toLowerCase();
        if (!q) return roles;
        return roles.filter((r) =>
            `${r.role_code} ${r.role_name} ${r.description || ''}`.toLowerCase().includes(q)
        );
    }

    function renderTable() {
        const list = filteredRoles();
        document.getElementById('roles-count').textContent = `${list.length} role(s)`;
        if (!list.length) {
            tbody().innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">No roles found.</td></tr>';
            return;
        }
        tbody().innerHTML = list.map((r) => {
            const typeBadge = r.is_system_role
                ? '<span class="badge bg-info">System</span>'
                : '<span class="badge bg-secondary">Custom</span>';
            const statusBadge = r.is_active
                ? '<span class="badge bg-success">Active</span>'
                : '<span class="badge bg-danger">Inactive</span>';
            const manageBtns = canManage ? `
                <button type="button" class="btn btn-sm btn-outline-primary" data-edit="${r.role_id}">Edit</button>
                <button type="button" class="btn btn-sm btn-outline-secondary" data-clone="${r.role_id}">Clone</button>
                ${(!r.is_system_role && r.role_code !== 'SUPER_ADMIN')
                    ? `<button type="button" class="btn btn-sm btn-outline-danger" data-del="${r.role_id}">Delete</button>`
                    : ''}
            ` : '';
            return `
                <tr>
                    <td><code>${esc(r.role_code)}</code></td>
                    <td>${esc(r.role_name)}</td>
                    <td class="text-muted">${esc(r.description || '—')}</td>
                    <td>${typeBadge}</td>
                    <td>${statusBadge}</td>
                    <td class="text-end text-nowrap">
                        <a class="btn btn-sm btn-outline-dark" href="/admin/menu-access?role_id=${r.role_id}" title="Main panel menus">
                            Menus
                        </a>
                        ${manageBtns}
                    </td>
                </tr>
            `;
        }).join('');

        tbody().querySelectorAll('[data-edit]').forEach((btn) => {
            btn.addEventListener('click', () => openEdit(Number(btn.dataset.edit)));
        });
        tbody().querySelectorAll('[data-clone]').forEach((btn) => {
            btn.addEventListener('click', () => openClone(Number(btn.dataset.clone)));
        });
        tbody().querySelectorAll('[data-del]').forEach((btn) => {
            btn.addEventListener('click', () => deleteRole(Number(btn.dataset.del)));
        });
    }

    function resetFormError() {
        const el = document.getElementById('role-form-error');
        el.classList.add('d-none');
        el.textContent = '';
    }

    function openCreate() {
        editingId = null;
        document.getElementById('roleModalTitle').textContent = 'New Role';
        document.getElementById('role-id').value = '';
        document.getElementById('role-code').value = '';
        document.getElementById('role-code').disabled = false;
        document.getElementById('role-code-group').style.display = '';
        document.getElementById('role-name').value = '';
        document.getElementById('role-description').value = '';
        document.getElementById('role-active').checked = true;
        document.getElementById('role-active-group').style.display = 'none';
        document.getElementById('perm-search').value = '';
        resetFormError();
        renderPermissions([]);
        roleModal.show();
    }

    async function openEdit(roleId) {
        try {
            const detail = await Api.get(`/api/v1/roles/${roleId}`);
            editingId = roleId;
            document.getElementById('roleModalTitle').textContent = `Edit Role — ${detail.role_name}`;
            document.getElementById('role-id').value = String(roleId);
            document.getElementById('role-code').value = detail.role_code;
            document.getElementById('role-code').disabled = true;
            document.getElementById('role-code-group').style.display = '';
            document.getElementById('role-name').value = detail.role_name || '';
            document.getElementById('role-description').value = detail.description || '';
            document.getElementById('role-active').checked = !!detail.is_active;
            document.getElementById('role-active-group').style.display =
                detail.role_code === 'SUPER_ADMIN' ? 'none' : '';
            document.getElementById('perm-search').value = '';
            resetFormError();
            renderPermissions(detail.permission_ids || []);
            roleModal.show();
        } catch (err) {
            showAlert(err.message, 'danger');
        }
    }

    function openClone(roleId) {
        const role = roles.find((r) => Number(r.role_id) === Number(roleId));
        if (!role) return;
        document.getElementById('clone-source-id').value = String(roleId);
        document.getElementById('clone-source-label').textContent =
            `Copy permissions from ${role.role_name} (${role.role_code})`;
        document.getElementById('clone-code').value = `${role.role_code}_COPY`;
        document.getElementById('clone-name').value = `${role.role_name} (Copy)`;
        document.getElementById('clone-form-error').classList.add('d-none');
        cloneModal.show();
    }

    async function deleteRole(roleId) {
        const role = roles.find((r) => Number(r.role_id) === Number(roleId));
        if (!role) return;
        if (!window.confirm(`Delete custom role "${role.role_name}"?\nUsers with only this role will lose its permissions.`)) {
            return;
        }
        try {
            await Api.delete(`/api/v1/roles/${roleId}`);
            showAlert(`Role ${role.role_code} deleted.`, 'success');
            await loadRoles();
        } catch (err) {
            showAlert(err.message, 'danger');
        }
    }

    async function saveRole(e) {
        e.preventDefault();
        resetFormError();
        const payload = {
            role_name: document.getElementById('role-name').value.trim(),
            description: document.getElementById('role-description').value.trim(),
            permission_ids: selectedPermissionIds(),
        };
        try {
            if (editingId) {
                payload.is_active = document.getElementById('role-active').checked;
                await Api.put(`/api/v1/roles/${editingId}`, payload);
                showAlert('Role updated. Users must re-login to refresh rights.', 'success');
            } else {
                payload.role_code = document.getElementById('role-code').value.trim();
                await Api.post('/api/v1/roles/', payload);
                showAlert('Role created. Assign it to users on the Users page.', 'success');
            }
            roleModal.hide();
            await loadRoles();
        } catch (err) {
            const el = document.getElementById('role-form-error');
            el.textContent = err.message;
            el.classList.remove('d-none');
        }
    }

    async function saveClone(e) {
        e.preventDefault();
        const sourceId = Number(document.getElementById('clone-source-id').value);
        const errEl = document.getElementById('clone-form-error');
        errEl.classList.add('d-none');
        try {
            await Api.post(`/api/v1/roles/${sourceId}/clone`, {
                role_code: document.getElementById('clone-code').value.trim(),
                role_name: document.getElementById('clone-name').value.trim(),
            });
            cloneModal.hide();
            showAlert('Role cloned successfully.', 'success');
            await loadRoles();
        } catch (err) {
            errEl.textContent = err.message;
            errEl.classList.remove('d-none');
        }
    }

    async function loadRoles() {
        roles = await Api.get('/api/v1/roles/');
        renderTable();
    }

    async function loadPermissions() {
        try {
            permissions = await Api.get('/api/v1/permissions/');
        } catch (_) {
            permissions = [];
        }
    }

    document.addEventListener('DOMContentLoaded', async () => {
        await Auth.requireAuth();
        if (!Auth.hasPermission('auth.roles.view')) {
            Auth.showAlert('roles-alert', 'You do not have permission to view roles.', 'warning');
            return;
        }
        canManage = Auth.hasPermission('auth.roles.manage');
        roleModal = new bootstrap.Modal(document.getElementById('roleModal'));
        cloneModal = new bootstrap.Modal(document.getElementById('cloneModal'));

        document.getElementById('btn-create-role')?.addEventListener('click', openCreate);
        document.getElementById('roleForm').addEventListener('submit', saveRole);
        document.getElementById('cloneForm').addEventListener('submit', saveClone);
        document.getElementById('role-search').addEventListener('input', renderTable);
        document.getElementById('perm-search').addEventListener('input', () => {
            renderPermissions(selectedPermissionIds());
        });
        document.getElementById('btn-perm-all').addEventListener('click', () => {
            document.querySelectorAll('.role-perm-cb').forEach((cb) => { cb.checked = true; });
        });
        document.getElementById('btn-perm-none').addEventListener('click', () => {
            document.querySelectorAll('.role-perm-cb').forEach((cb) => { cb.checked = false; });
        });
        document.getElementById('btn-perm-view-only').addEventListener('click', () => {
            document.querySelectorAll('.role-perm-cb').forEach((cb) => {
                const label = cb.parentElement?.querySelector('code')?.textContent || '';
                cb.checked = label.endsWith('.view') || label.includes('.view.') || /\.view$/.test(label);
            });
        });

        if (!canManage) {
            document.getElementById('btn-create-role')?.classList.add('d-none');
        }

        try {
            await Promise.all([loadRoles(), loadPermissions()]);
        } catch (err) {
            showAlert(err.message, 'danger');
        }
    });
})();
