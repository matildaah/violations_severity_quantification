import os
import pickle 
from pm4py.objects.petri.importer import importer as pnml_importer
from pm4py.objects.log.importer.xes import importer as xes_importer
from processmining.process_mining_analysis import *
from labelprocessing.label_processing import preprocess_label, parse_label
from activityviolationfeatures.semantic_similarity import *
from activityviolationfeatures.key_activites import get_start_activities, get_end_activities, get_decision_activity
import csv
from activityviolationfeatures.violation_frequencies import *
import pandas as pd
from sklearn.preprocessing import OneHotEncoder

log_dir = 'input/logs'

log_event_key = {
    "WABO.xes": "concept:name",
    "PermitLog.xes": "concept:name",
    "roadTrafficFineManagementProcess.xes": "concept:name",
}

reference_model_dir = 'reference_model'

log_reference_model = {
    "WABO.xes": "no",
    "PermitLog.xes": "no",
    "roadTrafficFineManagementProcess.xes": "no",
}

results_dir = 'results/evaluation'
file_dir = 'input'
file = 'value_added_activities.txt'
output = 'results'
clf_model = 'classification.clfser'


def run_evaluation():
    model, trainX_upsampled, trainY_upsampled = pickle.load(open(os.path.join(output, clf_model), 'rb'))
    print('finished clf model loading')

    ## load vaa activities 
    va_activities = {}
    va_file = open(os.path.join(file_dir, file))
    for line in va_file:
        key, value = line.split('->')
        key = key.strip()
        value = value.strip()
        va_activities[key] = value
    va_activities_l = list(va_activities)
    print('finished vaa activities')


    for event_log in log_event_key.keys():
        log_file = os.path.join(log_dir, event_log)
        event_key = log_event_key[event_log] 
        reference_model_key = log_reference_model[event_log]

        # import log file
        if os.path.exists(log_file):
                log = xes_importer.apply(log_file)
                print('Log ' + event_log +' successfully imported')
                total_traces = len(log)
        
        # process discovery or reference model if available
        log_name = event_log.split(".")[0]
        if reference_model_key == 'yes':
            net, initial_marking, final_marking = pnml_importer.apply(os.path.join("reference_model_dir","model"+ ".pnml"))
            print('Reference process model ' + log_name + ' successfully imported')
        else:
            net, initial_marking, final_marking = discover_process_model(log, event_key)
            print('Process model ' + log_name + ' successfully dicovered')
        
        # get log event classes
        log_events = get_event_classes(log,event_key)  
        preprocessed_log_events = {preprocess_label(event) for event in log_events} 
        preprocessed_log_events = {parse_label(event) for event in preprocessed_log_events}
        preprocessed_log_events_l = list(preprocessed_log_events)
        print('Finished parsing the labels')
        
        #compute similarity index & matrix
        sim_index, dictionary = compute_sim_index(va_activities, preprocessed_log_events)
        print('Finished sim matrix computation')

        # get start/end/decision point activities
        start_activities = get_start_activities(net)
        end_activities = get_end_activities(net)
        decision_activity = get_decision_activity(net)
        print('Finished key activities identification')
        
        # create simplified log for quicker processing
        simplified_log, alignments_map = create_simplified_log(log)
        print('Finished simplified log creation')

        # run conf checking 
        cc_alignments = run_conf_checking(simplified_log, event_key, net, initial_marking, final_marking)
        #cc_alignments, alignments_map, fitness = pickle.load(open(os.path.join(alignments_dir, alignments_file), 'rb'))
        print('Finished conformance checking analysis')

        results_file = 'violations_' + log_name + ".csv"
        with open(os.path.join(results_dir, results_file), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            result_header = ["event", "preprocessed event", "matched_vaa_activity", "vaa_type", 
                        "semantic_similarity", "violation_type","violation_frequency", "trace_share",
                        "activity_position", "decision_activity"] # "subsequent_missalignment"
            writer.writerow(result_header)
        
        
        # extract violations
        run = 1 
        for event in log_events:
            row = []
            preprocessed_event = preprocess_label(event)
            preprocessed_event = parse_label(preprocessed_event)
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


            if violation_freq > 0:
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

                
                row.extend([event, preprocessed_event, sim_activity,vaa_type, sim_score, type_violation, violation_freq, trace_share, activity_position, decision_act])

                with open(os.path.join(results_dir, results_file), 'a+', newline='') as csvfile:
                    writer = csv.writer(csvfile, delimiter=';')
                    writer.writerow(row)
            
            print('Finished activities: ' + str(run)+'/'+str(len(log_events)))
            run = run +1
        
        quantify_conf_severity(log_name, results_file, model, trainX_upsampled, trainY_upsampled)
        print('Finished model : ' + log_name)




def quantify_conf_severity(log_name, results_file, model, trainX_upsampled, trainY_upsampled):
    ## predict 
    model.fit(trainX_upsampled, trainY_upsampled)
    df = pd.read_csv(os.path.join(results_dir, results_file), sep=';', header=0) 
    #df.head()

    ##### label encoding
    # vaa type: VA, BVA, NVA
    encoder1 = OneHotEncoder()
    encoder_vaa_type = encoder1.fit_transform(df[["vaa_type"]])
    pd.DataFrame(encoder_vaa_type.toarray(), columns=encoder1.categories_).head()
    df = df.join(pd.DataFrame(encoder_vaa_type.toarray(), columns=encoder1.get_feature_names(['vaa_type'])))
    if (len(df["vaa_type"].unique())) < 3:
        current_df = list(df["vaa_type"].unique())
        expected_df = ['VA', 'BVA', 'NVA']
        missing = list(set(expected_df) - set(current_df))
        for miss in missing:
            column = 'vaa_type_'+ miss
            #print(column)
            df[column] = 0 

    # violation type = skip, add
    encoder2 = OneHotEncoder()
    encoder_violation_type = encoder2.fit_transform(df[["violation_type"]])
    pd.DataFrame(encoder_violation_type.toarray(), columns=encoder2.categories_).head()
    df = df.join(pd.DataFrame(encoder_violation_type.toarray(), columns=encoder2.get_feature_names(['violation_type'])))
    if (len(df["violation_type"].unique())) < 2:
        current_df = list(df["violation_type"].unique())
        expected_df = ['skip', 'add']
        missing = list(set(expected_df) - set(current_df))
        for miss in missing:
            column = 'violation_type_'+ miss
            #print(column)
            df[column] = 0

    # activity position: start, end, core
    encoder3 = OneHotEncoder()
    encoder_activity_pos = encoder3.fit_transform(df[["activity_position"]])
    pd.DataFrame(encoder_activity_pos.toarray(), columns=encoder3.categories_).head()
    df = df.join(pd.DataFrame(encoder_activity_pos.toarray(), columns=encoder3.get_feature_names(['activity_position'])))
    if (len(df["activity_position"].unique())) < 3:
        current_df = list(df["activity_position"].unique())
        expected_df = ['start', 'end', 'core']
        missing = list(set(expected_df) - set(current_df))
        for miss in missing:
            column = 'activity_position_'+ miss
            #print(column)
            df[column] = 0 

    # decision activity: True, False
    encoder4 = OneHotEncoder()
    encoder_decision_act = encoder4.fit_transform(df[["decision_activity"]])
    pd.DataFrame(encoder_decision_act.toarray(), columns=encoder4.categories_).head()
    df = df.join(pd.DataFrame(encoder_decision_act.toarray(), columns=encoder4.get_feature_names(['decision_activity'])))
    if (len(df["decision_activity"].unique())) < 2:
        current_df = list(df["decision_activity"].unique())
        expected_df = [True, False]
        missing = list(set(expected_df) - set(current_df))
        for miss in missing:
            column = 'decision_activity_'+ str(miss)
            #print(column)
            df[column] = 0

    ## remove non relevant attributes & reorder attributes 
    df = df.drop(columns=['event', 'preprocessed event', 'matched_vaa_activity', 'vaa_type', 'violation_type','activity_position','decision_activity'], axis=1)
    df = df.loc[:, ["semantic_similarity","violation_frequency","trace_share",
                    "vaa_type_BVA", "vaa_type_NVA", "vaa_type_VA",
                    "violation_type_add", "violation_type_skip",
                    "activity_position_core", "activity_position_end", "activity_position_start",
                    "decision_activity_False", "decision_activity_True"]]

    # predict & save
    prediction = model.predict(df)
    df_prediction = pd.DataFrame(prediction,columns=['severity_degree'])
    df_raw = pd.read_csv(os.path.join(results_dir, results_file), sep=';', header=0) 
    severity_df = pd.concat([df_raw, df_prediction], axis=1)
    # convert results df to excel
    severity_file = 'severity_quantification_' + log_name + '.xlsx'
    severity_df.to_excel(os.path.join(results_dir, severity_file), index=False)



if __name__ == "__main__":
    run_evaluation()






