"""
VitexBrain App
"""
import os
from dotenv import load_dotenv
import streamlit as st

from lib.codegen_streamlit_lib import StreamlitLib
from lib.codegen_utilities import get_app_config
from lib.codegen_utilities import log_debug

from lib.codegen_schema_generator import JsonGenerator
from lib.codegen_app_ideation_lib import (
    get_ideation_form_config,
    get_ideation_from_prompt_config,
)
from src.codegen_app_ideation import (
    show_ideation_form,
    show_ideation_from_prompt,
)
from src.codegen_buttons import (
    add_buttons_for_main_tab,
    add_buttons_for_code_gen_tab,
)

DEBUG = False

app_config = get_app_config()
cgsl = StreamlitLib(app_config)


# Code Generator specific


def process_json_and_code_generation(
    result_container: st.container,
    question: str = None
):
    """
    Generates the JSON file and GS python code for Tools
    """
    if not question:
        question = st.session_state.question
    if not cgsl.validate_question(question):
        return

    llm_text_model_elements = cgsl.get_llm_text_model()
    if llm_text_model_elements['error']:
        result_container.write(
            f"ERROR E-100-D: {llm_text_model_elements['error_message']}")
        return
    other_data = {
        "ai_provider": llm_text_model_elements['llm_provider'],
        "ai_model": llm_text_model_elements['llm_model'],
        "template": "json_and_code_generation",
    }

    with st.spinner("Procesing code generation..."):
        params = {
            "user_input_text": question,
            "use_embeddings": st.session_state.use_embeddings_flag,
            "embeddings_sources_dir": cgsl.get_par_value(
                "EMBEDDINGS_SOURCES_DIR", "./embeddings_sources"),
            "provider": llm_text_model_elements['llm_provider'],
            "model": llm_text_model_elements['llm_model'],
        }
        json_generator = JsonGenerator(params=params)
        response = json_generator.generate_json()
        if response['error']:
            other_data["error_message"] = (
                f"ERROR E-100: {response['error_message']}")
        other_data.update(response.get('other_data', {}))
        cgsl.save_conversation(
            type="text",
            question=question,
            refined_prompt=response.get('refined_prompt'),
            answer=response.get(
                'response',
                "No response. Check the Detailed Response section."),
            other_data=other_data,
        )
        # result_container.write(response['response'])
        st.rerun()


def process_use_response_as_prompt():
    """
    Process the use_response_as_prompt button pushed
    """
    if st.session_state.use_response_as_prompt_flag:
        if "last_retrieved_conversation" in st.session_state:
            conversation = dict(st.session_state.last_retrieved_conversation)
            st.session_state.question = conversation['answer']
    st.session_state.use_response_as_prompt_flag = False


