""" The simulation module is independent from the rest of the application.
Used mainly to simulate a three variant Bayesian A/B/C Test abd to generate
the XY values for plotting the Beta distribution curves at regular checkpoints
of the simulation. See ``experiment`` function below.
"""

import random
import numpy as np
import scipy.stats

class SimVariant:
    """Summary line.

    Extended description of function.

    Args:
        arg1 (int): Description of arg1
        arg2 (str): Description of arg2

    Returns:
        bool: Description of return value

    """
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


def experiment(p1, p2, p3, N=10000, algo="uniform", eps=0.2  ):
    
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