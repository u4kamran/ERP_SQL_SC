/** Shared admin layout initialization. */

document.addEventListener('DOMContentLoaded', async () => {
    const profile = await Auth.requireAuth();
    if (!profile) return;

    document.getElementById('topbar-user').textContent = profile.username;

    Auth.applySuperUserVisibility();

    // Hide nav items user lacks feature permission for (legacy role permissions)
    document.querySelectorAll('[data-perm]').forEach((el) => {
        const perm = el.getAttribute('data-perm');
        if (perm && !Auth.hasPermission(perm) && !Auth.hasPermission('auth.admin.full')) {
            el.style.display = 'none';
        }
    });

    // User Menu Rights (dedicated table) — hide unchecked menus completely
    Auth.applyMenuVisibility();

    // Block direct URL open when user menu rights are enforced
    const path = window.location.pathname;
    if (!Auth.hasMenuPath(path)) {
        Auth.requireMenuPath(path);
        return;
    }

    // Hide section headers when every following item in that section is hidden
    document.querySelectorAll('#sidebar-nav .nav-section').forEach((section) => {
        let sibling = section.nextElementSibling;
        let anyVisible = false;
        while (sibling && !sibling.classList.contains('nav-section')) {
            if (
                sibling.classList.contains('nav-item')
                && sibling.style.display !== 'none'
            ) {
                anyVisible = true;
                break;
            }
            sibling = sibling.nextElementSibling;
        }
        if (!anyVisible) {
            section.style.display = 'none';
        }
    });

    // Highlight active nav link
    document.querySelectorAll('#sidebar-nav .nav-link').forEach((link) => {
        if (link.getAttribute('href') === path) {
            link.classList.add('active');
        }
    });

    document.getElementById('logout-btn').addEventListener('click', () => Auth.logout());

    document.getElementById('sidebar-toggle')?.addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('show');
    });

    const compactKey = 'sidebar-compact';
    const compactBtn = document.getElementById('sidebar-compact');
    if (localStorage.getItem(compactKey) === '1') {
        document.body.classList.add('sidebar-compact');
    }
    document.querySelectorAll('#sidebar-nav .nav-link').forEach((link) => {
        if (!link.getAttribute('title')) {
            const label = link.querySelector('.nav-label');
            link.setAttribute('title', (label ? label.textContent : link.textContent).replace(/\s+/g, ' ').trim());
        }
    });
    compactBtn?.addEventListener('click', () => {
        const on = document.body.classList.toggle('sidebar-compact');
        localStorage.setItem(compactKey, on ? '1' : '0');
        compactBtn.setAttribute('title', on ? 'Expand menu' : 'Collapse menu');
        compactBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    if (compactBtn) {
        const on = document.body.classList.contains('sidebar-compact');
        compactBtn.setAttribute('title', on ? 'Expand menu' : 'Collapse menu');
        compactBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
    }
});