def process_ideation_form(form: dict, form_config: dict):
    """
    Process the ideation form
    """
    result_container = st.container()
    features_data = form_config.get("features_data", {})
    fields_data = form_config.get("fields", {})

    log_debug("process_ideation_form | form: " + f"{form}", debug=DEBUG)
    log_debug("process_ideation_form | form_config: " + f"{features_data}",
              debug=DEBUG)

    # Validates the submitted form
    if not form:
        cgsl.show_form_error("No data received from the form")
        return
    if not form.get("buttons_submitted_data"):
        cgsl.show_form_error("Missing buttons submitted data")
        return

    # Verify button pressed
    selected_feature = cgsl.get_selected_feature(form, features_data)
    if not selected_feature:
        cgsl.show_form_error("No button pressed... try again please")
        return

    # Verify mandatory field
    error_message = ""
    for key in features_data.get(selected_feature).get("mandatory_fields"):
        if not form.get(key):
            field_name = fields_data.get(key, {}).get("title", key)
            error_message += f"{field_name}, "
    if error_message:
        error_message = error_message[:-2]
        cgsl.show_form_error(f"Missing field(s): {error_message}")
        return

    template = features_data.get(selected_feature).get("template")
    if not template:
        cgsl.show_form_error("Missing template")
        return

    system_prompt_template = features_data.get(selected_feature) \
        .get("system_prompt")
    if not system_prompt_template:
        cgsl.show_form_error("Missing system prompt")
        return

    # Read the template file
    template_path = f"./config/{template}"
    if not os.path.exists(template_path):
        cgsl.show_form_error(f"Missing template file: {template_path}")
        return
    with open(template_path, "r") as f:
        question = f.read()

    # Read the system prompt file
    system_prompt_path = f"./config/{system_prompt_template}"
    if not os.path.exists(system_prompt_path):
        cgsl.show_form_error(
            f"Missing system prompt file: {system_prompt_path}")
        return
    with open(system_prompt_path, "r") as f:
        system_prompt = f.read()

    # Default values
    if "timeframe" not in form:
        form["timeframe"] = cgsl.get_par_value("IDEATION_DEFAULT_TIMEFRAME")
    if "quantity" not in form:
        form["quantity"] = cgsl.get_par_value("IDEATION_DEFAULT_QTY")

    # Replace the placeholders with the user input
    final_form = {}
    for key in form:
        if key in [
            "screenshots",
            "buttons_submitted_data",
            "buttons_submitted"
        ]:
            continue
        log_debug(f"process_ideation_form | key: {key} | "
                  f"form[key]: {form[key]}", debug=DEBUG)
        final_form[key] = form[key]
        if form[key]:
            question = question.replace(f"{{{key}}}", form[key])

    form_name = cgsl.get_form_name(form_config)
    form_session_state_key = cgsl.get_form_session_state_key(form_config)
    other_data = {
        "subtype": selected_feature,
        "template": template,
        "system_prompt": system_prompt,
        "form_name": form_name,
        "form_data": final_form,
        "form_session_state_key": form_session_state_key,
    }

    log_debug("process_ideation_form | question: " + f"{question}"
              "\n | other_data: " + f"{other_data}",
              debug=DEBUG)

    # Call the LLM to generate the ideation
    response = cgsl.text_generation(result_container, question, other_data,
                                    {"assign_global": False})

    log_debug("process_ideation_form | response: " + f"{response}",
              debug=DEBUG)

    error_message = None
    if response['error']:
        error_message = f"ERROR E-900-B: {response['error_message']}"
        cgsl.show_form_error(error_message)

    cgsl.save_conversation(
        type="text",
        question=question,
        refined_prompt=response.get('refined_prompt'),
        answer=response.get(
            'response',
            "No response. Check the Detailed Response section."),
        other_data=other_data,
    )

    # Restore the original question if App Ideation from prompt was used
    # original_question = other_data.get("form_data", {}).get("question")
    # if original_question:
    #     st.session_state.question = original_question

    st.rerun()


# UI elements


def get_question_label(tab: str = "main"):
    """
    Returns the question label based on the tab
    """
    label = "Question / Prompt:"
    if tab == "app_ideation" or tab == "code_gen":
        label = "App description:"
    st.session_state.question_label = label
    return label


def add_title():
    """
    Add the title section to the page
    """

    # Emoji shortcodes
    # https://streamlit-emoji-shortcodes-streamlit-app-gwckff.streamlit.app/

    with st.container():
        col = st.columns(
            2, gap="small",
            vertical_alignment="bottom")
        with col[0]:
            st.title(cgsl.get_title())
        with col[1]:
            sub_col = st.columns(
                2, gap="small",
                vertical_alignment="bottom")
            col_index = 0
            if cgsl.get_par_value("VIDEO_GENERATION_ENABLED", True):
                with sub_col[col_index]:
                    st.button(
                        "Video Gallery",
                        on_click=cgsl.set_query_param,
                        args=("page", "video_gallery"))
                col_index += 1
            if cgsl.get_par_value("IMAGE_GENERATION_ENABLED", True):
                with sub_col[col_index]:
                    st.button(
                        "Image Gallery",
                        on_click=cgsl.set_query_param,
                        args=("page", "image_gallery"))


def add_suggestions():
    """
    Add the suggestions section to the page
    """
    suggestion_container = st.empty()
    cgsl.show_suggestion_components(suggestion_container)

    # Show the siderbar selected conversation's question and answer in the
    # main section
    # (must be done before the user input)
    for conversation in st.session_state.conversations:
        if st.session_state.get(conversation['id']):
            cgsl.show_conversation_question(conversation['id'])
            break


