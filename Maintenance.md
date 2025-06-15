# Operations and Maintenance Documentation for Voix de la Ville (VdV)

## 1. Introduction
Voix de la Ville (VdV) is a Django - based MVP designed for urban voice reporting and moderation. This document provides guidance on setting up, running, and maintaining the VdV project.

## 2. Quick Start

### 2.1 Clone the repository
Clone the project repository to your local machine using the appropriate version control system.

### 2.2 Create and activate a Python environment
It is recommended to use Anaconda to create a virtual environment:
```bash
conda create -n django_env python=3.10
conda activate django_env
```

### 2.3 Install dependencies
Install the necessary Python packages and download the required models:
```bash
pip install .
python scripts/download_models.py
```

### 2.4 Apply migrations
Apply the database migrations and collect static files:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
```

### 2.5 Create a superuser
Create a superuser to access the Django admin interface:
```bash
python manage.py createsuperuser
```

### 2.6 Run the development server
Start the development server:
```bash
python manage.py runserver
```

### 2.7 Access the application
- Admin: http://127.0.0.1:8000/admin/
- Auth: http://127.0.0.1:8000/accounts/
- API: http://127.0.0.1:8000/api/

## 3. Mock Data

### 3.1 Seed Development Data
To assist with development and testing, you can seed sample data using the following command:
```bash
python manage.py dev_seed
```
This command will create sample users, generate reports with random categories, images, GPS coordinates, add comments and votes, use multilingual descriptions, and trigger the NLP categorization pipeline.

### 3.2 Clear Development Data
To clear the development data, you can use the following command:
```bash
python manage.py clear_dev_data
```
This command will delete reports, votes, comments, etc., but will not remove administrators or manually created users.

### 3.3 Multilanguage Support
To compile language codes, use the following command:
```bash
django - admin compilemessages
```
Note that this command is not natively available in Windows.

## 4. Warnings

Although the Voix de la Ville project has a complete set of core logic, features, and system design, it is currently not suitable for production deployment due to the following reasons:

1. **Geolocation Handling**: The project currently uses the browser's built - in `navigator.geolocation` API. This is only suitable for demonstration purposes and lacks the transparency, configurability, and compliance with French data governance standards required for public deployment. A map SDK (e.g., Leaflet, Mapbox, or Google Maps) would be necessary for production, but free solutions are limited and commercial ones incur costs.

2. **Static Asset Management**: Static resources are served using WhiteNoise from within the project directory. While this is convenient during development, a dedicated web server (such as Nginx) should be used in production to handle these assets efficiently. The current setup is not scalable for production traffic.

3. **Postal Code Estimation Service**: The project simulates postal code detection using SQLite and city center approximation logic, which only provides approximate results. A real deployment would require a dedicated geolocation service or API to ensure accurate postcode mapping.

4. **Deployment & Docker**: Although Dockerization was initially explored, it was excluded from the final setup. A real deployment would likely involve direct setup on a Linux server with specific configurations and services, such as switching from SQLite to PostgreSQL and integrating third - party APIs.

In summary, targeted modifications such as acquiring a real server environment and paying for proper third - party services are required to make the system production - ready. Since this is a student project, development currently ends at the MVP stage.