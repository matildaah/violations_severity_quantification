from pm4py.objects.petri.petrinet import PetriNet
from pm4py.algo.enhancement.decision.algorithm import get_decision_points


# get start activities of a petri net model
def get_start_activities(net):
    n1 = PetriNet.Place('n1')
    found_n1 = False
    places = net.places
    for place in places:
        if n1.name == place.name:
            found_n1 = True

    if found_n1:
        initial_place = 'n1'
    else:
        initial_place ='source'

    pre_start_activities = place_to_transition(net, initial_place)
    
    # checks if the first transition = tau transition 
    # it indicates an AND construct -> further process the petri net model
    if len(pre_start_activities) < 2:
        place = list(pre_start_activities.keys())[0]
        if pre_start_activities[place][0] is None:
            tau_transition = place
            tau_transition_places = transition_to_place(net,tau_transition)
            pre_start_activities = {}
            for tau in tau_transition_places:
                pre_start_activities.update(place_to_transition(net,tau))

    start_activities = []
    keys = list(pre_start_activities.keys())
    for key in keys:
        start_activities.append(pre_start_activities[key][0])
    #print(start_activities)
    return start_activities


def get_end_activities(net):
    n2 = PetriNet.Place('n2')
    found_n2 = False
    places = net.places
    for place in places:
        if n2.name == place.name:
            found_n2 = True

    if found_n2:
        initial_place = 'n2'
    else:
        initial_place ='sink'

    pre_end_activities = place_to_transition_b(net, initial_place)
    
    # checks if the last transition of the petri net = tau transition 
    # it indicates an AND construct -> further process (backwards) the petri net model
    if len(pre_end_activities) < 2:
        place = list(pre_end_activities.keys())[0]
        if pre_end_activities[place][0] is None:
            tau_transition = place
            tau_transition_places = transition_to_place_b(net,tau_transition)
            pre_end_activities = {}
            for tau in tau_transition_places:
                pre_end_activities.update(place_to_transition_b(net,tau))

    end_activities = []
    keys = list(pre_end_activities.keys())
    for key in keys:
        end_activities.append(pre_end_activities[key][0])
    return end_activities



# get decision activities (activities which precede an XOR construct)
def get_decision_activity(net):
    decision_places = get_decision_points(net= net, labels=True,pre_decision_points=None, parameters=None)
    decision_activity =set()
    for key in decision_places:
        for arc in net.arcs:
            if arc.source in net.transitions:
                if arc.target.name == key:
                    decision_activity.add(arc.source.label)

    return decision_activity


########################################################################################

# 'helper' functions for get_start_activities() & get_end_activities()

# place to transition: forward looking
# use: get activities from petri net start in sequence & XOR constructs 
def place_to_transition(net, place):
    transition = {}
    for arc in net.arcs:
        if arc.source in net.places:
            if arc.source.name == place:
                # print(arc.target.label)
                transition[arc.target.name]= [arc.target.label]
    return transition

# place to transition: backward looking
# use: get activites leading to the end of a petri net in sequence & XOR construct 
def place_to_transition_b(net, place):
    transition = {}
    for arc in net.arcs:
        if arc.target in net.places:
            if arc.target.name == place:
                transition[arc.source.name]= [arc.source.label] # removed last entry: arc.target.name
    return transition



# transition to place: forward looking 
# get places leading to start activities in AND construct
def transition_to_place(net, transition):
    collect_places = []
    for arc in net.arcs:
        if arc.source in net.transitions:
            if arc.source.name == transition:
                collect_places.append(arc.target.name)
    
    return collect_places


# transition to place: backward looking
# get places following end activities in AND construct
def transition_to_place_b(net, transition):
    collect_places = []
    for arc in net.arcs:
        if arc.target in net.transitions:
            if arc.target.name == transition:
                collect_places.append(arc.source.name)
    
    return collect_places



