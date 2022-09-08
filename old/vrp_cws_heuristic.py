""" CLARKE & WRIGHT SAVINGS HEURISTIC FOR THE VEHICLE ROUTING PROBLEM (VRP) """

import networkx as nx
import matplotlib.pyplot as plt
import random

from routing_objects import Node, Edge, Route, Solution
import math
import operator


""" Read instance data from txt file """

vehCap = 100.0 # update vehicle capacity for each instance
instanceName = 'A-n80-k10' # name of the instance
# txt file with the VRP instance data for each node (x, y, demand)
fileName = 'data/' + instanceName + '_input_nodes.txt' 


with open(fileName) as instance:
    i = 0
    nodes = []
    for line in instance: 
        # array data with node data: x, y, demand
        data = [float(x) for x in line.split()]
        aNode = Node(i, data[0], data[1], data[2])
        nodes.append(aNode)
        i += 1


""" Construct edges with costs and savings list from nodes """

depot = nodes[0] # node 0 is the depot

for node in nodes[1:]: # excludes the depot
    dnEdge = Edge(depot, node) # creates the (depot, node) edge (arc)
    ndEdge = Edge(node, depot) 
    dnEdge.invEdge = ndEdge # sets the inverse edge (arc)
    ndEdge.invEdge = dnEdge
    # compute the Euclidean distance as cost
    dnEdge.cost = math.sqrt((node.x - depot.x)**2 + (node.y - depot.y)**2)
    ndEdge.cost = dnEdge.cost # assume symmetric costs 
    # save in node a reference to the (depot, node) edge (arc)
    node.dnEdge = dnEdge
    node.ndEdge = ndEdge

savingsList = []
for i in range(1, len(nodes) - 1): # excludes the depot
    iNode = nodes[i]
    for j in range(i + 1, len(nodes)):
        jNode = nodes[j]
        ijEdge = Edge(iNode, jNode) # creates the (i, j) edge
        jiEdge = Edge(jNode, iNode) 
        ijEdge.invEdge = jiEdge # sets the inverse edge (arc)
        jiEdge.invEdge = ijEdge
        # compute the Euclidean distance as cost
        ijEdge.cost = math.sqrt((jNode.x - iNode.x)**2 + (jNode.y - iNode.y)**2)
        jiEdge.cost = ijEdge.cost # assume symmetric costs
        # compute savings as proposed by Clark % Wright
        ijEdge.savings = iNode.ndEdge.cost + jNode.dnEdge.cost - ijEdge.cost
        jiEdge.savings = ijEdge.savings
        # save one edge in the savings list
        savingsList.append(ijEdge)
        # sort the list of edges from higher to lower savings
        savingsList.sort(key = operator.attrgetter("savings"), reverse = True)


""" Construct the dummy solution """

sol = Solution()
for node in nodes[1:]: # excludes the depot
    dnEdge = node.dnEdge # get the (depot, node) edge
    ndEdge = node.ndEdge
    dndRoute = Route() # construct the route (depot, node, depot)
    dndRoute.edges.append(dnEdge)
    dndRoute.demand += node.demand
    dndRoute.cost += dnEdge.cost
    dndRoute.edges.append(ndEdge)
    dndRoute.cost += ndEdge.cost
    node.inRoute = dndRoute # save in node a reference to its current route
    node.isInterior = False # this node is currently exterior (connected to depot)
    sol.routes.append(dndRoute) # add this route to the solution
    sol.cost += dndRoute.cost
    sol.demand += dndRoute.demand


""" Perform the edge-selection & routing-merging iterative process """

def checkMergingConditions(iNode, jNode, iRoute, jRoute):
    # condition 1: iRoute and jRoure are not the same route object
    if iRoute == jRoute: return False
    # condition 2: both nodes are exterior nodes in their respective routes
    if iNode.isInterior == True or jNode.isInterior == True: return False
    # condition 3: demand after merging can be covered by a single vehicle
    if vehCap < iRoute.demand + jRoute.demand: return False
    # else, merging is feasible
    return True    


def getDepotEdge(aRoute, aNode):
    ''' returns the edge in aRoute that contains aNode and the depot 
      (it will be the first or the last one) '''
    # check if first edge in aRoute contains aNode and depot
    origin = aRoute.edges[0].origin
    end = aRoute.edges[0].end
    if ((origin == aNode and end == depot) or
        (origin == depot and end == aNode)):
            return aRoute.edges[0]
    else: # return last edge in aRoute
        return aRoute.edges[-1]


