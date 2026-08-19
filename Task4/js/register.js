/* ==========================================================================
   Distributor Registration Form Handler & Interactive Validation Module
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('distributorRegisterForm');
    if (!form) return;

    const fullNameInput = document.getElementById('fullName');
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const companyInput = document.getElementById('companyName');
    const termsCheckbox = document.getElementById('agreeTerms');
    const submitBtn = document.getElementById('submitBtn');

    const strengthFill = document.getElementById('strengthFill');
    const strengthLabel = document.getElementById('strengthLabel');
    const reqLength = document.getElementById('req-length');
    const reqMix = document.getElementById('req-mix');
    const reqNumber = document.getElementById('req-number');

    const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    const PHONE_REGEX = /^\+?[0-9\s\-()]{7,15}$/;

    function setFieldState(inputEl, isValid, message = '') {
        const feedbackEl = inputEl.closest('.mb-3')?.querySelector('.input-feedback');

        if (isValid) {
            inputEl.classList.remove('is-invalid');
            inputEl.classList.add('is-valid');
            if (feedbackEl) {
                feedbackEl.textContent = message || 'Looks good!';
                feedbackEl.className = 'input-feedback is-valid';
            }
        } else {
            inputEl.classList.remove('is-valid');
            inputEl.classList.add('is-invalid');
            if (feedbackEl) {
                feedbackEl.textContent = message;
                feedbackEl.className = 'input-feedback is-invalid';
            }
        }
        return isValid;
    }

    function validateName() {
        const val = fullNameInput.value.trim();
        if (!val) return setFieldState(fullNameInput, false, 'Full name is required.');
        if (val.length < 2) return setFieldState(fullNameInput, false, 'Name must be at least 2 characters.');
        return setFieldState(fullNameInput, true, 'Name verified.');
    }

    function validateEmail() {
        const val = emailInput.value.trim();
        if (!val) return setFieldState(emailInput, false, 'Email address is required.');
        if (!EMAIL_REGEX.test(val)) return setFieldState(emailInput, false, 'Enter a valid email address.');
        return setFieldState(emailInput, true, 'Email valid.');
    }

    function validatePhone() {
        const val = phoneInput.value.trim();
        if (!val) return setFieldState(phoneInput, false, 'Phone number is required.');
        const digits = val.replace(/\D/g, '');
        if (digits.length < 7 || digits.length > 15) return setFieldState(phoneInput, false, 'Enter a valid 7-15 digit phone number.');
        if (!PHONE_REGEX.test(val)) return setFieldState(phoneInput, false, 'Invalid phone number format.');
        return setFieldState(phoneInput, true, 'Phone number verified.');
    }

    function checkPasswordStrength(password) {
        let score = 0;
        const hasMinLength = password.length >= 8;
        const hasUpperAndLower = /[a-z]/.test(password) && /[A-Z]/.test(password);
        const hasDigitOrSpecial = /[0-9]/.test(password) || /[^A-Za-z0-9]/.test(password);

        if (reqLength) reqLength.classList.toggle('met', hasMinLength);
        if (reqMix) reqMix.classList.toggle('met', hasUpperAndLower);
        if (reqNumber) reqNumber.classList.toggle('met', hasDigitOrSpecial);

        if (!password) return { score: 0, text: 'Strength: Not entered', color: 'transparent', percent: 0 };

        if (hasMinLength) score++;
        if (hasUpperAndLower) score++;
        if (hasDigitOrSpecial) score++;
        if (password.length >= 12) score++;

        switch (score) {
            case 1: return { score: 1, text: 'Weak Password', color: '#ef4444', percent: 25 };
            case 2: return { score: 2, text: 'Fair Password', color: '#f59e0b', percent: 55 };
            case 3: return { score: 3, text: 'Good Password', color: '#38bdf8', percent: 80 };
            case 4: return { score: 4, text: 'Strong Password', color: '#10b981', percent: 100 };
            default: return { score: 0, text: 'Too Weak', color: '#ef4444', percent: 15 };
        }
    }

    function validatePassword() {
        const val = passwordInput.value;
        const strength = checkPasswordStrength(val);

        if (strengthFill) {
            strengthFill.style.width = strength.percent + '%';
            strengthFill.style.backgroundColor = strength.color;
        }
        if (strengthLabel) {
            strengthLabel.textContent = strength.text;
            strengthLabel.style.color = strength.color;
        }

        if (!val) return setFieldState(passwordInput, false, 'Password is required.');
        if (val.length < 8) return setFieldState(passwordInput, false, 'Password must be at least 8 characters long.');
        return setFieldState(passwordInput, true);
    }

    function validateConfirmPassword() {
        const pass = passwordInput.value;
        const confirmPass = confirmPasswordInput.value;

        if (!confirmPass) return setFieldState(confirmPasswordInput, false, 'Please confirm your password.');
        if (pass !== confirmPass) return setFieldState(confirmPasswordInput, false, 'Passwords do not match.');
        return setFieldState(confirmPasswordInput, true, 'Passwords match!');
    }

    fullNameInput.addEventListener('blur', validateName);
    emailInput.addEventListener('blur', validateEmail);
    phoneInput.addEventListener('blur', validatePhone);
    passwordInput.addEventListener('input', () => {
        validatePassword();
        if (confirmPasswordInput.value) validateConfirmPassword();
    });
    confirmPasswordInput.addEventListener('blur', validateConfirmPassword);

    document.querySelectorAll('.btn-password-toggle').forEach(btn => {
        btn.addEventListener('click', function () {
            const targetId = this.getAttribute('data-target');
            const targetInput = document.getElementById(targetId);
            if (!targetInput) return;
            if (targetInput.type === 'password') {
                targetInput.type = 'text';
                this.textContent = '🙈';
            } else {
                targetInput.type = 'password';
                this.textContent = '👁️';
            }
        });
    });

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        if (!validateName() || !validateEmail() || !validatePhone() || !validatePassword() || !validateConfirmPassword()) {
            alert('Please resolve all validation errors in the form.');
            return;
        }
        alert('Distributor registration completed successfully!');
        window.location.href = 'distributor-login.html?registered=true';
    });
});
