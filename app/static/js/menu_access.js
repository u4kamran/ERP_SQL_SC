/** Admin Menu Access — View / Add / Edit / Delete per sidebar menu. */

(() => {
    let roles = [];
    let selectedRoleId = null;
    let catalog = null;
    let canManage = false;

    const rolesEl = () => document.getElementById('menu-access-roles');
    const groupsEl = () => document.getElementById('menu-access-groups');
    const titleEl = () => document.getElementById('menu-access-role-title');
    const subEl = () => document.getElementById('menu-access-role-sub');
    const saveBtn = () => document.getElementById('btn-menu-save');
    const checkAllBtn = () => document.getElementById('btn-menu-check-all');
    const clearAllBtn = () => document.getElementById('btn-menu-clear-all');

    function showAlert(message, type = 'danger') {
        Auth.showAlert('menu-access-alert', message, type);
    }

    function setToolbarEnabled(enabled) {
        const on = !!enabled && canManage && selectedRoleId;
        saveBtn().disabled = !on;
        checkAllBtn().disabled = !on;
        clearAllBtn().disabled = !on;
    }

    function renderRoles() {
        const el = rolesEl();
        if (!roles.length) {
            el.innerHTML = '<div class="list-group-item text-muted">No roles found.</div>';
            return;
        }
        el.innerHTML = roles.map((role) => {
            const active = Number(role.role_id) === Number(selectedRoleId) ? ' active' : '';
            const badge = role.is_system_role
                ? '<span class="badge bg-info ms-1">System</span>'
                : '';
            return `
                <button type="button"
                        class="list-group-item list-group-item-action d-flex justify-content-between align-items-center${active}"
                        data-role-id="${role.role_id}">
                    <span>
                        <strong>${escapeHtml(role.role_name)}</strong>
                        <div class="small opacity-75"><code>${escapeHtml(role.role_code)}</code>${badge}</div>
                    </span>
                    <i class="bi bi-chevron-right"></i>
                </button>
            `;
        }).join('');

        el.querySelectorAll('[data-role-id]').forEach((btn) => {
            btn.addEventListener('click', () => {
                selectedRoleId = Number(btn.getAttribute('data-role-id'));
                renderRoles();
                loadCatalog(selectedRoleId);
            });
        });
    }

    function escapeHtml(value) {
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function actionCell(item, actionKey) {
        const actions = item.actions || [];
        const a = actions.find((x) => x.action === actionKey);
        if (!a) {
            return '<td class="text-center text-muted">—</td>';
        }
        const disabled = !a.permission_found || !canManage;
        const checked = a.granted ? 'checked' : '';
        const title = a.permission_found
            ? a.permission_code
            : `${a.permission_code} (not seeded)`;
        return `
            <td class="text-center">
                <input class="form-check-input menu-access-check"
                       type="checkbox"
                       value="${a.permission_id || ''}"
                       data-code="${escapeHtml(a.permission_code)}"
                       data-action="${escapeHtml(a.action)}"
                       data-row="${escapeHtml(item.permission_code)}"
                       title="${escapeHtml(title)}"
                       ${checked}
                       ${disabled ? 'disabled' : ''}>
            </td>
        `;
    }

    function bindActionLogic(root) {
        root.querySelectorAll('.menu-access-check').forEach((cb) => {
            cb.addEventListener('change', () => {
                const rowKey = cb.getAttribute('data-row');
                const action = cb.getAttribute('data-action');
                if (!rowKey) return;
                const rowCbs = [...root.querySelectorAll('.menu-access-check')].filter(
                    (el) => el.getAttribute('data-row') === rowKey
                );
                const viewCb = rowCbs.find((el) => el.getAttribute('data-action') === 'view');
                if (action === 'view' && !cb.checked) {
                    rowCbs.forEach((el) => {
                        if (el.getAttribute('data-action') !== 'view' && !el.disabled) {
                            el.checked = false;
                        }
                    });
                }
                if (action !== 'view' && cb.checked && viewCb && !viewCb.disabled) {
                    viewCb.checked = true;
                }
            });
        });
    }

    function renderCatalog() {
        if (!catalog) {
            groupsEl().innerHTML = '<div class="text-muted">Select a role on the left.</div>';
            titleEl().textContent = '2. Menu rights';
            subEl().textContent = 'Select a role on the left.';
            setToolbarEnabled(false);
            return;
        }

        titleEl().textContent = `2. Menu rights — ${catalog.role_name}`;
        subEl().textContent = catalog.role_code === 'SUPER_ADMIN'
            ? 'SUPER_ADMIN has full access. Rights cannot be reduced here.'
            : 'Per menu: View (show in panel), Add, Edit, Delete.';

        if (catalog.role_code === 'SUPER_ADMIN') {
            groupsEl().innerHTML = `
                <div class="alert alert-info mb-0">
                    SUPER_ADMIN includes <code>auth.admin.full</code> and already has every menu right.
                </div>`;
            setToolbarEnabled(false);
            return;
        }

        const missingNote = (catalog.missing_permissions || []).length
            ? `<div class="alert alert-warning py-2">
                    Some View permissions are missing from the database:
                    ${(catalog.missing_permissions || []).map((c) => `<code>${escapeHtml(c)}</code>`).join(', ')}
               </div>`
            : '';

        const groupsHtml = (catalog.groups || []).map((group) => {
            const rows = (group.items || []).map((item) => {
                const missingBadge = item.permission_found
                    ? ''
                    : '<span class="badge bg-warning text-dark ms-1">View not seeded</span>';
                return `
                    <tr class="${item.permission_found ? '' : 'is-missing'}">
                        <td>
                            <div class="menu-access-item-label">
                                <i class="bi ${escapeHtml(item.icon || 'bi-circle')} me-1"></i>
                                ${escapeHtml(item.label)}${missingBadge}
                            </div>
                            <div class="menu-access-item-meta">${escapeHtml(item.description || item.path)}</div>
                        </td>
                        ${actionCell(item, 'view')}
                        ${actionCell(item, 'create')}
                        ${actionCell(item, 'edit')}
                        ${actionCell(item, 'delete')}
                    </tr>
                `;
            }).join('');
            return `
                <section class="menu-access-group">
                    <h3>${escapeHtml(group.title)}</h3>
                    <div class="table-responsive">
                        <table class="table table-sm align-middle menu-access-table mb-0">
                            <thead>
                                <tr>
                                    <th>Menu</th>
                                    <th class="text-center" style="width:4.5rem">View</th>
                                    <th class="text-center" style="width:4.5rem">Add</th>
                                    <th class="text-center" style="width:4.5rem">Edit</th>
                                    <th class="text-center" style="width:4.5rem">Delete</th>
                                </tr>
                            </thead>
                            <tbody>${rows}</tbody>
                        </table>
                    </div>
                </section>
            `;
        }).join('');

        groupsEl().innerHTML = missingNote + (groupsHtml || '<div class="text-muted">No grantable menus found.</div>');
        bindActionLogic(groupsEl());
        setToolbarEnabled(canManage);
    }

    async function loadCatalog(roleId) {
        groupsEl().innerHTML = '<div class="text-muted">Loading menu rights…</div>';
        setToolbarEnabled(false);
        try {
            catalog = await Api.get(`/api/v1/roles/${roleId}/menu-access`);
            renderCatalog();
        } catch (error) {
            catalog = null;
            groupsEl().innerHTML = '';
            showAlert(error.message || 'Could not load menu rights.', 'danger');
        }
    }

    function selectedPermissionIds() {
        return Array.from(document.querySelectorAll('.menu-access-check:checked'))
            .map((el) => Number(el.value))
            .filter((id) => Number.isFinite(id) && id > 0);
    }

    function setAllChecks(checked) {
        document.querySelectorAll('.menu-access-check:not(:disabled)').forEach((el) => {
            el.checked = !!checked;
        });
    }

    async function saveRights() {
        if (!selectedRoleId || !canManage) return;
        saveBtn().disabled = true;
        try {
            const result = await Api.put(`/api/v1/roles/${selectedRoleId}/menu-access`, {
                permission_ids: selectedPermissionIds(),
            });
            showAlert(result.message || 'Menu rights saved.', 'success');
            await loadCatalog(selectedRoleId);
        } catch (error) {
            showAlert(error.message || 'Save failed.', 'danger');
            setToolbarEnabled(true);
        }
    }

    document.addEventListener('DOMContentLoaded', async () => {
        await Auth.requireAuth();
        if (!Auth.hasPermission('auth.roles.view') && !Auth.hasPermission('auth.admin.full')) {
            showAlert('You do not have permission to view menu access rights.', 'warning');
            rolesEl().innerHTML = '<div class="list-group-item text-muted">Access denied.</div>';
            return;
        }
        canManage = Auth.hasPermission('auth.roles.manage') || Auth.hasPermission('auth.admin.full');
        if (!canManage) {
            showAlert('You can view menu rights, but saving requires auth.roles.manage.', 'info');
        }

        checkAllBtn().addEventListener('click', () => setAllChecks(true));
        clearAllBtn().addEventListener('click', () => setAllChecks(false));
        saveBtn().addEventListener('click', saveRights);

        try {
            roles = await Api.get('/api/v1/roles/');
            renderRoles();
            const qsRole = Number(new URLSearchParams(location.search).get('role_id') || 0);
            const preferred = (qsRole && roles.find((r) => Number(r.role_id) === qsRole))
                || roles.find((r) => r.role_code === 'ADMIN')
                || roles.find((r) => r.role_code !== 'SUPER_ADMIN')
                || roles[0];
            if (preferred) {
                selectedRoleId = preferred.role_id;
                renderRoles();
                await loadCatalog(selectedRoleId);
            }
        } catch (error) {
            showAlert(error.message || 'Could not load roles.', 'danger');
            rolesEl().innerHTML = '<div class="list-group-item text-danger">Failed to load roles.</div>';
        }
    });
})();
