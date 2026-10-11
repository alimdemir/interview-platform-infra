from django.urls import path

from .consumers import JobProgressConsumer

websocket_urlpatterns = [
    path("ws/jobs/<int:job_id>/", JobProgressConsumer.as_asgi()),
]
