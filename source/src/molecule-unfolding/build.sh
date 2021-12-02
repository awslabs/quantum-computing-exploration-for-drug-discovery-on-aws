#!/usr/bin/env bash
set -e
curr_dir=$(pwd)

./sync_code.sh 

iamge_dirs=(
${curr_dir}/batch-images/create-model
${curr_dir}/batch-images/sa-optimizer 
${curr_dir}/lambda/DeviceAvailableCheckLambda
${curr_dir}/lambda/SubmitQCTaskLambda
)

HOST=$(hostname)
echo "HOST: $HOST"
if [[ $HOST =~ ip-.* ]];then
    AWS_REGION=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | grep region | awk -F\" '{print $4}' || echo '')
    if [[ -n $AWS_REGION ]];then
       export REGION=$AWS_REGION
       echo AWS_REGION=$AWS_REGION
    fi 
fi

for image_dir in ${iamge_dirs[@]};do 
  echo $image_dir
  cd $image_dir
  ./build.sh 
done 







