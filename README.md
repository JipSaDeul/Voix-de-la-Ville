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
   pip install .
   python scripts/download_models.py
   ```

4. **Apply migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py collectstatic
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

---

## Mock Data

To assist with development and testing, you can seed and clear sample data using custom Django management commands.

### Seed Development Data

```bash
python manage.py dev_seed
```

This will:

* Create sample users
* Generate reports with random categories, images, GPS coordinates
* Add comments and votes to simulate real usage
* Use multilingual descriptions (English, French, Spanish, German)
* Trigger the NLP categorization pipeline

### Clear Development Data

```bash
python manage.py clear_dev_data
```

This will:

* Remove all `Report`, `Vote`, `Comment` entries
* Optionally remove auto-generated categories
* Does **not** delete admin or manually created users

> ⚠️ Use with caution: this operation deletes data from the database.

---


### Multilanguage

Use

```bash
django-admin compilemessages
```
to compile language codes

Not natively available in Windows.

---

## Development

See [Dev.md](Dev.md) for detailed development instructions.
