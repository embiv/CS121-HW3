from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer # for better textual matches
import re
import os
import json
from pathlib import Path
import string

class Posting:
    def __init__(self,url,doc_id):
        self.url = url
        self.doc_id = doc_id
        self.term_freq = 0
        self.term_weight = 0
    
    def post_report(self):
        report = {
        "doc_id": self.doc_id,
        "term frequency": self.term_freq, "term weight (importance)": self.term_weight
        }
        return report

stemmer = PorterStemmer()
BODY_WEIGHT = 1.0
IMPORTANT_WEIGHT = 2.0

# deals with broken html (i hope)
def get_tokens_w_weights(html):
    tokens = []
    if not isinstance(html, str):
        return []
    
    stripped = html.strip()
    if not stripped or stripped.startswith("http://") or stripped.startswith("https://"):
        return []
    
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception as e:
        return [] # parsing failed
    
    try:
        normal_text = soup.get_text(" ", strip=True)
    except Exception:
        normal_text = ""
    
    
    for t in re.findall(r'\b[a-zA-Z0-9]+\b', normal_text.lower()):
        stem = stemmer.stem(t)
        tokens.append((stem, BODY_WEIGHT)) # token w weight
    
    # important tags: bold, titles, headers
    try:
        imp_tags = soup.find_all(['strong', 'b', 'title', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    except Exception:
        important_tags = []
    
    for tags in imp_tags:
        for t in re.findall(r'\b[a-zA-Z0-9]+\b', tags.get_text(" ", strip=True).lower()):
            stem = stemmer.stem(t)
            tokens.append((stem, IMPORTANT_WEIGHT))
    
    return tokens

# ADD FUNCTION: inverted index() w path parameter
# read thru file and use get_token_w_weights() to extract tokens
# use posting class, update the attributes for each token
# create dict for token, posting 
# return dict 

# partitions while be a-z and other
PARTITIONS = list(string.ascii_lowercase) + ["other"]

BATCHSIZE = 10000

#helps show which partial file to look at
def get_partition(token):
    if not token:
        return "other"
    char = token[0].lower()
    return char if char in string.ascii_lowercase else "other"

def flush_partial_index(partial_index, out_folder, run_id):
    out_folder = Path(out_folder)

    for part, index in partial_index.items():
        postings_obj_map = {}

        for term, postings_dict in index.items():
            sorted_postings = sorted(postings_dict.values(), key=lambda p: p.doc_id)
            postings_obj_map[term] = [p.post_report() for p in sorted_postings]

        if not postings_obj_map:
            continue

        postings_obj_map = dict(sorted(postings_obj_map.items()))

        inverted_index_path = out_folder / f"inverted_index_{part}_run{run_id}.json"
        with open(inverted_index_path, "w", encoding="utf-8") as file:
            json.dump(postings_obj_map, file, ensure_ascii=False, indent=2)

def make_partial_inverted_indexes(folderpath, out_folder, batch_size):
    #will be sorted by alphabet(a-z) or other
    partial_index = {p: {} for p in PARTITIONS} 
    doc_id = 0
    docs_in_batch = 0
    run_id = 0

    folder = Path(folderpath)
    out_folder = Path(out_folder)
    out_folder.mkdir(parents=True, exist_ok=True)
    
    docmap_path = out_folder / "docmap.tsv"

    print("Creating Index")

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
                    docs_in_batch += 1

                    if docs_in_batch >= batch_size:
                        flush_partial_index(partial_index, out_folder, run_id)
                        partial_index = {p: {} for p in PARTITIONS}
                        docs_in_batch = 0
                        run_id += 1

                    continue

                #how many times see stem, raw countt, stem ->count
                freq_map = {}

                #total weight from stem, stem -> total imp weight
                weight_map = {}

                for stem, weight in token_weights:
                    #give current count of stem, if doesnt exist treat as 0, add 1 becuase token appears once
                    freq_map[stem] = freq_map.get(stem, 0) + 1
                    
                    #give current weight of stem, if doesnt exist treat as 0, add given weight 
                    weight_map[stem] = weight_map.get(stem, 0.0) + weight

                #put info into partial inverted index
                for stem in freq_map:
                    part = get_partition(stem)
                    index = partial_index[part]

                    if stem not in index:
                        index[stem] = {}
                    
                    postings_for_term = index[stem]

                    if doc_id not in postings_for_term:
                        postings_for_term[doc_id] = Posting(url, doc_id)
                    
                    posting = postings_for_term[doc_id]
                    posting.term_freq += freq_map[stem]
                    posting.term_weight += weight_map[stem]
                
                doc_id += 1
                docs_in_batch +=1

                if docs_in_batch >= batch_size:
                    flush_partial_index(partial_index, out_folder, run_id)
                    partial_index = {p: {} for p in PARTITIONS}
                    docs_in_batch = 0
                    run_id += 1
    
    if any(partial_index[p] for p in PARTITIONS):
        flush_partial_index(partial_index, out_folder, run_id)
        run_id += 1

    print(f"Indexing Done. Created {run_id} partial runs.")
    
    return doc_id, run_id

def merge_partial_indexes(out_folder, num_runs):
    out_folder = Path(out_folder)

    for part in PARTITIONS:
        merged = {}

        for run_id in range(num_runs):
            path = out_folder / f"inverted_index_{part}_run{run_id}.json"
            if not path.exists():
                continue

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for term, postings in data.items():
                if term not in merged:
                    merged[term] = []
                merged[term].extend(postings)
        
        if not merged:
            continue

        for term in merged:
            merged[term].sort(key=lambda p: p["doc_id"])

        merged = dict(sorted(merged.items()))

        final_index_path = out_folder / f"inverted_index_{part}.json"
        with open(final_index_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

# ADD FUNCTION: to write results into txt or json file (later put into pdf)
# the number of indexed documents;
# the number of unique tokens;
# the total size (in KB) of your index on disk.
# return all the above 
def m1_analytics(out_folder, num_docs):
    out_folder = Path(out_folder)

    num_unique_tokens = 0
    total_bytes = 0

    for part in PARTITIONS:
        index_path = out_folder / f"inverted_index_{part}.json"
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                num_unique_tokens += len(data)    
            total_bytes += index_path.stat().st_size
    
    docmap_path = out_folder / "docmap.tsv"    
    if docmap_path.exists():
        total_bytes += docmap_path.stat().st_size
    
    total_kb = round(total_bytes / 1024, 2)

    report_path = out_folder / "m1_report.txt"

    with open(report_path, "w", encoding="utf-8") as file:
        file.write(
            f"Number of Indexed Documents: {num_docs}\n"
            f"Number of Unique tokens: {num_unique_tokens}\n"
            f"Index size  on disk (final index and docmap): {total_kb} KB\n"
        )


def main():
    # ask for input or hard code the path of folder
    # if does not exist then raise error or print message
    # call rest of functions 
    #input_folder = "/home/ecasasca/cs121/a3/CS121-HW3/DEV"
    #output_folder = "/home/ecasasca/cs121/a3/CS121-HW3/PARTIALM1"

    input_folder = "/home/ebivian/CS121/HW3/CS121-HW3/DEV"
    output_folder = "/home/ebivian/CS121/HW3/CS121-HW3/PARTIALM1"

    num_docs, num_runs = make_partial_inverted_indexes(input_folder, output_folder, BATCHSIZE)

    merge_partial_indexes(output_folder, num_runs)

    m1_analytics(output_folder, num_docs)

if __name__ == "__main__":
    main() # to run everything