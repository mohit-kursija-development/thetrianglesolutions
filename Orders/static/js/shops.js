// Shops JavaScript

let allShops = [];
let allAreaCodes = [];
let currentShopId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadAreaCodes();
    loadShops();
    
    // Setup search
    document.getElementById('shopSearchInput').addEventListener('keyup', function() {
        const searchTerm = this.value.trim();
        filterAndDisplayShops(searchTerm);
    });
});

// Load all shops from API
function loadShops() {
    fetch('/api/shops-data')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load shops');
            }
            return response.json();
        })
        .then(data => {
            allShops = data.shops;
            displayShops(allShops);
        })
        .catch(error => {
            console.error('Error loading shops:', error);
            document.getElementById('shopsContainer').innerHTML = 
                '<div class="loading-message">Error loading shops. Please refresh the page.</div>';
        });
}

// Load all area codes from API
function loadAreaCodes() {
    fetch('/api/area-codes')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load area codes');
            }
            return response.json();
        })
        .then(data => {
            allAreaCodes = data.area_codes || [];
            populateAreaCodeDropdown();
            if (userRole === 'admin') {
                displayAreaCodes();
            }
        })
        .catch(error => {
            console.error('Error loading area codes:', error);
        });
}

// Populate area code dropdown
function populateAreaCodeDropdown() {
    const dropdown = document.getElementById('shopAreaCode');
    if (!dropdown) return;
    
    const currentValue = dropdown.value;
    
    // Keep the first option (empty)
    dropdown.innerHTML = '<option value="">-- Select Area Code --</option>';
    
    allAreaCodes.forEach(areaCode => {
        const option = document.createElement('option');
        option.value = areaCode.code;
        option.textContent = `${areaCode.code} - ${areaCode.area_name}`;
        dropdown.appendChild(option);
    });
    
    if (currentValue) {
        dropdown.value = currentValue;
    }
}

// Display shops in the list
function displayShops(shops) {
    const container = document.getElementById('shopsContainer');
    
    if (shops.length === 0) {
        container.innerHTML = '<div class="no-items-message">No shops found</div>';
        return;
    }
    
    container.innerHTML = shops.map(shop => `
        <div class="shop-item" onclick="selectShop(${shop.id}, '${shop.name}')">
            <div class="shop-item-header">
                <div class="shop-item-name">
                    <i class="bi bi-shop"></i> ${shop.name}
                </div>
                <div class="shop-item-address">📍 ${shop.address}</div>
            </div>
            ${shop.outstanding > 0 ? `<div class="outstanding-badge">₹${shop.outstanding.toFixed(2)}</div>` : ''}
        </div>
    `).join('');
}

// Filter and display shops based on search
function filterAndDisplayShops(searchTerm) {
    if (!searchTerm) {
        displayShops(allShops);
        return;
    }
    const filtered = allShops.filter(shop => 
        shop.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        shop.address.toLowerCase().includes(searchTerm.toLowerCase())
    );
    displayShops(filtered);
}

// Select a shop and load its details
function selectShop(shopId, shopName) {
    currentShopId = shopId;
    
    // Update active state
    document.querySelectorAll('.shop-item').forEach(item => {
        item.classList.remove('active');
    });
    event.currentTarget.classList.add('active');
    
    // Load and display shop details
    loadShopDetails(shopId);
}

