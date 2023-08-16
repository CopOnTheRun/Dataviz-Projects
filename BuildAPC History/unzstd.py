import sys
from math import log
import datetime
import pandas as pd

chunks = pd.read_json("Data/buildapc_submissions.json", lines=True,
                      chunksize=10**3, convert_dates= ["created_utc"])

counter = 0
for chunk in chunks:
    #just testing for now
    if counter > 10:
        break
    #narrowing down the columns to what's important
    cols = ["created_utc", "author", "permalink", "title", "link_flair_text", "selftext"]
    chunk = chunk[cols]
    regex = r"\bType\|Item\|Price\b"
    df = chunk[chunk.selftext.str.contains(regex, case=False)]
    if not df.empty:
        print(df[["created_utc","author","selftext"]])
    counter += 1
