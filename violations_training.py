import os
import csv
import pickle
import pandas as pd
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.evaluation.replay_fitness import evaluator as replay_fitness
from pm4py.statistics.start_activities.log.get import get_start_activities as pm_start
from pm4py.statistics.end_activities.log.get import get_end_activities as pm_end
from processmining.process_mining_analysis import  *
from labelprocessing.label_processing import preprocess_label
from activityviolationfeatures.violation_frequencies import *
from activityviolationfeatures.semantic_similarity import *
from activityviolationfeatures.key_activites import get_decision_activity
#from activityviolationfeatures.key_activites import get_start_activities, get_end_activities
from activityviolationfeatures.subsequent_misalignments import get_misalignment_sequences, subsequent_count


########################### construction of the violations dataset from the selected process models

model_dir = 'input/process_model_collections/selected_models'
xes_dir ='input/test_logs_noisy'  # len(noisy_xes) = 1000
xes_dir_extensive ='input/test_logs' 
alignments_dir = 'input/alignments_training'
event_key = 'concept:name'
file_dir = 'input'
file = 'value_added_activities.txt'
results_dir = "results/testing"



# import value added activities
va_activities = {}
va_file = open(os.path.join(file_dir, file))
for line in va_file:
    key, value = line.split('->')
    key = key.strip()
    value = value.strip()
    va_activities[key] = value
va_activities_l = list(va_activities)


### construct the violations dataset from the selected process models
def extract_conf_violations ():
    petrinets = [f for f in os.listdir(model_dir)]
    count = 1
    results_file = 'violations_dataset.csv'
    with open(results_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        result_header = ["event", "preprocessed event", "matched_vaa_activity", "vaa_type", 
                    "semantic_similarity", "violation_type","violation_frequency", "trace_share",
                    "activity_position", "decision_activity", "subsequent_missalignment"]
        writer.writerow(result_header)
    for petrinet in petrinets:
        id = os.path.basename(petrinet).split('.')[0]
        print('Started model ' + id)
        xes_file = str(id)+'.xes'
        alignments_file = str(id)+'.algn'

        # import petrinet & model
        net, initial_marking, final_marking = pickle.load(open(os.path.join(model_dir, petrinet), 'rb'))
        log = xes_importer.apply(os.path.join(xes_dir, xes_file))
        log_extensive = xes_importer.apply(os.path.join(xes_dir_extensive, xes_file))
        total_traces = len(log)
        
        # get log event classes
        log_events = get_event_classes(log,event_key)  
        preprocessed_log_events = {preprocess_label(event) for event in log_events} 
        preprocessed_log_events_l = list(preprocessed_log_events)

        #compute similarity index & matrix
        sim_index, dictionary = compute_sim_index(va_activities, preprocessed_log_events)
        
        start_activities = pm_start(log_extensive)
        end_activities = pm_end(log_extensive)
        decision_activity = get_decision_activity(net)

        # import computed akignments
        cc_alignments, alignments_map, fitness = pickle.load(open(os.path.join(alignments_dir, alignments_file), 'rb'))

        # get misalignment sequences
        try:
            misalignment_sequences, total_sequences = get_misalignment_sequences(cc_alignments,alignments_map)
        except:
            # no subsequent misalignments found
            misalignment_sequences = {}
            total_sequences = 0

        run = 1 
        for event in log_events:
            row = []
            preprocessed_event = preprocess_label(event)
            sim_activity, sim_score = get_similarity(va_activities_l,preprocessed_log_events_l, dictionary, sim_index, preprocessed_event)
            if sim_activity in va_activities:
                vaa_type = va_activities[sim_activity]
            
            total_add, total_skip, total_synch = violation_type(cc_alignments, alignments_map, event)
            total_occurrences = total_add + total_skip + total_synch

            if total_add > total_skip:
                type_violation = 'add'
                violation_freq = total_add / total_occurrences
                pattern = ('>>', event)
            else:
                type_violation = 'skip'
                violation_freq = total_skip / total_occurrences
                pattern = (event, '>>')

            trace_share = violation_log_trace(cc_alignments, alignments_map, pattern) / total_traces

            if event in start_activities:
                activity_position = 'start'
            elif event in end_activities:
                activity_position = 'end'
            else:
                activity_position ='core'

            if event in decision_activity:
                decision_act = 'True'
            else:
                decision_act= 'False'

            if misalignment_sequences:
                seq_count = subsequent_count(misalignment_sequences, pattern)
                subsequent_share = seq_count/total_sequences
            else:
                subsequent_share = 0
            
            row.extend([event, preprocessed_event, sim_activity,vaa_type, sim_score, type_violation, violation_freq, trace_share, activity_position, decision_act, subsequent_share])

            with open(results_file, 'a+', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                writer.writerow(row)
            
            print('Finished activities: ' + str(run)+'/'+str(len(log_events)))
            run = run +1
        
        print('Finished models: ' + str(count)+'/'+str(len(petrinets)))
        count = count +1



# compute alignments for the selected models and save as serialized objects
# for quicker loading when extract_conf_violations()
def compute_alignments_training():
    petrinets = [f for f in os.listdir(model_dir)]
    count = 1
    for petrinet in petrinets:
        id = os.path.basename(petrinet).split('.')[0]
        print('Started model ' + id)
        xes_file = str(id)+'.xes'
        net, initial_marking, final_marking = pickle.load(open(os.path.join(model_dir, petrinet), 'rb'))
        log = xes_importer.apply(os.path.join(xes_dir, xes_file))
        simplified_log, alignments_map = create_simplified_log(log)

        cc_alignments = run_conf_checking(simplified_log, event_key, net, initial_marking, final_marking)
        fitness = replay_fitness.evaluate(cc_alignments, variant=replay_fitness.Variants.ALIGNMENT_BASED)
        print('Fitness for model ' + id + ' is ' + str(fitness))
        alignments_file = os.path.join(alignments_dir, id + ".algn")
        pickle.dump((cc_alignments,alignments_map,fitness),open(alignments_file, 'wb'))

        print("Finished " + str(count) + ' /' + str(len(petrinets)))
        count = count + 1
        print(f"\n")



###### filter & save the violations dataset 
# remove subsequent_misalignment column & semantic_similariy < 0.6
results_dir = "results"
csv_file = "violations_dataset.csv"

df_raw = pd.read_csv(os.path.join(results_dir,csv_file), sep=';', header=0)
#df_raw.head()

df = df_raw.drop(columns=['subsequent_missalignment'])
df = df[df.semantic_similarity > 0.6]
#df.head()

## save the filtered dataframe to excel
excel_file = 'filtered_violations_dataset.xlsx'
df.to_excel(excel_file)












