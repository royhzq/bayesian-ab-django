# Bayesian A/B Testing in Django

This application is an implementation of A/B testing for Django projects. The **ab_test** app helps in the easy implementation of A/B tests for Django applications. The testing framework implemented is bayesian in nature but may also be used for traditional frequentist A/B tests. **ab_test** is a standalone Django app and can be easily integrated with any Django 2.0 project.

You may try this out at the project's demo at [https://royhung.com/abtest/](https://royhung.com/abtest/)  The demo is a showcase of bayesian A/B testing on a [target page](https://royhung.com/abtest/), which, when visited will serve the user one of three versions (A/B/C) of the page. The goal is to find out which version has the highest clickthrough rate on the *Add To Cart* button. 

You may view the results for the demo A/B/C test at [https://royhung.com/abtest/dashboard](https://royhung.com/abtest/dashboard)  

For more details on bayesian A/B testing in Django, visit [https://royhung.com/bayesian-ab-testing](https://royhung.com/bayesian-ab-testing). 

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

## Models
The app consists of two models whose purpose is to store A/B test campaign data.
* ```Campaign``` model holds administrative details of the experiment such as name, description of the test, and if the test is active, etc.
* ```Variant``` model with a many-to-one relationship with ```Campaign```. Each variant is related to one campaign and represents the version to be tested (i.e, A/B/C). The model stores the variant details such as the file path to the template version, as well as impressions / conversions.

Run *setup_data.py* to create a test campaign with three variants.
```python
from abtest.models import Campaign, Variant

# Setup an AB Testing campaign
campaign, created = Campaign.objects.get_or_create(
    name="Test Homepage",
    description="Testing Homepage designs"    
)

# Create three variants
for code in ['A', 'B', 'C']:
    variant, created = Variant.objects.get_or_create(
        campaign=campaign,
        code=code,
        name=f'Homepage Design {code}',
        html_template=f'abtest/homepage_{code}.html'
    )
```

## API Reference


### Collecting User Responses
Use this API to collect responses from users visiting the page under A/B testing.
This API is used to register impressions from page visits and can also be used
to register conversions when it happens.

```bash
POST /api/experiment/response
```

#### Request POST JSON Example

```json
{
    "campaign_code": "eec7dbc2-eb60-4aad-8756-f5317c5254c5",
    "variant_code" : "A",
    "register_impression" : true,
    "register_conversion" : false,
    "params" : {}
}
```
| Property | Type |Description | Required
| --- | --- | :- | --- |
|``` campaign_code ```| String | Unique UUID4 code for ```Campaign``` object  | Yes |
|``` variant_code ```| String | variant code for ```Variant``` object in campaign  | Yes |
|``` register_impression ```| Boolean | If true, POST request will increment the impression count in the ```Variant``` object by 1 | Yes |
|``` register_conversion ```| Boolean | If true, POST request will increment the conversion count in the ```Variant``` object by 1  | Yes |
|``` params ```| Object | Json field for additional parameters to record from the event  | No |

#### Response JSON Example
```json
{
    "details": "Response registered.",
}
```
| Property | Type |Description |
| --- | --- | :- |
| ``` details ``` | String |  Message of successful POST request |
