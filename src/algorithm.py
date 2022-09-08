import time
import math
import random
import numpy as np
import collections
import itertools

from solution import Solution
from route import Route

import global_methods


BETA_DETERMINISTIC = 0.9999999



class Simheuristic (object):

    def __init__ (self, 
                  nodes, 
                  edges, 
                  n_vehicles, 
                  max_travel_time, 
                  beta = (.1, .3), 
                  maxiter = 3000, 
                  n_elites = 5):
        """
        Constructor.

        :param nodes: The set of nodes.
        :param edges: The set of edges (arcs) connecting the nodes to each other.
        :param n_vehicles: The number of vehicles
        :param max_travel_time: The maximum travel time allowed for a single vehicle.
        :param beta: The min and max values for the parameter of the quasi-geometric distribution.
        :param maxiter: The number of iterations of the metaheuristic framework.
        :param n_elites: The elite solutions kept in memory.

        """
        self.nodes = nodes
        self.edges = edges

        self.n_vehicles = n_vehicles
        self.max_travel_time = max_travel_time
        self.gamma = 0.0
        self.beta = beta
        self.maxiter = maxiter
        self.n_elites = n_elites

        self.elites = collections.deque([], maxlen=n_elites)
        self.ctime = 0.0
        self.sbest = None
        self.dbest = None



    @staticmethod
    def prepare_merging(medge, route1, route2, gamma, max_travel_time):
        """
        This method checks if the merging of two routes is possible. Four main controls
        are made:
                 - The nodes of the edge must be in different routes.
                 - They must be exterior (i.e., connected to the depot).
                 - The travel time does not have to exceed the maximum allowed.
                 - The cumulated delay does not exceed gamma.


        :param medge: The (merging)-edge considered that might merge the routes.
        :param route1: The first route.
        :param route2: The second route.
        :param gamma: The maximum cumulated delay allowed to the routes.
        :param max_travel_time: The maximum travel time of the routes.

        :return:| (i)   The feasibility of the mearging, 
                | (ii)  The mearging edge (eventually reversed)
                | (iii) The two routes (eventually reversed)

        """
        # Condition 0: iRoute and jRoure are not the same route instance
        # NOTE: This condition is not mentioned in the paper, but it is obvious
        if route1 == route2:
            return False, medge, route1, route2

        # Condition 1: both nodes are exterior nodes in their respective routes
        iNode, jNode = medge.origin, medge.end
        if iNode.interior or jNode.interior:
            return False, medge, route1, route2

        # Condition 2: the travel time of the new route does not have to exceed the
        # maximum allowed travel time.
        if max_travel_time < route1.travel_time + route2.travel_time - medge.saving:
            return False, medge, route1, route2
        
        
        # Condition 3: the maximum delay cumulated by the new route cannot exceed a certain threshold (i.e., gamma).
        # For doing this control, both directions of the new route must be observed.
        iedges = tuple(route1.edges)
        iedges_inv = tuple(reversed([edge.inverse for edge in route1.edges]))
        jedges = tuple(route2.edges)
        jedges_inv = tuple(reversed([edge.inverse for edge in route2.edges]))

        if medge.origin == route1.edges[0].end:
            iedges, iedges_inv = iedges_inv, iedges
            
        if medge.end == route2.edges[-1].origin:
            jedges, jedges_inv = jedges_inv, jedges

        _, delay = global_methods.evaluate(itertools.chain(iedges[:-1], (medge,), jedges[1:]))
        _, delay_inv = global_methods.evaluate(itertools.chain(jedges_inv[:-1], (medge.inverse,), iedges_inv[1:]))
        
        if delay > gamma and delay_inv > gamma:
            return False, medge, route1, route2    # None of directions is feasible
        
        if delay <= delay_inv:
            if medge.origin == route1.edges[0].end:
                route1.reverse()
            if medge.end == route2.edges[-1].origin:
                route2.reverse()
            return True, medge, route1, route2
        else:
            if medge.inverse.origin == route2.edges[0].end:
                route2.reverse()
            if medge.inverse.end == route1.edges[-1].origin:
                route1.reverse()
            return True, medge.inverse, route2, route1



    @staticmethod
    def biased_random_selection (beta, list_size):
        """
        This method allows a biased randomised selection over a list.

        To each element of the list is assigned a certain probability to be
        selected, that depends on its position in list. The firt elements of
        the list have an higher probability to be selected.

        The probability is calculated using a quasi-geometric distribution:

                            f(x) = (1 - beta)^x

        where x is the position of the element in list, and beta is the parameter
        of the distribution.
        Note that for beta very close to one, the function always return the first
        element of the list reproducing a greedy behaviour, while, for beta closer
        to zero, the distribution approximates a uniform where all the elements
        have the same probability to be selected.

        :param beta: The parameter of the quasi-geometric distribution.
        :param list_size: The size of the list.

        :return: The position in list of the selected element.

        """
        return int(math.log(random.random(), 1 - beta)) % list_size





    def getSolution (self, gamma, max_travel_time, beta):
        """
        This method returns a new solution to the problem.
        For beta very close to one, the solution is deterministic, otherwise
        it is built using a biased randomised selection.

        :param beta: The parameter of the quasi-geometric distribution.
        :return: The new solution and an indicator of feasibility.

        """
        routes = []
        for n in self.nodes[1:]:
            r = Route([n.dn_edge,n.nd_edge])
            r.evaluate()
            routes.append(r)
            n.interior = False
            n.route = r

        prepare_merging = self.prepare_merging
        biased_random_selection = self.biased_random_selection
        prepare_merging = self.prepare_merging
        n_vehicles = self.n_vehicles

        # Iterative process for routes' merging
        savings_list = list(self.edges)

        for _ in range(len(self.edges)):
            edgeIndex = biased_random_selection(beta, len(savings_list))
            edge = savings_list.pop(edgeIndex)

            iRoute = edge.origin.route
            jRoute = edge.end.route
            
            feasible, merging_edge, froute, sroute = prepare_merging (edge, iRoute, jRoute, gamma, max_travel_time)
            if feasible:
                froute.merge (sroute, by=merging_edge)
                routes.remove (sroute)        
            
            if len(routes) <= n_vehicles:
                return True, Solution(tuple(routes))
        else:
            # if the algorithm has not been able to provide a feasible solution a non feasible solution is returned.
            return False, None

        

    def __call__ (self):
        feasible, self.gamma = False, -10.0
        while not feasible:
            self.gamma += 10.0
            feasible, starting_sol = self.getSolution(self.gamma, self.max_travel_time, BETA_DETERMINISTIC)

        starting_sol.evaluate()
        starting_sol.simulate(50, self.max_travel_time)        
        self.elites.append(starting_sol)
        sbest = starting_sol
        dbest = starting_sol

        # Move paramters and methods to the stack
        getSolution = self.getSolution
        beta_min, beta_max = self.beta
        gamma = self.gamma
        max_travel_time = self.max_travel_time
        append = self.elites.append

        # Set starting time
        start = time.time()

        for _ in range(self.maxiter):
            feasible, newSol = getSolution (gamma, max_travel_time, random.uniform(beta_min,beta_max))
            if feasible:
                new_deterministic_cost = newSol.evaluate()
                if new_deterministic_cost <= dbest.deterministic_cost:
                    dbest = newSol
                    newSol.simulate(50, max_travel_time)
                    if newSol.stochastic_cost <= sbest.stochastic_cost:
                        sbest = newSol
                        append(newSol)

        [sol.simulate(10_000, self.max_travel_time) for sol in iter(self.elites)]
        self.sbest = min(self.elites)
        self.dbest = dbest
        self.ctime = time.time() - start




    




