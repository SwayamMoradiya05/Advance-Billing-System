/* ==========================================================================
   Advance Billing System with QR - Admin Dashboard Logic
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Enforce Strict Route Guard for Admin Role
    if (!AuthManager.enforceRouteGuard('admin')) return;

    // 2. Render Active Admin Profile
    const user = AuthManager.getUser();
    if (user) {
        document.getElementById('adminNavName').textContent = user.name;
        document.getElementById('adminNavRole').textContent = user.designation;
        if (user.avatar) {
            document.getElementById('adminNavAvatar').src = user.avatar;
        }
    }

    // 3. Initialize Item Line Calculator for QR Invoice Builder
    initInvoiceCalculator();

    // 4. Load Mock Distributor Table Data
    renderDistributorTable();
});

// Dynamic Invoice Form Item Management
function initInvoiceCalculator() {
    const itemsContainer = document.getElementById('invoiceItemsList');
    const btnAddItem = document.getElementById('btnAddInvoiceItem');
    const form = document.getElementById('qrInvoiceForm');

    if (!itemsContainer || !btnAddItem) return;

    btnAddItem.onclick = () => {
        const rowId = Date.now();
        const rowHTML = `
            <div class="row g-2 align-items-center mb-2 invoice-item-row" id="itemRow_${rowId}">
                <div class="col-md-5">
                    <input type="text" class="form-control form-control-dark item-desc" placeholder="Product / Service Description" required>
                </div>
                <div class="col-md-2">
                    <input type="number" class="form-control form-control-dark item-qty" value="1" min="1" required>
                </div>
                <div class="col-md-3">
                    <input type="number" class="form-control form-control-dark item-price" value="100" min="0" step="0.01" required>
                </div>
                <div class="col-md-2 text-end">
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeInvoiceItem('${rowId}')">✕</button>
                </div>
            </div>
        `;
        itemsContainer.insertAdjacentHTML('beforeend', rowHTML);
        attachCalcListeners();
        calculateTotals();
    };

    attachCalcListeners();
    calculateTotals();

    form.onsubmit = (e) => {
        e.preventDefault();
        generateAdminInvoiceQR();
    };
}

function removeInvoiceItem(rowId) {
    const row = document.getElementById(`itemRow_${rowId}`);
    if (row) {
        row.remove();
        calculateTotals();
    }
}

function attachCalcListeners() {
    document.querySelectorAll('.item-qty, .item-price').forEach(input => {
        input.oninput = calculateTotals;
    });
}

function calculateTotals() {
    let subtotal = 0;
    document.querySelectorAll('.invoice-item-row').forEach(row => {
        const qty = parseFloat(row.querySelector('.item-qty').value) || 0;
        const price = parseFloat(row.querySelector('.item-price').value) || 0;
        subtotal += qty * price;
    });

    const tax = subtotal * 0.18; // 18% GST / Tax
    const total = subtotal + tax;

    document.getElementById('invSubtotalText').textContent = `₹${subtotal.toFixed(2)}`;
    document.getElementById('invTaxText').textContent = `₹${tax.toFixed(2)}`;
    document.getElementById('invTotalText').textContent = `₹${total.toFixed(2)}`;
}

// Generate Dynamic Invoice QR
function generateAdminInvoiceQR() {
    const distSelect = document.getElementById('invDistributorSelect');
    const distId = distSelect.value;
    const distName = distSelect.options[distSelect.selectedIndex].text;
    const invoiceNum = 'INV-' + Math.floor(100000 + Math.random() * 900000);
    const dateStr = new Date().toLocaleDateString();

    const items = [];
    document.querySelectorAll('.invoice-item-row').forEach(row => {
        items.push({
            desc: row.querySelector('.item-desc').value,
            qty: row.querySelector('.item-qty').value,
            price: row.querySelector('.item-price').value
        });
    });

    const totalStr = document.getElementById('invTotalText').textContent;

    // Build encoded QR JSON payload
    const qrDataPayload = JSON.stringify({
        type: 'OFFICIAL_INVOICE',
        invoiceNum: invoiceNum,
        distributorId: distId,
        distributorName: distName,
        date: dateStr,
        total: totalStr,
        itemCount: items.length,
        signature: 'SECURE-SIG-' + Math.random().toString(36).substring(7).toUpperCase()
    });

    // Render QR Code using QREngine
    const qrContainer = document.getElementById('generatedInvoiceQR');
    QREngine.generateQR(qrContainer, qrDataPayload, 190);

    // Show output meta
    document.getElementById('invResultNum').textContent = invoiceNum;
    document.getElementById('invResultDist').textContent = distName;
    document.getElementById('invResultTotal').textContent = totalStr;

    document.getElementById('qrInvoiceOutputBox').classList.remove('d-none');
    AuthManager.showToast(`Invoice ${invoiceNum} generated with Embedded Verification QR!`, 'success');
}

// Mock Distributor Data Table
function renderDistributorTable() {
    const distributors = [
        { id: 'DIST-8842', name: 'Apex Global Supplies', contact: 'David Miller', creditLimit: 150000, creditUsed: 37550, status: 'Active' },
        { id: 'DIST-9021', name: 'Nexus Enterprise Logistics', contact: 'Elena Rostova', creditLimit: 250000, creditUsed: 39200, status: 'Active' },
        { id: 'DIST-4410', name: 'Metro Wholesale Corp', contact: 'Robert Chen', creditLimit: 100000, creditUsed: 89400, status: 'Review Required' },
        { id: 'DIST-7712', name: 'Horizon Regional Traders', contact: 'Amara Patel', creditLimit: 180000, creditUsed: 12000, status: 'Active' }
    ];

    const tbody = document.getElementById('distributorTableBody');
    if (!tbody) return;

    tbody.innerHTML = distributors.map(d => {
        const avail = d.creditLimit - d.creditUsed;
        const usedPct = Math.round((d.creditUsed / d.creditLimit) * 100);
        const statusBadge = d.status === 'Active' ? 'success' : 'warning';

        return `
            <tr>
                <td>
                    <div class="fw-bold text-light">${d.name}</div>
                    <div class="small text-secondary">ID: <code>${d.id}</code> • Rep: ${d.contact}</div>
                </td>
                <td>₹${d.creditLimit.toLocaleString()}</td>
                <td>
                    <div class="d-flex justify-content-between small mb-1">
                        <span>₹${d.creditUsed.toLocaleString()} (${usedPct}%)</span>
                        <span class="text-admin">₹${avail.toLocaleString()} avail</span>
                    </div>
                    <div class="progress" style="height: 6px; background: rgba(255,255,255,0.08);">
                        <div class="progress-bar ${usedPct > 80 ? 'bg-warning' : 'bg-success'}" style="width: ${usedPct}%"></div>
                    </div>
                </td>
                <td><span class="status-pill ${statusBadge}">${d.status}</span></td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-dark-custom" onclick="AuthManager.showToast('Credit line adjusted for ${d.name}', 'info')">
                        Adjust Credit
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}
