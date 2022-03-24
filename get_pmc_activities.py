import os
import csv
from labelprocessing.label_processing import get_activity_pattern

sap_activities = "input/process_model_collections/sap/sap_activities.txt" 
results_sap = "results/parsing_pmc_results/sap_results.csv"


bpmai_activities = "input/process_model_collections/bpmai/petrinets_activities"
results_bpmai = "results/parsing_pmc_results/bpmai_results.csv"


if not os.path.isfile(results_sap):
    open(results_sap, 'a').close()

if not os.path.isfile(results_bpmai):
    open(results_bpmai, 'a').close()


# extract the activities from relevant models of SAP collection
def get_activities_sap():
    parsed_activities = 0
    with open(sap_activities,'r') as f:
        activities = f.read().splitlines()
    total_activities = len(activities)
    #print(total_activities)   
    for activity in activities:
        act_bo = get_activity_pattern(activity)
        if act_bo is not None:
            #print(act_bo)
            result=[act_bo, 1]
            with open(results_sap, 'a', newline='') as e:
                writer = csv.writer(e)
                writer.writerow(result)
        parsed_activities += 1
        print("Activities parsed:", parsed_activities, "/", total_activities)    
    

# extract the activities from relevant models of BPMAI collection
def get_activities_bpmai():
    activity_files = [f for f in os.listdir(bpmai_activities)]
    total_files = len(activity_files)
    #print(total_files)
    completed_files = 0
    for activity_file in activity_files:
        with open(os.path.join(bpmai_activities, activity_file), 'r') as f:
            activities = f.read().splitlines()
        for activity in activities:
            act_bo= get_activity_pattern(activity)
            if act_bo is not None:
                #print(act_bo)
                result=[act_bo, 1]
                with open(results_bpmai, 'a', newline='') as e:
                    writer = csv.writer(e)
                    writer.writerow(result)
        completed_files += 1
        print("Files completed:", completed_files, "/", total_files)



