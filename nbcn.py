import streamlit as st
import os
import pandas as pd
import numpy as np
import math
import pymannkendall as mk
from scipy import stats
from enum import Enum
from datetime import datetime

from trend import TrendAnalysis
from nbcn_data import get_data, get_stations_metadata
from helper import (
    init_lang_dict_complete,
    get_lang,
    show_filter,
    show_download_button,
    remove_unit,
    add_date_column,
)
from plots import (
    bar_chart,
    box_plot,
    line_chart,
    heatmap,
    time_series_line,
    time_series_chart,
    line_chart_3d,
    histogram,
    map_chart,
)

MIN_POINTS = 4 * 12


class Plot(Enum):
    SUMMARY_TABLE = 0
    BARCHART = 1
    BOXPLOT = 2
    STACKED_LINES = 3
    HEATMAP = 4
    TIME_SERIES = 5
    SPIRAL = 6
    HISTOGRAM = 7


time_aggregation_plots = {
    "day": [
        Plot.SUMMARY_TABLE.value,
        Plot.BARCHART.value,
        Plot.BOXPLOT.value,
        Plot.HEATMAP.value,
        Plot.TIME_SERIES.value,
        Plot.HISTOGRAM.value,
    ],
    "week": [
        Plot.SUMMARY_TABLE.value,
        Plot.BARCHART.value,
        Plot.BOXPLOT.value,
        Plot.STACKED_LINES.value,
        Plot.HEATMAP.value,
        Plot.TIME_SERIES.value,
        Plot.HISTOGRAM.value,
    ],
    "month": [
        Plot.SUMMARY_TABLE.value,
        Plot.BARCHART.value,
        Plot.BOXPLOT.value,
        Plot.STACKED_LINES.value,
        Plot.HEATMAP.value,
        Plot.TIME_SERIES.value,
        Plot.SPIRAL.value,
        Plot.HISTOGRAM.value,
    ],
    "year": [
        Plot.SUMMARY_TABLE.value,
        Plot.BARCHART.value,
        Plot.BOXPLOT.value,
        Plot.HEATMAP.value,
        Plot.TIME_SERIES.value,
        Plot.HISTOGRAM.value,
    ],
    "decade": [
        Plot.SUMMARY_TABLE.value,
        Plot.BARCHART.value,
        Plot.BOXPLOT.value,
        Plot.HEATMAP.value,
        Plot.TIME_SERIES.value,
    ],
}

RESSOURCES_FILE = "./data/ressources.csv"
PAGE = __name__
lang = {}


