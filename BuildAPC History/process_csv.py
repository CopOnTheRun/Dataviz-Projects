import pandas as pd

from datetime import datetime as dt

def inflation(start, end, index_to=-1):
    """Returns a table with US inflation data indexed to some time period."""

    #inflation is based on the CPI-U, downloaded from BLS
    inf_df = pd.read_csv("Data/inflation.csv")
    #don't need to first and second half of the year data
    inf_df = inf_df[~inf_df.Period.str.contains("S")]
    #fixing formatting
    inf_df.rename({"Period":"Month"},inplace=True,axis='columns')
    inf_df["Month"] = inf_df["Month"].str.removeprefix("M")
    #to_datetime needs a day even though we don't have one
    inf_df["Day"] = "01"
    inf_df.index = pd.to_datetime(inf_df[["Year","Month","Day"]])

    #don't need this stuff anymore
    inf_df.pop("Day")
    inf_df.pop("Month")
    inf_df.pop("Year")
    inf_df.pop("Series Id")

    #slices the dataframe to appropriate date values
    after_start = inf_df.index >= pd.to_datetime(start)
    before_end = inf_df.index < pd.to_datetime(end)
    inf_df = inf_df.loc[after_start & before_end]

    #indexes the values to the last year/month
    inf_df.Value = 1/(inf_df.Value/inf_df.Value.iloc[index_to])
    return inf_df

def inflation_merge(part_table, inflation):
    """Merges inflation data with the part_table"""
    pt = part_table.assign(year_month=part_table.index.to_period("M"))
    inf = inflation.assign(year_month=inflation.index.to_period("M"))
    df3 = pd.merge(pt,inf)
    df3["Price_Adj"] = df3["Price"]*df3["Value"]
    df3.drop("year_month", axis = 1, inplace=True)
    return df3

def part_min(df):
    """Defines if there is a minimally viable computer in the dataframe."""
    #this is a minimum computer for my purposes
    parts = ["CPU","Video Card", "Motherboard", "Memory","Storage","Power Supply","Case"]
    minimum_series = pd.Series(parts)
    has_parts = minimum_series.isin(df["Type"]).all()
    paid_for_parts = df["Price"].sum() != 0 
    df["whole_comp"] = has_parts and paid_for_parts
    return df

def process_frame(df):
    """Takes the minimally processed csv from process_json and cleans it substantially"""

    start = dt.now()
    #datetime instead of string
    df["created_utc"] = pd.to_datetime(df["created_utc"])
    df.index = df["created_utc"]
    print(f"datetime: {dt.now()-start}")

    start = dt.now()
    df["permalink"] = df["permalink"].str.removeprefix("/r/buildapc/comments/")
    print(f"permalink clean: {dt.now()-start}")

    start = dt.now()
    #cleans up the Type columns a bit
    df["Type"] = df["Type"].str.strip(" :*\\")
    print(f"clean type: {dt.now()-start}")

    start = dt.now()
    #removing uneeded stuff
    df = df.loc[~(df["Type"] == "----")]
    print(f"remove ----: {dt.now()-start}")

    start = dt.now()
    #cutting off long tails
    types = df.Type.value_counts()[:25].index
    df = df.loc[df.Type.isin(types)]
    print(f"cut tails: {dt.now()-start}")

    start = dt.now()
    #splits the Price into Symbol, Price and Store components
    price_regex = r"([$|€|£|¥|₹])([0-9,]+(?:\.[0-9]{2})?)(?: @ ([\w .&;]*)\b)?"
    df[["Symbol","Price","Store"]] = df.pop("Price").str.extract(price_regex)
    print(f"price regex: {dt.now()-start}")

    start = dt.now()
    #converts price into a numeric
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    print(f"to nunmeric: {dt.now()-start}")

    start = dt.now()
    #strips whitespace from store component
    df["Store"] = df["Store"].str.strip(" ")
    print(f"strip store whitespace: {dt.now()-start}")

    start = dt.now()
    #replaces html code ampersand with string representation
    df["Store"] = df["Store"].str.replace("&amp;","&")
    print(f"replace ampersand: {dt.now()-start}")

    start = dt.now()
    #combines microcenter and Micro Center
    micro = df.Store.str.contains("microcenter", case=False, na=False)
    df.loc[micro, "Store"] = "Micro Center"
    print(f"combine micros: {dt.now()-start}")

    start = dt.now()
    #extracts the item name from the link
    link_text_regex = r"\[(.*?)\]"
    df["Item"] = df["Item"].str.extract(link_text_regex)
    print(f"extract link: {dt.now()-start}")

    start = dt.now()
    #adds a complete build row
    df = df.groupby('permalink').apply(part_min)
    print(f"complete build: {dt.now()-start}")

    start = dt.now()
    inf = inflation(df.index.min(), df.index.max())
    df = inflation_merge(df,inf)
    print(f"inflation: {dt.now()-start}")

    return df

def main():
    in_file = "Data/part_table.csv"
    df = pd.read_csv(in_file, lineterminator="\n")
    df = process_frame(df,)
    cleaned_file = "Data/part_table_cleaned.csv"
    df.to_csv(cleaned_file, index=False)

if __name__ == "__main__":
    main()
