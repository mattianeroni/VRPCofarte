import itertools
import numpy as np

import edge
import global_methods



class MergeError (Exception):
    """
    This Exception is raised if a merging operation is required without preparing
    the routes.
    When merging two routes with an edge, the last node of the first route
    (except for the depot) must be the origin of the edge, and the first node
    of the second route (except for the depot) must be the destination of the edge.

    """
    pass





class Route (object):
    """
    An instance of this class represents a route made by a vehicle.
    It is represented as a set of edges.

    """
    def __init__(self, edges):
        """
        Constructor.

        :param edges: The edges that constitute the route.
        :param travel_time: The total travel time of the route.
        :param delay: The aggregated delay on the route.
        :param delayCost: The delay cost of the route.

        """
        self.edges = edges
        self.travel_time = 0
        self._deterministic_cost = 0.0
        self._stochastic_cost = 0.0
        self.evaluated = False
        self.simulated = False
        
        
    @property
    def deterministic_cost (self):
        if not self.evaluated:
            raise Exception("Route not evaluated.")
        return self._deterministic_cost
    
    
    @property
    def stochastic_cost (self):
        if not self.simulated:
            raise Exception("Route not simulated.")
        return self._stochastic_cost
        
    
    def evaluate (self):
        """
        Deterministic evaluation of the route.
        
        """
        self.evaluated = True
        self.travel_time, self._deterministic_cost = global_methods.evaluate(self.edges)
        return self.travel_time, self._deterministic_cost
    
    
    def simulate (self, maxiter, max_travel_time):
        """
        Stochastic simulation of the route.
        
        """
        self.simulated = True
        self._stochastic_cost = global_methods.simulate(tuple(self.edges), maxiter, max_travel_time)
        return self._stochastic_cost
    

    def __len__ (self):
        """
        Overwrite the __len__ operator to provide a faster information concerning
        the length of the Route.

        :return: The number of edges that make the route.

        """
        return len(self.edges)


    def __repr__ (self):
        """
        Provides a readable representation of the route, e.g., [(0,1), (1,3), (3,2), (2,6), (6,0)]

        """
        return "".join([f"({e.origin.ID},{e.end.ID})" for e in self.edges])


    def merge (self, route, by):
        """
        This method merge this route IN PLACE with an other route.
        The lists of edges are joint, the costs of the routes are summed, and
        the demand satisfied by the routes in summed as well.

        :param route: The other route. (Remember to delete it later)
        :param by: The Edge used to connect the two routes.

        """
        # Check that the preparation to the merging has been made.
        if by.origin != self.edges[-1].origin or by.end != route.edges[0].end:
            raise MergeError (f"The routes {self} and {route} have not been correctly prepared for merging with edge {by}.")

        # Adjust the edges concerning the first route.
        self.travel_time -= self.edges[-1].deterministic_travel_time
        self.edges.pop(-1)
        iNode = by.origin
        if len(self.edges) > 1:
            iNode.interior = True

        # Adjust the edges concerning the second route
        route.edges.pop(0)
        jNode = by.end
        if len(route.edges) > 1:
            jNode.interior = True

        # Update list of edges and demand (for the moment the cost too)
        self.travel_time, self._deterministic_cost = global_methods.evaluate(itertools.chain([by], route.edges), self.travel_time, self._deterministic_cost)
        self.edges.extend(list(itertools.chain([by], route.edges)))

        # Change the reference to the route in the nodes
        by.end.route = self
        for edge in route.edges[:-1]:
            edge.end.route = self



    def reverse(self):
        """
        This method reverses in place the current Route,
        e.g., [(0,2), (2,6), (6,4), (4,0)]  becomes  [(0,4), (4,6), (6,2), (2,0)].

        """
        self.edges = list(reversed([edge.inverse for edge in self.edges]))
        if self.__len__() > 2:
            self.travel_time, self._deterministic_cost = global_methods.evaluate(self.edges)
