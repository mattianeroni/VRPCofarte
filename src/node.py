
class Node (object):
    """
    An instance of this class represents a Node of the graph, which represents a
    customer to be visited by the vehicles.

    """

    def __init__(self, ID, x, y, open=0, close=0, demand=0, importance=0 ):
        """
        Constructor.

        :param ID: The uniwue id of the node.
        :param x: The x coordinate of the node in space.
        :param y: The y coordinate of the node in space.
        :param open: The opening time of the node.
        :param close: The closing time of the node.
        :param demand: The quantity of products sold to that customer.
        :param importance: The importance of the customer.
        
        :attr route: The route the node belongs to.
        :attr interior: True if the node is interior in the current route.
        :attr dn_edge: Edge connecting the depot to the node.
        :attr nd_edge: Edge connecting the node to the depot.

        """
        self.ID = ID
        self.x = x
        self.y = y
        self.open = open
        self.close = close
        self.demand = demand
        self.importance = importance

        self.route = None 
        self.interior = False                 

        self.dn_edge = None
        self.nd_edge = None
        
        
    def __repr__(self):
        return f"(id : {self.ID}, x : {self.x}, y : {self.y}, open : {self.open}, close : {self.close})"



    def __sub__ (self, other):
        """
        This method returns the euclidean distance between two nodes.
        It might be used using the "-" (minus) operator.

        """
        return int(((self.x - other.x)**2 + (self.y - other.y)**2)**0.5)
