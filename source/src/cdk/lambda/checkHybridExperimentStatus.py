# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json, boto3, os

topic_arn = os.environ['topic_arn']

def lambda_handler(event, context):
    sns = boto3.client('sns')
    braket=boto3.client("braket")
    
    jobArn=event["detail"]["jobArn"]
    experiment_id=jobArn.split("/")[1][:4]
    all_jobs = braket.search_jobs(filters=[])
    this_job = braket.get_job(jobArn=jobArn)
    job_count = int(this_job['hyperParameters']['job_count'])
    finished_count = 0
    jobs_in_experiment=[]
    
    for job in all_jobs['jobs']:
        if job['jobName'][:4] == experiment_id:
            jobs_in_experiment.append({'jobName':job['jobName'],'status':job['status']})
            if job['status'] == 'COMPLETED' or job['status'] == 'FAILED':
                finished_count += 1

    if finished_count == job_count:
        message='Status of  experiment with id : '+experiment_id
        sns.publish(
        TopicArn=topic_arn,
        Subject=message,
        Message='''{message}.
        
Total number of jobs in this experiment : {job_count}
        
Detailed status:
{jobs_in_experiment}
        
        '''.format(
            message=message,
            job_count=job_count,
            jobs_in_experiment="\n".join(str(j) for j in jobs_in_experiment)
        )
    )