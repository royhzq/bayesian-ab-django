from django.shortcuts import render
from .utils import ab_assign
from .models import Campaign, Variant

def save_new_session(request):
    if not request.session.session_key:
        request.session.save()

def homepage(request, *args, **kwargs):

    ''' Homepage view where we test different versions
    of the html template
    ''' 
    save_new_session(request) # Ensure session exists 
    campaign = Campaign.objects.get(name="Test Homepage")
    variants = campaign.variants.all().values(
        'code',
        "impressions",
        'conversions',
        'conversion_rate',
        'html_template',
    )
    template = ab_assign(
        request=request,
        campaign=campaign,
        default_template='abtest/homepage.html',
        sticky_session=False,
        algo='thompson',
    )
    context = {
        'campaign':campaign,
        'codetype':type(campaign.code),
        'session_key':request.session.session_key,
        'variants':variants,
    }

    return render(
        request,
        template,
        context
    )

def clear_stats(request):
    ''' For dev only.
    Clears all variant impressions / conversions
    '''
    Variant.objects.all().update(
        conversions=0,
        impressions=0,
    )
    return render(
        request,
        'abtest/clear_stats.html',
        {}
    )

def dashboard(request):
    ''' For dev only.
    View dashboard for statistics on ab test
    '''
    
    return render(
        request,
        'abtest/dashboard.html',
        {}
    )