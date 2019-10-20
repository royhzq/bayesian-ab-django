from django.shortcuts import render
from .utils import ab_assign
from .models import Campaign, Variant
from django.conf import settings
import numpy as np
import json
import datetime

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
    ''' Demonstration dashboard for statistics on ab test
    '''
    campaign = Campaign.objects.get(name="Test Homepage")
    variant_vals = list(campaign.variants.all().order_by('id').values(
        'code',
        'impressions',
        'conversions',
        'conversion_rate',
        'html_template',
    ))
    x_vals = list(np.linspace(0,1,500))
    xy_vals = []
    max_y = 0
    for i, variant in enumerate(campaign.variants.all().order_by('id')):
        y_vals = variant.beta_pdf(x_vals)
        variant_vals[i]['xy'] = list(zip(x_vals, y_vals))
        variant_vals[i]['color'] = settings.COLOUR_PALETTE[i%len(settings.COLOUR_PALETTE)]
        if max(y_vals) > max_y:
            max_y = max(y_vals)

    context = {
        'campaign':campaign,
        'variant_vals':variant_vals,
        'x_vals': json.dumps(x_vals),
        'max_y':max_y,
        'last_update': datetime.datetime.utcnow().strftime('%Y-%m-%d | %H:%M:%S') 
    }
    return render(
        request,
        'abtest/dashboard.html',
        context
    )