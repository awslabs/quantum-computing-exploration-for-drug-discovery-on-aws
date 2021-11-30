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

for image_dir in ${iamge_dirs[@]};do 
  echo $image_dir
  cd $image_dir
  ./build.sh 
done 







