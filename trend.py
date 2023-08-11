import streamlit as st
import pandas as pd
import numpy as np
import os
import pymannkendall as mk
from scipy import stats

from plots import time_series_chart
from helper import init_lang_dict_complete, get_lang, show_filter

PAGE = __name__
lang = {}
MIN_POINTS = 8


class TrendAnalysis:
    def __init__(self):
        global lang
        init_lang_dict_complete(os.path.basename(__file__), __name__)
        lang = get_lang(PAGE)

        self.data_df = st.session_state["station_data"]
        self.stations_dict = self.get_station_dict()
        # self.stat_function_dict = self.get_stat_function_dict()
        self.parameters_dict = self.get_parameter_dict()
        self.min_year, self.max_year = self.get_min_max_year()
        self.parameter_label = ""
        self.parameter = ""

    def get_lin_reg(self, df: pd.DataFrame):
        df = df.dropna(how="all")
        if len(df) > 2:
            df["X_numeric"] = (df["Date"] - df["Date"].min()).dt.days
            x = np.array(list(df["X_numeric"]))
            y = np.array(list(df[self.parameter]))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            return slope, intercept, r_value, p_value, std_err
        else:
            return None, None, None, None, None

    def get_min_max_year(self):
        min_year = self.data_df["Year"].min()
        max_year = self.data_df["Year"].max()
        return int(min_year), int(max_year)

    def filter_data(self, filters):
        df = self.data_df
        if "stations" in filters and filters["stations"] != []:
            df = df[df["Station"].isin(filters["stations"])]
        if filters["years"] != []:
            df = df[
                (df["Year"] >= filters["years"][0])
                & (df["Year"] <= filters["years"][1])
            ]
        if filters["months"] != []:
            df = df[df["Month"].isin(filters["months"])]
        return df

    def get_station_dict(self):
        df = st.session_state["station_url"].reset_index()
        keys = list(df["Abbreviation"])
        values = list(df["Station"])
        return dict(zip(keys, values))

    def get_parameter_dict(self):
        # column headers as used in dataframe
        keys = ["Temperature", "Precipitation"]
        values = lang["parameter-options"]
        return dict(zip(keys, values))

    def show_info(self):
        st.header(lang["title"])
        st.markdown(lang["intro"])

    def show_mann_kendall(self):
        """
        https://github.com/mmhs013/pymannkendall
        Hussain et al., (2019). pyMannKendall: a python package for non parametric Mann Kendall family of trend tests.. Journal of Open Source Software, 4(39), 1556, https://doi.org/10.21105/joss.01556
        """

        def get_filter():
            settings = {"stat_par": "", "stations": [], "years": [], "months": []}
            options = {
                "stations_dict": self.stations_dict,
                "min_year": self.min_year,
                "max_year": self.max_year,
            }
            filter = show_filter(settings, lang, options)
            return filter

        def get_summary_df(df, result):
            keys = ["years", "min", "max", "mean", "std", "result", "p", "slope"]
            values = [
                f"{df['Date'].min().year} to {df['Date'].max().year}",
                f"{df[self.parameter].min():.2f}",
                f"{df[self.parameter].max():.2f}",
                f"{df[self.parameter].mean():.2f}",
                f"{df[self.parameter].std():.2f}",
                result.trend,
                f"{result.p:.2E}",
                f"{result.slope:.4f}",
            ]
            df = pd.DataFrame({"Parameter": keys, "Value": values})
            return df

        def show_result(result):
            ok = display == lang["display-options"][0]
            ok = ok or (
                display == lang["display-options"][1] and result.trend == "increasing"
            )
            ok = ok or (
                display == lang["display-options"][2] and result.trend == "decreasing"
            )
            ok = ok or (
                display == lang["display-options"][3] and result.trend == "no trend"
            )
            return ok

        self.parameter = st.sidebar.selectbox(
            label=lang["parameter"],
            options=list(self.parameters_dict.keys()),
            format_func=lambda x: self.parameters_dict[x],
        )
        self.parameter_label = self.parameters_dict[self.parameter]
        display_options = lang["display-options"]
        display = st.sidebar.selectbox(lang["display"], options=display_options)
        settings = {
            "x": "Date",
            "y": self.parameter,
            "x_title": "",
            "y_title": self.parameter_label,
            "tooltip": ["Station", "Date", self.parameter],
            "width": 800,
            "height": 300,
        }
        settings["show_regression"] = st.sidebar.checkbox("Show linear regression")
        station_data = self.filter_data(get_filter())
        num_stations = st.empty()
        # settings["x_domain"] = [
        #     f"{data['Date'].min().year}-01-01",
        #     f"{data['Date'].max().year}-12-31",
        # ]
        min_y = int(station_data[self.parameter].min()) - 1
        max_y = int(station_data[self.parameter].max()) + 1
        settings["y_domain"] = [min_y, max_y]
        cnt_stations = 0
        cnt_all_stations = 0

        for station in self.stations_dict.keys():
            cols = st.columns([3, 1])
            df = station_data[station_data["Station"] == station].sort_values(by="Date")
            df = df.dropna(subset=[self.parameter])
            if len(df) > MIN_POINTS:
                # settings['x_domain'] = [ f"{df['month_date'].min().year}-01-01", f"{df['month_date'].max().year}-12-31"]
                cnt_all_stations += 1
                values = list(df[self.parameter])
                result = mk.seasonal_test(values, 12)
                settings[
                    "title"
                ] = f"{self.stations_dict[station]} ({station}): {result.trend}"
                with cols[0]:
                    if settings["show_regression"]:
                        slope, intercept, r_value, p_value, std_err = self.get_lin_reg(
                            station_data
                        )

                    time_series_chart(df, settings)
                with cols[1]:
                    summary_df = get_summary_df(df, result)
                    st.dataframe(summary_df, hide_index=True)
                cnt_stations += 1
                num_stations.markdown(
                    f"{cnt_stations} of {len(self.stations_dict)} stations shown"
                )

    def run(self):
        analysis_options = lang["analysis-options"]
        sel_analysis = st.sidebar.selectbox(lang["analysis"], analysis_options)
        if analysis_options.index(sel_analysis) == 0:
            self.show_info()
        elif analysis_options.index(sel_analysis) == 1:
            self.show_mann_kendall()
