const cart = {}; // Format: { productId: { name, quantity, price, originalPrice, stock } }
let selectedShopId = null;
let allShops = [];

// Initialize the dropdown with all shops on page load
$(document).ready(function() {
    const $shopDropdown = $('#shopDropdown');
    const $shopOptions = $shopDropdown.find('.shop-option');
    
    allShops = $shopOptions.map(function() {
        return {
            id: $(this).attr('onclick').match(/\d+/)[0],
            name: $(this).find('.shop-option-name').text(),
            address: $(this).find('.shop-option-address').text().replace('📍 ', '')
        };
    }).get();
    
    console.log('Shops loaded:', allShops);
    
    // Show dropdown on focus
    $('#shopSearchInput').on('focus', function() {
        $shopDropdown.addClass('show');
    });
    
    // Hide dropdown when clicking outside
    $(document).on('click', function(event) {
        if (!$(event.target).closest('.search-container').length) {
            $shopDropdown.removeClass('show');
        }
    });
});

// Filter shops based on search input
function filterShops() {
    const searchInput = $('#shopSearchInput').val().toLowerCase();
    const $shopDropdown = $('#shopDropdown');
    const $shopOptions = $shopDropdown.find('.shop-option');
    
    // Show dropdown when typing
    $shopDropdown.addClass('show');
    
    $shopOptions.each(function() {
        const $option = $(this);
        const shopName = $option.find('.shop-option-name').text().toLowerCase();
        const shopAddress = $option.find('.shop-option-address').text().toLowerCase();
        
        if (shopName.includes(searchInput) || shopAddress.includes(searchInput) || searchInput === '') {
            $option.show();
        } else {
            $option.hide();
        }
    });
    
    // Hide dropdown if search is empty on focus out
    if (searchInput === '') {
        setTimeout(() => {
            $shopDropdown.removeClass('show');
        }, 100);
    }
}

// Select a shop and load its products
function selectShop(shopId, shopName) {
    selectedShopId = shopId;
    const $shopDropdown = $('#shopDropdown');
    const $selectedDisplay = $('#selectedShopDisplay');
    
    $('#shopSearchInput').val(shopName);
    $shopDropdown.removeClass('show');
    $selectedDisplay.show();
    $('#selectedShopName').text(shopName);
    
    loadProducts();
}

// Load products for the selected shop
async function loadProducts() {
    if (!selectedShopId) {
        $('#productsContainer').html('<div class="no-products-message">Select a shop to view products</div>');
        return;
    }

    try {
        const response = await fetch(`/api/products`);
        const data = await response.json();
        
        if (data.error) {
            $('#productsContainer').html(`<div class="no-products-message">Error: ${data.error}</div>`);
            return;
        }
        
        displayProducts(data.products);
    } catch (error) {
        console.error('Error loading products:', error);
        $('#productsContainer').html('<div class="no-products-message">Error loading products</div>');
    }
}

