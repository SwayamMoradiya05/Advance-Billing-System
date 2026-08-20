/* ==========================================================================
   Distributor Registration Form Handler & Interactive Validation Module
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('distributorRegisterForm');
    if (!form) return;

    // Form Elements
    const fullNameInput = document.getElementById('fullName');
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const companyInput = document.getElementById('companyName');
    const termsCheckbox = document.getElementById('agreeTerms');
    const submitBtn = document.getElementById('submitBtn');

    // Password Strength Meter Elements
    const strengthFill = document.getElementById('strengthFill');
    const strengthLabel = document.getElementById('strengthLabel');
    const reqLength = document.getElementById('req-length');
    const reqMix = document.getElementById('req-mix');
    const reqNumber = document.getElementById('req-number');

    // Validation Rules
    const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    const PHONE_REGEX = /^\+?[0-9\s\-()]{7,15}$/;

    // Helper: Set input validation state in UI
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

    // Clear validation state
    function clearFieldState(inputEl) {
        inputEl.classList.remove('is-valid', 'is-invalid');
        const feedbackEl = inputEl.closest('.mb-3')?.querySelector('.input-feedback');
        if (feedbackEl) {
            feedbackEl.className = 'input-feedback';
            feedbackEl.textContent = '';
        }
    }

    // 1. Full Name Validation
    function validateName() {
        const val = fullNameInput.value.trim();
        if (!val) {
            return setFieldState(fullNameInput, false, 'Full name is required.');
        }
        if (val.length < 2) {
            return setFieldState(fullNameInput, false, 'Name must be at least 2 characters.');
        }
        if (/\d/.test(val)) {
            return setFieldState(fullNameInput, false, 'Name should not contain numbers.');
        }
        return setFieldState(fullNameInput, true, 'Name verified.');
    }

    // 2. Email Validation
    function validateEmail() {
        const val = emailInput.value.trim();
        if (!val) {
            return setFieldState(emailInput, false, 'Email address is required.');
        }
        if (!EMAIL_REGEX.test(val)) {
            return setFieldState(emailInput, false, 'Please enter a valid email address (e.g. name@domain.com).');
        }
        if (AuthManager.isEmailRegistered && AuthManager.isEmailRegistered(val)) {
            return setFieldState(emailInput, false, 'This email is already registered. Try signing in.');
        }
        return setFieldState(emailInput, true, 'Email available.');
    }

    // 3. Phone Number Validation
    function validatePhone() {
        const val = phoneInput.value.trim();
        if (!val) {
            return setFieldState(phoneInput, false, 'Phone number is required.');
        }
        if (/[a-zA-Z]/.test(val)) {
            return setFieldState(phoneInput, false, 'Phone number cannot contain alphabetic characters.');
        }
        // Extract raw digits for length check
        const digits = val.replace(/\D/g, '');
        if (digits.length < 7 || digits.length > 15) {
            return setFieldState(phoneInput, false, 'Enter a valid 7 to 15 digit numerical phone number.');
        }
        if (!PHONE_REGEX.test(val)) {
            return setFieldState(phoneInput, false, 'Invalid phone number format.');
        }
        return setFieldState(phoneInput, true, 'Phone number verified.');
    }

    // 4. Password Strength Calculation & Live Feedback
    function checkPasswordStrength(password) {
        let score = 0;
        const hasMinLength = password.length >= 8;
        const hasUpperAndLower = /[a-z]/.test(password) && /[A-Z]/.test(password);
        const hasDigitOrSpecial = /[0-9]/.test(password) || /[^A-Za-z0-9]/.test(password);

        // Update Checklist UI
        if (reqLength) reqLength.classList.toggle('met', hasMinLength);
        if (reqMix) reqMix.classList.toggle('met', hasUpperAndLower);
        if (reqNumber) reqNumber.classList.toggle('met', hasDigitOrSpecial);

        if (!password) return { score: 0, text: 'Strength: Not entered', color: 'transparent', percent: 0 };

        if (hasMinLength) score++;
        if (hasUpperAndLower) score++;
        if (hasDigitOrSpecial) score++;
        if (password.length >= 12) score++;

        switch (score) {
            case 1:
                return { score: 1, text: 'Weak Password', color: '#ef4444', percent: 25 };
            case 2:
                return { score: 2, text: 'Fair Password', color: '#f59e0b', percent: 55 };
            case 3:
                return { score: 3, text: 'Good Password', color: '#38bdf8', percent: 80 };
            case 4:
                return { score: 4, text: 'Strong Password', color: '#10b981', percent: 100 };
            default:
                return { score: 0, text: 'Too Weak', color: '#ef4444', percent: 15 };
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

        if (!val) {
            return setFieldState(passwordInput, false, 'Password is required.');
        }
        if (val.length < 8) {
            return setFieldState(passwordInput, false, 'Password must be at least 8 characters long.');
        }
        return setFieldState(passwordInput, true);
    }

    // 5. Confirm Password Validation
    function validateConfirmPassword() {
        const pass = passwordInput.value;
        const confirmPass = confirmPasswordInput.value;

        if (!confirmPass) {
            return setFieldState(confirmPasswordInput, false, 'Please confirm your password.');
        }
        if (pass !== confirmPass) {
            return setFieldState(confirmPasswordInput, false, 'Passwords do not match.');
        }
        return setFieldState(confirmPasswordInput, true, 'Passwords match!');
    }

    // Attach Blur & Input Event Listeners for Live Interactivity
    fullNameInput.addEventListener('blur', validateName);
    fullNameInput.addEventListener('input', () => {
        if (fullNameInput.classList.contains('is-invalid')) validateName();
    });

    emailInput.addEventListener('blur', validateEmail);
    emailInput.addEventListener('input', () => {
        if (emailInput.classList.contains('is-invalid')) validateEmail();
    });

    phoneInput.addEventListener('blur', validatePhone);
    phoneInput.addEventListener('input', (e) => {
        // Optional formatting: restrict non-phone characters
        if (phoneInput.classList.contains('is-invalid')) validatePhone();
    });

    passwordInput.addEventListener('input', () => {
        validatePassword();
        if (confirmPasswordInput.value) {
            validateConfirmPassword();
        }
    });

    confirmPasswordInput.addEventListener('blur', validateConfirmPassword);
    confirmPasswordInput.addEventListener('input', () => {
        if (confirmPasswordInput.value) validateConfirmPassword();
    });

    // Password Show/Hide Toggle Logic
    document.querySelectorAll('.btn-password-toggle').forEach(btn => {
        btn.addEventListener('click', function () {
            const targetId = this.getAttribute('data-target');
            const targetInput = document.getElementById(targetId);
            if (!targetInput) return;

            if (targetInput.type === 'password') {
                targetInput.type = 'text';
                this.textContent = '🙈';
                this.setAttribute('title', 'Hide password');
            } else {
                targetInput.type = 'password';
                this.textContent = '👁️';
                this.setAttribute('title', 'Show password');
            }
        });
    });

    // Form Submission Handler
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        // Run all field validations
        const isNameValid = validateName();
        const isEmailValid = validateEmail();
        const isPhoneValid = validatePhone();
        const isPasswordValid = validatePassword();
        const isConfirmValid = validateConfirmPassword();

        if (!termsCheckbox.checked) {
            AuthManager.showToast('Please accept the Terms of Service & Privacy Policy to register.', 'warning');
            return;
        }

        if (!isNameValid || !isEmailValid || !isPhoneValid || !isPasswordValid || !isConfirmValid) {
            AuthManager.showToast('Please resolve the errors highlighted in the registration form.', 'error');
            return;
        }

        // Disable button during submission simulation
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Creating Distributor Account...
        `;

        const distributorData = {
            name: fullNameInput.value.trim(),
            email: emailInput.value.trim(),
            phone: phoneInput.value.trim(),
            password: passwordInput.value,
            company: companyInput ? companyInput.value.trim() : ''
        };

        // Simulate API call processing delay
        setTimeout(() => {
            const result = AuthManager.registerDistributor(distributorData);

            if (result.success) {
                AuthManager.showToast('Registration successful! Redirecting to Distributor Portal...', 'success');
                setTimeout(() => {
                    window.location.href = 'distributor-login.html?registered=true';
                }, 1500);
            } else {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Complete Distributor Registration &rarr;';
                AuthManager.showToast(result.message, 'error');
            }
        }, 1000);
    });
});
