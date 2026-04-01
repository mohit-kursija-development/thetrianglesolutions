let allPurchases = [];
let allProducts = [];

// Load purchases and products when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadProducts();
    loadPurchases();
    
    // Search functionality
    document.getElementById('searchInput').addEventListener('keyup', function() {
        filterPurchases();
    });
});

function loadProducts() {
    fetch('/api/products')
        .then(response => response.json())
        .then(data => {
            allProducts = data.products;
            populateProductSelect();
        })
        .catch(error => {
            console.error('Error loading products:', error);
        });
}

function populateProductSelect() {
    const select = document.getElementById('productSelect');
    select.innerHTML = '<option value="">Select a product...</option>';
    
    allProducts.forEach(product => {
        const option = document.createElement('option');
        option.value = product.id;
        option.textContent = `${product.name} (Current Stock: ${product.stock})`;
        select.appendChild(option);
    });
}

function loadPurchases() {
    fetch('/api/purchases')
        .then(response => response.json())
        .then(data => {
            allPurchases = data.purchases;
            displayPurchases(allPurchases);
            updateSummary();
        })
        .catch(error => {
            console.error('Error loading purchases:', error);
            document.getElementById('purchasesBody').innerHTML = '<tr><td colspan="8" class="text-center text-danger">Error loading purchases</td></tr>';
        });
}

function displayPurchases(purchasesToDisplay) {
    const tbody = document.getElementById('purchasesBody');
    
    if (purchasesToDisplay.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No purchases found</td></tr>';
        return;
    }
    
    tbody.innerHTML = purchasesToDisplay.map(purchase => `
        <tr>
            <td>${purchase.id}</td>
            <td>${escapeHtml(purchase.product_name)}</td>
            <td>${purchase.quantity}</td>
            <td>₹${purchase.cost_per_unit.toFixed(2)}</td>
            <td>₹${purchase.total_cost.toFixed(2)}</td>
            <td>${formatDate(purchase.purchase_date)}</td>
            <td>${purchase.notes ? escapeHtml(purchase.notes) : '-'}</td>
            <td>
                <button class="btn btn-sm btn-warning" onclick="openEditPurchaseModal(${purchase.id})">Edit</button>
                <button class="btn btn-sm btn-danger" onclick="deletePurchase(${purchase.id})">Delete</button>
            </td>
        </tr>
    `).join('');
}

function filterPurchases() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const filtered = allPurchases.filter(purchase => 
        purchase.product_name.toLowerCase().includes(searchTerm)
    );
    displayPurchases(filtered);
}

function updateSummary() {
    const totalPurchases = allPurchases.length;
    const totalQuantity = allPurchases.reduce((sum, p) => sum + p.quantity, 0);
    const totalCost = allPurchases.reduce((sum, p) => sum + p.total_cost, 0);
    
    document.getElementById('totalPurchases').textContent = totalPurchases;
    document.getElementById('totalQuantity').textContent = totalQuantity;
    document.getElementById('totalCost').textContent = '₹' + totalCost.toFixed(2);
}

function savePurchase() {
    const productId = document.getElementById('productSelect').value;
    const quantity = document.getElementById('purchaseQuantity').value;
    const costPerUnit = document.getElementById('costPerUnit').value;
    const notes = document.getElementById('purchaseNotes').value;
    
    if (!productId || !quantity || !costPerUnit) {
        document.getElementById('createPurchaseMessage').innerHTML = '<div class="alert alert-danger">Product, quantity, and cost are required</div>';
        return;
    }
    
    const messageDiv = document.getElementById('createPurchaseMessage');
    messageDiv.innerHTML = '<div class="alert alert-info">Adding purchase...</div>';
    
    fetch('/api/create-purchase', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            product_id: parseInt(productId),
            quantity: parseInt(quantity),
            cost_per_unit: parseFloat(costPerUnit),
            notes: notes
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            messageDiv.innerHTML = '<div class="alert alert-success">Purchase added successfully!</div>';
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('createPurchaseModal')).hide();
                document.getElementById('createPurchaseForm').reset();
                loadProducts();
                loadPurchases();
            }, 1000);
        } else {
            messageDiv.innerHTML = '<div class="alert alert-danger">' + data.error + '</div>';
        }
    })
    .catch(error => {
        messageDiv.innerHTML = '<div class="alert alert-danger">Error adding purchase: ' + error + '</div>';
    });
}

function openEditPurchaseModal(purchaseId) {
    const purchase = allPurchases.find(p => p.id === purchaseId);
    if (!purchase) return;
    
    document.getElementById('editPurchaseId').value = purchase.id;
    document.getElementById('editProductName').value = purchase.product_name;
    document.getElementById('editPurchaseQuantity').value = purchase.quantity;
    document.getElementById('editCostPerUnit').value = purchase.cost_per_unit.toFixed(2);
    document.getElementById('editPurchaseNotes').value = purchase.notes || '';
    document.getElementById('editPurchaseMessage').innerHTML = '';
    
    const modal = new bootstrap.Modal(document.getElementById('editPurchaseModal'));
    modal.show();
}

function updatePurchase() {
    const purchaseId = document.getElementById('editPurchaseId').value;
    const quantity = document.getElementById('editPurchaseQuantity').value;
    const costPerUnit = document.getElementById('editCostPerUnit').value;
    const notes = document.getElementById('editPurchaseNotes').value;
    
    if (!quantity || !costPerUnit) {
        document.getElementById('editPurchaseMessage').innerHTML = '<div class="alert alert-danger">Quantity and cost are required</div>';
        return;
    }
    
    const messageDiv = document.getElementById('editPurchaseMessage');
    messageDiv.innerHTML = '<div class="alert alert-info">Updating purchase...</div>';
    
    fetch(`/api/update-purchase/${purchaseId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            quantity: parseInt(quantity),
            cost_per_unit: parseFloat(costPerUnit),
            notes: notes
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            messageDiv.innerHTML = '<div class="alert alert-success">Purchase updated successfully!</div>';
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('editPurchaseModal')).hide();
                loadProducts();
                loadPurchases();
            }, 1000);
        } else {
            messageDiv.innerHTML = '<div class="alert alert-danger">' + data.error + '</div>';
        }
    })
    .catch(error => {
        messageDiv.innerHTML = '<div class="alert alert-danger">Error updating purchase: ' + error + '</div>';
    });
}

function deletePurchase(purchaseId) {
    if (!confirm('Are you sure you want to delete this purchase? This will reduce the product stock.')) {
        return;
    }
    
    fetch(`/api/delete-purchase/${purchaseId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Purchase deleted successfully!');
            loadProducts();
            loadPurchases();
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        alert('Error deleting purchase: ' + error);
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
