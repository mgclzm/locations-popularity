from rest_framework import serializers

from .models import Category, Location


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "created_at"]
        read_only_fields = ["id", "created_at"]


class LocationSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    avg_rating = serializers.FloatField(read_only=True, default=None)
    reviews_count = serializers.IntegerField(read_only=True, default=0)
    views_last_7_days = serializers.IntegerField(read_only=True, default=0)
    popularity = serializers.FloatField(read_only=True, default=0)

    class Meta:
        model = Location
        fields = [
            "id",
            "name",
            "description",
            "category",
            "address",
            "latitude",
            "longitude",
            "author",
            "created_at",
            "updated_at",
            "avg_rating",
            "reviews_count",
            "views_last_7_days",
            "popularity",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]
