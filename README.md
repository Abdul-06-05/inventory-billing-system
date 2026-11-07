# StockBill - Inventory & Billing System
Django + SQL + HTML + CSS + JavaScript (no React, no DRF).

## Run it
```
pip install -r requirements.txt
python manage.py makemigrations inventory
python manage.py migrate
python manage.py seed          # demo users + sample products (optional)
python manage.py runserver
```
Open http://127.0.0.1:8000/  
Demo logins (from `seed`): admin / admin123  and  staff / staff123

## Folder explanation
| File | What it does |
|---|---|
| `billing_project/settings.py` | Project settings: apps, SQLite database, login redirects |
| `inventory/models.py` | 8 database tables (Profile, Category, Product, Supplier, Purchase, Customer, Invoice, InvoiceItem) |
| `inventory/views.py` | All page logic (dashboard, CRUD, billing, reports, staff) |
| `inventory/urls.py` | Maps each URL to a view |
| `inventory/forms.py` | Django forms for add/edit pages |
| `inventory/decorators.py` | `admin_required` - blocks staff users from admin pages |
| `inventory/context_processors.py` | Gives every template the `is_admin` flag (hides menu links) |
| `inventory/admin.py` | Django admin panel at /django-admin/ |
| `inventory/templates/` | HTML pages (`base.html` is the common layout) |
| `static/js/billing.js` | Cart on the billing page |
| `static/css/style.css` | All styling |
| `management/commands/seed.py` | Creates demo data |

## How the main flows work
1. **Login / roles** - Django's built-in auth. `Profile.role` is `admin` or `staff`.
   `@admin_required` protects Reports, Staff and all Delete actions.
2. **Stock in** - Adding a `Purchase` increases `Product.stock` (in `Purchase.save`, using `F()`).
3. **Billing** - JavaScript builds the cart in the browser and sends JSON to `/billing/save/`.
   The view (`create_invoice`) runs inside `transaction.atomic()`:
   it locks each product row (`select_for_update`), checks stock, saves `InvoiceItem`,
   reduces stock, then calculates subtotal + GST + total.
   If anything fails, the whole bill is rolled back.
   Prices are read from the database, never trusted from the browser.
4. **Low stock** - `Product.objects.filter(stock__lte=F("reorder_level"))` (compares two columns in SQL).
5. **Reports** - `TruncDate + Sum + GROUP BY` for daily sales, `Sum` per product for the top-5 list, drawn with Chart.js.
6. **Delete safety** - Foreign keys use `PROTECT`, so a product used in invoices cannot be deleted.

## Interview questions you can answer from this project
- Why `transaction.atomic()`? So a bill and its stock update succeed or fail together.
- Why `F()` expressions? The update happens inside the database, so two users cannot overwrite each other's stock count.
- Why store `price` in `InvoiceItem`? Product price can change later; old invoices must not change.
- Why `PROTECT`? To keep invoice history safe.

## Switching to Oracle later
`pip install oracledb`, then change the `DATABASES` block in `settings.py`
(`ENGINE: django.db.backends.oracle`, plus NAME, USER, PASSWORD, HOST, PORT).

## Resume bullets
- Developed an Inventory & Billing System using Django, SQL, HTML, CSS and JavaScript with role-based access for admin and staff.
- Implemented automated stock updates, GST invoice generation and low-stock alerts using atomic database transactions.
- Designed a normalized relational schema and built sales reports with SQL aggregations and Chart.js visualizations.
