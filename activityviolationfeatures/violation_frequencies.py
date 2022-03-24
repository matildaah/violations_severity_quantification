

### Conformance violations related features


# count the frequencies: skip & add violations, synch moves
def violation_type(alignments, alignments_map, activity):
    add_pattern = ('>>', activity)
    skip_pattern = (activity, '>>')
    synch_pattern = (activity, activity)
   
    total_skip = 0
    total_add = 0
    total_synch = 0
    for index in range(len(alignments)):
        add_violation = 0
        skip_violation =  0
        synch = 0
        for move in alignments[index]['alignment']:
            if move == skip_pattern:
                skip_violation = skip_violation + 1
            elif move == add_pattern:
                add_violation = add_violation + 1
            elif move == synch_pattern:
                synch = synch +1
            else :
                pass
        total_skip = total_skip + skip_violation * alignments_map[index]
        total_add = total_add + add_violation * alignments_map[index]
        total_synch = total_synch + synch * alignments_map[index]
    return total_add, total_skip, total_synch 


# count the number of traces having a particular activity violation
def violation_log_trace(alignments, alignments_map, violation_pattern):
    trace_count = 0
    for index in range(len(alignments)):
        if violation_pattern in alignments[index]['alignment']:
            trace_count = trace_count + alignments_map[index]
        else:
            pass
    return trace_count












