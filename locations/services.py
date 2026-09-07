import redis
from django.conf import settings

from .models import LocationView

redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)


def get_viewer_key(request):
    if request.user.is_authenticated:
        return f"user:{request.user.id}"
    return f"ip:{request.META.get('REMOTE_ADDR', 'unknown')}"


def track_view(location, request):
    viewer_key = get_viewer_key(request)
    redis_key = f"location_view:{location.id}:{viewer_key}"
    if redis_client.set(redis_key, 1, nx=True, ex=3600):
        LocationView.objects.create(location=location, viewer_key=viewer_key)
