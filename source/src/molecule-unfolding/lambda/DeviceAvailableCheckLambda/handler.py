import boto3
import json
import datetime


def handler(event, context):
    device_arn = event['deviceArn']
    if 'd-wave' in device_arn:
        boto3.setup_default_session(region_name='us-west-2')

    braket = boto3.client('braket')

    try: 
        response = braket.get_device(deviceArn=device_arn)
        executionWindows = json.loads(response['deviceCapabilities'])[
            'service']['executionWindows'][0]
        # [{'executionDay': 'Everyday', 'windowStartHour': '00:00:00', 'windowEndHour': '23:59:59'}]
        # [{'executionDay': 'Weekdays', 'windowStartHour': '13:00:00', 'windowEndHour': '02:00:00'}]

        windowStartHour = executionWindows['windowStartHour']
        windowEndHour = executionWindows['windowEndHour']
        executionDay = executionWindows['executionDay']
        currentTime = datetime.datetime.now(datetime.timezone.utc)

        status_and_time = get_available_status_and_time(
            windowStartHour, windowEndHour, executionDay)

        print(f"Device {response['deviceName']} is {response['deviceStatus']}")
 
        return {
            "availableNow": status_and_time['availableNow'],
            "deviceStatus": response['deviceStatus'],
            "deviceName": response['deviceName'],
            "currentTime": currentTime.isoformat(),
            "nextAvaiableTime": status_and_time['nextAvaiableTime'].isoformat(),
            ** executionWindows
        }

    except Exception as e: 
        return {
            "availableNow": False,
            "errorMsg": repr(e),
            "currentTime": currentTime.isoformat()
        } 


def time_in_window(ctime, stime, etime):
    if ctime >= stime and ctime <= etime:
        return True
    return False


def get_available_status_and_time(windowStartHour, windowEndHour, executionDay):

    windowStartTime = datetime.time(*[int(it)
                                    for it in windowStartHour.split(":")])
    windowEndTime = datetime.time(*[int(it)
                                  for it in windowEndHour.split(":")])

    currentTime = datetime.datetime.now(datetime.timezone.utc)

    start_datetime = datetime.datetime.combine(
        currentTime.date(), windowStartTime, tzinfo=datetime.timezone.utc)
    end_datatime = datetime.datetime.combine(
        currentTime.date(), windowEndTime, tzinfo=datetime.timezone.utc)
    if end_datatime < start_datetime:
        end_datatime += datetime.timedelta(days=1)

    availableNow = False
    if executionDay == 'Everyday':
        if time_in_window(currentTime, start_datetime, end_datatime):
            availableNow = True
    elif executionDay == 'Weekdays' and currentTime.isoweekday() in [1, 2, 3, 4, 5]:
        if time_in_window(currentTime,  start_datetime, end_datatime):
            availableNow = True

    nextAvaiableTime = start_datetime

    if nextAvaiableTime < currentTime:
        if executionDay == 'Everyday':
            nextAvaiableTime += datetime.timedelta(days=1)
        if executionDay == 'Weekdays':
            if currentTime.isoweekday() in [1, 2, 3, 4]:
                nextAvaiableTime += datetime.timedelta(days=1)
            if currentTime.isoweekday() in [5]:
                nextAvaiableTime += datetime.timedelta(days=3)

    return {
        "availableNow": availableNow,
        "nextAvaiableTime": nextAvaiableTime
    }
