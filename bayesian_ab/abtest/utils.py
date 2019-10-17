import functools
import numpy as np
import random
from .models import Campaign, Variant

# def ab_select(template):
#     def _decorator(func):
#         @functools.wrap(func)
#         def wrapper(*args, **kwargs):
#             print("Hello World")
#             return func(testvar="YOOO", *args, **kwargs)
#         return wrapper
#     return _decorator()

def ab_assign(campaign):

    ''' Function to assign user a variant based
    on latest updated distribution. Choice of algorithm includes:
        - Epsilon-Greedy
        - UCB1
        - Thompson Sampling
    '''
    variants = campaign.variants.all().values(
        'code',
        "impressions",
        'conversions',
        'conversion_rate',
        'html_template',
    )    

    return None

def epsilon_greedy(variant_vals, eps=0.1):

    ''' Epsilon greedy algorithm for the
    explore-exploit problem
    '''

    if random.random() < eps: 
        # Explore
        selected_variant = random.sample(variant_vals, 1)[0]

    else:
        # Select best variant
        best_conversion_rate = 0.0
        selected_variant = None
        for var in variant_vals:
            if var['conversion_rate'] > best_conversion_rate:
                best_conversion_rate = var['conversion_rate']
                selected_variant = var

            if var['conversion_rate'] == best_conversion_rate:
                # Break tie - randomly choose between current and best
                selected_variant = random.sample([var, selected_variant], 1)[0]

    return selected_variant

def thompson_sampling(variant_vals):

    ''' Thompson sampling
    '''
    selected_variant = None
    best_sample = 0.0
    for var in variant_vals:
        sample = np.random.beta(var['conversions'], var['impressions'] - var['conversions'] +1)
        if sample > best_sample:
            best_sample = sample
            selected_variant = var

    return selected_variant