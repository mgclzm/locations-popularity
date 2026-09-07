from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from locations.models import Category, Location, LocationView
from locations.services import redis_client

User = get_user_model()


class LocationViewCounterTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="viewer1", password="pass12345")
        self.other_user = User.objects.create_user(
            username="viewer2", password="pass12345"
        )
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
        self.url = f"/api/locations/{self.location.id}/"
        self._clear_redis_keys()

    def tearDown(self):
        self._clear_redis_keys()

    def _clear_redis_keys(self):
        for key in redis_client.keys(f"location_view:{self.location.id}:*"):
            redis_client.delete(key)

    def _redis_key_for(self, viewer_key):
        return f"location_view:{self.location.id}:{viewer_key}"

    def test_first_view_creates_record(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(LocationView.objects.filter(location=self.location).count(), 1)

    def test_second_view_same_user_within_hour_not_recorded(self):
        self.client.force_authenticate(self.user)

        self.client.get(self.url)
        self.client.get(self.url)
        self.client.get(self.url)

        self.assertEqual(LocationView.objects.filter(location=self.location).count(), 1)

    def test_different_users_both_recorded(self):
        self.client.force_authenticate(self.user)
        self.client.get(self.url)

        self.client.force_authenticate(self.other_user)
        self.client.get(self.url)

        self.assertEqual(LocationView.objects.filter(location=self.location).count(), 2)

    def test_anonymous_users_tracked_by_ip(self):
        response = self.client.get(self.url, REMOTE_ADDR="1.2.3.4")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        viewer_key = "ip:1.2.3.4"
        self.assertTrue(redis_client.exists(self._redis_key_for(viewer_key)))
        self.assertEqual(
            LocationView.objects.filter(
                location=self.location, viewer_key=viewer_key
            ).count(),
            1,
        )

    def test_redis_lock_ttl_is_set_to_one_hour(self):
        self.client.force_authenticate(self.user)
        self.client.get(self.url)

        viewer_key = get_viewer_key_stub = f"user:{self.user.id}"
        ttl = redis_client.ttl(self._redis_key_for(viewer_key))

        self.assertGreater(ttl, 0)
        self.assertLessEqual(ttl, 3600)
        self.assertGreater(ttl, 3500)

    def test_view_recorded_again_after_ttl_expires(self):
        self.client.force_authenticate(self.user)
        self.client.get(self.url)
        self.assertEqual(LocationView.objects.filter(location=self.location).count(), 1)
        viewer_key = f"user:{self.user.id}"
        redis_client.delete(self._redis_key_for(viewer_key))

        self.client.get(self.url)
        self.assertEqual(LocationView.objects.filter(location=self.location).count(), 2)
