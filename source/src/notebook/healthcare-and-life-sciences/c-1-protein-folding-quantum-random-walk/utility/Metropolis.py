import copy
import numpy as np
from itertools import product
import time
import math
import json
from math import pi
import collections, functools, operator
from collections import OrderedDict

# Importing standard Qiskit libraries and configuring account
from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Statevector
from qiskit.compiler import transpile
from qiskit_aer import AerSimulator

import beta_precalc_TruthTableOracle

class QuantumMetropolis():

    def __init__(self, n_angles, input_oracle, initialization, bits, tools):

        self.tools = tools
        self.n_angles = n_angles
        self.input_oracle = input_oracle

        #Global variables
        # self.initialization = self.tools.args.initialization
        self.initialization = initialization

        # Number of bits necessary to specify the position of each angle
        # self.angle_precision_bits = self.tools.args.bits
        self.angle_precision_bits = bits
        #Oracle output ancilla bits
        self.probability_bits = self.tools.config_variables['ancilla_bits']
        self.beta = self.tools.config_variables['beta']
        self.beta_type = self.tools.config_variables['beta_type']
        self.kappa = self.tools.config_variables['kappa']
        self.alpha = self.tools.config_variables['alpha']
        self.oracle_option = self.tools.config_variables['oracle_option']

        self.qiskit_api_path = self.tools.config_variables['path_qiskit_token']
        self.selected_device = self.tools.config_variables['device_ibm_q']
        self.oracle_option = self.tools.config_variables['oracle_option']

        self.move_id_len = int(np.ceil(np.log2(n_angles)))
        self.annealing_schedule = self.tools.config_variables['annealing_schedule']

        self.initial_step = self.tools.config_variables['initial_step']
        self.final_step = self.tools.config_variables['final_step']
        self.w_real_mode = self.tools.config_variables['w_real_mode']

        if self.probability_bits < 3:
            raise ValueError('The minimum number of ancilla qubits needed for this algorithm is 3! Currently there are only', self.probability_bits) 

        if self.n_angles*self.angle_precision_bits + self.move_id_len + self.probability_bits + 2 > 32:
            raise ValueError('The number of qubits is too large (larger than 32)! Currently there are\n'+
                            str(self.n_angles)+ ' angles, each with '+str(self.angle_precision_bits)+' qubits\n'+
                            'an ancilla with '+str(self.probability_bits)+' bits\n'+
                            'a move_id register with '+str(self.move_id_len)+' bits\n'+
                            'and finally a single qubit called move_value and another for the coin.\n'+
                            'In total there are '+str(self.n_angles*self.angle_precision_bits + self.move_id_len + self.probability_bits + 1)+' qubits\n'
                            )

        # For n angles
        [self.move_preparation_gate, self.conditional_move_gate_n, self.reflection_gate] = self.prepare_initial_circuits_n()

    def move_preparation(self, circuit,move_value,move_id):
        '''
        Proposes new moves
        '''
        circuit.h(move_value) #Es un único bit que puede ser 0 para + y 1 para -
        if bin(self.n_angles).count('1') == 1: # if the number of angles is a power of two: dipeptides and tripeptides
            circuit.h(move_id)
        elif self.n_angles == 6: # For tetrapeptides
            circuit.u(theta = 2* np.arcsin(np.sqrt(1/3)), phi = 0, lam = 0, qubit=move_id[2])
            circuit.x(move_id[2])
            circuit.ch(move_id[2], move_id[1])
            circuit.x(move_id[2])
            circuit.h(move_id[0])              
        else:
            raise NotImplementedError
            # vector = ([1]*self.n_angles + [0]*(2**(self.move_id_len) - self.n_angles))/np.sqrt(self.n_angles)
            # circuit.initialize(vector, [move_id[j] for j in range(self.move_id_len)])

    def conditional_move_npeptide(self,circuit,ancilla,coin,move_value,move_id,angles):
        '''
        Conditioned on coin, perform a move. Tested ok.
        We use a repetitive structure where we perform the conditional sum and subtraction for each angle.
        '''
        # For each angle
        for i in range(self.n_angles):
            angle = angles[i] #Select the angle from the list of registers
            angle_index = np.binary_repr(i, width=self.move_id_len) #convert i to binary

            # Put the given move_id in all 1 to control on it: for instance if we are controling on i=2, move 010 ->111
            for j in range(len(angle_index)):
                if angle_index[j] == '0':
                    circuit.x(move_id[j])

            circuit.mcx(control_qubits= [coin[0]]+[move_id[j] for j in range(move_id.size)], target_qubit = ancilla[0])#create a single control
            self.sumsubtract1(circuit,angle,ancilla[0],ancilla[1],ancilla[2],move_value[0]) #sum or subtract 1 to the angle
            circuit.mcx(control_qubits= [coin[0]]+[move_id[j] for j in range(move_id.size)], target_qubit = ancilla[0])#create a single control        
            
            # Undo the move_id preparation: for instance, if we are controlling on i= 2 move 111->010
            for j in range(len(angle_index)):
                if angle_index[j] == '0':
                    circuit.x(move_id[j])

    def reflection(self, circuit,coin,move_value,move_id):
        '''
        I have to investigate over what is the reflection performed. Is it performed over 000?
        If in state 0000, make it 1111, cccz gate and back to 0000
        '''
        circuit.x(move_id)
        circuit.x(move_value)
        circuit.x(coin)
        
        # Perform a multicontrolled Z
        circuit.h(coin[0])
        circuit.mcx(control_qubits = [move_id[j] for j in range(self.move_id_len)]+ [move_value[0]], target_qubit = coin[0])
        circuit.h(coin[0])
        
        circuit.x(move_id)
        circuit.x(move_value)
        circuit.x(coin)

    def prepare_initial_circuits_n(self):

        # Move preparation gate ---------------------------------------
        s_move_id = QuantumRegister(self.move_id_len) 
        s_move_value = QuantumRegister(1)

        sub_circ = QuantumCircuit(s_move_value,s_move_id)
        self.move_preparation(sub_circ,s_move_value,s_move_id)
        move_preparation_gate = sub_circ.to_instruction()

        # Conditional move gate ----------------------------------------
        s_angles = []
        for i in range(self.n_angles):
            s_angles.append(QuantumRegister(self.angle_precision_bits, name = 'angle' + str(i)))
        s_move_id = QuantumRegister(self.move_id_len)
        s_move_value = QuantumRegister(1)
        s_coin = QuantumRegister(1)
        s_ancilla = QuantumRegister(self.probability_bits)


        # Creates the circuit
        sub_circ = QuantumCircuit(s_ancilla, s_coin, s_move_value, s_move_id)
        for i in range(self.n_angles-1,-1,-1):
            sub_circ.add_register(s_angles[i])

        self.conditional_move_npeptide(sub_circ,s_ancilla, s_coin, s_move_value, s_move_id, s_angles)

        # Optimize the circuit

        '''
        print('Before optimization------- conditional_move_npeptide')
        print('gates = ', sub_circ.count_ops())
        print('depth = ', sub_circ.depth())
        sub_circ = transpile(sub_circ, seed_transpiler=1, optimization_level=3)
        print('After optimization--------')
        print('gates = ', sub_circ.count_ops())
        print('depth = ', sub_circ.depth())
        '''
        conditional_move_gate_n = sub_circ.to_instruction()

        # Reflection gate --------------------------------------------------
        s_move_id = QuantumRegister(self.move_id_len) 
        s_move_value = QuantumRegister(1)
        s_coin = QuantumRegister(1)

        sub_circ = QuantumCircuit(s_coin, s_move_value, s_move_id)
        self.reflection(sub_circ,s_coin, s_move_value, s_move_id)

        # We could optimize the circuit, but it will probably not be worth it (fairly small)

        reflection_gate = sub_circ.to_instruction()

        return [move_preparation_gate, conditional_move_gate_n, reflection_gate]

    def sum1(self, circuit,qubit_string,control,start,end):
        
        circuit.cx(control,end) # iff control = 1, end = 1
        circuit.x(start)
        circuit.cx(control,start) # iff control = 1, start = 0

        for i in range(qubit_string.size,-1,-1):
            '''
            Next thing we analise if all qubits to the right have value 1, 
            and save it in the current qubit and start.
            Don't need to add control, since end already does that work
            '''
            if i < qubit_string.size:
                # For i = 0, there is only the start to worry about
                circuit.mcx(control_qubits= [qubit_string[j] for j in range(i-1,-1,-1)]+[end], target_qubit = qubit_string[i])
            circuit.mcx(control_qubits = [qubit_string[j] for j in range(i-1,-1,-1)]+[end], target_qubit = start)

            '''
            Next, controlling on the current qubit and start, we change all the following qubits to 0.
            We have to control with qubit_string[n_qubit], start and control because start could be at state 1 without control also being in that state.
            '''
            if i == qubit_string.size:
                for j in range(i-1,-1,-1):
                    circuit.ccx(control,start,qubit_string[j])
                circuit.ccx(control,start,end)
            elif i == 0:
                circuit.mcx(control_qubits = [control,qubit_string[i],start], target_qubit = end)
            else:
                for j in range(i-1,-1,-1):            
                    circuit.mcx(control_qubits = [control,qubit_string[i],start], target_qubit = qubit_string[j])
                circuit.mcx(control_qubits = [control,qubit_string[i],start], target_qubit = end)
        circuit.x(start)

    def subtract1(self, circuit,qubit_string,control,start,end):
        '''
        Outputs:
        subtracts register 2 (1 qubit) from register 1 in register 1. Tested ok.
        
        Input:
        circuit: QuantumCircuit with registers qubit_string, control, ancilla
        
        qubit_string: QuantumRegister
        
        control: Qubit. Use ancilla[0] or similar
        
        start: Qubit. Use ancilla[1] or similar
        end: Qubit. Use ancilla[2] or similar
        
        Comments: In binary, subtracting is the same procedure as summing when we exchange 0s and 1s
        '''
        circuit.x(qubit_string)

        self.sum1(circuit,qubit_string,control,start,end)
        
        circuit.x(qubit_string)
        
    def sumsubtract1(self,circuit,qubit_string,control,start,end,move_value):
        '''
        Outputs:
        Sum/subtracts register 2 (control, 1 qubit) from register 1 (qubit_string) in register 1. Tested ok.

        Input:
        circuit: QuantumCircuit with registers qubit_string, control, ancilla and move_value
        qubit_string: QuantumRegister where the sum/subtraction is performed
        control: Qubit. Use ancilla[0] or similar. It encodes the probability of change.
        start: Qubit. Use ancilla[1] or similar
        end: Qubit. Use ancilla[2] or similar
        move_value: 1 to subtract, 0 to sum

        Comments: In binary, subtracting is the same procedure as summing when we exchange 0s and 1s
        '''
        circuit.cx(move_value,qubit_string)

        self.sum1(circuit,qubit_string,control,start,end)

        circuit.cx(move_value,qubit_string)

    def coin_flip(self, circuit,ancilla,coin):
        '''
        Prepares the coin with the probability encoded in the ancilla.
        The important thing to notice is that we are using the same convention as qiskit: littleendian.
        That means that the larger the index of the ancilla bit, the more significant it is, and the larger the rotation
        '''
        
        #Necesitamos usar el número guardado en las ancillas para realizar rotaciones controladas.  
        #Notice that ancilla encodes 1-probability, rather than probability.
        #Notice also that cu3(theta) rotates theta/2. As the first angle to rotate is pi/4 we need to start in theta = pi/2

        circuit.x(coin) # Start in 1 and decrease it, since we encoded the angle corresponding 1-probability
        for i in range(ancilla.size-1,-1,-1): # See how to perform an rx rotation in https://qiskit.org/documentation/stubs/qiskit.circuit.library.U3Gate.html
            circuit.cu(theta = -math.pi*2**(i-ancilla.size), phi  = 0, lam = 0, gamma = 0, control_qubit = ancilla[i], target_qubit = coin)
    
    def coin_flip_func_n(self, oracle_gate):
        
        '''
        Defines de coin_flip_gate using the oracle that is provided on the moment.
        Notice that oracle gate has registers oracle.variable_register and oracle.output_register in that order
        oracle.variable_register should have size angle_phi.size + angle_psi.size + move_id.size + move_value.size
        oracle.output_register should have size self.probability_bits
        '''

        # Let us create a circuit for coin_flip
        cf_angles = []
        for i in range(self.n_angles):
            cf_angles.append(QuantumRegister(self.angle_precision_bits, name = 'angle' + str(i)))
        cf_move_id = QuantumRegister(self.move_id_len) 
        cf_move_value = QuantumRegister(1)
        cf_coin = QuantumRegister(1)
        cf_ancilla = QuantumRegister(self.probability_bits)

        cf_circ = QuantumCircuit(cf_ancilla,cf_coin,cf_move_value,cf_move_id)
        for i in range(self.n_angles-1,-1,-1):
            cf_circ.add_register(cf_angles[i])


        # Main operations
                
        cf_circ.append(oracle_gate, [cf_move_value[0]]+[cf_move_id[j] for j in range(cf_move_id.size)] + 
                                    [cf_angles[k][j] for (k,j) in product(range(self.n_angles-1,-1,-1), range(self.angle_precision_bits))] + 
                                    [cf_ancilla[j] for j in range(self.probability_bits)])

        self.coin_flip(cf_circ,cf_ancilla,cf_coin)

        cf_circ.append(oracle_gate.inverse(), [cf_move_value[0]]+[cf_move_id[j] for j in range(cf_move_id.size)]+
                                              [cf_angles[k][j] for (k,j) in product(range(self.n_angles-1,-1,-1), range(self.angle_precision_bits))]+ 
                                              [cf_ancilla[j] for j in range(self.probability_bits)])

        coin_flip_gate = cf_circ.to_instruction()
        
        return coin_flip_gate

    def W_func_n(self, oracle):
        
        '''This defines the parametrised gate W using the oracle that is provided to it, and we can reuse its inverse too.'''

        # State definition. All angles range from 0 to 2pi
        w_angles = []
        for i in range(self.n_angles):
            w_angles.append(QuantumRegister(self.angle_precision_bits, name = 'angle' + str(i)))

        # Move proposal
        w_move_id = QuantumRegister(self.move_id_len, name = 'move_id') #Which angle are we modifying
        w_move_value = QuantumRegister(1, name = 'move_value') #0 -> decrease the angle. 1-> increase it

        # Coin
        w_coin = QuantumRegister(1, name = 'coin')

        # Ancillas
        w_ancilla = QuantumRegister(self.probability_bits, name = 'ancilla')

        # Circuit
        qc = QuantumCircuit(w_ancilla,w_coin,w_move_value,w_move_id)
        for i in range(self.n_angles-1,-1,-1):
            qc.add_register(w_angles[i])

        
        # Define the coin_flip_gate
        coin_flip_gate = self.coin_flip_func_n(oracle)

        # Move preparation
        qc.append(self.move_preparation_gate, [w_move_value[0]]+[w_move_id[j] for j in range(self.move_id_len)])
        
        # Coin flip    
        qc.append(coin_flip_gate,  [w_ancilla[j] for j in range(self.probability_bits)]+[w_coin[0],w_move_value[0]]+ [w_move_id[j] for j in range(self.move_id_len)]+[w_angles[k][j] for (k,j) in product(range(self.n_angles-1,-1,-1), range(self.angle_precision_bits))])

        # Conditional move
        qc.append(self.conditional_move_gate_n, [w_ancilla[j] for j in range(self.probability_bits)]+[w_coin[0],w_move_value[0]]+ [w_move_id[j] for j in range(self.move_id_len)]+[w_angles[k][j] for (k,j) in product(range(self.n_angles-1,-1,-1), range(self.angle_precision_bits))])

        # Inverse coin flip
        qc.append(coin_flip_gate.inverse(),[w_ancilla[j] for j in range(self.probability_bits)]+[w_coin[0],w_move_value[0],]+ [w_move_id[j] for j in range(self.move_id_len)]+[w_angles[k][j] for (k,j) in product(range(self.n_angles-1,-1,-1), range(self.angle_precision_bits))])

        # Inverse move preparation
        qc.append(self.move_preparation_gate.inverse(), [w_move_value[0]]+[w_move_id[j] for j in range(self.move_id_len)])

        # Reflection
        qc.append(self.reflection_gate, [w_coin[0],w_move_value[0]]+[w_move_id[j] for j in range(self.move_id_len)])

        W_gate = qc.to_instruction()
        
        return W_gate

    def U_func_n(self):
        
        '''
        This defines the gate U that initially spreads the output of minifold, and we can reuse its inverse too.
        It is basically the gate W but with the coin flip being sin^2 (theta = pi/6) = 1/4 probability of acceptance
        '''

        # State definition. All angles range from 0 to 2pi
        u_angles = []
        for i in range(self.n_angles):
            u_angles.append(QuantumRegister(self.angle_precision_bits, name = 'angle' + str(i)))

        # Move proposal
        u_move_id = QuantumRegister(self.move_id_len, name = 'move_id') #Which angle are we modifying
        u_move_value = QuantumRegister(1, name = 'move_value') #0 -> decrease the angle. 1-> increase it

        # Coin
        u_coin = QuantumRegister(1, name = 'coin')

        # Ancillas
        u_ancilla = QuantumRegister(self.probability_bits, name = 'ancilla')

        # Circuit
        qc = QuantumCircuit(u_ancilla, u_coin, u_move_value,u_move_id)
        for i in range(self.n_angles-1,-1,-1):
            qc.add_register(u_angles[i])


        # Move preparation
        qc.append(self.move_preparation_gate, [u_move_value[0]]+ [u_move_id[j] for j in range(self.move_id_len)])
        
        # Coin flip: equivalent to rx: https://qiskit.org/documentation/stubs/qiskit.circuit.library.U3Gate.html
        qc.u( theta =  math.pi/2, phi = 0, lam = 0, qubit=u_coin)

        # Conditional move
        qc.append(self.conditional_move_gate_n, [u_ancilla[j] for j in range(self.probability_bits)]+[u_coin[0],u_move_value[0]]+ [u_move_id[j] for j in range(self.move_id_len)]+[u_angles[k][j] for (k,j) in product(range(self.n_angles-1,-1,-1), range(self.angle_precision_bits))])

        # Inverse coin flip
        qc.u( theta = math.pi/2, phi = 0, lam = 0, qubit=u_coin).inverse()

        # Inverse move preparation
        qc.append(self.move_preparation_gate.inverse(), [u_move_value[0]]+ [u_move_id[j] for j in range(self.move_id_len)])

        # Reflection
        qc.append(self.reflection_gate, [u_coin[0],u_move_value[0]]+[u_move_id[j] for j in range(self.move_id_len)])

        U_gate = qc.to_instruction()
        
        return U_gate

    def execute_quantum_metropolis_n(self, initial_step, nW):

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
        g_ancilla = QuantumRegister(self.probability_bits, name = 'ancilla')

        # Circuit
        qc = QuantumCircuit(g_ancilla,g_coin,g_move_value,g_move_id)
        for i in range(self.n_angles-1,-1,-1):
            qc.add_register(g_angles[i])

        # If initialization is totally mixed use
        if self.initialization == 'random':
            for g_angle in g_angles:
                qc.h(g_angle)
        elif self.initialization == 'minifold': # The minifold initialization initializes each angle from a VonMises distribution.
            
            # Notice that this initialization is efficient even in quantum computers if we used the Grover-Rudolph algorithm.
            initial_angle_amplitudes, _ = self.tools.von_mises_amplitudes(n_qubits = self.angle_precision_bits, kappa = self.kappa)
            for g_angle in g_angles:
                qc.initialize(initial_angle_amplitudes, g_angle)

        oracle_generator = beta_precalc_TruthTableOracle.Beta_precalc_TruthTableOracle(self.input_oracle, in_bits = self.n_angles*self.angle_precision_bits + self.move_id_len + 1, out_bits = self.probability_bits)
        #list_gates.append(W_gate) # We deepcopy W_gate to not interfere with other calls
        if self.beta_type == 'fixed':

            #It creates one different oracle for each beta
            oracle = oracle_generator.generate_oracle(self.oracle_option, self.beta)

        snapshot_labels = []
        for i in range(initial_step-1, nW):

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

            if i >= self.initial_step:
                label = str(i)
                qc.save_statevector(label = label)
                snapshot_labels.append(label)

        start_time = time.time()

        backend = AerSimulator(method = 'statevector')

        result = backend.run(transpile(qc, backend)).result()

        time_statevector = time.time() - start_time

        # Extract probabilities in the measurement of the angles phi and psi
        #probabilities = state.probabilities([j+self.probability_bits+2+self.move_id_len for j in range(self.angle_precision_bits * self.n_angles)])

        probs = {}
        number_bits_angles = self.angle_precision_bits * self.n_angles

        for label in snapshot_labels:
            int_i = int(label)
            probs[int_i] = {}

            state_vector = Statevector(result.data(0)[label])

            total_bits = state_vector.num_qubits
            angle_qubits = [qubit_index for qubit_index in range ((total_bits - number_bits_angles), total_bits)]
            probabilities = state_vector.probabilities(angle_qubits)
        
            for index_probabilites in range(2**(self.angle_precision_bits *self.n_angles)):

                key = self.convert_index_to_key(index_probabilites, self.angle_precision_bits, self.n_angles)
                probs[int_i][key] = probabilities[index_probabilites]#.as_integer

        probs = OrderedDict(sorted(probs.items()))

        return [probs, time_statevector]

    # this method converts the index returned by statevector into a string key. 
    # for example: key 10 is converted to 22 if there are two angles and two precision bits
    # for example: key 8 is converted to 0010 if there are four angles and three precision bits
    def convert_index_to_key(self, key_int, precision_bits, n_angles):

        key_str = ''

        # iterate over the number of angles
        for index_angle in range(n_angles):

            # generate a denominator to divide the key_int (integer key)
            # this denominator is equivalent to the 'weight' of this angle position
            # for example, if there are 4 angles, it goes to the first angle (from left) and calculate the denominator
            # then it goes to the next angle and calculate the new denominator
            denominator = 2**(precision_bits*((n_angles-1) - index_angle))

            result = int(key_int/denominator)
            key_str += str(result)
            
            # if not the last step, include a character to separate the angles
            if index_angle != n_angles-1:
                key_str += '-'

            # the key_int value is necessary to be updated
            key_int -= result * denominator

        return key_str

