import time
import numpy as np

from itertools import product
from collections import OrderedDict

from qiskit.circuit import QuantumRegister
from qiskit.quantum_info import Statevector
from qiskit import QuantumCircuit, Aer, execute

import deltas_oracle


class Quantum_Folding_Predictor():

    def __init__(self, n_angles, bits_to_discretize, ancilla_bits, input_oracle):
        
        self.n_angles = n_angles
        self.angle_precision_bits = bits_to_discretize
        self.move_id_len = int(np.ceil(np.log2(n_angles)))
        self.ancilla_bits = ancilla_bits
        self.input_oracle = input_oracle

    def quantum_calculate_3D_structure(self, nW):

        # State definition. All angles range from 0 to 2pi

        g_angles = []
        for i in range(self.n_angles):
            g_angles.append(QuantumRegister(self.angle_precision_bits, name = 'angle' + str(i)))

        # Move proposal
        g_move_id = QuantumRegister(self.move_id_len, name = 'move_id') #Which angle are we modifying
        g_move_value = QuantumRegister(1, name = 'move_value') #0 -> decrease the angle. 1-> increase it

        # Coin
        g_coin = QuantumRegister(1, name = 'coin')

        # Ancillas
        g_ancilla = QuantumRegister(self.ancilla_bits, name = 'ancilla')

        # Circuit
        qc = QuantumCircuit(g_ancilla,g_coin,g_move_value,g_move_id)
        for i in range(self.n_angles-1,-1,-1):
            qc = qc + QuantumCircuit(g_angles[i])

        
        # Notice that this initialization is efficient even in quantum computers if we used the Grover-Rudolph algorithm.
        initial_angle_amplitudes, _ = self.von_mises_amplitudes()
        for g_angle in g_angles:
            qc.initialize(initial_angle_amplitudes, g_angle)

        oracle_generator = deltas_oracle.Deltas_Oracle(self.input_oracle, in_bits = self.n_angles*self.angle_precision_bits + self.move_id_len + 1, out_bits = self.probability_bits)
        #list_gates.append(W_gate) # We deepcopy W_gate to not interfere with other calls
        if self.beta_type == 'fixed':

            #It creates one different oracle for each beta
            oracle = oracle_generator.generate_oracle(self.oracle_option, self.beta)

        for i in range(nW):

            if self.beta_type == 'variable':
                if self.annealing_schedule == 'Cauchy' or self.annealing_schedule == 'linear':
                    beta_value = self.beta * i 
                elif self.annealing_schedule == 'Boltzmann' or self.annealing_schedule == 'logarithmic':
                    beta_value = self.beta * np.log(i) + self.beta
                elif self.annealing_schedule == 'geometric':
                    beta_value = self.beta * self.alpha**(-i+1)
                elif self.annealing_schedule == 'exponential': 
                    space_dim = self.n_angles
                    beta_value = self.beta * np.exp( self.alpha * (i-1)**(1/space_dim) )
                else:
                    raise ValueError('<*> ERROR: Annealing Scheduling wrong value. It should be one of [linear, logarithmic, geometric, exponential] but it is', self.annealing_schedule)

                #It creates one different oracle for each beta
                oracle = oracle_generator.generate_oracle(self.oracle_option, beta_value)
            
            W_gate = self.W_func_n(oracle)
            
            #list_gates[i].params[0]= beta
            qc.append(W_gate, [g_ancilla[j] for j in range(self.probability_bits)] + [g_coin[0],g_move_value[0]]+ [g_move_id[j] for j in range(self.move_id_len)] +[g_angles[k][j] for (k,j) in product(range(self.n_angles-1,-1,-1), range(self.angle_precision_bits))])

            qc.snapshot(label = str(i))

        start_time = time.time()

        backend = Aer.get_backend('statevector_simulator')
        
        #experiment = execute(qc, backend=self.device, backend_options=self.backend_options)
        #state_vector = Statevector(experiment.result().get_statevector(qc))

        result = execute(qc, backend).result()
        snapshots = result.data()['snapshots']['statevector']

        time_statevector = time.time() - start_time

        # Extract probabilities in the measurement of the angles phi and psi
        #probabilities = state.probabilities([j+self.probability_bits+2+self.move_id_len for j in range(self.angle_precision_bits * self.n_angles)])

        probs = {}
        number_bits_angles = self.angle_precision_bits * self.n_angles

        for i, state_vector in snapshots.items():
            int_i = int(i)
            probs[int_i] = {}

            state_vector = Statevector(snapshots[i][0])

            total_bits = state_vector.num_qubits
            angle_qubits = [qubit_index for qubit_index in range ((total_bits - number_bits_angles), total_bits)]
            probabilities = state_vector.probabilities(angle_qubits)
        
            for index_probabilites in range(2**(self.angle_precision_bits *self.n_angles)):

                key = self.convert_index_to_key(index_probabilites, self.angle_precision_bits, self.n_angles)
                probs[int_i][key] = probabilities[index_probabilites]#.as_integer

        probs = OrderedDict(sorted(probs.items()))

        return [probs, time_statevector]
    
    def von_mises_amplitudes():
        pass