class Heuristic (Simheuristic):

    def __init__ (self, *args, **kwargs):
        super(Heuristic, self).__init__(*args, **kwargs)


    def __call__(self):
        feasible, self.gamma = False, -10.0
        while not feasible:
            self.gamma += 10.0
            feasible, sol = self.getSolution(self.gamma, self.max_travel_time, BETA_DETERMINISTIC)

        sol.evaluate()
        self.dbest = sol






class BRA (Simheuristic):

    def __init__ (self, *args, **kwargs):
        super(BRA, self).__init__(*args, **kwargs)


    def __call__ (self):
        feasible, self.gamma = False, -10.0
        while not feasible:
            self.gamma += 10.0
            feasible, starting_sol = self.getSolution(self.gamma, self.max_travel_time, BETA_DETERMINISTIC)

        starting_sol.evaluate()
        self.dbest = starting_sol

        # Move parameters and methods to the stack
        getSolution = self.getSolution
        beta_min, beta_max = self.beta
        gamma = self.gamma
        max_travel_time = self.max_travel_time

        # Set starting time
        start = time.time()

        for _ in range(self.maxiter):

            feasible, newSol = getSolution (gamma, max_travel_time, random.uniform(beta_min,beta_max))

            if feasible:
                if newSol.evaluate() < self.dbest.deterministic_cost:
                    self.dbest = newSol

        self.ctime = time.time() - start
