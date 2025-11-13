from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer # for better textual matches
import re
import os
import json
from pathlib import Path

class Posting:
    def __init__(self,url,doc_id):
        self.url = url
        self.doc_id = doc_id
        self.term_freq = 0
        self.term_weight = 0
    
    def post_report(self):
        report = {
        "doc_id": self.doc_id, "url": self.url, 
        "term frequency": self.term_freq, "term weight (importance)": self.term_weight
        }
        return report

stemmer = PorterStemmer()
BODY_WEIGHT = 1.0
IMPORTANT_WEIGHT = 2.0

def get_tokens_w_weights(html):
    tokens = []
    soup = BeautifulSoup(html, "lxml")
    
    normal_text = soup.get_text(" ", strip=True)
    for t in re.findall(r'\b[a-zA-Z0-9]+\b', normal_text.lower()):
        stem = stemmer.stem(t)
        tokens.append((stem, BODY_WEIGHT)) # token w weight
    
    # important tags: bold, titles, headers
    for tags in soup.find_all(['strong', 'b', 'title', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        for t in re.findall(r'\b[a-zA-Z0-9]+\b', tags.get_text().lower()):
            stem = stemmer.stem(t)
            tokens.append((stem, IMPORTANT_WEIGHT))
        
    return tokens

# ADD FUNCTION: inverted index() w path parameter
# read thru file and use get_token_w_weights() to extract tokens
# use posting class, update the attributes for each token
# create dict for token, posting 
# return dict 
def make_inverted_partial_index(folderpath, out_file, docs_seen=3000):
    index = {} #{doc_id: posting}
    doc_id = 0
    partial_id = 0
    num_partials = 0

    folder = Path(folderpath)
    out_file = Path(out_file)
    out_file.mkdir(parents=True, exist_ok=True)
    
    docmap_path = out_file / "docmap.tsv"

    with open(docmap_path, "w", encoding="utf-8") as docmap:

        for root, _, files in os.walk(folder):
            for file_name in files:
                if not file_name.lower().endswith(".json"):
                    continue
                
                file_path = Path(root) / file_name

                #load the json files
                with open(file_path, "r", encoding="utf-8") as file:
                    temp_object = json.load(file)

                url = temp_object.get("url", "")
                html = temp_object.get("content", "") or ""

                docmap.write(f"{doc_id}\t{url}\n")

                #get (token_stem, weight) from HTML
                token_weights = get_tokens_w_weights(html)
                
                if not token_weights:
                    #count document even if empty
                    doc_id += 1
                    continue

                #how many times see stem, raw cont, stem ->count
                freq_map = {}

                #total weight from stem, stem -> total imp weight
                weight_map = {}

                for stem, weight in token_weights:
                    #give current count of stem, if doesnt exist treat as 0, add 1 becuase token appears once
                    freq_map[stem] = freq_map.get(stem, 0) + 1
                    
                    #give current weight of stem, if doesnt exist treat as 0, add given weight 
                    weight_map[stem] = weight_map.get(stem, 0.0) + weight

                #put info into global inverted index
                for stem in freq_map:
                    if stem not in index:
                        index[stem] = {}
                    
                    postings_for_term = index[stem]

                    if doc_id not in postings_for_term:
                        postings_for_term[doc_id] = Posting(url, doc_id)
                    
                    posting = postings_for_term[doc_id]
                    posting.term_freq += freq_map[stem]
                    posting.term_weight += weight_map[stem]
                
                doc_id += 1

                #flushing
                if doc_id % docs_seen == 0:
                    write_partial_json(index, partial_id, out_file)
                    index.clear()
                    partial_id += 1
                    num_partials += 1
            
        #if after loop still terms in index, rellease contents one last time
        if index:
            write_partial_json(index, partial_id, out_file)
            index.clear()   
            partial_id += 1
            num_partials += 1
    
    summary_path = out_file / "summary.json"
    total_docs = doc_id

    data = {
        "num_documents" : total_docs,
        "num_partials": num_partials,
        "created_every_num of_docs": docs_seen
    }
    
    with open(summary_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    print("Index Done Building")
    print(f"Indexed Docs: {total_docs}")
    print(f"Num of partial indexs: {num_partials}")

    return total_docs, num_partials

def write_partial_json(index_block, partial_index, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    postings_obj_map = {}

    for term, postings_dict in index_block.items():
        postings_obj_map[term] = [p.post_report() for p in postings_dict.values()]

    out_path = out_dir / f"partial_{partial_index}.json"

    with open(out_path, "w", encoding="utf-8") as file:
        json.dump(postings_obj_map, file, ensure_ascii=False, indent=2)

    print(f"Current parsed pages sent to {out_path} with {len(postings_obj_map)} terms")



    
# ADD FUNCTION: to write results into txt or json file (later put into pdf)
# the number of indexed documents;
# the number of unique tokens;
# the total size (in KB) of your index on disk.
# return all the above 


def main():
    # ask for input or hard code the path of folder
    # if does not exist then raise error or print message

    # call rest of functions 
    pass

if __name__ == "__main__":
    main() # to run everything