
# function to generate list of potential stem pairs that form pseudoknots:
def potential_pseudoknots(stems_potential, pkp):

    pseudoknots_potential = []
    pseudoknot_penalty = pkp

    for i in range(len(stems_potential)):
        for j in range(i + 1, len(stems_potential)):
            
            stem1 = stems_potential[i]
            stem2 = stems_potential[j]
    
            i_a = stem1[0]
            j_a = stem1[1]
            i_b = stem2[0]
            j_b = stem2[1]
    
            pseudoknot = [i,j,1]
    
            if (i_a < i_b and i_b < j_a and j_a < j_b):
        
                pseudoknot[2] = pseudoknot_penalty
    
            pseudoknots_potential.append(pseudoknot)
            
    return pseudoknots_potential