import streamlit as st
import os
import pandas as pd
import math

from helper import init_lang_dict_complete, get_lang, show_filter, show_download_button
from plots import (
    bar_chart,
    box_plot,
    line_chart,
    heatmap,
    time_series_line,
    line_chart_3d,
    histogram
)

PAGE = __name__
lang = {}


class NCBNStats:
    def __init__(self):
        global lang

        init_lang_dict_complete(os.path.basename(__file__), __name__)
        lang = get_lang(PAGE)
        self.data_df = st.session_state["station_data"]
        self.stations_dict = self.get_station_dict()
        self.parameters_dict = self.get_parameter_dict()
        self.min_year, self.max_year = self.get_min_max_year(self.data_df)
        self.parameter_label = ""
        self.parameter = ""
        self.time_aggregation = "month"
        self.analysis_options_keys = [
            "summary_table",
            "barchart",
            "boxplots",
            "superposed-line",
            "heatmap",
            "time-series",
            "spiral",
        ]
        self.sel_analysis = None
        self.show_average = False

    def get_agg_function(self):
        agg_function = (
            "sum"
            if (self.time_aggregation == "Year") & (self.parameter == "Precipitation")
            else "mean"
        )
        return agg_function

    def get_line_settings(self, df, par, settings):
        if self.show_average:
            value = df[par].mean()
            df["_value"] = value
            settings["h_line"] = "_value"
        return settings

    def get_analysis_options(self) -> dict:
        """Removes some analasysis methods from the options, which do not make sense for yearly values

        Returns:
            dict: cleaned analysis dict
        """
        options = lang["analysis-options"]
        if self.time_aggregation != "Month":
            elements_remove = [options[2], options[3], options[4], options[6]]
            options = [x for x in options if x not in elements_remove]
        return options

    def get_min_max_year(self, df: pd.DataFrame):
        """Returns the first and last year of a given dataframe

        Returns:
            _type_: _description_
        """
        min_year = df["Year"].min()
        max_year = df["Year"].max()
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
        #todo: add region filter to the widgets and region filter to data
        if "region" in filters and filters["region"] != []:
            df = df[df["Climate region"].isin(filters["region"])]
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
        df = st.session_state["station_url"].reset_index()
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
            df.groupby(["Stationname", "Station", self.time_aggregation])[
                self.parameter
            ]
            .agg(["min", "max", "mean"])
            .reset_index()
        )
        col_config = {
            "Station Name": st.column_config.Column(lang["station_name"]),
            "Station": st.column_config.Column(lang["station"]),
            self.time_aggregation: st.column_config.Column(
                lang[self.time_aggregation.lower()]
            ),
            "min": st.column_config.Column(lang["min"] + f" {self.parameter_label}"),
            "max": st.column_config.Column(lang["max"] + f" {self.parameter_label}"),
            "mean": st.column_config.Column(lang["mean"] + f" {self.parameter_label}"),
        }
        st.dataframe(
            df, use_container_width=True, hide_index=True, column_config=col_config
        )
        show_download_button(df, {"button_text": lang["download_button_text"]})

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

        df = self.filter_data(get_filter())
        st.header(lang["barcharts"])
        st.markdown(lang["bar_chart_intro"].format(self.parameter_label, lang["intro_plot"]))

        agg_func = self.get_agg_function()
        df = (
            df.groupby(["Stationname", "Station", self.time_aggregation])[
                self.parameter
            ]
            .agg([agg_func])
            .reset_index()
        )
        settings = {
            "x": self.time_aggregation,
            "y": agg_func,
            "width": 800,
            "height": 400,
            "y_title": self.parameter_label,
            "x_title": lang[self.time_aggregation.lower()],
        }
        stations = df["Station"].unique()
        for station in stations:
            df_filtered = df[(df["Station"] == station) & (df[agg_func].notna())]
            if len(df_filtered) > 0:
                settings["title"] = f"{df_filtered.iloc[0]['Stationname']} ({station})"
                settings["bar_width"] = 800 / len(df_filtered) * 0.5
                settings = self.get_line_settings(df_filtered, agg_func, settings)
                bar_chart(df_filtered, settings)
                show_download_button(
                    df_filtered, {"button_text": lang["download_button_text"]}
                )
            else:
                st.markdown(lang["no_data"])

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

        st.header(lang["boxplot"].format(self.parameter_label))
        st.markdown(lang["intro_box_plot"].format(lang["intro_plot"]))
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
            show_download_button(
                df_filtered, {"button_text": lang["download_button_text"]}
            )

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

        st.header(lang["superposed_lines"].format(self.parameter_label))
        st.markdown(lang["intro_superposed_lines"].format(lang["intro_plot"]))
        df = self.filter_data(get_filter())
        if self.time_aggregation == "Year":
            df = (
                df.groupby(["Stationname", "Station", self.time_aggregation])[
                    self.parameter
                ]
                .agg(["mean"])
                .reset_index()
            )
            df.columns = [
                "Stationname",
                "Station",
                self.time_aggregation,
                self.parameter,
            ]
            x_domain = [
                df[self.time_aggregation].min(),
                df[self.time_aggregation].max(),
            ]
            color = None
        else:
            years = len(df["Year"].unique())
            x_domain = [1, 12]
            color = "Year:N" if years < 6 else "Year"

        min_val = math.floor(df[self.parameter].min())
        max_val = math.ceil(df[self.parameter].max())
        settings = {
            "x": self.time_aggregation,
            "y": self.parameter,
            "width": 800,
            "height": 400,
            "y_title": self.parameter_label,
            "x_title": lang[self.time_aggregation.lower()],
            "x_domain": x_domain,
            "y_domain": [min_val, max_val],
            "color": color,
            "tooltip": [self.time_aggregation, self.parameter],
        }
        stations = df["Station"].unique()
        for station in stations:
            df_filtered = df[df["Station"] == station]
            settings["title"] = f"{df_filtered.iloc[0]['Stationname']} ({station})"
            line_chart(df_filtered, settings)
            show_download_button(
                df_filtered, {"button_text": lang["download_button_text"]}
            )

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

        st.header(lang["heatmap"].format(self.parameter_label))
        st.markdown(lang["intro_heatmap"].format(lang["intro_plot"]))
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
            show_download_button(
                df_filtered, {"button_text": lang["download_button_text"]}
            )

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

        st.header(lang["time_series"].format(self.parameter_label))
        st.markdown(lang["time_series_intro"].format(lang["intro_plot"]))
        agg_func = self.get_agg_function()
        df = self.filter_data(get_filter())
        if self.time_aggregation == "Year":
            df["Day"] = 15
            df["Month"] = 7
            df["Date"] = pd.to_datetime(df[["Year", "Month", "Day"]])
            df = (
                df.groupby(["Stationname", "Station", "Year", "Date"])[self.parameter]
                .agg([agg_func])
                .reset_index()
            )
            df.columns = ["Stationname", "Station", "Year", "Date", self.parameter]
            tooltip = ["Year", "Stationname", self.parameter]
        else:
            tooltip = ["Date", "Stationname", self.parameter]
        min_val = math.floor(df[self.parameter].min()) - 1
        max_val = math.ceil(df[self.parameter].max()) + 1
        settings = {
            "x": "Date",
            "y": self.parameter,
            "color": "Station",
            "width": 800,
            "height": 400,
            "y_title": self.parameter_label,
            "x_title": lang["year"],
            "y_domain": [min_val, max_val],
            "title": "",
            "tooltip": tooltip,
        }
        settings = self.get_line_settings(df, self.parameter, settings)
        time_series_line(df, settings)
        show_download_button(df, {"button_text": lang["download_button_text"]})
    
    def show_histogram(self):
        def get_filter():
            settings = {"stat_par": "", "stations": [], "years": [], "months": []}
            options = {
                "stations_dict": self.stations_dict,
                "min_year": self.min_year,
                "max_year": self.max_year,
            }
            filter = show_filter(settings, lang, options)
            return filter

        st.header(lang["histogram"].format(self.parameter_label))
        st.markdown(lang["intro_histogram"].format(lang["intro_plot"]))
        df = self.filter_data(get_filter())
        min_val = math.floor(df[self.parameter].min()) - 1
        max_val = math.ceil(df[self.parameter].max()) + 1
        settings = {
            "x": self.parameter,
            "y": 'count()',
            "width": 800,
            "height": 400,
            "x_title": self.parameter_label,
            "y_title": lang['count'],
            "title": "",
            "maxbins": 10,
            "x_domain": [min_val, max_val],
            "tooltip": ["count()"]
        }
        stations = df["Station"].unique()
        for station in stations:
            df_filtered = df[df["Station"] == station]
            settings["title"] = f"{df_filtered.iloc[0]['Stationname']} ({station})"
            histogram(df_filtered, settings)
            show_download_button(df, {"button_text": lang["download_button_text"]})

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

        st.header(lang["3d_spiral"].format(self.parameter_label))
        st.markdown(lang["intro-spiral"].format(lang["intro_plot"]), unsafe_allow_html=True)
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
        show_download_button(df_filtered, {"button_text": lang["download_button_text"]})

    def get_parameters(self):
        # "Summary table", "Barcharts", "Boxplots", "Superposed lines", "Heatmap", "Time Series", "3D Spiral"
        with st.sidebar.expander(f"⚙️{lang['settings']}", expanded=True):
            time_aggregation_options = {
                "Month": lang["monthly"],
                "Year": lang["yearly"],
            }
            self.time_aggregation = st.selectbox(
                label=lang["time_aggregation"],
                options=list(time_aggregation_options.keys()),
                format_func=lambda x: time_aggregation_options[x],
            )
            analysis_options = self.get_analysis_options()
            sel_analysis = st.selectbox(
                label=lang["analysis"],
                options=analysis_options,
            )
            self.parameter = st.selectbox(
                label=lang["parameter"],
                options=list(self.parameters_dict.keys()),
                format_func=lambda x: self.parameters_dict[x],
            )
            if lang["analysis-options"].index(sel_analysis) in (1, 5):
                self.show_average = st.checkbox(lang["show-average-line"])
            self.parameter_label = self.parameters_dict[self.parameter]

            return sel_analysis

    def run(self):
        sel_analysis = self.get_parameters()

        if lang["analysis-options"].index(sel_analysis) == 0:
            self.show_summary_table()
        elif lang["analysis-options"].index(sel_analysis) == 1:
            self.show_barchart()
        elif lang["analysis-options"].index(sel_analysis) == 2:
            self.show_boxplot()
        elif lang["analysis-options"].index(sel_analysis) == 3:
            self.show_superposed_lines()
        elif lang["analysis-options"].index(sel_analysis) == 4:
            self.show_heatmap()
        elif lang["analysis-options"].index(sel_analysis) == 5:
            self.show_time_series()
        elif lang["analysis-options"].index(sel_analysis) == 6:
            self.show_spiral()
        elif lang["analysis-options"].index(sel_analysis) == 7:
            self.show_histogram()
