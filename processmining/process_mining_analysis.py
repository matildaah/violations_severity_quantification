import time
from pm4py.objects.log.log import EventLog
from pm4py.statistics.variants.log import get
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.conformance.alignments import algorithm as alignments


# if no reference process model is provided, discover a proces model using IMf
# if needed, change noise_threshold (default =0.2)
def discover_process_model(log, event_key):
    variant = inductive_miner.Variants.IMf
    noise_threshold = 0.2
    activity_key = event_key
    parameters_disc = {}
    parameters_disc[inductive_miner.Variants.IMf.value.Parameters.NOISE_THRESHOLD] = noise_threshold
    parameters_disc[inductive_miner.Variants.IMf.value.Parameters.ACTIVITY_KEY] = activity_key
    net, initial_marking, final_marking = inductive_miner.apply(log, parameters=parameters_disc, variant=variant)
    return net, initial_marking, final_marking


# run conformance checking analysis using A* algorithm
def run_conf_checking(log, event_key, net, initial_marking, final_marking):
    # define standard cost function
    model_cost_function = dict()
    sync_cost_function = dict()
    for t in net.transitions:
        # if the label is not None, we have a visible transition
        if t.label is not None:
            # associate cost 1 to each move-on-model associated to visible transitions
            model_cost_function[t] = 1
            # associate cost 1 to each move-on-log
            sync_cost_function[t] = 1
        else:
            # associate cost 0 to each move-on-model associated to hidden transitions
            model_cost_function[t] = 0
    
    parameters_conf = {}
    parameters_conf[alignments.Variants.VERSION_STATE_EQUATION_A_STAR.value.Parameters.PARAM_MODEL_COST_FUNCTION] = model_cost_function
    parameters_conf[alignments.Variants.VERSION_STATE_EQUATION_A_STAR.value.Parameters.PARAM_SYNC_COST_FUNCTION] = sync_cost_function
    parameters_conf[alignments.Variants.VERSION_STATE_EQUATION_A_STAR.value.Parameters.ACTIVITY_KEY] = event_key

    tic = time.perf_counter()
    aligned_traces = alignments.apply_log(log, net, initial_marking, final_marking, parameters=parameters_conf, variant=alignments.Variants.VERSION_STATE_EQUATION_A_STAR)
    toc = time.perf_counter()
    print(f"Computed optimal alignments in {toc - tic:0.4f} seconds")
    return aligned_traces

# get event log classes
def get_event_classes(log, event_key):
    event_classes = set()
    for trace in log:
        for event in trace:
            event_classes.add(event[event_key])
    return event_classes


# create a simplified event log with trace variants only
def create_simplified_log(log):
    simplified_log = EventLog()
    variants = get.get_variants_from_log_trace_idx(log)
    variants_count ={}
    alignments_map = {}
    for key in variants:
        trace = variants[key][0]
        variants_count[trace]= len(variants[key])

    for key in variants_count:
        simplified_log.append(log[key])
        idx = len(simplified_log) - 1
        alignments_map[idx] = variants_count[key]

    return simplified_log, alignments_map
