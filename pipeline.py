import re
import sys
import subprocess
import os
import time
import shutil
from tqdm import tqdm
import json

# get current working directory
wd = os.getcwd()

# change the apk_dir according to the apk to test
apk_dir = wd+r"/data/ground_truth_apks/non_obfuscated/"
lib_dir_dex = wd+r"/data/ground_truth_libs_dex/"
lib_dir_jar = wd+r"/data/ground_truth_libs_jar/"

print("Pipeline started")
print("Current directory:",os.getcwd())

# currently available tools (other can be added)
available_tools = ["LibPecker", "LibScan", 'LibHunter', 'LIBLOOM']
obfuscators = ['allatori', 'proguard', 'dasho']

# remove some prefixes and suffixes from the apk names from LibScan dataset (for comparision to ground truth)
def remove_pref_suf(apk):
    for obfuscator in obfuscators:
        apk = apk.replace(obfuscator+'-', '')
    for suffix in ['-ctrl','-fltn','-rnm','-rmv']:
        apk = apk.replace(suffix, '')
    return apk

# compute metrics per apk and add to global (per tool) metrics
def metrics(gt, apk_libs, TP, FP, FN):
    TP_apk = len(set(gt).intersection(set(apk_libs)))
    FP_apk = len(set(apk_libs)) - TP_apk
    FN_apk = len(set(gt)) - TP_apk

    TP += TP_apk
    FP += FP_apk
    FN += FN_apk

    return TP, FP, FN

# evaluation
def evaluate(apk, apk_libs, library_level, versions_level, TP_v, FP_v, FN_v, TP_l, FP_l, FN_l):
    # parameters:
    # apk is the apk name
    # apk_libs are the retrieved libraries
    # library and versions_level allows to choose if we want the library or version metrics or both
    # TP,FP,FN are the true positivees, the false positives and the false negatives on the global level (tool level) at version level (v) or library level (l)


    # remove some prefixes and suffixes as the apk names contain some obfuscation infos, this allows to match the apks and the ground truth
    apk = remove_pref_suf(apk)

    if versions_level:
        # compute TP, FP, FN for one apk and add results to the global TP, FP, FN (version level)
        TP_v, FP_v, FN_v = metrics(gt_dict[apk], apk_libs, TP_v, FP_v, FN_v)
    else:
        TP_v, FP_v, FN_v = None, None, None

    if library_level:
        # remove lib versions
        gt_l = []
        apk_libs_l = []
        for lib in gt_dict[apk]:
            # remove version (numbers) and some additional prefix (beta, alpha, RELEASE, ...)
            gt_l.append(re.sub(r'[\.,-][v\d*\.]?\d+[\.\d+]*(-beta\d)?(-alpha\d)?(RELEASE)?(-\d)?(-RC\d)?(.original)?(-GA)?$', '', lib))
        for lib in apk_libs:
            apk_libs_l.append(re.sub(r'[\.,-][v\d*\.]?\d+[\.\d+]*(-beta\d)?(-alpha\d)?(RELEASE)?(-\d)?(-RC\d)?(.original)?(-GA)?$', '', lib))
        # compute TP, FP, FN for one apk and add results to the global TP, FP, FN (library level)
        TP_l, FP_l, FN_l = metrics(gt_l, apk_libs_l, TP_l, FP_l, FN_l)
    else:
        TP_l, FP_l, FN_l = None, None, None

    return TP_v, FP_v, FN_v, TP_l, FP_l, FN_l


# compute the global score for a specific tool
def score(tool, level, TP, FP, FN, threshold=None):

    if TP!=0:
        precision = TP/(TP+FP)
        recall = TP/(TP+FN)
        F1 = (2*recall*precision)/(recall+precision)
    else:
        precision, recall, F1 = 0,0,0

    results = open(wd+r"/all_results.txt", "a")
    results.write(apk_dir+"\n")
    if threshold != None:
        print(f"Tool {tool} with threshold {threshold}, {level} level:")
        results.write(f"Tool {tool} with threshold {threshold}, {level} level:\n")
    else:
        print(f"Tool {tool}, {level} level:")
        results.write(f"Tool {tool}, {level} level:\n")
    print(f"Precision: {precision:.5f}, Recall: {recall:.5f}, F1 score: {F1:.4f}")
    results.write(f"Precision: {precision:.5f}, Recall: {recall:.5f}, F1 score: {F1:.4f}\n")
    print(f"True positives: {TP}, false positive: {FP}, false negative: {FN}")
    results.write(f"True positives: {TP}, false positive: {FP}, false negative: {FN} \n \n")

    results.close()


