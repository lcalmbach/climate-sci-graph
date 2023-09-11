import streamlit as st
import pandas as pd
from streamlit_lottie import st_lottie
import requests
from helper import get_used_languages, init_lang_dict_complete, get_lang
from streamlit_option_menu import option_menu
from enum import Enum
import datetime

import nbcn

__version__ = "0.0.7"
__author__ = "Lukas Calmbach"
__author_email__ = "lcalmbach@gmail.com"
VERSION_DATE = "2023-08-31"
APP_NAME = "ClimateSciGraph"
GIT_REPO = "https://github.com/lcalmbach/nbcn-browser"
PAGE = "app"

lang = {}
LOTTIE_URL = "https://assets9.lottiefiles.com/temp/lf20_rpC1Rd.json"
LOTTIE_URL = "https://lottie.host/016f9a14-ca58-4ade-85fa-ccce6bbc9318/ApQE6zjqWN.json"


class Menu(Enum):
    ABOUT = 0
    STATIONS = 1
    BROWSE = 2
    MONTHLY = 3
    TREND = 4
    RESSOURCES = 5


def init():
    st.set_page_config(
        page_title=APP_NAME,
        page_icon="🌡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    if not ("lang" in st.session_state):
        # first item is default language
        st.session_state["lang_dict"] = {}
        init_lang_dict_complete("app.py", PAGE)
        st.session_state["used_languages_dict"] = get_used_languages(
            st.session_state["lang_dict"][PAGE]
        )
        st.session_state["lang"] = next(
            iter(st.session_state["used_languages_dict"].items())
        )[0]
        st.session_state["last_data_refresh"] = datetime.datetime.now().strftime("%x")


def get_menu_selection(menu_options):
    # https://icons.getbootstrap.com/
    with st.sidebar:
        st.markdown(f"## {APP_NAME}")
        return option_menu(
            None,
            menu_options,
            icons=["house", "geo", "database", "calendar-month", "graph-up", "archive"],
            menu_icon="cast",
            default_index=0,
        )


def get_app_info():
    """
    Returns a string containing information about the application.
    Returns:
    - info (str): A formatted string containing details about the application.
    """
    created_by = lang["created-by"]
    powered_by = lang["powered-by"]
    version = lang["version"]
    translation = lang["translation"]
    data_source = lang["data-source"]

    info = f"""<div style="background-color:powderblue; padding: 10px;border-radius: 15px;">
    <small>{created_by} <a href="mailto:{__author_email__}">{__author__}</a><br>
    {version}: {__version__} ({VERSION_DATE})<br>
    {data_source}: <a href="https://www.meteoswiss.admin.ch/services-and-publications/applications/ext/climate-tables-homogenized.html">MeteoSwiss</a><br>
    {powered_by} <a href="https://streamlit.io/">Streamlit</a>, <a href="https://github.com/mmhs013/pymannkendall">pymannkendall</a><br>
    {translation} <a href="https://lcalmbach-gpt-translate-app-i49g8c.streamlit.app/">PolyglotGPT</a><br>
    <a href="{GIT_REPO}">git-repo</a><br>
    """
    return info


def display_language_selection():
    """
    The display_info function displays information about the application. It
    uses the st.expander container to create an expandable section for the
    information. Inside the expander, displays the input and output format.
    """
    index = list(st.session_state["used_languages_dict"].keys()).index(
        st.session_state["lang"]
    )
    x = st.sidebar.selectbox(
        label=f'🌐{lang["language"]}',
        options=st.session_state["used_languages_dict"].keys(),
        format_func=lambda x: st.session_state["used_languages_dict"][x],
        index=index,
    )
    if x != st.session_state["lang"]:
        st.session_state["lang"] = x
        st.experimental_rerun()


@st.cache_data(show_spinner=False)
def get_lottie():
    """Performs a GET request to fetch JSON data from a specified URL.

    Returns:
        tuple: A tuple containing the JSON response and a flag indicating the
        success of the request.

    Raises:
        requests.exceptions.RequestException: If an error occurs during the
        GET request. ValueError: If an error occurs while parsing the JSON
        response.
    """
    ok = True
    r = None
    try:
        response = requests.get(LOTTIE_URL)
        r = response.json()
    except requests.exceptions.RequestException as e:
        print(lang["get-request-error"]).format(e)
        ok = False
    except ValueError as e:
        print(lang["json-parsing-error"].format(e))
        ok = False
    return r, ok


def show_lottie():
    """
    Displays lottie animation if it is available.
    """
    lottie_search_names, ok = get_lottie()
    if ok:
        with st.sidebar:
            st_lottie(lottie_search_names, height=140, loop=20)
    else:
        pass


def main() -> None:
    """
    This function runs an app that classifies text data. Depending on the user's
    input option, it retrieves data from a demo or an uploaded file. Then,
    randomly selects a fixed number of records from the dataframe provided using
    record_selection function. The selected dataframe and dictionary of categories
    are previewed on the screen. If the user presses classify, the function runs the
    Classifier class on the selected dataframe, returns a response dataframe, and
    offers the user the option to download the dataframe to a CSV file.
    """
    global lang

    init()

    lang = get_lang(PAGE)
    with st.spinner(lang["loading-data"]):
        # if not ("ncbn" in st.session_state):
        st.session_state.ncbn = nbcn.NCBN(APP_NAME)
    show_lottie()
    ncbn = st.session_state.ncbn
    ncbn.menu_selection = get_menu_selection(ncbn.menu_options)
    display_language_selection()
    st.sidebar.markdown(get_app_info(), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
