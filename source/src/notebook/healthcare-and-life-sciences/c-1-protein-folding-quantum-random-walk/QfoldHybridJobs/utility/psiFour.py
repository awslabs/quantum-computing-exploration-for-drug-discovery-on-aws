from copy import Error
import subprocess
import atom
import json

class PsiFour():

    def __init__(self, psi4_path, input_filename, output_filename, precalculated_energies_path, energy_method, n_threads, basis):

        self.psi4_path = psi4_path
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.precalculated_energies_path = precalculated_energies_path
        self.energy_method = energy_method
        self.n_threads = n_threads
        self.basis = basis

    def getAtomsFromProtein(self, protein, protein_id):

        #create input file
        self.createInputFile(protein, protein_id)

        #execute psi4
        self.executePsiCommand()

        #read/parse outputfile
        [atoms, protein_id] = self.parsePsiOutputFile(protein)

        # if protein_id is not -1 means that psi4 was not able to find the protein but multiples ids for the protein
        # the solution is to create an input file with the name and the id
        if protein_id != -1:
            self.createInputFile(protein, protein_id)
            self.executePsiCommand()
            [atoms, protein_id] = self.parsePsiOutputFile(protein)

        if atoms == []:
            raise Error('No atoms have been found!')

        return atoms


    def createInputFile(self, protein, protein_id):

        inputFile = open(self.input_filename+'.dat', 'w')

        inputFile.write('molecule ' + protein + '{\n')

        if protein_id == -1:
            inputFile.write(' pubchem: '+ protein+'\n')
        else:
            inputFile.write(' pubchem: '+ protein_id+'\n')

        inputFile.write('}\n\n')

        inputFile.write('set basis ' +  self.basis + '\n')
        inputFile.write('set reference rhf\n')
        inputFile.write("energy('" + self.energy_method + "')\n")

        inputFile.close()

    def executePsiCommand(self):

        # execute psi4 by command line (it generates the file output.dat with the information)
        subprocess.run([self.psi4_path,'-n', str(self.n_threads), self.input_filename+".dat", self.output_filename+".dat"], stdout=subprocess.DEVNULL)

    def writeFileEnergies(self, atoms):

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

    def readEnergyFromFile(self):

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

    def parsePsiOutputFile(self, protein):

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
                    atoms += [atom.Atom(atomId, lineChunks[0], float(lineChunks[1]), float(lineChunks[2]), float(lineChunks[3]), float(lineChunks[4]))]
                    atomId += 1

                if isInfoLine and not 'Chemical ID' in line:
                    protein_id = line.split()[0]
                    break

                if 'Center' in line:
                    isDataLine = True

                if 'Chemical ID' in line:
                    isInfoLine = True
                        
        return [atoms, protein_id]

    def readEnergyJson(self, proteinName, numberBitsRotation, method_rotations_generation):

        with open(self.precalculated_energies_path + 'delta_energies_'+proteinName+'_'+str(numberBitsRotation)+'_'+method_rotations_generation+'.json') as json_file:
            data = json.load(json_file)

            return [data['deltas'], data['psi4_min_energy'], data['initial_min_energy'], data['index_min_energy'], data['initialization_stats']]