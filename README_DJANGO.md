# Azure Jewels - Django Ecommerce

## Setup
python -m venv venv
venv\\Scripts\\activate  (Windows)
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

Website: http://127.0.0.1:8000/
Admin: http://127.0.0.1:8000/admin/

## Features
- Django + SQLite
- Django Admin Product CRUD
- Category CRUD
- Product images, stock, pricing, sale price
- Order + Order Items models
- Checkout API
- Products API
- User authentication through Django admin/auth system
- Existing premium frontend assets retained in static/assets
