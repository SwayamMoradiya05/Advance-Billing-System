/* ==========================================================================
   Advance Billing System - Auth & Distributor Account Session Manager
   ========================================================================== */

const AuthManager = (function () {
    const STORAGE_KEY = 'abs_user_session';
    const DISTRIBUTORS_DB_KEY = 'abs_registered_distributors';

    // Default Seeded Accounts
    const INITIAL_USERS = {
        admin: [
            {
                id: 'ADM-001',
                email: 'admin@gmail.com',
                password: 'admin@gmail.com',
                name: 'Swayam',
                role: 'admin',
                designation: 'Super Administrator',
                badge: 'Level 5 Clearance'
            }
        ],
        distributor: [
            {
                id: 'DIST-8842',
                email: 'apex@distributor.com',
                phone: '+1 555-019-8842',
                password: 'dist123',
                name: 'David Miller',
                company: 'Apex Global Supplies',
                role: 'distributor',
                creditLimit: 150000,
                creditAvailable: 112450,
                activeOrders: 4
            },
            {
                id: 'DIST-0004',
                email: 'moradiyaswayam@gmail.com',
                phone: '+1 555-019-8842',
                password: 'dist123',
                name: 'Swayam Moradiya',
                company: 'Swayam Logistics',
                role: 'distributor',
                creditLimit: 150000,
                creditAvailable: 150000,
                activeOrders: 0
            }
        ]
    };

    // Load registered distributors from localStorage or initialize with defaults
    function getRegisteredDistributors() {
        try {
            const data = localStorage.getItem(DISTRIBUTORS_DB_KEY);
            if (data) {
                return JSON.parse(data);
            }
        } catch (e) {
            console.error('Error loading distributors from storage:', e);
        }
        localStorage.setItem(DISTRIBUTORS_DB_KEY, JSON.stringify(INITIAL_USERS.distributor));
        return INITIAL_USERS.distributor;
    }

    function saveDistributorsList(list) {
        try {
            localStorage.setItem(DISTRIBUTORS_DB_KEY, JSON.stringify(list));
        } catch (e) {
            console.error('Error saving distributor to storage:', e);
        }
    }

    function getSession() {
        try {
            const data = localStorage.getItem(STORAGE_KEY);
            return data ? JSON.parse(data) : null;
        } catch (e) {
            console.error('Failed to read auth session', e);
            return null;
        }
    }

    function setSession(user) {
        const sessionData = {
            user: user,
            token: 'TOKEN-' + Math.random().toString(36).substring(2) + Date.now(),
            loggedInAt: new Date().toISOString()
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(sessionData));
        return sessionData;
    }

    function clearSession() {
        localStorage.removeItem(STORAGE_KEY);
    }

    return {
        getUser: function () {
            const session = getSession();
            return session ? session.user : null;
        },

        isAuthenticated: function () {
            return !!getSession();
        },

        // Check if an email is already registered
        isEmailRegistered: function (email) {
            const distributors = getRegisteredDistributors();
            return distributors.some(d => d.email.toLowerCase() === email.toLowerCase().trim());
        },

        // Register a new Distributor
        registerDistributor: function (distributorData) {
            const distributors = getRegisteredDistributors();

            if (this.isEmailRegistered(distributorData.email)) {
                return {
                    success: false,
                    message: 'An account with this email address is already registered.'
                };
            }

            // Generate unique Distributor ID
            const newId = 'DIST-' + Math.floor(1000 + Math.random() * 9000);

            const newDistributor = {
                id: newId,
                name: distributorData.name,
                email: distributorData.email.trim(),
                phone: distributorData.phone.trim(),
                password: distributorData.password, // In production, this would be hashed on the server
                company: distributorData.company || `${distributorData.name} Logistics`,
                role: 'distributor',
                creditLimit: 50000, // Default initial credit limit
                creditAvailable: 50000,
                activeOrders: 0,
                createdAt: new Date().toISOString()
            };

            distributors.push(newDistributor);
            saveDistributorsList(distributors);

            return {
                success: true,
                user: newDistributor,
                message: 'Distributor account created successfully! Please sign in.'
            };
        },

        // Standard Login
        loginWithCredentials: function (identifier, password, expectedRole = 'distributor') {
            let userList = [];
            if (expectedRole === 'admin') {
                userList = INITIAL_USERS.admin;
            } else {
                userList = getRegisteredDistributors();
            }

            const user = userList.find(u =>
                (u.email.toLowerCase() === identifier.toLowerCase().trim() || u.id.toLowerCase() === identifier.toLowerCase().trim()) &&
                u.password === password
            );

            if (user) {
                setSession(user);
                return { success: true, user: user };
            } else {
                return { success: false, message: 'Invalid credentials. Please check your details.' };
            }
        },

        logout: function () {
            clearSession();
            window.location.href = 'index.html?action=logged_out';
        },

        // Update Distributor Profile
        updateDistributorProfile: function (profileData) {
            const session = getSession();
            if (!session || !session.user) {
                return { success: false, message: 'No active distributor session found.' };
            }

            const distributors = getRegisteredDistributors();
            const index = distributors.findIndex(d => d.id === session.user.id || d.email.toLowerCase() === session.user.email.toLowerCase());

            // Check email uniqueness if email is changed
            if (profileData.email && profileData.email.toLowerCase() !== session.user.email.toLowerCase()) {
                const isTaken = distributors.some(d => d.email.toLowerCase() === profileData.email.toLowerCase().trim() && d.id !== session.user.id);
                if (isTaken) {
                    return { success: false, message: 'An account with this email address is already registered.' };
                }
            }

            const updatedUser = {
                ...session.user,
                name: profileData.name || session.user.name,
                email: profileData.email ? profileData.email.trim() : session.user.email,
                phone: profileData.phone ? profileData.phone.trim() : session.user.phone,
                company: profileData.company || session.user.company,
            };

            if (index !== -1) {
                distributors[index] = updatedUser;
                saveDistributorsList(distributors);
            }

            setSession(updatedUser);

            return {
                success: true,
                user: updatedUser,
                message: 'Distributor Profile updated successfully!'
            };
        },

        // Custom Toast Notification System

        showToast: function (message, type = 'success') {
            let toastEl = document.getElementById('customToastNotification');
            if (!toastEl) {
                toastEl = document.createElement('div');
                toastEl.id = 'customToastNotification';
                toastEl.className = 'custom-toast';
                document.body.appendChild(toastEl);
            }

            const borderColor = type === 'error' ? '#ef4444' : (type === 'warning' ? '#f59e0b' : '#06b6d4');
            const icon = type === 'error' ? '⚠️' : (type === 'warning' ? '🔔' : '✅');

            toastEl.style.borderLeftColor = borderColor;
            toastEl.innerHTML = `
                <div class="d-flex align-items-center gap-3">
                    <span class="fs-5">${icon}</span>
                    <div>
                        <div class="fw-semibold text-light">${type.toUpperCase()}</div>
                        <div class="small text-secondary">${message}</div>
                    </div>
                </div>
            `;

            toastEl.classList.add('show');
            setTimeout(() => {
                toastEl.classList.remove('show');
            }, 4000);
        }
    };
})();
