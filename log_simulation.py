import os
import pickle
import random
from copy import deepcopy
from pm4py.simulation.playout import simulator
from pm4py.objects.log.log import Event, Trace, EventLog
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from labelprocessing.label_processing import is_relevant_label
from pm4py.objects.petri.check_soundness import check_easy_soundness_net_in_fin_marking


# part 1: simulate (extensive) logs via playout functionality 
# part 2: add noise in the xes logs -->  credits go to Semantic Anomaly Detection implementation
# https://gitlab.uni-mannheim.de/processanalytics/semanticanomalydetection/-/blob/master/evaluation/log_simulator.py


model_dir = 'input/process_model_collections/selected_models'
xes_dir = 'input/test_logs'
xes_dir_noisy ='input/test_logs_noisy'

# parameters
noisy_trace_prob = 0.7
noisy_event_prob = 0.7
log_size = 1000

if not os.path.exists(xes_dir):
    os.makedirs(xes_dir)

if not os.path.exists(xes_dir_noisy):
    os.makedirs(xes_dir_noisy)


################ Part 1

# create event logs from the resulting BPMAI petri nets
def create_xes_logs():
    petrinets = [f for f in os.listdir(model_dir)]
    count = 1
    for petrinet in petrinets:
        id = os.path.basename(petrinet).split('.')[0]
        print(id)
        print(f"\n")
        net, initial_marking, final_marking = pickle.load(open(os.path.join(model_dir, petrinet), 'rb'))

        # verify if petrinet is sound
        is_sound_easy = check_easy_soundness_net_in_fin_marking(net, initial_marking, final_marking) 
    
        if is_sound_easy:
            log = simulate_log_extensive(net, initial_marking, final_marking)

        print(f"\n")
        if len(log) > 0:
            xes_file = os.path.join(xes_dir, id + ".xes")
            xes_exporter.apply(log, xes_file)

        # create noisy log
        noisy_log = insert_noise(log, noisy_trace_prob, noisy_event_prob, log_size)
        xes_noisy_file = os.path.join(xes_dir_noisy, id + ".xes")
        xes_exporter.apply(noisy_log, xes_noisy_file)

        print(f"\n")
       
        print("Finished " + str(count) + ' /' + str(len(petrinets)))
        count = count + 1
        print(f"\n")


def simulate_log_extensive(net, initial_marking, final_marking):
    variant = simulator.Variants.EXTENSIVE
    pre_log = simulator.apply(net, initial_marking, final_marking, variant=variant)

    ### remove not relevant labels from log (i.e: EventbasedGateway)
    log = EventLog()
    for pre_trace in pre_log:
        trace = Trace([event for event in pre_trace if is_relevant_label(event["concept:name"])])
        if len(trace) > 0:
            log.append(trace)
    
    print('Traces computed: ' + str(len(log)))
    return log


################ Part 2
def insert_noise(log, noisy_trace_prob, noisy_event_prob, log_size):
    if len(log) < log_size:
        # add additional traces until desired log size reached
        log_cpy = EventLog()
        for i in range(0, log_size):
            log_cpy.append(deepcopy(log[i % len(log)]))
        log = log_cpy
    classes = _get_event_classes(log)
    log_new = EventLog()
    for trace in log:
        if len(trace) > 0:
            trace_cpy = deepcopy(trace)
            # check if trace makes random selection
            if random.random() <= noisy_trace_prob:
                insert_more_noise = True
                while insert_more_noise:
                    # randomly select which kind of noise to insert
                    noise_type = random.randint(0, 2)
                    if noise_type == 0:
                        _remove_event(trace_cpy)
                    if noise_type == 1:
                        _insert_event(trace_cpy, classes)
                    if noise_type == 2:
                        _swap_events(trace_cpy)
                    # flip coin to see if more noise will be inserted
                    insert_more_noise = (random.random() <= noisy_event_prob)
            log_new.append(trace_cpy)
    #print('Noisy log size: ' + str(len(log_new)))
    return log_new


def _remove_event(trace: Trace):
    del_index = random.randint(0, len(trace) - 1)
    trace2 = Trace()
    for i in range(0, len(trace)):
        if i != del_index:
            trace2.append(trace[i])
    return trace2


def _insert_event(trace: Trace, tasks):
    ins_index = random.randint(0, len(trace))
    task = random.choice(list(tasks))
    e = Event()
    e["concept:name"] = task
    trace.insert(ins_index, e)
    return trace


def _swap_events(trace: Trace):
    if len(trace) == 1:
        return trace
    indices = list(range(len(trace)))
    index1 = random.choice(indices)
    indices.remove(index1)
    index2 = random.choice(indices)
    trace2 = Trace()
    for i in range(len(trace)):
        if i == index1:
            trace2.append(trace[index2])
        elif i == index2:
            trace2.append(trace[index1])
        else:
            trace2.append(trace[i])
    return trace2


def _get_event_classes(log):
    classes = set()
    for trace in log:
        for event in trace:
            classes.add(event["concept:name"])
    return classes