// Display products in a grid
function displayProducts(products) {
    const $container = $('#productsContainer');
    
    if (!products || products.length === 0) {
        $container.html('<div class="no-products-message">No products available for this shop</div>');
        return;
    }

    let html = '<div class="products-grid">';
    
    products.forEach(product => {
        const isOutOfStock = !product.stock || product.stock <= 0;
        const stockStatus = isOutOfStock ? '<span class="stock-badge out-of-stock">OUT OF STOCK</span>' : `<span class="stock-badge in-stock">Stock: ${product.stock}</span>`;
        
        html += `
            <div class="product-card ${isOutOfStock ? 'out-of-stock-card' : ''}">
                <div class="product-name">${product.name}</div>
                <div class="product-price" id="price-${product.id}">₹${product.price.toFixed(2)}</div>
                <div class="product-stock">${stockStatus}</div>
                <div class="quantity-buttons">
                    ${[1, 3, 5, 10, 20].map(qty => `
                        <button class="qty-btn ${isOutOfStock ? 'disabled' : ''}" 
                                onclick="addToCart(${product.id}, ${qty}, '${product.name}', ${product.price}, ${product.stock})"
                                ${isOutOfStock ? 'disabled' : ''}>
                            ${qty} 
                        </button>
                    `).join('')}
                </div>
                
                <div class="price-edit-section">
                    <label class="price-edit-label">Edit Price:</label>
                    <input type="number" class="price-input" id="price-input-${product.id}" 
                           value="${product.price}" step="0.01" 
                           onchange="updateProductPrice(${product.id}, this.value)">
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    $container.html(html);
}

// Update product price when user edits
function updateProductPrice(productId, newPrice) {
    const $priceElement = $(`#price-${productId}`);
    $priceElement.text(`₹${parseFloat(newPrice).toFixed(2)}`);
    
    // Update in cart if product is already added
    if (cart[productId]) {
        cart[productId].originalPrice = parseFloat(newPrice);
        cart[productId].price = parseFloat(newPrice);
        updateCart();
    }
}

// Add product to cart
function addToCart(productId, quantity, productName, basePrice, stock) {
    const $priceInput = $(`#price-input-${productId}`);
    const actualPrice = $priceInput.length ? parseFloat($priceInput.val()) : basePrice;

    // Validate stock availability
    if (!stock || stock <= 0) {
        alert(`❌ No stock available for "${productName}". Please contact admin.`);
        return;
    }

    const currentQuantityInCart = cart[productId] ? cart[productId].quantity : 0;
    const totalQuantity = currentQuantityInCart + quantity;

    if (totalQuantity > stock) {
        alert(`❌ Insufficient stock for "${productName}". Available: ${stock}, Requested: ${totalQuantity}`);
        return;
    }

    if (cart[productId]) {
        cart[productId].quantity += quantity;
    } else {
        cart[productId] = {
            name: productName,
            quantity: quantity,
            price: actualPrice,
            originalPrice: basePrice,
            stock: stock
        };
    }

    updateCart();
}

// Remove product from cart
function removeFromCart(productId) {
    delete cart[productId];
    updateCart();
}

// Update cart display
function updateCart() {
    const $cartItemsContainer = $('#cartItems');
    const $totalPriceElement = $('#totalPrice');
    const $generateOrderBtn = $('#generateOrderBtn');

    if (Object.keys(cart).length === 0) {
        $cartItemsContainer.html('<div class="no-items-message">No items selected</div>');
        $totalPriceElement.text('₹0.00');
        $generateOrderBtn.prop('disabled', true);
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
                    <div>Qty: ${item.quantity} </div>
                    <div>Price: ₹${item.price.toFixed(2)}</div>
                    <div style="font-weight: 600; color: #667eea;">Total: ₹${itemTotal.toFixed(2)}</div>
                </div>
            </div>
        `;
    });

    $cartItemsContainer.html(cartHtml);
    $totalPriceElement.text(`₹${totalPrice.toFixed(2)}`);
    $generateOrderBtn.prop('disabled', false);
}

// Generate/Save order
async function generateOrder() {
    if (!selectedShopId || Object.keys(cart).length === 0) {
        alert('Please select a shop and add items to cart');
        return;
    }

    const items = Object.entries(cart).map(([productId, item]) => ({
        product_id: parseInt(productId),
        quantity: item.quantity,
        price: item.price
    }));

    try {
        const response = await fetch('/api/create-order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                shop_id: parseInt(selectedShopId),
                items: items
            })
        });

        const data = await response.json();
        
        if (data.success) {
            alert(`✅ Bill #${data.order_id} saved successfully!`);
            
            // Clear cart and reset
            Object.keys(cart).forEach(key => delete cart[key]);
            updateCart();
            
            // Reset shop selection
            selectedShopId = null;
            $('#shopSearchInput').val('');
            $('#selectedShopDisplay').hide();
            $('#productsContainer').html('<div class="no-products-message">Select a shop to view products</div>');
        } else {
            alert('❌ Error saving bill: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error creating order:', error);
        alert('❌ Error saving bill');
    }
}
