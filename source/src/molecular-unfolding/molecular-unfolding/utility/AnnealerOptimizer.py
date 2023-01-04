# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

########################################################################################################################
#   The following class is for different kinds of annealing optimizer
########################################################################################################################
from posixpath import basename
import dimod
import neal
from dwave.system.composites import EmbeddingComposite
from braket.ocean_plugin import BraketDWaveSampler
from braket.ocean_plugin import BraketSampler

import time
import pickle  # nosec
import os
import logging
import json
import boto3

s3_client = boto3.client("s3")

log = logging.getLogger()
log.setLevel('INFO')


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

        # location in s3
        self.my_bucket = None
        self.my_prefix = None

        if method == "dwave-sa":
            logging.info("use simulated annealer from dimod")
            self.sampler = dimod.SimulatedAnnealingSampler()
        elif method == "neal-sa":
            # https://github.com/dwavesystems/dwave-neal
            logging.info("use neal simulated annealer (c++) from dimod")
            self.sampler = neal.SimulatedAnnealingSampler()
        elif method == "dwave-qa":
            self.my_bucket = param["bucket"]  # the name of the bucket
            # the name of the folder in the bucket
            self.my_prefix = param["prefix"]
            s3_folder = (self.my_bucket, self.my_prefix)
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
        logging.info("fit() ...")
        start = time.time()
        if self.method == "dwave-sa" or self.method == "neal-sa":
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

#         print(f"result={self.result}")
#         print("fit result.model_info={}".format(result["model_info"]))

        # upload data
        if self.method != "dwave-qa":
            logging.info(f"{self.method} save to local")
            self.save(f"{self.method}_result.pickle")
        elif self.method == "dwave-qa":
            task_id = self.get_task_id()
            self.save("/tmp/qa_result.pickle")  # nosec
            response = self._upload_result_json(
                task_id, "/tmp/qa_result.pickle")  # nosec
            logging.info(f"{self.method} save to s3 - {task_id}: {response}")
        return result

    def _upload_result_json(self, task_id, file_name):
        base_file_name = basename(file_name)
        key = f"{self.my_prefix}/{task_id}/{base_file_name}"
        logging.info(
            f"_upload_result_json, bucket={self.my_bucket}, key={key}")
        response = s3_client.upload_file(
            file_name, Bucket=self.my_bucket, Key=key)
        return response

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
        if self.method == "dwave-sa" or self.method == "neal-sa":
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
