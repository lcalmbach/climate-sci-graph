import streamlit as st
import pandas as pd
from streamlit_lottie import st_lottie
import requests
from helper import get_used_languages, init_lang_dict_complete, get_lang
from streamlit_option_menu import option_menu
import re
import io
from enum import Enum
from trend import TrendAnalysis
import datetime

from about import About
from stations import Stations
from ressources import Ressources
from monthly_stats import MonthlyStats


__version__ = "0.0.2"
__author__ = "Lukas Calmbach"
__author_email__ = "lcalmbach@gmail.com"
VERSION_DATE = "2023-09-31"
APP_NAME = "ClimateSciGraph"
GIT_REPO = "https://github.com/lcalmbach/nbcn-browser"
PAGE = "app"

lang = {}
LOTTIE_URL = "https://assets9.lottiefiles.com/temp/lf20_rpC1Rd.json"
LOTTIE_URL = "https://lottie.host/016f9a14-ca58-4ade-85fa-ccce6bbc9318/ApQE6zjqWN.json"

STATIONS_URL = "./data/1_download_url_nbcn_homogen.csv"


class Menu(Enum):
    ABOUT = 0
    STATIONS = 1
    MONTHLY = 2
    TREND = 3
    RESSOURCES = 4


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


def get_menu_option():
    menu_options = lang["menu-options"]
    # https://icons.getbootstrap.com/
    with st.sidebar:
        st.markdown(f"## {APP_NAME}")
        return option_menu(
            None,
            menu_options,
            icons=["house", "geo", "calendar-month", "graph-up", "archive"],
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
    lottie_search_names, ok = get_lottie()
    if ok:
        with st.sidebar:
            st_lottie(lottie_search_names, height=140, loop=20)
    else:
        pass


@st.cache_data(show_spinner=False)
def get_data():
    def find_first_row(url):
        first_line = 0
        col_widths = []
        try:
            search_text = "Year"
            response = requests.get(url)
            if response.status_code == 200:
                file_content = io.StringIO(response.text)
                line_number = 1
                for line in file_content:
                    if search_text in line:
                        first_line = line_number
                        words = re.findall(r"\b\w+\b", line)
                        # start_positions = [m.start() for m in re.finditer(r'\b\w+\b', line)]
                        if len(words) == 3:
                            col_widths = [6, 13, 17]
                        else:
                            col_widths = [6, 13, 17, 13]
                    else:
                        line_number += 1

        except Exception as e:
            print(f"An error occurred: {e}")
        return first_line - 1, col_widths

    col_widths = []
    skiprows = 0
    # open file with all stations and associated urls
    url_df = pd.read_csv(STATIONS_URL, sep=";")
    stations = list(url_df["Abbreviation"])
    url_df.set_index("Abbreviation", inplace=True)
    # init dataframe
    station_data = pd.DataFrame(
        {
            "Station": [],
            "Year": [],
            "Month": [],
            "Date": [],
            "Temperature": [],
            "Precipitation": [],
        }
    )
    for station in stations:
        url = url_df.loc[station]["URL"]
        skiprows, col_widths = find_first_row(url)
        df = pd.read_fwf(url, col_widths=col_widths, skiprows=skiprows)
        df["Station"] = station
        # some stations have no precipitation data, so add this column
        if "Precipitation" not in df:
            df = df.assign(Precipitation=None)
        df["Day"] = 15
        df["Date"] = pd.to_datetime(df[["Year", "Month", "Day"]])
        df[["Temperature", "Precipitation"]] = df[
            ["Temperature", "Precipitation"]
        ].astype(float)
        df[["Year", "Month"]] = df[["Year", "Month"]].astype(int)
        station_data = pd.concat([station_data, df])

    stations = url_df.reset_index()[["Abbreviation", "Station"]]
    stations.columns = ["Station", "Stationname"]
    station_data = station_data.merge(stations, on="Station", how="left")
    # station_data.drop('Abbreviation', axis=1, inplace=True)
    return station_data, url_df


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
        st.session_state["station_data"], st.session_state["station_url"] = get_data()
    show_lottie()

    sel_menu_option = get_menu_option()
    if lang["menu-options"].index(sel_menu_option) == Menu.ABOUT.value:
        app = About(APP_NAME)
    elif lang["menu-options"].index(sel_menu_option) == Menu.STATIONS.value:
        app = Stations()
    elif lang["menu-options"].index(sel_menu_option) == Menu.MONTHLY.value:
        app = MonthlyStats()
    elif lang["menu-options"].index(sel_menu_option) == Menu.TREND.value:
        app = TrendAnalysis()
    elif lang["menu-options"].index(sel_menu_option) == Menu.RESSOURCES.value:
        app = Ressources()
    app.run()
    display_language_selection()
    st.sidebar.markdown(get_app_info(), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
