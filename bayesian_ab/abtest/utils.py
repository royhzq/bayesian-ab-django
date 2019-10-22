import numpy as np
import random
import scipy.stats
import json
from .models import Campaign, Variant
from scipy.special import betaln

def ab_assign(request, campaign, default_template, 
            sticky_session=True, algo='thompson', eps=0.1):

    ''' Function to assign user a variant based
    on latest updated distribution. Choice of algorithm includes:
        - Epsilon-Greedy (egreedy)
        - UCB1 (ucb1)
        - Thompson Sampling (thompson)
    '''
    code = str(campaign.code)
    # Sticky session - User gets previously assigned template
    if request.session.get(code):
        if request.session.get(code).get('html_template') and sticky_session:
           return request.session.get(code).get('html_template', default_template)
    else:
        # Register new session variable
        request.session[code] = {
            'html_template': '',
            'i': 1, # Session impressions
            'c': 0, # Session conversions
        }

    variants = campaign.variants.all().values(
        'code',
        "impressions",
        'conversions',
        'conversion_rate',
        'html_template',
    ) 
    if algo == 'thompson':
        assigned_variant = thompson_sampling(variants)
    if algo == 'egreedy':
        assigned_variant = epsilon_greedy(variants, eps=eps)
    if algo == 'UCB1':
        assigned_variant = UCB1(variants)
    if algo == 'uniform':
        assigned_variant = random.sample(list(variants), 1)[0]

    # Record assigned template as session variable
    request.session[code]['html_template'] = assigned_variant['html_template']
    request.session.modified = True

    return assigned_variant

def epsilon_greedy(variant_vals, eps=0.1):
    """Epsilon-greedy algorithm implementation 
    on Variant model values.

    Parameters
    ----------
    variant_vals : list
        A list of dictionary mappings of Variant field values for
        a given Campaign object. Required ``Variant`` fields are
        ``code`` ``impressions`` ``conversions`` ``conversion_rate`` 
        ``html_template``. For example: ::

            Campaign.objects.get(code='xxx').values(
                'code',
                'impressions',
                'conversions',
                'conversion_rate',
                'html_template'
            )    

    eps : float
        Exploration parameter. Values between 0.0 and 1.0.
        Defaults to 0.1

    Returns
    -------
    selected_variant : dict
        The selected dictionary mapping of Variant fields
        from ``variant_vals`` list, as chosen by the epsilon_greedy
        algorithm

    """

    if random.random() < eps: 
        # If random number < eps, exploration is chosen over 
        # exploitation
        selected_variant = random.sample(list(variant_vals), 1)[0]

    else:
        # If random number >= eps, exploitation is chosen over
        # exploration
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
    """Thompson Sampling algorithm implementation 
    on Variant model values.

    Parameters
    ----------
    variant_vals : list
        A list of dictionary mappings of Variant field values for
        a given Campaign object. Required ``Variant`` fields are
        ``code`` ``impressions`` ``conversions`` ``conversion_rate`` 
        ``html_template``. For example: ::

            Campaign.objects.get(code='xxx').values(
                'code',
                'impressions',
                'conversions',
                'conversion_rate',
                'html_template'
            )            

    Returns
    -------
    selected_variant : dict
        The selected dictionary mapping of Variant fields
        from ``variant_vals`` list, as chosen by the Thompson Sampling
        algorithm

    """
    selected_variant = None
    best_sample = 0.0
    for var in variant_vals:
        sample = np.random.beta(
            max(var['conversions'], 1), 
            max(var['impressions'] - var['conversions'],1 )
        )
        if sample > best_sample:
            best_sample = sample
            selected_variant = var

    return selected_variant

def UCB1(variant_vals):
    """Upper Confidence Bound algorithm implementation 
    on Variant model values.

    Parameters
    ----------
    variant_vals : list
        A list of dictionary mappings of Variant field values for
        a given Campaign object. Required ``Variant`` fields are
        ``code`` ``impressions`` ``conversions`` ``conversion_rate`` 
        ``html_template``. For example: ::

            Campaign.objects.get(code='xxx').values(
                'code',
                'impressions',
                'conversions',
                'conversion_rate',
                'html_template'
            )            

    Returns
    -------
    selected_variant : dict
        The selected dictionary mapping of Variant fields
        from ``variant_vals`` list, as chosen by the UCB1
        algorithm

    """
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

