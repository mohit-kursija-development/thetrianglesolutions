# Shop Payment Management Feature - Setup Guide

## Overview
A new "Shops" page has been added to manage shop payments and track outstanding amounts.

## Features Implemented
✅ **Shops Navigation Button** - Added to all pages (Orders, Past Orders, Edit Order)
✅ **Shop Search** - Search shops by name or location
✅ **Outstanding Payments** - View total amount pending collection for each shop
✅ **Pending Orders** - See all unpaid orders for a selected shop
✅ **Payment Collection** - Mark orders as paid with a single click
✅ **Payment History** - View recently collected payments
✅ **Responsive Design** - Works on desktop and mobile devices

## Database Schema Requirements

The feature requires the following columns in the `orders` table. **Please run these SQL queries to update your database:**

```sql
-- Add payment status column if it doesn't exist
ALTER TABLE orders ADD COLUMN payment_status VARCHAR(50) DEFAULT 'pending' AFTER shop_id;

-- Add payment collected datetime column if it doesn't exist
ALTER TABLE orders ADD COLUMN payment_collected_at DATETIME NULL AFTER payment_status;

-- Create index for better query performance
CREATE INDEX idx_orders_payment_status ON orders(payment_status);
CREATE INDEX idx_orders_shop_id ON orders(shop_id);
```

## Database Fields Explanation

| Column | Type | Purpose |
|--------|------|---------|
| `payment_status` | VARCHAR(50) | Tracks payment state: 'pending' or 'collected' |
| `payment_collected_at` | DATETIME | Timestamp when payment was collected |

## How to Use

### Accessing the Shops Page
1. Click the **"Shops"** button in the navigation menu (available on all pages)
2. The page will load all shops with outstanding payment amounts

### Searching for Shops
1. Use the search box on the left panel
2. Type shop name or location
3. Results filter in real-time

### Viewing Outstanding Payments
1. Select a shop from the list
2. The right panel shows:
   - Total outstanding amount (if any)
   - List of pending orders needing payment collection
   - Previously collected payments

### Collecting Payment
1. Find the order in the "Pending Payments" section
2. Click the **"Collect"** button next to the order
3. The payment status updates immediately
4. Order moves to "Recently Collected" section

## File Structure Created

```
Orders/
├── templates/
│   ├── shops.html (NEW)
│   ├── orders.html (UPDATED - added Shops button)
│   ├── past_orders.html (UPDATED - added Shops button)
│   └── edit_order.html (UPDATED - added Shops button)
├── static/
│   ├── css/
│   │   └── shops.css (NEW)
│   └── js/
│       └── shops.js (NEW)
└── app.py (UPDATED - added new routes and API endpoints)
```

## New Routes Added

### Page Routes
- `GET /shops` - Display shop management page

### API Endpoints
- `GET /api/shops-data` - Get all shops with outstanding payment info
  - Query param: `search` (optional) - Filter shops by name/location
  
- `GET /api/shop-details/<shop_id>` - Get detailed payment info for a specific shop
  - Returns: Pending orders, collected orders, outstanding amount
  
- `PUT /api/collect-payment/<order_id>` - Mark an order's payment as collected
  - Returns: Success message

## Testing the Feature

1. **Verify database changes:**
   ```sql
   DESCRIBE orders;  -- Check if new columns exist
   ```

2. **Test the feature:**
   - Go to Orders page
   - Create a few orders for different shops
   - Navigate to Shops page
   - Search for a shop
   - Click "Collect" on an order
   - Verify the order moves to collected section

3. **Check the browser console** (F12) for any JavaScript errors

## Troubleshooting

### "Error loading shops"
- Check database connection in `.env` file
- Verify the shops table exists and has data

### "Error loading details"
- Run the SQL queries above to add missing columns
- Check MySQL error logs

### Payment not updating
- Clear browser cache (Ctrl+F5 or Cmd+Shift+R)
- Check browser console for JavaScript errors
- Verify user is logged in and has a valid session

## Styling Notes

The feature uses:
- **Bootstrap 5.3** for responsive layout
- **Bootstrap Icons** for icons
- **Custom CSS** with color scheme:
  - Primary: #2c3e50 (Dark blue-gray)
  - Secondary: #3498db (Light blue)
  - Success: #27ae60 (Green)
  - Warning: #f39c12 (Orange)
  - Danger: #e74c3c (Red)

## Future Enhancements

Possible additions:
- Export payment reports
- Payment receipts/invoices
- Recurring payment reminders
- Multiple payment methods tracking
- Payment date range filters
- Payment statistics dashboard

## Support

For issues or questions:
1. Check browser console for errors (F12)
2. Verify database schema with ALTER TABLE queries
3. Check Flask debug output in terminal
4. Review app.py logs for API errors
