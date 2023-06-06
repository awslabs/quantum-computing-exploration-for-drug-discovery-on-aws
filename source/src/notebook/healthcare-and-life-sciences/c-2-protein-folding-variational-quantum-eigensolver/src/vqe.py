import os
import json
import logging
import warnings
import ast
import importlib
import numpy as np
from typing import List, Dict
from qiskit_nature.problems.sampling.protein_folding.peptide.peptide import Peptide
from qiskit_nature.problems.sampling.protein_folding.penalty_parameters import PenaltyParameters
from qiskit_nature.problems.sampling.protein_folding.protein_folding_problem import ProteinFoldingProblem
from qiskit.algorithms import VQE
from qiskit.circuit.library import RealAmplitudes
from qiskit.utils import QuantumInstance
from qiskit_braket_provider import AWSBraketProvider, BraketLocalBackend
from braket.jobs.metrics import log_metric
from braket.jobs import save_job_result
from pdbparser.pdbparser import pdbparser

warnings.filterwarnings('ignore')


provider = AWSBraketProvider()

available_interactions = {
    "RandomInteraction": "qiskit_nature.problems.sampling.protein_folding.interactions.random_interaction",
    "MiyazawaJerniganInteraction": "qiskit_nature.problems.sampling.protein_folding.interactions.miyazawa_jernigan_interaction",
    "MixedInteraction": "qiskit_nature.problems.sampling.protein_folding.interactions.mixed_interaction"
}

def get_polypeptide(main_chain: List[str], side_chains: List[str] = None) -> Peptide:
    """Create structural information based on the provided main chain and side chains
    
    Args:
        main_chain (List[str]): Amino acid sequence
        side_chains (List[str]): Amino acids attached to the residues of the main chain

    Returns:
        Peptide: structural information of the amino acids sequence
    """
    if len(main_chain) > 1:
        if side_chains is None:
            side_chains = [""] * len(main_chain)
        peptide = Peptide(main_chain, side_chains)
        return peptide
    raise Exception("Length of main chain should be greater than 1.")


def _get_penalty_parameters(penalty_parameters: Dict[str, int]) -> PenaltyParameters:
    """Creates penalty parameter values to prevent chain from folding back on itself.

    Args:
        penalty_parameters (Dict[str, str]): Penalty parameters dictionary containing penalty_chiral to impose right chirality, 
        penalty_back to penalize turns along the same axis, 
        penalty_1 to penalize local overlap.

    Returns:
        PenaltyParameters: PenaltyParameters object with values to penalize chain


    """
    penalty_parameters = ast.literal_eval(penalty_parameters)
    return PenaltyParameters(penalty_parameters["penalty_chiral"],
                             penalty_parameters["penalty_back"],
                             penalty_parameters["penalty_1"])


def get_hamiltonian(peptide: Peptide, 
                  penalty_parameters: Dict[str, int], 
                  interaction: str = "MiyazawaJerniganInteraction"):
    """Get hamiltonian using the provided polypeptide chain and interaction.
    
    Args: 
        peptide (Peptide): Structural information of amino acids sequence
        penalty_parameters (Dict[str, str]): Penalty parameters to penalize chirality, turns along the same axis and
        local overlap.
        interaction (Union[MiyazawaJerniganInteraction, RandomInteraction, MixedInteraction]): interaction between amino acids in peptide
    
    Returns:
        qubit_op: Hamiltonian for the provided polypeptide chain and interaction
    """
    if interaction not in available_interactions.keys():
        raise Exception("Please use either RandomInteraction, MixedInteraction or MiyazawaJerniganInteraction")
    interaction_module = importlib.import_module(available_interactions[interaction])
    interaction = getattr(interaction_module, interaction)
    interaction = interaction()
    penalty_parameters = _get_penalty_parameters(penalty_parameters)
    protein_folding_problem = ProteinFoldingProblem(peptide, interaction, penalty_parameters)
    qubit_op = protein_folding_problem.qubit_op()
    return qubit_op, protein_folding_problem


def store_intermediate_result(eval_count, parameters, mean, std):
    """Callback to access intermediate results during optimization
    
    Args: 
        eval_count (int): Evaluation count
        parameters (np.ndarray): An array containing parameters values for the ansatz
        mean (float): Evaluated mean
        std (float): Evaluated standard deviation
    """
    log_metric(
        metric_name="Energy",
        value=mean,
        iteration_number=eval_count
    )


