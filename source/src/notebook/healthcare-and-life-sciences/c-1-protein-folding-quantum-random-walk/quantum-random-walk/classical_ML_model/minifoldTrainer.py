######################################################################################################################################
##  Minifold is a project developed by Eric Alcaide (https://github.com/EricAlcaide/MiniFold)                                       ##
##  Thanks to the autor for his awesome project similar to AlphaFold but in miniature                                               ##
##                                                                                                                                  ##
## Initial project uses Jupyter Notebooks, but in this project everything was translated to plain python due to performance reasons ## 
######################################################################################################################################

import os
import numpy as np
import math

# Import libraries
from keras.optimizers import Adam

# Model architecture
from resnet_1d_angles import resnet_v2, custom_mse_mae

class MinifoldTrainer():
    
    def __init__(self, inputPath, model_path, max_aa_length, window_size, epochs, batch_size):

        #Hidde info messages from tensorflow
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'

        self.inputPath = inputPath
        self.model_path = model_path
        self.max_aa_length = max_aa_length
        self.window_size = window_size
        self.epochs = epochs
        self.batch_size = batch_size

        if not os.path.isfile(inputPath):
            raise IOError('<!> ERROR: %s does not exist!' %inputPath)

        #Global variables used to preprocess data
        self.names = []
        self.seqs = []
        self.coords = []
        self.phis = []
        self.psis = []
        self.input_aa = []
        self.outputs = []
    
    def train(self):

        print('\n## DATA PREPROCESSING ##\n')

        #Get protein under defined maximum aminoacid length
        self.getProteinsFromRaw(self.max_aa_length)
        print('<i>', len(self.names),'proteins with less than', self.max_aa_length, 'aminoacids from raw data extracted')

        #Get angles froom coords
        self.getAnglesFromCoords()
        print('<i> Angles extracted from protein coordinates')

        #Angle data preparation
        self.angleDataPreparation()
        print('<i> Angle data input for training prepared from angles')

        print('\n## MODEL TRAINING ##\n')

        #Generate model (using resnet_1d_angles)
        self.generateModel()
        print('\n<i> Knowledge model:', 'protein_under_'+str(self.max_aa_length)+'.h5','generated! Path:', '../'+self.model_path+'protein_under_'+str(self.max_aa_length)+'.h5')

    def getProteinsFromRaw(self, max_aminoacid_length):        

        with open(self.inputPath) as f:
            lines = f.readlines()

            name = ''
            seq = []
            coord = []
            for index in range(0, len(lines)):
                
                if len(self.coords) == 995:
                    break
                
                # Start recording
                if lines[index] == "[ID]\n":
                    name = lines[index+1]
                
                elif lines[index] == "[PRIMARY]\n":
                    seq = lines[index+1]

                elif lines[index] == "[TERTIARY]\n":
                    coord = self.coords_split(lines[index+1:index+4], "\t")

                elif lines[index] == "\n":

                    #Save all attributes of the protein only if it shorter than the maximum aminoacids length
                    if len(seq) <= max_aminoacid_length:
                        self.names.append(name)
                        self.seqs.append(seq)
                        self.coords.append(coord)

    def getAnglesFromCoords(self):

        # Organize by atom type
        coords_nterm = [self.separate_coords(full_coords, 0) for full_coords in self.coords]
        coords_calpha = [self.separate_coords(full_coords, 1) for full_coords in self.coords]
        coords_cterm = [self.separate_coords(full_coords, 2) for full_coords in self.coords]

        print('<i> Computing angles from coordinates')
        # Compute angles for a protein
        for k in range(len(self.coords)):
            phi, psi = [0.0], []
            index_to_remove = []

            # Use our own functions inspired from bioPython
            for i in range(len(coords_calpha[k])):
                # Calculate phi, psi
                # CALCULATE PHI - Can't calculate for first residue
                if i>0:
                    result = self.get_dihedral(coords_cterm[k][i-1], coords_nterm[k][i], coords_calpha[k][i], coords_cterm[k][i])
                    phi.append(result) # my_calc
                    
                # CALCULATE PSI - Can't calculate for last residue
                if i<len(coords_calpha[k])-1: 
                    result = self.get_dihedral(coords_nterm[k][i], coords_calpha[k][i], coords_cterm[k][i], coords_nterm[k][i+1])
                    psi.append(result) # my_calc

                if result == 'error':
                    #If there was an error (the angle is nan because the coords were wrong), it is necessary to save the k index to delete it
                    index_to_remove.append(i)

                    #Depending on the coord that is wrong, the previous or the next (or both) angles are wrong calculated (it is also necessary to remove them)
                    if coords_cterm[k][i][0] == 0.0 and i<len(coords_calpha[k])-1:
                        index_to_remove.append(i+1)
                    if coords_nterm[k][i][0] == 0.0 and i > 0:
                        index_to_remove.append(i-1)
                
            # Add an extra 0 to psi (unable to claculate angle with next aa)
            psi.append(0)

            index_to_remove = set(index_to_remove)
            #Delete of selected positions
            delete_caracter = '@'
            for index in set(index_to_remove):
                #Split and merge string without the index position
                self.seqs[k] = self.seqs[k][0:index] + delete_caracter + self.seqs[k][(index+1):len(self.seqs[k])]
                if index > 0:
                    phi[index] = delete_caracter
                
                if index < len(psi)-1:
                    psi[index] = delete_caracter

            self.seqs[k] = self.seqs[k].replace(delete_caracter, '')
            index = 0
            while index < len(phi):
                if(phi[index] == delete_caracter):
                    del phi[index]
                else:
                    index += 1

            index = 0
            while index < len(psi):
                if(psi[index] == delete_caracter):
                    del psi[index]
                else:
                    index += 1

            # Add protein info to register
            self.phis.append(phi)
            self.psis.append(psi)

    def angleDataPreparation(self):

        long = 0 # Counter to ensure everythings fine

        print('<i> Preparing input/output for model trainer')
        for i in range(len(self.seqs)): 
            if len(self.seqs[i])>self.window_size*2:
                long += len(self.seqs[i])-self.window_size*2

                for j in range(self.window_size,len(self.seqs[i])-self.window_size):
                # Padd sequence
                    self.input_aa.append(self.onehotter_aa(self.seqs[i], j))
                    self.outputs.append([self.phis[i][j], self.psis[i][j]])
                    # break

        self.input_aa = np.array(self.input_aa).reshape(len(self.input_aa), self.window_size*2, 22)

    def generateModel(self):

        ## LOAD DATASET ##
        
        # Get inputs data
        aas = self.input_aa
        self.outputs = np.array(self.outputs)

        out = []
        out.append(np.sin(self.outputs[:,0]))
        out.append(np.cos(self.outputs[:,0]))
        out.append(np.sin(self.outputs[:,1]))
        out.append(np.cos(self.outputs[:,1]))
        out = np.array(out).T


        # Concatenate input features
        inputs = np.concatenate((aas[:, :, :20], aas[:, :, 20:]), axis=2) 
        np.set_printoptions(threshold=np.inf)

        # Separate data between training and testing
        split = 38700
        x_train, x_test = inputs[:split], inputs[split:]
        y_train, y_test = out[:split], out[split:]

        ## LOADING MODEL ##

        # Using AMSGrad optimizer for speed 
        adam = Adam(lr=0.001, beta_1=0.9, beta_2=0.999, decay=0.0, amsgrad=True)
        # Create model
        model = resnet_v2(input_shape=(self.window_size*2,22), depth=20, num_classes=4, conv_first=True)
        model.compile(optimizer=adam, loss=custom_mse_mae, metrics=["mean_absolute_error", "mean_squared_error"])

        # Resnet (pre-act structure) with windows_size*22 columns as inputs - leaving a subset for validation
        model.fit(x_train, y_train, epochs=self.epochs, batch_size=self.batch_size, verbose=1, shuffle=True, validation_data=(x_test, y_test))

        model.save('../'+self.model_path+'protein_under_'+str(self.max_aa_length)+'.h5')


    # Helper function to save data to a .txt file
    def stringify_angle_data_preparation(self, vec):
        return "".join(str(v)+" " for v in vec)

    # Helper functions to extract numeric data from text
    def parse_lines(self, raw):
        return np.array([[float(x) for x in line.split(" ") if x != ""] for line in raw])

    def parse_line_angle_data_preparation(self, line):
        return np.array([float(x) for x in line.split(" ") if x != ""])

    def coords_split(self, lister, splice):
        # Split all passed sequences by "splice" and return an array of them
        # Convert string fragments to float 
        coords = []
        for c in lister:
            coords.append([float(a) for a in c.split(splice)])
        
        return coords

    # Length of masking - window_sizex2 AAs
    def onehotter_aa(self, seq, pos):
        # Pad sequence
        key = "HRKDENQSYTCPAVLIGFWM"
        # Van der Waals radius
        vdw_radius = {"H": 118, "R": 148, "K": 135, "D": 91, "E": 109, "N": 96, "Q": 114,
                    "S": 73, "Y": 141, "T": 93, "C": 86, "P": 90, "A": 67, "V": 105,
                    "L": 124, "I": 124, "G": 48, "F": 135, "W": 163, "M": 124}
        radius_rel = vdw_radius.values()
        basis = min(radius_rel)/max(radius_rel)
        # Surface exposure 
        surface = {"H": 151, "R": 196, "K": 167, "D": 106, "E": 138, "N": 113, "Q": 144,
                    "S": 80, "Y": 187, "T": 102, "C": 104, "P": 105, "A": 67, "V": 117,
                    "L": 137, "I": 140, "G": 0, "F": 175, "W": 217, "M": 160}
        surface_rel = surface.values()
        surface_basis = min(surface_rel)/max(surface_rel)
        # One-hot encoding
        one_hot = []
        for i in range(pos-self.window_size, pos+self.window_size):
            vec = [0 for i in range(22)]
            # mark as 1 the corresponding indexes
            for j in range(len(key)):
                if seq[i] == key[j]:
                    vec[j] = 1
                    # Add Van der Waals relative radius
                    vec[-2] = vdw_radius[key[j]]/max(radius_rel)-basis
                    vec[-1] = surface[key[j]]/max(surface_rel)-surface_basis

            one_hot.append(vec) 
        
        return np.array(one_hot)

    # Could use "Using LinearAlgebra + built-in norm()" but gotta learn Julia
    def norm(self, vector):
        return math.sqrt(sum([v*v for v in vector]))

    def parse_line_angle_from_coords(self, raw):
        return np.array([[float(x) for x in line.split("\t") if x != ""] for line in raw])

    #Get the coordinates for 1 atom type
    def separate_coords(self, full_coords, pos): # pos can be either 0(n_term), 1(calpha), 2(cterm)
        res = []
        for i in range(len(full_coords[1])):
            if i%3 == pos:
                res.append([full_coords[j][i] for j in range(3)])

        return np.array(res)

    # Helper functions
    def get_dihedral(self, coords1, coords2, coords3, coords4):
        """Returns the dihedral angle in degrees."""

        a1 = coords2 - coords1
        a2 = coords3 - coords2
        a3 = coords4 - coords3

        v1 = np.cross(a1, a2)
        #If all components of the vector are 0 the division is 0/0 so an error is returned
        if v1[0] == 0 and v1[1] == 0 and v1[2] == 0:
            return 'error'
        else:
            v1 = v1 / (v1 * v1).sum(-1)**0.5

        v2 = np.cross(a2, a3)
        #If all components of the vector are 0 the division is 0/0 so an error is returned
        if v2[0] == 0 and v2[1] == 0 and v2[2] == 0:
            return 'error'
        else: 
            v2 = v2 / (v2 * v2).sum(-1)**0.5
        
        porm = np.sign((v1 * a3).sum(-1))
        rad = np.arccos((v1*v2).sum(-1) / ((v1**2).sum(-1) * (v2**2).sum(-1))**0.5)
        if not porm == 0:
            rad = rad * porm

        return rad

    def stringify_angle_from_coords(self, vec):
        """ Helper function to save data to .txt file. """
        line = ""
        for v in vec:
            line = line+str(v)+" "
        return line