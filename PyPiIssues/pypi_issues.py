import json
import requests 
import re

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

# Very much created in the morning before my interview
# don't read this code for you own sanity's sake
def grab_all_dem_issues(filename: str = "pypi_issues.json"):
    url = "https://api.github.com/repos/pypi/Support/issues"

    #rate limited to 60req/hr so you should be able to grab 6k issues
    #I think 100 per page is the max
    fields = {"per_page": 100, "state":"all"}
    r = requests.get(url, params=fields)

    #grabs the last page from the initial headers
    last_re = r'page=(?P<last_page>\d+)>; rel="last"'
    links = r.headers["Link"]
    match = re.search(last_re,r.headers["Link"])
    last_page = int(match["last_page"])
    issues = r.json()

    for page in range(2,last_page+1):#first page added, half open intervals
        fields["page"] = page
        r = requests.get(url,params=fields)
        if r.ok:
            issues += r.json()

    with open(filename,"w") as f:
        f.write(json.dumps(issues, indent=2))

def wrangle_that_data(filename: str = "pypi_issues.json"):
    keep = ["title","number","state","created_at","closed_at","html_url"]
    issues = ["name","color"]
    df = pd.read_json(filename)[keep]
    pypi_json = json.load(open("pypi_issues.json"))
    df = df.set_index("number")
    normalize = pd.json_normalize(pypi_json, "labels", meta="number")
    awaiting = normalize["name"] == "status: awaiting response"
    triag = normalize["name"] == "requires triaging"
    labels = normalize[~(awaiting | triag)]
    uniques = labels.drop_duplicates("number").set_index("number")
    df[["label","color"]] = uniques[issues]
    df["closed_at"].fillna(pd.Timestamp.now("UTC"),inplace=True)
    df["time_open"] = df["closed_at"] - df["created_at"]
    return df


df = wrangle_that_data()
closed_issues = df[df["state"] == "closed"]
open_issues = df[df["state"] == "open"]
sns.set_theme()
fig,ax = plt.subplots(figsize=(14,9))
sns.boxplot(data = df, x = "label", y = closed_issues["time_open"].dt.days, 
                 showfliers=None, ax = ax)

ax.set(ylabel="Time Open (days)")
fig.suptitle("Number of Days to Close an Issue by its Github Label")
fig.tight_layout()
fig.savefig("time_open.svg")

fig,ax = plt.subplots(figsize=(14,9))
sns.histplot(data = open_issues, x = "label")
fig.suptitle("Number of Open Issues by Github Label")
fig.tight_layout()
fig.savefig("number_open_issues.svg")

fig,ax = plt.subplots(figsize=(10,8))
created_by_year = df.groupby(df["created_at"].dt.year).count()
sns.barplot(x = created_by_year.index, y = created_by_year["created_at"])
fig.suptitle("Number of Issues Created by Year")
ax.set(xlabel = "Year", ylabel = "Count")
fig.tight_layout()
fig.savefig("created_by_year.svg")
