from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.db.models.aggregates import Avg, Count
from django.db.models.functions import Coalesce
from django.utils import timezone


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    def get_queryset(self) -> models.QuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).active()


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])


class LocationQuerySet(SoftDeleteQuerySet):
    def with_stats(self):
        week_ago = timezone.now() - timedelta(days=7)
        return self.annotate(
            avg_rating=Avg("reviews__rating"),
            reviews_count=Count("reviews", distinct=True),
            views_last_7_days=Count(
                "views", filter=Q(views__created_at__gte=week_ago), distinct=True
            ),
        ).annotate(
            popularity=Coalesce(F("avg_rating"), 0.0) * 10
            + F("reviews_count") * 5
            + F("views_last_7_days") * 1
        )


class LocationManager(models.Manager.from_queryset(LocationQuerySet)):
    def get_queryset(self) -> models.QuerySet:
        return LocationQuerySet(self.model, using=self._db).active()


class Location(SoftDeleteModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="locations"
    )
    address = models.CharField(max_length=500)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="locations"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    objects = LocationManager()
    all_objects = models.Manager()


class LocationView(models.Model):
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="views"
    )
    viewer_key = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
