from django.contrib import admin
from .models import User, ReportCategory, Report, Vote, Comment

admin.site.register(User)
admin.site.register(ReportCategory)
admin.site.register(Report)
admin.site.register(Vote)
admin.site.register(Comment)
