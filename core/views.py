import json
import os
import uuid

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_http_methods

from core.utils import get_user_id, create_vote, create_or_update_comment, nlp_categorize, auto_translate, \
    build_report_data
from .models import Report, Comment
from .models import ReportCategory


@login_required
def home(request):
    return render(request, 'home.html')


@login_required
@require_GET
def report_vote_count(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    vote_count = report.votes.count()
    return JsonResponse({"report_id": report_id, "vote_count": vote_count})


@login_required
@require_GET
def top_pending_reports(request):
    N = int(request.GET.get("n", 10))  # by default 10, can be chosen by frontend
    reports = (
        Report.objects.filter(status="pending")
        .annotate(vote_count=Count("votes"))
        .order_by("-vote_count")[:N]
    )
    data = build_report_data(reports)
    return JsonResponse({"results": data})


@login_required
@csrf_exempt
def reports_list(request):
    if request.method == "GET":
        reports = Report.objects.all()
        # Build the report data using the abstracted helper function
        data = build_report_data(reports)
        # Return the response with the data
        return JsonResponse(data, safe=False)
    elif request.method == "POST":
        if request.content_type.startswith("multipart/form-data"):
            data_json = request.POST.get("data")
            if not data_json:
                return JsonResponse({"error": "Missing data field"}, status=400)
            data = json.loads(data_json)
            image = request.FILES.get("image")
        else:
            data = json.loads(request.body)
            image = None

        category = nlp_categorize(data["description"])
        category = ReportCategory.objects.filter(name=category["name"]).first()

        if not category:
            category = ReportCategory.objects.create(name=category["name"],
                                                     description=category["description"])

        current_user_id = get_user_id(request)  # get current user id
        if current_user_id is None:
            return JsonResponse({"error": "User not authenticated"}, status=401)

        report = Report.objects.create(
            user_id=current_user_id,
            category=category,
            title=data["title"],
            description=data["description"],
            latitude=data["latitude"],
            longitude=data["longitude"],
        )

        if image:
            ext = os.path.splitext(image.name)[1]
            unique_name = f"{uuid.uuid4().hex}{ext}"
            report.image.save(unique_name, image)

        return JsonResponse({"id": report.id}, status=201)


@login_required
@require_GET
def get_report_categories(request):
    categories = ReportCategory.objects.all()
    # Fetch categories and build data with both English and French names and descriptions
    data = [
        {
            "id": c.id,
            "name_en": c.name,  # English Name
            "name_fr": auto_translate(c.name, from_lang="en", to_lang="fr"),  # French Name
            "description_en": c.description,  # English Description
            "description_fr": auto_translate(c.description, from_lang="en", to_lang="fr"),  # French Description
        }
        for c in categories
    ]
    return JsonResponse({"categories": data})


@login_required
@require_GET
def get_reports_by_category(request):
    category_name = request.GET.get("category_name")
    N = int(request.GET.get("n", 10))  # by default return 10 reports

    if not category_name:
        return JsonResponse({"error": "Category name is required"}, status=400)

    # Get the corresponding category
    category = ReportCategory.objects.filter(name=category_name).first()
    if not category:
        return JsonResponse({"error": "Category not found"}, status=404)

    # Get reports of the category
    reports = (
        Report.objects.filter(category=category)
        .annotate(vote_count=Count("votes"))
        .order_by("-vote_count")[:N]
    )

    data = build_report_data(reports)
    return JsonResponse({"reports": data})


@login_required
@csrf_exempt
def votes_create(request):
    if request.method == "POST":
        try:
            # Parse the incoming JSON request data
            data = json.loads(request.body)

            # Ensure that the necessary fields are present
            if not isinstance(data.get("user_id"), int) or not isinstance(data.get("report_id"), int):
                raise TypeError("Invalid input types for 'user_id' or 'report_id'")

            # Call the create_vote utility function
            vote, created = create_vote(
                user_id=data["user_id"],
                report_id=data["report_id"]
            )

            if vote is None:
                # If vote is None, return an error response
                return JsonResponse({"error": "Failed to create vote due to invalid input."}, status=400)

            # If the vote was successfully created or retrieved, return the response
            return JsonResponse({"created": created}, status=201)

        except json.JSONDecodeError:
            # Handle invalid JSON input
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except KeyError:
            # Handle missing keys in the input data
            return JsonResponse({"error": "Missing 'user_id' or 'report_id' in the request."}, status=400)
        except TypeError as e:
            # Handle invalid input types
            return JsonResponse({"error": str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["GET", "POST"])
def report_comments(request, report_id):
    report = get_object_or_404(Report, id=report_id)

    if request.method == "GET":
        # Retrieve all comments for the report and return them
        comments = Comment.objects.filter(report=report).order_by("created_at")
        data = [
            {
                "id": c.id,
                "user": c.user_id,
                "content": c.content,
                "created_at": c.created_at,
            }
            for c in comments
        ]
        return JsonResponse({"comments": data})

    elif request.method == "POST":
        try:
            # Parse the incoming JSON data
            body = json.loads(request.body.decode())
            user_id = body.get("user_id")
            content = body.get("content")

            # Ensure user_id and content are provided
            if not user_id or not content:
                return HttpResponseBadRequest("Both 'user_id' and 'content' are required.")

            # Call the existing utility function to create or update the comment
            comment, created = create_or_update_comment(user_id=user_id, report_id=report_id, content=content)

            if comment is None:
                # If the comment creation or update failed (invalid input), return an error
                return JsonResponse({"error": "Failed to create or update the comment due to invalid input."},
                                    status=400)

            # Return the created or updated comment
            return JsonResponse({
                "id": comment.id,
                "user": comment.user_id,
                "content": comment.content,
                "created_at": comment.created_at,
            })

        except json.JSONDecodeError:
            # Handle invalid JSON input
            return HttpResponseBadRequest("Invalid JSON format.")
        except Exception as e:
            # Catch any other errors
            return HttpResponseBadRequest(str(e))
