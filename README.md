# Azure Jewels — Luxury Haute Joaillerie E-Commerce Platform

A production-grade, bespoke luxury fine jewellery e-commerce platform engineered with Python and Django. Designed with an editorial haute joaillerie visual identity, high-speed server rendering, and database-backed transactional workflows.

---

## ✦ Luxury Design System

Azure Jewels strictly adheres to an editorial, regal aesthetic:

| Color Role | Hex Code | Purpose |
| :--- | :--- | :--- |
| **Primary Navy** | `#071A2D` | Top announcement bar, primary buttons, hero frames, footer background |
| **Secondary Navy** | `#0B2A45` | Subtitles, section accents, active indicator states, card tags |
| **Accent Navy** | `#123B5D` | Utility navigation links, secondary buttons, interactive highlights |
| **Pure White** | `#FFFFFF` | Main logo row, product card backgrounds, crisp content surfaces |
| **Soft White** | `#F6F8FA` | Section alternate backgrounds, control bars, stepper tracks |
| **Subtle Border** | `#D9E3EC` | Fine hairline borders, dividers, subtle card contours |

- **Typography**: Editorial serif headings in *Cormorant Garamond* / *Playfair Display* paired with clean, ultra-legible body typography in *Inter*.
- **Iconography**: Bootstrap Icons with consistent sizing and alignment.
- **Header Architecture**: A 3-tier luxury header with mathematical logo centering, left utility bar (`Store Locator`, `Track Package`, `Return & Exchange`, `Contact Us`), right patron utility actions (Search, Account, Wishlist, Bag), and a single-line 10-category navigation row with zero horizontal overflow.

---

## ✦ Key Platform Features

### 1. Catalog & Curated Collections
- **Categorized Silhouettes**: Full hierarchy covering Rings, Necklaces, Earrings, Bracelets, Solitaires, Polki & Jadau, Bridal Trousseau, Mangalsutras, Men's Regal, and High Jewellery Sets.
- **Dynamic Filtering**: Filter by category, price ranges (min/max), search queries, and curated edits (New Arrivals, Best Sellers, Special Offers).
- **Interactive Sorting**: Low-to-high, high-to-low, newest arrivals, and customer favorites.
- **Unified Product Card**: Reusable component (`templates/includes/product-card.html`) with dual image hover transitions, wishlist toggling, inventory badges, and AJAX quick add.

### 2. Cart & Wishlist
- **Session & User Hybrid Storage**: Guest patrons seamlessly accumulate items in session-based carts/wishlists which automatically merge upon account sign-in.
- **AJAX State Sync**: Live badge counter updates for bag and wishlist without disrupting browsing flow.
- **Direct Checkout Acceleration**: "Buy Now" flow directly initializes orders.

### 3. Orders, Inventory & Checkout
- **Strict Pre-Order Inventory Guard**: Real-time stock verification prevents overselling before order confirmation.
- **Safe Stock Decrement**: Automatic stock adjustment upon verified order creation.
- **Patron Order Authorization**: Security boundaries preventing unauthorized users from accessing receipts of other customers.
- **Cash on Delivery & Prepaid Ready**: Pre-configured for Cash on Delivery and online gateways (Razorpay, Stripe, PayU, PhonePe) with idempotent pending state handling.

### 4. Client Atelier & Account Portal
- Unified sidebar component (`templates/includes/account-sidebar.html`) across all account pages.
- Order history with order statuses (`confirmed`, `processing`, `shipped`, `out_for_delivery`, `delivered`, `cancelled`).
- Address book management with default shipping selection and deletion.
- Profile and personal details management.

### 5. Consignment Tracking & Store Locator
- **Live Tracking (`/track-package/`)**: 4-milestone visual stepper (Order Placed, Atelier Inspection & Hallmark, Armored Transit, Doorstep Handover) with patron data privacy masking for anonymous queries.
- **Store Locator (`/store-locator/`)**: Interactive multi-city directory featuring flagship ateliers across Mumbai, New Delhi, Bengaluru, Hyderabad, Kolkata, and Jaipur.

### 6. Concierge & Client Communications
- **Bespoke Inquiries (`/contact/`)**: Persisted inquiry capture with concierge subject classification.
- **Private Privileges Newsletter (`/newsletter/subscribe/`)**: Email capture with AJAX validation.

---

## ✦ Project Structure