# test if the tool passed as argument exists
try:
    tool = sys.argv[1]
except IndexError:
    print("Indicate a valid tool name. Program terminated.")
    sys.exit()
try:
    if tool not in available_tools:
        raise ValueError(f'The tool {tool} is not available. Please choose a tool from the list {available_tools}')
except ValueError:
    print(f'The tool {tool} is not available. Please choose a tool from the list {available_tools}. Program terminated.')
    sys.exit()

# store the ground truth as a dictionary {apk: [used libs]}
gt_dict = {}
with open('./data/apk_ground_truth_list.txt','r') as f:
    gt = f.read().splitlines()
    for line in gt:
        apk_libs_gt = line.split(":")
        apk_gt = apk_libs_gt[0]
        libs_gt = apk_libs_gt[1].split(",")
        gt_dict[apk_gt] = libs_gt

# version level
TP_v = 0
FP_v = 0
FN_v = 0

# library level
TP_l = 0
FP_l = 0
FN_l = 0

start_time = time.time()

########## part specific to each tool ##############


if tool == "LibPecker":

    # got to LibPecker folder in order to run the tool
    os.chdir('./LibPecker')

    # LibPecker needs a threashold [0,1] to be set as argument
    try:
        threshold = sys.argv[2]
    except IndexError:
        print("Indicate a threshold. Program terminated.")
        sys.exit()
    try:
        threshold = float(threshold)
    except ValueError:
        print("The threashold is not a number. Program terminated.")
        sys.exit()
    try:
        if not (0 <= threshold <= 1):
            raise ValueError('The threashold must be in range (0,1)')
    except ValueError:
        print("The threashold must be in range (0,1). Program terminated.")
        sys.exit()

    # run the LibPecker tool on each apk, lib pairs and extract the similarity score, appends all libs with simmilarity>threshold to the detected libraries list (apk_libs)
    for apk in tqdm(os.listdir(apk_dir), desc="apk"):
        apk_libs = []

        for lib in tqdm(os.listdir(lib_dir_dex), desc="lib"):
            string = subprocess.run(['java' ,'-jar', wd+'/LibPecker/LibPecker.jar' ,apk_dir+apk ,lib_dir_dex+lib], stdout=subprocess.PIPE).stdout.decode('utf-8')
            similarity = re.search(r"similarity: [0-9]+\.*[0-9]+", string)
            if similarity!=None:
                value = float(re.findall(r'\d+\.?\d*', similarity.group())[0])
                if value >= threshold:
                    lib = lib.replace('.dex', '')
                    apk_libs.append(lib)
            else:
                print(f"Could not extract the similarity of {apk} and {lib}")

        TP_v, FP_v, FN_v, TP_l, FP_l, FN_l = evaluate(apk, apk_libs, True, True, TP_v, FP_v, FN_v, TP_l, FP_l, FN_l)

    score(tool, "library", TP_l, FP_l, FN_l, threshold)
    score(tool, "version", TP_v, FP_v, FN_v, threshold)


if tool == "LibScan":

    # LibScan needs and additional "output" folder for storing temporary information
    if os.path.exists("outputs"):
        shutil.rmtree("outputs")
    os.mkdir("outputs")
    os.mkdir("outputs/outputs_LibScan")
    output_dir = wd+r"/outputs/outputs_LibScan/"

    os.chdir('./LibScan/tool')
    subprocess.run(['python3', 'LibScan.py', 'detect_all', '-o', output_dir, '-af', apk_dir, '-ld', lib_dir_dex])
    os.chdir(wd)

    # get the results in the ouput folder and parse the results (one output file per apk)
    for apk_output in os.listdir(output_dir):
        apk_libs = []
        apk = apk_output.replace('.txt', '')
        with open(output_dir+apk_output,'r') as f:
            outputs = f.read()
            output_libs = re.findall(r"lib:.*", outputs)
            # reformat
            for lib in output_libs:
                string = lib.replace('lib: ', '')
                list = string.split(' and ')
                apk_libs.extend(list)

        TP_v, FP_v, FN_v, TP_l, FP_l, FN_l = evaluate(apk, apk_libs, True, True, TP_v, FP_v, FN_v, TP_l, FP_l, FN_l)

    score(tool, "library", TP_l, FP_l, FN_l)
    score(tool, "version", TP_v, FP_v, FN_v)


