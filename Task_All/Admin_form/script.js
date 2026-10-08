/* ============================================================
   Advance Billing System - Admin Registration Form Script
   ============================================================ */

(function () {
    'use strict';

    // ---- DOM References ----
    const form = document.getElementById('adminRegisterForm');
    const alertBox = document.getElementById('alertBox');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const strengthContainer = document.getElementById('strengthContainer');
    const strengthBar = document.getElementById('strengthBar');
    const strengthText = document.getElementById('strengthText');
    const submitBtn = document.getElementById('submitBtn');
    const roleOptions = document.querySelectorAll('.role-option');

    // ---- Role Selector Toggle ----
    roleOptions.forEach(option => {
        option.addEventListener('click', () => {
            roleOptions.forEach(o => o.classList.remove('active'));
            option.classList.add('active');
        });
    });

    // ---- Password Visibility Toggle ----
    document.querySelectorAll('.toggle-password').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const input = document.getElementById(targetId);
            if (!input) return;
            if (input.type === 'password') {
                input.type = 'text';
                btn.textContent = '🙈';
            } else {
                input.type = 'password';
                btn.textContent = '👁️';
            }
        });
    });

    // ---- Live Password Strength ----
    passwordInput.addEventListener('input', () => {
        const val = passwordInput.value;
        if (val.length === 0) {
            strengthContainer.style.display = 'none';
            return;
        }
        strengthContainer.style.display = 'flex';

        let score = 0;
        if (val.length >= 8)  score++;
        if (val.length >= 12) score++;
        if (/[A-Z]/.test(val)) score++;
        if (/[0-9]/.test(val)) score++;
        if (/[^A-Za-z0-9]/.test(val)) score++;

        const levels = [
            { label: 'Very Weak', pct: 15,  color: '#ef4444' },
            { label: 'Weak',      pct: 30,  color: '#f97316' },
            { label: 'Fair',      pct: 55,  color: '#f59e0b' },
            { label: 'Strong',    pct: 80,  color: '#22c55e' },
            { label: 'Very Strong', pct: 100, color: '#10b981' },
        ];
        const level = levels[Math.min(score, levels.length - 1)];
        strengthBar.style.width = level.pct + '%';
        strengthBar.style.backgroundColor = level.color;
        strengthText.textContent = level.label;
        strengthText.style.color = level.color;
    });

    // ---- Helper: Show Alert ----
    function showAlert(message, type = 'danger') {
        alertBox.className = 'alert-box alert-' + type;
        alertBox.innerHTML = message;
        alertBox.style.display = 'block';
        alertBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function hideAlert() {
        alertBox.style.display = 'none';
    }

    // ---- Helper: Mark Input Error ----
    function setInputError(input, hasError) {
        if (hasError) {
            input.classList.add('input-error');
        } else {
            input.classList.remove('input-error');
        }
    }

    // ---- Client-side Validation ----
    function validateForm(data) {
        const errors = [];
        const emailRegex = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;

        if (!data.first_name || data.first_name.trim().length < 1) {
            errors.push('First Name is required.');
            setInputError(document.getElementById('firstName'), true);
        } else {
            setInputError(document.getElementById('firstName'), false);
        }

        if (!data.username || data.username.trim().length < 3) {
            errors.push('Username must be at least 3 characters long.');
            setInputError(document.getElementById('username'), true);
        } else {
            setInputError(document.getElementById('username'), false);
        }

        if (!data.email || !emailRegex.test(data.email)) {
            errors.push('Please enter a valid corporate email address.');
            setInputError(document.getElementById('email'), true);
        } else {
            setInputError(document.getElementById('email'), false);
        }

        if (!data.password || data.password.length < 8) {
            errors.push('Password must be at least 8 characters long.');
            setInputError(passwordInput, true);
        } else if (!/[A-Za-z]/.test(data.password) || !/[0-9]/.test(data.password)) {
            errors.push('Password must contain a mix of letters and numbers.');
            setInputError(passwordInput, true);
        } else {
            setInputError(passwordInput, false);
        }

        if (data.password !== data.confirm_password) {
            errors.push('Passwords do not match. Please re-enter.');
            setInputError(confirmPasswordInput, true);
        } else {
            setInputError(confirmPasswordInput, false);
        }

        if (!document.getElementById('agreeTerms').checked) {
            errors.push('You must confirm that you are authorized to register an Admin account.');
        }

        return errors;
    }

    // ---- Form Submit ----
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert();

        const activeRole = document.querySelector('.role-option.active input[type="radio"]');
        const isSuperuser = activeRole && activeRole.value === 'superuser';

        const payload = {
            username: document.getElementById('username').value.trim(),
            email: document.getElementById('email').value.trim().toLowerCase(),
            password: passwordInput.value,
            confirm_password: confirmPasswordInput.value,
            first_name: document.getElementById('firstName').value.trim(),
            last_name: document.getElementById('lastName').value.trim(),
            is_superuser: isSuperuser,
        };

        const clientErrors = validateForm(payload);
        if (clientErrors.length > 0) {
            showAlert('⚠️ Please fix the following:<br>• ' + clientErrors.join('<br>• '));
            return;
        }

        // -- Disable button + show spinner --
        submitBtn.disabled = true;
        submitBtn.querySelector('.btn-text').style.display = 'none';
        submitBtn.querySelector('.btn-spinner').style.display = 'inline';

        try {
            const response = await fetch('/api/admin/register/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (response.status === 201) {
                showAlert(
                    '✅ Admin account created successfully! Welcome, <strong>' +
                    (data.user.first_name || data.user.username) +
                    '</strong>. Redirecting to Admin Sign In...',
                    'success'
                );
                form.reset();
                strengthContainer.style.display = 'none';
                setTimeout(() => { window.location.href = '/login/'; }, 2500);
            } else {
                let errorMsg = '⚠️ Registration failed:';
                if (data.details) {
                    const fieldErrors = Object.entries(data.details)
                        .map(([field, msgs]) => `<br>• <strong>${field}:</strong> ${Array.isArray(msgs) ? msgs[0] : msgs}`)
                        .join('');
                    errorMsg += fieldErrors;
                } else if (data.error) {
                    errorMsg += '<br>• ' + data.error;
                }
                showAlert(errorMsg);
            }
        } catch (networkError) {
            showAlert('❌ Network error. Please check your connection and try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.querySelector('.btn-text').style.display = 'inline';
            submitBtn.querySelector('.btn-spinner').style.display = 'none';
        }
    });

})();