```text
Azure_Jewels_DJANGO_PREMIUM_MENU/
├── azure_jewels/              # Django Project Core Configuration
│   ├── __init__.py
│   ├── asgi.py                # ASGI application entry point
│   ├── settings.py            # Environment-aware production settings
│   ├── urls.py                # Root URL dispatcher
│   └── wsgi.py                # WSGI deployment entry point
├── store/                     # Main E-Commerce Application
│   ├── admin.py               # Customized Django Admin interfaces
│   ├── apps.py                # Store App Config
│   ├── context_processors.py  # Global cart & category context processors
│   ├── forms.py               # Clean ModelForms & validation forms
│   ├── models.py              # Category, Product, Cart, Order, Address, Inquiry
│   ├── urls.py                # App URL routing & legacy 301 redirects
│   └── views.py               # E-Commerce business logic & API endpoints
├── templates/                 # Jinja/Django HTML Templates
│   ├── base.html              # Core layout with luxury SEO & OpenGraph meta
│   ├── index.html             # Curated Haute Joaillerie Homepage
│   ├── shop-grid.html         # Shop & Filter Grid
│   ├── product-details.html   # Product Atelier Details
│   ├── cart.html              # Shopping Bag
│   ├── checkout.html          # Order Placement
│   ├── thank-you.html         # Order Confirmation Receipt
│   ├── track-package.html     # Consignment Tracking
│   ├── store-locator.html     # Multi-City Boutique Locator
│   ├── account-*.html         # Client Atelier Account Suite
│   ├── includes/              # Modular Reusable Sub-components
│   │   ├── header.html        # 3-Tier Luxury Navbar
│   │   ├── footer.html        # Regal Multi-column Footer
│   │   ├── product-card.html  # Unified Reusable Product Card
│   │   ├── account-sidebar.html # Dynamic Account Navigation
│   │   ├── mobile-menu.html   # Mobile Offcanvas Drawer
│   │   └── messages.html      # Flash Messages
│   └── ...                    # Policy and informational pages
├── static/                    # Static Assets
│   └── assets/
│       ├── css/               # bootstrap, luxury-theme.css, premium-menu.css
│       ├── js/                # bootstrap.bundle, azure-store.js, premium-menu.js
│       └── images/            # Curated imagery, banners, categories, sliders
├── media/                     # Uploaded Product & Category Media Files
├── manage.py                  # Django Management Script
├── requirements.txt           # Python Dependencies
├── .env.example               # Environment Configuration Blueprint
└── db.sqlite3                 # Local Development Database
```

---

## ✦ Getting Started

### 1. Prerequisites
- Python 3.10+ (Recommended: Python 3.11 / 3.12)
- Virtual environment tool (`venv`)

### 2. Environment Configuration
Create your environment variables file from the provided template:
```bash
cp .env.example .env
```
Key configuration parameters:
```ini
DJANGO_SECRET_KEY=your-secure-random-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

### 3. Setup Virtual Environment & Install Dependencies
```bash
# Windows PowerShell
python -m venv env
.\env\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 4. Database Migrations
```bash
python manage.py migrate
```

### 5. Create Superuser (Admin Access)
```bash
python manage.py createsuperuser
```

### 6. Run Local Development Server
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/` in your browser.  
Access the administrative portal at `http://127.0.0.1:8000/admin/`.

---

## ✦ External Service Integration Guide

For full live production deployment, configure the following external gateways:

### 1. Online Payment Gateway (Razorpay / Stripe)
1. Add gateway credentials to `.env`:
   ```ini
   RAZORPAY_KEY_ID=rzp_live_xxxxxxxx
   RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxx
   ```
2. Integrate client-side checkout modal in `templates/checkout.html`.
3. Create an endpoint in `store/views.py` (e.g., `payment_webhook`) to receive asynchronous HMAC-SHA256 signature verification callbacks and update `order.payment_status = 'Paid'`.

### 2. SMS & WhatsApp Order Notifications (Twilio / Gupshup)
1. Connect post-order hooks in `checkout_view` to dispatch instant SMS/WhatsApp alerts with tracking links (`/track-package/?order_number=AZ-xxxxxx`).

### 3. Production Deployment (Gunicorn / Nginx / Hostinger)
1. Set `DJANGO_DEBUG=False` in `.env`.
2. Configure `DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com`.
3. Run `python manage.py collectstatic --noinput`.
4. Deploy using Gunicorn / Uvicorn behind Nginx reverse proxy with SSL certification (Let's Encrypt / Certbot).
