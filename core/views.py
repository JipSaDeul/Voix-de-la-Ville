from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Report, Vote
import json

@csrf_exempt
def reports_list(request):
    if request.method == "GET":
        reports = list(Report.objects.values())
        return JsonResponse(reports, safe=False)
    elif request.method == "POST":
        data = json.loads(request.body)
        report = Report.objects.create(
            user_id=data["user_id"],
            category_id=data.get("category_id"),
            title=data["title"],
            description=data["description"],
            latitude=data["latitude"],
            longitude=data["longitude"],
            # image upload not handled here (use DRF for full support)
        )
        return JsonResponse({"id": report.id}, status=201)

@csrf_exempt
def votes_create(request):
    if request.method == "POST":
        data = json.loads(request.body)
        vote, created = Vote.objects.get_or_create(
            user_id=data["user_id"],
            report_id=data["report_id"]
        )
        return JsonResponse({"created": created}, status=201)
