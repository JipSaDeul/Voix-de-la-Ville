from django.core.management.base import BaseCommand
from django.utils.timezone import now, timedelta
from core.models import User, ReportCategory, Report, Comment, Vote
import random
import uuid

class Command(BaseCommand):
    help = 'Seed development data for reports, users, votes, and comments'

    def handle(self, *args, **kwargs):
        self.stdout.write("🚧 Dev seeding started...")

        # Create a unique test user with a suffix
        suffix = uuid.uuid4().hex[:6]  # e.g. "testuser_a1b2c3"
        username = f"testuser_{suffix}"
        email = f"{username}@example.com"

        user, created = User.objects.get_or_create(username=username, defaults={
            "email": email
        })
        if created:
            user.set_password("password123")
            user.save()
            self.stdout.write(f"👤 Created test user: {username}")
        else:
            self.stdout.write(f"ℹ️ Using existing test user: {username}")

        # Create categories
        categories = [
            ("Infrastructure", "Roads, potholes, etc."),
            ("Environment", "Pollution, noise, etc."),
            ("Traffic", "Congestion, signals, etc."),
            ("Security", "Crime, theft, etc."),
            ("Health", "Medical, sanitation, etc.")
        ]

        category_objs = []
        for name, desc in categories:
            obj, _ = ReportCategory.objects.get_or_create(name=name, defaults={"description": desc})
            category_objs.append(obj)

        # Create reports
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
            report = Report.objects.create(
                user=user,
                title=report_titles[i],
                description=report_descs[i],
                category=random.choice(category_objs),
                latitude=45.5 + random.random() * 0.1,
                longitude=-73.5 + random.random() * 0.1,
                created_at=now() - timedelta(days=random.randint(0, 5))
            )

            Vote.objects.create(user=user, report=report)
            Comment.objects.create(user=user, report=report, content=f"Thanks for reporting: {report.title}")

        self.stdout.write("✅ Dev data seeding complete.")
