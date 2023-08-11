#!/usr/bin/env python

from matplotlib import pyplot as plt
import pandas as pd

#this data doesn't exist anymore lol
path = "../Data/battery_report.csv"

df = pd.read_csv(path, sep='\t+', engine='python')

to_date = lambda s: s.split(' ')[0]
df["PERIOD"] = pd.to_datetime(df["PERIOD"].apply(to_date))

charge = "CHARGE CAPACITY"
design = "DESIGN CAPACITY"

to_num = lambda s: int(s.split(' ')[0].replace(',',''))

df[charge] = df[charge].apply(to_num)

df[design] = df[design].apply(to_num)

df["Percent"] = df[charge]/df[design]*100

df["Diff"] = df["Percent"] - df["Percent"].shift(1)

plt.style.use("ggplot")
fig, ax = plt.subplots(1,1)
ax.set_title("Dell XPS 13 2-in-1 Battery Degredation")
ax.plot(df["Percent"],)
ax.set_ylim(0,100)
ax.set_ylabel("Battery Degredation")
ax.set_xlabel("Weeks of Ownership")
ax.axvline(51, color = "black",lw=.5,label="warranty expiration")
ax.legend()
fig.tight_layout()
fig.savefig("Battery Percent.svg")
fig.savefig("Battery Percentage.png", dpi=300)

ax.clear()
ax.set_title("Battery degredation per week")
ax.set_ylabel("Change in % per week")
ax.set_xlabel("Weeks of Ownership")
ax.bar(df.index[1:],df["Diff"][1:])
ax.axvline(51, color = "black",lw=.5,label="warranty expiration")
ax.legend(loc='lower left')
fig.savefig("Weekly Change.svg")
fig.savefig("Weekly Change.png",dpi=300)

