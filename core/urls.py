from django.urls import path
from . import views

urlpatterns = [
    path("reports/", views.reports_list, name="reports_list"),
    path("reports/<int:report_id>/votes/", views.report_vote_count, name="report_vote_count"),
    path("votes/", views.votes_create, name="votes_create"),
    path("reports/top-pending/", views.top_pending_reports, name="top_pending_reports"),
    path("reports/<int:report_id>/comments/", views.report_comments, name="report_comments"),
    path("categories/", views.get_report_categories, name="get_report_categories"),
    path("reports/by_category/", views.get_reports_by_category, name="get_reports_by_category"),

    path("reports/user/", views.user_reports_by_time),
    path("reports/user/voted/", views.user_voted_reports),
    path("reports/user/commented/", views.user_commented_reports),
]
