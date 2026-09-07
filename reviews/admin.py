from django.contrib import admin

from .models import Review, ReviewVote

# Register your models here.

admin.site.register(Review)
admin.site.register(ReviewVote)
