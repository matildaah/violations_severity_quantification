import numpy as np
import gensim.downloader as api
from gensim.utils import simple_preprocess
from gensim.corpora import Dictionary
from gensim.similarities import WordEmbeddingSimilarityIndex
from gensim.similarities import SparseTermSimilarityMatrix
from gensim.similarities import SoftCosineSimilarity



# create the term similarity matrix
def compute_sim_index (value_added_activities, log_events):
    corpus = [simple_preprocess(activity) for activity in value_added_activities]
    queries = [simple_preprocess(event) for event in log_events]

    # load only if not already in memory
    if 'glove' not in locals(): 
        glove = api.load("glove-wiki-gigaword-50")
        
    similarity_index = WordEmbeddingSimilarityIndex(glove)
    dictionary = Dictionary(corpus + queries)
    similarity_matrix = SparseTermSimilarityMatrix(similarity_index, dictionary)
    bow_corpus = [dictionary.doc2bow(document) for document in corpus]
    sim_index = SoftCosineSimilarity(bow_corpus, similarity_matrix)

    return sim_index, dictionary

# perform a similarity query: get the matched activity & respective similarity score 
def get_similarity(value_added_activities, log_events, dictionary, sim_index, event):
    # remove finding the index --> simply add to simple_preprocess(event)
    index = log_events.index(event)
    bow_query = dictionary.doc2bow(simple_preprocess(log_events[index]))
    doc_similarity_scores = sim_index[bow_query]
    sorted_indexes = np.argsort(doc_similarity_scores)[::-1]        
    sim_score = doc_similarity_scores[sorted_indexes[0]]
    sim_activity = value_added_activities[sorted_indexes[0]]

    return sim_activity, sim_score



