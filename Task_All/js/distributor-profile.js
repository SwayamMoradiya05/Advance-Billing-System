/* ==========================================================================
   Advance Billing System - Distributor Profile Manager
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
    const profileForm = document.getElementById('distributorProfileForm');
    const profileNameDisplay = document.getElementById('profileNameDisplay');
    const profileAvatarDisplay = document.getElementById('profileAvatarDisplay');
    const profileIdDisplay = document.getElementById('profileIdDisplay');
    const profileCreditDisplay = document.getElementById('profileCreditDisplay');

    const profileFullNameVal = document.getElementById('profileFullNameVal');
    const profileEmailVal = document.getElementById('profileEmailVal');
    const profilePhoneVal = document.getElementById('profilePhoneVal');
    const profileCompanyVal = document.getElementById('profileCompanyVal');
    const profileIdVal = document.getElementById('profileIdVal');
    const profileCreditVal = document.getElementById('profileCreditVal');

    const inputFullName = document.getElementById('inputFullName');
    const inputEmail = document.getElementById('inputEmail');
    const inputPhone = document.getElementById('inputPhone');
    const inputCompany = document.getElementById('inputCompany');

    // Load active session user profile details
    function loadProfile() {
        const user = AuthManager.getUser();

        // Fallback default user if no active session in static mode
        const activeUser = user || {
            id: 'DIST-8842',
            name: 'David Miller',
            email: 'apex@distributor.com',
            phone: '+1 555-019-8842',
            company: 'Apex Global Supplies',
            creditLimit: 150000,
            creditAvailable: 112450
        };

        if (profileNameDisplay) profileNameDisplay.textContent = activeUser.name || 'Distributor Partner';
        if (profileAvatarDisplay) profileAvatarDisplay.textContent = (activeUser.name || 'D').charAt(0).toUpperCase();
        if (profileIdDisplay) profileIdDisplay.textContent = `ID: ${activeUser.id || 'DIST-8842'}`;
        if (profileCreditDisplay) profileCreditDisplay.textContent = `₹${(activeUser.creditLimit || 50000).toLocaleString('en-IN')}.00`;

        if (profileFullNameVal) profileFullNameVal.textContent = activeUser.name || 'David Miller';
        if (profileEmailVal) profileEmailVal.textContent = activeUser.email || 'apex@distributor.com';
        if (profilePhoneVal) profilePhoneVal.textContent = activeUser.phone || '+1 555-019-8842';
        if (profileCompanyVal) profileCompanyVal.textContent = activeUser.company || 'Apex Global Supplies';
        if (profileIdVal) profileIdVal.textContent = activeUser.id || 'DIST-8842';
        if (profileCreditVal) profileCreditVal.textContent = `₹${(activeUser.creditLimit || 50000).toLocaleString('en-IN')}.00`;

        if (inputFullName) inputFullName.value = activeUser.name || '';
        if (inputEmail) inputEmail.value = activeUser.email || '';
        if (inputPhone) inputPhone.value = activeUser.phone || '';
        if (inputCompany) inputCompany.value = activeUser.company || '';
    }

    loadProfile();

    if (profileForm) {
        profileForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const fullName = inputFullName.value.trim();
            const email = inputEmail.value.trim();
            const phone = inputPhone.value.trim();
            const company = inputCompany.value.trim();

            if (!fullName || fullName.length < 2) {
                AuthManager.showToast('Full Name must be at least 2 characters long.', 'error');
                return;
            }

            if (/\d/.test(fullName)) {
                AuthManager.showToast('Full Name cannot contain numeric digits.', 'error');
                return;
            }

            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!email || !emailRegex.test(email)) {
                AuthManager.showToast('Please enter a valid email address format.', 'error');
                return;
            }

            if (/[a-zA-Z]/.test(phone)) {
                AuthManager.showToast('Phone number cannot contain alphabetic characters.', 'error');
                return;
            }

            const digitsOnly = phone.replace(/\D/g, '');
            if (digitsOnly.length < 7 || digitsOnly.length > 15) {
                AuthManager.showToast('Please enter a valid 7 to 15 digit phone number.', 'error');
                return;
            }

            const res = AuthManager.updateDistributorProfile({
                name: fullName,
                email: email,
                phone: phone,
                company: company
            });

            if (res.success) {
                AuthManager.showToast(res.message, 'success');
                loadProfile();
            } else {
                AuthManager.showToast(res.message, 'error');
            }
        });
    }
});
