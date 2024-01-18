import seaborn as sns
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.ticker as mtick
from scipy import stats
from numpy import linspace
import bar_chart_race as bcr
from datetime import datetime as dt

def quantile_year(df, name = "Images/quantile_year.svg"):
    """Creates a graph of the quantiled price across time"""
    fig, ax = plt.subplots(figsize=(9,7))
    link_group = df.groupby([df.Date.dt.to_period("M"), "permalink"])
    quantiles = [.9,.75,.5,.25,.1]
    #prettyfying
    quant_str = {x:f"{x:.0%}" for x in quantiles}

    monthly_quantile = link_group.Price.sum().groupby(level=0).quantile(quantiles)
    monthly_quantile.rename(quant_str,level=1,inplace=True)
    years = monthly_quantile.index.get_level_values(0).astype('datetime64[M]')
    price = monthly_quantile
    quants = monthly_quantile.index.get_level_values(1)
    sns.lineplot(x=years,y=price,hue=quants,ax=ax)
    ax.set_ylabel("Price Adjusted for Inflation")
    ax.set_title("Cost of the Nth Percentile PC on /r/buildapc by Year")
    ax.yaxis.set_major_formatter("${x:1,.0f}")
    ax.figure.tight_layout()
    ax.figure.savefig(name,)

def part_cost(df,):
    #this is so I can create a quantile column
    breakpoint()
    quantile = df.groupby('permalink').Price.sum().rank(pct=True).rename('quantile')
    #merges the column to the table
    df = df.merge(quantile, on='permalink')
    keeper_parts = ["CPU","Video Card", "Motherboard","Memory","Storage","Power Supply","Case"]
    all_parts = set(df.Type.unique())
    toss_parts = all_parts - set(keeper_parts)
    df.Type.replace(toss_parts,"Other",inplace=True)

    #why .99 instead of 0 for the quantiles?
    #because there's like argentinian dollars floating and other outliers
    #floating around in the dataset, and this might take some of them out
    quants = [0,.1,.25,.5,.75,.9,.99]
    fig,axs = plt.subplots(2, 3, sharey=True, figsize=(16,9))
    axs[0,0].set_ylim(top=.31)

    for i,x in enumerate(quants[:-1]):
        ax = axs.flatten()[i]
        lower = quants[i]
        upper = quants[i+1]
        quant_df = df[df['quantile'].between(lower,upper)]
        total_cost = quant_df.Price.sum()
        cost_per_comp = total_cost/len(quant_df.permalink.unique())
        part_cost = quant_df.groupby('Type').Price.sum()
        cost_by_part = part_cost/total_cost
        full_cost = "$" + (cost_per_comp*cost_by_part).round().astype(int).astype(str)
        full_cost = full_cost.reindex(keeper_parts+["Other"])
        sns.barplot(x=cost_by_part.index, y=cost_by_part.values, ax=ax,order=full_cost.index)
        title = f"{100*lower:.0f}-{100*upper:.0f}th Percentile: Total = ${cost_per_comp:.0f}"
        ax.set_title(title)
        ax.set(xlabel=None)
        ax.set_xticklabels(ax.get_xticklabels(),rotation=20,ha="right",)
        ax.set_yticklabels([f"{x:.0%}" for x in ax.get_yticks()])
        ax.bar_label(ax.containers[0], full_cost,)

    fig.suptitle("Average Cost of Each Component")
    fig.supxlabel("Part Type")
    fig.supylabel("Percent of Total")
    fig.tight_layout()
    fig.savefig("Images/Part_Breakdown.svg")

def bitcoin_vs_gpu_prices(df):
    fig,ax = plt.subplots()

    #constraints on dataframe
    is_gpu = df.Type == "Video Card"
    not_0 = df.Price != 0
    not_crazy = df.Price < df.Price.quantile(.999)
    dollars = df.Symbol == "$"
    gpu = df.loc[is_gpu & not_0 & not_crazy & dollars]

    #change index to datetime
    gpu.index = pd.to_datetime(gpu.Date)
    
    #quantiles
    quantiles = [.1,.25,.5,.75,.9]
    monthly_gpu = gpu.resample("1M").quantile(quantiles,numeric_only=True)[["Price","Value"]]

    #gets bitcoin prices
    btc_prices = pd.read_csv("Data/BTC-USD.csv")
    btc_prices.index = pd.to_datetime(btc_prices.Date)
    monthly_btc = btc_prices.Close.resample("1M").last()
    btc_df = pd.merge(monthly_gpu,monthly_btc,left_index=True,right_index=True)
    btc_df.index = btc_df.index.rename(["Date","Quantile"])
    btc_df["Close"] = btc_df.Close*btc_df.pop("Value")

    fig,ax = plt.subplots()
    median = btc_df[btc_df.index.get_level_values(1) == .5]
    cumsum = median.pct_change().cumsum()
    sns.lineplot(data = cumsum, x = cumsum.index.get_level_values(0),
                 y = "Close", ax = ax, label = "BTC-USD Rate")
    sns.lineplot(data = cumsum, x = cumsum.index.get_level_values(0), 
                 y = "Price", ax=ax, label = "Median GPU Price")
    ax.set_ylabel("Relative Change in Price")
    ax.set_title("Effects of Bitcoin on /r/buildapc GPU Price")
    fig.tight_layout()
    fig.savefig("Images/Relative_Change_in_BTC_&_GPU.svg")

    fig,ax = plt.subplots()
    sns.scatterplot(data = median, x="Close", y = "Price",
                    linewidth=0, alpha = .7, ax=ax)
    ax.set_ylabel("Median GPU Price")
    ax.set_xlabel("Bitcoin to USD Rate")
    ax.set_title("Bitcoin Price vs Median GPU Prices on /r/buildapc")
    ax.set_xscale("log",base = 2)
    ax.yaxis.set_major_formatter("${x:1.0f}")
    ax.xaxis.set_major_formatter("${x:1,.0f}")
    ax.set_xticks([500,10**3,5*10**3,10**4,5*10**4])

    #linear regression
    m, b, r, *_ = stats.linregress(x = median.Close, y = median.Price)
    x = linspace(median.Close.min(), median.Close.max(), 1000)
    y = m*x+b
    sns.lineplot( x = x, y = y, 
                 label = f"$y = {m*1000:.2}\\times 10^{{-3}}x + {b:.0f}$", ax = ax)
    fig.tight_layout()
    fig.savefig("Images/BTC_vs_Median_GPU.svg")

