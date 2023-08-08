#!/usr/bin/env python

import calendar as cd
import pandas as pd
import seaborn as sns
import matplotlib
from dataclasses import dataclass
from pathlib import Path
from scipy import stats
from matplotlib import pyplot as plt
import matplotlib.dates as mdates


@dataclass
class ModifiedFrame:
    og_frame: pd.DataFrame
    entities: dict[str, str]
    columns: dict[str, str]

    def __post_init__(self):
        # only keeping the entities we care about
        # this creates a slice that is a copy, this is fine
        mod_frame = self.og_frame.copy(deep=True)
        mod_frame = mod_frame[self.og_frame["entity_id"].isin(self.entities.keys())]
        # changing the names to something prettier
        for k, v in self.entities.items():
            mod_frame["entity_id"] = mod_frame["entity_id"].str.replace(
                k, v, regex=False
            )

        # changing the columns to something prettier
        mod_frame = mod_frame.rename(columns=self.columns)

        self.mod_frame = mod_frame

    def __getitem__(self, item):
        return self.mod_frame[item]

    def __setitem__(self, key, value):
        self.mod_frame[key] = value

    @staticmethod
    def create_entities(ent_dict, case="power"):
        match case:
            case "power":
                return {
                    f"sensor.{k}_current_consumption": v for k, v in ent_dict.items()
                }
            case "contact":
                return {f"binary_sensor.{k}_contact": v for k, v in ent_dict.items()}
            case _:
                return "No good"

    @classmethod
    def power(cls):
        power = pd.read_csv(
            "Data/power_usage.csv",
        )

        # Why am I doing this? To make the graphs look prettier
        columns = {
            "day": "Day",
            "entity_id": "Device",
            "energy_kwh": "Energy (kWh)",
            "price_per_day": "Price Per Day ($)",
            "daily_duration_min": "Duration (m)",
            "quantity": "Times Opened Per Day",
            "day_of_week": "Day of the Week",
        }

        ents = {
            "archbox": "Desktop",
            "server": "Server",
            "big_boy": "TV",
            "monitor": "Monitor",
            "fridge": "Fridge",
        }

        power_entities = cls.create_entities(ents)
        return cls(power, power_entities, columns)

    @classmethod
    def contact(cls):
        states = pd.read_csv(
            "Data/fridge_states.csv",
        )

        columns = {
            "day": "Day",
            "entity_id": "Door",
            "state": "State",
            "daily_duration_min": "Duration (m)",
            "quantity": "Times Opened Per Day",
            "day_of_week": "Day of the Week",
        }

        ents = {
            "fridge": "Fridge",
            "freezer": "Freezer",
        }

        state_entities = cls.create_entities(ents, "contact")
        return cls(states, state_entities, columns)


def main():
    matplotlib.use("cairo")  # need this here for some reason

    create_swarm()

    # contact graph
    contact = ModifiedFrame.contact()
    contact["Day of the Week"] = contact["Day of the Week"].apply(
        lambda x: cd.day_abbr[x]
    )

    # manually changing it so that the on state is counted even when the total time is 0
    cond1 = contact["Duration (m)"] == 1440
    cond2 = contact["State"] == "off"
    contact.mod_frame.loc[cond1 & cond2, "Duration (m)"] = 0
    contact.mod_frame.loc[cond1 & cond2, "State"] = "on"
    contact.mod_frame.loc[cond1 & cond2, "Times Opened Per Day"] = 0

    # only looking at the states where the fridge is on
    on_states = contact[contact["State"] == "on"]

    # collecting the arguments to pass to seaborn
    seaborn_args = {}
    seaborn_args["data"] = on_states
    seaborn_args["hue"] = contact.columns["entity_id"]

    title = "Number of Times Opened"
    seaborn_args["x"] = "Times Opened Per Day"
    seaborn_args["binwidth"] = 5
    create_sensor_graph(title, **seaborn_args)

    title = "Cumulative Time Open Per Day"
    seaborn_args["x"] = "Duration (m)"
    seaborn_args["binwidth"] = 1
    create_sensor_graph(title, **seaborn_args)

    power = ModifiedFrame.power()

    # dataframe of just the fridge power
    fridge_power = power.mod_frame[power.mod_frame["Device"] == "Fridge"].set_index(
        "Day"
    )

    # joining the fridge power and contact dataframes
    joined = on_states.join(
        fridge_power,
        on="Day",
        rsuffix="_power",
    )

    on_fridge = joined[joined["Door"] == "Fridge"]
    on_freezer = joined[joined["Door"] == "Freezer"]
    fridge_freeze = joined.groupby(
        "Day",
    ).sum("Duration (m)")
    fridge_freeze["Energy (kWh)"] = fridge_freeze["Energy (kWh)"] / 2
    fridge_freeze["Price Per Day ($)"] = fridge_freeze["Price Per Day ($)"] / 2
    fridge_freeze["Door"] = "Fridge + Freezer"
    fridge_freeze.index.name = "Day"
    fridge_freeze.reset_index(inplace=True)
    both = pd.concat((joined, fridge_freeze))

    seaborn_args = {}
    seaborn_args["x"] = "Duration (m)"
    seaborn_args["y"] = "Energy (kWh)"
    seaborn_args["data"] = on_fridge
    seaborn_args["hue"] = "Door"

    title = "Fridge Cumulative Time Open"
    create_scatter(title, **seaborn_args)

    title = "Freezer Cumulative Time Open"
    seaborn_args["data"] = on_freezer
    create_scatter(title, **seaborn_args)

    title = "Fridge + Freezer Cumulative Time Open"
    seaborn_args["data"] = both
    create_scatter(title, ["Freezer", "Fridge", "Fridge + Freezer"], **seaborn_args)

    title = "Fridge Number of Times Opened"
    seaborn_args["x"] = "Times Opened Per Day"
    seaborn_args["data"] = on_fridge
    create_scatter(title, **seaborn_args)

    title = "Freezer Number of Times Opened"
    seaborn_args["data"] = on_freezer
    create_scatter(title, **seaborn_args)

    title = "Fridge + Freezer Number of Times Opened"
    seaborn_args["data"] = both
    create_scatter(title, ["Freezer", "Fridge", "Fridge + Freezer"], **seaborn_args)

    title = "Fridge + Freezer Time Open vs Cost"
    seaborn_args["data"] = both
    seaborn_args["x"] = "Duration (m)"
    seaborn_args["y"] = "Price Per Day ($)"
    create_scatter(title, ["Freezer", "Fridge", "Fridge + Freezer"], **seaborn_args)


