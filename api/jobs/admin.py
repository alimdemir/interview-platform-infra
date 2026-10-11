from django.contrib import admin

from .models import Job, JobEvent, JobResult


class JobEventInline(admin.TabularInline):
    model = JobEvent
    extra = 0
    fields = ("seq", "level", "message")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "status", "duration_seconds", "created_at")
    list_filter = ("kind", "status")
    inlines = [JobEventInline]


@admin.register(JobEvent)
class JobEventAdmin(admin.ModelAdmin):
    list_display = ("job", "seq", "level", "message")
    list_filter = ("level",)


@admin.register(JobResult)
class JobResultAdmin(admin.ModelAdmin):
    list_display = ("job", "source_event", "created_at")
