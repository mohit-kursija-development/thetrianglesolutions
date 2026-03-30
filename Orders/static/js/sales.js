// Load sales data on page load
$(document).ready(function() {
    loadSalesmanData();
    loadProductData();
});

// Load salesman sales data
async function loadSalesmanData() {
    try {
        const response = await fetch('/api/salesman-sales');
        const data = await response.json();
        
        if (data.error) {
            $('#salesmanTableBody').html(`<tr><td colspan="4" class="error-message">Error: ${data.error}</td></tr>`);
            return;
        }
        
        const salesmen = data.salesmen;
        displaySalesmanTable(salesmen);
    } catch (error) {
        console.error('Error loading salesman data:', error);
        $('#salesmanTableBody').html('<tr><td colspan="4" class="error-message">Error loading salesman data</td></tr>');
    }
}

// Display salesman sales in table
function displaySalesmanTable(salesmen) {
    const $tbody = $('#salesmanTableBody');
    
    if (!salesmen || salesmen.length === 0) {
        $tbody.html('<tr><td colspan="4" class="no-data-message">No salesman data available</td></tr>');
        return;
    }
    
    let html = '';
    let rank = 1;
    
    salesmen.forEach((salesman) => {
        html += `
            <tr>
                <td class="rank-cell">${rank}</td>
                <td class="name-cell"><i class="bi bi-person-fill"></i> ${salesman.username}</td>
                <td class="number-cell">${salesman.total_orders}</td>
                <td class="amount-cell"><strong>₹${salesman.total_sales.toFixed(2)}</strong></td>
            </tr>
        `;
        rank++;
    });
    
    $tbody.html(html);
}

// Load product sales data
async function loadProductData() {
    try {
        const response = await fetch('/api/product-sales');
        const data = await response.json();
        
        if (data.error) {
            $('#productTableBody').html(`<tr><td colspan="4" class="error-message">Error: ${data.error}</td></tr>`);
            return;
        }
        
        const products = data.products;
        displayProductTable(products);
    } catch (error) {
        console.error('Error loading product data:', error);
        $('#productTableBody').html('<tr><td colspan="4" class="error-message">Error loading product data</td></tr>');
    }
}

// Display product sales in table
function displayProductTable(products) {
    const $tbody = $('#productTableBody');
    
    if (!products || products.length === 0) {
        $tbody.html('<tr><td colspan="4" class="no-data-message">No product data available</td></tr>');
        return;
    }
    
    let html = '';
    let rank = 1;
    
    products.forEach((product) => {
        // Only show products with actual sales
        if (product.total_quantity > 0 || product.total_revenue > 0) {
            html += `
                <tr>
                    <td class="rank-cell">${rank}</td>
                    <td class="name-cell"><i class="bi bi-box"></i> ${product.name}</td>
                    <td class="number-cell">${product.total_quantity.toFixed(2)}</td>
                    <td class="amount-cell"><strong>₹${product.total_revenue.toFixed(2)}</strong></td>
                </tr>
            `;
            rank++;
        }
    });
    
    if (html === '') {
        $tbody.html('<tr><td colspan="4" class="no-data-message">No sales data available this month</td></tr>');
    } else {
        $tbody.html(html);
    }
}
