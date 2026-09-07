from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from locations.models import Category, Location

User = get_user_model()


class ReviewApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pass12345")
        self.category = Category.objects.create(name="Parks")
        self.location = Location.objects.create(
            name="Park",
            description="desc",
            category=self.category,
            address="addr",
            latitude=1,
            longitude=1,
            author=self.user,
        )

    def test_create_review_requires_auth(self):
        response = self.client.post(
            "/api/reviews/",
            {"location": self.location.id, "rating": 5, "comment": "nice"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_review_rejected(self):
        self.client.force_authenticate(self.user)
        url = "/api/reviews/"
        self.client.post(
            url, {"location": self.location.id, "rating": 5, "comment": "nice"}
        )
        response = self.client.post(
            url, {"location": self.location.id, "rating": 4, "comment": "again"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LocationSoftDeleteTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u2", password="pass12345")
        self.category = Category.objects.create(name="Museums")
        self.location = Location.objects.create(
            name="Museum",
            description="desc",
            category=self.category,
            address="addr",
            latitude=1,
            longitude=1,
            author=self.user,
        )

    def test_soft_delete_hides_but_keeps_record(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(f"/api/locations/{self.location.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Location.objects.filter(id=self.location.id).exists())
        self.assertTrue(Location.all_objects.filter(id=self.location.id).exists())


from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from locations.models import LocationView
from reviews.models import Review

User = get_user_model()


class LocationCalculatedFieldsTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username="author", password="pass12345")
        self.reviewer1 = User.objects.create_user(username="rev1", password="pass12345")
        self.reviewer2 = User.objects.create_user(username="rev2", password="pass12345")
        self.category = Category.objects.create(name="Parks")
        self.location = Location.objects.create(
            name="Park",
            description="desc",
            category=self.category,
            address="addr",
            latitude=1,
            longitude=1,
            author=self.author,
        )

    def test_location_without_reviews_has_no_rating_but_has_popularity_zero(self):
        result = Location.objects.with_stats().get(id=self.location.id)
        self.assertIsNone(result.avg_rating)
        self.assertEqual(result.reviews_count, 0)
        self.assertEqual(result.popularity, 0.0)

    def _add_view(self, viewer_key, days_ago):
        view = LocationView.objects.create(
            location=self.location, viewer_key=viewer_key
        )
        LocationView.objects.filter(id=view.id).update(
            created_at=timezone.now() - timedelta(days=days_ago)
        )
        return view

    def test_avg_rating_and_popularity_calculated_correctly(self):
        Review.objects.create(
            location=self.location, author=self.reviewer1, rating=5, comment="great"
        )
        Review.objects.create(
            location=self.location, author=self.reviewer2, rating=3, comment="ok"
        )
        self._add_view("ip:1.1.1.1", days_ago=1)
        self._add_view("ip:2.2.2.2", days_ago=6)
        self._add_view("ip:3.3.3.3", days_ago=10)

        result = Location.objects.with_stats().get(id=self.location.id)

        expected_avg_rating = (5 + 3) / 2
        expected_reviews_count = 2
        expected_views_last_7_days = 2
        expected_popularity = (
            expected_avg_rating * 10
            + expected_reviews_count * 5
            + expected_views_last_7_days * 1
        )

        self.assertAlmostEqual(float(result.avg_rating), expected_avg_rating, places=2)
        self.assertEqual(result.reviews_count, expected_reviews_count)
        self.assertEqual(result.views_last_7_days, expected_views_last_7_days)
        self.assertAlmostEqual(float(result.popularity), expected_popularity, places=2)

    def test_deleted_review_author_review_excluded_after_soft_delete_of_location(self):
        Review.objects.create(
            location=self.location, author=self.reviewer1, rating=5, comment="great"
        )
        self.location.delete()

        self.assertFalse(
            Location.objects.with_stats().filter(id=self.location.id).exists()
        )
        self.assertTrue(Location.all_objects.filter(id=self.location.id).exists())
