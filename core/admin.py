from django import forms
from django.contrib import admin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path, reverse

from core.utils import create_or_update_admin_comment
from core.utils import get_city_info_by_zipcodes
from .models import Report, AdminComment
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
    city_info.short_description = "City Info"

    def has_add_permission(self, request):
        return False


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

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['admin_comment_url'] = f"/admin/core/report/{object_id}/add_admin_comment/"
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

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
    list_display = ['user', 'report', 'content', 'created_at']
    readonly_fields = ['user', 'report', 'content', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# READONLY
@admin.register(AdminComment)
class AdminCommentAdmin(admin.ModelAdmin):
    list_display = ['admin', 'report', 'content', 'created_at']
    readonly_fields = ['admin', 'report', 'content', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
