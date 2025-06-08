from django.core.management.base import BaseCommand

from core.models import User, Report, Comment, Vote, ReportCategory


class Command(BaseCommand):
    help = "Clear development/test data before production deployment"

    def handle(self, *args, **options):
        self.stdout.write("🧹 Starting dev data cleanup...")

        # 1. Locate test users
        test_users = User.objects.filter(username__startswith="testuser")
        test_user_ids = list(test_users.values_list("id", flat=True))

        # 2. Find reports created by test users
        test_reports = Report.objects.filter(user_id__in=test_user_ids)
        test_report_ids = list(test_reports.values_list("id", flat=True))

        # 3. Delete ALL votes on testuser's reports
        Vote.objects.filter(report_id__in=test_report_ids).delete()

        # 4. Delete ALL comments on testuser's reports
        Comment.objects.filter(report_id__in=test_report_ids).delete()

        # 5. Delete testuser's own votes/comments elsewhere (if any)
        Vote.objects.filter(user_id__in=test_user_ids).delete()
        Comment.objects.filter(user_id__in=test_user_ids).delete()

        # 6. Delete the test reports
        test_reports.delete()

        # 7. Delete test users
        test_users.delete()

        # 8. (Optional) Remove unused dev categories
        if ReportCategory.objects.count() > 10:
            ReportCategory.objects.filter(report__isnull=True).delete()

        self.stdout.write("✅ Dev data cleanup complete.")
