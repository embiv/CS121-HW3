import tkinter as tk
from tkinter import ttk
import time
import retrieval

class SearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESEM Search Engine")

        retrieval.load_docmap()

        # query input and button
        query_frame = ttk.Frame(root, padding=10)
        query_frame.pack(fill = "x")

        ttk.Label(query_frame, text = "Query:").pack(side="left")

        self.query = tk.StringVar()
        self.query_entry = ttk.Entry(query_frame, textvariable=self.query, width=60)
        self.query_entry.pack(side="left", fill="x", expand=True)

        self.query_entry.bind("<Return>", self.on_search)

        self.search_bttn = ttk.Button(query_frame, text="Search", command=self.searching)
        self.search_bttn.pack(side="left", padx=5)

        #results area
        results_frame = ttk.Frame(root, padding=10)
        results_frame.pack(fill="both", expand=True)

        self.results = tk.Text(results_frame, wrap="word", height=20)
        self.results.pack(side="left", fill="both", expand=True)

        #status info
        status_frame = ttk.Frame(root, padding=(10, 0, 10, 10))
        status_frame.pack(fill="x")
        self.status = tk.StringVar(value="Ready")
        self.status_lbl = ttk.Label(status_frame, textvariable=self.status)
        self.status_lbl.pack(side="left")


    def searching(self, event=None):

        
        search_query = self.query.get().strip()
        if not search_query:
            self.status.set("Please type a Search Query")
            return
        
        self.status.set(f"Searching for : {search_query!r} ...")
        self.root.update_idletasks()

        start = time.perf_counter()
        results = retrieval.and_only_search(search_query)
        end = time.perf_counter()
        elaspsed_ms = (end-start) * 1000 # query response time

        self.results.delete("1.0", tk.END)

        if not results:
            self.results.insert(tk.END, "No results found :(\n")
            self.status.set("No results.")
            return
        
        top_links = 5
        self.results.insert(tk.END, f"Top {min(top_links, len(results))} Results\n\n")

        for rank, (doc_id, score) in enumerate(results[:top_links], start=1):
            url = retrieval.doc_id_made_url(doc_id)
            self.results.insert(tk.END,
                                f"{rank}. Score: {score:.3f}\n URL: {url}\n\n")
        
        self.status.set(f"Found {len(results)} result(s). Showing TOP {min(top_links, len(results))}."
                        f"Search time: {elaspsed_ms:.1f} ms"
        )

if __name__ == "__main__":
    root = tk.Tk()
    search_gui = SearchGUI(root)
    root.mainloop()
