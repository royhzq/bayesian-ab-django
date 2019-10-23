""" The simulation module is independent from the rest of the application.
Used mainly to simulate a three variant Bayesian A/B/C Test abd to generate
the XY values for plotting the Beta distribution curves at regular checkpoints
of the simulation. See ``experiment`` function below.
"""

import random
import numpy as np
import scipy.stats

class SimVariant:
    """ Simple variant object for simulating A/B test.
    """
    def __init__(self, p):
        """
        Parameters
        ----------
        p : float
            The 'true' probability of converting. I.e., 
            the probability that a user visiting this variant will 
            generate a conversion. 0 < p < 1

        a : int
            Number of conversions + 1, or the alpha parameter for a beta 
            distribution. a >= 1

        b : int
            Number of impressions - conversions -1, or the beta parameter
            for a beta distribution. b >= 1

        """
        self.p = p
        self.a = 1
        self.b = 1

    def simulate(self):
        """
        Returns
        -------
        int
            1 or 0. Returns 1 with a probability ``p``
            and 0 with probability 1 - ``p``.
        """
        return random.random() < self.p

    def sample(self):
        """ 
        Returns
        -------
        float
            Sample value drawn from a beta distribution X 
            where X ~ Beta( ``a`` , ``b`` ).
        """
        return np.random.beta(self.a, self.b)

    def update(self, x):
        """ Function to update ``a`` and ``b`` parameters
        of the beta distribution for the SimVariant instance

        Parameters
        ----------
        x : int
            1 if instance is updated with conversion.
            I.e. ``a`` increment by 1
            0 if instance is updated with no converion.
            I.e., ``b`` increment by 1    
        """
        self.a += x
        self.b += 1-x


def experiment(p1, p2, p3, N=10000, algo="thompson", eps=0.2  ):
    """ Main function to simulate a bayesian A/B/C test with 
    given ``N`` number of page visits.
    
    Parameters
    ----------
    p1 : float
        0 < p1 < 1. 'true' conversion rate. The probability that
        a user visiting variant A will generate a conversion.
    p2 : float
        0 < p2 < 1. 'true' conversion rate. The probability that
        a user visiting variant B will generate a conversion.
    p3 : float
        0 < p3 < 1. 'true' conversion rate. The probability that
        a user visiting variant C will generate a conversion.
    N : int, optional
        The number of page visits (user requests) to simulate.
        Defaults to 10000
    algo : str, optional
        Choice of explore-exploit algorithms to determine the assignment
        of variant to the user / request. The choice of algorithms are:
        
            * *thompson* : Thompson sampling algorithm
            * *UCB1* : Upper Confidence Bound algorithm
            * *uniform* : Uniformly random sampling of variants
            * *egreedy* : Epsilon-Greedy algorithm with exploration parameter determined by ``eps`` parameter

        Defaults to *thompson*.
    eps : float, optional
        Exploration parameter for the epsilon-greedy ``egreedy`` algorithm. 
        Only applicable to ``egreedy`` algorithm option. Defaults to 0.1

    Returns
    -------
    :obj:`list` of ``dict``
        Returns a list of dictionary elements where each element contains
        the beta distribution parameter values and (x,y) values for plotting
        of the beta distribution curve for each variant at various 
        checkpoints in the simulation (i.e., when N=0, N=10, N=100, etc.)
        values returned. The key-value pairs returned are:

            * ``N`` : Number of visits simulated at the checkpoint.
            * ``A`` : Dict of alpha, beta parameters and their values in the form {'a':1,'b':1} for variant A
            * ``B`` : Dict of alpha, beta parameters and their values in the form {'a':1,'b':1} for variant B
            * ``C`` : Dict of alpha, beta parameters and their values in the form {'a':1,'b':1} for variant C
            * ``xy_A`` : List of tuples containing (x,y) coordinates of beta distribution curve for variant A
            * ``xy_B`` : List of tuples containing (x,y) coordinates of beta distribution curve for variant B
            * ``xy_C`` : List of tuples containing (x,y) coordinates of beta distribution curve for variant C
            * ``max_y`` : Max value generated from the beta PDFs across all variants. For plotting axes.

    Examples
    --------
    >>> experiment(
    ...     p1=0.3,
    ...     p2=0.5,
    ...     p3=0.7,
    ...     N=50,
    ...     algo='thompson',
    ... )
    [
        ...
        {
            'N':100,
            'A':{'a':5,'b':9},
            'B':{'a':2,'b':4},
            'C':{'a':59,'b':27},
            'xy_A': [[0,0],...],
            'xy_B': [[0,0],...],
            'xy_C': [[0,0],...],
            'max_y': 7.972833733909,
        }
        ...
    ]
    
    """

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
            selected.update(selected.simulate())
        
        # Append data at intervals
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