class ClassicalMetropolis():

    def __init__(self, number_angles, deltas_dict, initialization, bits, tools):

        self.tools = tools

        # self.initialization = tools.args.initialization
        self.initialization = initialization
        # self.bits_rotation = tools.args.bits
        self.bits_rotation = bits
        # self.mode = tools.args.mode
        self.beta = tools.config_variables['beta']
        self.beta_type = tools.config_variables['beta_type']
        self.kappa = tools.config_variables['kappa']
        self.alpha = tools.config_variables['alpha']
        self.annealing_schedule = tools.config_variables['annealing_schedule']
        self.w_real_mode = tools.config_variables['w_real_mode']

        self.deltas_dict = deltas_dict
        self.number_angles = int(number_angles/2)
        self.rotation_steps = 2**self.bits_rotation
        self.bits_number_angles = math.ceil(np.log2(self.number_angles))

        self.n_iterations = tools.config_variables['number_iterations'] * (self.rotation_steps ** self.number_angles)

    def execute_metropolis(self, nW):

        probabilities_matrix = {}
        for _ in range(self.n_iterations):
            
            [phi, psi] = self.calculate_metropolis_result(nW)
        
            # it is necessary to construct the key from the received phi/psi (from the classical metropolis)
            # the idea is to add 1/n_repetitions to the returned value (to get the normalized number of times that this phi/psi was produced)
            position_angles = ''
            for index in range(len(phi)): position_angles += str(phi[index]) + '-' + str(psi[index]) + "-"
            position_angles = position_angles[:-1]

            # if the is already created, sum the entry to the dict, else create the entry
            if position_angles in probabilities_matrix.keys():
                probabilities_matrix[position_angles] += (1/self.n_iterations) 
            else:
                probabilities_matrix[position_angles] = (1/self.n_iterations)

        return probabilities_matrix

    def calculate_metropolis_result(self, nW):

        #Final structure calculated with metropolis. This variable will be returned to angle calculator

        # Data structure with the rotatation (0-rotation steps) of each phi/psi angle
        # for example, if there are 3 aminoacids, there are two phis and two psi
        # the data structure for phis contains two positions the rotation for first phi and for the second phi, etc.
        anglePhi_old = []
        anglePsi_old = []

        if self.initialization == 'random' or self.initialization == 'original':

            for _ in range(self.number_angles):

                # Random initialization of angles
                anglePsi_old.append(np.random.choice(self.rotation_steps))
                anglePhi_old.append(np.random.choice(self.rotation_steps))

        elif self.initialization == 'minifold':

            _, accumulated_probs = self.tools.von_mises_amplitudes(n_qubits = self.bits_rotation, kappa = self.kappa)

            for _ in range(self.number_angles):

                # Random initialization of angles
                r = np.random.random()
                for i in range(self.rotation_steps):
                    if accumulated_probs[i] >= r:
                        anglePhi_old.append(i)
                        break

                r = np.random.random()
                for i in range(self.rotation_steps):
                    if accumulated_probs[i] >= r:
                        anglePsi_old.append(i)
                        break

        for i in range(1, nW+1):

            anglePhi_new, anglePsi_new, change_angle, position_angle, change_plus_minus = self.generate_new_angles(anglePhi_old, anglePsi_old)
            position_angle_binary = np.binary_repr(position_angle, width = self.bits_number_angles)            

            binary_key = ''
            for index in range(len(anglePhi_new)):

                # binary key should contain: phi_1 | psi_1 | phi_2 | psi_2 | ...
                binary_key += np.binary_repr(anglePhi_old[index], width = self.bits_rotation)
                binary_key += np.binary_repr(anglePsi_old[index], width = self.bits_rotation)

            # This choice of Delta_E seems weird.
            # Correspondingly: (state = angle_phi, angle_psi...) +  (move_id = phi/psi+  position_angle_binary) +  move_value
            beta_value = 0
            if self.beta_type == 'fixed':
                beta_value = self.beta
            elif self.beta_type == 'variable':
                if self.annealing_schedule == 'Cauchy' or self.annealing_schedule == 'linear':
                    beta_value = self.beta * i 
                elif self.annealing_schedule == 'Boltzmann' or self.annealing_schedule == 'logarithmic':
                    beta_value = self.beta * np.log(i) + self.beta
                elif self.annealing_schedule == 'geometric':
                    beta_value = self.beta * self.alpha**(-i+1)
                elif self.annealing_schedule == 'exponential': 
                    space_dim = self.number_angles
                    beta_value = self.beta * np.exp( self.alpha * (i-1)**(1/space_dim) )
                else:
                    raise ValueError('<*> ERROR: Annealing Scheduling wrong value. It should be one of [linear, logarithmic, geometric, exponential] but it is', self.annealing_schedule)
            else:
                ValueError('<*> ERROR: Beta type wrong value. Beta type should be variable or fixed but it is', self.beta_type)

            Delta_E = self.deltas_dict[binary_key + str(change_angle) + position_angle_binary + str(change_plus_minus)]
            if Delta_E >= 0:
                probability_threshold = math.exp(-beta_value * Delta_E)
            else:
                probability_threshold = 1

            random_number = np.random.random_sample()

            # We should accept the change if probability_threshold > 1 (the energy goes down) or if beta is small.
            # If beta small, np.exp(-beta*Delta_E) approx 1.
            if random_number < min(1,probability_threshold): # Accept the change
                anglePhi_old = copy.deepcopy(anglePhi_new)
                anglePsi_old = copy.deepcopy(anglePsi_new)

        return [anglePhi_old, anglePsi_old]
    
    def generate_new_angles(self, anglePhi_old, anglePsi_old):
        # initially the new angles are equal to the old (then one angle will be randomly modified)
        # deep copy is necessary to avoid two pointer to the same data structure (it is necessary only to modify one of the arrays)
        anglePhi_new = copy.deepcopy(anglePhi_old)
        anglePsi_new = copy.deepcopy(anglePsi_old)
        
        # Propose a change
        # 0 = phi | 1 = psi
        change_angle = np.random.choice((0,1))

        # number of angle (it is possible to have more than one phi/psi)
        position_angle = np.random.choice(self.number_angles)

        # 0 = 1 | 1 = -1
        change_plus_minus = np.random.choice((0,1))
        pm = -2*change_plus_minus + 1

        # Calculate the new angles
        if change_angle == 0:
            #Change just +1 or -1 step in the energies dictionary
            anglePhi_new[position_angle] = (anglePhi_old[position_angle] + pm) % self.rotation_steps
        elif change_angle == 1:
            #Change just +1 or -1 step in the energies dictionary
            anglePsi_new[position_angle] = (anglePsi_old[position_angle] + pm) % self.rotation_steps

        return anglePhi_new, anglePsi_new, change_angle, position_angle, change_plus_minus