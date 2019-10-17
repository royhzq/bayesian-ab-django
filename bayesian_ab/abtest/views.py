from django.shortcuts import render
from .utils import ab_select
# Create your views here.

def homepage(request):

    ''' Homepage view where we test different versions
    of the html template
    '''

    context = {}
    template = 'abtest/homepage.html'
    return render(
        request,
        template,
        context
    )