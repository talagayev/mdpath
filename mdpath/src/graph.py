import networkx as nx
import pandas as pd
from tqdm import tqdm
from itertools import combinations
from Bio import PDB

from mdpath.src.structure import calculate_distance


def graph_building(pdb_file: str, end: int, dist=5.0) -> nx.Graph:
    """Generates a graph of residues within a certain distance of each other.

    Args:
        pdb_file (str): Input PDB file.
        end (int): Last residue to consider.
        dist (float, optional): Cutoff distance for graph egdes. Distance of residues to eachother in Angström. Defaults to 5.0.

    Returns:
        residue_graph (nx.Graph): Graph of residues within a certain distance of each other.
    """
    residue_graph = nx.Graph()
    parser = PDB.PDBParser(QUIET=True)
    structure = parser.get_structure("pdb_structure", pdb_file)
    heavy_atoms = ["C", "N", "O", "S"]
    for model in structure:
        for chain in model:
            residues = [res for res in chain if res.get_id()[0] == " "]
            for res1, res2 in tqdm(
                combinations(residues, 2),
                desc="Processing residues",
                total=len(residues) * (len(residues) - 1) // 2,
            ):
                res1_id = res1.get_id()[1]
                res2_id = res2.get_id()[1]
                if res1_id <= end and res2_id <= end:
                    for atom1 in res1:
                        if atom1.element in heavy_atoms:
                            for atom2 in res2:
                                if atom2.element in heavy_atoms:
                                    distance = calculate_distance(
                                        atom1.coord, atom2.coord
                                    )
                                    if distance <= dist:
                                        residue_graph.add_edge(
                                            res1.get_id()[1], res2.get_id()[1], weight=0
                                        )
    return residue_graph


def graph_assign_weights(residue_graph: nx.Graph, mi_diff_df: pd.DataFrame) -> nx.Graph:
    """Assignes edge weights to the graph based on mutual information differences.

    Args:
        residue_graph (nx.Graph): Base residue graph.
        mi_diff_df (pd.DataFrame): Pandas dataframe with mutual information differences.

    Returns:
        residue_graph (nx.Graph): Residue graph with edge weights assigned.
    """
    for edge in residue_graph.edges():
        u, v = edge
        pair = ("Res " + str(u), "Res " + str(v))
        if pair in mi_diff_df["Residue Pair"].apply(tuple).tolist():
            weight = mi_diff_df.loc[
                mi_diff_df["Residue Pair"].apply(tuple) == pair, "MI Difference"
            ].values[0]
            residue_graph.edges[edge]["weight"] = weight
    return residue_graph


def max_weight_shortest_path(
    graph: nx.Graph, source: int, target: int
) -> tuple[list[int], float]:
    """Finds the shortest path between 2 far away residues with the highest weight.

    Args:
        graph (nx.Graph): Residue graph.
        source (int): Starting residue.
        target (int): Final residue.

    Returns:
        shortest_path (list[int]): List of residues in the shortest path with the heighest weight.
        total_weight (float): Total weight of the shortest path.
    """
    shortest_path = nx.dijkstra_path(graph, source, target, weight="weight")
    total_weight = sum(
        graph[shortest_path[i]][shortest_path[i + 1]]["weight"]
        for i in range(len(shortest_path) - 1)
    )
    return shortest_path, total_weight


def collect_path_total_weights(
    residue_graph: nx.Graph, df_distant_residues: pd.DataFrame
) -> list[tuple[list[int], float]]:
    """Wrapper function to collect the shortest path and total weight between distant residues.

    Args:
        residue_graph (nx.Graph): Residue graph.
        df_distant_residues (pd.DataFrame): Panda dataframe with distant residues.

    Returns:
        path_total_weights (list[tuple[list[int], float]]): List of tuples with the shortest path and total weight between distant residues.
    """
    path_total_weights = []
    for index, row in df_distant_residues.iterrows():
        try:
            shortest_path, total_weight = max_weight_shortest_path(
                residue_graph, row["Residue1"], row["Residue2"]
            )
            path_total_weights.append((shortest_path, total_weight))
        except nx.NetworkXNoPath:
            continue
    return path_total_weights
