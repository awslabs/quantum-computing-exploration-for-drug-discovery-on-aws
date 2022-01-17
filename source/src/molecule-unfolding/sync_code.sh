#!/usr/bin/env bash
set -e

sync_dirs=(
    ./batch-images/create-model
    ./batch-images/sa-optimizer
    ./batch-images/qa-optimizer
    ./lambda/ParseBraketResultLambda/
)

for d in ${sync_dirs[@]};do 
   echo $d
   rm -rf $d/utility
   echo "cp -r ../utility $d/"
   cp -r ./utility $d/
done

rm -rf ./batch-images/create-model/molecule-data

echo "cp -r ./molecule-data ./batch-images/create-model/"
cp -r ./molecule-data ./batch-images/create-model/


# echo "copy files to ./notebook/"
# rm -rf ./notebook/* 
# cp -r ./molecule-data ./notebook/
# cp -r ./utility ./notebook/
# cp *.ipynb ./notebook/

echo "Done"