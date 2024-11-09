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


def generate_json(result_container: st.container,
                  question: str = None):
    """
    Generates the JSON file and GS python code for Tools
    """
    if not question:
        question = st.session_state.question
    if not cgsl.validate_question(question):
        return

    with st.spinner("Procesing code generation..."):
        params = {
            "user_input_text": question,
        }
        json_generator = JsonGenerator(params=params)
        response = json_generator.generate_json()
        if response['error']:
            result_container.write(
                f"ERROR E-100: {response['error_message']}")
            return
        cgsl.save_conversation(
            type="text",
            question=question,
            refined_prompt=response.get('refined_prompt'),
            answer=response['response'],
        )
        # result_container.write(response['response'])
        st.rerun()


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

    tab1, tab2, tab3 = st.tabs(["Main", "App Ideation", "Code Generation"])

    # Suggestions
    with st.container():
        suggestion_container = st.empty()
        cgsl.show_suggestion_components(suggestion_container)

        # Show the siderbar selected conversarion's question and answer in the
        # main section
        # (must be done before the user input)
        for conversation in st.session_state.conversations:
            if st.session_state.get(conversation['id']):
                cgsl.show_conversation_question(conversation['id'])
                break

    # Models selection
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

    # Attachments
    with st.expander("Attachments"):
        st.file_uploader(
            "Choose file(s) to be attached to the conversation",
            accept_multiple_files=True,
            on_change=cgsl.attach_files,
            key="attach_files",
        )

    # User input
    with st.container():
        question = st.text_area(
            "Question / Prompt:",
            st.session_state.question)

    # Emoji shortcodes
    # https://streamlit-emoji-shortcodes-streamlit-app-gwckff.streamlit.app/

    # Buttons

    # Buttons line 1: Answer Questions, Generate Code, Generate Video,
    # Generate Image, Use Response as Prompt, Enhance prompt

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
            {
                "text": "Use Response as Prompt",
                "key": "use_response_as_prompt",
                "enable_config_name": "USE_RESPONSE_AS_PROMPT_ENABLED",
            },
            {
                "text": "",
                "type": "spacer",
            },
            # {
            #     "text": ":paperclip:",
            #     "key": "attach_files",
            #     "enable_config_name": "ATTACH_FILES_ENABLED",
            # },
            {
                "text": "Enhance prompt",
                "key": "prompt_enhancement",
                "type": "checkbox",
                "on_change": cgsl.prompt_enhancement,
            },
        ]
        cgsl.show_buttons_row(buttons_config)

        # Buttons line 2:
        # Generate App Names, Generate App Structure,
        # Start App Code, Generate Presentation

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
                "text": "Generate Config & Code",
                "key": "generate_code",
                "enable_config_name": "CODE_GENERATION_ENABLED",
            },
            {
                "text": "Start App Code",
                "key": "start_app_code",
                "enable_config_name": "START_APP_CODE_ENABLED",
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
        ]
        cgsl.show_buttons_row(buttons_config)

        # # Buttons line 3: Generate Video Script

        # buttons_config = [
        # ]
        # cgsl.show_buttons_row(buttons_config)

    # Results containers
    with st.container():
        additional_result_container = st.empty()
        result_container = st.empty()

    # Show the selected conversation's question and answer in the
    # main section
    with st.container():
        if "new_id" in st.session_state:
            cgsl.show_conversation_question(st.session_state.new_id)
            cgsl.show_conversation_content(
                st.session_state.new_id,
                result_container,
                additional_result_container)
            st.session_state.new_id = None

    # Sidebar
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

    # Check buttons pushed

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
        generate_json(result_container, question)

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
    page = st.query_params.get("page", cgsl.get_par_value("DEFAULT_PAGE",
                                                          "home"))

    # Page navigation logic
    if page == "home":
        page_1()
    elif page == "video_gallery":
        page_2()
    elif page == "image_gallery":
        page_3()
    else:
        page_1()


if __name__ == "__main__":
    main()
