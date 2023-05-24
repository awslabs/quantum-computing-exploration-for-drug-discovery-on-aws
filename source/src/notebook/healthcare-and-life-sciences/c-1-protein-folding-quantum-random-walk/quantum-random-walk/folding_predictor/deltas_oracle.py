from qiskit.circuit import QuantumRegister, QuantumCircuit
from collections import OrderedDict

import math
import numpy as np

class Deltas_Oracle():
    '''Outputs the binary angle of rotation to get the correct probability. Tested ok'''
    def __init__(self, deltas_dictionary, in_bits, out_bits):

        self.out_bits = out_bits
        self.deltas_dictionary = OrderedDict(sorted(deltas_dictionary.items()))

        # If there are only two angles, we need to eliminate the penultimate digit of the keys:
        if len(list(self.deltas_dictionary.keys())[0]) == in_bits + 1:
            deltas = {}
            for (key, value) in list(self.deltas_dictionary.items()):
                deltas[key[:-2]+key[-1]] = value
            self.deltas_dictionary = deltas

    def generate_oracle(self, beta):

        angles = self.generate_angles_codification(beta)
        oracle_circuit = self.generate_qfold_oracle(angles)

        return oracle_circuit.to_instruction()

    def generate_angles_codification(self, beta):

        angles = {}

        for key in self.deltas_dictionary.keys():

            if self.deltas_dictionary[key] >= 0:
                probability = math.exp(-beta * self.deltas_dictionary[key])
            else: 
                probability = 1
            # Instead of encoding the angle corresponding to the probability, we will encode the angle theta such that sin^2(pi/2 - theta) = probability.
            # That way 1 -> 000, but if probability is 0 there is some small probability of acceptance
            
            # Instead of probability save angles so rotations are easier to perform afterwards sqrt(p) = sin(pi/2-theta/2).
            # The theta/2 is because if you input theta, qiskits rotates theta/2. Also normalised (divided between pi the result)
            angle = 1 - 2/math.pi * math.asin(math.sqrt(probability))

            # Ensure that the angle stays minimally away from 1
            angle = np.minimum(angle, 1-2**(-self.out_bits-1))
            # Convert it into an integer and a string
            if angle == 1.:
                print('probability = ',probability)
                print('angle',angle)
                raise ValueError('Warning: angle seems to be pi/2, and that should not be possible')
            
            # angle will be between 0 and 1, so we move it to between 0 and 2^out_bits. Then calculate the integer and the binary representation
            angles[key] = np.binary_repr(int(angle*2**self.out_bits), width= self.out_bits)

        self.angles = angles

        return angles

    def generate_qfold_oracle(self, angles):

        # create a quantum circuit with the same length than the key of the deltas energies
        oracle_key = QuantumRegister(len(list(self.deltas_dictionary.keys())[0]))
        oracle_value = QuantumRegister(len(list(angles.values())[0]))
        oracle_circuit = QuantumCircuit(oracle_key, oracle_value)

        len_key = len(list(self.angles.keys())[0])

        for key in self.angles.keys():
            
            # apply x gates to the 0s in the key
            for key_bit_index in range(len(key)):
                if key[(len_key-1) - key_bit_index] == '0':
                    oracle_circuit.x(oracle_key[key_bit_index])

            # apply mcx gates with the 1s in the angles (control the whole key)
            angle = angles[key]
            for angle_bit_index in range(len(angle)):
                if angle[(len(angle)-1) - angle_bit_index] == '1':
                    oracle_circuit.mcx(oracle_key, oracle_value[angle_bit_index])

            # apply x gates to the 0s in the key
            for key_bit_index in range(len(key)):
                if key[(len_key-1) - key_bit_index] == '0':
                    oracle_circuit.x(oracle_key[key_bit_index])

        return oracle_circuit