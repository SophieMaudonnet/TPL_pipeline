#!/bin/bash

# apks from 'theashold apks ground truth' (LibScan folder) not used

# make data folder and subfolders
mkdir -p ./data/ground_truth_apks/allatori
mkdir ./data/ground_truth_apks/dasho
mkdir ./data/ground_truth_apks/dasho/ctrl-fltn-rnm-rmv
mkdir ./data/ground_truth_apks/dasho/ctrl
mkdir ./data/ground_truth_apks/dasho/fltn-rnm
mkdir ./data/ground_truth_apks/dasho/rmv
mkdir ./data/ground_truth_apks/proguard
mkdir ./data/ground_truth_apks/non_obfuscated

# copy data from LibScan dataset (ground truth, libraries files (dex and jar) formats
cp ./LibScan/data/apk_ground_truth_list.txt ./data/
cp -r ./LibScan/data/ground_truth_libs_dex ./data/
cp -r ./LibScan/data/ground_truth_libs ./data/ground_truth_libs_jar

# separate apks obfuscated with different obfuscators in different folders
for filename in ./LibScan/data/ground_truth_apks/*.apk; do
    if [[ "$(basename ${filename})" =~ allatori-.*\.apk ]]; then
        cp ${filename} ./data/ground_truth_apks/allatori/

    # dasho was applied on four different levels --> four folders
    elif [[ "$(basename ${filename})" =~ dasho-.*\.apk ]]; then
        cp ${filename} ./data/ground_truth_apks/dasho/ctrl-fltn-rnm-rmv
    elif [[ "$(basename ${filename})" =~ .*-ctrl.apk ]]; then
        cp ${filename} ./data/ground_truth_apks/dasho/ctrl
    elif [[ "$(basename ${filename})" =~ .*-fltn-rnm.apk ]]; then
        cp ${filename} ./data/ground_truth_apks/dasho/fltn-rnm
    elif [[ "$(basename ${filename})" =~ .*-rmv.apk ]]; then
        cp ${filename} ./data/ground_truth_apks/dasho/rmv

    elif [[ "$(basename ${filename})" =~ proguard-.*\.apk ]]; then
        cp ${filename} ./data/ground_truth_apks/proguard/
    else
        cp ${filename} ./data/ground_truth_apks/non_obfuscated
    fi
done


# make small apk subsets for testing
number=8 # number of apks to copy in test subset (multiple of 4)


mkdir -p ./data/apk_subsets/non_obfuscated
mkdir ./data/apk_subsets/proguard
mkdir ./data/apk_subsets/dasho
mkdir ./data/apk_subsets/allatori
mkdir ./data/apk_subsets/mix

# copy the "number" first apks of a folder to the subset folders
find ./data/ground_truth_apks/allatori/ -maxdepth 1 -type f |head -n ${number}|xargs cp -t "./data/apk_subsets/allatori"
find ./data/ground_truth_apks/dasho/ctrl-fltn-rnm-rmv -maxdepth 1 -type f |head -n $((number/4))|xargs cp -t "./data/apk_subsets/dasho"
find ./data/ground_truth_apks/dasho/fltn-rnm -maxdepth 1 -type f |head -n $((number/4))|xargs cp -t "./data/apk_subsets/dasho"
find ./data/ground_truth_apks/dasho/rmv -maxdepth 1 -type f |head -n $((number/4))|xargs cp -t "./data/apk_subsets/dasho"
find ./data/ground_truth_apks/dasho/ctrl -maxdepth 1 -type f |head -n $((number/4))|xargs cp -t "./data/apk_subsets/dasho"
find ./data/ground_truth_apks/proguard/ -maxdepth 1 -type f |head -n ${number}|xargs cp -t "./data/apk_subsets/proguard"
find ./data/ground_truth_apks/non_obfuscated/ -maxdepth 1 -type f |head -n ${number}|xargs cp -t "./data/apk_subsets/non_obfuscated"

# create a mixed subfolder
find ./data/ground_truth_apks/allatori/ -maxdepth 1 -type f |head -n $((number/4))|xargs cp -t "./data/apk_subsets/mix"
find ./data/apk_subsets/dasho -maxdepth 1 -type f |head -n ${number}|xargs cp -t "./data/apk_subsets/mix"
find ./data/ground_truth_apks/proguard/ -maxdepth 1 -type f |head -n $((number/4))|xargs cp -t "./data/apk_subsets/mix"
find ./data/ground_truth_apks/non_obfuscated/ -maxdepth 1 -type f |head -n $((number/4))|xargs cp -t "./data/apk_subsets/mix"
