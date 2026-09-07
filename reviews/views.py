from django.core.cache import cache
from django.db import IntegrityError
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Review, ReviewVote
from .permissions import IsAuthorOrAdmin
from .serializers import ReviewSerializer, ReviewVoteSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdmin]
    filterset_fields = ["location", "author", "rating"]

    def perform_create(self, serializer):
        try:
            serializer.save(author=self.request.user)
        except IntegrityError:
            raise ValidationError({"detail": "You already reviewed this location."})
        cache.delete_pattern("location_list:*")

    def perform_update(self, serializer):
        serializer.save()
        cache.delete_pattern("location_list:*")

    def perform_destroy(self, instance):
        instance.delete()
        cache.delete_pattern("location_list:*")

    @action(detail=True, methods=["post"])
    def vote(self, request, pk=None):
        review = self.get_object()
        serializer = ReviewVoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vote_type = serializer.validated_data["vote_type"]

        vote, created = ReviewVote.objects.get_or_create(
            review=review, user=request.user, defaults={"vote_type": vote_type}
        )
        if not created:
            if vote.vote_type == vote_type:
                return Response(
                    {"detail": "Already voted this way."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            vote.vote_type = vote_type
            vote.save(update_fields=["vote_type"])

        return Response({"detail": "Vote recorded.", "vote_type": vote.vote_type})
