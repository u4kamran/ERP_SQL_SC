/** Shared admin layout initialization. */

document.addEventListener('DOMContentLoaded', async () => {

    const profile = await Auth.requireAuth();

    if (!profile) return;



    document.getElementById('topbar-user').textContent = profile.username;



    Auth.applySuperUserVisibility();



    // Hide nav items user lacks permission for

    document.querySelectorAll('[data-perm]').forEach(el => {

        const perm = el.getAttribute('data-perm');

        if (perm && !Auth.hasPermission(perm) && !Auth.hasPermission('auth.admin.full')) {

            el.style.display = 'none';

        }

    });



    // Highlight active nav link

    const path = window.location.pathname;

    document.querySelectorAll('#sidebar-nav .nav-link').forEach(link => {

        if (link.getAttribute('href') === path) {

            link.classList.add('active');

        }

    });



    document.getElementById('logout-btn').addEventListener('click', () => Auth.logout());



    document.getElementById('sidebar-toggle')?.addEventListener('click', () => {

        document.getElementById('sidebar').classList.toggle('show');

    });

});

