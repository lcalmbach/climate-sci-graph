import streamlit as st
import os
import math

from helper import init_lang_dict_complete, get_lang, show_filter, show_download_button
from plots import (
    bar_chart,
    box_plot,
    line_chart,
    heatmap,
    time_series_line,
    line_chart_3d,
)

PAGE = __name__
lang = {}


class MonthlyStats:
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

    def get_parameter_dict(self):
        # column headers as used in dataframe
        keys = ["Temperature", "Precipitation"]
        values = lang["parameters"]
        return dict(zip(keys, values))

    def get_stat_function_dict(self):
        keys = ["min", "max", "average"]
        values = lang["stat-functions"]
        return dict(zip(keys, values))

    def get_station_dict(self):
        df = st.session_state["stations_url"].reset_index()
        keys = list(df["Abbreviation"])
        values = list(df["Station"])
        return dict(zip(keys, values))

    def show_summary_table(self):
        def get_filter():
            settings = {"stat_par": "", "stations": [], "years": [], "months": []}
            options = {
                "stations_dict": self.stations_dict,
                "min_year": self.min_year,
                "max_year": self.max_year,
            }
            filter = show_filter(settings, lang, options)
            return filter

        st.header(lang["title"])
        st.markdown(f"**{self.parameter_label}**")
        st.markdown(lang["intro"])

        df = self.filter_data(get_filter())
        df = (
            df.groupby(["Stationname", "Station", "Month"])[self.parameter]
            .agg(["min", "max", "mean"])
            .reset_index()
        )
        col_config = {
            "Station Name": st.column_config.Column(lang["station_name"]),
            "Station": st.column_config.Column(lang["station"]),
            "Month": st.column_config.Column(lang["month"]),
            "min": st.column_config.Column(lang["min"] + f" {self.parameter_label}"),
            "max": st.column_config.Column(lang["max"] + f" {self.parameter_label}"),
            "mean": st.column_config.Column(lang["mean"] + f" {self.parameter_label}"),
        }
        st.dataframe(
            df, use_container_width=True, hide_index=True, column_config=col_config
        )
        show_download_button(df)

    def show_barchart(self):
        def get_filter():
            settings = {"stat_par": "", "stations": [], "years": [], "months": []}
            options = {
                "stations_dict": self.stations_dict,
                "min_year": self.min_year,
                "max_year": self.max_year,
            }
            filter = show_filter(settings, lang, options)
            return filter

        st.header(lang["barcharts"])
        st.markdown(f"**{self.parameter_label}**")
        st.markdown(lang["bar_chart_intro"])
        show_average = st.sidebar.checkbox("Show average line")
        df = self.filter_data(get_filter())

        df = (
            df.groupby(["Stationname", "Station", "Month"])[self.parameter]
            .agg(["min", "max", "mean"])
            .reset_index()
        )
        settings = {
            "x": "Month",
            "y": "mean",
            "width": 800,
            "height": 400,
            "y_title": self.parameter_label,
            "x_title": lang["month"],
            "bar_width": 20,
        }
        stations = df["Station"].unique()
        st.write(self.parameter)
        for station in stations:
            df_filtered = df[df["Station"] == station]
            settings["title"] = f"{df_filtered.iloc[0]['Stationname']} ({station})"
            if show_average:
                mean = df["mean"].mean()
                df_filtered["mean_all"] = mean
                settings["h_line"] = "mean_all"
            bar_chart(df_filtered, settings)
            show_download_button(df_filtered)

    def show_boxplot(self):
        def get_filter():
            settings = {"stat_par": "", "stations": [], "years": [], "months": []}
            options = {
                "stations_dict": self.stations_dict,
                "min_year": self.min_year,
                "max_year": self.max_year,
            }
            filter = show_filter(settings, lang, options)
            return filter

        st.header(lang["boxplot"])
        st.markdown(f"**{self.parameter_label}**")
        st.markdown(lang["boxplot_intro"])
        df = self.filter_data(get_filter())
        settings = {
            "x": "Month",
            "y": self.parameter,
            "width": 800,
            "height": 400,
            "y_title": self.parameter_label,
            "x_title": lang["month"],
        }
        stations = df["Station"].unique()
        for station in stations:
            df_filtered = df[df["Station"] == station]
            settings["title"] = f"{df_filtered.iloc[0]['Stationname']} ({station})"
            box_plot(df_filtered, settings)
            show_download_button(df_filtered)

    def show_superposed_lines(self):
        def get_filter():
            settings = {"stat_par": "", "stations": [], "years": [], "months": []}
            options = {
                "stations_dict": self.stations_dict,
                "min_year": self.min_year,
                "max_year": self.max_year,
            }
            filter = show_filter(settings, lang, options)
            return filter

        st.header(lang["boxplot"])
        st.markdown(f"**{self.parameter_label}**")
        st.markdown(lang["intro"])
        df = self.filter_data(get_filter())
        years = len(df["Year"].unique())
        min_val = math.floor(df[self.parameter].min())
        max_val = math.ceil(df[self.parameter].max())
        settings = {
            "x": "Month",
            "y": self.parameter,
            "width": 800,
            "height": 400,
            "y_title": self.parameter_label,
            "x_title": lang["month"],
            "color": "Year:N" if years < 6 else "Year",
            "x_domain": [1, 12],
            "y_domain": [min_val, max_val],
            "tooltip": ["Month", self.parameter],
        }
        stations = df["Station"].unique()
        for station in stations:
            df_filtered = df[df["Station"] == station]
            settings["title"] = f"{df_filtered.iloc[0]['Stationname']} ({station})"
            line_chart(df_filtered, settings)
            show_download_button(df_filtered)

    def show_heatmap(self):
        def get_filter():
            settings = {"stat_par": "", "stations": [], "years": [], "months": []}
            options = {
                "stations_dict": self.stations_dict,
                "min_year": self.min_year,
                "max_year": self.max_year,
            }
            filter = show_filter(settings, lang, options)
            return filter

        st.header(lang["heatmap"])
        st.markdown(f"**{self.parameter_label}**")
        st.markdown(lang["intro"])
        df = self.filter_data(get_filter())
        settings = {
            "x": "Month:N",
            "y": "Year:N",
            "color": self.parameter,
            "width": 800,
            "height": 400,
            "y_title": self.parameter_label,
            "x_title": lang["month"],
            "tooltip": ["Month", self.parameter],
        }
        stations = df["Station"].unique()
        for station in stations:
            df_filtered = df[df["Station"] == station]
            settings["title"] = f"{df_filtered.iloc[0]['Stationname']} ({station})"
            heatmap(df_filtered, settings)
            show_download_button(df_filtered)

    def show_time_series(self):
        def get_filter():
            settings = {"stat_par": "", "stations": [], "years": [], "months": []}
            options = {
                "stations_dict": self.stations_dict,
                "min_year": self.min_year,
                "max_year": self.max_year,
            }
            filter = show_filter(settings, lang, options)
            return filter

        st.header(lang["time_series"])
        st.markdown(f"**{self.parameter_label}**")
        st.markdown(lang["intro"])
        df = self.filter_data(get_filter())
        min_val = math.floor(df[self.parameter].min())
        max_val = math.ceil(df[self.parameter].max())
        settings = {
            "x": "Date",
            "y": self.parameter,
            "color": "Station",
            "width": 800,
            "height": 400,
            "y_title": self.parameter_label,
            "x_title": lang["month"],
            "y_domain": [min_val, max_val],
            "title": "",
            "tooltip": ["Month", "Stationname", self.parameter],
        }
        time_series_line(df, settings)
        show_download_button(df)

    def show_spiral(self):
        def get_filter():
            settings = {"stat_par": "", "station": [], "years": [], "months": []}
            options = {
                "stations_dict": self.stations_dict,
                "min_year": self.min_year,
                "max_year": self.max_year,
            }
            filter = show_filter(settings, lang, options)
            return filter

        st.header(lang["3d_spiral"])
        st.markdown(f"**{self.parameter_label}**")
        st.markdown(lang["intro"])
        filter = get_filter()
        df = self.filter_data(filter)
        min_val = math.floor(df[self.parameter].min())
        max_val = math.ceil(df[self.parameter].max())
        df_filtered = df[df["Station"] == filter["station"]]
        settings = {
            "month": "Month",
            "year": "Year",
            "value": self.parameter,
            "width": 800,
            "height": 400,
            "y_title": self.parameter_label,
            "x_title": lang["month"],
            "x_domain": [1, 12],
            "y_domain": [min_val, max_val],
            "tooltip": ["Month", self.parameter],
            "title": f"{df.iloc[0]['Stationname']} ({filter['station']})",
        }
        settings[
            "title"
        ] = f"{df_filtered.iloc[0]['Stationname']} ({filter['station']})"
        line_chart_3d(df_filtered, settings)
        show_download_button(df_filtered)

    def run(self):
        # "Summary table", "Barcharts", "Boxplots", "Superposed lines", "Heatmap", "Time Series", "3D Spiral"
        sel_menu = st.sidebar.selectbox(
            label=lang["analysis"], options=lang["analysis-options"]
        )
        self.parameter = st.sidebar.selectbox(
            label=lang["parameter"],
            options=list(self.parameters_dict.keys()),
            format_func=lambda x: self.parameters_dict[x],
        )
        self.parameter_label = self.parameters_dict[self.parameter]

        if lang["analysis-options"].index(sel_menu) == 0:
            self.show_summary_table()
        elif lang["analysis-options"].index(sel_menu) == 1:
            self.show_barchart()
        elif lang["analysis-options"].index(sel_menu) == 2:
            self.show_boxplot()
        elif lang["analysis-options"].index(sel_menu) == 3:
            self.show_superposed_lines()
        elif lang["analysis-options"].index(sel_menu) == 4:
            self.show_heatmap()
        elif lang["analysis-options"].index(sel_menu) == 5:
            self.show_time_series()
        elif lang["analysis-options"].index(sel_menu) == 6:
            self.show_spiral()
