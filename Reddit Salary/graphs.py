import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import pandas as pd

def format_currency_axis(ax, xaxis=True) -> None:
    if xaxis:
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f"${x/1000:.0f}k"))
    else:
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f"${x/1000:.0f}k"))

def salary_vs_comparisons(df: pd.DataFrame, filename: str):
    fig,axs = plt.subplots(2,2,sharey=True,)
    comparisons = ("Years on Reddit", "Comment Karma", "Link Karma", "Comment Score")
    for ax, var in zip(axs.flatten(),comparisons):
        sns.scatterplot(data=df, x = var, y = "Salary", ax = ax,
                    alpha = .2, linewidth = 0)
        ax.set(ylabel=None)
        format_currency_axis(ax,xaxis=False)
    axs[0][1].set_xscale("log") #Link Karma
    axs[1][0].set_xscale("log") #Comment Karma
    fig.supylabel("Salary")
    fig.suptitle("Redditor's Salary in Relation to Their ...")
    fig.tight_layout()
    fig.savefig(filename,dpi=300)

def salary_ecdf(df: pd.DataFrame, filename: str) -> None:
    fig,ax = plt.subplots()
    sns.ecdfplot(data=df,x="Salary",ax=ax)
    format_currency_axis(ax)
    fig.suptitle("Proportion of /r/rva making less than...")
    fig.savefig(filename,dpi=300)

def salary_box(df: pd.DataFrame, filename: str) -> None:
    fig,ax = plt.subplots()
    counts = df.value_counts("Flair")
    flairs = counts[counts>6]
    df = df[df["Flair"].isin(flairs.index)]
    groups = df.groupby("Flair").median(numeric_only=True).sort_values("Salary",ascending=False)
    format_currency_axis(ax)
    sns.boxplot(data=df,x="Salary",y="Flair",ax=ax,order=groups.index)
    fig.suptitle("Income by Neighborhood")
    fig.tight_layout()
    fig.savefig(filename,dpi=300)

def salary_hist(df: pd.DataFrame, filename: str) -> None:
    cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
    fig,ax = plt.subplots()
    sns.histplot(data=df, x="Salary",bins=range(0,51*10**4,10**4),ax=ax)
    fig.suptitle("r/rva Salary Histogram")
    mean = df["Salary"].mean()
    median = df["Salary"].median()

    #just data from google
    us_med = 31133
    va_med = 36895
    ax.axvline(us_med,color=cycle[2],label=f"US median income = ${us_med}")
    ax.axvline(va_med,color=cycle[3],label=f"Virginia median income = ${va_med}")
    ax.axvline(median, color=cycle[1], label = f"/r/rva's median salary = ${median:.0f}")
    ax.legend()
    format_currency_axis(ax)
    fig.savefig(filename,dpi=300)

def age_hist(df: pd.DataFrame, filename: str) -> None:
    fig,axs = plt.subplots(2,2,figsize=[8,6],sharey=True)
    attributes = ("Years on Reddit", "Comment Karma", "Link Karma")
    for ax,a in zip(axs.flatten(),attributes):
        sns.ecdfplot(data=df,x=a,hue="Group",ax=ax,)
    #ax.set_xlabel("Years on Reddit")
    axs[1,0].set_xscale("log")
    axs[0,1].set_xscale("log")
    sns.barplot(data=df,x="Group",y="Verified",ax=axs[1,1],errorbar=None)
    axs[1,1].set_ylabel("Proportion Verified")
    fig.suptitle("Salary Thread Accounts vs 500 Most Recent")
    fig.tight_layout()
    fig.savefig(filename,dpi=300)

def load_dataframe():
    salary = pd.read_csv("Reddit Salary.csv",index_col=0)
    new_comments = pd.read_csv("new_comments.csv",index_col=0,nrows=500)
    salary["Group"] = "Salary"
    new_comments["Group"] = "Recent"
    df = pd.concat([salary,new_comments],ignore_index = True)
    return df

def main():
    df = load_dataframe()
    salary = df[df["Group"] == "Salary"]
    sns.set_theme()
    salary_hist(salary,"Salary_Hist.png")
    salary_box(salary,"Salary_Box.png")
    age_hist(df,"Age_Hist.png")
    salary_vs_comparisons(salary,"salary_age.png")


if __name__ == "__main__":
    main()
