import pandas as pd
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import LocationFilter
from .models import Category, Location
from .permissions import IsOwnerOrAdmin
from .serializers import CategorySerializer, LocationSerializer
from .services import track_view


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class LocationViewSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    filterset_class = LocationFilter
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "avg_rating", "popularity"]

    def get_queryset(self):
        return Location.objects.with_stats()

    def list(self, request, *args, **kwargs):
        cache_key = f"location_list:{request.get_full_path()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=300)
        return response

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        track_view(instance, request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        cache.delete_pattern("location_list:*")

    def perform_update(self, serializer):
        serializer.save()
        cache.delete_pattern("location_list:*")

    def perform_destroy(self, instance):
        instance.delete()
        cache.delete_pattern("location_list:*")

    @action(detail=False, methods=["get"])
    def export(self, request):
        fmt = request.query_params.get("format", "json")
        queryset = self.filter_queryset(self.get_queryset())
        data = self.get_serializer(queryset, many=True).data

        if fmt == "csv":
            df = pd.DataFrame(data)
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = "attachment; filename=locations.csv"
            df.to_csv(response, index=False)
            return response

        return Response(data)
