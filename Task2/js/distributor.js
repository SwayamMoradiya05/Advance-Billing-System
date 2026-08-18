/* ==========================================================================
   Advance Billing System with QR - Distributor Dashboard Logic
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Enforce Strict Route Guard for Distributor Role
    if (!AuthManager.enforceRouteGuard('distributor')) return;

    // 2. Render Active Distributor Profile
    const user = AuthManager.getUser();
    if (user) {
        document.getElementById('distNavName').textContent = user.name;
        document.getElementById('distNavCompany').textContent = user.company || 'Wholesale Partner';
        
        // Render Credit Bar
        const creditLimit = user.creditLimit || 150000;
        const creditAvail = user.creditAvailable || 112450;
        const used = creditLimit - creditAvail;
        const pct = Math.round((used / creditLimit) * 100);

        document.getElementById('distCreditLimitText').textContent = `₹${creditLimit.toLocaleString()}`;
        document.getElementById('distCreditAvailText').textContent = `₹${creditAvail.toLocaleString()}`;
        document.getElementById('distCreditProgressBar').style.width = `${pct}%`;

        if (user.avatar) {
            document.getElementById('distNavAvatar').src = user.avatar;
        }

        // Generate Digital QR Badge Pass
        const qrBadgeToken = `QR-${user.id}`;
        QREngine.generateQR('distributorDigitalQRCanvas', qrBadgeToken, 160);
        document.getElementById('distQrTokenText').textContent = qrBadgeToken;
    }

    // 3. Render Purchase Orders Table
    renderPurchaseOrders();
});

// QR Scanner Callback for Stock Intake Verification
function scanInvoiceQRForDistributor() {
    QREngine.openScannerModal((scannedToken) => {
        try {
            // Check if token is JSON invoice string or token string
            let invData;
            if (scannedToken.startsWith('{')) {
                invData = JSON.parse(scannedToken);
            } else {
                // Mock payload for scanned demo token
                invData = {
                    type: 'OFFICIAL_INVOICE',
                    invoiceNum: 'INV-2026-8894',
                    distributorId: AuthManager.getUser()?.id || 'DIST-8842',
                    distributorName: AuthManager.getUser()?.company || 'Apex Global Supplies',
                    date: new Date().toLocaleDateString(),
                    total: '₹4,425.00',
                    itemCount: 5,
                    signature: 'SECURE-SIG-APEX-998'
                };
            }

            // Display Verification Modal / Card
            const outputBox = document.getElementById('scanVerificationResultBox');
            document.getElementById('verifyInvNum').textContent = invData.invoiceNum || 'INV-2026-EXPRESS';
            document.getElementById('verifyInvTotal').textContent = invData.total || '₹4,425.00';
            document.getElementById('verifyInvDate').textContent = invData.date || new Date().toLocaleDateString();
            document.getElementById('verifyInvSig').textContent = invData.signature || 'VALID-SECURE-SIG';

            outputBox.classList.remove('d-none');
            outputBox.scrollIntoView({ behavior: 'smooth' });

            AuthManager.showToast(`Invoice ${invData.invoiceNum} Verified & Stock Intake Logged!`, 'success');
        } catch (e) {
            AuthManager.showToast('Invalid invoice QR code structure.', 'error');
        }
    });
}

function renderPurchaseOrders() {
    const orders = [
        { id: 'PO-9942', date: '2026-08-15', items: 'Industrial Microprocessors (x5)', amount: '₹3,750.00', status: 'Dispatched', verified: true },
        { id: 'PO-9918', date: '2026-08-10', items: 'High-Torque Motors (x20)', amount: '₹12,400.00', status: 'Delivered', verified: true },
        { id: 'PO-9850', date: '2026-08-04', items: 'Sensors & Controllers Kit (x50)', amount: '₹8,950.00', status: 'Delivered', verified: true },
        { id: 'PO-9799', date: '2026-07-28', items: 'Heavy Duty Relay Assemblies (x100)', amount: '₹14,200.00', status: 'Delivered', verified: true }
    ];

    const tbody = document.getElementById('purchaseOrdersTableBody');
    if (!tbody) return;

    tbody.innerHTML = orders.map(o => `
        <tr>
            <td>
                <div class="fw-bold text-light">${o.id}</div>
                <div class="small text-muted">${o.date}</div>
            </td>
            <td class="text-secondary">${o.items}</td>
            <td class="fw-bold text-distributor">${o.amount}</td>
            <td><span class="status-pill info">${o.status}</span></td>
            <td>
                ${o.verified 
                    ? '<span class="status-pill success">✓ QR Verified</span>' 
                    : '<button class="btn btn-sm btn-outline-dark-custom" onclick="scanInvoiceQRForDistributor()">Verify QR</button>'}
            </td>
        </tr>
    `).join('');
}
