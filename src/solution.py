
class Solution (object):

    def __init__ (self, routes):
        self.routes = routes

        self.simulated = False
        self.evaluated = False

        self._deterministic_cost = 0.0
        self._stochastic_cost = 0.0
        self._reliability = 0.0


    def __hash__(self):
        return hash(str(self))


    def __repr__(self):
        return f"({self._deterministic_cost}, {self._stochastic_cost})"


    def __lt__(self, other):
        if self.simulated and other.simulated:
            return self._stochastic_cost < other.stochastic_cost

        if self.evaluated and other.evaluated:
            return self._deterministic_cost < other.deterministic_cost

        raise Exception("Solution not comparable.")


    def __gt__(self, other):
        if self.simulated and other.simulated:
            return self._stochastic_cost > other.stochastic_cost

        if self.evaluated and other.evaluated:
            return self._deterministic_cost > other.deterministic_cost

        raise Exception("Solution not comparable.")



    @property
    def deterministic_cost (self):
        if self.evaluated:
            return self._deterministic_cost
        raise Exception("Solution not evaluated.")
        


    @property
    def stochastic_cost (self):
        if self.simulated:
            return self._stochastic_cost
        raise Exception("Solution not simulated.")


    @property
    def reliability (self):
        if self.simulated:
            return self._reliability
        raise Exception("Solution not simulated.")
        


    def evaluate (self):
        self.evaluated = True
        if not all(r.evaluated for r in self.routes):
            for r in self.route:
                if not r.evaluated:
                    r.evaluate()

        self._deterministic_cost = sum(r.deterministic_cost for r in self.routes)
        return self._deterministic_cost


    def simulate (self, maxiter, max_travel_time):
        self.simulated = True
        self._stochastic_cost = sum(route.simulate(maxiter, max_travel_time) for route in self.routes)
        return self._stochastic_cost
