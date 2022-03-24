import os
import json
import shutil 
import pickle
import gc
from labelprocessing.label_processing import is_relevant_label


# convert_jsons_to_petri() --> credits go to Semantic Anomaly Detection implementation
# https://gitlab.uni-mannheim.de/processanalytics/semanticanomalydetection/-/blob/master/preprocess_bpmai.py

json_dir_orig = "bpmai/models"  
# missing directory in the project structure due to the large size of the files
# link to download: https://zenodo.org/record/3758705#.YjO1RXrMJPY

bpmai_dir = "process_model_collections/bpmai"   # contains only  BPMAI models which are in EN & BPMN2.0
petri_dir = "process_model_collections/bpmai/petrinets"
petri_dir_activities = "process_model_collections/bpmai/petrinets_activities"
json_dir  = "process_model_collections/bpmai/models"
bpmn20_en = "process_model_collections/bpmai/bpmn20_en.txt"


if not os.path.exists(bpmai_dir):
    os.makedirs(bpmai_dir)
if not os.path.exists(json_dir):
    os.makedirs(json_dir)
if not os.path.isfile(bpmn20_en):
    open(bpmn20_en, 'a').close()

# collect bpmai model ids which are  en language && bpmn2.0
def bpmn_en_models(): 
    json_files = [f for f in os.listdir(json_dir_orig) if f.endswith(".json") and not f.endswith("meta.json")]
    count_bpmn20 = 0 
    file = open(bpmn20_en, "a+") 
    for json_file in json_files:
        json_file_meta = json_file.replace(".json", ".meta.json")
        with open(os.path.abspath(json_dir_orig) + "/" + json_file_meta, 'r') as f:
            data = f.read()
            json_data = json.loads(data)
        nat_language = json_data['model']['naturalLanguage']
        mod_language = json_data['model']['modelingLanguage']
        model_id = json_data['model']['modelId']
        if nat_language == "en" and mod_language == 'bpmn20':
            file.write(model_id + '\n')
            count_bpmn20 += 1
        else :
            pass
    file.close()
    print("Models in English && BPMN 2.0: " + str(count_bpmn20))


# copy & transfer  relevant en&&bpmn20 models
def copy_models():
    with open(bpmn20_en,'r') as f:
        for line in f:
            case_id=line.strip()
            try:
                files_to_copy=find_files(case_id, json_dir_orig)
                for element in files_to_copy:
                    shutil.copy2(os.path.join(json_dir_orig, element),json_dir)
            except:
                print("Failed for case_id " + case_id)


def find_files(name, dir):
    result = []
    for file in os.listdir(dir):
        if file.startswith(name):
            result.append(file)
    return result


# convert json models to petri net models && extract activity labels for each petrinet model
def convert_jsons_to_petri():
    converter = JsonToPetriNetConverter()
    json_files = [f for f in os.listdir(json_dir) if f.endswith(".json") and not f.endswith("meta.json")]
    json_files.sort()
    print("Total number of json files:", len(json_files))
    success = 0
    failed = 0

    if not os.path.exists(petri_dir):
        os.makedirs(petri_dir)
    if not os.path.exists(petri_dir_activities):
        os.makedirs(petri_dir_activities)

    for json_file in json_files:
        case_name = os.path.basename(json_file).split('.')[0]
        try:
            # Load and convert json-based BPMN into Petri net
            net, initial_marking, final_marking = converter.convert_to_petri_net(
                os.path.join(json_dir, json_file))
            transitions = net.transitions
            pnet_file = os.path.join(petri_dir, case_name + ".pnser")
            pickle.dump((net, initial_marking, final_marking), open(pnet_file, 'wb'))
            success += 1
            file=open(os.path.join(petri_dir_activities, case_name + ".txt"), 'a+')
            for transition in transitions:
                file.write(str(transition.label) + '\n')
            file.close()   
        except:
            print("WARNING: Error during conversion from bpmn to Petri net.")
            failed += 1
        print(success + failed, "jsons done. Succes: ", success, "failed: ", failed)
        if (success + failed) % 50 == 0:
            gc.collect()
    print("Run completed.")



# keep only the relevant models (no_activities >=2) 
def keep_relevant_models():
    models = [f for f in os.listdir(petri_dir_activities)]
    total = len(models)
    relevant = 0
    non_relevant = 0
    for model in models:
        model_id = model.split(".")[0]
        relevant_model = is_relevant_model(model_id)
        file = os.path.join(petri_dir_activities, model_id + '.txt')
        if relevant_model == True:
            with open(file,'r') as f:
                activities = f.read().splitlines()
            delete_index = []
            index = 0
            for activity in activities:
                label = is_relevant_label(activity)
                if label == False:
                    delete_index.append(index)
                    index += 1
                else:
                    #pass
                    index += 1
            with open(file, 'w') as fw:
                for nr, act in enumerate(activities):
                    if nr not in delete_index:
                        fw.write(act + '\n')
            delete_index.clear()
            fw.close()
            relevant += 1
        else:
            os.remove(file)
            non_relevant += 1
    print(total, "models.| Relevant:", relevant, "| Non relevant:", non_relevant)


def is_relevant_model(model_id):
    count_relevant = 0 
    count_non_relevant = 0
    file = os.path.join(petri_dir_activities, model_id + '.txt')
    with open(file,'r') as f:
        activities = f.read().splitlines()

    for activity in activities:
        label = is_relevant_label(activity)
        if label == True:
            count_relevant += 1
        else:
            count_non_relevant += 1
    if count_relevant >= 2:
        return True
    else: 
        return False
   

 






