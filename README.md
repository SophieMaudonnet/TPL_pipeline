# Evaluation pipeline for TPL detection tools in android apps

This pipeline was designed for testing various TPL detection tools. It allows to test easily each tool individually on the dataset provided by LibScan. At the moment, this pipeline allows for testing four tools: LibPecker, LibScan, LibHunter and LIBLOOM. It was designed in such a way that it can be extended to other tools if needed. The results provided by this pipeline are the precision, recall and F1 scores for each tool on the provided dataset, as well as the run time. It can futher be applied to obfuscated applications with the obfuscators: allatori, dasho and proguard.

If we want to apply this pipeline on another dataset than the one of LibScan, the dataset directory can be modified in the pipeline code. This should only require minor changes, even though the file namings in this pipeline followed the notation from LibScan.

## Setup the test directory

To use this pipeline, please download the "pipeline.py" and the "load_LibScan_data.sh" in the directory where you want to run the tests.

In the same directory, download the various tools form their github repositiories: (LibPecker, LibScan, LibHunter, LIBLOOM)

For some of these tools, some packages need to be installed:<br>
```console
sudo apt install python3-pip
```
For LibScan:
```console
pip install asn1crypto decorator lxml network
```
For LibHunter:
```console
pip install python-Levenshtein
```
In the configurations of the LibHunter some variable (lib_similar) is defined twice and thus overrides itself. For my test I removed the second (lib_similar = 0.1) and I left lib_similar = 0.85 as it seems more reasonable. To reproduce this step:

In LibHunter/LibHunter/module/config.py remove: lib_similar = 0.1 (line 24)


## Load the dataset from LibScan

A first bash script was designed to extract and reformat the dataset provided by LibScan. With the LibScan repository cloned in the same directory as the "load_LibScan_data.sh" run:

```console
bash load_LibScan_data.sh
```
This script creates a new "data" folder, which contains the following subfolders. All data are extracted from the LibScan dataset but they are sorted such that they are more convenient to use for the pipeline.

```bash
├── apk_subsets
│   ├── allatori
│   ├── dasho
│   ├── mix
│   ├── non_obfuscated
│   └── proguard
├── ground_truth_apks
│   ├── allatori
│   ├── dasho
│   │   ├── ctrl
│   │   ├── ctrl-fltn-rnm-rmv
│   │   ├── fltn-rnm
│   │   └── rmv
│   ├── non_obfuscated
│   └── proguard
├── apk_ground_truth_list.txt
├── ground_truth_libs_dex
└── ground_truth_libs_jar
```

The "ground_truth_libs_dex" and "ground_truth_libs_jar" contain all the libraries that we want to test in the dex or jar format. Most tools use the dex format (LibPecker, LibScan, LibHunter) but others use the jar format (like LIBLOOM). Various tools exist to turn one format into the other if needed. The "apk_ground_truth_list.txt" is also directly copied for the LibScan dataset and contains the groundtruth list of all apps and the TPL they use.

Then, we have the "ground_truth_apks" folder, which contains the apks that we want to test. It is subdivided into four subfolders which contain some apks that were obfuscated with different obfuscators or non-obfuscated. Dasho contains four further subfolders which contain apks obfuscated to different levels using: dead code removal, control-flow randomization, package flattening/repackaging, identifier renaming. 

Finally, the "apk_subset" folder contains a copy of some files of each of the categories and a mixed subset of all categories. This is for testing purposes, if we do not want to test all the apks. The number of apks in these subsets can be defined in the bash script "load_LibScan_data.sh", in the "number" variable.

## Run the pipeline

Each tool has to be run separately. Therefore, we pass as argument the name of the tool we want to test with the pipeline. The tool "LibPecker" uses an additional threashold parameter. As this tool returns the similarity score between each app and each library, this threshold defines the similarity score from which a library is considered as present in the app.

Here are the different options for running the pipeline (the threashold for LibPecker can be set to any value between 0 and 1):

```console
python3 pipeline.py LibPecker 0.6
or
python3 pipeline.py LibScan
or
python3 pipeline.py LibHunter
or
python3 pipeline.py LIBLOOM
```

Additionally, the tools LibScan and LibHunter define some internal thresholds that can be adapted and optimized. These can be set in LibScan/tool/module/config.py and in LibHunter/module/config.py respectively.

Notes:
- I did not try to optimize these parameters for this pipeline and I just used the ones provided in the github repo.

- Some of these tools might take several days to run. Especially LibPecker, which is very slow. Don't be surprised by that.

## Run on remote server

If we want to run this pipeline on a remote server and we need to disconnect from the terminal. We can use "nohup" that will keep the process running after the disconnection and store the output in a separate folder "output.txt". This can be done using the command:

```console
nohup python3 pipeline.py <Tool> [<threshold>] >> output.txt &
```

This will append the new results to the previous ones in the output.txt file. Some additional information appear in the output.txt depending on the processes launched by the different tools themselves.



## Results
The results are directly printed on the console and have the form:
```console
Tool XXX with threshold X, library level:
Precision: X, Recall: X, F1 score: X
True positives: X, false positive: X, false negative: X
This tool ran for X hours, X minutes and X seconds.
```
All the current tools (LibPecker, LibScan, LibHunter and LIBLOOM) return these scores for the library as well as for the version level.

All the results of previous runs are stored into an "all_results.txt" file for more readability.
