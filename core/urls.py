from django.urls import path
from . import views

urlpatterns = [
    path("reports/", views.reports_list, name="reports_list"),
    path("votes/", views.votes_create, name="votes_create"),
]