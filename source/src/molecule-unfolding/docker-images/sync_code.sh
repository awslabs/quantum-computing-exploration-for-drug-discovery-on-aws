#!/usr/bin/env bash
set -e

sync_dirs=(
    create-model
    qa-optimizer 
    sa-optimizer 
)

for d in ${sync_dirs[@]};do 
   echo $d
   rm -rf $d/utility
   cp -r ../utility $d/
done
rm -rf create-model/molecule-data
cp -r ../molecule-data create-model/
echo "Done"