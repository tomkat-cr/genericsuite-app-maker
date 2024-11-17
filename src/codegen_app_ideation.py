import streamlit as st

from lib.codegen_streamlit_lib import StreamlitLib
from lib.codegen_utilities import get_app_config
# from src.codegen_buttons import (
#     get_response_as_prompt_button_config,
#     get_prompt_enhancement_button_config,
# )
from lib.codegen_utilities import log_debug


DEBUG = True

app_config = get_app_config()
cgsl = StreamlitLib(app_config)


def get_features_data():
    """
    Returns the features data: template, mandatory fields
    The features are related with the form buttons
    """
    return {
        "generate_app_ideas": {
            "template": "generate_app_ideas_prompt.txt",
            "mandatory_fields": [
                # "title",
                # "subtitle",
                "application_subject",
                "timeframe",
                "web_or_mobile",
            ],
        },
        "generate_app_names": {
            "template": "generate_app_names_prompt.txt",
            "mandatory_fields": [
                # "title",
                # "subtitle",
                "application_subject",
                "web_or_mobile",
            ],
        },
        "generate_app_structure": {
            "template": "generate_app_structure_prompt.txt",
            "mandatory_fields": [
                "title",
                # "subtitle",
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


def get_features_data_from_prompt():
    """
    Returns the features data: template, mandatory fields
    The features are related with the from-prompt form buttons
    """
    return {
        "generate_app_ideas_from_prompt": {
            "template": "generate_app_ideas_from_question_prompt.txt",
            "mandatory_fields": [
                "question",
            ],
        },
        "generate_app_names_from_prompt": {
            "template": "generate_app_names_from_question_prompt.txt",
            "mandatory_fields": [
                "question",
            ],
        },
        "generate_app_structure_from_prompt": {
            "template": "generate_app_structure_from_question_prompt.txt",
            "mandatory_fields": [
                "question",
            ],
        },
        "generate_presentation_from_prompt": {
            "template": "generate_app_presentation_from_question_prompt.txt",
            "mandatory_fields": [
                "question",
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
            "type": "selectbox",
            "options": ["", "Web", "Mobile", "Web and Mobile"],
        },
        "timeframe": {
            "title": "Time frame",
            "help": "Available time to develop the application"
                     "(e.g. 2-3 days, 1 moth, etc.)",
            "type": "text",
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


def get_fields_data_from_prompt():
    """
    Returns the fields data for ideation from question (prompt)
    """
    fields_data = {
        "question": {
            "title": "Question / Prompt",
            "help": "App subject or question to generate the app idea",
            "type": "text",
        },
    }
    return fields_data


def get_buttons_config():
    """
    Returns the buttons configuration
    """
    buttons_config = [
        {
            "text": "Generate App Ideas",
            "key": "generate_app_ideas",
            "enable_config_name": "GENERATE_APP_IDEAS_ENABLED",
            "type": "submit",
        },
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
    ]
    return buttons_config


def get_buttons_config_for_prompt():
    """
    Returns the buttons configuration for ideation from question (prompt)
    """
    buttons_config = [
        {
            "text": "Generate App Ideas",
            "key": "generate_app_ideas_from_prompt",
            "enable_config_name": "GENERATE_APP_IDEAS_ENABLED",
        },
        {
            "text": "Generate App Names",
            "key": "generate_app_names_from_prompt",
            "enable_config_name": "GENERATE_APP_NAMES_ENABLED",
        },
        {
            "text": "Generate App Structure",
            "key": "generate_app_structure_from_prompt",
            "enable_config_name": "GENERATE_APP_STRUCTURE_ENABLED",
        },
        {
            "text": "Generate Presentation",
            "key": "generate_presentation_from_prompt",
            "enable_config_name": "GENERATE_PRESENTATION_ENABLED",
        },
        {
            "text": "Generate Video Script",
            "key": "generate_video_script_from_prompt",
            "enable_config_name": "GENERATE_VIDEO_SCRIPT_ENABLED",
        },
        # get_response_as_prompt_button_config(
        #     "use_response_as_prompt_app_ideation_tab"),
        # get_prompt_enhancement_button_config(
        #     "prompt_enhancement_app_ideation_tab"),
    ]
    return buttons_config


def get_ideation_form_config():
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


def get_ideation_from_prompt_config():
    """
    Returns the ideation from prompt configuration
    """
    form_config = {
        "title": "Application Ideation from Prompt",
        "name": "application_form_data_from_prompt",
        "subtitle": "This option will help you generate application idea from"
                    " the Question / Prompt",
        "suffix": "When you are ready, click one of the buttons below to"
                  " generate the application idea.",
        "fields": get_fields_data_from_prompt(),
        "buttons_config": get_buttons_config_for_prompt(),
        "features_data": get_features_data_from_prompt(),
        "form_session_state_key": "application_form_data_from_prompt",
        # "buttons_function": add_buttons_for_app_ideation_tab,
    }
    return form_config


def show_ideation_form(container: st.container):
    """
    Returns the ideation form
    """
    form_config = get_ideation_form_config()
    with container.expander("From Application Ideation Form"):
        form_result = cgsl.show_form(form_config)
    return form_result


def show_ideation_from_prompt(container: st.container, mode: str,
                              data: dict = None):
    """
    Returns the buttons for the ideation from the question (prompt)
    """
    if not data:
        data = {}
    form_config = get_ideation_from_prompt_config()
    form_session_state_key = form_config.get(
        "form_session_state_key")
    buttons_config = form_config.get("buttons_config")

    if mode == "show_form":
        with container.expander("From Prompt"):
            st.title(form_config.get("title", "Application Form"))
            if form_config.get("subtitle"):
                st.write(form_config.get("subtitle"))

            if form_config.get("suffix"):
                st.write(form_config.get("suffix"))
            cgsl.show_buttons_row(buttons_config)

    if mode == "process_form":
        buttons_submitted = data.get("buttons_submitted")
        buttons_submitted_data = cgsl.get_buttons_submitted_data(
            buttons_submitted, buttons_config, False)

        log_debug(f"show_ideation_from_prompt | data: {data}",
                  debug=DEBUG)
        log_debug(f"| buttons_config: {buttons_config}",
                  debug=DEBUG)
        log_debug(f"| buttons_submitted: {buttons_submitted}",
                  debug=DEBUG)
        log_debug(f"| buttons_submitted_data: {buttons_submitted_data}",
                  debug=DEBUG)

        if not buttons_submitted_data:
            return None
        fields_values = {
            "question": data.get("question"),
        }
        st.session_state[form_session_state_key] = dict(fields_values)
        st.session_state[form_session_state_key].update({
            "buttons_submitted_data": buttons_submitted_data
        })
        return st.session_state[form_session_state_key]
