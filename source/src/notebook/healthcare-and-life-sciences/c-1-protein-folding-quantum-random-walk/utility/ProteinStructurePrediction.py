# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

########################################################################################################################
#   The following class is for different kinds of annealing optimizer
########################################################################################################################
from posixpath import basename

import time
import pickle  # nosec
import os
import logging
import json
import boto3
import utils

s3_client = boto3.client("s3")

log = logging.getLogger()
log.setLevel('INFO')


class ProteinStructurePrediction():

    def __init__(self, model, method, config_path, **param):

        self.model_info = {}
        self._update_model_info(model)
        self.model = model
        # TODO see if update model is necessary
        self.method = method

        self.tools = utils.Utils(config_path)

        self.param = param

        # result containing time/response
        self.result = {}

        # location in s3
        self.my_bucket = None
        self.my_prefix = None
        
        if method == "qfold-cc" or method == "qfold-qc":
            self.precision_solution = self.tools.config_variables['precision_solution']
            self.default_value_tts = self.tools.config_variables['default_value_tts']
            logging.info(f"initial protein structure prediction using {method} in QFold")
            
    def run(self):
        mode = self.param["mode"]
        if self.method == "qfold-cc":
            self._qfold_cc_psp()
        elif self.method == "qfold-qc":
            self._qfold_qc_psp(mode)

    def _update_model_info(self, model):
        self.model_info["model_name"] = model["model_name"]
    
    def _qfold_cc_psp(self):
        c_accumulated_tts = []

        min_c_tts = {'step': 0, 'value': -1}

        initial_step = self.tools.config_variables['initial_step']
        final_step = self.tools.config_variables['final_step']
        qfold_cc_model = self.model["model"]
        index_min_energy = self.model["model_params"]["index_min_energy"]
        initialization_stats = self.model["model_params"]["initilization_stats"]
        for step in range(initial_step, final_step):  
            start_time = time.time()

            probabilities_matrix = qfold_cc_model.execute_metropolis(step)

            logging.info(f"CLASSICAL METROPOLIS: Time for {step} steps: {time.time() - start_time} seconds")

            c_tts = self._calculate_tts_from_probability_matrix(probabilities_matrix, index_min_energy, step, self.precision_solution)

            c_accumulated_tts.append(c_tts)

            if c_tts < min_c_tts['value'] or min_c_tts['value'] == -1: min_c_tts.update(dict(value=c_tts, step=step))

        final_stats = {'min_tts': min_c_tts}
        self.result['initial_step'] = initial_step
        self.result['final_step'] = final_step
        self.result['tts'] = c_accumulated_tts
        self.result['initialization_stats'] = initialization_stats
        self.result['final_stats'] = final_stats

        self.save()
    
    def _qfold_qc_psp(self, mode):
        q_accumulated_tts = []

        min_q_tts = {'step': 0, 'value': -1}

        qfold_qc_model = self.model["model"]
            
        start_time = time.time()

        initial_step = self.tools.config_variables['initial_step']
        final_step = self.tools.config_variables['final_step']
        initialization_stats = self.model["model_params"]["initilization_stats"]
        index_min_energy = self.model["model_params"]["index_min_energy"]

        if mode == 'local-simulator':
            [dict_probabilities_matrix, time_statevector] = qfold_qc_model.execute_quantum_metropolis_n(initial_step=initial_step, nW=final_step)
            q_time = time.time() - start_time
            logging.info(f"QUANTUM METROPOLIS: Time for final steps {q_time} seconds ({time_statevector} seconds statevector)")

            for step, probabilities_matrix in dict_probabilities_matrix.items():

                ###### Accumulated values Quantum Metropolis ######
                q_tts = self._calculate_tts_from_probability_matrix(probabilities_matrix, index_min_energy, step, self.precision_solution)

                q_accumulated_tts.append(q_tts)     
                if q_tts < min_q_tts['value'] or min_q_tts['value'] == -1: min_q_tts.update(dict(value=q_tts, step=step))

        elif mode == 'experiment': 
            [experiment_result_matrix, time_statevector, execution_stats, measures_dict] = qfold_qc_model.execute_real_hardware(nWs = 2)
        else:
            print(f"<*> ERROR!! Quantum execution mode not recognized. The mode selected is {mode} ")

        final_stats = {'min_tts': min_q_tts}
        self.result['initial_step'] = initial_step
        self.result['final_step'] = final_step
        self.result['tts'] = q_accumulated_tts
        self.result['initialization_stats'] = initialization_stats
        self.result['final_stats'] = final_stats

        self.save()


    def _calculate_tts_from_probability_matrix(self, probabilities_matrix, index_min_energy, step, precision_solution):

        p_t = 0
        # if the index of min energy calculated by psi 4 is in the results of metropolis, p_t is extracted
        # else, the p_t is set to a very small value close to 0 (not 0 to avoid inf values)
        if index_min_energy in probabilities_matrix.keys():
            p_t = probabilities_matrix[index_min_energy]
        else:
            p_t = 0

        result = 0
        # Result is the calculated TTS
        if p_t >= 1:
            result = 1
        elif p_t == 0:
            result = self.default_value_tts
        else:
            result = self.tools.calculateTTS(precision_solution, step, p_t)

        return result

    def fit(self):
        logging.info("fit() ...")
        start = time.time()
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

    def save(self):
        save_name = ''
        model_name = self.model["model_name"]
        save_name = 'tts_results_'+model_name+'_'+str(self.tools.config_variables['beta'])+'_'+self.method+'.json'

        with open(save_name, "w") as f:
            json.dump(self.result, f)

        logging.info(f"finish save {save_name}")

        return save_name

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
