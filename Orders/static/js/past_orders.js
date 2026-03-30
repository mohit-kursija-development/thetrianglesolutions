let allOrders = [];

// Load past orders on page load
$(document).ready(function() {
    loadPastOrders();
});

// Load past orders from API
async function loadPastOrders() {
    try {
        const response = await fetch('/api/past-orders');
        const data = await response.json();
        
        if (data.error) {
            $('#ordersContent').html(`<div class="no-orders-message">Error: ${data.error}</div>`);
            return;
        }
        
        allOrders = data.orders;
        displayOrders(allOrders);
    } catch (error) {
        console.error('Error loading past orders:', error);
        $('#ordersContent').html('<div class="no-orders-message">Error loading past orders</div>');
    }
}

// Display orders
function displayOrders(orders) {
    const $container = $('#ordersContent');
    
    if (!orders || orders.length === 0) {
        $container.html('<div class="no-orders-message"><i class="bi bi-inbox"></i> No past orders found</div>');
        return;
    }
    
    let html = '<div class="orders-list">';
    
    orders.forEach(order => {
        const orderDate = new Date(order.created_at);
        const formattedDate = orderDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        html += `
            <div class="order-card">
                <div class="order-header">
                    <div class="order-id-date">
                        <div class="order-id">Order #${order.id}</div>
                        <div class="order-date">${formattedDate}</div>
                    </div>
                    <div class="order-total">₹${order.total.toFixed(2)}</div>
                </div>
                <div class="order-body">
                    <div class="shop-info">
                        <div class="shop-name"><i class="bi bi-shop"></i> ${order.shop_name}</div>
                        <div class="shop-label">Shop ID: #${order.shop_id}</div>
                    </div>
                    
                    <div class="order-items">
                        <div class="items-title">Items:</div>
                        ${order.items.map(item => `
                            <div class="order-item">
                                <div class="item-name-qty">
                                    ${item.product_name} × ${item.quantity} @ ₹${item.price.toFixed(2)}
                                </div>
                                <div class="item-total">₹${item.total.toFixed(2)}</div>
                            </div>
                        `).join('')}
                    </div>
                    
                    <div class="order-actions">
                        ${userRole === 'admin' ? `
                            <a href="/edit-order/${order.id}" class="edit-btn">
                                <i class="bi bi-pencil-square"></i> Edit
                            </a>
                            <button class="delete-btn" onclick="deleteOrder(${order.id})">
                                <i class="bi bi-trash"></i> Delete
                            </button>
                        ` : `
                            <a href="/edit-order/${order.id}" class="edit-btn" style="opacity: 0.5; cursor: not-allowed;" onclick="event.preventDefault(); alert('Only admin users can edit orders.')">
                                <i class="bi bi-eye"></i> View Only
                            </a>
                        `}
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    $container.html(html);
}

// Search/filter orders
function searchOrders() {
    const searchTerm = $('#searchInput').val().toLowerCase();
    
    const filteredOrders = allOrders.filter(order => 
        order.shop_name.toLowerCase().includes(searchTerm)
    );
    
    displayOrders(filteredOrders);
}

// Delete order
async function deleteOrder(orderId) {
    if (!confirm('Are you sure you want to delete this order? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/delete-order/${orderId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Order deleted successfully!');
            loadPastOrders();
        } else if (response.status === 403) {
            alert('❌ Permission Denied: Only admin users can delete orders');
        } else {
            alert('❌ Error deleting order: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error deleting order:', error);
        alert('❌ Error deleting order');
    }
}
