########################################################################################################################
#   The following class is for different kinds of annealing optimizer
########################################################################################################################
import dimod
from dwave.system.composites import EmbeddingComposite
from braket.ocean_plugin import BraketDWaveSampler

import time
import logging


class Annealer():
    
    def __init__(self, qubo, method, **param):
        
        self.qubo = qubo
        self.method = method
        self.param = param
        
        self.sampler = None
        self.time = {}
        self.init_time()
        
        if method == "dwave-sa":
            logging.info("use simulated annealer from dimod")
            self.sampler = dimod.SimulatedAnnealingSampler()
        elif method == "dwave-qa":
            my_bucket = param["bucket"] # the name of the bucket
            my_prefix = param["prefix"] # the name of the folder in the bucket
            s3_folder = (my_bucket, my_prefix)
            self.sampler = BraketDWaveSampler(s3_folder, param["device"])
            logging.info("use quantum annealer {} ".format(param["device"]))
            
    def fit(self):
        self.pre_check()
        start = time.time()
        response = None
        if self.method == "dwave-sa" or self.method == "dwave-qa":
            response = self.sampler.sample(self.qubo, num_reads=self.param["shots"]).aggregate()
        end = time.time()
        self.time["optimize-min"] = (end-start)/60
        return response
        
    def embed(self):
        start = time.time()
        if self.param["embed_method"] == "default":
            self.sampler = EmbeddingComposite(self.sampler)
        end = time.time()
        self.time["embed-min"] = (end-start)/60
    
    def time_summary(self):
        if self.method == "dwave-sa":
            self.time["time-min"] = self.time["optimize-min"]
        elif self.method == "dwave-qa":
            self.time["time-min"] = self.time["optimize-min"] + self.time["embed-min"]
        logging.info("method {} complte time {} minutes".format(self.method, self.time["time-min"]))
        if self.method == "dwave-qa":
            logging.info("quantum annealer embed time {} minutes, optimize time {} minutes".format(self.time["embed-min"], self.time["optimize-min"]))
            
    def init_time(self):
        if self.method == "dwave-qa":
            self.time["embed-min"] = 0
    
    def pre_check(self):
        if self.method == "dwave-qa":
            if self.time["embed-min"] == 0:
                raise Exception("You should run Annealer.embed() before Annealer.fit()!")
   
            
          