def create_swarm():
    names = {
        "state_id": "State ID",
        "entity_id": "Door",
        "state": "State",
        "local_updated": "Time",
        "local_changed": "Changed",
    }

    on_times = pd.read_csv(
        "Data/modified_diff.csv",
        parse_dates=["local_updated"],
        index_col="local_updated",
    )

    ent_dict = {"fridge": "Fridge", "freezer": "Freezer"}
    ents = ModifiedFrame.create_entities(ent_dict, "contact")

    mod_frame = ModifiedFrame(on_times, ents, names).mod_frame

    mod_frame["Day"] = on_times.index.strftime("%a")
    time = on_times.index.strftime("%H:%M:%S")
    dummy_date = "2023-02-02"
    mod_frame["Time"] = pd.to_datetime(dummy_date + " " + time)

    with sns.axes_style("darkgrid"), sns.color_palette("deep"):
        fig, ax = plt.subplots(figsize=(14, 9))
        sns.swarmplot(
            data=mod_frame,
            x="Time",
            y="Day",
            hue="Door",
            size=3.2,
            alpha=0.9,
            dodge=True,
            order=list(cd.day_abbr),
        )
        sns.move_legend(
            ax,
            "lower right",
            bbox_to_anchor=(0.155, 0.99),
            ncol=2,
            title=None,
            frameon=False,
        )
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        title = "Every Time the Freezer and Fridge Were Opened Over 100 Days"
        ax.set_title(title)
        fig.tight_layout()
        save(fig, title)


def create_scatter(title, new_index=None, **kwargs):
    """Creates a scatterplot with one or multilple lines depending on whether new_index
    is defined"""
    df = kwargs["data"]
    x = kwargs["x"]
    y = kwargs["y"]
    asdf = df.groupby(kwargs["hue"])

    # creating the regression line
    regs = asdf.apply(lambda d: stats.linregress(x=d[x], y=d[y])).reindex(new_index)
    mins = asdf.min()[x].reindex(new_index)
    maxs = asdf.max()[x].reindex(new_index)
    m, b, r, *_ = stats.linregress(x=df[x], y=df[y])
    reg = stats.linregress(x=df[x], y=df[y])

    with sns.axes_style("darkgrid"), sns.color_palette("deep"):
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.scatterplot(linewidth=0, alpha=0.8, **kwargs)
        for reg, mn, mx in zip(regs, mins, maxs):
            m, b, r, *_ = reg
            sns.lineplot(
                x=(mn, mx),
                y=(mn * m + b, mx * m + b),
                label=f"$y = {m:.2f}x+{b:.2f}$\n$r^2={r**2:.2f}$",
            )
        ax.set_title(f"{title} vs energy consumed".title())
        sns.move_legend(ax, "lower right")
        fig.tight_layout()
        save(fig, title)


def create_sensor_graph(title="states", **kwargs):
    with sns.axes_style("darkgrid"), sns.color_palette("deep"):
        fig, ax = plt.subplots()
        sns.histplot(**kwargs)
        fig = ax.figure
        ax.set_title(f"{title}".title())
        ax.set_ylabel("Number of Days")
        fig.tight_layout()
        save(fig, title)


def save(figure, name, ext="svg", directory="Images"):
    new_name = name.replace(" ", "_")
    Path(directory).mkdir(parents=True, exist_ok=True)
    figure.savefig(Path(directory) / f"{new_name}.{ext}")


def create_energy_graph(df, x, y, hue=None, name="energy_usage.svg"):
    with sns.axes_style("dark"), sns.color_palette("deep"):
        fig, ax = plt.subplots(figsize=(5, 6))
        sns.boxplot(data=df, x=x, y=y, hue=hue)
        ax1 = fig.axes[0]
        ax2 = ax1.secondary_yaxis(
            "right",
            functions=(lambda x: x * 0.14, lambda x: x / 0.14),
        )
        ax2.set_ylabel("Cost ($)")
        ax2.yaxis.set_ticks_position("none")
        fig.suptitle("Daily Energy Usage and Cost Over 100 Days")
        fig.tight_layout()
        save(fig, name)


if __name__ == "__main__":
    main()
