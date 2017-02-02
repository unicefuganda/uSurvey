from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from survey.forms.aboutus_form import AboutUsForm
from survey.models import Survey, AboutUs
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse
from survey.utils import views_helper



@login_required
def home(request):
    return render(request, 'home/index.html', {'surveys': Survey.objects.all().order_by('name'),
                                               'title': settings.PROJECT_TITLE,
                                               'twitter_token': settings.TWITTER_TOKEN,
                                               'twitter_url': settings.TWITTER_URL,
                                               'shape_file_uri': settings.SHAPE_FILE_URI,
                                               'loc_field': settings.SHAPE_FILE_LOC_FIELD,
                                               'alt_loc_field': settings.SHAPE_FILE_LOC_ALT_FIELD,
                                               'map_center': settings.MAP_CENTER})


def index(request):
    return render(request, 'main/index.html', {'title': settings.PROJECT_TITLE})


def about(request):
    if AboutUs.objects.count():
        about_us_content = AboutUs.objects.all()[0]
    else:
        about_us_content = AboutUs.objects.create(
            content="No content available yet !!")

    return render(request, 'home/about.html', {'about_content': about_us_content})


@permission_required('auth.can_view_users')
def edit(request):
    about_us = AboutUs.objects.all()[0]
    about_form = AboutUsForm(instance=about_us)
    if request.method == 'POST':
        about_form = AboutUsForm(instance=about_us, data=request.POST)
        if about_form.is_valid():
            about_form.save()
            message = "About us content successfully updated."
            messages.success(request, message)
            return HttpResponseRedirect("/about/")
    return render(request, 'home/edit.html', {'about_form': about_form})


@login_required
@permission_required('can_have_super_powers')
def activate_super_powers(request):
    if request.method == 'POST':
        # activate super powers for settings.SUPER_POWERS_DURATION
        views_helper.activate_super_powers(request)
        messages.info(request, 'Super Powers activated! You would now be able to perform actions like wiping off data')
        return HttpResponseRedirect(reverse('home_page'))
    else:
        return render(request, 'home/manage_super_powers.html')


@login_required
@permission_required('can_have_super_powers')
def deactivate_super_powers(request):
    if request.method == 'POST':
        # activate super powers for settings.SUPER_POWERS_DURATION
        views_helper.deactivate_super_powers(request)
        messages.info(request, 'Super powers deactivated!')
        return HttpResponseRedirect(reverse('home_page'))
    else:
        return render(request, 'home/manage_super_powers.html')





