"""
This module contains the code for the buttons that are displayed on
the Streamlit app.
"""
import streamlit as st

from lib.codegen_streamlit_lib import StreamlitLib
from lib.codegen_utilities import get_app_config

DEBUG = False

app_config = get_app_config()
cgsl = StreamlitLib(app_config)


def get_response_as_prompt_button_config(key_name: str):
    """
    Returns the response as prompt button config
    """
    return {
        "text": "Use Response as Prompt",
        "key": key_name,
        "enable_config_name": "USE_RESPONSE_AS_PROMPT_ENABLED",
        # "on_click": cgsl.use_response_as_prompt,
        "on_click": cgsl.set_session_flag,
        "args": (key_name, "use_response_as_prompt_flag"),
    }


def get_prompt_enhancement_button_config(key_name: str):
    """
    Returns the prompt enhancement button config
    """
    return {
        "text": "Enhance prompt",
        "key": key_name,
        "type": "checkbox",
        # "on_change": cgsl.prompt_enhancement,
        "on_change": cgsl.set_session_flag,
        "args": (key_name, "prompt_enhancement_flag"),
    }


def get_use_embeddings_button_config(key_name: str):
    """
    Returns the use embeddings button config
    """
    return {
        "text": "Use Embeddings",
        "key": key_name,
        "type": "checkbox",
        "enable_config_name": "USE_EMBEDDINGS_ENABLED",
        "on_change": cgsl.set_session_flag,
        "args": (key_name, "use_embeddings_flag"),
    }


def add_buttons_for_main_tab():
    """
    Add the main tab buttons section to the page
    """
    with st.container():
        buttons_config = [
            {
                "text": "Answer Question",
                "key": "generate_text",
                "enable_config_name": "TEXT_GENERATION_ENABLED",
            },
            {
                "text": "Generate Video",
                "key": "generate_video",
                "enable_config_name": "VIDEO_GENERATION_ENABLED",
            },
            {
                "text": "Generate Image",
                "key": "generate_image",
                "enable_config_name": "IMAGE_GENERATION_ENABLED",
            },
            # {
            #     "text": "",
            #     "type": "spacer",
            # },
            get_response_as_prompt_button_config(
                "use_response_as_prompt_main_tab"),
            get_prompt_enhancement_button_config(
                "prompt_enhancement_main_tab"),
        ]
        cgsl.show_buttons_row(buttons_config)


def add_buttons_for_code_gen_tab():
    """
    Add the code generation tab buttons section to the page
    """
    with st.container():
        buttons_config = [
            {
                "text": "Generate Config & Tools Code",
                "key": "generate_code",
                "enable_config_name": "CODE_GENERATION_ENABLED",
            },
            get_use_embeddings_button_config(
                "use_embeddings_code_gen_tab",
            ),
            {
                "text": "Start App Code",
                "key": "start_app_code",
                "enable_config_name": "START_APP_CODE_ENABLED",
            },
            get_response_as_prompt_button_config(
                "use_response_as_prompt_code_gen_tab"),
            get_prompt_enhancement_button_config(
                "prompt_enhancement_code_gen_tab"),
        ]
        cgsl.show_buttons_row(buttons_config)
