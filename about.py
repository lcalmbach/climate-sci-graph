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

    def run(self):
        st.image('saentis_wide.jpg', use_column_width=True)
        st.header(self.app_name)
        st.markdown(lang["app-info"])
