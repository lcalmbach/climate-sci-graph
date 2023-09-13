import streamlit as st
import iso639
import json
from io import BytesIO
import os
import socket
import string
import random
import pandas as pd
import numpy as np

LOCAL_HOST = "liestal"
DEV_MACHINES = [LOCAL_HOST]


def reduce_memory_usage(df, verbose=True):
    numerics = ["int8", "int16", "int32", "int64", "float16", "float32", "float64"]
    start_mem = df.memory_usage().sum() / 1024**2
    for col in df.columns:
        col_type = df[col].dtypes
        if col_type in numerics:
            c_min = df[col].min()
            c_max = df[col].max()
            if str(col_type)[:3] == "int":
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                    df[col] = df[col].astype(np.int64)
            else:
                if (
                    c_min > np.finfo(np.float16).min
                    and c_max < np.finfo(np.float16).max
                ):
                    df[col] = df[col].astype(np.float16)
                elif (
                    c_min > np.finfo(np.float32).min
                    and c_max < np.finfo(np.float32).max
                ):
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)
    end_mem = df.memory_usage().sum() / 1024**2
    if verbose:
        print(
            "Mem. usage decreased to {:.2f} Mb ({:.1f}% reduction)".format(
                end_mem, 100 * (start_mem - end_mem) / start_mem
            )
        )
    return df


def init_lang_dict_complete(module: str, key: str):
    """
    Retrieves the complete language dictionary from a JSON file.

    Returns:
    - lang (dict): A Python dictionary containing all the language strings.
    """
    lang_file = f"./lang/{module.replace('.py','.json')}"
    try:
        with open(lang_file, "r") as file:
            st.session_state["lang_dict"][key] = json.load(file)
    except FileNotFoundError:
        print("File not found.")
        return {}
    except json.JSONDecodeError:
        print("Invalid JSON format.")
        return {}
    except Exception as e:
        print("An error occurred:", str(e))
        return {}


def get_all_language_dict():
    """
    Retrieves a dictionary containing all the available languages and their
    ISO 639-1 codes.

    Returns:
        language_dict (dict): A Python dictionary where the keys are the ISO 639-1 codes and the values are the language names.
    """
    keys = [lang["iso639_1"] for lang in iso639.data if lang["iso639_1"] != ""]
    values = [lang["name"] for lang in iso639.data if lang["iso639_1"] != ""]
    language_dict = dict(zip(keys, values))
    return language_dict


def get_used_languages(lang_dict: dict):
    language_dict = get_all_language_dict()
    used_languages = list(lang_dict.keys())
    extracted_dict = {
        key: language_dict[key] for key in used_languages if key in language_dict
    }
    return extracted_dict


def get_lang(page: str) -> dict:
    """Retrieves the dictionary from the session statethe hierarchical
    organisation is lang_dict, then one key for ever py file (module)

    Args:
        page (str): every py file with multilang commands must have a file
                    with the same name and extension json in the lang folder

    Returns:
        _type_: _description_
    """
    return st.session_state["lang_dict"][page][st.session_state["lang"]]


def download_button(data, download_filename, button_text):
    """
    Function to create a download button for a given object.

    Parameters:
    - object_to_download: The object to be downloaded.
    - download_filename: The name of the file to be downloaded.
    - button_text: The text to be displayed on the download button.
    """
    # Create a BytesIO buffer
    json_bytes = json.dumps(data).encode("utf-8")
    buffer = BytesIO(json_bytes)

    # Set the appropriate headers for the browser to recognize the download
    st.set_option("deprecation.showfileUploaderEncoding", False)
    st.download_button(
        label=button_text,
        data=buffer,
        file_name=download_filename,
        mime="application/json",
    )


def get_var(varname: str):
    if socket.gethostname().lower() == LOCAL_HOST:
        return os.environ[varname]
    else:
        return st.secrets[varname]


def is_valid_json(json_str):
    try:
        json.loads(json_str)
        return True
    except ValueError:
        return False


