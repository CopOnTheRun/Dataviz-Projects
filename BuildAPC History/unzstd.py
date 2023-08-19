import pandas as pd
import re
from io import StringIO

def read_table(string):
    return pd.read_table(StringIO(string), sep="|", header=0, skipinitialspace=True).dropna(axis=1, how='all').iloc[1:]

chunks = pd.read_json("Data/buildapc_submissions.json", lines=True,
                      chunksize=10**5, convert_dates= ["created_utc"])
errors = 0
counter = 0
for chunk in chunks:
    #just testing for now
    if counter > 8:
        break
    #narrowing down the columns to what's important
    cols = ["created_utc", "author", "permalink", "title", "link_flair_text", "selftext"]
    chunk = chunk[cols]
    regex = r"\bType\|Item\|Price\b"
    df = chunk[chunk.selftext.str.contains(regex, case=False)]
    if not df.empty:
        print(df[["created_utc","author","selftext"]])
        regex2 = r"(\bType\|Item\|Price.*)\*\*Total"
        asdf = df.selftext.str.extract(regex2,flags=re.DOTALL)
        print(asdf)
        tab = read_table(asdf[0].iloc[0])
        split_reg = r"\W+@?\W+|$"
        cols = tab["Price"].str.split(split_reg, n=1, expand=True,)
        try:
            tab[["Price","Store"]] = cols
        except ValueError as e:
            print(e)
            print(tab)
            errors+=1
        tab = tab.dropna()
        print(tab[["Type","Price","Store"]])

    counter += 1
print(errors)
