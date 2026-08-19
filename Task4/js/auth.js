const AuthManager = (function () {
    const STORAGE_KEY = 'abs_user_session';

    const DEMO_USERS = {
        admin: [
            {
                id: 'ADM-001',
                email: 'admin@gmail.com',
                password: 'admin@gmail.com',
                name: 'Swayam',
                role: 'admin',
                designation: 'Super Administrator',
                badge: 'Level 5 Clearance',
                avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80'
            },
            {
                id: 'ADM-002',
                email: 'manager@billing.com',
                password: 'manager123',
                name: 'Marcus Vance',
                role: 'admin',
                designation: 'Store Operations Manager',
                badge: 'Level 3 Clearance',
                avatar: 'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=150&auto=format&fit=crop&q=80'
            }
        ],
        distributor: [
            {
                id: 'DIST-8842',
                email: 'apex@distributor.com',
                password: 'dist123',
                pin: '8842',
                name: 'David Miller',
                company: 'Apex Global Supplies',
                role: 'distributor',
                creditLimit: 150000,
                creditAvailable: 112450,
                activeOrders: 4,
                badge: 'Tier 1 Preferred Partner',
                avatar: 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150&auto=format&fit=crop&q=80'
            },
            {
                id: 'DIST-9021',
                email: 'nexus@distributor.com',
                password: 'dist123',
                pin: '9021',
                name: 'Elena Rostova',
                company: 'Nexus Enterprise Logistics',
                role: 'distributor',
                creditLimit: 250000,
                creditAvailable: 210800,
                activeOrders: 9,
                badge: 'Diamond Distribution Partner',
                avatar: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80'
            }
        ]
    };

    const QR_TOKENS = {
        'QR-ADMIN-SUPER-8871': DEMO_USERS.admin[0],
        'QR-ADMIN-MANAGER-5524': DEMO_USERS.admin[1],
        'QR-DIST-APEX-8842': DEMO_USERS.distributor[0],
        'QR-DIST-NEXUS-9021': DEMO_USERS.distributor[1]
    };

    function getSession() {
        try {
            const data = localStorage.getItem(STORAGE_KEY);
            return data ? JSON.parse(data) : null;
        } catch (e) {
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

        enforceRouteGuard: function (allowedRole) {
            const user = this.getUser();
            const currentPage = window.location.pathname.split('/').pop() || 'index.html';

            if (!user) {
                const targetLogin = allowedRole === 'admin' ? 'admin-login.html' : 'distributor-login.html';
                window.location.href = `${targetLogin}?redirect=${encodeURIComponent(currentPage)}&reason=unauthenticated`;
                return false;
            }

            if (user.role !== allowedRole) {
                if (user.role === 'admin') {
                    window.location.href = 'admin-dashboard.html?reason=role_mismatch';
                } else {
                    window.location.href = 'distributor-dashboard.html?reason=role_mismatch';
                }
                return false;
            }

            return true;
        },

        login: function (role, identifier, password) {
            const userList = DEMO_USERS[role] || [];
            const user = userList.find(u => 
                (u.email.toLowerCase() === identifier.toLowerCase() || u.id.toLowerCase() === identifier.toLowerCase()) && 
                u.password === password
            );

            if (user) {
                setSession(user);
                return user;
            }
            return null;
        },

        authenticateQR: function (token) {
            const user = QR_TOKENS[token];
            if (user) {
                setSession(user);
                return user;
            }
            return null;
        },

        demoLogin: function (role, index = 0) {
            const user = DEMO_USERS[role][index];
            if (user) {
                setSession(user);
                window.location.href = role === 'admin' ? 'admin-dashboard.html' : 'distributor-dashboard.html';
            }
        },

        logout: function () {
            clearSession();
            window.location.href = 'index.html?action=logged_out';
        },

        showToast: function (message, type = 'success') {
            let toastEl = document.getElementById('customToastNotification');
            if (!toastEl) {
                toastEl = document.createElement('div');
                toastEl.id = 'customToastNotification';
                toastEl.className = 'custom-toast';
                document.body.appendChild(toastEl);
            }

            toastEl.style.borderLeftColor = type === 'error' ? '#ef4444' : (type === 'warning' ? '#f59e0b' : '#10b981');
            toastEl.innerHTML = `
                <div class="d-flex align-items-center gap-3">
                    <span class="fs-5">${type === 'error' ? '⚠️' : '✅'}</span>
                    <div>
                        <div class="fw-semibold text-light">${type.toUpperCase()}</div>
                        <div class="small text-secondary">${message}</div>
                    </div>
                </div>
            `;

            toastEl.classList.add('show');
            setTimeout(() => {
                toastEl.classList.remove('show');
            }, 3500);
        }
    };
})();
