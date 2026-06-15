import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from parameters import N, rep_flow_weights

BASE_DIR = "Simulations_Output/Results"
output_dir = "Simulations_Output/Plots"
os.makedirs(output_dir, exist_ok=True)
rep_weight_step = 1/(len(rep_flow_weights)-1)

def reconstruct_graph(snapshot):
    """
    Reconstruct the cooperation graph from the saved snapshot object.
    """
    g = nx.Graph()
    g.add_nodes_from(range(N))
    g.add_edges_from(snapshot["initial_edges"])
    for step_edges in snapshot["edge_history"]:
        g.add_edges_from(step_edges)
    return g

def compute_layout(initial_edges):
    G_init = nx.Graph()
    G_init.add_nodes_from(range(N))
    G_init.add_edges_from(initial_edges)

    components = list(nx.connected_components(G_init))
    pos = {}

    n_cols = int(np.ceil(np.sqrt(len(components))))
    spacing = 5
    radius = 2

    for comp_idx, comp in enumerate(components):
        row = comp_idx // n_cols
        col = comp_idx % n_cols
        center_x = col * spacing
        center_y = -row * spacing
        comp_nodes = sorted(comp)

        for k, node in enumerate(comp_nodes):
            angle = 2 * np.pi * k / len(comp_nodes)
            pos[node] = (
                center_x + radius * np.cos(angle),
                center_y + radius * np.sin(angle)
         )
    return pos


def load_snapshots(sim_path):
    """Load all pkl dicts in a simulation folder, keyed by time step."""
    snapshots = {}
    for file in sorted(os.listdir(sim_path)):
        if file.endswith(".pkl"):
            with open(os.path.join(sim_path, file), "rb") as f:
                snap = pickle.load(f)
            snapshots[snap["time"]] = snap
    return snapshots
    

def plot_graph_snapshot(snapshot, pos, save_path, weight, t):
    g = reconstruct_graph(snapshot)
    components = list(nx.connected_components(g))
    # assign a color id per component
    color_map = {}
    for comp_id, comp in enumerate(components):
        for node in comp:
            color_map[node] = comp_id

    node_colors = [color_map[n] for n in g.nodes()]

    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_facecolor("#f8f8f8")
    fig.patch.set_facecolor("#f8f8f8")

    nx.draw_networkx_edges(g, pos, edge_color="#888888",
        width=1.2, alpha=0.7, ax=ax)

    nx.draw_networkx_nodes(g, pos, node_color=node_colors,
        cmap=plt.get_cmap("tab20"), node_size=120,
        linewidths=0.5, edgecolors="white", ax=ax)

    fig.suptitle(
        f"{len(components)} connected component{'s' if len(components) != 1 else ''}",
        fontsize=28, fontweight="normal", y=0.92)

    fig.text(0.02, 0.5, f"Reputational Flow Weight (w) = {weight}", va="center", ha="left",
        rotation=90, fontsize=24, fontweight="normal")

    fig.text(0.5, 0.02, f"Time step (t) = {t}", ha="center",
        fontsize=24, fontweight="normal")
    
    ax.set_title("")
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
 
def plot_simulation_graphs(weight_folder, sim_folder, sim_path):
    """Generate and save graph snapshots for every saved time step of one simulation."""
    snapshots = load_snapshots(sim_path)
    if not snapshots:
        return
 
    earliest = snapshots[min(snapshots.keys())]
    pos = compute_layout(earliest["initial_edges"])
    
    # Parse weight from folder name (format: "weight_XXX" where XXX are digits)
    weight_str = weight_folder[-3:]
    weight_int = int(weight_str)      
    weight_value = weight_int / 100   
    
    # Format weight to remove redundant trailing zeros
    weight_display = 0
    if weight_value != 0:
        formatted = f"{weight_value:.10f}".rstrip('0').rstrip('.')
        weight_display = int(formatted) if '.' not in formatted else formatted
    
    graph_output_dir = os.path.join(output_dir, weight_folder, sim_folder, "graphs")
    os.makedirs(graph_output_dir, exist_ok=True)
 
    for t, snap in sorted(snapshots.items()):
        save_path = os.path.join(graph_output_dir, f"graph_t{str(t).zfill(2)}.png")
        plot_graph_snapshot(snap, pos, save_path, weight=weight_display, t=t)
 
    print(f"    Graph snapshots saved to {graph_output_dir}")
 
