import copy
import math
import random
import numpy as np

from classical_ML_model import minifold

class Structure_Calculator():

    def __init__(self, model_path, window_size, max_aa_length, path_input_file, epochs_train_classical_folding_model, batch_size_classical_folding_model):

        self.model_path = model_path
        self.window_size = window_size
        self.max_aa_length = max_aa_length

        self.path_input_file = path_input_file
        self.epochs_train_classical_folding_model = epochs_train_classical_folding_model
        self.batch_size_classical_folding_model = batch_size_classical_folding_model
        

    def calculate_initial_structure(self, atoms, aminoacids, method_rotations_generation, backbone):

        phis_initial_rotation = []
        psis_initial_rotation = []

        # First we calculate all the angles. Psi uses the first atom from the next aminoacid, whereas phi uses the last from the previous
        psi_angles_psi4 = [self.calculate_angle(backbone[3*j:3*j+4],'psi') for j in range(len(backbone)//3 - 1)]
        phi_angles_psi4 = [self.calculate_angle(backbone[3*j-1:3*j+3],'phi') for j in range(1, len(backbone)//3)]
        
        
        #minifold
        print('\n## MINIFOLD initialization for protein structure ##\n')

        #Set angles to 0. PSI4 returns the optimal angles for the protein, so it is necessary to set these angles to 0
        atoms = self.flat_protein(atoms, backbone, phi_angles_psi4, psi_angles_psi4)

        mfold = minifold.Minifold(self.model_path, self.window_size, self.max_aa_length, self.path_input_file, self.epochs_train_classical_folding_model, self.batch_size_classical_folding_model)
        angles = mfold.predictAngles(aminoacids)

        for angle in angles:

            phis_initial_rotation.append(angle[0])
            psis_initial_rotation.append(angle[1])

        #Rotate all angles to get the initial protein structure
        if method_rotations_generation != 'original':

            for index in range(len(phis_initial_rotation)):

                self.rotate(angle_type = 'psi', angle = psis_initial_rotation[index], starting_atom = backbone[3*index+2], backbone = backbone)
                self.rotate(angle_type = 'phi', angle = phis_initial_rotation[index], starting_atom = backbone[3*index+4], backbone = backbone) 

        #Calculate the precision in constrast of the real value calculated by psi4
        [phis_precision, psis_precision] = self.calculate_precision_of_angles(phi_angles_psi4, psi_angles_psi4, phis_initial_rotation, psis_initial_rotation)

        # if it is necessary convert float32 in standard python type (float32 is not serializable by json)
        print(phis_initial_rotation, psis_initial_rotation)
        if type(phis_initial_rotation[0]) is np.float32:
            phis_initial_rotation = [value.item() for value in phis_initial_rotation]
        
        if type(psis_initial_rotation[0]) is np.float32:
            psis_initial_rotation = [value.item() for value in psis_initial_rotation]

        # phis/psis initial rotation is a float 32 and it is not serializable by the json, so it is necessary to convert to a native type of python
        initialization_stats = {
            'phis_precision': phis_precision, 
            'psis_precision': psis_precision, 
            'phi_angles_psi4': phi_angles_psi4, 
            'psi_angles_psi4': psi_angles_psi4, 
            'phis_initial_rotation': phis_initial_rotation,
            'psis_initial_rotation': psis_initial_rotation
            }

        return [atoms, initialization_stats]
    
    def calculate_angle(self, angle_atoms, angle_type):
        'Uses get dihedral to calculate angles between atoms'
        if angle_type == 'phi':
            # For angle phi we take the last atom of the previous aminoacid
            assert(angle_atoms[0].c_type == 'Carboxy' and angle_atoms[1].c_type == 'N_backbone' and angle_atoms[2].c_type =='C_alpha' and angle_atoms[3].c_type == 'Carboxy')
            assert(angle_atoms[0] in angle_atoms[1].linked_to and angle_atoms[1] in angle_atoms[2].linked_to and angle_atoms[2] in angle_atoms[3].linked_to)
            coords1 = np.array([angle_atoms[0].x, angle_atoms[0].y, angle_atoms[0].z])
            coords2 = np.array([angle_atoms[1].x, angle_atoms[1].y, angle_atoms[1].z])
            coords3 = np.array([angle_atoms[2].x, angle_atoms[2].y, angle_atoms[2].z])
            coords4 = np.array([angle_atoms[3].x, angle_atoms[3].y, angle_atoms[3].z])

            return self.get_dihedral(coords1, coords2, coords3, coords4)

        elif angle_type == 'psi':
            # For angle psi we take the first atom of the next aminoacid
            assert(angle_atoms[0].c_type == 'N_backbone' and angle_atoms[1].c_type =='C_alpha' and angle_atoms[2].c_type == 'Carboxy' and angle_atoms[3].c_type == 'N_backbone')
            assert(angle_atoms[0] in angle_atoms[1].linked_to and angle_atoms[1] in angle_atoms[2].linked_to and angle_atoms[2] in angle_atoms[3].linked_to)
            coords1 = np.array([angle_atoms[0].x, angle_atoms[0].y, angle_atoms[0].z])
            coords2 = np.array([angle_atoms[1].x, angle_atoms[1].y, angle_atoms[1].z])
            coords3 = np.array([angle_atoms[2].x, angle_atoms[2].y, angle_atoms[2].z])
            coords4 = np.array([angle_atoms[3].x, angle_atoms[3].y, angle_atoms[3].z])

            return self.get_dihedral(coords1, coords2, coords3, coords4)

        else:
            raise('Angle not recognised!:'+str(angle_type))

    def flat_protein(self, atoms, backbone, phi_angles_psi4, psi_angles_psi4):

        # Next we need to flatten the peptide
        for i in range(len(psi_angles_psi4)):
            # For psi we have to rotate -angle starting in the carboxy of the i-th aminoacid
            self.rotate(angle_type = 'psi', angle = -1*psi_angles_psi4[i], starting_atom = backbone[3*i+2], backbone = backbone)
            # For phi we have to rotate -angle starting in the C_alpha of the (i+1)-th aminoacid
            self.rotate(angle_type ='phi', angle = -1*phi_angles_psi4[i], starting_atom = backbone[3*i+4], backbone = backbone)

        return atoms
    
    def rotate(self, angle_type, angle, starting_atom, backbone):

        previous_atom = backbone[backbone.index(starting_atom)-1]

        if angle_type == 'phi':
            if previous_atom.c_type != 'N_backbone' or starting_atom.c_type != 'C_alpha':
                raise Exception('Wrong starting atom for the angle phi:',starting_atom.c_type,'or wrong previous atom',previous_atom.c_type )
                    
        elif angle_type == 'psi':
            if previous_atom.c_type != 'C_alpha' or starting_atom.c_type != 'Carboxy':
                raise Exception('Wrong starting atom for the angle phi:',starting_atom.c_type )

        else:
            raise Exception('Angle not recognised!:',angle_type)
        
        # Define the list of atoms to rotate and then rotate them
        
        backbone2rotate = backbone[backbone.index(starting_atom)+1:]
        ##self.backbone_to_rotate(angle_type,starting_atom, backbone)
        list_of_atoms_to_rotate = self.decorations_to_rotate(backbone2rotate,backbone)

        for atom in list_of_atoms_to_rotate:
            # The axis is defined by the starting atom and the atom prior to the starting atom in the backbone
            atom.rotate(previous_atom, starting_atom, angle, angle_type)

    def get_dihedral(self, coords1, coords2, coords3, coords4):

        """Returns the dihedral angle in degrees."""

        a1 = coords2 - coords1
        a2 = coords3 - coords2
        a3 = coords4 - coords3

        v1 = np.cross(a1, a2)
        v1 = v1 / (v1 * v1).sum(-1)**0.5
        v2 = np.cross(a2, a3)
        v2 = v2 / (v2 * v2).sum(-1)**0.5
        porm = np.sign((v1 * a3).sum(-1))
        #Round the value to avoid 1.0000000000002 (python precision error)
        rad = np.arccos(round((v1*v2).sum(-1) / ((v1**2).sum(-1) * (v2**2).sum(-1))**0.5, 10))
        if not porm == 0:
            rad = rad * porm
        return rad

    def calculate_precision_of_angles(self, phi_angles_psi4, psi_angles_psi4, phis_initial_rotation, psis_initial_rotation):

        if len(phi_angles_psi4) != len(phis_initial_rotation) or len(psi_angles_psi4) != len(phis_initial_rotation):
            print('<*> ERROR: The number of generated angles (initialization) is different than the number of protein angles')

        phi_precisions = []
        psi_precisions = []

        angles_initial_rotation = [phis_initial_rotation, psis_initial_rotation]
        angles_psi4 = [phi_angles_psi4, psi_angles_psi4]
        
        # it calculates precision for phi (0) and psi(1)
        for phi_psi in [0,1]:

            for index in range(len(angles_psi4[phi_psi])):

                if angles_initial_rotation[phi_psi][index] > angles_psi4[phi_psi][index]:

                    #Calculate the distance if the angles go to zero and starts again
                    option_1 = abs(math.pi - angles_initial_rotation[phi_psi][index]) + abs(-math.pi - angles_psi4[phi_psi][index])

                else:

                    #Calculate the distance if the angles go to zero and starts again
                    option_1 = abs(math.pi - angles_psi4[phi_psi][index]) + abs(-math.pi - angles_initial_rotation[phi_psi][index])

                # option 2 is the inverse space of option 1
                option_2 = abs(2*math.pi - option_1)

                minimum_option = min(option_1, option_2)

                phi_precisions.append((1-(minimum_option / (math.pi)))*100) if phi_psi == 0 else psi_precisions.append((1-(minimum_option / (math.pi)))*100)
        
        print('\nPHI precision: ', np.mean(phi_precisions), '% phi mean real value: ', np.mean(phi_angles_psi4), 'phi mean calculated value:', np.mean(phis_initial_rotation))
        print('PSI precision: ', np.mean(psi_precisions), '% psi mean real value: ', np.mean(psi_angles_psi4), 'psi mean calculated value:', np.mean(psis_initial_rotation), '\n')

        return [phi_precisions, psi_precisions]