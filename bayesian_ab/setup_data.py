#Setup Django environment to access models
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bayesian_ab.settings")

import django
django.setup()

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