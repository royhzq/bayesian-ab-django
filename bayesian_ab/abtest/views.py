from django.shortcuts import render
# from .utils import ab_select
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
    template = kwargs.get('template', 'abtest/homepage.html')
    testvar = kwargs.get('testvar','None found')
    context = {
        'testvar':testvar,
        'campaign':campaign,
        'variants':variants,
    }

    return render(
        request,
        template,
        context
    )