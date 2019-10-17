import uuid
from django.utils import timezone
from django.db import models

# Create your models here.

class Campaign(models.Model):

    ''' Record for AB Tests conducted
    '''
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text='timestamp of creation of campaign' 
    )
    code = models.UUIDField(
        default=uuid.uuid4, 
        editable=False,
        help_text='AB test campaign code'
    )
    name = models.CharField(
        unique=True,
        max_length=255,
        help_text='Name of AB test'
    )
    description = models.TextField(
        blank=True,
        default='',
        help_text='Description of AB test'
    )

    def __str__(self):
        return f'AB Test Campaign: {self.code}, {self.name}'

# Stopping date
# Max observations

class Variant(models.Model):

    ''' Model to store variants (treatments)
    within an AB test campaign. Variants are the different
    versions served to users (A/B/C...)
    '''

    campaign = models.ForeignKey(
        Campaign,
        related_name='variants',
        on_delete=models.CASCADE,
    )
    code = models.CharField(
        max_length=32,
        help_text='Variant code, (i.e., A, B, C etc)'
    )
    name = models.CharField(
        max_length=64,
        help_text='Name of variant'
    )
    impressions = models.IntegerField(
        default=1,
        help_text='Number of times variant was shown/visited'
    )
    conversions = models.IntegerField(
        default=1,
        help_text='Number of conversions for variant'
    )
    conversion_rate = models.FloatField(
        default=1.0,
        help_text='conversions / impressions'
    )
    html_template = models.FilePathField(
        null=True,
        help_text='Path to HTML template for variant View'
    )
    def __str__(self):
        return f'Variant: {self.code} | {self.campaign.code} '
