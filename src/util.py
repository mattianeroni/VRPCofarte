import node
import edge

import random
import numpy as np
import itertools
import math


# Names of the file where the benchmark problems are written
benchmarks = (
     "A-n32-k5_input_nodes.txt",
     "A-n38-k5_input_nodes.txt",
     "A-n45-k7_input_nodes.txt",
     "A-n55-k9_input_nodes.txt",
     "A-n60-k9_input_nodes.txt",
     "A-n61-k9_input_nodes.txt",
     "A-n65-k9_input_nodes.txt",
    "A-n80-k10_input_nodes.txt",
     "B-n50-k7_input_nodes.txt",
     "B-n52-k7_input_nodes.txt",
     "B-n57-k9_input_nodes.txt",
    "B-n78-k10_input_nodes.txt",
     "E-n22-k4_input_nodes.txt",
     "E-n30-k3_input_nodes.txt",
     "E-n33-k4_input_nodes.txt",
     "E-n51-k5_input_nodes.txt",
    "E-n76-k10_input_nodes.txt",
    "E-n76-k14_input_nodes.txt",
     "E-n76-k7_input_nodes.txt",
    "F-n135-k7_input_nodes.txt",
     "F-n45-k4_input_nodes.txt",
     "F-n72-k4_input_nodes.txt",
   "M-n101-k10_input_nodes.txt",
    "M-n121-k7_input_nodes.txt",
    "P-n101-k4_input_nodes.txt",
     "P-n22-k8_input_nodes.txt",
     "P-n40-k5_input_nodes.txt",
    "P-n50-k10_input_nodes.txt",
    "P-n55-k15_input_nodes.txt",
    "P-n65-k10_input_nodes.txt",
    "P-n70-k10_input_nodes.txt",
     "P-n76-k4_input_nodes.txt",
     "P-n76-k5_input_nodes.txt"
)


def readfile (filename : str, path : str = "../data/" ):
    """
    This method might be used to read a specific file and translate the data in a
    tuple of Nodes easy-to-manage by the algorithm.

    We use tuple instead of List for reason of performance. Tuple are immutable
    and passed by value, this makes them high-performant.


    :param filename: The name of the file to read.
    :param path: The directory where the file is.
    :return: A tuple of nodes

    """
    nodes = list()
    with open(path + filename) as file:
        # Split each line in tokens
        rows = [" ".join(line.split()).split(" ") for line in file]
        # Calculate the total number of products sold during this tour
        total_demand = sum(int(tokens[2]) for tokens in rows)

        # Build the nodes intances
        for i, tokens in enumerate(rows):
            nodes.append(node.Node (i,
                                    x = int(float(tokens[0])),
                                    y = int(float(tokens[1])),
                                    open = float(tokens[3]),
                                    close = float(tokens[4]),
                                    demand = int(tokens[2]),
                                    importance = int(tokens[2]) / total_demand
                                 ))
    return tuple(nodes)






def build_edges (nodes, pvariance = 0.25):
    """
    Given the set of nodes that constitute the problem, this method construct the
    edges connecting the nodes to each other and each node to the depot.

    :param nodes: The nodes of the problem.
    :return: The edges connecting the nodes sorted by savings

    """
    # Node 0 is the depot
    depot = nodes[0]

    for node in nodes[1:]:
        # Calculate the distance from the depot calling the __sub__ operator
        distance_from_depot = node - depot
        variance = math.pow(pvariance * distance_from_depot, 2)
        # Make the edges connecting the node to the depot
        dn_edge = edge.Edge(depot, node, deterministic_travel_time = distance_from_depot, variance=variance)
        nd_edge = edge.Edge(node, depot, deterministic_travel_time = distance_from_depot, variance=variance)
        # Set the inverse edges
        dn_edge.inverse = nd_edge
        nd_edge.inverse = dn_edge
        # save in node a reference to the (depot, node) edge (arc)
        node.dn_edge = dn_edge
        node.nd_edge = nd_edge
        
    edges = list()
    for inode, jnode in itertools.combinations(nodes[1:], 2):
        # Compute euclidean distance between nodes
        distance = inode - jnode
        variance = math.pow(pvariance * distance, 2)
        # Instantiate edges
        ijEdge = edge.Edge(inode, jnode, deterministic_travel_time=distance, variance=variance)
        jiEdge = edge.Edge(jnode, inode, deterministic_travel_time=distance, variance=variance)
        # make the inverse
        ijEdge.inverse = jiEdge
        jiEdge.inverse = ijEdge
        # Compute the savings according to Clark-Wright Saving algorithm
        saving = inode.nd_edge.deterministic_travel_time + jnode.dn_edge.deterministic_travel_time - distance
        ijEdge.saving = saving
        jiEdge.saving = saving

        # Just one edge is included in the savings list
        edges.append (ijEdge)

    return tuple(sorted(edges, key=lambda i: i.saving, reverse=True))






def build_time_windows (*, filename, path = "../data/", n_vehicles = 5, time_window = 100):
    """
    This method build the time windows.

    """
    def getCost (nodes_list, distances):
        ids_list = np.array([0] + [n.ID for n in nodes_list])
        return (distances[ids_list, np.roll(ids_list, -1)]).sum()

    # Read nodes without time windows
    nodes = list()
    with open(path + filename) as file:
        # Split each line in tokens
        rows = [" ".join(line.split()).split(" ") for line in file]
        # Calculate the total number of products sold during this tour
        total_demand = sum (int(tokens[2]) for tokens in rows)

        # Build the nodes intances
        for i, tokens in enumerate(rows):
            nodes.append(node.Node (i,
                                    x = int(float(tokens[0])),
                                    y = int(float(tokens[1])),
                                    demand = int(tokens[2]),
                                    importance = int(tokens[2]) / total_demand
                                 ))
    #nodes = tuple(nodes)
    dists = np.array([[n - m  for m in nodes] for n in nodes])


    # Shuffle nodes and split them in a number of clusters equal to
    # the number of vehicles.
    nodes_no_depot = nodes[1:] # Exclude the depot
    random.shuffle(nodes_no_depot)
    routes = np.array_split(nodes_no_depot, n_vehicles)

    # Optimize each random route using a 2-OPT
    for r in range(len(routes)):
        csol = list(routes[r])
        
        ccost = getCost(csol, dists)
        cut_points = tuple(i for i in itertools.combinations(range(len(csol)) , 2))
        i = 0
        while i < len(cut_points):
            a, b = cut_points[i]
            newSol = csol[:a] + list(reversed(csol[a:b])) + csol[b:]
            newCost = getCost(newSol, dists)

            if newCost < ccost:
                csol, ccost = newSol, newCost
                i = -1
            i += 1
        
        # For each node, look at the arrival time, and define the time window
        # around that time.
        arrival = 0
        current_node = 0
        for n in csol:
            arrival += dists[current_node, n.ID]
            n.open = max( arrival - time_window // 2, 0 )
            n.close = arrival + time_window // 2
            current_node = n.ID



    # Overwrite the text files
    nodes[0].close = float("inf")
    with open (path + filename, "w") as file:
        for i, n in enumerate(nodes):
            file.write(f"{n.x}  {n.y}  {n.demand}  {n.open}  {n.close}\n")