def h(a, b, c, d):
    """Closed form solution for P(X>Y).
    Where:
        X ~ Beta(a,b), Y ~ Beta(c,d)  

    Parameters
    ----------
    a : int
        alpha shape parameter for the beta distribution. a > 0
    b : int
        beta shape parameter for the beta distribution. b > 0

    Returns
    -------
    float
        Returns probability of X > Y 

    References
    ----------
        https://www.chrisstucchio.com/blog/2014/bayesian_ab_decision_rule.html
 
    """
    total = 0.0 
    for j in range(c):
        total += np.exp(betaln(a+j, b+d) - np.log(d+j) - betaln(1+j, d) - betaln(a, b))
    return 1 - total

def loss(a, b, c, d):
    """Expected loss function built on P(X>Y)
    Where:
        X ~ Beta(a,b), Y ~ Beta(c,d)  

    Parameters
    ----------
    a : int
        alpha shape parameter for the beta distribution. a > 0
    b : int
        beta shape parameter for the beta distribution. b > 0

    Returns
    -------
    float
        Returns the expected loss in terms of conversion rate
        when you pick variant Y over X when variant X actually has a higher 
        conversion rate than Y.

    References
    ----------
        https://www.chrisstucchio.com/blog/2014/bayesian_ab_decision_rule.html
        https://cdn2.hubspot.net/hubfs/310840/VWO_SmartStats_technical_whitepaper.pdf
 
    """
    return np.exp(betaln(a+1,b)-betaln(a,b))*h(a+1,b,c,d) - \
           np.exp(betaln(c+1,d)-betaln(c,d))*h(a,b,c+1,d)


def sim_page_visits(campaign, conversion_rates={}, n=1, eps=0.1, algo='thompson'):

    """ Simulate `n` page visits to the page that is being A/B tested. 
    The probability of each simulated page visited generating a conversion
    is determined by the conversion rates provided in the `conversion_rates` param.

    Parameters
    ----------
    campaign : :obj:`Campaign`
        The A/B test Campaign model object which will be subject to the simulation 
    conversion_rates : dict: ``{code: probability}``
        Dictionary mapping to contain the probability of conversion for each 
        simulated page visit for each Variant available in the campaign.
    n : int
        Number of page visits to simulate.
    algo : str
        Algorithm to determine the assignment (explore-exploit) of the Variant
        to the page request. Valid values are `thompson`, `egreedy`, `uniform`, `UCB1`.
        Defaults to `thompson`.

    Returns
    -------
    
    """

    # Simulate users visiting variants of page
    # Given dict of 'true' conversion rates. 
    # Where dict = { 'A':0.5, 'B':0.84, 'C':0.12} example
    # If key-value pair for variant not found, defaults to 0.5

    variants = campaign.variants.all().values(
        'code',
        "impressions",
        'conversions',
        'conversion_rate',
        'html_template',
    ) 

    for i in range(n):

        if algo == 'thompson':
            assigned_variant = thompson_sampling(variants)
        if algo == 'egreedy':
            assigned_variant = epsilon_greedy(variants, eps=eps)
        if algo == 'UCB1':
            assigned_variant = UCB1(variants)
        if algo == 'uniform':
            assigned_variant = random.sample(list(variants), 1)[0]

        # Simulate user conversion after version assigned

        conversion_prob = conversion_rates.get(assigned_variant['code'], 0.5)
        conversion = 1 if random.random() > 1 - conversion_prob else 0
        variant = Variant.objects.get(campaign=campaign, code=assigned_variant['code'])
        variant.impressions = variant.impressions + 1
        variant.conversions = variant.conversions + conversion
        variant.conversion_rate = variant.conversions / variant.impressions
        variant.save()

    return True