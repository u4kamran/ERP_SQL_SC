/**
 * Shared API client with JWT authentication.
 */
const Api = {
    getToken() {
        return localStorage.getItem('access_token') || this.getCookie('access_token');
    },

    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    },

    async request(method, url, body = null, { timeoutMs = 300000 } = {}) {
        const headers = { 'Content-Type': 'application/json' };
        const token = this.getToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const options = { method, headers, credentials: 'include' };
        if (body) options.body = JSON.stringify(body);

        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs);
        options.signal = controller.signal;

        let response;
        try {
            response = await fetch(url, options);
        } catch (err) {
            if (err?.name === 'AbortError') {
                throw new Error('Request timed out after 5 minutes. Check your connection or try again.');
            }
            throw new Error(
                'Cannot reach server. Wait a few seconds and refresh — the app may be restarting.'
            );
        } finally {
            clearTimeout(timer);
        }
        const raw = await response.text();
        let data;
        try {
            data = raw ? JSON.parse(raw) : {};
        } catch {
            const snippet = raw ? raw.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 180) : '';
            data = {
                detail: snippet || `Server error (${response.status}). Please try again.`,
            };
        }

        if (!response.ok) {
            const message = typeof data.detail === 'string'
                ? data.detail
                : Array.isArray(data.detail)
                    ? data.detail.map(e => e.msg || JSON.stringify(e)).join(', ')
                    : data.message || 'Request failed.';
            throw new Error(message);
        }
        return data;
    },

    get(url, opts) { return this.request('GET', url, null, opts); },
    post(url, body, opts) { return this.request('POST', url, body, opts); },
    put(url, body, opts) { return this.request('PUT', url, body, opts); },
    delete(url, opts) { return this.request('DELETE', url, null, opts); },

    async upload(url, formData, { timeoutMs = 300000 } = {}) {
        const headers = {};
        const token = this.getToken();
        if (token) headers.Authorization = `Bearer ${token}`;
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs);
        let response;
        try {
            response = await fetch(url, {
                method: 'POST',
                headers,
                body: formData,
                credentials: 'include',
                signal: controller.signal,
            });
        } catch (err) {
            if (err?.name === 'AbortError') {
                throw new Error('Upload timed out. Try a smaller image.');
            }
            throw new Error('Cannot reach server for upload.');
        } finally {
            clearTimeout(timer);
        }
        const raw = await response.text();
        let data;
        try {
            data = raw ? JSON.parse(raw) : {};
        } catch {
            data = { detail: `Server error (${response.status}).` };
        }
        if (!response.ok) {
            const message = typeof data.detail === 'string'
                ? data.detail
                : data.message || 'Upload failed.';
            throw new Error(message);
        }
        return data;
    },
};

/**
 * Auth helpers — profile, permissions, logout.
 */
const Auth = {
    profile: null,

    async loadProfile() {
        this.profile = await Api.get('/api/v1/profile/');
        return this.profile;
    },

    hasPermission(code) {
        if (!this.profile) return false;
        return this.profile.permissions.includes(code) ||
               this.profile.permissions.includes('auth.admin.full');
    },

    /**
     * Super-only UI (site links). Set by server from live DB roles — not JWT.
     */
    isSuperAdmin() {
        return Boolean(this.profile?.is_super_admin);
    },

    /** Cached after login from UserMenuRights (empty/enforced=false = legacy role menus). */
    hasMenuPath(path) {
        if (!this.profile) return false;
        if (this.isSuperAdmin() || this.hasPermission('auth.admin.full')) return true;
        if (!this.profile.menu_access_enforced) return true;
        const clean = String(path || '').split('?', 1)[0].replace(/\/$/, '') || '/';
        const always = ['/dashboard', '/admin/profile', '/admin/change-password'];
        if (always.includes(clean)) return true;
        const allowed = (this.profile.allowed_menu_paths || []).map((p) =>
            String(p).replace(/\/$/, ''));
        return allowed.includes(clean);
    },

    requireMenuPath(path) {
        if (this.hasMenuPath(path)) return true;
        const host = document.getElementById('alert-container') || document.body;
        const box = document.createElement('div');
        box.className = 'container py-5';
        box.innerHTML = `<div class="alert alert-warning">You do not have permission to access this module.</div>
            <a class="btn btn-primary" href="/dashboard">Back to Dashboard</a>`;
        document.querySelector('main')?.replaceChildren(box)
            || host.replaceChildren(box);
        return false;
    },

    applySuperUserVisibility() {
        const show = this.isSuperAdmin();
        document.querySelectorAll('[data-super-only]').forEach((el) => {
            el.classList.toggle('d-none', !show);
        });
    },

    applyMenuVisibility() {
        if (!this.profile?.menu_access_enforced || this.isSuperAdmin()) {
            return;
        }
        document.querySelectorAll('#sidebar-nav .nav-link[href]').forEach((link) => {
            const href = link.getAttribute('href') || '';
            if (!href.startsWith('/')) return;
            const item = link.closest('.nav-item');
            if (!item) return;
            if (!this.hasMenuPath(href)) {
                item.style.display = 'none';
            }
        });
    },

    async requireAuth() {
        const token = Api.getToken();
        if (!token) {
            window.location.href = '/login';
            return null;
        }
        try {
            await this.loadProfile();
            return this.profile;
        } catch {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
            return null;
        }
    },

    async logout() {
        try {
            await Api.post('/api/v1/auth/logout', {});
        } catch { /* proceed */ }
        localStorage.removeItem('access_token');
        document.cookie = 'access_token=; Max-Age=0; path=/';
        document.cookie = 'refresh_token=; Max-Age=0; path=/';
        window.location.href = '/login';
    },

    showAlert(containerId, message, type = 'danger') {
        const el = document.getElementById(containerId);
        if (!el) return;
        el.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>`;
    },
};
