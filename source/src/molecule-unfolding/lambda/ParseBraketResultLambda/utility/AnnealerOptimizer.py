########################################################################################################################
#   The following class is for different kinds of annealing optimizer
########################################################################################################################
import dimod
from dwave.system.composites import EmbeddingComposite
from braket.ocean_plugin import BraketDWaveSampler
from braket.ocean_plugin import BraketSampler

import time
import pickle
import os
import logging


class Annealer():

    def __init__(self, model, method, **param):

        self.qubo = model["qubo"]
        self.model_info = {}
        self._update_model_info(model)
        self.method = method
        self.param = param

        self.sampler = None
        self.time = {}
        self.init_time()

        # initial result
        self.response = None
        # result containing time/response
        self.result = None

        if method == "dwave-sa":
            logging.info("use simulated annealer from dimod")
            self.sampler = dimod.SimulatedAnnealingSampler()
        elif method == "dwave-qa":
            my_bucket = param["bucket"]  # the name of the bucket
            my_prefix = param["prefix"]  # the name of the folder in the bucket
            s3_folder = (my_bucket, my_prefix)
            # async implementation
            self.sampler = BraketSampler(s3_folder, param["device"])
            logging.info("use quantum annealer {} ".format(param["device"]))

    def _update_model_info(self, model):
        self.model_info["model_name"] = model["model_name"]
        self.model_info["rb_name"] = model["rb_name"]
        self.model_info["var"] = model["var"]
        self.model_info["var_rb_map"] = model["var_rb_map"]
        self.model_info["rb_var_map"] = model["rb_var_map"]

    def fit(self):
        # self.pre_check()
        start = time.time()
        if self.method == "dwave-sa":
            # response = self.sampler.sample(
            #     self.qubo, num_reads=self.param["shots"]).aggregate()
            self.response = self.sampler.sample_qubo(
                self.qubo, num_reads=self.param["shots"])
        elif self.method == "dwave-qa":
            # response = self.sampler.sample(
            #     self.qubo, num_reads=self.param["shots"]).aggregate()
            # actually it's quantum task
            self.response = self.sampler.sample_qubo(
                self.qubo, shots=self.param["shots"])
        end = time.time()
        self.time["run-time"] = end-start
        result = {}
        result["response"] = self.response
        result["time"] = self.time["run-time"]
        result["model_info"] = self.model_info
        self.result = result
        return result

    def get_task_id(self):
        if self.method == "dwave-qa":
            return self.response.info["taskMetadata"]["id"].split("/")[-1]
        else:
            raise Exception(
                "only method 'dwave-qa' has task id !")

    def save(self, name, path=None):
        save_path = None
        save_name = f"{name}"

        if path != None:
            save_path = os.path.join(path, save_name)
        else:
            save_path = os.path.join(".", save_name)

        with open(save_path, "wb") as f:
            pickle.dump(self.result, f)

        logging.info(f"finish save {save_name}")

        return save_path

    def embed(self):
        start = time.time()
        if self.param["embed_method"] == "default":
            self.sampler = EmbeddingComposite(self.sampler)
        end = time.time()
        self.time["embed"] = (end-start)/60

    def time_summary(self):
        if self.method == "dwave-sa":
            self.time["time"] = self.time["optimize"]
        elif self.method == "dwave-qa":
            self.time["time"] = self.time["optimize"] + \
                self.time["embed"]
        logging.info("method {} complte time {} minutes".format(
            self.method, self.time["time"]))
        if self.method == "dwave-qa":
            logging.info("quantum annealer embed time {} minutes, optimize time {} minutes".format(
                self.time["embed"], self.time["optimize"]))

    def init_time(self):
        if self.method == "dwave-qa":
            self.time["embed"] = 0

    def pre_check(self):
        if self.method == "dwave-qa":
            if self.time["embed"] == 0:
                raise Exception(
                    "You should run Annealer.embed() before Annealer.fit()!")
