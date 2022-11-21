# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import datetime
from braket.aws import AwsDevice
from braket.aws.aws_session import AwsSession
from boto3 import Session
from botocore import config
import os
import logging

log = logging.getLogger()
log.setLevel('INFO')

def handler(event, context):
    log.info(f"event={event}")
    device_arn = event['device_arn']
    device_region = os.environ['AWS_REGION']

    if 'd-wave' in device_arn:
        #boto3.setup_default_session(region_name='us-west-2')
        device_region = 'us-west-2'
        
    log.info(f"device_arn: {device_arn}, device_region: {device_region}")
    boto_sess = Session(region_name=device_region)

    try:
        aws_session = AwsSession(boto_session=boto_sess)
        device = AwsDevice(arn=device_arn, aws_session=aws_session)
        log.info(f"device={device}, status: {device.status}")
        log.info(f"device.properties={device.properties}")

        nextAvailableSeconds = getNextAvailable(device)
        currentTime = datetime.datetime.now(datetime.timezone.utc)
        currentTime += datetime.timedelta(seconds=nextAvailableSeconds)

        return {
            "nextAvailableSeconds": nextAvailableSeconds,
            "nextAvailableTime": currentTime.isoformat(),
            "availableNow": nextAvailableSeconds == 0,
            "deviceStatus": device.status
        }
    except Exception as e:
        log.info(repr(e))
        return {
            "availableNow": False,
            "errorMsg": repr(e),
            "deviceStatus": "ERROR"
        }


def splitWindow(window):
    start_hour = window.windowStartHour.hour
    start_min = window.windowStartHour.minute
    end_hour = window.windowEndHour.hour
    end_min = window.windowEndHour.minute

    return start_hour, start_min, end_hour, end_min


def createTimeRange(date, window, available_days):
    TWENTY_FOUR_HOURS_IN_MILLISECONDS = 86400000
    # hour/min string -> numbers
    start_hour, start_min, end_hour, end_min = splitWindow(window)

    time_ranges = []

    for day in available_days:

        start_utc = datetime.datetime(
            date.year, date.month, date.day, start_hour, start_min, 0).timestamp()*1000
        end_utc = datetime.datetime(
            date.year, date.month, date.day, end_hour, end_min, 0).timestamp()*1000

        start_utc = start_utc + TWENTY_FOUR_HOURS_IN_MILLISECONDS * \
            (day - date.weekday())
        end_utc = end_utc + TWENTY_FOUR_HOURS_IN_MILLISECONDS * \
            (day - date.weekday())

        if start_utc > end_utc:
            if (day == 6):
                wrap_start_utc = wrap_start_utc + \
                    TWENTY_FOUR_HOURS_IN_MILLISECONDS * \
                    (day - 7 - date.weekday())
                wrap_end_utc = wrap_end_utc + \
                    TWENTY_FOUR_HOURS_IN_MILLISECONDS * \
                    (day - 6 - date.weekday())

                time_ranges.unshift([wrap_start_utc, wrap_end_utc])
            end_utc = end_utc + TWENTY_FOUR_HOURS_IN_MILLISECONDS

        time_ranges.append([start_utc, end_utc])

    return time_ranges


def getTimeDifference(date, window, available_days):
    # Get current time in milliseconds
    current_time = date.timestamp() * 1000
    # Create an array of possible available ranges
    time_ranges = createTimeRange(date, window, available_days)

    for time_range in time_ranges:
        if current_time > time_range[0] and current_time < time_range[1]:
            return 0
        elif current_time < time_range[0]:
            return time_range[0] - current_time

# return next available time in ms


def getNextAvailable(device):
    DaysEnum = {
        'Sunday': 6,
        'Monday': 0,
        'Tuesday': 1,
        'Wednesday': 2,
        'Thursday': 3,
        'Friday': 4,
        'Saturday': 5
    }

    window = device.properties.service.executionWindows[0]
    exec_days = window.executionDay.value

    # minimum time is 20 ms
    min_time = None
    calc_time = 0

    date = datetime.datetime.utcnow()

    # "Everyday" | "Weekdays" | "Weekend" | "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday" | "Saturday" | "Sunday"
    if exec_days == 'Everyday':
        calc_time = getTimeDifference(date, window, range(0, 7))
    elif exec_days == 'Weekdays':
        calc_time = getTimeDifference(date, window, range(0, 6))
    elif exec_days == 'Weekend':
        calc_time = getTimeDifference(date, window, [5, 6])
    else:
        calc_time = getTimeDifference(date, window, [DaysEnum[exec_days]])

    if (min_time == None or calc_time < min_time):
        min_time = calc_time
    log.info("calc time {}".format(calc_time))
    if min_time == None:
        return 0
    else:
        return min_time/1000.
