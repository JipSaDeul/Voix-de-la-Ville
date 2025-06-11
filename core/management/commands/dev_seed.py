# core/management/commands/dev_seed.py
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils.timezone import now
from core.models import User, Admin, ReportCategory, Report, Comment, Vote
from core.cities.helper import get_zipcode_by_location
import uuid

# Create categories
from core.utils import nlp_categorize, categories
import random
from typing import Tuple


def generate_paris_area_coords() -> Tuple[float, float]:
    """
    Generate a random coordinate within Paris or its surrounding region.

    70% chance the coordinate falls inside the central Paris area (±0.03 degrees),
    30% chance it falls in the greater Île-de-France region (±0.1 degrees).

    :return: A tuple containing (latitude, longitude)
    """
    base_lat = 48.853  # Central latitude of Paris
    base_lon = 2.349  # Central longitude of Paris

    if random.random() < 0.7:
        # Central Paris: small offset (~2–3 km)
        lat_offset = random.uniform(-0.03, 0.03)
        lon_offset = random.uniform(-0.03, 0.03)
    else:
        # Greater Paris region: wider offset (~10 km)
        lat_offset = random.uniform(-0.1, 0.1)
        lon_offset = random.uniform(-0.1, 0.1)

    return base_lat + lat_offset, base_lon + lon_offset


class Command(BaseCommand):
    help = 'Seed development data for reports, users, votes, comments, and admin'

    def handle(self, *args, **kwargs):
        self.stdout.write("🚧 Dev seeding started...")

        # Create a test User
        suffix = uuid.uuid4().hex[:6]
        username = f"testuser_{suffix}"
        email = f"{username}@example.com"

        user, created = User.objects.get_or_create(username=username, defaults={"email": email})
        if created:
            user.set_password("password123")
            user.save()
            self.stdout.write(f"👤 Created test user: {username}")
        else:
            self.stdout.write(f"ℹ️ Using existing test user: {username}")

        # Create a test Admin
        admin_username = f"testadmin_{suffix}"
        admin_email = f"{admin_username}@example.com"
        admin, created = Admin.objects.get_or_create(username=admin_username, defaults={
            "email": admin_email,
            "department": "Development"
        })
        if created:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write(f"🛡️ Created test admin: {admin_username}")
        else:
            self.stdout.write(f"ℹ️ Using existing test admin: {admin_username}")

        category_objs = {}
        for key, meta in categories.items():
            obj, _ = ReportCategory.objects.get_or_create(
                name=meta["name"],
                defaults={"description": meta["description"]}
            )
            category_objs[key] = obj

        # Create sample reports
        report_titles = [
            "Pothole on 5th Avenue",
            "Loud noise every night",
            "Broken traffic light at intersection",
            "Suspicious activity in alley",
            "Overflowing trash bin"
        ]
        report_descs = [
            "There is a huge pothole causing traffic delays.",
            "Construction noise is too loud after 10 PM.",
            "The traffic light keeps blinking red and green rapidly.",
            "Looks like someone is trying to break into houses.",
            "Trash hasn't been collected in 3 days."
        ]

        for i in range(len(report_titles)):
            lat, lon = generate_paris_area_coords()
            zipcode = get_zipcode_by_location(lat, lon)
            category_data = nlp_categorize(report_descs[i])
            if category_data:
                category = category_objs.get(category_data["name"], category_objs["other"])
            else:
                category = category_objs["other"]

            report = Report.objects.create(
                user=user,
                title=report_titles[i],
                description=report_descs[i],
                category=category,
                latitude=lat,
                longitude=lon,
                zipcode=zipcode,
                created_at=now() - timedelta(days=random.randint(0, 5))
            )

            Vote.objects.create(user=user, report=report)
            Comment.objects.create(user=user, report=report, content=f"Thanks for reporting: {report.title}")

            # Create a second Admin: testuser_admin
        admin2_username = f"testuser_admin_{suffix}"
        admin2_email = f"{admin2_username}@example.com"
        admin2, created = Admin.objects.get_or_create(username=admin2_username, defaults={
            "email": admin2_email,
            "department": "City Services"
        })
        if created:
            admin2.set_password("admin123")
            admin2.save()
            self.stdout.write(f"🛡️ Created testuser_admin: {admin2_username}")
        else:
            self.stdout.write(f"ℹ️ Using existing testuser_admin: {admin2_username}")

        # Create one admin-generated report
        admin2_title = "Leaking fire hydrant on Rue de Rivoli"
        admin2_desc = "Water is continuously leaking from a fire hydrant. It might be a hazard."

        lat, lon = generate_paris_area_coords()
        zipcode = get_zipcode_by_location(lat, lon)
        category_data = nlp_categorize(admin2_desc)
        if category_data:
            category = category_objs.get(category_data["name"], category_objs["other"])
        else:
            category = category_objs["other"]

        admin2_report = Report.objects.create(
            user=admin2,  # Admin is a subclass of User
            title=admin2_title,
            description=admin2_desc,
            category=category,
            latitude=lat,
            longitude=lon,
            zipcode=zipcode,
            created_at=now() - timedelta(days=random.randint(0, 5))
        )

        Vote.objects.create(user=admin2, report=admin2_report)
        Comment.objects.create(user=admin2, report=admin2_report, content="We are dispatching maintenance personnel.")

        self.stdout.write("🛠️ testuser_admin created a report.")

        self.stdout.write("✅ Dev data seeding complete.")
