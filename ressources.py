import streamlit as st
import pandas as pd
import os

from helper import init_lang_dict_complete, get_lang

PAGE = __name__
lang = {}


class Ressources:
    def __init__(self):
        global lang
        init_lang_dict_complete(os.path.basename(__file__), __name__)
        lang = get_lang(PAGE)

    @st.cache_data()
    def get_data(_self):
        df = pd.read_csv(RESSOURCES_FILE, sep=";")
        df["link"] = '<a href="' + df["url"] + '">' + df["title"] + "</a>"
        return df

    def run(self):
        st.header(lang["title"])
        st.markdown(lang["intro"])
        df = self.get_data()[["link", "description"]]
        df.columns = ["Link", "Description"]
        html_table = df.to_html(escape=False, index=False)
        st.markdown(html_table, unsafe_allow_html=True)
