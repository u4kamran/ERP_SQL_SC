document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('access_token') || getCookie('access_token');

    if (!token) {
        window.location.href = '/login';
        return;
    }

    try {
        const response = await fetch('/api/v1/profile/', {
            headers: { 'Authorization': `Bearer ${token}` },
            credentials: 'include',
        });

        if (!response.ok) {
            window.location.href = '/login';
            return;
        }

        const profile = await response.json();
        document.getElementById('user-info').textContent = profile.username;
    } catch {
        window.location.href = '/login';
    }

    document.getElementById('logout-btn').addEventListener('click', async () => {
        const token = localStorage.getItem('access_token');
        try {
            await fetch('/api/v1/auth/logout', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                credentials: 'include',
            });
        } catch { /* proceed with local cleanup */ }

        localStorage.removeItem('access_token');
        document.cookie = 'access_token=; Max-Age=0; path=/';
        document.cookie = 'refresh_token=; Max-Age=0; path=/';
        window.location.href = '/login';
    });

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
});
