import re
from extraction import extract
from nltk.stem import WordNetLemmatizer

lemmatizer = WordNetLemmatizer()
ext = extract.get_instance()

# preprocess event labels 
def preprocess_label(label):
    # handle newlines & carriage returns
    label = label.replace('\n', ' ').replace('\r', '')
  
    # handle camel case
    label = re.compile('(.)([A-Z][a-z]+)').sub(r'\1 \2', label)
    label = re.compile('([a-z0-9])([A-Z])').sub(r'\1 \2', label)
    
    # handle non-alphanumeric characters
    label = re.compile('[^a-zA-Z]').sub(' ', label)
    label = label.strip()

    # handle 1 character word parts
    label = " ".join([word for word in label.split() if len(word) > 1])
    label = label.strip()
    
    # make string  lower case
    label = label.lower()
    
    return label


# extract activities from labels | format: action (ACT) + business object (BO)
def get_activity_pattern(label):
    try:
        extraction = ext.extract_roles_from_label(label)
        roles = list(extraction.keys())
        if 'action:name' in roles and 'object:name' in roles:
            if len(extraction['action:name']) == 1 and len(extraction['object:name']) == 1:
                activity = extraction['action:name'][0]
                activity = lemmatize_activity(activity)
                business_object = extraction['object:name'][0]
                result = activity + " " + business_object
                return result
            else: 
                pass
        else:
            pass
    except:
        return


# lemmatize ACT tag
def lemmatize_activity(word):
    lemma = lemmatizer.lemmatize(word, pos='v')
    lemma = re.sub('ise$', 'ize', lemma)
    return lemma


# check if label of a BPMAI model is relevant 
def is_relevant_label(label):
    if label == "None":
        return False
    elif label == " ":
        return False
    elif label.isnumeric():
        return False
    elif "Message" in label:
        return False
    # handle: ParallelGateway, InclusiveGateway, EventbasedGateway, ComplexGateway, Exclusive_Databased_Gateway
    elif "Gateway" in label:
        return False
    elif label.startswith("EventSubprocess") or label.startswith("CollapsedEventSubprocess") or label.startswith("Subprocess"):
        return False
    elif label.startswith("Task") or label.startswith("task"):
        return False
    elif label.startswith("processparticipant"):
        return False
    # handle labels with 2 characters only(i.e observed labels in models: a,b,xy) 
    elif len(label) <= 2:
        return False
    else:
        return True


def parse_label(label):
    try:
        extraction = ext.extract_roles_from_label(label)
        roles = list(extraction.keys())
        if 'action:name' in roles and 'object:name' in roles:
            activity = extraction['action:name'][0]
            activity = lemmatize_activity(activity)
            business_object = extraction['object:name'][0]
            result = activity + " " + business_object
            return result
        elif 'action:name' in roles:
            activity = extraction['action:name'][0]
            activity = lemmatize_activity(activity)
            result = activity
            return result
        elif 'object:name' in roles:
            business_object = extraction['object:name'][0]
            result = business_object
            return result
        else:
            pass
    except:
        result ='n/a'
        return result