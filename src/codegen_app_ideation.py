import streamlit as st

from lib.codegen_streamlit_lib import StreamlitLib
from lib.codegen_utilities import get_app_config, log_debug
from lib.codegen_app_ideation_lib import (
    get_ideation_form_config,
    get_ideation_from_prompt_config,
)

DEBUG = False

app_config = get_app_config()
cgsl = StreamlitLib(app_config)


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
