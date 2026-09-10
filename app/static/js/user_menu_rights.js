/** System Administration → User Menu Rights */

(() => {
    let users = [];
    let selectedUserId = null;
    let catalog = null;
    let dirty = false;

    const $ = (id) => document.getElementById(id);

    function alertMsg(message, type = 'danger') {
        Auth.showAlert('umr-alert', message, type);
    }

    function escapeHtml(value) {
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function setToolbar(enabled) {
        const on = !!enabled && !!selectedUserId && !(catalog && catalog.is_system_admin);
        $('btn-umr-save').disabled = !on;
        $('btn-umr-check-all').disabled = !on;
        $('btn-umr-uncheck-all').disabled = !on;
    }

    function filteredUsers() {
        const q = ($('umr-user-search').value || '').trim().toLowerCase();
        if (!q) return users;
        return users.filter((u) =>
            `${u.username} ${u.full_name}`.toLowerCase().includes(q));
    }

    function renderUserSelect() {
        const list = filteredUsers();
        const el = $('umr-user-select');
        if (!list.length) {
            el.innerHTML = '<option value="">No users found</option>';
            return;
        }
        el.innerHTML = list.map((u) => {
            const selected = Number(u.user_id) === Number(selectedUserId) ? ' selected' : '';
            const inactive = u.is_active ? '' : ' (inactive)';
            return `<option value="${u.user_id}"${selected}>${escapeHtml(u.username)} — ${escapeHtml(u.full_name)}${inactive}</option>`;
        }).join('');
    }

    function renderTree() {
        const tree = $('umr-menu-tree');
        if (!catalog) {
            tree.innerHTML = '<div class="text-muted">Select a user to load menu rights.</div>';
            setToolbar(false);
            return;
        }

        $('umr-selected-name').textContent = `${catalog.full_name} (${catalog.username})`;
        if (catalog.is_system_admin) {
            $('umr-selected-meta').textContent = 'System Administrator — full access (locked).';
            tree.innerHTML = `<div class="alert alert-info mb-0">${escapeHtml(catalog.message || 'Administrator always has full access.')}</div>`;
            setToolbar(false);
            return;
        }
        $('umr-selected-meta').textContent = 'Checked = visible. Unchecked = hidden completely.';

        const html = (catalog.groups || []).map((group) => {
            const parentId = group.parent_menu_id || '';
            const parentChecked = group.parent_can_access ? 'checked' : '';
            const parentBox = parentId
                ? `<input class="form-check-input umr-parent" type="checkbox" data-menu-id="${parentId}" ${parentChecked}>`
                : '';
            const items = (group.items || []).map((item) => `
                <label class="umr-item">
                    <input class="form-check-input umr-child" type="checkbox"
                           data-menu-id="${item.menu_id}"
                           data-parent-id="${parentId}"
                           ${item.can_access ? 'checked' : ''}>
                    <span>
                        <span class="umr-item-label">
                            <i class="bi ${escapeHtml(item.icon || 'bi-circle')} me-1"></i>
                            ${escapeHtml(item.menu_name)}
                        </span>
                        <div class="umr-item-meta">${escapeHtml(item.description || item.path || '')}</div>
                    </span>
                </label>
            `).join('');
            return `
                <section class="umr-group">
                    <div class="umr-group-title">
                        ${parentBox}
                        <span>${escapeHtml(group.title)}</span>
                    </div>
                    ${items}
                </section>
            `;
        }).join('');

        tree.innerHTML = html || '<div class="text-muted">No menus found.</div>';

        tree.querySelectorAll('.umr-parent').forEach((box) => {
            box.addEventListener('change', () => {
                dirty = true;
                const pid = box.getAttribute('data-menu-id');
                tree.querySelectorAll(`.umr-child[data-parent-id="${pid}"]`).forEach((child) => {
                    child.checked = box.checked;
                });
            });
        });
        tree.querySelectorAll('.umr-child').forEach((box) => {
            box.addEventListener('change', () => {
                dirty = true;
                const pid = box.getAttribute('data-parent-id');
                if (!pid) return;
                const parent = tree.querySelector(`.umr-parent[data-menu-id="${pid}"]`);
                if (!parent) return;
                const kids = Array.from(tree.querySelectorAll(`.umr-child[data-parent-id="${pid}"]`));
                parent.checked = kids.some((k) => k.checked);
            });
        });
        setToolbar(true);
    }

    function collectRights() {
        const rights = [];
        document.querySelectorAll('.umr-parent[data-menu-id], .umr-child[data-menu-id]').forEach((el) => {
            const menuId = Number(el.getAttribute('data-menu-id'));
            if (!menuId) return;
            rights.push({ menu_id: menuId, can_access: !!el.checked });
        });
        return rights;
    }

    async function loadUsers() {
        users = await Api.get('/api/v1/user-menu-rights/users');
        renderUserSelect();
    }

    async function loadRights(userId) {
        catalog = null;
        dirty = false;
        $('umr-menu-tree').innerHTML = '<div class="text-muted">Loading menu rights…</div>';
        setToolbar(false);
        try {
            catalog = await Api.get(`/api/v1/user-menu-rights/users/${userId}`);
            renderTree();
        } catch (error) {
            alertMsg(error.message || 'Could not load menu rights.', 'danger');
            $('umr-menu-tree').innerHTML = '';
        }
    }

    async function saveRights() {
        if (!selectedUserId || (catalog && catalog.is_system_admin)) return;
        $('btn-umr-save').disabled = true;
        try {
            const result = await Api.put(`/api/v1/user-menu-rights/users/${selectedUserId}`, {
                rights: collectRights(),
            });
            dirty = false;
            alertMsg(result.message || 'Saved.', 'success');
            await loadRights(selectedUserId);
        } catch (error) {
            alertMsg(error.message || 'Save failed.', 'danger');
            setToolbar(true);
        }
    }

    function cancelEdits() {
        if (!selectedUserId) return;
        if (dirty && !window.confirm('Discard unsaved changes?')) return;
        loadRights(selectedUserId);
    }

    function setAll(checked) {
        document.querySelectorAll('.umr-parent, .umr-child').forEach((el) => {
            el.checked = !!checked;
        });
        dirty = true;
    }

    document.addEventListener('DOMContentLoaded', async () => {
        await Auth.requireAuth();
        if (!Auth.hasPermission('auth.roles.manage') && !Auth.hasPermission('auth.admin.full')) {
            alertMsg('You do not have permission to manage user menu rights.', 'warning');
            return;
        }

        $('umr-user-search').addEventListener('input', renderUserSelect);
        $('umr-user-select').addEventListener('change', () => {
            const value = Number($('umr-user-select').value || 0);
            if (!value) return;
            if (dirty && !window.confirm('Discard unsaved changes and switch user?')) {
                renderUserSelect();
                return;
            }
            selectedUserId = value;
            loadRights(selectedUserId);
        });
        $('btn-umr-refresh').addEventListener('click', async () => {
            try {
                await Api.post('/api/v1/user-menu-rights/sync-menus', {});
                await loadUsers();
                if (selectedUserId) await loadRights(selectedUserId);
                alertMsg('Menus refreshed from application registry.', 'success');
            } catch (error) {
                alertMsg(error.message || 'Refresh failed.', 'danger');
            }
        });
        $('btn-umr-cancel').addEventListener('click', cancelEdits);
        $('btn-umr-save').addEventListener('click', saveRights);
        $('btn-umr-check-all').addEventListener('click', () => setAll(true));
        $('btn-umr-uncheck-all').addEventListener('click', () => setAll(false));

        try {
            await loadUsers();
        } catch (error) {
            alertMsg(error.message || 'Could not load users.', 'danger');
        }
    });
})();
