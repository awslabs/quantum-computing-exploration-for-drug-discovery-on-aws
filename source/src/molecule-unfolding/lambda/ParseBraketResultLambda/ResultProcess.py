########################################################################################################################
#   The following class is for different kinds of annealing optimizer
########################################################################################################################
import boto3
import json
import pickle

import datetime
import logging

s3_client = boto3.client("s3")

class ResultParser():
    def __init__(self, method, **param):
        self.agg_response = None
        self.method = method
        # raw_result, load from pickle file, maintain by dwave
        self.raw_result = None
        self._load_raw_result()
        # result: get by task_id, maintain by braket api
        self.result = None
        if self.method == "dwave-sa":
            logging.info("parse simulated annealer result")
            self.result = None
        elif self.method == "dwave-qa":
            logging.info("parse quantum annealer result")
            self.bucket = param["bucket"]
            self.prefix = param["prefix"]
            self.task_id = param["task_id"]
            self.result = self._read_result_json(self.bucket, self.prefix, self.task_id, "results.json")
    
    def _read_result_json(self, bucket, prefix, task_id, file_name):
        key = f"{prefix}/{task_id}/{file_name}"
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        return json.loads(obj["Body"].read())
    
    def _load_raw_result(self):
        with open(self.path, "rb") as f:
            self.raw_result = pickle.load(f)
    
    def get_all_result(self):
        return self.raw_result, self.result
    
    def get_time(self):
        if self.method == "dwave-qa":
            local_time = self.raw_result["time"]
            # task_time
            date_time_str = self.result["taskMetadata"]["createdAt"]
            start = datetime.datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            date_time_str = self.result["taskMetadata"]["endedAt"]
            end = datetime.datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            task_time = (end-start).total_seconds()
            # reference https://docs.dwavesys.com/docs/latest/c_qpu_timing.html
            # qa_total_time = qpu_program_time + sampling_time + qpu_access_overhead_time + total_post_processing_time
            qpu_programming_overtime = self.result["additionalMetadata"]["dwaveMetadata"]["timing"]["qpuProgrammingTime"]
            qpu_sampling_time = self.result["additionalMetadata"]["dwaveMetadata"]["timing"]["qpuSamplingTime"]
            qpu_access_overhead_time = self.result["additionalMetadata"]["dwaveMetadata"]["timing"]["qpuAccessOverheadTime"]
            total_post_processing_time = self.result["additionalMetadata"]["dwaveMetadata"]["timing"]["totalPostProcessingTime"]
            qa_total_time = qpu_programming_overtime + qpu_sampling_time + qpu_access_overhead_time + total_post_processing_time
            qa_total_time = qa_total_time/1000.0
            qa_total_time = qa_total_time/1000.0
            qa_access_time = self.result["additionalMetadata"]["dwaveMetadata"]["timing"]["qpuAccessTime"]/1000.0
            qa_access_time = qa_access_time/1000.0
            return local_time, task_time, qa_total_time, qa_access_time
        else:
            local_time = self.raw_result["time"]
            logging.info("sa only has local_time!")
            return local_time, None, None, None
    
    def process_data(self):
        if self.method == "dwave-qa":
            self.agg_response = self.result.aggregate()
            logging.info("parsing calculating results from dwave-qa")
        
        elif self.method == "dwave-sa":
            self.agg_response = self.result.aggregate()
            logging.info("parsing calculating results from dwave-sa")