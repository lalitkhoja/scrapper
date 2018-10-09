
from __future__ import unicode_literals

from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404
from django.utils.http import base36_to_int, int_to_base36
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.edit import FormView

from django.contrib import auth, messages
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User

from account import signals
from account.conf import settings
from account.forms import SignupForm, LoginUsernameForm
from account.forms import ChangePasswordForm, PasswordResetForm, PasswordResetTokenForm
from account.forms import SettingsForm
from account.hooks import hookset
from account.mixins import LoginRequiredMixin
from account.models import SignupCode, EmailAddress, EmailConfirmation, Account, AccountDeletion
from account.utils import default_redirect, get_form_data

from django.http import Http404, HttpResponseForbidden, HttpRequest, HttpResponse
from django.shortcuts import redirect, get_object_or_404, render_to_response, render
from django.views.generic import TemplateView, DetailView
from django.views.generic.edit import FormView, CreateView
import account.views
from .forms import SignupForm, addThingForm
from .models import UserProfile, addThing, itemdetails
from account.conf import settings

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from bs4 import BeautifulSoup
import cookielib
import mechanize

# signup view overwrided
class SignupView(account.views.SignupView):

    form_class = SignupForm

    def update_profile(self, form):
        UserProfile.objects.create(
            user = self.created_user,
            first_name = form.cleaned_data["first_name"],
            last_name = form.cleaned_data["last_name"],
            image = form.cleaned_data["image"],
            mobile = form.cleaned_data["mobile"],
            facebook = form.cleaned_data["facebook"],
            address = form.cleaned_data["address"]
            )

    def after_signup(self, form):
        self.update_profile(form)
        super(SignupView, self).after_signup(form)

@login_required
# profile view
def ProView(request, pk):
    user = get_object_or_404(UserProfile, user__pk=pk)
    path = ""
    for i in reversed(user.image.url):
        if i == '/':
            break
        else:
            path = i+path
    var = "{0}{1}".format(settings.MEDIA_URL, path)
    return render(request, 'sni/profile.html', {'user':user, 'var':var})

# profile detail view
class ProfileView(DetailView):
    model = UserProfile


# createview for add item
class addThingCreate(CreateView):
    template_name = "sni/addThing_create_form.html"
    form_class = addThingForm
    success_url = '/addthing/added/'
    model = addThing
    # adding current user using validation
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(addThingCreate, self).form_valid(form)



def homeView(request):
    items = itemdetails.objects.all().order_by("-id")
    item_image_list = []
    item_name_list = []
    item_price_list = []
    item_rating_list = []
    item_urls_list = []
    sources = []

    for item in items:
        item_image_list.append(item.itemimage)
        item_name_list.append(item.itemname)
        item_price_list.append(item.price)
        item_rating_list.append(item.rating)
        item_urls_list.append(item.itemurl)
        sources.append(item.source)

    
    itemlist = zip(item_name_list, item_price_list, item_image_list, item_rating_list, item_urls_list, sources)
    return render(request, 'homepage.html',{"itemlist":itemlist})


# check username in ajax calls
def validate_username(request):
    username = request.GET.get('username', None)
    data = {
        'is_taken': User.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(data)


def add_item_details(request):
    # method to scrap and save item details in database
    br = mechanize.Browser()
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)
    br.set_handle_equiv(True)
    br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    item_from_get_method = request.GET["item_name"]
    item_from_get_method = item_from_get_method.replace(" ", "+")
    print(item_from_get_method)
    url = "https://www.amazon.in/s/ref=nb_sb_noss?url=search-alias%3Daps&field-keywords="+item_from_get_method

    response = mechanize.urlopen(url)
    content = response.read()

    soup = BeautifulSoup(content,'html.parser')

    # now extract the data from soup

    extracted_items = soup.find("ul", {"id": "s-results-list-atf"})
 
    item_with_details = extracted_items.find_all('li')

    item_image_list = []
    item_name_list = []
    item_price_list = []
    item_rating_list = []
    item_urls_list = []

    for item in item_with_details:
        # item image
        try:
            item_url = item.find('img').get('src')
        except AttributeError:
            continue

        # item name
        try:
            item_name = item.find('h2').get_text()
            item_name = item_name.encode('utf-8').strip()
        except AttributeError:
            continue
        # item price 
        try:
            item_price = item.find("span", {"class": "s-price"}).get_text()
        except AttributeError:
            continue

        # strip item_price to get exact integer number
        item_price = item_price.strip()

        # item rating
        try:
            item_rating = item.find("a", {"class": "a-popover-trigger a-declarative"}).get_text()
        except AttributeError:
            continue

        # item url
        try:
            itemurl = item.find("a", {"class": "s-access-detail-page"})["href"]
        except AttributeError:
            continue

        # save the data in database to show
        itemdetails.objects.create(
            itemname=item_name,
            itemimage=item_url,
            price=item_price,
            rating=item_rating,
            itemurl=itemurl,
            source="amazon")

        # append the data to lists
        item_image_list.append(item_url)
        item_price_list.append(item_price)
        item_name_list.append(item_name)
        item_rating_list.append(item_rating)
        item_urls_list.append(itemurl)
        # print(item_urls_list)


    # extract the data from snapdeal
    
    urlsnap = "https://www.snapdeal.com/search?keyword=" + item_from_get_method
    response = mechanize.urlopen(urlsnap)
    content = response.read()

    soup = BeautifulSoup(content,'html.parser')

    extracted_items = soup.find("div", {"id": "products"})   
    
    item_with_details = extracted_items.find_all("div", {"class": "col-xs-6"})


    for i in item_with_details:
        try:
            imageurl = i.find("img", {"class":"product-image"})["src"]
        except KeyError:
            continue
        except AttributeError:
            continue

        try:
            itemname = i.find("p", {"class":"product-title"}).get_text()
        except KeyError:
            continue
        except AttributeError:
            continue

        try:
            itemrate = i.find("span", {"class":"product-price"}).get_text()
        except KeyError:
            continue
        except AttributeError:
            continue

        rating = "3 out of 5"

        try:
            itemurl = i.find("a", {"class": "dp-widget-link"})["href"]
        except AttributeError:
            continue

        itemdetails.objects.create(
            itemname=itemname,
            itemimage=imageurl,
            price=itemrate,
            rating=rating,
            itemurl=itemurl,
            source="snapdeal")

        item_image_list.append(imageurl)
        item_price_list.append(itemrate)
        item_name_list.append(itemname)
        item_rating_list.append(rating)
        item_urls_list.append(itemurl)      

    itemlist = zip(item_name_list, item_price_list, item_image_list, item_rating_list, item_urls_list)    
    return render(request, 'scrapeddata.html', {"itemlist":itemlist})


