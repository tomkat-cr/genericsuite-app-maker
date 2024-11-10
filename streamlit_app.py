"""
VitexBrain App
"""
from dotenv import load_dotenv
import streamlit as st

from lib.codegen_streamlit_lib import StreamlitLib
from lib.codegen_utilities import get_app_config
# from lib.codegen_utilities import log_debug

from src.codegen_schema_generator import JsonGenerator


DEBUG = True

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
            answer=response.get('response',
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


# UI elements

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

    # Show the siderbar selected conversarion's question and answer in the
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
    available_llm_providers = cgsl.get_par_value("LLM_PROVIDERS")
    llm_provider_index = cgsl.get_llm_provider_index(
        "LLM_PROVIDERS",
        "llm_provider")
    llm_model_index = cgsl.get_llm_model_index(
        "LLM_PROVIDERS", "llm_provider",
        "LLM_AVAILABLE_MODELS", "llm_model")

    available_image_providers = cgsl.get_par_value("TEXT_TO_IMAGE_PROVIDERS")
    image_provider_index = cgsl.get_llm_provider_index(
        "TEXT_TO_IMAGE_PROVIDERS",
        "image_provider")
    image_model_index = cgsl.get_llm_model_index(
        "TEXT_TO_IMAGE_PROVIDERS", "image_provider",
        "TEXT_TO_IMAGE_AVAILABLE_MODELS", "image_model")

    available_video_providers = cgsl.get_par_value("TEXT_TO_VIDEO_PROVIDERS")
    video_provider_index = cgsl.get_llm_provider_index(
        "TEXT_TO_VIDEO_PROVIDERS",
        "video_provider")
    video_model_index = cgsl.get_llm_model_index(
        "TEXT_TO_VIDEO_PROVIDERS", "video_provider",
        "TEXT_TO_VIDEO_AVAILABLE_MODELS", "video_model")

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


def add_attachments():
    """
    Add the attachments section to the page
    """
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
            "Question / Prompt:",
            st.session_state.question)
    return question


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


def add_buttons_for_app_ideation_tab():
    """
    Add the app ideation tab buttons section to the page
    """

    with st.container():
        buttons_config = [
            {
                "text": "Generate App Names",
                "key": "generate_app_names",
                "enable_config_name": "GENERATE_APP_NAMES_ENABLED",
            },
            {
                "text": "Generate App Structure",
                "key": "generate_app_structure",
                "enable_config_name": "GENERATE_APP_STRUCTURE_ENABLED",
            },
            {
                "text": "Generate Presentation",
                "key": "generate_presentation",
                "enable_config_name": "GENERATE_PRESENTATION_ENABLED",
            },
            {
                "text": "Generate Video Script",
                "key": "generate_video_script",
                "enable_config_name": "GENERATE_VIDEO_SCRIPT_ENABLED",
            },
            get_response_as_prompt_button_config(
                "use_response_as_prompt_app_ideation_tab"),
            get_prompt_enhancement_button_config(
                "prompt_enhancement_app_ideation_tab"),
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


def add_footer():
    """
    Add the footer to the page
    """
    st.caption(f"© 2024 {st.session_state.maker_name}. All rights reserved.")


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

    # Tabs defintion
    tab1, tab2, tab3 = st.tabs(["Main", "App Ideation", "Code Generation"])

    with tab1:
        # Buttons
        add_buttons_for_main_tab()

    with tab2:
        # Buttons
        add_buttons_for_app_ideation_tab()

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
        question
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
