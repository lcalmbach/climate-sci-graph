# import streamlit as st
import streamlit as st
import pandas as pd
import os
import datetime
import numpy as np

# from st_files_connection import FilesConnection
from helper import get_config_value

STATIONS_METADATA_URL = "./data/1_download_url_nbcn_homogen.csv"

DATA_DICT = {
    "stations_file": "https://data.geo.admin.ch/ch.meteoschweiz.klima/nbcn-tageswerte/liste-download-nbcn-d.csv",
    "current": {
        "target_file": "./data/climate-data-ncbn-current.parquet",
        "url": "url current year",
    },
    "previous": {
        "target_file": "./data/climate-data-ncbn-previous.parquet",
        "url": "url previous years (verified data)",
    },
}


@st.cache_data(show_spinner=False, ttl=3600 * 24)
def get_stations_metadata():
    def create_link(row):
        link_temlate = "https://www.meteoschweiz.admin.ch/service-und-publikationen/applikationen/messwerte-und-messnetze.html#param=messnetz-klima&station={}&lang=de&chart=month"
        url = link_temlate.format(row["abbreviation"])
        return url
    df = pd.read_csv(STATIONS_METADATA_URL, sep=";", encoding="utf-8")
    df.columns = [x.lower() for x in df.columns]
    df = df[df["abbreviation"].notna()]
    df["station-info"] = df.apply(create_link, axis=1)
    df.rename(
        columns={"station": "station name", "abbreviation": "station"}, inplace=True
    )
    return df


@st.cache_data(show_spinner=False, ttl=3600 * 24)
def get_stations_df():
    df = pd.read_csv(DATA_DICT["stations_file"], sep=";", encoding="cp1252")
    # st.write(123, df)
    df.columns = [x.lower() for x in df.columns]
    return df


def load_data(load_all_data: bool):
    def clean_data(df: pd.DataFrame):
        df.rename(columns={"station/location": "Station", "date": "Date"}, inplace=True)
        df["Date"] = df["Date"].astype(str)
        # Convert the column to datetime format
        df["Date"] = pd.to_datetime(df["Date"], format="%Y%m%d")
        # remove text columns then convert each column to float after
        # replacing the missing values - by None
        cols = df.columns.drop(["Station", "Date"])
        for col in cols:
            df[col] = df[col].replace("-", np.nan)
            df[col] = df[col].astype(float)
        # adds a Month and date column
        df["day"] = df["Date"].dt.dayofyear
        df["month"] = df["Date"].dt.month
        df["week"] = df["Date"].dt.isocalendar().week
        df["year"] = df["Date"].dt.year
        df["decade"] = (df["year"] // 10) * 10
        return df

    def write_to_parquet(mode: str):
        df_all = None
        list_files = list(url_df[DATA_DICT[mode]["url"]])
        for url in list_files:
            df = pd.read_csv(url, sep=";")
            df = clean_data(df)
            if df_all is None:
                df_all = df
            else:
                df_all = pd.concat([df_all, df], ignore_index=True)
        df_all.columns = [x.lower() for x in df_all.columns]
        df_all.to_parquet(DATA_DICT[mode]["target_file"], index=False)

    url_df = get_stations_df()
    url_df.dropna(subset=["station"], inplace=True)
    if load_all_data:
        write_to_parquet("previous")
    write_to_parquet("current")


def aggregate_data(df: pd.DataFrame):
    value_fields = df.columns.drop(["station"])
    df = df.groupby(["station"])[value_fields].agg(["min", "max"]).reset_index()


@st.cache_data(show_spinner=False, ttl=3600 * 24)
def get_data():
    """
    Combines previous and current data into a single DataFrame.

    :return: Combined DataFrame of previous and current data
    """
    # make sure the data exists and is recent
    if not os.path.exists(DATA_DICT["current"]["target_file"]):
        load_data(load_all_data=True)
    else:
        today = datetime.date.today()
        # Get February 1st of the current year
        feb_first = datetime.date(today.year, 2, 1)
        previous_df = pd.read_parquet(DATA_DICT["previous"]["target_file"])
        last_year = previous_df["year"].max()
        if today > feb_first and last_year < (today.year - 1):
            load_data(load_all_data=True)

    previous_df = pd.read_parquet(DATA_DICT["previous"]["target_file"])
    load_data(load_all_data=False)
    current_df = pd.read_parquet(DATA_DICT["current"]["target_file"])
    df = pd.concat([previous_df, current_df], ignore_index=True)
    return df


if __name__ == "__main__":
    load_data(load_all_data=True)
    # get_data()
