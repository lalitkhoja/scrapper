from django.conf import settings
from django.db import models
from django import utils
import datetime


class UserProfile(models.Model):
    """
    model for storing user information for authenticated user
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete = models.CASCADE, primary_key = True)
    first_name = models.TextField(default = " ")
    last_name = models.TextField(default = " ")
    image = models.ImageField(default = " ", upload_to = settings.MEDIA_ROOT)
    mobile = models.TextField(default = " ")
    address = models.TextField(default = " ")
    facebook = models.TextField(default = " ")
    def __str__(self):
    	return "{0}".format(self.user)



class addThing(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE, blank =True, related_name = 'owneruser')
    soundname = models.CharField(default=" ", max_length=30)
    soundimage = models.ImageField(default=" ", upload_to = settings.MEDIA_ROOT+"/things/")
    sound = models.FileField(default=" ", upload_to = settings.MEDIA_ROOT+"/sounds/")
    def __str__(self):
        return "{0}".format(self.soundname)

    def get_absolute_url(self):
        return "/buyitem/%i/" % self.id



class itemdetails(models.Model):
    """
    model for saving item details
    """
    itemname = models.CharField(default=" ", max_length=200)
    itemimage = models.CharField(default=" ", max_length=200)
    price = models.CharField(default=" ", max_length=200)
    rating = models.CharField(default=" ", max_length=200)
    itemurl = models.CharField(default=" ", max_length=300)
    source = models.CharField(default=" ", max_length=300)
    def __str__(self):
        return "{0}".format(self.itemname)