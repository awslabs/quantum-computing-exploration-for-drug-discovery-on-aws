#!/usr/bin/env bash
set -e

sync_dirs=(
    ./batch-images/create-model
    ./batch-images/sa-optimizer
    ./lambda/SubmitQCTaskLambda/ 
)

for d in ${sync_dirs[@]};do 
   echo $d
   rm -rf $d/utility
   echo "cp -r ../utility $d/"
   cp -r ./utility $d/
done
rm -rf ./batch-images/create-model/molecule-data
cp -r ./molecule-data ./batch-images/create-model/

echo "Done"