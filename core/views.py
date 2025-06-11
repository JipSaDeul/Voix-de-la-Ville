# core.views

import json
import os
import uuid

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Q
from django.http import JsonResponse, HttpResponseBadRequest, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from core.cities.helper import get_zipcode_by_location
from core.utils import (get_user_id, create_vote, create_or_update_comment, nlp_categorize, auto_translate, \
                        build_report_data, detect_profanity)
from .models import Report, Comment, ReportCategory, AdminComment


@login_required
def home(request: HttpRequest) -> HttpResponse:
    """
    @brief Render the home page.
    @param request The HTTP request object.
    @return Rendered home page as HttpResponse.
    """
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
        N = int(request.GET.get("n", 10))
        reports = Report.objects.all().order_by("-created_at")[:N]
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
            if image:
                if image.content_type not in ["image/jpeg", "image/png"]:
                    return JsonResponse({"error": "Invalid image type"}, status=400)
                if image.size > 2 * 1024 * 1024:
                    return JsonResponse({"error": "Image is too large"}, status=400)
        else:
            data = json.loads(request.body)
            image = None

        title = data.get("title", "")
        description = data.get("description", "")

        profanity_title = detect_profanity(title, 0.95)
        profanity_desc = detect_profanity(description)
        latitude = data["latitude"]
        longitude = data["longitude"]

        zipcode = get_zipcode_by_location(latitude, longitude)

        if profanity_title["is_toxic"] or profanity_desc["is_toxic"]:
            return JsonResponse({
                "error": "Your report contains inappropriate language.",
                "title_score": profanity_title["score"],
                "description_score": profanity_desc["score"]
            }, status=400)

        category_data = nlp_categorize(description)
        if category_data is None:
            return JsonResponse({
                "error": "Your description could not be understood. Please describe the issue more clearly."
            }, status=400)

        category = ReportCategory.objects.filter(name=category_data["name"]).first()

        if not category:
            category = ReportCategory.objects.create(name=category_data["name"],
                                                     description=category_data["description"])

        current_user_id = get_user_id(request)  # get current user id
        if current_user_id is None:
            return JsonResponse({"error": "User not authenticated"}, status=401)

        report = Report.objects.create(
            user_id=current_user_id,
            category=category,
            title=data["title"],
            description=data["description"],
            latitude=latitude,
            longitude=longitude,
            zipcode=zipcode,
        )

        if image:
            ext = os.path.splitext(image.name)[1]
            unique_name = f"{uuid.uuid4().hex}{ext}"
            report.image.save(unique_name, image)

        return JsonResponse({"id": report.id}, status=201)


@login_required
@require_GET
def user_reports_by_time(request):
    """
    Returns reports created by the current user, filtered by an optional time range,
    and sorted by creation time in descending order (latest first).
    """
    user_id = get_user_id(request)
    if user_id is None:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    start_time_str = request.GET.get("start")
    end_time_str = request.GET.get("end")

    try:
        # Parse start and end time from query parameters
        start_time = parse_datetime(start_time_str) if start_time_str else None
        end_time = parse_datetime(end_time_str) if end_time_str else now()

        # Base queryset: reports created by the current user
        reports = Report.objects.filter(user_id=user_id)

        # Apply time filtering if provided
        if start_time:
            reports = reports.filter(created_at__gte=start_time)
        if end_time:
            reports = reports.filter(created_at__lte=end_time)

        # Sort reports by creation time (latest first)
        reports = reports.order_by("-created_at")

        # Use helper to build response data
        data = build_report_data(reports)
        return JsonResponse({"reports": data})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_GET
@login_required
def user_voted_reports(request):
    """
    Returns reports the current user has voted on, sorted by latest vote time.
    """
    user_id = get_user_id(request)
    if user_id is None:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    reports = (
        Report.objects.filter(votes__user_id=user_id)
        .annotate(vote_time=Max("votes__created_at"))
        .order_by("-vote_time")
    )

    if not reports.exists():
        return JsonResponse({"reports": []})

    data = build_report_data(reports)
    return JsonResponse({"reports": data})


@require_GET
@login_required
def user_commented_reports(request):
    """
    Returns reports the current user has commented on, sorted by latest comment time.
    Includes admin comments if the user is a superuser.
    """
    user = request.user
    user_id = user.id

    if user_id is None:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    # Base Q: user comments
    q = Q(comments__user_id=user_id)

    # Add AdminComment only if user is superuser (admin)
    if user.is_superuser:
        q |= Q(admin_comments__admin_id=user_id)

    reports = (
        Report.objects.filter(q)
        .distinct()
        .annotate(last_commented=Max("comments__created_at"))
        .order_by("-last_commented")
    )
    if not reports.exists():
        return JsonResponse({"reports": []})

    return JsonResponse({"reports": build_report_data(reports)})


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

            user_id = get_user_id(request)

            # Ensure that the necessary fields are present
            if user_id is None or not (data.get("report_id"), int):
                raise TypeError("Invalid input types for 'user_id' or 'report_id'")

            # Call the create_vote utility function
            vote, created = create_vote(
                user_id=user_id,
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
        admin_comments = AdminComment.objects.filter(report=report).order_by("created_at")
        admin_data = [
            {
                "id": c.id,
                "user": c.admin_id,
                "username": c.admin.username,
                "is_admin": True,
                "content": c.content,
                "created_at": c.created_at,
            }
            for c in admin_comments
        ]

        comments = Comment.objects.filter(report=report).order_by("created_at")
        user_data = [
            {
                "id": c.id,
                "user": c.user_id,
                "username": c.user.username,
                "is_admin": False,
                "content": c.content,
                "created_at": c.created_at,
            }
            for c in comments
        ]

        all_data = admin_data + user_data

        return JsonResponse({"comments": all_data})

    elif request.method == "POST":
        try:
            # Parse the incoming JSON data
            body = json.loads(request.body.decode())
            user_id = get_user_id(request)
            content = body.get("content")

            profanity_result = detect_profanity(content)
            if profanity_result["is_toxic"]:
                return JsonResponse({
                    "error": "Your comment contains inappropriate language.",
                    "score": profanity_result["score"]
                }, status=400)

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
