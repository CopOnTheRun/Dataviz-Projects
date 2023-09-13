import re
from io import StringIO
from datetime import datetime as dt
import pandas as pd

def read_md_table(row):
    """Turn a markdown table into a pandas dataframe"""
    try:
        cols = ["Type", "Item", "Price"]
        tab = pd.read_table(
                StringIO(row["selftext"]), sep="|", skipinitialspace = True, skiprows = 2,
                on_bad_lines = "error", dtype = str, lineterminator = "\n", na_values = ["", " "],
                usecols = [0,1,2], names = cols).dropna().dropna(axis = 1, how = "all")

    except Exception as e:
        print(e)

    else:
        tab["created_utc"] = row["created_utc"]
        tab["permalink"] = row["permalink"]
        tab.set_index("created_utc", inplace = True)

        if not tab.empty:
            return tab

def process_json(in_file, out_file, chunk_size = 10**5,):
    """Processes the json file containing raw reddit data and turns it into a more manageable csv"""

    #data is too big atm, must chunk it
    chunks = pd.read_json(in_file, lines=True,
                          chunksize=chunk_size, convert_dates= ["created_utc"],)

    #narrowing down the columns to what's important
    cols = ["created_utc", "permalink", "selftext"]

    for count, chunk in enumerate(chunks):
        start = dt.now()

        #this avoids set on copy warning
        new_tab = chunk[cols].copy(deep=True)

        #this will grab the text from the table and not the rest of the comment
        table_regex = r"(\bType\|Item\|Price.*?)Total"
        new_tab["selftext"] = new_tab["selftext"].str.extract(
                table_regex, flags=re.DOTALL)

        #narrows down to only rows with regex matches
        new_tab = new_tab.dropna()

        #now to apply the function to convert the string into a dataframe
        part_table = new_tab.apply(read_md_table, axis="columns",)

        #dropping more empty stuff
        part_table = part_table.dropna()

        #joining the series of dataframes into a single dataframe
        part_table = pd.concat(part_table.to_list())

        #only create the heading on the first loop
        if count == 0:
            part_table.to_csv(out_file, mode="w")
        else:
            part_table.to_csv(out_file, header=False, mode="a")

        end = dt.now()
        delta = end - start

        print(f"Finished processing chunk {count} in {delta} seconds.", flush=True)

def main():
    in_file = "Data/buildapc_submissinos.json"
    out_file = "Data/part_table.csv"
    process_json(in_file = in_file, out_file = out_file)

if __name__ == "__main__":
    main()
