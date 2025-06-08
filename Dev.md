# Development Environment Setup and Startup Guide

## 1. Environment Preparation

It is recommended to use Anaconda or a Python 3.10+ virtual environment.

### Create Environment with Anaconda
```bash
conda create -n django_env python=3.10
conda activate django_env
```

### Install Dependencies
It is recommended to use pyproject.toml for dependency installation (make sure the virtual environment is activated):
```bash
pip install .  
python scripts/download_models.py
```
If you need a requirements.txt, you can generate it with:
```bash
pip freeze > requirements.txt
```
(This project does not provide requirements.txt by default.)

## 2. Database Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

## 3. Create Superuser (for Admin Panel)
```bash
python manage.py createsuperuser
```

## 4. Start Development Server
```bash
python manage.py runserver
```

## 5. Access the Project
- Admin Panel: http://127.0.0.1:8000/admin/
- User Authentication: http://127.0.0.1:8000/accounts/
- API Endpoints: http://127.0.0.1:8000/api/

## 6. Other Notes
- The image upload directory is `media/`, and static/media file serving is automatically configured for development.
- For frontend development or deployment, please refer to the subsequent phases in Workflow.md.
