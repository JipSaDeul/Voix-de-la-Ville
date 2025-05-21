# Voix de la Ville (VdV)

A Django-based MVP for urban voice reporting and moderation.

## Features

- User registration and authentication (django-allauth)
- Report creation with image upload and geolocation
- Voting and commenting on reports
- Admin moderation and status management
- RESTful API endpoints with CORS support

## Quick Start

1. **Clone the repository**

2. **Create and activate a Python environment**
   ```bash
   conda create -n django_env python=3.10
   conda activate django_env
   ```

3. **Install dependencies**
   ```bash
   pip install .[dev]
   ```

4. **Apply migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access**
   - Admin: http://127.0.0.1:8000/admin/
   - Auth: http://127.0.0.1:8000/accounts/
   - API: http://127.0.0.1:8000/api/

## Development

See [Dev.md](Dev.md) for detailed development instructions.
