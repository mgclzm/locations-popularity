from django.contrib import admin

# Register your models here.
from .models import Category, Location

admin.site.register(Category)
admin.site.register(Location)
