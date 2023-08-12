import streamlit as st
import os

from helper import init_lang_dict_complete, get_lang
from plots import map_chart
from helper import show_download_button

PAGE = __name__
lang = {}


class Stations:
    def __init__(self):
        global lang

        init_lang_dict_complete(os.path.basename(__file__), __name__)
        lang = get_lang(PAGE)
        self.stations_summary_df = st.session_state["station_url"].reset_index()
        self.stations_summary_df = self.add_station_info_link(self.stations_summary_df)

    def add_station_info_link(self, df):
        def create_link(row):
            link_temlate = "https://www.meteoschweiz.admin.ch/service-und-publikationen/applikationen/messwerte-und-messnetze.html#param=messnetz-klima&station={}&lang=de&chart=month"
            url = link_temlate.format(row["Abbreviation"])
            return url

        df["Station Info"] = df.apply(create_link, axis=1)
        return df

    def show_map(self):
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

        df = self.stations_summary_df

        df["tooltip"] = df.apply(format_popup_row, axis=1)
        num_of_stations = len(self.stations_summary_df)
        st.header("Map")
        st.markdown(lang["intro"].format(num_of_stations))
        settings = {
            "latitude": "Latitude",
            "longitude": "Longitude",
            "width": 800,
            "height": 400,
            "tooltip": "tooltip",
            "popup": "Station",
            "zoom_start": 7,
        }
        map_json = map_chart(df, settings)
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
        fields = [
            "Abbreviation",
            "Station",
            "WIGOS-ID",
            "Data since",
            "Station height m. a. sea level",
            "CoordinatesE",
            "CoordinatesN",
            "Latitude",
            "Longitude",
            "Climate region",
            "Canton",
        ]
        df = self.stations_summary_df[fields]
        df.columns = lang["table_column_titles"]
        st.dataframe(df, use_container_width=True, hide_index=True)
        show_download_button(
            self.stations_summary_df, {"button_text": lang["download_button_text"]}
        )

    def run(self):
        sel_menu = st.sidebar.selectbox(
            label=lang["analysis"], options=lang["analysis-options"]
        )
        if lang["analysis-options"].index(sel_menu) == 0:
            self.show_map()
        elif lang["analysis-options"].index(sel_menu) == 1:
            self.show_stats()
