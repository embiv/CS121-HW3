from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer # for better textual matches
import re


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
def get_tokens_w_weights(html):
    tokens = []
    soup = BeautfiulSoup(hmtl, "html.parser")
    
    normal_text = soup.get_text(" ", strip=True)
    for t in re.findall(r'\b[a-zA-Z0-9]+\b', normal_text.lower()):
        tokens.append((t, 1)) # token w weight
    
    # important tags: bold, titles, headers
    for tags in soup.find_all(['strong', 'b', 'title', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        for t in re.findall(r'\b[a-zA-Z0-9]+\b', tags.get_text().lower()):
            tokens.append(t,2)
    
    # stemming
    stemmed = []
    for word, weight in tokens:
        stemmed.append(stemmer.stem(word), weight)
    
    return stemmed

# ADD FUNCTION: inverted index() w path parameter
# read thru file and use get_token_w_weights() to extract tokens
# use posting class, update the attributes for each token
# create dict for token, posting 
# return dict 

# ADD FUNCTION: to write results into txt or json file (later put into pdf)
# the number of indexed documents;
# the number of unique tokens;
# the total size (in KB) of your index on disk.
# return all the above 

def main():
    # ask for input or hard code the path of folder
    # if does not exist then raise error or print message

    # call rest of functions 

if __name__ == "__main__":
    main() # to run everything