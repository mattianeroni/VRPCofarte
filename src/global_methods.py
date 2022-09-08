import numpy as np
import collections
import functools
import statistics

_intercept = 5.42
_coef = np.array([0.98, 452.25])


@functools.lru_cache(maxsize=126)
def predict (delay, importance):
    return _intercept + np.dot(_coef, np.array([delay,importance])) if delay > 0 else 0



def evaluate (edges, current_travel_time=0, current_delay_cost=0.0):
    travel_time, delay_cost = current_travel_time, current_delay_cost
    for e in iter(edges):
        node = e.end
        travel_time += e.deterministic_travel_time
        delay = max(travel_time - node.close, 0)
        delay_cost += predict(delay, node.importance)

    return travel_time, delay_cost




def simulate (edges, maxiter, max_travel_time):
    results = collections.deque()
    append = results.append
    
    for i in range(maxiter):
        travel_time, delay_cost = 0, 0.0
        for e in iter(edges):
            node = e.end
            travel_time += e.stochastic_travel_time
            if travel_time > max_travel_time:
                break
            
            delay = max(travel_time - node.close, 0)
            delay_cost += predict(delay, node.importance)

        else:
            append(delay_cost)
    return statistics.mean(results)
