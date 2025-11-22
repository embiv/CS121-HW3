import json
from indexer import get_partition #useful to find out which inverted_index_*.json to use 
from nltk.stem import PorterStemmer # for better textual matches
from pathlib import Path
import math

# path of index data
BASE_DIRECTORY = Path(__file__).parent.resolve()

#folder path
INDEX_SET_FOLDER = BASE_DIRECTORY / "index_data" #should make a folder named "index_data" that had the doc_map.tsv and the partials

#folder path to get the doc map
DOCMAP_PATH = INDEX_SET_FOLDER / "docmap.tsv"

#start of partial index
PARTIAL_INDEX_START = "inverted_index_"

#acting as cache for partial indexes so dont have to look them up often
loaded_partials = {}

# make docmap dictionary for easy look up
DOC_INDEX = {}

stemmer = PorterStemmer()

# make the load_docmap so mapping is made into dictionary
def load_docmap():
    with open(DOCMAP_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            doc_id, url = line.strip().split("\t", 1)
            DOC_INDEX[int(doc_id)] = url


# process query like how we did to make tokens,
#assume use of PORTERSTEMMER so get the same tokens
#return lis of stems?
def normalize_query(q):
    tokens = []
    for token in q.lower().split():
        stem = stemmer.stem(token)
        tokens.append(stem)
    return tokens


#load relevant partial to loaded_partials
def load_partial(partial):
    if partial in loaded_partials:
        return loaded_partials[partial]

    filename = INDEX_SET_FOLDER / f"{PARTIAL_INDEX_START}{partial}.json" #change part to partial
    if not filename.exists():
        loaded_partials[partial] = {}
        return loaded_partials[partial]
    
    with open(filename,"r", encoding="utf-8") as f:
        loaded_partials[partial] = json.load(f)
    return loaded_partials[partial]


#get the postings, takes a token/stem
# use get partiton, checks the first char to spit out inverted_index_*
def get_postings(stem_term):
    part = get_partition(stem_term)
    partial_index = load_partial(part)

    return partial_index.get(stem_term, [])

#and only query
#uses the terms from process query
#uses get postings
#can probobly use .intersection?
def and_only_search(query): #should we change this to say w_ranking
    stems = normalize_query(query)

    # get postings
    posting_lists = []
    for s in stems:
        posting_lists.append(get_postings(s))
    
    if any(len(p) == 0 for p in posting_lists):
        return [] # no postings 
    
    docs = []
    posting_map = {} # doc_id : posting info
    for stem,plist in zip(stems,posting_lists):
        stem_dict = {p["doc_id"]: p for p in plist}
        posting_map[stem] = stem_dict
        docs.append(set(stem_dict.keys()))
    
    # AND intersections
    common_docs = set.intersection(*docs)

    if not common_docs:
        return []
    
    # ranking TF-IDF
    results = []
    N = len(DOC_INDEX)

    for doc_id in common_docs:
        score = 0.0
        for stem in stems:
            posting = posting_map[stem][doc_id] #think use posting_map not postings
            tf = posting["term frequency"]
            weight = posting["term weight (importance)"]

            df = len(posting_map[stem]) # doc freq
            idf = math.log((N+1)/(df+1)) + 1 

            score += (tf*idf* (1+weight))
        results.append((doc_id, score))
    
    # descending order
    results.sort(key=lambda x: x[1], reverse=True)
    return results
    

#need to actually decode the doc_id to actual url
#can use the global dictionary to do this
def doc_id_made_url(doc_id):
    return DOC_INDEX.get(doc_id, "URL not found.")


#output the 5 urls
#calls the and only search function
#decodes the doc id to actual url
def print_and_only_data(query, num_urls_to_show = 5):
    results = and_only_search(query)
    if not results:
        print("\nNo results found.")
        return
    
    print("\nTop 5 Results")
    for doc_id, score in results[:num_urls_to_show]:
        print(f"{score:.3f} - {doc_id_made_url(doc_id)}")


def ret_main():
    print("\nType a search query and press Enter key.")
    print("Type 'quit' or 'exit' to leave.")

    while True:
        try:
            query = input("\nSearch for: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nQuitting Search Engine.")
            break

        if not query:
            print("EMPTY QUERY TRY AGAIN")
            continue

        if query.lower() in {"quit", "exit"}:
            print("\nQuitting Search Engine.")
            break

        if query:
            print_and_only_data(query)

if __name__ == "__main__":
    load_docmap()
    ret_main() # to run everything