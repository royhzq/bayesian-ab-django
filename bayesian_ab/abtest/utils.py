import functools
import numpy as np
import random
import scipy
from .models import Campaign, Variant

# def ab_select(template):
#     def _decorator(func):
#         @functools.wrap(func)
#         def wrapper(*args, **kwargs):
#             print("Hello World")
#             return func(testvar="YOOO", *args, **kwargs)
#         return wrapper
#     return _decorator()

def ab_assign(request, campaign, default_template, algo='thompson', eps=0.1):

    ''' Function to assign user a variant based
    on latest updated distribution. Choice of algorithm includes:
        - Epsilon-Greedy (egreedy)
        - UCB1 (ucb1)
        - Thompson Sampling (thompson)
    '''
    if request.session.get(campaign.code):
        # User already previously assigned
        # Sticky session - User gets previously assigned template
        prev_assignment = request.session.get(campaign.code).get('variant')
        return prev_assignment.get('html_template', default_template)

    variants = campaign.variants.all().values(
        'code',
        "impressions",
        'conversions',
        'conversion_rate',
        'html_template',
    ) 
    # total_conversions = [ var['conversions'] for var in variants ]
    # total_impressions = [ var['impressions'] for var in variants ]
    if algo == 'thompson':
        assigned_variant = thompson_sampling(variants)
    if algo == 'egreedy':
        assigned_variant = epsilon_greedy(variants, eps=eps)
    if algo == 'UCB1':
        assigned_variant = UCB1(variants)
        
    # Remember assignment for session
    request.session[campaign.code] = assigned_variant
    request.session.modified = True

    return assigned_variant['html_template']

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

def UCB1(variant_vals):

    ''' Upper Confidence Bound
    '''
    selected_variant = None
    best_score = 0.0
    total_impressions = sum([ var['impressions'] for var in variant_vals ])
    for var in variant_vals:
        score = var['conversion_rate'] + np.sqrt(2*np.log(total_impressions)/var['impressions'])
        if score > best_score:
            best_score = score
            selected_variant = var
        if score == best_score:
            # Tie breaker
            selected_variant = random.sample([var, selected_variant], 1)[0]

    return selected_variant

## Stopping RUle
# http://www.claudiobellei.com/2017/11/02/bayesian-AB-testing/
# https://www.chrisstucchio.com/blog/2014/bayesian_ab_decision_rule.html
# http://www.evanmiller.org/bayesian-ab-testing.html

def h(a, b, c, d):

    ''' Closed form solution for P(X>Y).
    Where:
        X ~ Beta(a,b)
        Y ~ Beta(c,d)    

    Reference:
        https://www.chrisstucchio.com/blog/2014/bayesian_ab_decision_rule.html
        https://cdn2.hubspot.net/hubfs/310840/VWO_SmartStats_technical_whitepaper.pdf
        http://www.evanmiller.org/bayesian-ab-testing.html#implementation
    '''
    total = 0.0 
    for j in range(c):
        total += np.exp(betaln(a+j, b+d) - np.log(d+j) - betaln(1+j, d) - betaln(a, b))
    return 1 - total

def loss(a, b, c, d):
    ''' The expected loss of choosing variant X over Y
    Given that Y > X.
    Where:
        X ~ Beta(a,b)
        Y ~ Beta(c,d)    

    Example:
        loss(a=c, b=d, c=a, d=b)
    Reference:
        https://www.chrisstucchio.com/blog/2014/bayesian_ab_decision_rule.html
    '''
    return np.exp(betaln(a+1,b)-betaln(a,b))*h(a+1,b,c,d) - \
           np.exp(betaln(c+1,d)-betaln(c,d))*h(a,b,c+1,d)