def add_models_selection():
    """
    Add the models selection to the page
    """
    # available_llm_providers = cgsl.get_par_value("LLM_PROVIDERS")
    available_llm_providers = cgsl.get_available_ai_providers("LLM_PROVIDERS")
    llm_provider_index = cgsl.get_llm_provider_index(
        "LLM_PROVIDERS",
        "llm_provider")
    llm_model_index = cgsl.get_llm_model_index(
        "LLM_PROVIDERS", "llm_provider",
        "LLM_AVAILABLE_MODELS", "llm_model")

    # available_image_providers = cgsl.get_par_value("TEXT_TO_IMAGE_PROVIDERS")
    available_image_providers = cgsl.get_available_ai_providers(
        "TEXT_TO_IMAGE_PROVIDERS")
    image_provider_index = cgsl.get_llm_provider_index(
        "TEXT_TO_IMAGE_PROVIDERS",
        "image_provider")
    image_model_index = cgsl.get_llm_model_index(
        "TEXT_TO_IMAGE_PROVIDERS", "image_provider",
        "TEXT_TO_IMAGE_AVAILABLE_MODELS", "image_model")

    # available_video_providers = cgsl.get_par_value("TEXT_TO_VIDEO_PROVIDERS")
    available_video_providers = cgsl.get_available_ai_providers(
        "TEXT_TO_VIDEO_PROVIDERS")
    video_provider_index = cgsl.get_llm_provider_index(
        "TEXT_TO_VIDEO_PROVIDERS",
        "video_provider")
    video_model_index = cgsl.get_llm_model_index(
        "TEXT_TO_VIDEO_PROVIDERS", "video_provider",
        "TEXT_TO_VIDEO_AVAILABLE_MODELS", "video_model")

    # log_debug("image_provider_index: " + f"{image_provider_index}",
    #           debug=DEBUG)
    # log_debug("image_model_index: " + f"{image_model_index}", debug=DEBUG)
    # log_debug("video_provider_index: " + f"{video_provider_index}",
    #           debug=DEBUG)

    with st.expander("Models Selection"):
        # LLM Provider and Model
        col = st.columns(2, gap="small", vertical_alignment="bottom")
        with col[0]:
            st.selectbox(
                "LLM Provider",
                available_llm_providers,
                key="llm_provider",
                index=llm_provider_index,
                help="Select the provider to use for the LLM call")
        with col[1]:
            st.selectbox(
                "LLM Model",
                cgsl.get_model_options(
                    "LLM_PROVIDERS",
                    "llm_provider",
                    "LLM_AVAILABLE_MODELS"
                ),
                key="llm_model",
                index=llm_model_index,
                help="Select the model to use for the LLM call")

        # Image Provider and Model
        col = st.columns(2, gap="small", vertical_alignment="bottom")
        with col[0]:
            st.selectbox(
                "Text-to-Image Provider",
                available_image_providers,
                key="image_provider",
                index=image_provider_index,
                help="Select the provider to use for the text-to-image call")
        with col[1]:
            st.selectbox(
                "Text-to-Image Model",
                cgsl.get_model_options(
                    "TEXT_TO_IMAGE_PROVIDERS",
                    "image_provider",
                    "TEXT_TO_IMAGE_AVAILABLE_MODELS",
                ),
                key="image_model",
                index=image_model_index,
                help="Select the model to use for the text-to-image call")

        # Video Provider and Model
        col = st.columns(2, gap="small", vertical_alignment="bottom")
        with col[0]:
            st.selectbox(
                "Text-to-Video Provider",
                available_video_providers,
                key="video_provider",
                index=video_provider_index,
                help="Select the provider to use for the text-to-video call")
        with col[1]:
            st.selectbox(
                "Text-to-Video Model",
                cgsl.get_model_options(
                    "TEXT_TO_VIDEO_PROVIDERS",
                    "video_provider",
                    "TEXT_TO_VIDEO_AVAILABLE_MODELS",
                ),
                key="video_model",
                index=video_model_index,
                help="Select the model to use for the text-to-video call")

    with st.expander("Model configuration (advanced)"):
        # Temperature slider | default: 1.00
        col = st.columns(4, gap="small", vertical_alignment="bottom")
        with col[0]:
            st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=0.5,
                step=0.01,
                key="model_config_par_temperature",
                help="Controls the randomness of the output. Lower values make"
                     " the output more deterministic.",
            )

        # Max tokens slider | default: 2048
        col = st.columns(4, gap="small", vertical_alignment="bottom")
        with col[0]:
            st.slider(
                "Max Tokens",
                min_value=0,
                max_value=4095,
                value=2048,
                step=1,
                key="model_config_par_max_tokens",
                help="The maximum number of tokens to generate.",
            )

        # Top P slider | default: 1.00
        col = st.columns(4, gap="small", vertical_alignment="bottom")
        with col[0]:
            st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=1.0,
                step=0.01,
                key="model_config_par_top_p",
                help="The cumulative probability of the top tokens to"
                     " generate.",
            )

        # Frequency penalty slider | default: 0.00
        col = st.columns(4, gap="small", vertical_alignment="bottom")
        with col[0]:
            st.slider(
                "Frequency Penalty",
                min_value=0.0,
                max_value=2.0,
                value=0.0,
                step=0.01,
                key="model_config_par_frequency_penalty",
                help="The higher the value, the more diverse the output.",
            )

        # Presence penalty slider | default: 0.00
        col = st.columns(4, gap="small", vertical_alignment="bottom")
        with col[0]:
            st.slider(
                "Presence Penalty",
                min_value=0.0,
                max_value=2.0,
                value=0.0,
                step=0.01,
                key="model_config_par_presence_penalty",
                help="The higher the value, the more diverse the output.",
            )


