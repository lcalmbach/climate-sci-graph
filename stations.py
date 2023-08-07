import streamlit as st
import os

from helper import init_lang_dict_complete, get_lang
from plots import map_chart

PAGE = __name__
lang = {}


class Stations:
    def __init__(self):
        global lang

        init_lang_dict_complete(os.path.basename(__file__), __name__)
        lang = get_lang(PAGE)
        self.stations_summary_df = st.session_state["stations_url"].reset_index()
        self.stations_summary_df = self.add_station_info_link(self.stations_summary_df)

    def add_station_info_link(self, df):
        def create_link(row):
            link_temlate = "https://www.meteoschweiz.admin.ch/service-und-publikationen/applikationen/messwerte-und-messnetze.html#param=messnetz-klima&station={}&lang=de&chart=month"
            url = link_temlate.format(row["Abbreviation"])
            return url

        df["Station Info"] = df.apply(create_link, axis=1)
        return df

    def show_map(self):
        num_of_stations = len(self.stations_summary_df)

        st.header("Map")
        st.markdown(lang["intro"].format(num_of_stations))
        settings = {
            "latitude": "Latitude",
            "longitude": "Longitude",
            "width": 800,
            "tooltip": "Station",
            "popup": "Station",
            "zoom_start": 7,
        }
        map_json = map_chart(self.stations_summary_df, settings)
        if map_json["last_object_clicked_popup"] is not None:
            station = map_json["last_object_clicked_popup"]
            row = self.stations_summary_df[
                self.stations_summary_df["Station"] == station
            ]
            more_info = f"""<a href="{row.iloc[0]['Station Info']}">More Info</a>"""
            data_download_link = (
                f"""<a href="{row.iloc[0]['URL']}">Download data from station</a>"""
            )
            df = self.stations_summary_df.drop(columns=["URL", "Station Info"])
            row = df[df["Station"] == station]
            transposed_df = row.T
            st.dataframe(transposed_df, use_container_width=True)
            st.markdown(more_info, unsafe_allow_html=True)
            st.markdown(data_download_link, unsafe_allow_html=True)

    def show_stats(self):
        num_of_stations = len(self.stations_summary_df)

        st.header(lang["summary-table"])
        st.markdown(lang["summary-table-intro"].format(num_of_stations))
        st.dataframe(self.stations_summary_df)

    def run(self):
        sel_menu = st.sidebar.selectbox(
            label=lang["analysis"], options=lang["analysis-options"]
        )
        if lang["analysis-options"].index(sel_menu) == 0:
            self.show_map()
        elif lang["analysis-options"].index(sel_menu) == 1:
            self.show_stats()
