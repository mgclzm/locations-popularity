from rest_framework import serializers

from .models import Review, ReviewVote


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "location",
            "author",
            "rating",
            "comment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]


class ReviewVoteSerializer(serializers.Serializer):
    vote_type = serializers.ChoiceField(choices=ReviewVote.VoteType.choices)
