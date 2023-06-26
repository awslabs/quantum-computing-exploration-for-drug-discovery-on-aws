#!/bin/bash

# Specify the directory to search
src_directory="../healthcare-and-life-sciences"
en_tgt_directory="../../../../docs/en/workshop"
zh_tgt_directory="../../../../docs/zh/workshop"

file_ext=".ipynb"
# Loop through each item in the directory
for item in "$src_directory"/*; do
  # Check if the item is a directory
  if [ -d "$item" ]; then
    # If it's a directory, print the name to the console
    en_dst_pos=$en_tgt_directory/$(basename "$item")
    zh_dst_pos=$zh_tgt_directory/$(basename "$item")
    echo $en_dst_pos
    echo $zh_dst_pos
    # find "$item" -maxdepth 1 -mindepth 1 -type f -name "*$file_ext" -exec cp {} "$en_dst_pos" \;
    file=$(find "$item" -maxdepth 1 -mindepth 1 -type f -name "*$file_ext")
    echo $file
    cp $file $en_dst_pos
    cp $file $zh_dst_pos
    # find "$item" -maxdepth 1 -mindepth 1 -type f -name "*$file_ext" -exec cp {} "$zn_dst_pos" \;
    # echo "$(basename "$item")"
  fi
done