// Load shop details from API
function loadShopDetails(shopId) {
    const detailsContent = document.getElementById('detailsContent');
    detailsContent.innerHTML = '<div class="loading-message">Loading details...</div>';
    
    fetch(`/api/shop-details/${shopId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load shop details');
            }
            return response.json();
        })
        .then(data => {
            displayShopDetails(data);
        })
        .catch(error => {
            console.error('Error loading shop details:', error);
            detailsContent.innerHTML = 
                '<div class="loading-message">Error loading details. Please try again.</div>';
        });
}

// Display shop details
function displayShopDetails(data) {
    const { shop, pending_orders, collected_orders, total_outstanding } = data;
    const isAdmin = userRole === 'admin';
    
    let html = `
        <div class="shop-header">
            <div class="shop-header-title">
                <i class="bi bi-shop"></i>
                <h3>${shop.name}</h3>
            </div>
            ${isAdmin ? `<button class="btn btn-sm btn-primary" onclick="openEditShopModal(${shop.id})"><i class="bi bi-pencil"></i> Edit Shop Details</button>` : ''}
        </div>
        
        <div class="shop-details-section">
            <div class="detail-item">
                <label>Address:</label>
                <p>${shop.address}</p>
            </div>
            ${shop.area_code ? `<div class="detail-item">
                <label>Area Code:</label>
                <p>${shop.area_code} ${shop.area_name ? `- ${shop.area_name}` : ''}</p>
            </div>` : ''}
            ${shop.number_1 ? `<div class="detail-item">
                <label>Number 1:</label>
                <p>${shop.number_1}</p>
            </div>` : ''}
            ${shop.number_2 ? `<div class="detail-item">
                <label>Number 2:</label>
                <p>${shop.number_2}</p>
            </div>` : ''}
        </div>
    `;
    
    // Outstanding section
    if (total_outstanding > 0) {
        html += `
            <div class="outstanding-section">
                <h4><i class="bi bi-exclamation-circle"></i> Outstanding Payment</h4>
                <div class="outstanding-amount">₹${total_outstanding.toFixed(2)}</div>
                <p style="margin: 0; font-size: 12px; color: #856404;">
                    ${pending_orders.length} order(s) pending payment collection
                </p>
            </div>
        `;
    }
    
    // Pending Orders Section
    html += `
        <div class="section">
            <div class="section-title">
                <i class="bi bi-clock"></i> Pending Payments (${pending_orders.length})
            </div>
            <div class="pending-orders-list">
    `;
    
    if (pending_orders.length === 0) {
        html += '<div class="no-items-message">No pending payments</div>';
    } else {
        pending_orders.forEach(order => {
            const date = new Date(order.created_at);
            const dateStr = date.toLocaleDateString('en-IN', { 
                day: '2-digit', 
                month: 'short', 
                year: 'numeric' 
            });
            
            html += `
                <div class="order-item">
                    <div class="order-info">
                        <div class="order-id">Order #${order.id}</div>
                        <div class="order-date">${dateStr}</div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div class="order-amount">₹${order.total.toFixed(2)}</div>
                        ${isAdmin ? `<button class="collect-btn" onclick="collectPayment(${order.id})">
                            <i class="bi bi-check-circle"></i> Collect
                        </button>` : ''}
                    </div>
                </div>
            `;
        });
    }
    
    html += `
            </div>
        </div>
    `;
    
    // Collected Orders Section
    if (collected_orders.length > 0) {
        html += `
            <div class="section">
                <div class="section-title">
                    <i class="bi bi-check-circle-fill"></i> Recently Collected (${collected_orders.length})
                </div>
                <div class="collected-orders-list">
        `;
        
        collected_orders.forEach(order => {
            const createdDate = new Date(order.created_at);
            const collectedDate = new Date(order.collected_at);
            
            const createdStr = createdDate.toLocaleDateString('en-IN', { 
                day: '2-digit', 
                month: 'short', 
                year: 'numeric' 
            });
            const collectedStr = collectedDate.toLocaleDateString('en-IN', { 
                day: '2-digit', 
                month: 'short', 
                year: 'numeric' 
            });
            
            html += `
                <div class="collected-order-item">
                    <div class="collected-order-header">
                        <div class="collected-order-id">Order #${order.id}</div>
                        <div class="collected-amount">₹${order.total.toFixed(2)}</div>
                    </div>
                    <div class="collected-dates">
                        <span>Order: ${createdStr}</span>
                        <span>Collected: ${collectedStr}</span>
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    document.getElementById('detailsContent').innerHTML = html;
}

// Collect payment for an order
function collectPayment(orderId) {
    const button = event.target.closest('.collect-btn');
    button.classList.add('loading');
    button.disabled = true;
    
    fetch(`/api/collect-payment/${orderId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to collect payment');
        }
        return response.json();
    })
    .then(data => {
        // Show success message
        alert('Payment collected successfully!');
        
        // Reload shop details
        if (currentShopId) {
            loadShopDetails(currentShopId);
        }
        
        // Reload shops list to update outstanding amounts
        loadShops();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to collect payment. Please try again.');
        button.classList.remove('loading');
        button.disabled = false;
    });
}

// Open Create Shop Modal
function openCreateShopModal() {
    document.getElementById('modalTitle').textContent = 'Create New Shop';
    document.getElementById('shopForm').reset();
    document.getElementById('submitBtn').textContent = 'Create';
    document.getElementById('submitBtn').onclick = saveShop;
    
    const modal = new bootstrap.Modal(document.getElementById('shopModal'));
    modal.show();
}

// Open Edit Shop Modal
function openEditShopModal(shopId) {
    // Get the shop data from allShops array
    const shop = allShops.find(s => s.id === shopId);
    if (!shop) {
        alert('Shop not found');
        return;
    }
    
    document.getElementById('modalTitle').textContent = 'Edit Shop Details';
    document.getElementById('shopName').value = shop.name;
    document.getElementById('shopAddress').value = shop.address;
    document.getElementById('shopAreaCode').value = shop.area_code || '';
    document.getElementById('shopNumber1').value = shop.number_1 || '';
    document.getElementById('shopNumber2').value = shop.number_2 || '';
    document.getElementById('submitBtn').textContent = 'Update';
    document.getElementById('submitBtn').onclick = () => updateShop(shopId);
    
    const modal = new bootstrap.Modal(document.getElementById('shopModal'));
    modal.show();
}

// Save Shop (Create or Update)
function saveShop() {
    const name = document.getElementById('shopName').value.trim();
    const address = document.getElementById('shopAddress').value.trim();
    const areaCode = document.getElementById('shopAreaCode').value.trim();
    const number1 = document.getElementById('shopNumber1').value.trim();
    const number2 = document.getElementById('shopNumber2').value.trim();
    
    if (!name || !address) {
        alert('Please fill in Shop Name and Address');
        return;
    }
    
    const shopData = {
        name: name,
        address: address,
        area_code: areaCode || null,
        number_1: number1,
        number_2: number2
    };
    
    fetch('/api/create-shop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(shopData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to create shop');
        }
        return response.json();
    })
    .then(data => {
        alert('Shop created successfully!');
        bootstrap.Modal.getInstance(document.getElementById('shopModal')).hide();
        loadShops();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to create shop. Please try again.');
    });
}

// Update Shop
function updateShop(shopId) {
    const name = document.getElementById('shopName').value.trim();
    const address = document.getElementById('shopAddress').value.trim();
    const areaCode = document.getElementById('shopAreaCode').value.trim();
    const number1 = document.getElementById('shopNumber1').value.trim();
    const number2 = document.getElementById('shopNumber2').value.trim();
    
    if (!name || !address) {
        alert('Please fill in Shop Name and Address');
        return;
    }
    
    const shopData = {
        name: name,
        address: address,
        area_code: areaCode || null,
        number_1: number1,
        number_2: number2
    };
    
    fetch(`/api/update-shop/${shopId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(shopData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to update shop');
        }
        return response.json();
    })
    .then(data => {
        alert('Shop updated successfully!');
        bootstrap.Modal.getInstance(document.getElementById('shopModal')).hide();
        loadShops();
        if (currentShopId) {
            loadShopDetails(currentShopId);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to update shop. Please try again.');
    });
}

// Open Area Code Panel (Sidebar)
function openAreaCodePanel() {
    const offcanvas = new bootstrap.Offcanvas(document.getElementById('areaCodePanel'));
    offcanvas.show();
}

// Display area codes in the sidebar
function displayAreaCodes() {
    const container = document.getElementById('areaCodesList');
    
    if (allAreaCodes.length === 0) {
        container.innerHTML = '<div class="text-muted">No area codes created yet</div>';
        return;
    }
    
    container.innerHTML = allAreaCodes.map(areaCode => `
        <div class="area-code-item">
            <div class="area-code-header">
                <strong>${areaCode.code}</strong>
                <button class="btn btn-sm btn-link edit-area-code-btn" data-code="${areaCode.code}" data-name="${areaCode.area_name}">
                    <i class="bi bi-pencil"></i>
                </button>
            </div>
            <small>${areaCode.area_name}</small>
        </div>
    `).join('');
    
    // Add event listeners to edit buttons
    document.querySelectorAll('.edit-area-code-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const code = this.dataset.code;
            const area_name = this.dataset.area_name;
            openEditAreaCodeModal(code, area_name);
        });
    });
}