def convert_xyz(path, export):
    """Convert xyz coordinates file to pdb file
    
    Args:
        path (str): Location to xyz file
        export (str): Location to pdb file
    """
    assert os.path.isfile(path), "Unable to find given xyz file '%s'"%path
    with open(path, 'r') as fd:
        lines = [l.strip() for l in fd.readlines()]
    records = []
    for l in lines[2:]:
        el, x, y, z = l.split()
        records.append( { "record_name"       : 'ATOM',
                          "serial_number"     : len(records)+1,
                          "atom_name"         : el,
                          "location_indicator": '',
                          "residue_name"      : 'XYZ',
                          "chain_identifier"  : '',
                          "sequence_number"   : len(records)+1,
                          "code_of_insertion" : '',
                          "coordinates_x"     : float(x),
                          "coordinates_y"     : float(y),
                          "coordinates_z"     : float(z),
                          "occupancy"         : 1.0,
                          "temperature_factor": 0.0,
                          "segment_identifier": '',
                          "element_symbol"    : el,
                          "charge"            : '',
                          } )
    pdb = pdbparser(filePath = None)
    pdb.records = records
    if export is not None:
        pdb.export_pdb(export)
    return pdb
    
    
def run(qubit_op, optimizer, optimizer_params, shots, backend="local"):
    """Run VQE optimization to find lowest energy state
    
    Args:
        qubit_op (primitive_ops):  Hamiltonian for the provided polypeptide chain and interaction
        optimizer (str): Optimizer to be used to find minimum energy
        optimizer_params (Dict[str, Any]): Parameters to pass to optimizer
        shots (int): Number of shots to execute ansatz
        backend (str): Whether to run locally or as an Amazon Braket job

    Returns:
        Dict[str, Any]: Returns a dictionay containing output 
    """
    optimizer_module = importlib.import_module("qiskit.algorithms.optimizers")
    optimizer = getattr(optimizer_module, optimizer)
    optimizer_params = ast.literal_eval(optimizer_params)
    optimizer = optimizer(**optimizer_params)
    backend_device = None
    quantum_instance=None

    if backend=="local":
        backend_device = BraketLocalBackend()
    else:
        backend_device = backend.split("/")[-1]
        if backend_device in ["sv1", "tn1"]:
            backend_device = backend_device.upper()
        if backend_device == "ionQdevice":
            backend_device = "IonQ Device"
        print(backend_device)
        backend_device = provider.get_backend(backend_device)
    quantum_instance = QuantumInstance(
        backend_device, shots=shots
    )

    vqe = VQE(
        optimizer=optimizer,
        ansatz=RealAmplitudes(reps=2),
        quantum_instance=quantum_instance,
        callback=store_intermediate_result
    )

    raw_result = vqe.compute_minimum_eigenvalue(qubit_op)
    print(raw_result)
    return raw_result


if __name__ == "__main__":

    hp_file = os.environ["AMZN_BRAKET_HP_FILE"]
    device_arn = os.environ["AMZN_BRAKET_DEVICE_ARN"]
    output_dir = os.environ["AMZN_BRAKET_JOB_RESULTS_DIR"]
    
    with open(hp_file, "r") as f:
        hyperparams = json.load(f)
    print(hyperparams)
    
    main_chain = hyperparams["main_chain"]
    side_chains = [""] * len(main_chain) if hyperparams["side_chains"] == "None" else hyperparams["side_chains"]
    penalty_params = hyperparams["penalty_params"]
    optimizer = hyperparams["optimizer"]
    optimizer_params = hyperparams["optimizer_params"]
    interaction = hyperparams["interaction"]
    shots = hyperparams["shots"]
    
    peptide = get_polypeptide(main_chain, side_chains)
    qubit_op, protein_folding_problem = get_hamiltonian(peptide, penalty_params, interaction)
    result = run(qubit_op, optimizer, optimizer_params, shots, device_arn)
    np.save(output_dir + "/" + "optimal_point.npy", result.optimal_point)
    result = protein_folding_problem.interpret(raw_result=result)
    print(result.protein_shape_file_gen.get_xyz_data())
    xyz_file = output_dir + "/" + main_chain
    pdb_file = output_dir + "/" + main_chain + ".pdb"
    result.protein_shape_file_gen.save_xyz_file(xyz_file)
    convert_xyz(xyz_file + ".xyz", pdb_file)