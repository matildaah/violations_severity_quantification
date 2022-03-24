
### Conformance violations related features : subsequent misalignments move

# get subsequent misalignment sequences
def get_misalignment_sequences(alignments,alignments_map):
    log_misalignment_indexes = misalignment_indexes(alignments)
    log_subsequent_misalignments = subsequent_misalignment_indexes(log_misalignment_indexes)
    misalignment_sequences = {}
    for index_mis in range(len(log_subsequent_misalignments)):
        for sequence in log_subsequent_misalignments[index_mis]:
            serie = tuple()
            for item in sequence:
                move = alignments[index_mis]['alignment'][item]
                serie = serie + (move,)
            if serie in misalignment_sequences:
                misalignment_sequences[serie] = misalignment_sequences[serie] + alignments_map[index_mis]
            else:
                misalignment_sequences[serie] = alignments_map[index_mis]
    total_sequences = 0
    for key in misalignment_sequences:
        total_sequences = total_sequences + misalignment_sequences[key]
    return misalignment_sequences, total_sequences


# get all misalignment indexes in the computed alignments
def misalignment_indexes(alignments):
    log_misalignments = {}
    pattern = ('>>', None)
    for index in range(len(alignments)):
        misalignment_indexes = []
        for (pointer,move) in enumerate(alignments[index]['alignment']):
            if ('>>' in move) and move != pattern:
                misalignment_indexes.append(pointer)

        log_misalignments[index] = misalignment_indexes
    
    return log_misalignments

# get all subsequent misalignment indexes in the computed alignments
def subsequent_misalignment_indexes(log_misalignment_indexes):
    log_subsequent_misalignments = {}
    for index in range(len(log_misalignment_indexes)):
        if len(log_misalignment_indexes[index]) >= 3:
            misalignments = log_misalignment_indexes[index]
            misalignment_subsequent =[]
            while len(misalignments) >= 3:
                misalignments, result = find_subsequent(misalignments)
                misalignment_subsequent.append(result)

            log_subsequent_misalignments[index] = misalignment_subsequent
        else:
            pass
        
    return log_subsequent_misalignments

# find sequences containing subsequent indexes: at least 3
# helper func for subsequent_misalignment_indexes()
def find_subsequent(list):
    for i in range(len(list)-1):
        j=i+1
        counter = 1
        for j in range(j,len(list)):
            if list[j]== list[i] + counter:
                counter = counter + 1 
            else:
                break
        break
    result = []
    if counter >=3:
        for k in range(counter):
            result.append(list[0])
            list.pop(0)
    else:
        for k in range(counter):
            list.pop(0)

    return list, result


# count the misalignment subsequences containing a specific violation (skip or add) pattern
def subsequent_count(misalignment_sequences, violation_pattern):
    total_count = 0
    for key in misalignment_sequences:
        if violation_pattern in key:
            total_count = total_count + misalignment_sequences[key]
        else:
            pass
    return total_count

