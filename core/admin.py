from allauth.account.models import EmailAddress
from django import forms
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.db.models import Count, Case, When
from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from core.utils import create_or_update_admin_comment
from core.utils import get_city_info_by_zipcodes
from .models import Report, AdminComment, ReportTools
from .models import User, ReportCategory, Vote, Comment


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_active', 'is_superuser', 'date_joined']
    readonly_fields = [field.name for field in User._meta.fields if field.name != 'id']
    # All readonly, id invisible

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_superuser:
            return False
        return request.user.is_superuser

    def get_deleted_objects(self, objs, request):
        """
        Override this method to skip permission checks for related objects.
        """
        # Call the parent method to get the list of objects to delete and permission requirements
        deleted_objects, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)

        # Clear perms_needed to tell admin no permission check is needed for related objects
        perms_needed.clear()

        return deleted_objects, model_count, perms_needed, protected


# READONLY
@admin.register(ReportCategory)
class ReportCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    readonly_fields = ['name', 'description']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class AdminCommentForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea, label="Admin Comment")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):

    def has_module_permission(self, request):
        # Prevent this model menu from appearing in the admin sidebar
        return False

    def has_view_permission(self, request, obj=None):
        # Prevent viewing details and list pages
        return False

    def has_add_permission(self, request):
        # Prevent adding
        return False

    def has_delete_permission(self, request, obj=None):
        # Allow normal permission check for deletion
        return request.user.has_perm('core.delete_report')

    # Intercept all views to prevent page access errors
    def changelist_view(self, request, extra_context=None):
        raise Http404

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['admin_comment_url'] = reverse('admin:add_admin_comment', args=[object_id])
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        raise Http404

    def get_deleted_objects(self, objs, request):
        """
        Override this method to skip permission checks for related objects.
        """
        # Call the parent method to get the list of objects to delete and permission requirements
        deleted_objects, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)

        # Clear perms_needed to tell admin no permission check is needed for related objects
        perms_needed.clear()

        return deleted_objects, model_count, perms_needed, protected

    list_display = ['title', 'user', 'status', 'zipcode', 'city_info', 'created_at']

    readonly_fields = [
        'user', 'category', 'title', 'description',
        'image', 'zipcode', 'city_info', 'latitude', 'longitude', 'created_at'
    ]
    fields = (
        'title', 'user', 'category', 'description', 'image',
        'zipcode', 'city_info', 'latitude', 'longitude',
        'status', 'created_at'
    )

    def city_info(self, obj):
        if obj.zipcode:
            result = get_city_info_by_zipcodes([obj.zipcode])
            if result:
                info = result[0]
                return f"{info['place']}, {info['province']} ({info['zipcode']})"
        return "Unknown"

    city_info.short_description = _("City Info")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:report_id>/add_admin_comment/',
                self.admin_site.admin_view(self.add_admin_comment),
                name='add_admin_comment'
            ),
        ]
        return custom_urls + urls

    @staticmethod
    def add_admin_comment(request, report_id):
        report = Report.objects.get(pk=report_id)

        if request.method == 'POST':
            form = AdminCommentForm(request.POST)
            if form.is_valid():
                content = form.cleaned_data['content']
                comment, created = create_or_update_admin_comment(
                    admin_id=request.user.id,
                    report_id=report.id,
                    content=content
                )
                if created:
                    messages.success(request, "✅ Admin comment created.")
                else:
                    messages.success(request, "✏️ Admin comment updated.")
                return redirect(reverse('admin:core_report_change', args=[report_id]))
        else:
            existing = AdminComment.objects.filter(report=report, admin_id=request.user.id).first()
            form = AdminCommentForm(initial={'content': existing.content if existing else ''})

        return render(request, 'admin/add_admin_comment.html', {
            'form': form,
            'report': report,
            'title': 'Add or Update Admin Comment',
        })


# READONLY
@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'report', 'created_at']
    readonly_fields = ['user', 'report', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# READONLY
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'report_link', 'content', 'created_at']
    readonly_fields = ['user', 'report', 'content', 'created_at']

    def report_link(self, obj):
        url = reverse('admin:core_report_change', args=[obj.report.id])
        return format_html('<a href="{}">{}</a>', url, obj.report.title)

    report_link.short_description = _('Report')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# READONLY
@admin.register(AdminComment)
class AdminCommentAdmin(admin.ModelAdmin):
    list_display = ['admin', 'report_link', 'content', 'created_at']
    readonly_fields = ['admin', 'report', 'content', 'created_at']

    def report_link(self, obj):
        url = reverse('admin:core_report_change', args=[obj.report.id])
        return format_html('<a href="{}">{}</a>', url, obj.report.title)

    report_link.short_description = _('Report')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class ZipcodeSearchForm(forms.Form):
    zipcode = forms.CharField(label="Zipcode", max_length=10)


@admin.register(ReportTools)
class ReportToolAdmin(admin.ModelAdmin):
    change_list_template = "admin/core/reporttools/change_list.html"

    def has_add_permission(self, request):
        return False

    def changelist_view(self, request, extra_context=None):
        reports = None

        if request.method == 'POST':
            zipcode = request.POST.get('zipcode', '').strip()
            if zipcode.isdigit():
                reports = Report.objects.filter(zipcode=int(zipcode)).annotate(
                    vote_count=Count('votes')
                ).annotate(
                    status_priority=Case(
                        When(status='pending', then=2),
                        When(status='in_progress', then=1),
                        When(status__in=['resolved', 'rejected'], then=0),
                        default=0
                    )
                ).order_by('-vote_count', '-status_priority', '-created_at')
            else:
                self.message_user(request, "Invalid zipcode input.", level=messages.ERROR)

        context = {
            **self.admin_site.each_context(request),
            'reports': reports,
            'title': 'Custom ReportTools Admin',
        }
        return render(request, self.change_list_template, context)


admin.site.unregister(Group)
admin.site.unregister(Site)
admin.site.unregister(EmailAddress)
