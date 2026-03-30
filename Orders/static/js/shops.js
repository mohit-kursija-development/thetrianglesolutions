// Shops JavaScript

let allShops = [];
let currentShopId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
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
    
    let html = `
        <div class="shop-header">
            <div class="shop-header-title">
                <i class="bi bi-shop"></i>
                <h3>${shop.name}</h3>
            </div>
            <div class="shop-header-address">
                <i class="bi bi-geo-alt"></i> ${shop.address}
            </div>
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
                        <button class="collect-btn" onclick="collectPayment(${order.id})">
                            <i class="bi bi-check-circle"></i> Collect
                        </button>
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
