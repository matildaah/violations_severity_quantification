import os
from pm4py.objects.petri.importer.variants.pnml import import_net as pnml_importer

sap_dir = "input/process_model_collections/sap"
pnml_dir = "input/process_model_collections/sap/sapmodels"
sapmodels_list = "input/process_model_collections/sap/sapmodels_list.txt"
sap_activities = "input/process_model_collections/sap/sap_activities.txt"


# collect activities from SAP relevant models
def preprocess_pnml():
    if not os.path.exists(sap_dir):
        os.makedirs(sap_dir)
    if not os.path.isfile(sapmodels_list):
        open(sapmodels_list, 'a').close()
    if not os.path.isfile(sap_activities):
        open(sap_activities, 'a').close()
    success = 0
    pnml_files = [f for f in os.listdir(pnml_dir) if f.endswith(".pnml") and not f.endswith(".jpg")]
    file_model = open(sapmodels_list, 'a+')
    file_activity = open(sap_activities, 'a+')
    activity_list =[]
    for pnml_file in pnml_files:
        case_id = os.path.basename(pnml_file).split('.')[0]
        no_activities = 0
        net, initial_marking, final_marking = pnml_importer(os.path.join(pnml_dir, pnml_file))
        transitions = net.transitions
        for transition in transitions: 
            
            if "tau" in transition.label or "and-" in transition.label:
                pass
            else:
                activity_label = flatten(transition.label)
                activity_list.append(activity_label)
                no_activities += 1
        if no_activities >= 2:
            success += 1
            file_model.write(case_id + '\n')
            for activity in activity_list:
                file_activity.write(activity + '\n')
        activity_list.clear()
    print("Nr of parsed models: " + str(success))
    file_model.close()
    file_activity.close()
    

# In pnml files, some transition labels are multiline (example below)
#  <text>Asset
# Maintenance</text>
# In activities file, this generates multiple activity entries for one single label - > func to avoid label splitting
def flatten(multiline):
    str = multiline.split('\n')
    oneline = ''
    for line in str:
        oneline = oneline + " " + line
    return oneline.strip()



