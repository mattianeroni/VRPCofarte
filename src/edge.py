import random
import math
import numpy as np


class Edge (object):
    """
    An instance of this class represents an edge of the graph, and it might
    be representative of a road connecting two customers.

    For the moment, we consider the edges as direct arcs (i.e., the edge connecting
    node A to node B is different by the edge connecting node B to node A).

    """

    def __init__(self, origin, end, deterministic_travel_time, variance):

        self.origin = origin 
        self.end = end
        
        self.deterministic_travel_time = deterministic_travel_time
        self.variance = variance

        self.saving = 0  
        self.inverse = None


    def __repr__ (self):
        return f"({self.origin.ID},{self.end.ID})"
    
    
    @staticmethod
    def _rand_lognormal (mean, variance):
        if mean == 0:
            return 0
        
        phi = math.sqrt(variance + mean**2)
        mu = math.log((mean**2) / phi)
        sigma = math.sqrt(math.log((phi**2) / (mean**2)))
        
        return np.random.lognormal(mean=mu, sigma=sigma)


    
    @property
    def stochastic_travel_time (self):
        """
        This method returns a stochastic cost/travel-time.
        
        NOTE: This is not a proper lognormal distribution, with the average 
        and standard deviation givens. This is a lognormal distribution where
        the mode corresponds to the <mu> given.
        
        """
        return self._rand_lognormal(self.deterministic_travel_time, self.variance)
