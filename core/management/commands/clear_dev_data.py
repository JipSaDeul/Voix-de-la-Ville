from django.core.management.base import BaseCommand
from core.models import User, Report, Comment, Vote, ReportCategory


class Command(BaseCommand):
    help = "Clear development/test data before production deployment"

    def handle(self, *args, **options):
        self.stdout.write("🧹 Starting dev data cleanup...")

        # 1. Find test users and admins (they're all Users)
        test_users = User.objects.filter(
            username__startswith="testuser"
        ) | User.objects.filter(
            username__startswith="testadmin"
        )
        test_user_ids = list(test_users.values_list("id", flat=True))

        # 2. Find reports created by those users
        test_reports = Report.objects.filter(user_id__in=test_user_ids)
        test_report_ids = list(test_reports.values_list("id", flat=True))

        # 3. Delete votes and comments on those reports
        Vote.objects.filter(report_id__in=test_report_ids).delete()
        Comment.objects.filter(report_id__in=test_report_ids).delete()

        # 4. Delete those users' own votes/comments elsewhere
        Vote.objects.filter(user_id__in=test_user_ids).delete()
        Comment.objects.filter(user_id__in=test_user_ids).delete()

        # 5. Delete reports
        test_reports.delete()

        # 6. Delete test users/admins
        test_users.delete()

        # 7. Optionally delete unused dev categories (over 10)
        if ReportCategory.objects.count() > 10:
            ReportCategory.objects.filter(report__isnull=True).delete()

        self.stdout.write("✅ Dev data cleanup complete.")
