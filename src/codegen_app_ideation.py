import streamlit as st

from lib.codegen_streamlit_lib import StreamlitLib
from lib.codegen_utilities import get_app_config
# from lib.codegen_utilities import log_debug


DEBUG = True

app_config = get_app_config()
cgsl = StreamlitLib(app_config)


def get_features_data():
    """
    Returns the features data: template, mandatory fields
    The features are related with the form buttons
    """
    return {
        "generate_app_names": {
            "template": "generate_app_names_prompt.txt",
            "mandatory_fields": [
                "title",
                "subtitle",
                "application_subject",
                "web_or_mobile",
            ],
        },
        "generate_app_structure": {
            "template": "generate_app_structure_prompt.txt",
            "mandatory_fields": [
                "title",
                "subtitle",
                "application_subject",
                "web_or_mobile",
            ],
        },
        "generate_presentation": {
            "template": "generate_app_presentation_prompt.txt",
            "mandatory_fields": [
                "title",
                "subtitle",
                "application_subject",
                "web_or_mobile",
                "problem_statement",
                "objective",
                "technologies_used",
                "application_features",
                "how_it_works",
                # "screenshots",
                "benefits",
                "feedback_and_future_development",
                "future_vision",
            ],
        }
    }


def get_fields_data():
    """
    Returns the fields data: description, type, length
    """
    fields_data = {
        "title": {
            "title": "Application name",
            "help": "If you don't have a name, you can use "
                    "[Generate App Names] button to generate one.",
            "type": "text",
        },
        "subtitle": {
            "title": "Subtitle",
            "help": "Super short description for a sub-title",
            "type": "text",
        },
        "application_subject": {
            "title": "Summary",
            "help": "Describe the application in a brief summary.",
        },
        "web_or_mobile": {
            "title": "Application type",
            "help": "",
            "type": "radio",
            "options": ["Web", "Mobile", "Web and Mobile"],
        },
        "problem_statement": {
            "title": "Problem Statement",
            "help": "Describe the problem the application addresses. Explain"
                    " why the problem is significant and how the audience"
                    " might relate to it.",
        },
        "objective": {
            "title": "Objective",
            "help": "Explain the application's main goal. Emphasize how the"
                    " objective aligns with solving the problem introduced"
                    " earlier.",
        },
        "technologies_used": {
            "title": "Technologies Used",
            "help": "Mention programming languages, AI models, API providers"
                    "/platforms, etc. Break down which technologies were used"
                    " and why they were chosen for this project.",
        },
        "application_features": {
            "title": "Application Features",
            "help": "Summary of the main features. Provide detailed"
                    " explanations or anecdotes for each feature's utility.",
        },
        "how_it_works": {
            "title": "How It Works",
            "help": "Describe the workflow from user input to API integration"
                    " and outputs. Detail the process flow, ensuring the"
                    " audience understands how each element contributes to the"
                    " functionality.",
        },
        "screenshots": {
            "title": "Screenshots",
            "help": "Include screenshots of the application showcasing key"
                    " parts. Describe each screenshot's relevance, pointing"
                    " out important functionalities.",
            "enabled": False,
        },
        "benefits": {
            "title": "Benefits",
            "help": "Include the main benefits of the application. Persuade"
                    " the audience why these benefits help address the user's"
                    " problem effectively.",
        },
        "feedback_and_future_development": {
            "title": "Feedback and Future Development",
            "help": "Notable positive aspects and potential improvements."
                    " Emphasize user satisfaction and iterate potential"
                    " evolution based on feedback.",
        },
        "future_vision": {
            "title": "Future Vision",
            "help": "Describe possible enhancements like expanding"
                    " capabilities to more complex tasks, and how it can"
                    " evolve to embrace users\' needs. Include possible"
                    " use cases (e.g., training, education, real-time"
                    " support).",
        },
    }
    return fields_data


def get_buttons_config():
    """
    Returns the buttons configuration
    """
    buttons_config = [
        {
            "text": "Generate App Names",
            "key": "generate_app_names",
            "enable_config_name": "GENERATE_APP_NAMES_ENABLED",
            "type": "submit",
        },
        {
            "text": "Generate App Structure",
            "key": "generate_app_structure",
            "enable_config_name": "GENERATE_APP_STRUCTURE_ENABLED",
            "type": "submit",
        },
        {
            "text": "Generate Presentation",
            "key": "generate_presentation",
            "enable_config_name": "GENERATE_PRESENTATION_ENABLED",
            "type": "submit",
        },
        {
            "text": "Generate Video Script",
            "key": "generate_video_script",
            "enable_config_name": "GENERATE_VIDEO_SCRIPT_ENABLED",
            "type": "submit",
        },
        # get_response_as_prompt_button_config(
        #     "use_response_as_prompt_app_ideation_tab"),
        # get_prompt_enhancement_button_config(
        #     "prompt_enhancement_app_ideation_tab"),
    ]
    return buttons_config


def get_form_config():
    """
    Returns the ideation form configuration
    """
    form_config = {
        "title": "Application Ideation Form",
        "name": "application_form",
        "subtitle": "This form will help you generate the initial plan for the"
                    " application idea. Please fill in the following fields:",
        "suffix": "When you are ready, click one of the buttons below to"
                  " generate the application idea.",
        "fields": get_fields_data(),
        "buttons_config": get_buttons_config(),
        "features_data": get_features_data(),
        "form_session_state_key": "application_form_data",
        # "buttons_function": add_buttons_for_app_ideation_tab,
    }
    return form_config


def show_ideation_form(container: st.container):
    """
    Returns the ideation form
    """
    form_config = get_form_config()
    return cgsl.show_form(container, form_config)
