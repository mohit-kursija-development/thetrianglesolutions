// Load order details on page load
$(document).ready(function() {
    loadOrderDetails();
});

// Load order from API
async function loadOrderDetails() {
    try {
        const response = await fetch(`/api/get-order/${orderId}`);
        
        if (!response.ok) {
            $('#productsContainer').html('<div class="no-products-message">Error loading order</div>');
            return;
        }
        
        orderData = await response.json();
        
        // Display shop info
        $('#selectedShopName').text(orderData.shop_name);
        
        // Initialize cart with existing items
        orderData.items.forEach(item => {
            cart[item.product_id] = {
                name: item.product_name,
                quantity: item.quantity,
                price: item.price,
                originalPrice: item.price
            };
        });
        
        displayOrderItems();
        updateCart();
    } catch (error) {
        console.error('Error loading order:', error);
        $('#productsContainer').html('<div class="no-products-message">Error loading order details</div>');
    }
}

// Display order items as editable cards
function displayOrderItems() {
    const $container = $('#productsContainer');
    
    if (!orderData.items || orderData.items.length === 0) {
        $container.html('<div class="no-products-message">No items in this order</div>');
        return;
    }

    let html = '<div class="products-grid">';
    
    orderData.items.forEach(item => {
        html += `
            <div class="product-card">
                <div class="product-name">${item.product_name}</div>
                <div class="product-price" id="price-${item.product_id}">₹${item.price.toFixed(2)}</div>
                
                <div class="quantity-section" style="margin: 15px 0; padding: 15px; background: #f9f9f9; border-radius: 8px;">
                    <label style="font-size: 13px; font-weight: 600; color: #666; display: block; margin-bottom: 8px;">Edit Quantity:</label>
                    <input type="number" class="qty-input" id="qty-${item.product_id}" 
                           value="${item.quantity}" step="0.1" min="0"
                           onchange="updateItemQuantity(${item.product_id}, this.value)"
                           style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px;">
                </div>
                
                <div class="price-edit-section">
                    <label class="price-edit-label">Edit Price:</label>
                    <input type="number" class="price-input" id="price-input-${item.product_id}" 
                           value="${item.price}" step="0.01" min="0"
                           onchange="updateItemPrice(${item.product_id}, this.value)">
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    $container.html(html);
}

// Update item quantity
function updateItemQuantity(productId, newQuantity) {
    const qty = parseFloat(newQuantity);
    
    if (qty === 0) {
        delete cart[productId];
    } else if (cart[productId]) {
        cart[productId].quantity = qty;
    }
    
    updateCart();
}

// Update item price
function updateItemPrice(productId, newPrice) {
    const price = parseFloat(newPrice);
    
    if (cart[productId]) {
        cart[productId].price = price;
    }
    
    const $priceElement = $(`#price-${productId}`);
    $priceElement.text(`₹${price.toFixed(2)}`);
    
    updateCart();
}

// Update cart display
function updateCart() {
    const $cartItemsContainer = $('#cartItems');
    const $totalPriceElement = $('#totalPrice');

    if (Object.keys(cart).length === 0) {
        $cartItemsContainer.html('<div class="no-items-message">No items in order</div>');
        $totalPriceElement.text('₹0.00');
        return;
    }

    let totalPrice = 0;
    let cartHtml = '';
    
    $.each(cart, function(productId, item) {
        const itemTotal = item.quantity * item.price;
        totalPrice += itemTotal;
        cartHtml += `
            <div class="cart-item">
                <div class="cart-item-header">
                    <span class="cart-item-name">${item.name}</span>
                    <span class="cart-item-remove" onclick="removeFromCart(${productId})">✕ Remove</span>
                </div>
                <div class="cart-item-details">
                    <div>Qty: ${item.quantity}</div>
                    <div>Price: ₹${item.price.toFixed(2)} /-</div>
                    <div style="font-weight: 600; color: #667eea;">Total: ₹${itemTotal.toFixed(2)}</div>
                </div>
            </div>
        `;
    });

    $cartItemsContainer.html(cartHtml);
    $totalPriceElement.text(`₹${totalPrice.toFixed(2)}`);
}

// Remove item from cart
function removeFromCart(productId) {
    delete cart[productId];
    $(`#qty-${productId}`).val(0);
    updateCart();
}

// Update order
async function updateOrder() {
    if (Object.keys(cart).length === 0) {
        alert('Please add at least one item to the order');
        return;
    }

    const items = Object.entries(cart).map(([productId, item]) => ({
        product_id: parseInt(productId),
        quantity: item.quantity,
        price: item.price
    }));

    try {
        const response = await fetch(`/api/update-order/${orderId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                items: items
            })
        });

        const data = await response.json();
        
        if (data.success) {
            alert(`✅ Order #${orderId} updated successfully!`);
            window.location.href = '/past-orders';
        } else {
            alert('❌ Error updating order: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error updating order:', error);
        alert('❌ Error updating order');
    }
}

// Delete order
async function deleteOrder() {
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
            window.location.href = '/past-orders';
        } else {
            alert('❌ Error deleting order: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error deleting order:', error);
        alert('❌ Error deleting order');
    }
}

// Print order (placeholder for future implementation)
function printOrder() {
    alert('🖨️ Print functionality will be available soon!');
    // Future implementation: window.print() or custom print layout
}
