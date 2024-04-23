import seaborn as sns
import pandas as pd

from matplotlib import pyplot as plt

from get_10k_data import get_df

def graph_participant_hist(df):
    fig, ax = plt.subplots(figsize=(15,10))
    fig.suptitle("Monument Avenue 10k Participants")
    sns.histplot(df, x = "Age Group", hue = "Gender", ax=ax, linewidth=0,)
    ax.grid(axis='y')
    fig.tight_layout()
    fig.savefig("Images/10k_participants.svg")
    fig.savefig("Images/10k_participants.png", dpi=300)

def graph_finish_times(df, title, plot_type, size = (10,15), **kwargs):
    fig, ax = plt.subplots(figsize=size)
    fig.suptitle(title)
    chip_time  = df["Chip Time"].astype(int)/10**9/3600
    getattr(sns, plot_type)(data = df, x = chip_time, ax=ax, **kwargs)
    ax.set(xlabel = "Finish Time (hours)")
    fig.tight_layout()
    title_file = title.replace(" ","_")
    fig.savefig(f"Images/{title_file}.svg")
    fig.savefig(f"Images/{title_file}.png", dpi = 300)

def main():
    df = get_df()
    sns.set_theme()
    sns.set_style("dark")

    graph_participant_hist(df)
    five_df = df
    graph_finish_times(df, "Finish Times by Gender", "histplot", hue = "Gender",size=(8,5),linewidth=0 )
    five_df["5K SPLIT"] = df["5K SPLIT"].astype(int)/10**9/3600
    five_df = five_df[five_df["5K SPLIT"] >0]
    graph_finish_times(five_df, "Finish Times by 5k Split", "scatterplot", (8,5), y = "5K SPLIT", alpha=.1)
    graph_finish_times(df, "Finish Times by Age", "histplot", (8,8), y = "Age Group",)
    names = df["First Name"].value_counts()[:15]
    names_df = df[df["First Name"].isin(names.index)]
    graph_finish_times(names_df, "Finish Times by Name", "boxplot", y = "First Name", showfliers=False)
    toms = df[df["First Name"] == "Tom"]
    graph_finish_times(toms, "Finish Times by People Named Tom", "swarmplot", (9,5))

main()
