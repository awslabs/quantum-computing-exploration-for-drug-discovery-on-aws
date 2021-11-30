#!/usr/bin/env bash
set -e

sync_dirs=(
    create-model
    qa-optimizer 
    sa-optimizer
    ../lambda/WaitTaskCompleteLambda/ 
)

for d in ${sync_dirs[@]};do 
   echo $d
   rm -rf $d/utility
   echo "cp -r ../utility $d/"
   cp -r ../utility $d/
done
rm -rf create-model/molecule-data
cp -r ../molecule-data create-model/

echo "Done"