import os.path
from keras.models import load_model
import numpy as np
from keras.losses import mean_squared_error, mean_absolute_error

class Minifold:

    def __init__(self, model_path, window_size, max_aa_length):

        self.model_path = model_path+'protein_under_'+str(max_aa_length)+'.h5'
        self.window_size = window_size

        #Hidde info messages from tensorflow
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'

        if not os.path.isfile(self.model_path):

            raise IOError('<!> ERROR: Knowledge model not existing!\nTo generate a model execute: initialAngleTrainer/initialAngleTrainer.py')

    def predictAngles(self, aminoacids):

        print('    ⬤ Loading knowledge model')
        #Load existing model
        model = load_model(self.model_path, custom_objects={'custom_mse_mae': self.custom_mse_mae})

        print('    ⬤ Generating input values')
        input_values = self.generate_input_values(aminoacids)

        #input_aas is a rows x aas windows size x 22 (20 aas, Van der Waals distance, Surface)
        predicted_angles = model.predict(input_values)

        #get angles from sin and cos. Angles are expresed between π and -π
        angles = self.extract_angles(predicted_angles)

        return angles

    # Metric defined in: https://github.com/EricAlcaide/MiniFold/blob/master/models/angles/resnet_1d_angles.py#L14
    def custom_mse_mae(self, y_true, y_pred):
        """ Custom loss function - MSE + MAE """
        return mean_squared_error(y_true, y_pred)+ mean_absolute_error(y_true, y_pred)

    def generate_input_values(self, protein_sequence):

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


        print('    ⬤ Generating input for minifold prediction')

        aas_input = []
        # iterate over each aminoacid
        for right in range(1, len(protein_sequence)):

            aa_input = []
            [left_index, right_index] = self.calculate_left_right(self.window_size, right, len(protein_sequence))
            protein_sequence_index = left_index

            #create input for each aminoacid pair
            for window_index in range(0, self.window_size*2):

                column = []

                if window_index >= left_index and window_index <= right_index:
                    
                    #in each window is necessary to create an array with 22 positions
                    for column_index in range(0, 22):

                        #If the aa is the same than in the key, it inserts a 1 (one-hot encoding)
                        if column_index < len(key) and protein_sequence[protein_sequence_index] == key[column_index]:
                            column.append(1)
                            #The aminoacid is found in this index value so it is stored in a variable for the VdW and surface
                            key_index = column_index

                        #If the aa is not the same than in the key, it inserts a 0 (one-hot encoding)
                        elif column_index < len(key) and protein_sequence[protein_sequence_index] != key[column_index]:
                            column.append(0)

                        #Van der Waals radius
                        elif column_index == 20:
                            column.append(vdw_radius[key[key_index]]/max(radius_rel)-basis)
                            
                        #Surface
                        elif column_index == 21:
                            column.append(surface[key[key_index]]/max(surface_rel)-surface_basis)

                    protein_sequence_index += 1

                else:
                    column = np.zeros(22)

                aa_input.append(column)

            aas_input.append(aa_input)

        inputs = np.array(aas_input)
        return inputs

    def calculate_left_right(self, window_size, right, protein_sequence_length):

        left = right - 1 
        
        for _ in range(1, window_size):

            if left > 1:
                left -= 1

            if right < protein_sequence_length-1:
                right += 1

        return [left, right]

    
    def extract_angles(self, predicted_angles):

        angles = []

        for prediction in predicted_angles:
            angles_row = []
            phi_sin, phi_cos, psi_sin, psi_cos = prediction[0], prediction[1], prediction[2], prediction[3]

            angles_row.append(np.arctan2(phi_sin, phi_cos))
            angles_row.append(np.arctan2(psi_sin, psi_cos))
            
            angles.append(angles_row)

        return angles