"""Function that returns data from ERA5
"""
# External modules
import sys, os, json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
from pandas.plotting import register_matplotlib_converters
import math
import time
from pathlib import Path
from tqdm import tqdm
import logging
import coloredlogs

# Locals
dirname = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(dirname)
from src.utils.settings import config


def get_era5(location="schwarzsee19"):

    with open("data/common/constants.json") as f:
        CONSTANTS = json.load(f)

    SITE, FOLDER = config(location)

    if location in ["schwarzsee19"]:
        df_in3 = pd.read_csv(
            "../ERA5/outputs/" + location[:-2] + "_2019.csv",
            sep=",",
            header=0,
            parse_dates=["When"],
        )

    if location in ["guttannen20"]:
        df_in3 = pd.read_csv(
            FOLDER["raw"] + "era5_2019.csv",
            sep=",",
            header=0,
            parse_dates=["time"],
        )
        df_in2 = pd.read_csv(
            FOLDER["raw"] + "era5_2020.csv",
            # "../ERA5/outputs/" + location[:-2] + "_2020.csv",
            sep=",",
            header=0,
            parse_dates=["time"],
        )
        df_in3 = df_in3.set_index("time")
        df_in2 = df_in2.set_index("time")
        df_in3 = pd.concat([df_in2, df_in3])
        df_in3 = df_in3.reset_index()

    if location in ["guttannen21"]:
        df_in3 = pd.read_csv(
            FOLDER["raw"] + "era5_2021.csv",
            # "../ERA5/outputs/" + location[:-2] + "_2021.csv",
            sep=",",
            header=0,
            parse_dates=["time"],
        )
        df_in2 = pd.read_csv(
            FOLDER["raw"] + "era5_2020.csv",
            # "../ERA5/outputs/" + location[:-2] + "_2020.csv",
            sep=",",
            header=0,
            parse_dates=["time"],
        )
        # df_in2 = df_in2.rename(columns={"When": "time"})
        # df_in3 = df_in3.rename(columns={"When": "time"})
        df_in3 = df_in3.set_index("time")
        df_in2 = df_in2.set_index("time")
        df_in3 = pd.concat([df_in2, df_in3])
        df_in3 = df_in3.reset_index()

    if location in ["guttannen22"]:
        df_in3 = pd.read_csv(
            FOLDER["raw"] + "era5_2022.csv",
            # "../ERA5/outputs/" + location[:-2] + "_2022.csv",
            sep=",",
            header=0,
            parse_dates=["time"],
        )
        df_in2 = pd.read_csv(
            FOLDER["raw"] + "era5_2021.csv",
            # "../ERA5/outputs/" + location[:-2] + "_2021.csv",
            sep=",",
            header=0,
            parse_dates=["time"],
        )
        # df_in2 = df_in2.rename(columns={"When": "time"})
        # df_in3 = df_in3.rename(columns={"When": "time"})
        df_in3 = df_in3.set_index("time")
        df_in2 = df_in2.set_index("time")
        df_in3 = pd.concat([df_in2, df_in3])
        df_in3 = df_in3.reset_index()

    if location in ["diavolezza21"]:
        df_in3 = pd.read_csv(
            "/home/suryab/work/ERA5/outputs/" + location[:-2] + "_2021.csv",
            sep=",",
            header=0,
            parse_dates=["When"],
        )
        df_in3 = df_in3.rename({"When": "time"})
        df_in3 = df_in3.set_index("time")
        df_in3 = df_in3.reset_index()

    if location in ["ravat20"]:
        df_in3 = pd.read_csv(
            "/home/suryab/work/ERA5/outputs/" + location[:-2] + "_2020.csv",
            sep=",",
            header=0,
            parse_dates=["When"],
        )
        df_in3 = df_in3.rename({"When": "time"})
        df_in3 = df_in3.set_index("time")
        df_in3 = df_in3.reset_index()

    time_steps = 60 * 60
    df_in3["ssrd"] /= time_steps
    df_in3["strd"] /= time_steps
    df_in3["fdir"] /= time_steps
    df_in3["wind"] = np.sqrt(df_in3["u10"] ** 2 + df_in3["v10"] ** 2)
    # Derive RH
    df_in3["t2m"] -= 273.15
    df_in3["d2m"] -= 273.15
    df_in3["t2m_RH"] = df_in3["t2m"]
    df_in3["d2m_RH"] = df_in3["d2m"]
    df_in3 = df_in3.apply(lambda x: e_sat(x) if x.name == "t2m_RH" else x)
    df_in3 = df_in3.apply(lambda x: e_sat(x) if x.name == "d2m_RH" else x)
    df_in3["RH"] = 100 * df_in3["d2m_RH"] / df_in3["t2m_RH"]
    df_in3["sp"] = df_in3["sp"] / 100
    # df_in3["tp"] = df_in3["tp"] * 1000  # mm
    df_in3["SW_diffuse"] = df_in3["ssrd"] - df_in3["fdir"]
    df_in3 = df_in3.set_index("time")

    # CSV output
    df_in3.rename(
        columns={
            "t2m": "temp",
            "sp": "press",
            # "tp": "ppt",
            "ssrd": "SW_global",
            "fdir": "SW_direct",
            "strd": "LW_in",
        },
        inplace=True,
    )

    df_in3 = df_in3[
        [
            "temp",
            "RH",
            # "ppt",
            "wind",
            "SW_global",
            # "SW_diffuse",
            "LW_in",
            "press",
            # "tcc",
        ]
    ]

    df_in3 = df_in3.round(3)

    df_in3 = df_in3.reset_index()
    df_in3.to_csv(FOLDER["input"] + "era5.csv")

    return df_in3


def e_sat(T, surface="water", a1=611.21, a3=17.502, a4=32.19):
    T += 273.16
    if surface == "ice":
        a1 = 611.21  # Pa
        a3 = 22.587  # NA
        a4 = -0.7  # K
    return a1 * np.exp(a3 * (T - 273.16) / (T - a4))
