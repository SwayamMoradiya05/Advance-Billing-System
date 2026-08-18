/* ==========================================================================
   Advance Billing System with QR - QR Generator & Scanner Engine
   ========================================================================== */

const QREngine = (function () {
    return {
        /**
         * Render a QR code into a container element
         * @param {string|HTMLElement} containerIdOrEl 
         * @param {string} textToEncode 
         * @param {number} size 
         */
        generateQR: function (containerIdOrEl, textToEncode, size = 180) {
            const container = typeof containerIdOrEl === 'string' ? document.getElementById(containerIdOrEl) : containerIdOrEl;
            if (!container) return;

            container.innerHTML = ''; // Clear container

            if (typeof QRCode !== 'undefined') {
                new QRCode(container, {
                    text: textToEncode,
                    width: size,
                    height: size,
                    colorDark: '#0b0f19',
                    colorLight: '#ffffff',
                    correctLevel: QRCode.CorrectLevel.H
                });
            } else {
                // SVG / Canvas Fallback Generator if QRCode library isn't loaded yet
                const canvas = document.createElement('canvas');
                canvas.width = size;
                canvas.height = size;
                const ctx = canvas.getContext('2d');
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(0, 0, size, size);
                ctx.fillStyle = '#0b0f19';
                ctx.font = '12px monospace';
                ctx.textAlign = 'center';
                ctx.fillText('QR CODE', size / 2, size / 2 - 10);
                ctx.font = '10px monospace';
                ctx.fillText(textToEncode.substring(0, 16), size / 2, size / 2 + 10);
                container.appendChild(canvas);
            }
        },

        /**
         * Opens the universal QR Auth Modal
         * @param {function} onScanSuccessCallback 
         */
        openScannerModal: function (onScanSuccessCallback) {
            let modalEl = document.getElementById('qrScannerModal');
            if (!modalEl) {
                this.createScannerModalDOM();
                modalEl = document.getElementById('qrScannerModal');
            }

            const modal = new bootstrap.Modal(modalEl);
            modal.show();

            // Setup Demo QR Quick Selectors inside modal for effortless testing
            const demoButtonsContainer = document.getElementById('qrModalDemoButtons');
            if (demoButtonsContainer) {
                demoButtonsContainer.innerHTML = `
                    <div class="small text-secondary mb-2 fw-semibold">Or Click a Demo QR Pass token:</div>
                    <div class="d-flex flex-wrap gap-2 justify-content-center">
                        <button type="button" class="btn btn-sm btn-outline-success rounded-pill demo-qr-btn" data-token="QR-ADMIN-SUPER-8871">
                            🛡️ Super Admin QR Pass
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-info rounded-pill demo-qr-btn" data-token="QR-DIST-APEX-8842">
                            📦 Apex Distributor QR Pass
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-info rounded-pill demo-qr-btn" data-token="QR-DIST-NEXUS-9021">
                            🚚 Nexus Logistics QR Pass
                        </button>
                    </div>
                `;

                demoButtonsContainer.querySelectorAll('.demo-qr-btn').forEach(btn => {
                    btn.onclick = (e) => {
                        const token = e.currentTarget.getAttribute('data-token');
                        modal.hide();
                        if (onScanSuccessCallback) onScanSuccessCallback(token);
                    };
                });
            }

            // Handle manual input fallback
            const manualSubmitBtn = document.getElementById('btnSubmitManualQR');
            const manualInput = document.getElementById('manualQRInput');
            if (manualSubmitBtn && manualInput) {
                manualSubmitBtn.onclick = () => {
                    const token = manualInput.value.trim();
                    if (token) {
                        modal.hide();
                        if (onScanSuccessCallback) onScanSuccessCallback(token);
                    }
                };
            }
        },

        createScannerModalDOM: function () {
            const modalHTML = `
                <div class="modal fade" id="qrScannerModal" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content glass-panel border-secondary">
                            <div class="modal-header border-secondary">
                                <h5 class="modal-title text-light d-flex align-items-center gap-2">
                                    <span>📷</span> QR Pass Scanner Portal
                                </h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body text-center p-4">
                                <div class="scanner-viewport mb-3">
                                    <div class="scanner-laser"></div>
                                    <div class="scanner-target"></div>
                                    <div class="text-secondary small z-1">Position QR Code in scanner box</div>
                                </div>

                                <div id="qrModalDemoButtons" class="mt-3 p-3 rounded bg-dark-card border border-secondary"></div>

                                <div class="mt-3 text-start">
                                    <label class="form-label text-secondary small">Enter or Paste QR Code Pass Key Manually:</label>
                                    <div class="input-group">
                                        <input type="text" id="manualQRInput" class="form-control form-control-dark" placeholder="e.g. QR-ADMIN-SUPER-8871">
                                        <button class="btn btn-admin" type="button" id="btnSubmitManualQR">Authenticate</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }
    };
})();