if tool == "LibHunter":

    # LibHunter needs and additional "output" folder for storing temporary information
    if os.path.exists("outputs"):
        shutil.rmtree("outputs")
    os.mkdir("outputs")
    os.mkdir("outputs/outputs_LibHunter")
    output_dir = wd+r"/outputs/outputs_LibHunter/"

    os.chdir('./LibHunter/LibHunter')
    subprocess.run(['python3', 'LibHunter.py', 'detect_all', '-o', output_dir, '-af', apk_dir, '-ld', lib_dir_dex])
    os.chdir(wd)

    # get the results in the ouput folder and parse the results (one output file per apk)
    for apk_output in os.listdir(output_dir):
        apk_libs = []
        apk = apk_output.replace('.txt', '')
        with open(output_dir+apk_output,'r') as f:
            outputs = f.read()
            output_libs = re.findall(r"lib:.*", outputs)
            # reformat
            for lib in output_libs:
                string = lib.replace('lib: ', '').replace('.dex','')
                apk_libs.append(string)

        TP_v, FP_v, FN_v, TP_l, FP_l, FN_l = evaluate(apk, apk_libs, True, True, TP_v, FP_v, FN_v, TP_l, FP_l, FN_l)

    score(tool, "library", TP_l, FP_l, FN_l)
    score(tool, "version", TP_v, FP_v, FN_v)


if tool == "LIBLOOM":

    # LIBLOOM needs and additional "output" folder for storing temporary information
    if os.path.exists("outputs"):
        shutil.rmtree("outputs")
    os.mkdir("outputs")
    os.mkdir("outputs/outputs_LIBLOOM")

    output_dir = wd+r"/outputs/outputs_LIBLOOM/"

    os.chdir('./LIBLOOM/artifacts/')
    subprocess.run(['java', '-jar', 'LIBLOOM.jar', 'profile', '-d', lib_dir_jar, '-o', output_dir+'libs'])
    subprocess.run(['java', '-jar', 'LIBLOOM.jar', 'profile', '-d', apk_dir, '-o', output_dir+'apps'])
    out = subprocess.run(['java', '-jar', 'LIBLOOM.jar', 'detect', '-ad', output_dir+'apps', '-ld', output_dir+'libs', '-o', output_dir+'results'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    os.chdir(wd)

    # for this tool I used the "terminal" output of the tool instead of the (json) result file, from which only the library level matches could be retrieved
    for apk in tqdm(os.listdir(apk_dir), desc="apk"):
        apk_libs = []

        apk_txt = re.sub('.apk$','.txt', apk)
        lines = re.findall(apk_txt+r'\(app\)\s:\s.*\.txt\(lib\)', out)

        for line in lines:
            end = line.split(' : ')[-1]
            lib = re.sub('.txt\(lib\)$','', end)
            apk_libs.append(lib)

        TP_v, FP_v, FN_v, TP_l, FP_l, FN_l = evaluate(apk, apk_libs, True, True, TP_v, FP_v, FN_v, TP_l, FP_l, FN_l)

    score(tool, "library", TP_l, FP_l, FN_l)
    score(tool, "version", TP_v, FP_v, FN_v)

############################

# check the time needed for the tested tool
end_time = time.time()
prog_time = end_time-start_time
hours = prog_time//3600
t = prog_time - 3600*hours
minutes = t//60
t = t-60*minutes
seconds = t
print('This tool ran for %d hours, %d minutes and %d seconds.' %(hours,minutes,seconds))

results = open(wd+r"/all_results.txt", "a")
results.write(f"This tool ran for {int(hours)} hours, {int(minutes)} minutes and {int(seconds)} seconds. \n \n \n")
results.close()

