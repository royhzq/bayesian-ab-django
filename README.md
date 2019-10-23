# Bayesian A/B Testing in Django

This application is an implementation of A/B testing for Django projects. The ```ab_test``` app helps in the easy implementation of A/B tests for Django applications. The testing framework implemented is bayesian in nature but may also be used for traditional frequentist A/B tests. ```ab_test``` is a standalone Django app and can be easily integrated with any Django 2.0 project.

You may try this out at the project's demo at [https://royhung.com/abtest/](https://royhung.com/abtest/)  The demo is a showcase of bayesian A/B testing on a [target page](https://royhung.com/abtest/), which, when visited will serve the user one of three versions (A/B/C) of the page. The goal is to find out which version has the highest clickthrough rate on the *Add To Cart* button. 

You may view the results for the demo A/B/C test at [https://royhung.com/abtest/dashboard](https://royhung.com/abtest/dashboard)

## Quickstart

### Running the application
To run the application yourself, first make sure Docker is installed. In the current project folder, run the command:
```bash
docker-compose up
```
This will build and start the docker containers for the Django application, Nginx, and Postgresql. Once launched, you can access application at http://127.0.0.1:1337. 

#### Built-in URL Paths
The project comes with a few url paths and views for demonstration purposes.
* ``` / ``` : Target test page that is undergoing the A/B test
* ``` /dashboard ``` : Dashboard to see the impressions/conversions and the beta distributions of the different variants served to users.
* ``` /simulation ``` : A separate application to simulate users on an A/B test page based on predetermined 'true' conversion rates set for each variant. 


### Installing the application on your Django 2.0 project

* Copy the ```ab_test``` folder into your django project root. 
* Add the app ```ab_test``` to ```INSTALLED_APPS``` in your ```settings.py``` file.
* Remove unwanted urlpaths in the ```urls.py``` of the ```ab_test``` app (for demo purposes only).
* Run migrations.

## Usage

A typical Django function-based view looks like the following:

```python 
from django.shortcuts import render

def homepage(request):

    template = "myproject/homepage.html"
    context = {
        'foo':'Hello World',
    }
    return render(
        request,
        template,
        context
    )
```

Let's say you'd like to test two versions of the homepage template (we'll call it variant A and variant B) and would like to conduct a bayesian A/B test to decide which version will generate more "conversion" in the home page. The function-based view will look like the following:

```python 
from django.shortcuts import render
from abtest.models import Campaign

def homepage(request):

    assigned_variant = ab_assign(
        request=request,
        campaign=Campaign.objects.get(name="Test Homepage"),
        default_template='abtest/homepage.html',
        algo='thompson'
    )
    template = assigned_variant['html_template']
    context = {
        'foo':'Hello World',
    }
    return render(
        request,
        template,
        context
    )
```

```ab_assign``` is the function that does the heavy lifting. It will access a A/B test ```Campaign``` model instance to determine the variants that will be tested. It will then assign a variant based on the explore-exploit algorithm of the user's choosing. The template associated with the assigned variant is then served to the user.
