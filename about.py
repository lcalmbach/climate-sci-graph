import streamlit as st
import os

from helper import init_lang_dict_complete, get_lang

PAGE = __name__
lang = {}


class About:
    def __init__(self, app_name):
        global lang
        init_lang_dict_complete(os.path.basename(__file__), __name__)
        lang = get_lang(PAGE)
        self.app_name = app_name
        self.station_url = st.session_state.station_url

    def run(self):
        data_source_link = "https://www.meteoswiss.admin.ch/weather/measurement-systems/land-based-stations/swiss-national-basic-climatological-network.html"
        last_data_refresh = st.session_state["last_data_refresh"]
        station_number = len(self.station_url)
        st.image("saentis_wide.jpg", use_column_width=True)
        st.header(self.app_name)
        st.markdown(
            lang["app-info"].format(station_number, data_source_link, last_data_refresh)
        )