// Open Create Area Code Modal
function openCreateAreaCodeModal() {
    document.getElementById('areaCodeModalTitle').textContent = 'Create Area Code';
    document.getElementById('areaCodeForm').reset();
    document.getElementById('areaCodeInput').disabled = false;
    document.getElementById('areaCodeSubmitBtn').textContent = 'Create';
    document.getElementById('areaCodeSubmitBtn').onclick = saveAreaCode;
    
    const modal = new bootstrap.Modal(document.getElementById('areaCodeModal'));
    modal.show();
}

// Open Edit Area Code Modal
function openEditAreaCodeModal(code, area_name) {
    document.getElementById('areaCodeModalTitle').textContent = 'Edit Area Code';
    document.getElementById('areaCodeInput').value = code;
    document.getElementById('areaCodeName').value = area_name;
    document.getElementById('areaCodeInput').disabled = true;
    document.getElementById('areaCodeSubmitBtn').textContent = 'Update';
    document.getElementById('areaCodeSubmitBtn').onclick = () => updateAreaCode(code);
    
    const modal = new bootstrap.Modal(document.getElementById('areaCodeModal'));
    modal.show();
}

// Save Area Code (Create)
function saveAreaCode() {
    const code = document.getElementById('areaCodeInput').value.trim().toUpperCase();
    const area_name = document.getElementById('areaCodeName').value.trim();
    
    if (!code || !area_name) {
        alert('Please fill in both Area Code and Name');
        return;
    }
    
    const areaCodeData = {
        code: code,
        area_name: area_name
    };
    
    fetch('/api/create-area-code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(areaCodeData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to create area code');
        }
        return response.json();
    })
    .then(data => {
        alert('Area code created successfully!');
        bootstrap.Modal.getInstance(document.getElementById('areaCodeModal')).hide();
        loadAreaCodes();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to create area code. It may already exist.');
    });
}

// Update Area Code
function updateAreaCode(code) {
    const area_name = document.getElementById('areaCodeName').value.trim();
    
    if (!area_name) {
        alert('Please fill in the Area Name');
        return;
    }
    
    const areaCodeData = {
        area_name: area_name
    };
    
    fetch(`/api/update-area-code/${code}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(areaCodeData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to update area code');
        }
        return response.json();
    })
    .then(data => {
        alert('Area code updated successfully!');
        bootstrap.Modal.getInstance(document.getElementById('areaCodeModal')).hide();
        loadAreaCodes();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to update area code. Please try again.');
    });
}
