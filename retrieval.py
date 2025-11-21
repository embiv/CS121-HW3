import json
import sys
import os
from indexer import get_partition #useful to find out which inverted_index_*.json to use 
from nltk.stem import PorterStemmer # for better textual matches
from pathlib import Path

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
    pass


# process query like how we did to make tokens,
#assume use of PORTERSTEMMER so get the same tokens
#return lis of stems?
def normalize_query(q):
    pass



#load relevant partial to loaded_partials
def load_partial(partial):
    pass
 


#get the postings, takes a token/stem
# use get partiton, checks the first char to spit out inverted_index_*
def get_postings(stem_term):
    pass



#and only query
#uses the terms from process query
#uses get postings
#can probobly use .intersection?
def and_only_search(query):
    pass


#need to actually decode the doc_id to actual url
#can use the global dictionary to odo this
def doc_id_made_url(doc_id):
    pass


#output the 5 urls
#calls the and only search function
#decodes the doc id to actual url
def print_and_only_data(query, num_urls_to_show = 5):
    pass

def ret_main():
    print("Type a search query and press Enter key.")
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
            break

        if query:
            print_and_only_data(query)

if __name__ == "__main__":
    load_docmap()
    ret_main() # to run everything