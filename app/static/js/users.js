/** User management page logic. */
let allRoles = [];
let userModal, resetModal;

document.addEventListener('DOMContentLoaded', async () => {
    const profile = await Auth.requireAuth();
    if (!profile) return;

    if (!Auth.hasPermission('auth.users.view')) {
        Auth.showAlert('alert-container', 'You do not have permission to view users.', 'warning');
        return;
    }

    userModal = new bootstrap.Modal(document.getElementById('userModal'));
    resetModal = new bootstrap.Modal(document.getElementById('resetPasswordModal'));

    if (!Auth.hasPermission('auth.users.create')) {
        document.getElementById('btn-create-user').style.display = 'none';
    }

    document.getElementById('btn-create-user').addEventListener('click', () => openCreateModal());
    document.getElementById('userForm').addEventListener('submit', handleUserSubmit);
    document.getElementById('resetPasswordForm').addEventListener('submit', handleResetPassword);

    await loadRoles();
    await loadUsers();
});

async function loadRoles() {
    try {
        allRoles = await Api.get('/api/v1/roles/');
    } catch {
        allRoles = [];
    }
}

async function loadUsers() {
    const tbody = document.getElementById('users-table-body');
    try {
        const users = await Api.get('/api/v1/users/');
        if (!users.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">No users found.</td></tr>';
            return;
        }
        tbody.innerHTML = users.map(u => `
            <tr>
                <td><strong>${esc(u.username)}</strong></td>
                <td>${esc([u.first_name, u.last_name].filter(Boolean).join(' ') || '—')}</td>
                <td>${esc(u.email)}</td>
                <td>${u.roles.map(r => `<span class="badge bg-secondary badge-role">${esc(r)}</span>`).join('')}</td>
                <td>${u.is_active
                    ? '<span class="badge bg-success">Active</span>'
                    : '<span class="badge bg-danger">Inactive</span>'}
                    ${u.must_change_password ? '<span class="badge bg-warning text-dark">Must change pwd</span>' : ''}
                </td>
                <td class="small text-muted">${formatUtcDateTime(u.last_login_date)}</td>
                <td class="text-end table-actions">
                    ${Auth.hasPermission('auth.users.update') ? `
                        <button class="btn btn-sm btn-outline-primary" onclick="openEditModal(${u.user_id})" title="Edit">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-warning" onclick="openResetModal(${u.user_id}, '${esc(u.username)}')" title="Reset Password">
                            <i class="bi bi-key"></i>
                        </button>` : ''}
                    ${Auth.hasPermission('auth.users.delete') ? `
                        <button class="btn btn-sm btn-outline-danger" onclick="deactivateUser(${u.user_id}, '${esc(u.username)}')" title="Deactivate">
                            <i class="bi bi-person-x"></i>
                        </button>` : ''}
                </td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">${esc(err.message)}</td></tr>`;
    }
}

function renderRoleCheckboxes(selectedIds = []) {
    const container = document.getElementById('user-roles-checkboxes');
    container.innerHTML = allRoles.map(r => `
        <div class="form-check">
            <input class="form-check-input role-check" type="checkbox" value="${r.role_id}"
                id="role-${r.role_id}" ${selectedIds.includes(r.role_id) ? 'checked' : ''}>
            <label class="form-check-label" for="role-${r.role_id}">${esc(r.role_name)}</label>
        </div>
    `).join('');
}

function openCreateModal() {
    document.getElementById('userModalTitle').textContent = 'New User';
    document.getElementById('user-id').value = '';
    document.getElementById('userForm').reset();
    document.getElementById('username-group').style.display = '';
    document.getElementById('password-group').style.display = '';
    document.getElementById('user-password').required = true;
    document.getElementById('active-group').style.display = 'none';
    document.getElementById('user-form-error').classList.add('d-none');
    renderRoleCheckboxes();
    userModal.show();
}

async function openEditModal(userId) {
    try {
        const user = await Api.get(`/api/v1/users/${userId}`);
        document.getElementById('userModalTitle').textContent = 'Edit User';
        document.getElementById('user-id').value = user.user_id;
        document.getElementById('user-username').value = user.username;
        document.getElementById('user-email').value = user.email;
        document.getElementById('user-firstname').value = user.first_name || '';
        document.getElementById('user-lastname').value = user.last_name || '';
        document.getElementById('user-phone').value = user.phone_number || '';
        document.getElementById('user-active').checked = user.is_active;
        document.getElementById('username-group').style.display = 'none';
        document.getElementById('password-group').style.display = 'none';
        document.getElementById('user-password').required = false;
        document.getElementById('active-group').style.display = '';
        document.getElementById('user-form-error').classList.add('d-none');
        renderRoleCheckboxes(user.role_ids || []);
        userModal.show();
    } catch (err) {
        Auth.showAlert('alert-container', err.message, 'danger');
    }
}

function openResetModal(userId, username) {
    document.getElementById('reset-user-id').value = userId;
    document.getElementById('reset-username').textContent = username;
    document.getElementById('resetPasswordForm').reset();
    document.getElementById('reset-must-change').checked = true;
    document.getElementById('reset-form-error').classList.add('d-none');
    resetModal.show();
}

async function handleUserSubmit(e) {
    e.preventDefault();
    const errEl = document.getElementById('user-form-error');
    errEl.classList.add('d-none');

    const userId = document.getElementById('user-id').value;
    const roleIds = [...document.querySelectorAll('.role-check:checked')].map(c => parseInt(c.value));

    try {
        if (userId) {
            await Api.put(`/api/v1/users/${userId}`, {
                email: document.getElementById('user-email').value,
                first_name: document.getElementById('user-firstname').value || null,
                last_name: document.getElementById('user-lastname').value || null,
                phone_number: document.getElementById('user-phone').value || null,
                is_active: document.getElementById('user-active').checked,
                role_ids: roleIds,
            });
            Auth.showAlert('alert-container', 'User updated successfully.', 'success');
        } else {
            await Api.post('/api/v1/users/', {
                username: document.getElementById('user-username').value,
                email: document.getElementById('user-email').value,
                password: document.getElementById('user-password').value,
                first_name: document.getElementById('user-firstname').value || null,
                last_name: document.getElementById('user-lastname').value || null,
                phone_number: document.getElementById('user-phone').value || null,
                role_ids: roleIds,
            });
            Auth.showAlert('alert-container', 'User created successfully.', 'success');
        }
        userModal.hide();
        await loadUsers();
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('d-none');
    }
}

async function handleResetPassword(e) {
    e.preventDefault();
    const errEl = document.getElementById('reset-form-error');
    errEl.classList.add('d-none');
    const userId = document.getElementById('reset-user-id').value;

    try {
        await Api.post(`/api/v1/users/${userId}/reset-password`, {
            new_password: document.getElementById('reset-password').value,
            must_change_password: document.getElementById('reset-must-change').checked,
        });
        resetModal.hide();
        Auth.showAlert('alert-container', 'Password reset successfully.', 'success');
        await loadUsers();
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('d-none');
    }
}

async function deactivateUser(userId, username) {
    if (!confirm(`Deactivate user "${username}"?`)) return;
    try {
        await Api.delete(`/api/v1/users/${userId}`);
        Auth.showAlert('alert-container', 'User deactivated.', 'success');
        await loadUsers();
    } catch (err) {
        Auth.showAlert('alert-container', err.message, 'danger');
    }
}

function esc(str) {
    const d = document.createElement('div');
    d.textContent = str || '';
    return d.innerHTML;
}