def process_frame(df,part):
    match part:
        case "Video Card":
            gpus = df.Type == part
            regex = r"((?:[GR]TX?|Quadro|Radeon|Arc).*?[MG]B)"
            df.loc[gpus,"Item"] = df.loc[gpus,"Item"].str.extract(regex, expand=False)
            df.loc[gpus,"Item"] = df.loc[gpus,"Item"].str.replace(" GB","GB")
        case "CPU":
            cpus = df.Type == part
            regex = r"(?:Intel|AMD)\s+(?:- )?(.*)\s+Processor"
            df.loc[cpus,"Item"] = df.loc[cpus,"Item"].str.extract(regex,expand=False)
            df.loc[cpus,"Item"] = df.loc[cpus,"Item"].str.replace(" GHz","GHz")
            df.loc[cpus,"Item"] = df.loc[cpus,"Item"].str.replace("Quad","4")
            df.loc[cpus,"Item"] = df.loc[cpus,"Item"].str.replace("Dual","2")
        case "Case": 
            cases = df.Type == part
            regex = r"(.*?)\s*(?:\(.*\))?(?:\s?[IA]TX|\sCase)"
            case_items = df.loc[cases,"Item"]
            case_items = case_items.str.extract(regex,expand=False)
            case_items = case_items.str.replace(" - "," ")
            case_items = case_items.str.replace("Cooler Master","C.M.")
            case_items = case_items.str.replace("Fractal Design","F.D.")
            case_items = case_items.str.replace("Tempered Glass","TG", case=False)
            df.loc[cases,"Item"] = case_items
        case "Storage":
            storage = df.Type == part
            items = df.loc[storage, "Item"]
            regex = r"(.*[TG]B).*?((?:NVME|Internal|Solid).*(?:Drive|Disk))"
            strings = items.str.extract(regex)
            items = strings[0] + " " + strings[1]
            items = items.str.replace(" - ", " ")
            items = items.str.replace("-Series", "")
            items = items.str.replace(r" ([GT]B)", r"\1",regex=True)
            #order matters for the next 2 lines!
            items = items.str.replace("NVME Solid State Drive", "NVME")
            items = items.str.replace(r"Solid State (?:Disk|Drive)", r"SSD", regex=True)
            items = items.str.replace("Internal Hard Drive", "HDD")
            df.loc[storage, "Item"] = items
        case "Power Supply":
            name = r"(?P<name>.*?)"
            wattage = r"(?P<watt>\d+) ?W"
            cert = r"(?:(?:80\+|80 PLUS)(?P<cert>.*)Certified)?"
            mod = r"(?P<mod>\w+[- ]Modular)?"
            rest = r"(.*) Power Supply"
            regex = f"{name}\s*{wattage}\s*{cert}\s*{mod}{rest}"
    return df

def parts_race(df, parts, num):
    part_frame = df[df.Type.isin(parts)]
    quarters = part_frame.index.to_period("Q")
    for x in parts:
        process_frame(part_frame, x)

    grouped_parts = part_frame.groupby(["Type",quarters]).Item.value_counts(normalize=True)
    truncated_parts = grouped_parts.groupby(level=[0,1]).head(num)
    wide_parts = truncated_parts.unstack([0,2],0)*10000

    fig_kwargs = {'figsize': (8,4),
                  'dpi': 250}
    for x in parts:
        start = dt.now()
        bcr.bar_chart_race(
            df = wide_parts[x],
            title = f"Relative Popularity of {x}s on /r/buildapc",
            filename = f"chart_race_{x}.mp4",
            fig_kwargs = fig_kwargs,
            n_bars = num,
            period_length = 3000,
            steps_per_period = 100,
            end_period_pause = 700,
            )
        print(f"{x} finished after: {dt.now() - start}")

def main():
    df = pd.read_csv("Data/part_table_cleaned.csv", parse_dates=["created_utc"])
    renames = {"Price": "Price (unadjusted)", "Price_Adj":"Price", "created_utc":"Date"}
    df.rename(renames, inplace=True, axis="columns")
    df.index = pd.to_datetime(df.Date)
    sns.set_theme()
    whole = df.whole_comp == True
    dollar = df.Symbol == "$"
    after_2012 = df.Date >= "2013-01-01"
    breakpoint()
    full_parts = df.loc[whole & dollar & after_2012]
    quantile_year(full_parts)
    part_cost(full_parts)
    bitcoin_vs_gpu_prices(df)
    #parts = ["Storage"]
    #parts_race(df, parts , 8)

if __name__ == "__main__":
    main()
