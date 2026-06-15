from parameters import *
from classes import *
import os
import shutil

base_dir = "Simulations_Output/Results/"

## Main
def simulate():
    print("Executing the simulations...")
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir, exist_ok=True)
    shutil.copy("parameters.py", base_dir)
    for w in rep_flow_weights:
        print(">>>>> Reputational flow weight: " + f'{w}')
        weight_dir = base_dir + "Weight_" + str(int(w*100)).rjust(nbr_weight_size,"0")
        #os.system("mkdir " + weight_dir)
        os.makedirs(weight_dir, exist_ok=True)
        for k in range(nbr_simus):
            print("Simulation " + f'{k+1}' + '/' + f'{nbr_simus}')
            simu_dir = weight_dir + "/Simu_" + str(k).rjust(nbr_simu_size,"0")
            #os.system("mkdir " + simu_dir)
            os.makedirs(simu_dir, exist_ok=True)
            pop = Population(w)
            pop.write_state(simu_dir + "/")
            while pop.actualise() and pop.time < max_time: 
                pop.write_state(simu_dir + "/")

    print("Simulations finished successfully.")

if __name__=="__main__":
    simulate()
