from pathlib import Path

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from adjustText import adjust_text

data_dir = Path("Data")
image_dir = Path("Images")
headers = ["Drink", "fl oz", "Calories", "Caffeine (mg)", "mg/ floz"]

tabs = []
for file in data_dir.glob("*.txt"):
    tab = pd.read_table(file, names=headers)
    stem = file.stem.replace("_"," ").title()
    tab["Type"] = stem
    tabs.append(tab)

caf_tab = pd.concat(tabs)
#caf_tab = pd.read_csv(data_dir / "Caffeine_Content.csv")
years = pd.read_csv(data_dir / "Energy_Drink_Release.csv",
                    usecols=["Name","Release Year","Source"])
#cleaning up a little
caf_tab["Drink"] = caf_tab["Drink"].str.strip()
years["Name"] = years["Name"].str.strip()

caf_tab = caf_tab.merge(years, left_on="Drink", right_on="Name", how="outer")
caf_tab["Drink"] = caf_tab["Drink"].fillna(caf_tab["Name"])
caf_tab.drop("Name",inplace=True, axis='columns')
caf_tab.to_csv(data_dir / "Caffeine_Table.csv", index=False)

caf_tab["cal/oz"] = caf_tab["Calories"]/caf_tab["fl oz"]

sns.set_theme()
fig,ax = plt.subplots()
title = "Caffeine Content in Energy Drinks Over Time"
ax.set_title(title)
not_na = caf_tab["Release Year"].notna()
energy = caf_tab["Type"] == "Energy Drink"
caf_years = caf_tab.loc[energy & not_na]
sns.scatterplot(data = caf_years, ax = ax, 
                x = "Release Year", y = "Caffeine (mg)", hue = "Calories",
                alpha = .8, linewidth = 0)

#h, l = ax.get_legend_handles_labels()

popular_drinks = {"Red Bull":"Red Bull", "Monster Energy":"Monster",
                  "Rockstar Energy Drink (Original)":"Rockstar",
                  "Celsius Energy Drink":"Celsius", "Prime Energy Drink":"Prime",
                  "Bang Energy":"Bang","NOS Energy Drink":"NOS",}

pop_frame = caf_years[caf_years["Drink"].isin(popular_drinks)]
atts = ["Drink","Release Year","Caffeine (mg)"]
print(pop_frame[atts])
texts = []
for drink,year,caf in pop_frame[atts].itertuples(index=False):
    texts.append(ax.text(year,caf,popular_drinks[drink]))
    print(drink,year,caf)
print(caf_tab)
adjust_text(texts,arrowprops=dict(arrowstyle='-',color='black'))

#print(h)
#print(h[0],h[5])
#ax.get_legend().remove()
#ax.legend(h[:4],l[:4],loc = "upper left",)
fig.tight_layout()
fig.savefig(image_dir / "Caffeine_Years.png",dpi=300)

fig,ax = plt.subplots()
sns.scatterplot(data=caf_tab, x="fl oz", y= "Caffeine (mg)",
                      hue = "Type", alpha = .6,
                ax=ax, linewidth = 0)
bottom = ax.get_ylim()[0]
right = ax.get_xlim()[1]
fig.text(.6,.01,"Sources: caffeineinformer.com & data.ftl.studio/high-on-caffeine")
fig.tight_layout()
ax.set_ylim([-10,550])
ax.set_xlim([-2,27])
ax.figure.savefig(image_dir / "Caffeine_Size_Type.svg")