class NCBN:
    def __init__(self, app_name):
        global lang
        init_lang_dict_complete(os.path.basename(__file__), __name__)
        lang = get_lang(PAGE)

        self.app_name = app_name
        self.menu_dict = self.get_menu_dict()
        self.menu_options = list(self.menu_dict.values())
        self._menu_selection = list(self.menu_dict.keys())[0]
        self.raw_data_df = get_data()
        self._base_data_df = pd.DataFrame()
        self.station_df = get_stations_metadata()
        self.stations_dict = self.get_station_dict()
        self.min_year, self.max_year = self.get_min_max_year(self.raw_data_df)
        self.parameters = []

        self.time_aggregation = "month"
        self.analysis_options = []
        self.time_aggregation_options = []
        self.sel_analysis = None

        self.show_average_line = False
        self.parameters_dict = {
            "gre000d0": lang["gre000d0"],
            "hto000d0": lang["hto000d0"],
            "nto000d0": lang["nto000d0"],
            "prestad0": lang["prestad0"],
            "rre150d0": lang["rre150d0"],
            "sre000d0": lang["sre000d0"],
            "tre200d0": lang["tre200d0"],
            "tre200dn": lang["tre200dn"],
            "tre200dx": lang["tre200dx"],
            "ure200d0": lang["ure200d0"],
        }
        self.parameters_short_dict = {
            "gre000d0": lang["gre000d0-s"],
            "hto000d0": lang["hto000d0-s"],
            "nto000d0": lang["nto000d0-s"],
            "prestad0": lang["prestad0-s"],
            "rre150d0": lang["rre150d0-s"],
            "sre000d0": lang["sre000d0-s"],
            "tre200d0": lang["tre200d0-s"],
            "tre200dn": lang["tre200dn-s"],
            "tre200dx": lang["tre200dx-s"],
            "ure200d0": lang["ure200d0-s"],
        }
        self.parameters_agg_dict = {
            "gre000d0": "mean",
            "hto000d0": "sum",
            "nto000d0": "mean",
            "prestad0": "mean",
            "rre150d0": "sum",
            "sre000d0": "sum",
            "tre200d0": "mean",
            "tre200dn": "min",
            "tre200dx": "max",
            "ure200d0": "mean",
        }

    @property
    def menu_selection(self):
        return self._menu_selection

    @menu_selection.setter
    def menu_selection(self, value: str):
        id = self.menu_options.index(value)
        self._menu_selection = list(self.menu_dict.keys())[id]
        if self._menu_selection == "home":
            self.show_about(self.app_name)
        elif self._menu_selection == "stations":
            config = []
            self.show_stations()
        elif self._menu_selection == "data":
            config = ["time-aggregation", "parameters", "value"]
            self.show_browse_data(config)
        elif self._menu_selection == "plots":
            self.show_stats()
        elif self._menu_selection == "trend":
            self.show_trend()
        elif self._menu_selection == "ressources":
            self.show_ressources()

    @property
    def par_label_no_unit(self):
        return remove_unit(self.parameters_short_dict[self.parameters[0]])

    def get_aggregated_data(self, df):
        # generate values aggregated by month
        # for day-month, the year must be added ot the aggregation parameters
        if self.time_aggregation in ("week", "month", "day"):
            group_parameters = ["station", "year", self.time_aggregation]
        else:
            group_parameters = ["station", self.time_aggregation]
        df = (
            df.groupby(group_parameters)[self.parameters]
            .agg([self.parameters_agg_dict[self.parameters[0]]])
            .reset_index()
        )
        # rename parameter back
        df.columns = group_parameters + self.parameters
        return df

    def get_menu_dict(self):
        menu_values = lang["menu-options-values"]
        menu_keys = ["home", "stations", "data", "plots", "trend", "ressources"]
        return dict(zip(menu_keys, menu_values))

    def get_base_data(self, filter, add_fields: list = [], include_date: bool = False):
        if include_date:
            fields = ["station", "date"] + add_fields + self.parameters
        else:
            fields = (
                ["station", self.time_aggregation] + add_fields + self.parameters
                if add_fields
                else ["station", self.time_aggregation] + self.parameters
            )
        df = self.filter_base_data(filter)
        df = df[fields]
        if len(self.parameters) == 1:
            df = df.dropna(subset=self.parameters)
        return df

    def rename_columns(self, df: pd.DataFrame):
        columns = {}
        for col in df.columns.copy():
            if col == "station name":
                columns[col] = lang["station_name"]
            elif col == "station":
                columns[col] = lang["station"]
            elif col == "date":
                columns[col] = lang["date"]
            elif col == "day":
                columns[col] = lang["day"]
            elif col == "week":
                columns[col] = lang["week"]
            elif col == "month":
                columns[col] = lang["month"]
            elif col == "year":
                columns[col] = lang["year"]
            elif col == "decade":
                columns[col] = lang["decade"]
            elif col in self.parameters_dict.keys():
                columns[col] = remove_unit(self.parameters_short_dict[col])
        return df.rename(columns=columns)

    # for later use
    def aggregate(self):
        agg_functions = {par: self.parameters_agg_dict[par] for par in self.parameters}
        df = (
            df.groupby(["station", self.time_aggregation])[self.parameters]
            .agg(agg_functions)
            .reset_index()
        )
        # remove multiindex first join par + agg func, then replace the parameter names with labels
        df.columns = ["".join(col).strip() for col in df.columns.values]
        for par in self.parameters:
            df.rename(
                columns={par + agg_functions[par]: self.par_label_no_unit}, inplace=True
            )

    def get_domain(self, df: pd.DataFrame, par_name, buffer):
        min_val = math.floor(df[par_name].min()) - buffer
        max_val = math.ceil(df[par_name].max()) + buffer
        return [min_val, max_val]

    def merge_station_columns(self, df: pd.DataFrame, columns2add: list):

        merged_df = df.merge(
            self.station_df[["station"] + columns2add], on="station", how="left"
        )
        # put merged columns at start of columns
        merged_df = merged_df[columns2add + list(df.columns)]
        return merged_df

    def get_h_line_value(self, df, settings):
        if self.show_average_line:
            value = df[settings["y"]].mean()
            df["_value"] = value
            settings["h_line"] = "_value"
        return settings

    def get_analysis_options(self) -> dict:
        """Removes some analsysis methods from the options, which do not make sense for yearly values

        Returns:
            dict: cleaned analysis dict
        """

        if self.menu_selection == 'trend':
            options = lang['trend-analysis-options']
        else:
            all_options = lang["stats-analysis-options"]
            options = []
            for option in time_aggregation_plots[self.time_aggregation]:
                options.append(all_options[option])
        return options

    def get_min_max_year(self, df: pd.DataFrame):
        """Returns the first and last year of a given dataframe

        Returns:
            _type_: _description_
        """
        min_year = df["year"].min()
        max_year = df["year"].max()
        return int(min_year), int(max_year)

    def filter_values(self, filters, df):
        if "value" in filters:
            if filters["value"]["use_numeric_filter"]:
                if filters["value"]["compare_op"] == ">=":
                    df = df[df[self.parameters[0]] >= filters["value"]["value"]]
                elif filters["value"]["compare_op"] == ">":
                    df = df[df[self.parameters[0]] > filters["value"]["value"]]
                elif filters["value"]["compare_op"] == "<=":
                    df = df[df[self.parameters[0]] <= filters["value"]["value"]]
                elif filters["value"]["compare_op"] == "<":
                    df = df[df[self.parameters[0]] < filters["value"]["value"]]
                elif filters["value"]["compare_op"] == "=":
                    df = df[df[self.parameters[0]] == filters["value"]["value"]]
            return df

    def filter_base_data(self, filters):
        df = self.raw_data_df
        if "stations" in filters and filters["stations"] != []:
            df = df[df["station"].isin(filters["stations"])]
        if "years" in filters and filters["years"] != []:
            df = df[
                (df["year"] >= filters["years"][0])
                & (df["year"] <= filters["years"][1])
            ]
        # todo: add region filter to the widgets and region filter to data
        if "year" in filters:
            df = df[(df["year"] == filters["year"])]
        if "month" in filters:
            df = df[(df["month"] == filters["month"])]
        if "region" in filters and filters["region"] != []:
            df = df[df["climate region"].isin(filters["region"])]
        if "months" in filters and filters["months"] != []:
            df = df[df["month"].isin(filters["months"])]
        return df

    def get_stat_function_dict(self):
        keys = ["min", "max", "average"]
        values = lang["stat-functions"]
        return dict(zip(keys, values))

    def get_station_dict(self):
        df = get_stations_metadata().reset_index()
        keys = list(df["station"])
        values = list(df["station name"])
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

        st.header(lang["stats-title"])
        st.markdown(
            lang["stats-intro"].format(
                self.time_aggregation, self.parameters_dict[self.parameters[0]]
            )
        )
        year_field = (
            ["year"] if self.time_aggregation in ("day", "week", "month") else []
        )
        df = self.get_base_data(get_filter(), add_fields=year_field)
        df = self.get_aggregated_data(df)
        # calculate statistics
        group_parameters = list(df.columns)
        if self.time_aggregation in ("week", "month", "day"):
            group_parameters.remove("year")
        group_parameters.remove(self.time_aggregation)
        group_parameters.remove(self.parameters[0])
        agg_funcs = ["min", "max", "mean", "std"]
        df = df.groupby(group_parameters)[self.parameters].agg(agg_funcs).reset_index()
        df.columns = group_parameters + agg_funcs
        df = self.merge_station_columns(df, ["station name"])

        par_label = remove_unit(self.parameters_short_dict[self.parameters[0]])
        col_config = {
            "station name": st.column_config.Column(lang["station_name"]),
            "station": st.column_config.Column(lang["station"]),
            self.time_aggregation: st.column_config.Column(
                lang[self.time_aggregation.lower()]
            ),
            "min": st.column_config.Column(lang["min"] + f" {par_label}"),
            "max": st.column_config.Column(lang["max"] + f" {par_label}"),
            "mean": st.column_config.Column(lang["mean"] + f" {par_label}"),
            "std": st.column_config.Column(lang["std"] + f" {par_label}"),
        }
        st.dataframe(
            df, use_container_width=True, hide_index=True, column_config=col_config
        )
        show_download_button(df, {"button_text": lang["download_button_text"]})

    def show_barchart(self):
        def get_filter():
            settings = {
                "stat_par": "",
                "stations": [],
                "years": [],
                "months": None,
            }
            options = {
                "stations_dict": self.stations_dict,
                "min_year": self.min_year,
                "max_year": self.max_year,
                "show-average-line": False,
            }
            filter = show_filter(settings, lang, options)
            return filter

        st.header(lang["barcharts"])
        st.markdown(
            lang["bar_chart_intro"].format(self.parameters_label, lang["intro_plot"])
        )
        year_field = (
            ["year"] if self.time_aggregation in ("day", "week", "month") else []
        )
        df = self.get_base_data(get_filter(), add_fields=year_field)
        df = self.get_aggregated_data(df)
        # calculate statistics
        group_parameters = list(df.columns)
        if self.time_aggregation in ("week", "month", "day"):
            group_parameters.remove("year")
        group_parameters.remove(self.parameters[0])
        agg_funcs = ["mean"]
        df = df.groupby(group_parameters)[self.parameters].agg(agg_funcs).reset_index()
        df.columns = group_parameters + agg_funcs
        par_name = remove_unit(self.parameters_short_dict[self.parameters[0]])
        df.columns = ["station", self.time_aggregation, par_name]
        settings = {
            "x": self.time_aggregation,
            "y": par_name,
            "width": 800,
            "height": 400,
            "y_title": self.parameters_short_dict[self.parameters[0]],
            "x_title": lang[self.time_aggregation.lower()],
            "format_x": "%d.%b",
        }
        if self.time_aggregation == "year":
            settings["x_domain"] = self.get_domain(df, self.time_aggregation, 1)
        stations = df["station"].unique()
        for station in stations:
            df_filtered = df[(df["station"] == station)]
            if len(df_filtered) > 0:
                settings["title"] = f"{self.stations_dict[station]} ({station})"
                settings["bar_width"] = 800 / len(df_filtered) * 0.5
                settings = self.get_h_line_value(df_filtered, settings)
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

        st.header(lang["boxplot"].format(self.parameters_label))
        st.markdown(lang["intro-box-plot"].format(lang["intro_plot"]))
        year_field = (
            ["year"] if self.time_aggregation in ("day", "week", "month") else []
        )
        df = self.get_base_data(get_filter(), add_fields=year_field)
        df = self.get_aggregated_data(df)
        # calculate statistics
        group_parameters = list(df.columns)
        if self.time_aggregation in ("week", "month", "day"):
            group_parameters.remove("year")
        group_parameters.remove(self.parameters[0])
        settings = {
            "x": self.time_aggregation,
            "y": self.parameters[0],
            "width": 800,
            "height": 400,
            "y_title": self.parameters_short_dict[self.parameters[0]],
            "x_title": lang[self.time_aggregation],
        }
        stations = df["station"].unique()
        for station in stations:
            df_filtered = df[(df["station"] == station)]
            settings["title"] = f"{self.stations_dict[station]} ({station})"
            settings = self.get_h_line_value(df_filtered, settings)
            box_plot(df_filtered, settings)
            show_download_button(
                df_filtered, {"button_text": lang["download_button_text"]}
            )

    def show_stacked_lines(self):
        def get_filter():
            settings = {"stat_par": "", "stations": [], "years": [], "months": []}
            options = {
                "stations_dict": self.stations_dict,
                "min_year": self.min_year,
                "max_year": self.max_year,
            }
            filter = show_filter(settings, lang, options)
            return filter

        st.header(lang["stacked-lines"].format(self.parameters_label))
        if self.compare_year > 0:
            st.markdown("Comparison of the years {} to {} with {}".format(self.min_year,self.max_year,self.compare_year))
        st.markdown(lang["intro-stacked-lines"].format(lang["intro_plot"]))

        year_field = (
            ["year"] if self.time_aggregation in ("day", "week", "month") else []
        )
        df = self.get_base_data(get_filter(), add_fields=year_field)
        df = self.get_aggregated_data(df)

        df.rename(columns={self.parameters[0]: self.par_label_no_unit}, inplace=True)
        df = df[["station", "year", self.time_aggregation, self.par_label_no_unit]]
        df = self.merge_station_columns(df, ["station name"])
        x_domain = [
            df[self.time_aggregation].min(),
            df[self.time_aggregation].max(),
        ]
        min_val = math.floor(df[self.par_label_no_unit].min())
        max_val = math.ceil(df[self.par_label_no_unit].max())
        settings = {
            "x": self.time_aggregation,
            "y": self.par_label_no_unit,
            "width": 800,
            "height": 400,
            "y_title": self.par_label_no_unit,
            "x_title": lang[self.time_aggregation.lower()],
            "x_domain": x_domain,
            "y_domain": [min_val, max_val],
            "color": "year",
            "opacity": 0.1,
            "hide_legend": True,
            "compare_line": self.compare_year,
            "tooltip": [self.time_aggregation, "year", self.par_label_no_unit],
        }
        stations = df["station"].unique()
        for station in stations:
            df_filtered = df[
                (df["station"] == station) & (df[self.par_label_no_unit].notna())
            ]
            settings["title"] = f"{df_filtered.iloc[0]['station name']} ({station})"
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

        st.header(lang["heatmap"].format(self.par_label_no_unit))
        st.markdown(lang["intro_heatmap"].format(lang["intro_plot"]))
        df = self.filter_base_data(get_filter())
        agg_func = self.parameters_agg_dict[self.parameters[0]]
        agg_parameters = ["station", "year", self.time_aggregation]
        df = (
            df.groupby(agg_parameters)[self.parameters]
            .agg([agg_func])
            .reset_index()
            .round(2)
        )
        df.columns = agg_parameters + [self.par_label_no_unit]
        # df = df[["station", "year", self.time_aggregation, self.par_label_no_unit]]
        settings = {
            "x": f"{self.time_aggregation}:N",
            "y": "year:N",
            "color": self.par_label_no_unit,
            "width": 800,
            "height": 400,
            "y_title": lang['year'],
            "x_title": lang["month"],
            "tooltip": [self.time_aggregation, "year", self.par_label_no_unit],
            "show_numbers": (self.time_aggregation == 'month')
        }
        stations = df["station"].unique()
        for station in stations:
            df_filtered = df[df["station"] == station]
            settings["title"] = f"{self.stations_dict[station]} ({station})"
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

        st.header(lang["time_series"].format(self.par_label_no_unit))
        st.markdown(lang["time_series_intro"].format(lang["intro_plot"]))
        agg_func = self.parameters_agg_dict[self.parameters[0]]
        df = self.filter_base_data(get_filter())
        if (self.time_aggregation in ('week', 'day')) & ((self.max_year - self.min_year) > 1):
            df = df[df['year'] == datetime.now().year]
            st.info(lang["interval_too_long"])
        if len(df["station"].unique()) > 10:
            st.info(lang["too_many_stations"])
        else:
            df = add_date_column(df, self.time_aggregation)
            aggregation_fields = ["year", "station", self.time_aggregation, "date"] if self.time_aggregation != 'year' else ["station", self.time_aggregation, "date"]
            if self.time_aggregation != 'daily':
                df = (
                    df.groupby(aggregation_fields)[
                        self.parameters
                    ]
                    .agg([agg_func])
                    .reset_index()
                )
                df.columns = aggregation_fields + [self.par_label_no_unit]
            tooltip = list(df.columns)
            min_val = math.floor(df[self.par_label_no_unit].min()) - 1
            max_val = math.ceil(df[self.par_label_no_unit].max()) + 1
            settings = {
                "x": "date",
                "y": self.par_label_no_unit,
                "color": "station",
                "width": 800,
                "height": 400,
                "y_title": self.par_label_no_unit,
                "x_title": lang["year"],
                "y_domain": [min_val, max_val],
                "title": "",
                "tooltip": tooltip,
            }
            settings = self.get_h_line_value(df, settings)
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

        st.header(lang["histogram"].format(self.parameters_short_dict[self.parameters[0]]))
        st.markdown(lang["intro_histogram"].format(lang["intro_plot"]))
        df = self.filter_base_data(get_filter())
        agg_func = self.parameters_agg_dict[self.parameters[0]]
        aggregation_fields = ["year", "station", self.time_aggregation]
        df = (
            df.groupby(aggregation_fields)[self.parameters]
            .agg([agg_func])
            .reset_index()
        )
        df.columns = aggregation_fields + [self.par_label_no_unit]
        min_val = math.floor(df[self.par_label_no_unit].min()) - 1
        max_val = math.ceil(df[self.par_label_no_unit].max()) + 1
        settings = {
            "x": self.par_label_no_unit,
            "y": "count()",
            "width": 800,
            "height": 400,
            "x_title": self.parameters_short_dict[self.parameters[0]],
            "y_title": lang["count"],
            "title": "",
            "maxbins": 10,
            "x_domain": [min_val, max_val],
            "tooltip": ["count()"],
        }
        stations = df["station"].unique()
        for station in stations:
            df_filtered = df[df["station"] == station]
            settings["title"] = f"{self.stations_dict[station]} ({station})"
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

        st.header(lang["3d_spiral"].format(self.par_label_no_unit))
        st.markdown(
            lang["intro-spiral"].format(lang["intro_plot"]), unsafe_allow_html=True
        )
        filter = get_filter()
        df = self.filter_base_data(filter)
        agg_func = self.parameters_agg_dict[self.parameters[0]]
        aggregation_fields = ["year", "station", self.time_aggregation]
        df = (
            df.groupby(aggregation_fields)[self.parameters]
            .agg([agg_func])
            .reset_index()
        )
        df.columns = ["year", "station", self.time_aggregation] + [self.par_label_no_unit]
        min_val = math.floor(df[self.par_label_no_unit].min())
        max_val = math.ceil(df[self.par_label_no_unit].max())
        df_filtered = df[df["station"] == filter["station"]]
        settings = {
            "month": "month",
            "year": "year",
            "value": self.par_label_no_unit,
            "width": 800,
            "height": 400,
            "y_title": self.par_label_no_unit,
            "x_title": lang["month"],
            "x_domain": [1, 12],
            "y_domain": [min_val, max_val],
            "tooltip": ["month", self.parameters],
            "title": f"{self.stations_dict[filter['station']]} ({filter['station']})",
        }
        line_chart_3d(df_filtered, settings)
        show_download_button(df_filtered, {"button_text": lang["download_button_text"]})

    def get_parameters(self, config: list):
        # "Summary table", "Barcharts", "Boxplots", "Superposed lines", "Heatmap", "Time Series", "3D Spiral"
        # default value, if no analysis is returned and function is only called for selecting a parameter
        sel_analysis = None

        analysis_options = self.get_analysis_options()
        if config == []:
            config = ["time-aggregation", "analysis-options", "parameter"]
        with st.sidebar.expander(f"⚙️{lang['settings']}", expanded=True):
            if "time-aggregation" in config:
                time_aggregation_options = {
                    "day": lang["daily"],
                    "week": lang["weekly"],
                    "month": lang["monthly"],
                    "year": lang["yearly"],
                    "decade": lang["decadal"],
                }
                self.time_aggregation = st.selectbox(
                    label=lang["time_aggregation"],
                    options=list(time_aggregation_options.keys()),
                    format_func=lambda x: time_aggregation_options[x],
                )
            if "parameter" in config:
                self.parameters.append(
                    st.selectbox(
                        label=lang["parameter"],
                        options=list(self.parameters_short_dict.keys()),
                        format_func=lambda x: self.parameters_short_dict[x],
                    )
                )
            if "parameters" in config:
                self.parameters = st.multiselect(
                    label=lang["parameter"],
                    options=list(self.parameters_short_dict.keys()),
                    format_func=lambda x: self.parameters_short_dict[x],
                )
                if self.parameters == []:
                    self.parameters = list(self.parameters_dict.keys())

            if self.menu_selection == 'trend':
                display_options = lang['trend-display-options']
                self.display = st.selectbox(lang["display"], options=display_options)
                self.show_regression = st.checkbox(lang['show-regression-line'])
            
            if "analysis-options" in config:
                analysis_options = analysis_options
                sel_analysis = st.selectbox(
                    label=lang["analysis"],
                    options=analysis_options,
                )

            if self.menu_selection == "plots":
                if analysis_options.index(sel_analysis) in (1, 2, 3, 5):
                    self.show_average_line = st.checkbox(lang["show-average-line"])
                    self.parameters_label = self.parameters_short_dict[
                        self.parameters[0]
                    ]
                if analysis_options.index(sel_analysis) == 3:
                    year_options = range(self.min_year, self.max_year + 1)[::-1]
                    self.compare_year = st.selectbox(label=lang["compare-year"],
                                                     options=year_options)
                    self.parameters_label = self.parameters_short_dict[
                        self.parameters[0]
                    ]

            return sel_analysis

    def show_ressources(self):
        @st.cache_data()
        def get_ressource_data():
            df = pd.read_csv(RESSOURCES_FILE, sep=";")
            df["link"] = '<a href="' + df["url"] + '">' + df["title"] + "</a>"
            return df

        st.header(lang["ressources-title"])
        st.markdown(lang["ressources-intro"])
        df = get_ressource_data()[["link", "description"]]
        df.columns = ["Link", "Description"]
        html_table = df.to_html(escape=False, index=False)
        st.markdown(html_table, unsafe_allow_html=True)

    def show_about(self, app_name):
        data_source_link = "https://www.meteoswiss.admin.ch/weather/measurement-systems/land-based-stations/swiss-national-basic-climatological-network.html"
        last_data_refresh = st.session_state["last_data_refresh"]
        station_number = len(self.station_df)
        st.image("saentis_wide.jpg", use_column_width=True)
        st.header(app_name)
        st.markdown(
            lang["app-info"].format(station_number, data_source_link, last_data_refresh)
        )
        st.markdown("**Parameters**")
        for key, value in self.parameters_dict.items():
            st.markdown(f"- {value}")

    def show_stats(self):
        config = ["time-aggregation", "analysis-options", "parameter"]
        sel_analysis = self.get_parameters(config)

        if lang["stats-analysis-options"].index(sel_analysis) == 0:
            self.show_summary_table()
        elif lang["stats-analysis-options"].index(sel_analysis) == 1:
            self.show_barchart()
        elif lang["stats-analysis-options"].index(sel_analysis) == 2:
            self.show_boxplot()
        elif lang["stats-analysis-options"].index(sel_analysis) == 3:
            self.show_stacked_lines()
        elif lang["stats-analysis-options"].index(sel_analysis) == 4:
            self.show_heatmap()
        elif lang["stats-analysis-options"].index(sel_analysis) == 5:
            self.show_time_series()
        elif lang["stats-analysis-options"].index(sel_analysis) == 6:
            self.show_spiral()
        elif lang["stats-analysis-options"].index(sel_analysis) == 7:
            self.show_histogram()

    def show_stations(self):
        def show_map():
            def format_popup_row(row):
                col_titles = df.columns
                result = f"""<table><tr>
                            <td>{col_titles[0]}</td>
                            <td>{row[col_titles[0]]}</td>
                            <tr>
                            <td>{col_titles[1]}</td>
                            <td>{row[col_titles[1]]}</td>
                            <tr>
                            <td>{col_titles[4]}</td>
                            <td>{row[col_titles[4]]}</td>
                            </tr>
                            <tr>
                            <td>{col_titles[9]}</td>
                            <td>{row[col_titles[9]]}</td>
                            </tr>
                            <tr>
                            <td>{col_titles[10]}</td>
                            <td>{row[col_titles[10]]}</td>
                            </tr>
                            </table>"""
                return result

            df = self.station_df

            df["tooltip"] = df.apply(format_popup_row, axis=1)
            num_of_stations = len(self.station_df)
            st.header("Map")
            st.markdown(lang["stations-intro"].format(num_of_stations))
            settings = {
                "latitude": "latitude",
                "longitude": "longitude",
                "width": 800,
                "height": 400,
                "tooltip": "tooltip",
                "popup": "station",
                "zoom_start": 7,
            }
            map_json = map_chart(df, settings)
            if map_json["last_object_clicked_popup"] is not None:
                station = map_json["last_object_clicked_popup"]
                row = self.station_df[self.station_df["station"] == station]
                more_info = """<a href="{}">{}</a>""".format(row.iloc[0]['station-info'], lang['more-info'])
                data_download_link = (
                    """<a href="{}">{}</a>""".format(row.iloc[0]['url'], lang["download-station-data"])
                )
                df = self.station_df.drop(columns=["url", "station-info", "tooltip"])
                row = df[df["station"] == station]
                transposed_df = row.T
                st.dataframe(transposed_df, use_container_width=True)
                st.markdown(more_info, unsafe_allow_html=True)
                st.markdown(data_download_link, unsafe_allow_html=True)

        def show_stats():
            num_of_stations = len(self.station_df)

            st.header(lang["summary-table"])
            st.markdown(lang["summary-table-intro"].format(num_of_stations))
            fields = self.station_df.columns.drop(["url", "station-info"])
            df = self.station_df[fields]
            df.columns = lang["stations-table-column-titles"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            show_download_button(
                self.station_df, {"button_text": lang["download_button_text"]}
            )

        sel_menu = st.sidebar.selectbox(
            label=lang["stations-analysis"], options=lang["stations-analysis-options"]
        )
        if lang["stations-analysis-options"].index(sel_menu) == 0:
            show_map()
        elif lang["stations-analysis-options"].index(sel_menu) == 1:
            show_stats()

    def display_data_grid(self):
        def get_filter():
            settings = {
                "stat_par": "",
                "stations": [],
                "years": [],
                "months": [],
                "value": {"parameter": self.parameters_short_dict[self.parameters[0]]},
            }
            options = {
                "stations_dict": self.stations_dict,
                "min_year": self.min_year,
                "max_year": self.max_year,
            }
            filter = show_filter(settings, lang, options)
            return filter

        st.header(lang["browse_data"])
        st.markdown(lang["browse_data_intro"])
        filter = get_filter()
        if self.time_aggregation == "day":
            df = self.get_base_data(filter, include_date=True)
        elif self.time_aggregation in ("week", "month"):
            df = self.get_base_data(filter, add_fields=["year"])
        else:
            df = self.get_base_data(filter)
        agg_func = {f: self.parameters_agg_dict[f] for f in self.parameters}
        if self.time_aggregation in ("month", "week"):
            df = (
                df.groupby(["station", "year", self.time_aggregation])[self.parameters]
                .agg(agg_func)
                .reset_index()
            )
        elif self.time_aggregation in ("year", "decade"):
            df = (
                df.groupby(["station", self.time_aggregation])[self.parameters]
                .agg(agg_func)
                .reset_index()
            )
        df = self.filter_values(filter, df)
        df = self.merge_station_columns(df, ["station name"])
        df = self.rename_columns(df)
        config = {
            "Year": st.column_config.NumberColumn(format="%d"),
            # this does not seem to be working
            "Date": st.column_config.DateColumn(format="YYYY-MM-DD"),
        }
        st.dataframe(
            df,
            hide_index=True,
            height=800,
            use_container_width=True,
            column_config=config,
        )

    def get_lin_reg(self, df: pd.DataFrame):
        df = df.dropna(how="all")
        if len(df) > 2:
            df["X_numeric"] = (df["date"] - df["date"].min()).dt.days
            x = np.array(list(df["X_numeric"]))
            y = np.array(list(df[self.par_label_no_unit]))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            return slope, intercept, r_value, p_value, std_err
        else:
            return None, None, None, None, None
        
    def mann_kendall(self):
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
            keys = lang["result-keys"]
            values = [
                f"{df['date'].min().year} to {df['date'].max().year}",
                f"{df[self.par_label_no_unit].min():.2f}",
                f"{df[self.par_label_no_unit].max():.2f}",
                f"{df[self.par_label_no_unit].mean():.2f}",
                f"{df[self.par_label_no_unit].std():.2f}",
                result.trend,
                f"{result.p:.2E}",
                f"{result.slope:.4f}",
            ]
            df = pd.DataFrame({"Parameter": keys, "Value": values})
            return df

        def show_result(result):
            ok = self.display == lang["trend-display-options"][0]
            ok = ok or (
                self.display == lang["trend-display-options"][1] and result.trend == self.display
            )
            return ok

        df = self.filter_base_data(get_filter())
        df = df.dropna(subset=[self.parameters[0]])
        agg_func = self.parameters_agg_dict[self.parameters[0]]
        aggregation_fields = ["year", "month", "station"]
        df = (
            df.groupby(aggregation_fields)[self.parameters]
            .agg([agg_func])
            .reset_index()
        )
        df.columns = aggregation_fields + [self.par_label_no_unit]
        df = add_date_column(df, "month")
        settings = {
            "x": "date",
            "y": self.par_label_no_unit,
            "x_title": "",
            "y_title": self.parameters_short_dict[self.parameters[0]],
            "tooltip": ["station", "date", self.par_label_no_unit],
            "width": 800,
            "height": 300,
            "show_regression": self.show_regression
        }
        num_stations = st.empty()
        # settings["x_domain"] = [
        #     f"{data['Date'].min().year}-01-01",
        #     f"{data['Date'].max().year}-12-31",
        # ]
        min_y = int(df[self.par_label_no_unit].min()) - 1
        max_y = int(df[self.par_label_no_unit].max()) + 1
        settings["y_domain"] = [min_y, max_y]
        cnt_stations = 0
        cnt_all_stations = 0

        for station in self.stations_dict.keys():
            cols = st.columns([3, 1])
            filtered_df = df[df["station"] == station].sort_values(by="date")
            
            if len(filtered_df) > MIN_POINTS:
                # settings['x_domain'] = [ f"{df['month_date'].min().year}-01-01", f"{df['month_date'].max().year}-12-31"]
                cnt_all_stations += 1
                values = list(filtered_df[self.par_label_no_unit])
                result = mk.seasonal_test(values, 12)
                if show_result(result):
                    settings[
                        "title"
                    ] = f"{self.stations_dict[station]} ({station}): {result.trend}"
                    with cols[0]:
                        if settings["show_regression"]:
                            slope, intercept, r_value, p_value, std_err = self.get_lin_reg(
                                filtered_df
                            )

                        time_series_chart(filtered_df, settings)
                    with cols[1]:
                        summary_df = get_summary_df(df, result)
                        st.dataframe(summary_df, hide_index=True, use_container_width=True)
                    cnt_stations += 1
                    num_stations.markdown(
                        lang["stations-shown"].format(cnt_stations, len(self.stations_dict))
                    )

    def show_browse_data(self, config):
        # todo: include records menu item: show value and date for record events
        # record year, month, date
        sel_analysis = self.get_parameters(config)
        self.display_data_grid()
        # if analysis_options.index(sel_analysis) == 0:
        #     self.display_data_grid()

    def show_trend(self):
        def get_filter():
            settings = {
                "stat_par": "",
                "stations": [],
                "years": [],
                "months": [],
            }
            options = {
                "stations_dict": self.stations_dict,
                "min_year": self.min_year,
                "max_year": self.max_year,
            }
            filter = show_filter(settings, lang, options)
            return filter

        # create monthly data
        config = ["analysis-options", "parameter"]
        sel_analysis = self.get_parameters(config)
        st.header(lang["trend-title"].format(self.parameters_short_dict[self.parameters[0]]))
        if lang['trend-analysis-options'].index(sel_analysis) == 0:
            st.markdown(lang['trend-intro'])
        else:
            self.mann_kendall()
