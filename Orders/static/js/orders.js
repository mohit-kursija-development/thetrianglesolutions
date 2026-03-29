const cart = {}; // Format: { productId: { name, quantity, price, originalPrice, stock } }
let selectedShopId = null;
let allShops = [];

// Initialize the dropdown with all shops on page load
document.addEventListener('DOMContentLoaded', function() {
    const shopDropdown = document.getElementById('shopDropdown');
    const shopOptions = shopDropdown.querySelectorAll('.shop-option');
    allShops = Array.from(shopOptions).map(option => ({
        id: option.getAttribute('onclick').match(/\d+/)[0],
        name: option.querySelector('.shop-option-name').textContent,
        location: option.querySelector('.shop-option-location').textContent.replace('📍 ', '')
    }));
    console.log('Shops loaded:', allShops);
});

// Filter shops based on search input
function filterShops() {
    const searchInput = document.getElementById('shopSearchInput').value.toLowerCase();
    const shopDropdown = document.getElementById('shopDropdown');
    const shopOptions = shopDropdown.querySelectorAll('.shop-option');
    
    // Show dropdown when typing
    shopDropdown.classList.add('show');
    
    shopOptions.forEach(option => {
        const shopName = option.querySelector('.shop-option-name').textContent.toLowerCase();
        const shopLocation = option.querySelector('.shop-option-location').textContent.toLowerCase();
        
        if (shopName.includes(searchInput) || shopLocation.includes(searchInput) || searchInput === '') {
            option.style.display = 'block';
        } else {
            option.style.display = 'none';
        }
    });
    
    // Hide dropdown if search is empty on focus out
    if (searchInput === '') {
        setTimeout(() => {
            shopDropdown.classList.remove('show');
        }, 100);
    }
}

// Show dropdown on focus
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('shopSearchInput');
    if (searchInput) {
        searchInput.addEventListener('focus', function() {
            const shopDropdown = document.getElementById('shopDropdown');
            shopDropdown.classList.add('show');
        });
        
        // Hide dropdown when clicking outside
        document.addEventListener('click', function(event) {
            const shopSearchSection = document.querySelector('.search-container');
            if (!shopSearchSection.contains(event.target)) {
                document.getElementById('shopDropdown').classList.remove('show');
            }
        });
    }
});

// Select a shop and load its products
function selectShop(shopId, shopName) {
    selectedShopId = shopId;
    const searchInput = document.getElementById('shopSearchInput');
    const shopDropdown = document.getElementById('shopDropdown');
    const selectedDisplay = document.getElementById('selectedShopDisplay');
    const selectedShopNameSpan = document.getElementById('selectedShopName');
    
    searchInput.value = shopName;
    shopDropdown.classList.remove('show');
    selectedDisplay.style.display = 'block';
    selectedShopNameSpan.textContent = shopName;
    
    loadProducts();
}

// Load products for the selected shop
async function loadProducts() {
    if (!selectedShopId) {
        document.getElementById('productsContainer').innerHTML = '<div class="no-products-message">Select a shop to view products</div>';
        return;
    }

    try {
        const response = await fetch(`/api/products/${selectedShopId}`);
        const data = await response.json();
        
        if (data.error) {
            document.getElementById('productsContainer').innerHTML = `<div class="no-products-message">Error: ${data.error}</div>`;
            return;
        }
        
        displayProducts(data.products);
    } catch (error) {
        console.error('Error loading products:', error);
        document.getElementById('productsContainer').innerHTML = '<div class="no-products-message">Error loading products</div>';
    }
}

// Display products in a grid
function displayProducts(products) {
    const container = document.getElementById('productsContainer');
    
    if (!products || products.length === 0) {
        container.innerHTML = '<div class="no-products-message">No products available for this shop</div>';
        return;
    }

    container.innerHTML = `
        <div class="products-grid">
            ${products.map(product => `
                <div class="product-card">
                    <div class="product-name">${product.name}</div>
                    <div class="product-price" id="price-${product.id}">₹${product.price.toFixed(2)}</div>
                    <div class="product-description">${product.description || 'No description'}</div>
                    <div class="product-stock">Stock: ${product.stock} units</div>
                    
                    <div class="quantity-buttons">
                        ${[1, 3, 5, 10, 20].map(qty => `
                            <button class="qty-btn" onclick="addToCart(${product.id}, ${qty}, '${product.name}', ${product.price}, ${product.stock})">
                                ${qty} kg
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
            `).join('')}
        </div>
    `;
}

// Update product price when user edits
function updateProductPrice(productId, newPrice) {
    const priceElement = document.getElementById(`price-${productId}`);
    priceElement.textContent = `₹${parseFloat(newPrice).toFixed(2)}`;
    
    // Update in cart if product is already added
    if (cart[productId]) {
        cart[productId].originalPrice = parseFloat(newPrice);
        cart[productId].price = parseFloat(newPrice);
        updateCart();
    }
}

// Add product to cart
function addToCart(productId, quantity, productName, basePrice, stock) {
    const priceInput = document.getElementById(`price-input-${productId}`);
    const actualPrice = priceInput ? parseFloat(priceInput.value) : basePrice;

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
    const cartItemsContainer = document.getElementById('cartItems');
    const totalPriceElement = document.getElementById('totalPrice');
    const generateOrderBtn = document.getElementById('generateOrderBtn');

    if (Object.keys(cart).length === 0) {
        cartItemsContainer.innerHTML = '<div class="no-items-message">No items selected</div>';
        totalPriceElement.textContent = '₹0.00';
        generateOrderBtn.disabled = true;
        return;
    }

    let totalPrice = 0;
    cartItemsContainer.innerHTML = Object.entries(cart).map(([productId, item]) => {
        const itemTotal = item.quantity * item.price;
        totalPrice += itemTotal;
        return `
            <div class="cart-item">
                <div class="cart-item-header">
                    <span class="cart-item-name">${item.name}</span>
                    <span class="cart-item-remove" onclick="removeFromCart(${productId})">✕ Remove</span>
                </div>
                <div class="cart-item-details">
                    <div>Qty: ${item.quantity} kg</div>
                    <div>Price: ₹${item.price.toFixed(2)}/kg</div>
                    <div style="font-weight: 600; color: #667eea;">Total: ₹${itemTotal.toFixed(2)}</div>
                </div>
            </div>
        `;
    }).join('');

    totalPriceElement.textContent = `₹${totalPrice.toFixed(2)}`;
    generateOrderBtn.disabled = false;
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
            document.getElementById('shopSearchInput').value = '';
            document.getElementById('selectedShopDisplay').style.display = 'none';
            document.getElementById('productsContainer').innerHTML = '<div class="no-products-message">Select a shop to view products</div>';
        } else {
            alert('❌ Error saving bill: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error creating order:', error);
        alert('❌ Error saving bill');
    }
}