while len(savingsList) > 0: # list is not empty
    ijEdge = savingsList.pop(0) # select the next edge from the list
    # determine the nodes i < j that define the edge
    iNode = ijEdge.origin
    jNode = ijEdge.end
    # determine the routes associated with each node
    iRoute = iNode.inRoute
    jRoute = jNode.inRoute
    # check if merge is possible
    isMergeFeasible = checkMergingConditions(iNode, jNode, iRoute, jRoute)
    # if all necessary conditions are satisfied, merge
    if isMergeFeasible == True:
        # iRoute will contain either edge (depot, i) or edge (i, depot)
        iEdge = getDepotEdge(iRoute, iNode) # iEdge is either (0,i) or (i,0)
        # remove iEdge from iRoute and update iRoute cost
        iRoute.edges.remove(iEdge)
        iRoute.cost -= iEdge.cost
        # if there are multiple edges in iRoute, then i will be interior
        if len(iRoute.edges) > 1: iNode.isInterior = True
        # if new iRoute does not start at 0 it must be reversed
        if iRoute.edges[0].origin != depot: iRoute.reverse()
        # jRoute will contain either edge (depot, j) or edge (j, depot)
        jEdge = getDepotEdge(jRoute, jNode) # jEdge is either (0,j) or (j,0)
        # remove jEdge from jRoute and update jRoute cost
        jRoute.edges.remove(jEdge)
        jRoute.cost -= jEdge.cost
        # if there are multiple edges in jRute, then j will be interior
        if len(jRoute.edges) > 1: jNode.isInterior = True
        # if new jRoute starts at 0 it must be reversed
        if jRoute.edges[0].origin == depot: jRoute.reverse()
        # add ijEdge to iRoute
        iRoute.edges.append(ijEdge)
        iRoute.cost += ijEdge.cost
        iRoute.demand += jNode.demand
        jNode.inRoute = iRoute
        # add jRoute to new iRoute
        for edge in jRoute.edges:
            iRoute.edges.append(edge)
            iRoute.cost += edge.cost
            iRoute.demand += edge.end.demand
            edge.end.inRoute = iRoute
        # delete jRoute from emerging solution
        sol.cost -= ijEdge.savings
        sol.routes.remove(jRoute)

print('Instance: ', instanceName)        
print('Cost of C&W savings sol =', "{:.{}f}".format(sol.cost, 2))    
for route in sol.routes:
    s = str(0)
    for edge in route.edges:
        s = s + '-' + str(edge.end.ID)
    print('Route: ' + s + ' || cost = ' + "{:.{}f}".format(route.cost, 2))
    
    
# Plot the solution

#G = nx.Graph()
#for route in sol.routes:
#    for edge in route.edges:
#        G.add_edge(edge.origin.ID, edge.end.ID)
#        G.add_node(edge.end.ID, coord=(edge.end.x, edge.end.y))
#coord = nx.get_node_attributes(G, 'coord')
#nx.draw_networkx(G, coord)

# Plot (enhanced) the solution

G = nx.Graph()
fnode = sol.routes[0].edges[0].origin
G.add_node(fnode.ID, coord=(fnode.x,fnode.y))
coord = nx.get_node_attributes(G,'coord')    
fig, ax = plt.subplots() #Add axes
nx.draw_networkx_nodes(G, coord, node_size = 60, node_color='white', ax = ax)
nx.draw_networkx_labels(G, coord)

j=0
for route in sol.routes:
    #Assign random colors in RGB
    c1 = int(random.uniform(0, 255)) if (j%3 == 2) else (j%3)*int(random.uniform(0, 255))
    c2 = int(random.uniform(0, 255)) if ((j+1)%3 == 2) else ((j+1)%3)*int(random.uniform(0, 255))
    c3 = int(random.uniform(0, 255)) if ((j+2)%3 == 2) else ((j+2)%3)*int(random.uniform(0, 255))
    for edge in route.edges:
        G.add_edge(edge.origin.ID, edge.end.ID)
        G.add_node(edge.end.ID, coord=(edge.end.x, edge.end.y))
        coord = nx.get_node_attributes(G,'coord')   
        nx.draw_networkx_nodes(G, coord, node_size = 60, node_color='white', ax = ax)
        nx.draw_networkx_edges(G, coord, edge_color='#%02x%02x%02x' % (c1, c2, c3))
        nx.draw_networkx_labels(G, coord, font_size = 9)
        G.remove_node(edge.origin.ID)
    j += 1

limits=plt.axis('on') #Turn on axes
ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)

        
        
        
    
    
    
        
        
    
    
