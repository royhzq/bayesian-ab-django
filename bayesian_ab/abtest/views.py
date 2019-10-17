from django.shortcuts import render
# from .utils import ab_select
from .models import Campaign, Variant
# Create your views here.
def homepage(request, *args, **kwargs):

    ''' Homepage view where we test different versions
    of the html template
    ''' 
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