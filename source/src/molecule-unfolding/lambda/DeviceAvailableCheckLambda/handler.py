import boto3


def handler(event, context):
    device_arn = event['deviceArn']
    if 'd-wave' in device_arn:
        boto3.setup_default_session(region_name='us-west-2')

    braket = boto3.client('braket')

    response = braket.get_device(deviceArn=device_arn)

    print(f"Device {response['deviceName']} is {response['deviceStatus']}")
    return {
        "deviceStatus": response['deviceStatus'],
        "deviceName": response['deviceName']
    }
