"""
VitexBrain App
"""
from dotenv import load_dotenv
import streamlit as st

from lib.codegen_streamlit_lib import StreamlitLib, get_app_config

from src.codegen_schema_generator import JsonGenerator

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
            refined_prompt=response['refined_prompt'],
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
            cgsl.recycle_suggestions()

    # Main content

    # Title
    col = st.columns(
        2, gap="small",
        vertical_alignment="bottom")
    with col[0]:
        st.title(f"{st.session_state.app_name} {st.session_state.app_icon}")
    with col[1]:
        sub_col = st.columns(
            2, gap="small",
            vertical_alignment="bottom")
        col_index = 0
        if app_config.get("VIDEO_GENERATION_ENABLED", True):
            with sub_col[col_index]:
                st.button(
                    "Video Gallery",
                    on_click=cgsl.set_query_param,
                    args=("page", "video_gallery"))
            col_index += 1
        if app_config.get("IMAGE_GENERATION_ENABLED", True):
            with sub_col[col_index]:
                st.button(
                    "Image Gallery",
                    on_click=cgsl.set_query_param,
                    args=("page", "image_gallery"))

    # Suggestions
    suggestion_container = st.empty()
    cgsl.show_suggestion_components(suggestion_container)

    # Show the siderbar selected conversarion's question and answer in the
    # main section
    # (must be done before the user input)
    for conversation in st.session_state.conversations:
        if st.session_state.get(conversation['id']):
            cgsl.show_conversation_question(conversation['id'])
            break

    # User input
    question = st.text_area(
        "Question / Prompt:",
        st.session_state.question)

    # "generate_video" and "generate_text" Buttons
    col = st.columns(5)

    col_index = 0
    if app_config.get("CODE_GENERATION_ENABLED", False):
        with col[col_index]:
            # Generate code button
            col[col_index].button("Generate Code", key="generate_code")
        col_index += 1
    if app_config.get("TEXT_GENERATION_ENABLED", True):
        with col[col_index]:
            # Generate text button
            col[col_index].button("Answer Question", key="generate_text")
        col_index += 1
    if app_config.get("VIDEO_GENERATION_ENABLED", True):
        with col[col_index]:
            # Generate video button
            col[col_index].button("Generate Video", key="generate_video")
        col_index += 1
    if app_config.get("IMAGE_GENERATION_ENABLED", True):
        with col[col_index]:
            # Generate video button
            col[col_index].button("Generate Image", key="generate_image")
        col_index += 1
    with col[col_index]:
        # Enhance prompt checkbox
        col[col_index].checkbox(
            "Enhance prompt",
            key="prompt_enhancement",
            on_change=cgsl.prompt_enhancement)

    # Results containers
    additional_result_container = st.empty()
    result_container = st.empty()

    # Show the selected conversation's question and answer in the
    # main section
    if "new_id" in st.session_state:
        cgsl.show_conversation_question(st.session_state.new_id)
        cgsl.show_conversation_content(
            st.session_state.new_id,
            result_container,
            additional_result_container)
        st.session_state.new_id = None

    # Sidebar
    with st.sidebar:
        st.sidebar.write(
            f"**{st.session_state.app_name}** {app_config.get('APP_DESCRIPTION')}")

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
        page_title=st.session_state.app_name,
        page_icon=st.session_state.app_icon,
        layout="wide",
        initial_sidebar_state="auto",
    )

    # Query params to handle navigation
    page = st.query_params.get("page", app_config.get("DEFAULT_PAGE", "home"))

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