def add_attachments():
    """
    Add the attachments section to the page
    """
    if not cgsl.get_par_value("ADD_ATTACHMENTS_ENABLED", False):
        return
    with st.expander("Attachments"):
        st.file_uploader(
            "Choose file(s) to be attached to the conversation",
            accept_multiple_files=True,
            on_change=cgsl.attach_files,
            key="attach_files",
        )


def add_user_input():
    """
    Add the user input section to the page and return the question object
    """
    with st.container():
        question = st.text_area(
            st.session_state.question_label,
            st.session_state.question)
    return question


def add_results_containers():
    """
    Add the results containers to the page
    """
    with st.container():
        additional_result_container = st.empty()
        result_container = st.empty()
    return additional_result_container, result_container


def add_show_selected_conversation(
        result_container: st.container,
        additional_result_container: st.container):
    """
    Show the selected conversation's question and answer in the
    main section
    """
    if "new_id" not in st.session_state:
        return
    with st.container():
        cgsl.show_conversation_question(st.session_state.new_id)
        cgsl.show_conversation_content(
            st.session_state.new_id,
            result_container,
            additional_result_container)
        st.session_state.new_id = None


def add_sidebar():
    """
    Add the sidebar to the page and return the data management container
    """
    with st.sidebar:
        app_desc = cgsl.get_par_value("APP_DESCRIPTION")
        app_desc = app_desc.replace(
            "{app_name}",
            f"**{st.session_state.app_name}**")
        st.sidebar.write(app_desc)

        cgsl.data_management_components()
        data_management_container = st.empty()

        # Show the conversations in the side bar
        cgsl.show_conversations()
    return data_management_container


def add_check_buttons_pushed(
        result_container: st.container,
        additional_result_container: st.container,
        data_management_container: st.container,
        parameters_container: st.container,
        question: str):
    """
    Check buttons pushed
    """

    # Process the generate_video button pushed
    if st.session_state.get("generate_video"):
        cgsl.video_generation(result_container, question)

    # Process the generate_image button pushed
    if st.session_state.get("generate_image"):
        cgsl.image_generation(result_container, question)

    # Process the generate_text button pushed
    if st.session_state.get("generate_text"):
        cgsl.text_generation(result_container, question)

    # Process the generate_code button pushed
    if st.session_state.get("generate_code"):
        process_json_and_code_generation(result_container, question)

    # Show the selected conversation's question and answer in the
    # main section
    for conversation in st.session_state.conversations:
        if st.session_state.get(conversation['id']):
            cgsl.show_conversation_content(
                conversation['id'], result_container,
                additional_result_container)
            break

    # Perform data management operations
    if st.session_state.get("import_data"):
        cgsl.import_data(data_management_container)

    if st.session_state.get("export_data"):
        cgsl.export_data(data_management_container)

    if "dm_results" in st.session_state and st.session_state.dm_results:
        cgsl.success_message(
            "Operation result:\n\n" +
            f"{cgsl.format_results(st.session_state.dm_results)}",
            container=data_management_container)
        st.session_state.dm_results = None

    # Process the ideation-from-prompt buttons
    cgsl.process_no_form_buttons(
        "ideation_from_prompt", question,
        show_ideation_from_prompt, process_ideation_form)


