document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('login-form');
    const loginBtn = document.getElementById('login-btn');
    const loginBtnText = document.getElementById('login-btn-text');
    const loginSpinner = document.getElementById('login-spinner');
    const alertContainer = document.getElementById('alert-container');
    const alertBox = document.getElementById('alert-box');
    const togglePassword = document.getElementById('toggle-password');
    const passwordInput = document.getElementById('password');

    // Redirect if already logged in
    const token = getCookie('access_token') || localStorage.getItem('access_token');
    if (token) {
        window.location.href = '/dashboard';
        return;
    }

    // Toggle password visibility
    togglePassword.addEventListener('click', () => {
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
        togglePassword.querySelector('i').className = type === 'password' ? 'bi bi-eye' : 'bi bi-eye-slash';
    });

    // Theme support (dark/light ready)
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-bs-theme', savedTheme);
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        form.classList.remove('was-validated');

        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return;
        }

        setLoading(true);
        hideAlert();

        const payload = {
            username: document.getElementById('username').value.trim(),
            password: document.getElementById('password').value,
            remember_me: document.getElementById('remember-me').checked,
        };

        try {
            const response = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(payload),
            });

            let data;
            try {
                data = await response.json();
            } catch {
                showAlert('Server error. Please try again.', 'danger');
                setLoading(false);
                return;
            }

            if (!response.ok) {
                const message = typeof data.detail === 'string'
                    ? data.detail
                    : Array.isArray(data.detail)
                        ? data.detail.map(e => e.msg || e).join(', ')
                        : 'Login failed. Please try again.';
                showAlert(message, 'danger');
                setLoading(false);
                return;
            }

            localStorage.setItem('access_token', data.access_token);

            if (data.must_change_password) {
                window.location.href = '/admin/change-password';
            } else {
                window.location.href = '/dashboard';
            }
        } catch (err) {
            showAlert('Network error. Please check your connection.', 'danger');
            setLoading(false);
        }
    });

    document.getElementById('forgot-password-link').addEventListener('click', async (e) => {
        e.preventDefault();
        const email = prompt('Enter your registered email address:');
        if (!email) return;

        try {
            const response = await fetch('/api/v1/auth/forgot-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });
            const data = await response.json();
            showAlert(data.message || 'Request submitted.', 'info');
        } catch {
            showAlert('Unable to process request.', 'danger');
        }
    });

    function setLoading(loading) {
        loginBtn.disabled = loading;
        loginSpinner.classList.toggle('d-none', !loading);
        loginBtnText.textContent = loading ? 'Signing In...' : 'Sign In';
    }

    function showAlert(message, type) {
        alertBox.className = `alert alert-${type}`;
        alertBox.textContent = message;
        alertContainer.classList.remove('d-none');
    }

    function hideAlert() {
        alertContainer.classList.add('d-none');
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
});
