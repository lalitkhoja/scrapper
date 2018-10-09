from django.contrib import admin
from .models import UserProfile, addThing, itemdetails

admin.site.register(UserProfile)
# admin.site.register(addThing)
admin.site.register(itemdetails)