def main():
    final_results = []
    final_times = None
    global_min_len = None

    # Loop over Weight_XX folders
    for weight_folder in sorted(os.listdir(BASE_DIR)):
        weight_path = os.path.join(BASE_DIR, weight_folder)
        if not os.path.isdir(weight_path):
            continue

        print("Processing:", weight_folder)
        all_simulations = []
        weight_min_len = None
        weight_times_ref = None
        
        # Loop over simulations
        for weight_sub in sorted(os.listdir(weight_path)):
            sim = os.path.join(weight_path, weight_sub)
            if not os.path.isdir(sim):
                continue
            
            time_series = {}
            # Load all timeXX.pkl files
            for file in sorted(os.listdir(sim)):       
                if file.endswith(".pkl"):
                    filepath = os.path.join(sim, file)
                    with open(filepath, "rb") as f:
                        pop = pickle.load(f)
                    time_series[pop["time"]] = pop["number_of_connected_components"]

            # Sort by time
            times = sorted(time_series.keys())
            values = [time_series[t] for t in times]

            # Track minimum length within this weight folder
            if weight_min_len is None or len(values) < weight_min_len:
                weight_min_len = len(values)
                weight_times_ref = times  # times array corresponding to the shortest run
            
            all_simulations.append(values)
            plt.figure()
            plt.plot(times, values, marker='o', linestyle='-')
            plt.xlabel("Time")
            plt.ylabel("Number of Connected Components")
            plt.title(f"Weight: {weight_folder}")
            plt.grid(False)
            weight_output_dir = os.path.join(output_dir, weight_folder)
            os.makedirs(weight_output_dir, exist_ok=True)
            filename = os.path.join(weight_output_dir, f"{weight_sub}.png")
            plt.savefig(filename, dpi=300)
            final_times = times
            plt.close()

            plot_simulation_graphs(weight_folder, weight_sub, sim)

        # Truncate all simulations in this weight folder to weight_min_len
        all_simulations = [sim[:weight_min_len] for sim in all_simulations]
        weight_times = weight_times_ref[:weight_min_len]
        
        if global_min_len is None or weight_min_len < global_min_len:
            global_min_len = weight_min_len
            final_times = weight_times

        plt.figure()
        mean = np.mean(all_simulations, axis=0)
        std = np.std(all_simulations, axis=0)
        plt.plot(weight_times, mean, marker='o', linestyle='-')
        plt.fill_between(weight_times, mean - std, mean + std, alpha=0.3, label="±1 std")
        plt.xlabel("Time")
        plt.ylabel("Mean Number of Connected Components")
        plt.title(f"Weight: {weight_folder}")
        plt.legend()
        plt.grid(False)
        plt.savefig(os.path.join(output_dir, f"{weight_folder}.png"), dpi=300)
        plt.close()
        
        final_results.append(mean.tolist())

    # Truncate final_results to global_min_len so all weights align
    final_results = [res[:global_min_len] for res in final_results]
    final_times = final_times[:global_min_len]


    # Plot final results
    plt.figure(figsize=(8,6))
    for i, weight in enumerate(final_results):
        w = i * rep_weight_step
        plt.plot(final_times, weight, marker='o', linestyle='-', label=f"w = {w}")
    plt.xlabel("Time Steps")
    plt.ylabel("Mean number of connected components")
    plt.title("Cooperation Dynamics")
    # remove background grid lines
    plt.grid(False)
    # legend with title
    plt.legend(title="Reputational Flow Weight")
    plt.savefig(os.path.join(output_dir, "Results_per_time.png"), dpi=300)
    plt.close()

    data = np.array(final_results)
    plt.figure(figsize=(8,6))
    for t in range(data.shape[1]):
        plt.plot(rep_flow_weights, data[:, t], marker='o', linestyle='-', label=f"t = {t}")
    plt.xlabel("Reputational Flow Weight")
    plt.ylabel("Mean number of connected components")
    plt.title("Cooperation Dynamics")
    plt.grid(False)
    plt.legend()
    plt.savefig(os.path.join(output_dir, "Results_per_weight.png"), dpi=300)
    plt.close()

if __name__=="__main__":
    main()