def get_var(varname: str) -> str:
    """
    Retrieves the value of a given environment variable or secret from the Streamlit configuration.

    If the current host is the local machine (according to the hostname), the environment variable is looked up in the system's environment variables.
    Otherwise, the secret value is fetched from Streamlit's secrets dictionary.

    Args:
        varname (str): The name of the environment variable or secret to retrieve.

    Returns:
        The value of the environment variable or secret, as a string.

    Raises:
        KeyError: If the environment variable or secret is not defined.
    """
    if socket.gethostname().lower() == LOCAL_HOST:
        return os.environ[varname]
    else:
        return st.secrets[varname]


def show_filter(settings: dict, lang: dict, options: dict):
    """Shows a list of filters in the sidebar.

    Args:
        settings (dict): holds the keys and empty values of the filters to be shown
        lang (dict): holds the lang settings for the translated labels
        options (dict): holds the required options lists and mandatory parameters such as min, max for a slider
    """
    with st.sidebar:
        with st.expander(f"🔎{lang['filter']}", expanded=True):
            if "" in settings:
                settings["parameter"] = st.selectbox(
                    lang["parameter"], options["parameter_list"]
                )
            if "station" in settings:
                settings["station"] = st.selectbox(
                    label=lang["stations"],
                    options=list(options["stations_dict"].keys()),
                    format_func=lambda x: options["stations_dict"][x],
                )
            if "stations" in settings:
                settings["stations"] = st.multiselect(
                    label=lang["stations"],
                    options=list(options["stations_dict"].keys()),
                    format_func=lambda x: options["stations_dict"][x],
                )
            if "year" in settings:
                years = sorted(
                    range(options["min_year"], options["max_year"] + 1), reverse=True
                )
                settings["year"] = st.selectbox(lang["year"], options=years)
            if "years" in settings:
                settings["years"] = st.slider(
                    lang["years"],
                    min_value=options["min_year"],
                    max_value=options["max_year"],
                    value=[options["min_year"], options["max_year"]],
                )
            if "month" in settings:
                settings["month"] = st.selectbox(lang["month"], options=range(1, 13))
            if "months" in settings:
                settings["months"] = st.multiselect(
                    lang["months"], options=range(1, 13)
                )
            if "value" in settings:
                settings["value"]["use_numeric_filter"] = st.checkbox(
                    lang["use_numeric_filter"]
                )
                if settings["value"]["use_numeric_filter"]:
                    options_compare = [">=", ">", "<=", "<" "="]
                    settings["value"]["compare_op"] = st.selectbox(
                        label=settings["value"]["parameter"], options=options_compare
                    )
                    settings["value"]["value"] = st.number_input(lang["numeric_filter"])

    return settings


def randomword(length):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


def show_download_button(df: pd.DataFrame, cfg: dict = {}):
    if "filename" not in cfg:
        cfg["filename"] = "file.csv"
    key = randomword(10)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=cfg["button_text"],
        data=csv,
        file_name=cfg["filename"],
        mime="text/csv",
        key=key,
    )


def round_to_nearest(value, base):
    return int(value / base / base) * base


def get_config_value(key: str) -> str:
    if socket.gethostname().lower() in DEV_MACHINES:
        return os.environ.get(key)
    else:
        return st.secrets[key]


def remove_special_chars(s: str):
    s_modified = s.replace("[", "(").replace("]", ")")
    return s_modified


def remove_unit(s: str):
    s_modified = s[: s.find("[")].strip()
    return s_modified


def add_date_column(df: pd.DataFrame, agg_type: str):

    if agg_type == "day":
        ...
    elif agg_type == "week":
        df["date"] = df["date"] + pd.to_timedelta(
            (2 - df["date"].dt.weekday + 7) % 7, unit="d"
        )
    else:
        if agg_type == "year":
            df["month"] = 7
        if agg_type == "decade":
            df["year"] = df["decade"] + 5
            df["month"] = 7
        df["date"] = pd.to_datetime(
            df["year"].astype(str) + "-" + df["month"].astype(str) + "-15"
        )

    return df
