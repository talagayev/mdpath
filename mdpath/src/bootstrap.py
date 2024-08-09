import pandas as pd
import numpy as np
from mdpath.src.graph import GraphBuilder
from mdpath.src.mutual_information import NMICalculator
from typing import Dict, Set, Tuple, List
import os


class BootstrapAnalysis:
    def __init__(
        self,
        df_all_residues,
        df_distant_residues,
        sorted_paths,
        num_bootstrap_samples,
        numpath,
        pdb,
        last_residue,
        num_bins: int = 35,
    ) -> None:
        self.df_all_residues = df_all_residues
        self.df_distant_residues = df_distant_residues
        self.sorted_paths = sorted_paths
        self.num_bootstrap_samples = num_bootstrap_samples
        self.numpath = numpath
        self.pdb = pdb
        self.last_residue = last_residue
        self.num_bins = num_bins
        self.common_counts, self.path_confidence_intervals = self.bootstrap_analysis

    def create_bootstrap_sample(
        self, df_dihedral: pd.DataFrame
    ) -> tuple[int, set[tuple]]:
        """Creates a sample from the dataframe with replacement for bootstrap analysis.

        Args:
            df (pd.DataFrame):Pandas dataframe with residue dihedral angle movements.

        Returns:
            bootstrap_sample (pd.DataFrame): Pandas dataframe containing the frames for the bootstrap analysis.
        """
        bootstrap_sample = df_dihedral.apply(
            lambda col: col.sample(n=len(df_dihedral), replace=True).reset_index(
                drop=True
            )
        )
        return bootstrap_sample

    def process_bootstrap_sample(
        self,
        pathways_set: Set[Tuple],
        sample_num: int,
    ) -> Tuple[int, List[List[int]]]:
        """Process a bootstrap sample to find common paths with the original sample.

        Args:
            df_all_residues (pd.DataFrame): Pandas dataframe with residue dihedral angle movements.
            df_distant_residues (pd.DataFrame): Pandas dataframe with distant residues.
            pathways_set (set[tuple]): Set of tuples with the pathways for bootstrapping.
            numpath (int): Amount of top paths to consider.
            num_bins (int, optional): Number of bins to group dihedral angle movements into for NMI calculation. Defaults to 35.

        Returns:
            common_count (int): Number of common paths between the bootstrap sample and the original sample.
            bootstrap_pathways (list[list[int]]): List of paths within the bootstrap sample.
        """
        bootstrap_sample = self.create_bootstrap_sample(self.df_all_residues)
        nmi_calculator = NMICalculator(bootstrap_sample, num_bins=self.num_bins)
        bootstrap_mi_diff = nmi_calculator.mi_diff_df
        graph = GraphBuilder(self.pdb, self.last_residue, bootstrap_mi_diff)
        bootstrap_path_total_weights = graph.collect_path_total_weights(
            self.df_distant_residues
        )
        bootstrap_sorted_paths = sorted(
            bootstrap_path_total_weights, key=lambda x: x[1], reverse=True
        )
        bootstrap_pathways = [
            path for path, _ in bootstrap_sorted_paths[: self.numpath]
        ]
        file_name = f"bootstrap_sample_{sample_num}.txt"
        new_file_path = os.path.join("bootstrap", file_name)
        with open(new_file_path, "w") as file:
            for pathway in bootstrap_pathways:
                file.write(f"{pathway}\n")

        bootstrap_set = set(tuple(path) for path in bootstrap_pathways)
        common_elements = bootstrap_set.intersection(pathways_set)
        common_count = len(common_elements)
        return common_count, bootstrap_pathways

    def bootstrap_analysis(self) -> Tuple[np.ndarray, Dict]:
        """Analyse the common paths between the original sample and bootstrap samples.

        Args:
            df_all_residues (pd.DataFrame): Pandas dataframe with residue dihedral angle movements.
            df_distant_residues (pd.DataFrame): Pandas dataframe with distant residues.
            sorted_paths (list[tuple]): List of tuples with the sorted paths.
            num_bootstrap_samples (int): Amount of samples to generate for bootstrap analysis.
            numpath (int): Number of top paths to consider.
            num_bins (int, optional): Number of bins to group dihedral angle movements into for NMI calculation. Defaults to 35.

        Returns:
            common_counts (np.array): Array with the counts of common paths between the original sample and bootstrap samples.
            path_confidence_intervals (dict): Dictionary with the confidence intervals for each path.
        """
        os.makedirs("bootstrap", exist_ok=True)
        pathways = [path for path, _ in self.sorted_paths[: self.numpath]]
        pathways_set = set(tuple(path) for path in pathways)
        results = []
        path_occurrences = {tuple(path): [] for path in pathways_set}

        for _ in range(self.num_bootstrap_samples):
            result, occurrences = self.process_bootstrap_sample(
                pathways_set,
                sample_num=_,
            )
            results.append(result)
            current_paths = set(tuple(path) for path in occurrences)
            for path in path_occurrences.keys():
                if path in current_paths:
                    path_occurrences[path].append(1)
                else:
                    path_occurrences[path].append(0)

        common_counts = np.array(results)
        standard_error = np.std(common_counts) / np.sqrt(self.num_bootstrap_samples)
        print("Standard error:", standard_error)

        path_confidence_intervals = {}
        for path, occurrences in path_occurrences.items():
            occurrences = np.array(occurrences, dtype=int)
            mean_occurrence = np.mean(occurrences)
            lower_bound = np.percentile(occurrences, 2.5)
            upper_bound = np.percentile(occurrences, 97.5)
            path_confidence_intervals[path] = (
                mean_occurrence,
                lower_bound,
                upper_bound,
            )

        return common_counts, path_confidence_intervals
