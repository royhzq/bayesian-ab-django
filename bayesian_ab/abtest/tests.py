from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase, RequestFactory
from .models import Campaign, Variant
from .simulation import experiment
from .utils import (epsilon_greedy, thompson_sampling, UCB1,
                    h, loss, ab_assign, sim_page_visits)

class AlgorithmTests(TestCase):

    ''' Unit tests for multi-armed bandit algorithms
    - Epsilon-Greedy
    - Thompson Sampling
    - UCB1 
    '''
    variant_vals = {}

    def setUp(self):

        campaign, created = Campaign.objects.get_or_create(
            name="Test Homepage",
            description="Testing Homepage designs"    
        )
        for code in ['A', 'B', 'C']:
            variant, created = Variant.objects.get_or_create(
                campaign=campaign,
                code=code,
                name=f'Homepage Design {code}',
                html_template=f'abtest/homepage_{code}.html'
            )

        self.variant_vals = campaign.variants.all().values(
            'code',
            "impressions",
            'conversions',
            'conversion_rate',
            'html_template',
        )

    def test_epsilon_greedy(self):

        selected_variant = epsilon_greedy(self.variant_vals, eps=0.1)

        self.assertTrue(selected_variant in list(self.variant_vals))

    def test_thompson_sampling(self):

        selected_variant = thompson_sampling(self.variant_vals)
        
        self.assertTrue(selected_variant in list(self.variant_vals))

    def test_ucb1(self):

        selected_variant = UCB1(self.variant_vals)
        
        self.assertTrue(selected_variant in list(self.variant_vals))

class DecicsionRuleTest(TestCase):
    
    ''' 
    Test function for evaluation rules P(X>Y) and loss(X,Y)
    Where:
        X ~ Beta(a,b)
        Y ~ Beta(c,d)
    '''
    def test_h_1(self):

        self.assertEqual(h(1,1,1,1), 0.5)

    def test_h_2(self):

        self.assertEqual(h(99,123,23,36), 0.784752290600683)

    def test_loss_1(self):

        self.assertEqual(loss(1,1,1,1), 0.16666666666666669)

    def test_loss_2(self):

        self.assertEqual(loss(23,36,78,120), 0.026744171285783824)

class ABAssignmentTest(TestCase):
    '''
    Test cases for assigning variants to request made.
    '''
    request_factory = RequestFactory()
    request = request_factory.get('/')
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()
    
    campaign = None
    variant_vals = {}

    def setUp(self):

        self.campaign, created = Campaign.objects.get_or_create(
            name="Test Homepage",
            description="Testing Homepage designs"    
        )
        for code in ['A', 'B', 'C']:
            variant, created = Variant.objects.get_or_create(
                campaign=self.campaign,
                code=code,
                name=f'Homepage Design {code}',
                html_template=f'abtest/homepage_{code}.html'
            )

        self.variant_vals = self.campaign.variants.all().values(
            'code',
            "impressions",
            'conversions',
            'conversion_rate',
            'html_template',
        )

    def test_ab_assign_session(self):
        # Test to check if session variable is added to WSGI requests object
        selected_variant = ab_assign(
            self.request, 
            self.campaign, 
            default_template='/abtest/homepage.html', 
        )
        self.assertTrue(self.request.session.get(str(self.campaign.code)))

    def test_ab_assign_epsilon_greedy(self):
        # Test assign with epsilon greedy algorithm
        selected_variant = ab_assign(
            self.request, 
            self.campaign, 
            algo='egreedy',
            default_template='/abtest/homepage.html', 
        )
        self.assertTrue(selected_variant in list(self.variant_vals))

    def test_ab_assign_thompson(self):
        # Test assign with epsilon thompson sampling algorithm
        selected_variant = ab_assign(
            self.request, 
            self.campaign, 
            algo='thompson',
            default_template='/abtest/homepage.html', 
        )
        self.assertTrue(selected_variant in list(self.variant_vals))

    def test_ab_assign_ucb1(self):
        # Test assign with ucb1 algorithm
        selected_variant = ab_assign(
            self.request, 
            self.campaign, 
            algo='UCB1',
            default_template='/abtest/homepage.html', 
        )
        self.assertTrue(selected_variant in list(self.variant_vals))

    def test_ab_assign_uniform(self):
        # Test assign with uniform random sampling algorithm
        selected_variant = ab_assign(
            self.request, 
            self.campaign, 
            algo='uniform',
            default_template='/abtest/homepage.html', 
        )
        self.assertTrue(selected_variant in list(self.variant_vals))

class SimulationTests(TestCase):

    ''' Test cases for simulation-related functions
    '''
    campaign = None
    variant_vals = {}

    def setUp(self):

        self.campaign, created = Campaign.objects.get_or_create(
            name="Test Homepage",
            description="Testing Homepage designs"    
        )
        for code in ['A', 'B', 'C']:
            variant, created = Variant.objects.get_or_create(
                campaign=self.campaign,
                code=code,
                name=f'Homepage Design {code}',
                html_template=f'abtest/homepage_{code}.html'
            )

        self.variant_vals = self.campaign.variants.all().values(
            'code',
            "impressions",
            'conversions',
            'conversion_rate',
            'html_template',
        )

    def test_sim_page_visits_1(self):
        # Test sim_page_visits function
        # With no conversion_rates provided
        all_simulated = True
        for algo in ['thompson', 'egreedy', 'UCB1', 'uniform']:
    
            simulated = sim_page_visits(
                campaign=self.campaign,
                conversion_rates = {
                    'A' : 0.5,
                    'B' : 0.6,
                    'C' : 0.7
                },
                n=100,
                algo=algo
            )
            if not simulated:
                all_simulated = False

        self.assertTrue(all_simulated)

    def test_sim_page_visits_2(self):
        # Test sim_page_visits function
        # With conversion_rates provided
        all_simulated = True
        for algo in ['thompson', 'egreedy', 'UCB1', 'uniform']:
    
            simulated = sim_page_visits(
                campaign=self.campaign,
                n=100,
                algo=algo,
                conversion_rates={
                    'A':0.1,
                    'B':0.8,
                    'C':0.43,
                }
            )
            if not simulated:
                all_simulated = False

        self.assertTrue(all_simulated)

    def test_experiment_1(self):
        # Test experiment function for simulating 2 variant A/B test
        # Test for all algorithms
        all_simulated = True
        for algo in ['thompson', 'egreedy', 'UCB1', 'uniform']:
            dataset = experiment(
                p1=0.5,
                p2=0.55,
                p3=0.66,
                N=10000,
            )
        self.assertTrue(dataset)