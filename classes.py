import numpy as np
import pickle
import networkx as nx
from parameters import *


def create_initial_graph():
    """
    Creates n/family_size circles of family_size nodes each.
    Each node connects to exactly 2 others (a cycle graph of size family_size)
    """
    if N % family_size != 0:
        raise ValueError(f'N must be divisible by {family_size}.')
    G = nx.Graph()
    num_circles = N // family_size
    node_id = 0
    for _ in range(num_circles):
        circle_nodes = list(range(node_id, node_id + family_size))
        # Add the cycle edges
        for i in range(family_size):
            G.add_edge(circle_nodes[i], circle_nodes[(i + 1) % family_size])
        node_id += family_size
    return G

# Parameters l_max: max number of intermediate nodes
def count_simple_paths(g):
    """
    g: NetworkX Graph with n nodes (unweighted, undirected)
    l_max: maximum number of intermediate nodes
    
    Returns: list of graphs where graph k contains edge weights
             representing number of simple paths of length k+1 
             between any two nodes
    """
    
    # Initialize result counting graphs
    counting_graphs = [nx.empty_graph(N) for _ in range(l_max)]

    # Build adjacency list from NetworkX graph
    adj = [list(g.neighbors(i)) for i in range(N)]

    # DFS helper
    def dfs(start, current, length, visited, counting_graph):
        for neighbor in adj[current]:
            if not visited[neighbor]:
                if length > 1:
                    visited[neighbor] = True
                    dfs(start, neighbor, length-1, visited, counting_graph)
                    visited[neighbor] = False                    
                else:
                    if counting_graph.has_edge(start, neighbor):
                        counting_graph[start][neighbor]['weight'] += 1
                    else:
                        counting_graph.add_edge(start, neighbor, weight=1)

    # Main loop
    for start in range(N):
        visited = [False]*N
        visited[start] = True
        for path_len in range(2, l_max+2):
            dfs(start, start, path_len, visited, counting_graphs[path_len-2])
    res = []
    for x in counting_graphs:
        res.append(nx.to_numpy_array(x).astype(int)//2)
    return res

def create_affinity_graph():
    aff_matrix = np.zeros((N, N))
    # Generate integers 0, step, 2*step, ..., 100
    vals = np.arange(0, 101, affinity_step)
    for i in range(N):
        for j in range(i+1, N):
            aff_matrix[i][j] = np.random.choice(vals)
            aff_matrix[j][i] = aff_matrix[i][j]
    return aff_matrix / 100.0

def connected_components(g):
    subgroups = list(nx.connected_components(g))
    return len(subgroups)

## Class
class Population:

    def __init__(self, rep_flow_weight):
        self.time = 0
        self.rep_flow_weight = rep_flow_weight
        self.coop_graph = create_initial_graph()
        self.affinity_graph = create_affinity_graph()
        self.rep_flow_graph = np.zeros((N, N))
        self.utility_graph = np.zeros((N, N))
        self.number_of_connected_components = connected_components(self.coop_graph)
        self.initial_edges = list(self.coop_graph.edges())
        self.edge_history = []

    def calculate_rep_flow(self):
        paths = count_simple_paths(self.coop_graph)
        self.rep_flow_graph = np.zeros((N, N))
        for i in range(N):
            for j in range(i+1, N):
                for inter in range(l_max):
                    self.rep_flow_graph[i][j] += paths[inter][i][j] * alpha**(inter+2)
                    self.rep_flow_graph[j][i] = self.rep_flow_graph[i][j]

    def normalize_rep_flow(self):
        max_rep = np.max(self.rep_flow_graph)
        if max_rep == 0:
            rep_norm = self.rep_flow_graph
        else:
            rep_norm = self.rep_flow_graph / max_rep 
        return rep_norm

    def cooperate(self):
        added_edges = []
        matched = set()
        utilities = []
        for i in range(N):
            for j in range(i+1, N):
                if not self.coop_graph.has_edge(i, j):
                    utilities.append((self.utility_graph[i][j], i, j))
        utilities.sort(key=lambda x: x[0], reverse=True)
        for _, i, j in utilities:
            deg = max(self.coop_graph.degree(i), self.coop_graph.degree(j))
            benefit = deg ** beta
            if benefit <= cost:
                continue;
            if i not in matched and j not in matched:
                self.coop_graph.add_edge(i, j)
                matched.add(i)
                matched.add(j)
                added_edges.append((i,j))
        return added_edges
    
    def update_utility(self):
        self.calculate_rep_flow()
        self.utility_graph = self.rep_flow_weight * self.normalize_rep_flow() + (1-self.rep_flow_weight) * self.affinity_graph
        
    def actualise(self):
        self.time += 1
        self.update_utility() # it activates self.calculate_rep_flow()
        new_edges = self.cooperate()
        # save graph snapshot
        self.edge_history.append(new_edges)
        self.number_of_connected_components = connected_components(self.coop_graph)
        return len(new_edges) > 0
        
    # Parameters: nbr_size
    def write_state(self, dir):
        snapshot = {
            "time":                          self.time,
            "initial_edges":                 self.initial_edges,
            "edge_history":                  self.edge_history,
            "number_of_connected_components": self.number_of_connected_components,
        }
        file_name = dir + 'time' + str(self.time).rjust(nbr_size,"0") + '.pkl'
        with open(file_name, 'wb') as file:
            pickle.dump(snapshot, file)