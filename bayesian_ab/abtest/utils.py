import functools
import numpy as np
import random
import scipy.stats
import json
from .models import Campaign, Variant
from scipy.special import betaln

def ab_assign(request, campaign, default_template, sticky_session=True, algo='thompson', eps=0.1):

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

    # Record assigned template
    request.session[code]['html_template'] = assigned_variant['html_template']
    request.session.modified = True

    return assigned_variant

def epsilon_greedy(variant_vals, eps=0.1):

    ''' Epsilon greedy algorithm for the
    explore-exploit problem
    '''

    if random.random() < eps: 
        # Explore
        selected_variant = random.sample(list(variant_vals), 1)[0]

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
        sample = np.random.beta(max(var['conversions'],1), max(var['impressions'] - var['conversions'],1))
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


class SimVariant:
    # Variant object for running simulation
    def __init__(self, p):
        self.p = p
        self.a = 1.0
        self.b = 1.0

    def simulate(self):
        # simulate a visit
        # returns 1 if conversion occurred
        return random.random() < self.p

    def sample(self):
        return np.random.beta(self.a, self.b)

    def update(self, x):
        # x is 1 or 0 for convert / no convert
        self.a += x
        self.b += 1-x


def experiment(p1, p2, p3, N=1000, algo="uniform", eps=0.2  ):
    
    # Simulate experiment with three variants
    # Returns array of y values for distributions
    # At checkpoints N=10, N=20, N=40, ... N=100

    A = SimVariant(p=p1)
    B = SimVariant(p=p2)
    C = SimVariant(p=p3)
    variants = [A, B, C]

    #  initialize dataset
    dataset = []
    x_vals = list(np.linspace(0,1,500))
    init_y_val = list(scipy.stats.beta.pdf(x_vals, 1, 1))
    init_xy_val = list(zip(x_vals, init_y_val))
    dataset.append({
        'N': 0,
        'A':{'a':1, 'b' : 1 },
        'B':{'a':1, 'b' : 1 },
        'C':{'a':1, 'b' : 1 },
        'xy_A': init_xy_val,
        'xy_B': init_xy_val,
        'x_vals': x_vals,
        'xy_C': init_xy_val,
        'max_y': 2,
    })

    for i in range(N):

        if algo == 'uniform':
            # Random selection
            selected = random.sample(variants, 1)[0]
            selected.update(selected.simulate())
            
        if algo == 'thompson':
            variants_samples = [A.sample(), B.sample(), C.sample()]
            selected = variants[variants_samples.index(max(variants_samples))]
            selected.update(selected.simulate())
            
        if algo == 'egreedy':
            # epsilon is default 0.1
            if random.random() < 0.1:
                selected = random.sample(variants, 1)[0]
                selected.update(selected.simulate())
            else:
                variants_rates = [
                    A.a/(A.a+A.b),
                    B.a/(B.a+B.b),
                    C.a/(C.a+C.b)
                ]
                selected = variants[variants_rates.index(max(variants_rates))]
                selected.update(selected.simulate())

        if algo == 'UCB1':
            variants_scores = [
                A.a/(A.a+A.b) + np.sqrt(2*np.log(i+1)/(A.a + A.b)),
                B.a/(B.a+B.b) + np.sqrt(2*np.log(i+1)/(B.a + B.b)),
                C.a/(C.a+C.b) + np.sqrt(2*np.log(i+1)/(C.a + C.b)),
            ]
            selected = variants[variants_scores.index(max(variants_scores))]
            # selected = A if ucb_score_A > ucb_score_B else B
            selected.update(selected.simulate())
        
        # Return data at intervals
        if i+1 in [10, 20, 50, 100, 200, 500, 1000, 5000, 10000]:
            data = {
                'N': i+1,
                'A':{'a':A.a, 'b' : A.b },
                'B':{'a':B.a, 'b' : B.b },
                'C':{'a':C.a, 'b' : C.b }
            }
            y_A = list(scipy.stats.beta.pdf(x_vals, A.a, A.b))
            y_B = list(scipy.stats.beta.pdf(x_vals, B.a, B.b))
            y_C = list(scipy.stats.beta.pdf(x_vals, C.a, C.b))
            data['xy_A'] = list(zip(x_vals, y_A))
            data['xy_B'] = list(zip(x_vals, y_B))
            data['xy_C'] = list(zip(x_vals, y_C))
            data['x_vals'] = x_vals
            data['max_y'] = max([max(y_A), max(y_B), max(y_C)])
            dataset.append(data)

    return dataset

def sim_page_visits(campaign, conversion_rates={}, n=1, eps=0.1, algo='thompson'):

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