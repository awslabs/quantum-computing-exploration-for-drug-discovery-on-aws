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
import qiskit
from qiskit import QuantumCircuit, execute, Aer, IBMQ
from qiskit.circuit import QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Statevector
from qiskit.compiler import transpile

import beta_precalc_TruthTableOracle

# Import measurement calibration functions
import scipy

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

        # # The delta E's dictionary

        # if self.tools.args.mode == 'experiment':
        #     self.device = self.login_ibmq()
        # elif self.tools.args.mode == 'simulation' or self.tools.args.mode == 'real':
        #     self.device = Aer.get_backend('statevector_simulator')
        #     self.backend_options = {"method" : "statevector"}

        # For n angles
        [self.move_preparation_gate, self.conditional_move_gate_n, self.reflection_gate] = self.prepare_initial_circuits_n()

    def login_ibmq(self):

        #read the file that contains the Qiskit user API
        with open(self.qiskit_api_path) as json_file:
            api_token = json.load(json_file)['qiskit_token']

        if api_token == '':
            print('<*> ERROR!! It is necessary to introduce an qiskit API token')

        IBMQ.save_account(api_token, overwrite=True)
        IBMQ.load_account()

        self.provider = IBMQ.get_provider(hub=self.tools.config_variables['hub'],
                                        group=self.tools.config_variables['group'], 
                                        project=self.tools.config_variables['project'])

        self.backend = self.provider.get_backend(self.selected_device)
        
        return self.backend

    def move_preparation(self, circuit,move_value,move_id):
        '''
        Proposes new moves
        '''
        circuit.h(move_value) #Es un único bit que puede ser 0 para + y 1 para -
        if bin(self.n_angles).count('1') == 1: # if the number of angles is a power of two: dipeptides and tripeptides
            circuit.h(move_id)
        elif self.n_angles == 6: # For tetrapeptides
            circuit.u3(theta = 2* np.arcsin(np.sqrt(1/3)), phi = 0, lam = 0, qubit=move_id[2])
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
            sub_circ = sub_circ + QuantumCircuit(s_angles[i])

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
            circuit.cu3(theta = -math.pi*2**(i-ancilla.size), phi  = 0, lam = 0, control_qubit = ancilla[i], target_qubit = coin)
    
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
            cf_circ = cf_circ + QuantumCircuit(cf_angles[i])


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
            qc = qc + QuantumCircuit(w_angles[i])

        
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
            qc = qc + QuantumCircuit(u_angles[i])


        # Move preparation
        qc.append(self.move_preparation_gate, [u_move_value[0]]+ [u_move_id[j] for j in range(self.move_id_len)])
        
        # Coin flip: equivalent to rx: https://qiskit.org/documentation/stubs/qiskit.circuit.library.U3Gate.html
        qc.u3( theta =  math.pi/2, phi = 0, lam = 0, qubit=u_coin)

        # Conditional move
        qc.append(self.conditional_move_gate_n, [u_ancilla[j] for j in range(self.probability_bits)]+[u_coin[0],u_move_value[0]]+ [u_move_id[j] for j in range(self.move_id_len)]+[u_angles[k][j] for (k,j) in product(range(self.n_angles-1,-1,-1), range(self.angle_precision_bits))])

        # Inverse coin flip
        qc.u3( theta = math.pi/2, phi = 0, lam = 0, qubit=u_coin).inverse()

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
            qc = qc + QuantumCircuit(g_angles[i])

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

    ####### FOR THE REAL HARDWARE OPTION ###########

    def execute_real_hardware(self, nWs):

        start_time = time.time()
        shots = self.tools.config_variables['ibmq_shots']
        n_repetitions = self.tools.config_variables['number_repetitions_ibmq']
        n_repetitions_zero_beta = self.tools.config_variables['number_repetitions_ibmq_zero_beta']

        # prepare dictionary with deltas
        deltas_dictionary = collections.OrderedDict(sorted(self.input_oracle.items()))
        deltas = {}
        for (key,value) in deltas_dictionary.items():
            deltas[key[:3]] = value
        
        counts = {}
        measures_dict = {}

        # First we load all the previous results so that for beta = 0 we do not have to recalculate more than necessary
        with open('./results/measurements.json', 'r') as outfile2: 
            dictionary = json.load(outfile2)

        try: # the dictionary has the form dictionary['--']['0-0']['measurements'] = {'00': [1329,3213 ...], '01':...}
            beta0_counts = dictionary['--']['0-0']['measurements'] 
            len_beta0_counts00  = len(beta0_counts['00'])

            if len_beta0_counts00 >= n_repetitions_zero_beta:
                measures_dict['0-0'] = beta0_counts
                runs = [1]

            else:
                beta0_n_repetitions = n_repetitions_zero_beta - len_beta0_counts00
                runs = range(2)

        except:
            beta0_counts = {'00': [], '01':[], '10':[], '11':[]}
            beta0_n_repetitions = n_repetitions_zero_beta
            runs = range(2)

        
        # Then we execute the needed runs
        for index in runs:

            # in the first iteration (index=0) it uses the betas = 0. In the second iteration, it uses the betas of the config file
            if index == 0:
                betas = [1e-10,1e-10]
                key_name_counts = 'betas=0'
                reps = beta0_n_repetitions  
            
            else:
                betas = self.tools.config_variables['betas']
                key_name_counts = 'betas=betas'
                reps = n_repetitions

            counts[key_name_counts] = {}
            # Let us first analyse the noise of the circuit for the ideal case of betas = 0, which should imply .25 chance of success
            qc = self.generate_circ(nWs, deltas, betas)
            

            # get the NOISELESS counts
            counts[key_name_counts]['noiseless'] = self.exe_noiseless(nWs)

            # get the RAW counts
            raw_counts = []
            for i in range(reps):
                print("<i> Waiting to get access to IBMQ processor. Betas = ", betas, ". Iteration = ",i)
                #raw_counts.append(execute(qc, self.backend, shots=shots).result().get_counts())
                raw_counts.append(execute(qc, Aer.get_backend('qasm_simulator'), shots=shots).result().get_counts())
                print("<i> Circuit in IBMQ executed")

            if index == 0: # Notice that we will add here the measurements for beta =0 already saved in results.json
                measures_dict['0-0']= self.tools.list_of_dict_2_dict_of_lists(raw_counts, beta0_counts = beta0_counts)
            else:
                measures_dict[str(betas[0]) + '-' +str(betas[1])]= self.tools.list_of_dict_2_dict_of_lists(raw_counts)

            # sum all values of the same position and get the mean of each position to store in counts
            raw_counts = dict(functools.reduce(operator.add, map(collections.Counter, raw_counts)))
            raw_counts = {k:v/n_repetitions for k,v in raw_counts.items()}
            counts[key_name_counts]['raw'] = raw_counts


        # In order to see if there is some statistical difference between the two noise circuit (due to the value of beta and the angles)
        # we generate bernouilli distribuitions that follow the same statistics as those that we have measured
        betas = self.tools.config_variables['betas']
        print('measures_dict',measures_dict)
        beta0_bernouilli = self.generate_bernouilli(int(sum(measures_dict['0-0']['00'])), shots*len(measures_dict['0-0']['00']))
        beta1_bernouilli = self.generate_bernouilli(int(sum(measures_dict[str(betas[0]) + '-' +str(betas[1])]['00'])), shots*len(measures_dict[str(betas[0]) + '-' +str(betas[1])]['00']))
        exec_stats, pvalue = scipy.stats.ttest_ind(beta0_bernouilli, beta1_bernouilli, equal_var=False)

        execution_stats = 'The t-test statistic value for there being a significat average difference between measured processes with beta zero and non-zero is ' + str(exec_stats) + ' and the corresponding pvalue is '+ str(pvalue)
        print('<i>', execution_stats)

        time_statevector = time.time() - start_time

        return [counts, time_statevector, execution_stats, measures_dict]

    def calculate_angles(self, deltas_dictionary, beta):
    
        exact_angles = {}

        for key in deltas_dictionary.keys():

            if deltas_dictionary[key] >= 0:
                probability = math.exp(-beta * deltas_dictionary[key])
            else: 
                probability = 1
            # Instead of encoding the angle corresponding to the probability, we will encode the angle theta such that sin^2(pi/2 - theta) = probability.
            # That way 1 -> 000, but if probability is 0 there is some small probability of acceptance

            # Instead of probability save angles so rotations are easier to perform afterwards sqrt(p) = sin(pi/2-theta/2).
            # The theta/2 is because if you input theta, qiskits rotates theta/2. Also normalised (divided between pi the result)
            exact_angles[key] = math.pi - 2 * math.asin(math.sqrt(probability))

        # Order angles by key
        exact_angles = collections.OrderedDict(sorted(exact_angles.items()))

        return exact_angles

    def simulated_hardware_1_coin_flip(self, circuit, coin, move_id, angle_psi, angle_phi, angles, inverse):
        ''' Applies the controlled rotation to the target coin'''
        if inverse == 1:
            circuit.x(coin)
        
        if angles['111'] > .01:
            circuit.mcrx(theta = -inverse * angles['111'], q_controls = [angle_phi[0],angle_psi[0],move_id[0]], q_target = coin[0], use_basis_gates=False)
        circuit.x(move_id)
        
        if angles['110'] > .01:
            circuit.mcrx(theta = -inverse * angles['110'], q_controls = [angle_phi[0],angle_psi[0],move_id[0]], q_target = coin[0], use_basis_gates=False)
        circuit.x(angle_psi)
        
        if angles['100'] > .01:
            circuit.mcrx(theta = -inverse * angles['100'], q_controls = [angle_phi[0],angle_psi[0],move_id[0]], q_target = coin[0], use_basis_gates=False)
        circuit.x(move_id)
        
        if angles['101'] > .01:
            circuit.mcrx(theta = -inverse * angles['101'], q_controls = [angle_phi[0],angle_psi[0],move_id[0]], q_target = coin[0], use_basis_gates=False)
        circuit.x(angle_phi)
        
        if angles['001'] > .01:
            circuit.mcrx(theta = -inverse * angles['001'], q_controls = [angle_phi[0],angle_psi[0],move_id[0]], q_target = coin[0], use_basis_gates=False)
        circuit.x(move_id)
        
        if angles['000'] > .01:
            circuit.mcrx(theta = -inverse * angles['000'], q_controls = [angle_phi[0],angle_psi[0],move_id[0]], q_target = coin[0], use_basis_gates=False)
        circuit.x(angle_psi)
        
        if angles['010'] > .01:
            circuit.mcrx(theta = -inverse * angles['010'], q_controls = [angle_phi[0],angle_psi[0],move_id[0]], q_target = coin[0], use_basis_gates=False)
        circuit.x(move_id)
        
        if angles['011'] > .01:
            circuit.mcrx(theta = -inverse * angles['011'], q_controls = [angle_phi[0],angle_psi[0],move_id[0]], q_target = coin[0], use_basis_gates=False) 
        circuit.x(angle_phi)
        
        if inverse == -1:
            circuit.x(coin)

    def hardware_1_coin_flip(self, circuit, coin, move_id, angle_psi, angle_phi, angles, inv):

        '''Warning! This only works for dipeptide 1 in experiment mode. Do not use elsewhere!'''
        # First we have to identify the non-zero angles. For the rest we accept with probability 1
        circuit.x(coin)
        '''
        Since the angles from 001 and 101 ~= 2.59; and those from 010 and 000 ~= 0.32 (when beta = .1, 
        but they'll always be similar nevertheless), we will perform those rotations together
        '''
        non_zero_angles = {}
        non_zero_angles['0x0'] = (angles['000']+angles['010'])/2
        non_zero_angles['x01'] = (angles['001']+angles['101'])/2
        
        # Let us first perform the first
        circuit.x(angle_phi)
        circuit.x(move_id)
        circuit.mcrx(theta = -inv*non_zero_angles['0x0'],
                    q_controls = [move_id[0],angle_phi[0]], q_target = coin[0], use_basis_gates=True)
        circuit.x(angle_phi)
        circuit.x(move_id)
        
        # Let us perform the second
        circuit.x(angle_psi)
        circuit.mcrx(theta = -inv*non_zero_angles['x01'],
                    q_controls = [move_id[0],angle_psi[0]], q_target = coin[0], use_basis_gates=True)
        circuit.x(angle_psi)

    def W_step(self, qc,coin,move_id,angle_psi,angle_phi,angles,nW,nWs): 
        
        # Perform the preparation of possible moves----
        qc.h(move_id)

        # Prepare the Boltzmann coin ------------------
        self.hardware_1_coin_flip(qc, coin, move_id, angle_psi, angle_phi, angles, inv = 1)
        
        # Perform move ---------------------------------
        # For the second angle
        qc.ccx(coin,move_id,angle_psi)

        # For the first angle
        qc.x(move_id)
        qc.ccx(coin,move_id,angle_phi)
        qc.x(move_id)

        if nW < nWs-1: # This happens unless we are in the last step, in which case uncomputing is unnecessary.
            # Unprepare the Boltzmann coin--------------------
            self.hardware_1_coin_flip(qc, coin, move_id, angle_psi, angle_phi, angles, inv = -1)

            # Perform the preparation of possible moves ----
            qc.h(move_id)

            #Reflection -------------------------------------
            qc.x(move_id)
            qc.x(coin)

            # Perform a multicontrolled Z
            qc.cz(move_id,coin)

            qc.x(move_id)
            qc.x(coin)

    def simulated_W_step(self, qc,coin,move_id,angle_psi,angle_phi,angles,nW,nWs):

        # Perform the preparation of possible moves----
        qc.h(move_id)

        # Prepare the Boltzmann coin ------------------
        self.simulated_hardware_1_coin_flip(qc, coin, move_id, angle_psi, angle_phi, angles, inverse = 1)
        
        # Perform move ---------------------------------
        # For the second angle
        qc.ccx(coin,move_id,angle_psi)

        # For the first angle
        qc.x(move_id)
        qc.ccx(coin,move_id,angle_phi)
        qc.x(move_id)

        if nW < nWs-1: # This happens unless we are in the last step, in which case uncomputing is unnecessary.
            # Unprepare the Boltzmann coin--------------------
            self.simulated_hardware_1_coin_flip(qc, coin, move_id, angle_psi, angle_phi, angles, inverse = -1)

            # Perform the preparation of possible moves ----
            qc.h(move_id)

            #Reflection -------------------------------------
            qc.x(move_id)
            qc.x(coin)

            # Perform a multicontrolled Z
            qc.cz(move_id,coin)

            qc.x(move_id)
            qc.x(coin)

    def generate_circ(self, nWs, deltas, betas):

        assert(len(betas) == nWs)
    
        move_id  = QuantumRegister(1)
        angle_phi = QuantumRegister(1)
        angle_psi = QuantumRegister(1)
        coin = QuantumRegister(1)
        c_reg = ClassicalRegister(2)
        qc = QuantumCircuit(coin,move_id,angle_psi,angle_phi,c_reg)

        #Circuit ----------
        qc.h(angle_phi)
        qc.h(angle_psi)
        for (i,beta) in zip(range(nWs),betas):
            angles = self.calculate_angles(deltas, beta)
            self.W_step(qc,coin,move_id,angle_psi,angle_phi,angles,nW = i, nWs = nWs)

        # Measure
        qc.measure(angle_phi[0], c_reg[1])
        qc.measure(angle_psi[0], c_reg[0])

        # Transpiling -------

        #layout = {5: angle_phi[0], 6: angle_psi[0], 4: move_id[0], 5: coin[0]}
        layout = {2: angle_psi[0], 3: angle_phi[0], 1: coin[0], 0: move_id[0]} 
        qc = transpile(qc, backend = self.backend, optimization_level=3, 
                    initial_layout=layout, basis_gates = ['u1', 'u2', 'u3', 'cx'], routing_method = 'lookahead')
        
        print('\n⬤⬤⬤⬤  Circuit stadistics after optimization  ⬤⬤⬤⬤\n')
        print('•  Gates = ', qc.count_ops())
        print('•  Depth = ', qc.depth())
        print('\n') 
        
        return qc

    def generate_hardware_simulation_circuit(self,nWs, deltas, betas):

        assert(len(betas) == nWs)
    
        move_id  = QuantumRegister(1)
        angle_phi = QuantumRegister(1)
        angle_psi = QuantumRegister(1)
        coin = QuantumRegister(1)
        c_reg = ClassicalRegister(2)
        aerqc = QuantumCircuit(coin,move_id,angle_psi,angle_phi,c_reg)

        #Circuit ----------
        aerqc.h(angle_phi)
        aerqc.h(angle_psi)
        for (i,beta) in zip(range(nWs),betas):
            angles = self.calculate_angles(deltas, beta)
            print('angles step',i,angles)
            self.simulated_W_step(aerqc,coin,move_id,angle_psi,angle_phi,angles,nW = i, nWs = nWs)
        
        return aerqc


    def exe_noiseless(self, nWs):

        betas = self.tools.config_variables['betas']

        # prepare dictionary with deltas
        deltas_dictionary = collections.OrderedDict(sorted(self.input_oracle.items()))
        deltas = {}
        for (key,value) in deltas_dictionary.items():
            deltas[key[:3]] = value

        print('deltas', deltas)

        aerqc = self.generate_hardware_simulation_circuit(nWs, deltas, betas)

        aerbackend = Aer.get_backend('statevector_simulator')
        backend_options = {"method" : "statevector"}
        experiment = execute(aerqc, aerbackend, backend_options=backend_options)
        state_vector = Statevector(experiment.result().get_statevector(aerqc))

        probabilities = state_vector.probabilities([2,3]) # We are reporting the angles as (psi,phi); since qiskit inverts the reporting order
        print('probabilities',probabilities)
        noiseless_counts = {}
        noiseless_counts['00'] = float(probabilities[0])
        noiseless_counts['01'] = float(probabilities[1])
        noiseless_counts['10'] = float(probabilities[2])
        noiseless_counts['11'] = float(probabilities[3])

        return noiseless_counts

    def generate_bernouilli(self, n_0, n):
        array = np.random.binomial(1, n_0/n, n)
        s = np.sum(array)
        while s != n_0:
            i = np.random.randint(n)
            if s<n_0 and array[i] == 0:
                array[i] = 1
            elif s>n_0 and array[i] == 1:
                array[i] = 0
            s = np.sum(array)
        return array    

    def executor(self, qc, n_iterations, shots, circuit = qiskit.QuantumCircuit):
        """Returns the expectation value to be mitigated.

        Args:
            circuit: Circuit to run.
            shots: Number of times to execute the circuit to compute the expectation value.
        """

        # (1) Run the circuit
        raw_counts = 0
        for i in range(n_iterations):
            print('iteration =',i)
            counts= execute(qc, self.backend, shots=shots, optimization_level=0).result().get_counts()
            raw_counts += counts['00']
            
        # (2) Convert from raw measurement counts to the expectation value    
        expectation_value = raw_counts/(shots*n_iterations)

        return expectation_value

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