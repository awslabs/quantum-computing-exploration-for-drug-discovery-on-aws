import json
import math
import numpy as np

class Energy_Calculator():

    def __init__(self, input_filename, output_filename, precalculated_energies_path, basis, energy_method):

        self.input_filename = input_filename
        self.output_filename = output_filename
        self.precalculated_energies_path = precalculated_energies_path
        self.basis = basis
        self.energy_method = energy_method

    def calculate_energy_of_rotations(self, copied_atoms):

        #Write the file with the actual rotations
        self.write_file_energies(copied_atoms)

        #Calculate the energy of the actual rotations using PSI4
        self.execute_psi_command()

        #Read the PSI4 output file and get the energy
        energy = self.read_energy_from_psi4_file()

        return energy
    
    def execute_psi_command():

        # execute psi4 by command line (it generates the file output.dat with the information)
        return NotImplementedError
    
    def write_file_energies(self, atoms):

        #Write file with all atoms rotated
        rotationHandle = open(self.input_filename+'.dat', 'w')

        rotationHandle.write('molecule glycylglycine{\n')
        #write input.dat with all rotated atoms
        for at in atoms:
            rotationHandle.write(" " + at.element + " " + str(at.x) + " " + str(at.y) + " " + str(at.z)+'\n')
        
        rotationHandle.write('}\n\n')
        rotationHandle.write('set basis ' +  self.basis + '\n')
        rotationHandle.write("set reference rhf\n")
        rotationHandle.write("energy('" + self.energy_method + "')\n")

        rotationHandle.close()

    def read_energy_from_psi4_file(self):

        energy = 0
        with open(self.output_filename+'.dat', 'r') as filehandle:
            for line in filehandle:

                #If the PSI4 algorithm converges
                if 'Final Energy' in line:
                    energy = float(line.split(':')[1])
                
                #If the PSI4 algorithm does not converge, the energy used is the calculated in the last iteration (iteration 100)
                if 'iter 100:' in line:
                    energy = float(line.split()[3])

        return energy
    
    #This method returns the json with all rotations and energies associated to these rotations
    def calculate_all_deltas_of_rotations(self, atoms, aminoacids, min_energy_psi4, proteinName, numberBitsRotation, method_rotations_generation, backbone):

        rotationSteps = pow(2, int(numberBitsRotation))
        
        # it calculates the number of necessary bits to represent the number of angles
        # example, 4 aminoacids: 3 phis/psis => 2 bits
        bits_number_angles = math.ceil(np.log2(len(aminoacids)-1))

        print('    ⬤ Calculating energies for all posible rotations')
        number_angles = 2*(len(aminoacids)-1)
        energies = self.calculate_all_energies(atoms, rotationSteps, number_angles, number_angles, aminoacids)

        #Write the headers of the energies json that is going to be returned
        deltas_json = {}
        deltas_json['protein'] = proteinName
        deltas_json['numberBitsRotation'] = numberBitsRotation
        deltas_json['psi4_min_energy'] = min_energy_psi4
        deltas_json['deltas'] = {}

        print('    ⬤ Calculating deltas for all possible combinations of rotations')

        min_energy = 99999
        index_min_energy = -1  
        # iterates over all calculated energies using the keys (contains the values of the phi/psi angles)      
        for e_key in energies.keys():

            old_energy = energies[e_key]

            # check if the energy is lower than the minimum
            if old_energy < min_energy:
                min_energy = old_energy
                index_min_energy = e_key
            
            angle_keys = e_key.split(' ')
            # iterate over all angles keys
            for index_a_key in range(len(angle_keys)):

                # calculate the plus/minus 1 rotation delta
                for plusminus in [0,1]:
                    pm = (-2)*plusminus + 1

                    new_value = (int(angle_keys[index_a_key]) + pm) % (2**numberBitsRotation)

                    # create a key with the values of the angles (if the index is equal to the index of the modified angle, insert the modified one)
                    angle_key = ''
                    binary_key = ''
                    for index_key in range(len(angle_keys)):

                        binary_key += np.binary_repr(int(angle_keys[index_key]), width = numberBitsRotation)

                        if index_key == index_a_key:
                            angle_key += str(new_value)+ ' '
                        
                        else:
                            angle_key += angle_keys[index_key] + ' '

                    new_energy = energies[angle_key.strip()]

                    # add 0/1 for phi/psi
                    if index_a_key % 2 == 0:
                        # if it is even number is phi (add 0)
                        binary_key += str(0)
                    else:
                        # if it is odd number is psi (add 1)
                        binary_key += str(1)
                    
                    # add the index of the phi/psi angle (with more than 2 aminoacids, there are more than one phi/psi)
                    binary_key += np.binary_repr(int(index_a_key/2), width = bits_number_angles)

                    # add 0/1 for plus/minus
                    binary_key += str(plusminus)

                    delta = new_energy - old_energy
                    
                    #Add the values to the file with the precalculated energies
                    deltas_json['deltas'][binary_key] = delta

        deltas_json['initial_min_energy'] = min_energy
        deltas_json['index_min_energy'] = index_min_energy.replace(' ', '-')

        return deltas_json
    
    def write_json(self, json_data, file_name, proteinName, numberBitsRotation, method_rotations_generation):

        #Create json with calculated energies
        #TODO: extract the path to a config file
        with open(self.precalculated_energies_path+file_name+'_'+proteinName+'_'+str(numberBitsRotation)+'_'+method_rotations_generation+'.json', 'w') as outfile:
            json.dump(json_data, outfile)

    def read_energy_json(self, proteinName, numberBitsRotation, method_rotations_generation):

        with open(self.precalculated_energies_path + 'delta_energies_'+proteinName+'_'+str(numberBitsRotation)+'_'+method_rotations_generation+'.json') as json_file:
            data = json.load(json_file)

            return [data['deltas'], data['psi4_min_energy'], data['initial_min_energy'], data['index_min_energy'], data['initialization_stats']]

        