def add_footer():
    """
    Add the footer to the page
    """
    st.caption(f"© 2024 {st.session_state.maker_name}. All rights reserved.")


# Pages


def page_1():
    # Get suggested questions initial value
    with st.spinner("Loading App..."):
        if "suggestion" not in st.session_state:
            if cgsl.get_par_value("DYNAMIC_SUGGESTIONS", True):
                cgsl.recycle_suggestions()
            else:
                st.session_state.suggestion = \
                    cgsl.get_par_value("DEFAULT_SUGGESTIONS")

    # Main content

    # Title
    add_title()

    # Suggestions
    add_suggestions()

    # Models selection
    add_models_selection()

    # Attachments
    add_attachments()

    # Process the use_response_as_prompt button pushed
    process_use_response_as_prompt()

    # User input
    question = add_user_input()

    # Additional parameters SECTION
    _, parameters_container = add_results_containers()

    # Tabs defintion
    tab1, tab2, tab3 = st.tabs(["Main", "App Ideation", "Code Generation"])

    # When a tab is changed, reset the question label
    # tab1.on_change("active", lambda: get_question_label("main"))
    # tab2.on_change("active", lambda: get_question_label("app_ideation"))
    # tab3.on_change("active", lambda: get_question_label("code_gen"))

    with tab1:
        # Buttons
        add_buttons_for_main_tab()

    with tab2:
        # Idea from Form
        form = show_ideation_form(tab2)
        if form:
            process_ideation_form(form, get_ideation_form_config())

        # Idea from Prompt
        st.session_state.forms_config["ideation_from_prompt"] = \
            get_ideation_from_prompt_config()
        show_ideation_from_prompt(tab2, "show_form")

    with tab3:
        # Buttons
        add_buttons_for_code_gen_tab()

    # Results containers
    additional_result_container, result_container = add_results_containers()

    # Show the selected conversation's question and answer in the
    # main section
    add_show_selected_conversation(
        result_container,
        additional_result_container)

    # Sidebar
    data_management_container = add_sidebar()

    # Check buttons pushed
    add_check_buttons_pushed(
        result_container,
        additional_result_container,
        data_management_container,
        parameters_container,
        question,
    )

    # Footer
    with st.container():
        add_footer()


# Page 2: Video Gallery
def page_2():
    cgsl.show_gallery("video")
    # Footer
    add_footer()


# Page 3: Image Gallery
def page_3():
    cgsl.show_gallery("image")
    # Footer
    add_footer()


# Main


# Main function to render pages
def main():
    load_dotenv()

    st.session_state.app_name = cgsl.get_par_or_env("APP_NAME")
    st.session_state.app_version = cgsl.get_par_or_env("APP_VERSION")
    st.session_state.app_name_version = \
        f"{st.session_state.app_name} v{st.session_state.app_version}"
    st.session_state.maker_name = cgsl.get_par_or_env("MAKER_MAME")
    st.session_state.app_icon = cgsl.get_par_or_env("APP_ICON", ":sparkles:")

    if "question" not in st.session_state:
        st.session_state.question = ""
    if "prompt_enhancement_flag" not in st.session_state:
        st.session_state.prompt_enhancement_flag = False
    if "use_response_as_prompt_flag" not in st.session_state:
        st.session_state.use_response_as_prompt_flag = False
    if "use_embeddings_flag" not in st.session_state:
        st.session_state.use_embeddings_flag = True
    if "conversations" not in st.session_state:
        cgsl.update_conversations()
    if "question_label" not in st.session_state:
        get_question_label()
    if "forms_config" not in st.session_state:
        st.session_state.forms_config = {}

    # Streamlit app code
    st.set_page_config(
        page_title=st.session_state.app_name_version,
        page_icon=st.session_state.app_icon,
        layout="wide",
        initial_sidebar_state="auto",
    )

    # Query params to handle navigation
    page = st.query_params.get("page", cgsl.get_par_value("DEFAULT_PAGE"))

    # Page navigation logic
    if page == "video_gallery":
        page_2()
    elif page == "image_gallery":
        page_3()
    # if page == "home":
    #     page_1()
    else:
        # Defaults to home
        page_1()


if __name__ == "__main__":
    main()
