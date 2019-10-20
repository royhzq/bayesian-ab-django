from django.shortcuts import render, redirect
from .utils import ab_assign, loss, h
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
    return redirect(dashboard)

def dashboard(request):
    ''' Demonstration dashboard for statistics on ab test
    '''
    campaign = Campaign.objects.get(name="Test Homepage")
    variant_vals = list(campaign.variants.all().order_by('code').values(
        'code',
        'impressions',
        'conversions',
        'conversion_rate',
        'html_template',
    ))
    x_vals = list(np.linspace(0,1,500))
    xy_vals = []
    max_y = 0
    for i, variant in enumerate(campaign.variants.all().order_by('code')):
        y_vals = variant.beta_pdf(x_vals)
        variant_vals[i]['xy'] = list(zip(x_vals, y_vals))
        variant_vals[i]['color'] = settings.COLOUR_PALETTE[i%len(settings.COLOUR_PALETTE)]
        if max(y_vals) > max_y:
            max_y = max(y_vals)

    h_ab = loss(
        variant_vals[0]['conversions'], 
        variant_vals[0]['impressions'] - variant_vals[0]['conversions'],
        variant_vals[1]['conversions'], 
        variant_vals[1]['impressions'] - variant_vals[1]['conversions']
    )
    h_ac = loss(
        variant_vals[0]['conversions'], 
        variant_vals[0]['impressions'] - variant_vals[0]['conversions'],
        variant_vals[2]['conversions'], 
        variant_vals[2]['impressions'] - variant_vals[2]['conversions']
    )
    h_ba = 1 - h_ab
    h_bc = loss(
        variant_vals[1]['conversions'], 
        variant_vals[1]['impressions'] - variant_vals[1]['conversions'],
        variant_vals[2]['conversions'], 
        variant_vals[2]['impressions'] - variant_vals[2]['conversions']
    )
    h_ca = 1 - h_ac
    h_cb = 1 - h_bc

    context = {
        'campaign':campaign,
        'variant_vals':variant_vals,
        'x_vals': json.dumps(x_vals),
        'max_y':max_y,
        'h_ab':h_ab,
        'h_ac':h_ac,
        'h_ba':h_ba,
        'h_bc':h_bc,
        'h_ca':h_ca,
        'h_cb':h_cb,
        'last_update': datetime.datetime.utcnow().strftime('%Y-%m-%d | %H:%M:%S')
    }
    return render(
        request,
        'abtest/dashboard.html',
        context
    )