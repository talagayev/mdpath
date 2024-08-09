from tqdm import tqdm
import numpy as np
import pandas as pd
import MDAnalysis as mda
from MDAnalysis.analysis.dihedrals import Dihedral
from multiprocessing import Pool
from Bio import PDB
from itertools import combinations

class StructureCalculations:
    def __init__(self, pdb):
        self.pdb = pdb
        self.first_res_num, self.last_res_num = self.res_num_from_pdb()
        self.num_residues = self.last_res_num - self.first_res_num 
        
    def res_num_from_pdb(self) -> tuple[int, int]:
        """Gets first and last residue number from a PDB file.

        Args:
            pdb (str): Path to PDB file.

        Returns:
            first_res_num (int): First residue number.
            last_res_num (int): Last residue number.
        """
        parser = PDB.PDBParser(QUIET=True)
        structure = parser.get_structure("protein", self.pdb)
        first_res_num = float("inf")
        last_res_num = float("-inf")
        for res in structure.get_residues():
            if PDB.Polypeptide.is_aa(res):
                res_num = res.id[1]
                if res_num < first_res_num:
                    first_res_num = res_num
                if res_num > last_res_num:
                    last_res_num = res_num
        return int(first_res_num), int(last_res_num)



    def calculate_distance(self, atom1: int, atom2: int) -> float:
        """Calculates the distance between two atoms.

        Args:
            atom1 (tuple[float]): Coordinates of the first atom.
            atom2 (tuple[float]): Coordinates of the second atom.

        Returns:
            distance (float): Normalized distance between the two atoms.
        """
        distance_vector = [atom1[i] - atom2[i] for i in range(min(len(atom1), len(atom2)))]
        distance = np.linalg.norm(distance_vector)
        return distance


    def calculate_residue_suroundings(self, dist: float, mode: str) -> pd.DataFrame:
        """Calculates residues that are either close to or far away from each other in a PDB structure.

        Args:
            dist (float): Distance cutoff for residue pairs.
            mode (str): 'close' to calculate close residues, 'far' to calculate faraway residues.

        Returns:
            pd.DataFrame: Pandas dataframe with residue pairs and their distance.
        """
        if mode not in ["close", "far"]:
            raise ValueError("Mode must be either 'close' or 'far'.")

        parser = PDB.PDBParser(QUIET=True)
        structure = parser.get_structure("pdb_structure", self.pdb_file)
        heavy_atoms = ["C", "N", "O", "S"]
        residue_pairs = []
        residues = [res for res in structure.get_residues() if PDB.Polypeptide.is_aa(res)]

        for res1, res2 in tqdm(
            combinations(residues, 2),
            desc=f"\033[1mCalculating {mode} residue surroundings\033[0m",
            total=len(residues) * (len(residues) - 1) // 2,
        ):
            res1_id = res1.get_id()[1]
            res2_id = res2.get_id()[1]
            if res1_id <= self.last_res_num and res2_id <= self.last_res_num:
                condition_met = False if mode == "close" else True
                for atom1 in res1:
                    if atom1.element in heavy_atoms:
                        for atom2 in res2:
                            if atom2.element in heavy_atoms:
                                distance = self.calculate_distance(atom1.coord, atom2.coord)
                                if (mode == "close" and distance <= dist) or (mode == "far" and distance > dist):
                                    condition_met = True
                                    break
                        if condition_met:
                            break
                if condition_met:
                    residue_pairs.append((res1_id, res2_id))
        
        return pd.DataFrame(residue_pairs, columns=["Residue1", "Residue2"])
    
class DihedralAngles:
    def __init__(self, traj, first_res_num, last_res_num, num_residues) -> None:
        self.traj = traj
        self.first_res_num = first_res_num
        self.last_res_num = last_res_num
        self.num_residues = num_residues
    
    
    def calc_dihedral_angle_movement(self, res_id: int) -> tuple[int, np.array]:
        """Calculates dihedral angle movement for a residue over the cours of the MD trajectory.

        Args:
            res_id (int): Residue number.
            traj (mda.Universe): MDAnalysis Universe object containing the trajectory.

        Returns:
            res_id (int): Residue number.
            dihedral_angle_movement (np.array): Dihedral angle movement for the residue over the course of the trajectory.
        """
        res = self.traj.residues[res_id]
        ags = [res.phi_selection()]
        R = Dihedral(ags).run()
        dihedrals = R.results.angles
        dihedral_angle_movement = np.diff(dihedrals, axis=0)
        return res_id, dihedral_angle_movement




    def calculate_dihedral_movement_parallel(self, num_parallel_processes: int,) -> pd.DataFrame:
        """Parallel calculation of dihedral angle movement for all residues in the trajectory.

        Args:
            num_parallel_processes (int): Amount of parallel processes.

        Returns:
            df_all_residues (pd.DataFrame): Pandas dataframe with all residue dihedral angle movements.
        """
        try:
            with Pool(processes=num_parallel_processes) as pool:
                df_all_residues = pd.DataFrame()
                with tqdm(
                    total=self.num_residues,
                    ascii=True,
                    desc="\033[1mProcessing residue dihedral movements\033[0m",
                ) as pbar:
                    for res_id, result in pool.imap_unordered(
                        self.calc_dihedral_angle_movement, range(self.first_res_num, self.last_res_num + 1)
                    ):
                        try:
                            df_residue = pd.DataFrame(result, columns=[f"Res {res_id}"])
                            df_all_residues = pd.concat(
                                [df_all_residues, df_residue], axis=1
                            )
                            pbar.update(1)
                        except Exception as e:
                            print(f"\033[1mError processing residue {res_id}: {e}\033[0m")
        except Exception as e:
            print(f"{e}")
        return df_all_residues