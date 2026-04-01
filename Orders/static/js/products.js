let allProducts = [];

// Load products when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadProducts();
    
    // Search functionality
    document.getElementById('searchInput').addEventListener('keyup', function() {
        filterProducts();
    });
});

function loadProducts() {
    fetch('/api/products')
        .then(response => response.json())
        .then(data => {
            allProducts = data.products;
            displayProducts(allProducts);
        })
        .catch(error => {
            console.error('Error loading products:', error);
            document.getElementById('productsBody').innerHTML = '<tr><td colspan="8" class="text-center text-danger">Error loading products</td></tr>';
        });
}

function displayProducts(productsToDisplay) {
    const tbody = document.getElementById('productsBody');
    
    if (productsToDisplay.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No products found</td></tr>';
        return;
    }
    
    tbody.innerHTML = productsToDisplay.map(product => `
        <tr>
            <td>${product.id}</td>
            <td>${escapeHtml(product.name)}</td>
            <td>${product.stock}</td>
            <td>₹${product.mrp.toFixed(2)}</td>
            <td>₹${product.price.toFixed(2)}</td>
            <td>${formatDate(product.created_at)}</td>
            <td>${formatDate(product.updated_at)}</td>
            <td>
                <button class="btn btn-sm btn-warning" onclick="openEditProductModal(${product.id})">Edit</button>
                <button class="btn btn-sm btn-danger" onclick="deleteProduct(${product.id})">Delete</button>
            </td>
        </tr>
    `).join('');
}

function filterProducts() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const filtered = allProducts.filter(product => 
        product.name.toLowerCase().includes(searchTerm)
    );
    displayProducts(filtered);
}

function openCreateProductModal() {
    document.getElementById('createProductForm').reset();
    document.getElementById('createProductMessage').innerHTML = '';
    const modal = new bootstrap.Modal(document.getElementById('createProductModal'));
    modal.show();
}

function saveProduct() {
    const name = document.getElementById('productName').value;
    const stock = document.getElementById('productStock').value;
    const mrp = document.getElementById('productMrp').value;
    const price = document.getElementById('productPrice').value;
    
    if (!name || !stock || !mrp || !price) {
        document.getElementById('createProductMessage').innerHTML = '<div class="alert alert-danger">All fields are required</div>';
        return;
    }
    
    const messageDiv = document.getElementById('createProductMessage');
    messageDiv.innerHTML = '<div class="alert alert-info">Creating product...</div>';
    
    fetch('/api/create-product', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: name,
            stock: parseInt(stock),
            mrp: parseFloat(mrp),
            price: parseFloat(price)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            messageDiv.innerHTML = '<div class="alert alert-success">Product created successfully!</div>';
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('createProductModal')).hide();
                loadProducts();
            }, 1000);
        } else {
            messageDiv.innerHTML = '<div class="alert alert-danger">' + data.error + '</div>';
        }
    })
    .catch(error => {
        messageDiv.innerHTML = '<div class="alert alert-danger">Error creating product: ' + error + '</div>';
    });
}

function openEditProductModal(productId) {
    const product = allProducts.find(p => p.id === productId);
    if (!product) return;
    
    document.getElementById('editProductId').value = product.id;
    document.getElementById('editProductName').value = product.name;
    document.getElementById('editProductStock').value = product.stock;
    document.getElementById('editProductMrp').value = product.mrp.toFixed(2);
    document.getElementById('editProductPrice').value = product.price.toFixed(2);
    document.getElementById('editProductMessage').innerHTML = '';
    
    const modal = new bootstrap.Modal(document.getElementById('editProductModal'));
    modal.show();
}

function updateProduct() {
    const productId = document.getElementById('editProductId').value;
    const name = document.getElementById('editProductName').value;
    const stock = document.getElementById('editProductStock').value;
    const mrp = document.getElementById('editProductMrp').value;
    const price = document.getElementById('editProductPrice').value;
    
    if (!name || !stock || !mrp || !price) {
        document.getElementById('editProductMessage').innerHTML = '<div class="alert alert-danger">All fields are required</div>';
        return;
    }
    
    const messageDiv = document.getElementById('editProductMessage');
    messageDiv.innerHTML = '<div class="alert alert-info">Updating product...</div>';
    
    fetch(`/api/update-product/${productId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: name,
            stock: parseInt(stock),
            mrp: parseFloat(mrp),
            price: parseFloat(price)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            messageDiv.innerHTML = '<div class="alert alert-success">Product updated successfully!</div>';
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('editProductModal')).hide();
                loadProducts();
            }, 1000);
        } else {
            messageDiv.innerHTML = '<div class="alert alert-danger">' + data.error + '</div>';
        }
    })
    .catch(error => {
        messageDiv.innerHTML = '<div class="alert alert-danger">Error updating product: ' + error + '</div>';
    });
}

function deleteProduct(productId) {
    if (!confirm('Are you sure you want to delete this product?')) {
        return;
    }
    
    fetch(`/api/delete-product/${productId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Product deleted successfully!');
            loadProducts();
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        alert('Error deleting product: ' + error);
    });
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString('en-IN', options);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
