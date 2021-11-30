########################################################################################################################
#   The following class is for different kinds of annealing optimizer
########################################################################################################################
import boto3
import json

import datetime
import logging

s3_client = boto3.client("s3")

class ResultParser():
    def __init__(self, method, **param):
        self.result = None
        self.method = method
        if self.method == "dwave-sa":
            logging.info("parse simulated annealer result")
            self.result = param["response"]
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
    
    def get_result(self):
        return self.result
    
    def get_time(self):
        if self.method == "dwave-qa":
            # task_time
            date_time_str = self.result["taskMetadata"]["createdAt"]
            start = datetime.datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            date_time_str = self.result["taskMetadata"]["endedAt"]
            end = datetime.datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            task_time = (end-start).total_seconds()
            # qpu_time
            qpu_time = self.result["additionalMetadata"]["dwaveMetadata"]["timing"]["qpuAccessTime"]/1000.0
            return task_time, qpu_time
        else:
            logging.info("only dwave-qa support get time from s3 path!")
            return None, None