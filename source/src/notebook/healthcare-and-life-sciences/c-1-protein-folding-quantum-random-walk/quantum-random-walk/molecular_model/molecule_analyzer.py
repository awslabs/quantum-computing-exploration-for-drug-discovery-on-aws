from copy import Error

import molecular_model.atom

class Molecule_Analizer():

    def __init__(self, protein_name, aminoacids, protein_id, input_filename, output_filename, basis, energy_method):

        self.protein_name = protein_name
        self.aminoacids = aminoacids
        self.protein_id = protein_id

        self.input_filename = input_filename
        self.output_filename = output_filename
        self.basis = basis
        self.energy_method = energy_method

    #Get the atoms (and the properties) of a protein
    def extract_atoms(self):

        print('    ⬤ Extracting atoms from proteins')
        #call psi4 to get the atoms of the protein
        atoms = self.get_atoms_from_protein()
        
        # if atoms length is 0 means that the proteins was not find in the database
        if len(atoms) == 0:
            raise Exception("Protein name not found. There is no atoms for that protein")

        print('    ⬤ Calculating connections between atoms')
        #Calculate the connection between atoms
        atoms, backbone = self.calculate_atom_connection(atoms)

        return atoms, backbone

    def get_atoms_from_protein(self):

        #create input file
        self.create_input_file()

        #execute psi4
        self.execute_psi_command()

        #read/parse outputfile
        [atoms, protein_id] = self.parsePsiOutputFile()

        # if protein_id is not -1 means that psi4 was not able to find the protein but multiples ids for the protein
        # the solution is to create an input file with the name and the id
        if protein_id != -1:
            self.create_input_file(self.protein_name, protein_id)
            self.execute_psi_command()
            [atoms, protein_id] = self.parse_psi_output_file(self.protein_name)

        if atoms == []:
            raise Error('No atoms have been found!')

        return atoms

    def create_input_file(self):

        inputFile = open(self.input_filename+'.dat', 'w')

        inputFile.write('molecule ' + self.protein_name + '{\n')

        inputFile.write(' pubchem: '+ self.protein_name+'\n') if self.protein_id == -1 else inputFile.write(' pubchem: '+ self.protein_id+'\n')

        inputFile.write('}\n\n')

        inputFile.write('set basis ' +  self.basis + '\n')
        inputFile.write('set reference rhf\n')
        inputFile.write("energy('" + self.energy_method + "')\n")

        inputFile.close()

    def execute_psi_command():

        # execute psi4 by command line (it generates the file output.dat with the information)
        return NotImplementedError
    
    def parse_psi_output_file(self):

        atomId = 0
        protein_id = -1
        with open(self.output_filename+'.dat', 'r') as filehandle:

            isDataLine = False
            isInfoLine = False
            atoms = []
            for line in filehandle:

                #if line is an empty string after reading data
                if isDataLine and line.isspace():
                    break
                
                # Data has ------ and it is necessary to avoid it
                if isDataLine and not '--' in line:

                    lineChunks = line.split()
                    atoms += [molecular_model.atom.Atom(atomId, lineChunks[0], float(lineChunks[1]), float(lineChunks[2]), float(lineChunks[3]), float(lineChunks[4]))]
                    atomId += 1

                if isInfoLine and not 'Chemical ID' in line:
                    protein_id = line.split()[0]
                    break

                if 'Center' in line:
                    isDataLine = True

                if 'Chemical ID' in line:
                    isInfoLine = True
                        
        return [atoms, protein_id]
    
    def calculate_atom_connection(self, atoms):

        #Let us first map the topology. Currently cost is O(N^2). Some other algorithm could be desirable
        for at1 in atoms:
            for at2 in atoms:
                if at1 != at2:
                    if at1.element != 'H' and at2.element != 'H' and self.distance(at1,at2)<2  and (at1 not in at2.linked_to): 
                        at1.linked_to = [at2] + at1.linked_to 
                        at2.linked_to = [at1] + at2.linked_to

                    elif at1.element != 'H' and at2.element == 'H' and self.distance(at1,at2)<1.3  and (at1 not in at2.linked_to):
                        at1.linked_to = [at2] + at1.linked_to 
                        at2.linked_to = [at1] + at2.linked_to

        # Next we give an structure to each linked_to list
        for at in atoms:
            at.linked_to_dict = {'N': [], 'O': [], 'C': [], 'H': [], 'Other': []}
            for at1 in at.linked_to:
                if at1.element == 'N':
                    at.linked_to_dict['N'].append(at1)
                elif at1.element == 'O':
                    at.linked_to_dict['O'].append(at1)
                elif at1.element == 'C':
                    at.linked_to_dict['C'].append(at1)
                elif at1.element == 'H':
                    at.linked_to_dict['H'].append(at1)
                else:
                    at.linked_to_dict['Other'].append(at1)

        #self.plotting(list_of_atoms = atoms, title = 'Peptide_plot')

        #make a list of nitrogen atoms where one could start the main chain
        nitrogen_starts = []

        # For any aminoacid except proline
        if self.aminoacids[0] != 'P':
            for at in atoms:
                # This allows to identify any initial N to start except for Proline which has a weird structure
                if at.element == 'N' and len(at.linked_to_dict['C']) == 1 and len(at.linked_to_dict['H'])==2:
                    nitrogen_starts.append(at)

        # For the protein starting at proline
        elif self.aminoacids[0] == 'P':
            for at in atoms:
                # This allows to identify any initial N to start except for Proline which has a weird structure
                if at.element == 'N' and self.is_proline_N(at):
                    nitrogen_starts.append(at)

        # Find main_chain
        backbone = self.main_chain_builder(nitrogen_starts, self.aminoacids)

        # Name the atoms
        for (atom,i) in zip(backbone, range(len(backbone))):
            if atom.element == 'N' and (i % 3 == 0):
                atom.c_type = 'N_backbone'
            elif atom.element == 'C' and (i % 3 == 1) and (atom.linked_to_dict['O'] == []):
                atom.c_type = 'C_alpha'
            elif atom.element == 'C' and (i % 3 == 2) and (atom.linked_to_dict['O'] != []):
                atom.c_type = 'Carboxy'
            else:
                raise TypeError('The atom', atom.element, 'does not fulfill the requirements to be part of the backbone')

        return atoms, backbone