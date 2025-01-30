"""
Streamlit UI library
"""
from typing import Any, Callable
import os
import time
import json
import uuid
import html

import streamlit as st

from lib.codegen_utilities import (
    log_debug,
    get_date_time,
    get_new_item_id,
    get_default_resultset,
    read_file,
    is_an_url,
    path_exists,
)
from lib.codegen_db import CodegenDatabase
from lib.codegen_ai_utilities import (
    TextToVideoProvider,
    LlmProvider,
    ImageGenProvider,
)
from lib.codegen_powerpoint import PowerPointGenerator


DEBUG = False


@st.dialog("Form validation")
def show_popup(title: str, message: str, msg_type: str = "success"):
    """
    Show a streamlit popup with a message
    """
    message = message.replace("\n", "<br>")
    message = message.replace("\r", "<br>")
    st.header(f"{title}")
    if msg_type == "success":
        st.success(message)
    elif msg_type == "error":
        st.error(message)
    elif msg_type == "info":
        st.info(message)
    elif msg_type == "warning":
        st.warning(message)


class StreamlitLib:
    """
    Streamlit UI library
    """
    def __init__(self, params: dict):
        self.params = params

    # General utilities and functions

    def set_new_id(self, id: str = None):
        """
        Set the new id global variable
        """
        # if "new_id" not in st.session_state:
        #     st.session_state.new_id = None
        st.session_state.new_id = id

    def get_new_id(self):
        """
        Get the new id global variable
        """
        if "new_id" in st.session_state:
            return st.session_state.new_id
        else:
            return "No new_id"

    def set_query_param(self, name, value):
        """
        Set a URL query parameter
        """
        st.query_params[name] = value

    def timer_message(
        self, message: str, type: str,
        container: st.container = None,
        seconds: int = 10
    ):
        """
        Start a timer
        """
        if not container:
            container = st.empty()
        if type == "info":
            alert = container.info(message)
        elif type == "warning":
            alert = container.warning(message)
        elif type == "success":
            alert = container.success(message)
        elif type == "error":
            alert = container.error(message)
        else:
            raise ValueError(f"Invalid type: {type}")
        time.sleep(seconds)
        # Clear the alert
        alert.empty()

    def success_message(self, message: str, container: st.container = None):
        """
        Display a success message
        """
        self.timer_message(message, "success", container)

    def error_message(self, message: str, container: st.container = None):
        """
        Display an error message
        """
        self.timer_message(message, "error", container)

    def info_message(self, message: str, container: st.container = None):
        """
        Display an info message
        """
        self.timer_message(message, "info", container)

    def warning_message(self, message: str, container: st.container = None):
        """
        Display a warning message
        """
        self.timer_message(message, "warning", container)

    # Conversations database

    def init_db(self):
        """
        Initialize the JSON file database
        """
        db_type = os.getenv('DB_TYPE')
        db = None
        if db_type == 'json':
            db = CodegenDatabase("json", {
                "JSON_DB_PATH": os.getenv(
                    'JSON_DB_PATH',
                    self.get_par_value("CONVERSATION_DB_PATH")
                ),
            })
        if db_type == 'mongodb':
            db = CodegenDatabase("mongodb", {
                "MONGODB_URI": os.getenv('MONGODB_URI'),
                "MONGODB_DB_NAME": os.getenv('MONGODB_DB_NAME'),
                "MONGODB_COLLECTION_NAME": os.getenv('MONGODB_COLLECTION_NAME')
            })
        if not db:
            raise ValueError(f"Invalid DB_TYPE: {db_type}")
        return db

    def update_conversations(self):
        """
        Update the side bar conversations from the database
        """
        st.session_state.conversations = self.get_conversations()

    def update_conversation(
        self,
        item: dict = None,
        id: str = None
    ):
        db = self.init_db()
        log_debug(f"UPDATE_CONVERSATION | id: {id} | item: {item}",
                  debug=DEBUG)
        db.save_item(item, id)
        self.set_new_id(id)

    def save_conversation(
        self, type: str,
        question: str,
        answer: str,
        title: str = None,
        refined_prompt: str = None,
        other_data: dict = None,
        id: str = None
    ):
        """
        Save the conversation in the database
        """
        if not id:
            id = get_new_item_id()
        if not title:
            title = self.generate_title_from_question(question)
            title = title[:self.get_title_max_length()]
        db = self.init_db()
        item = {
            "type": type,
            "title": title,
            "question": question,
            "answer": answer,
            "refined_prompt": refined_prompt,
            "timestamp": time.time(),
        }
        if not other_data:
            other_data = {}
        item.update(other_data)
        db.save_item(item, id)
        self.update_conversations()
        self.recycle_suggestions()
        self.set_new_id(id)
        return id

    def get_conversations(self):
        """
        Returns the conversations in the database
        """
        db = self.init_db()
        conversations = db.get_list("timestamp", "desc")
        # Add the date_time field to each conversation
        for conversation in conversations:
            conversation['date_time'] = get_date_time(
                conversation['timestamp'])
        return conversations

    def get_conversation(self, id: str):
        """
        Returns the conversation in the database
        """
        db = self.init_db()
        conversation = db.get_item(id)
        if conversation:
            # Add the date_time field to the conversation
            conversation['date_time'] = get_date_time(
                conversation['timestamp'])
            return conversation
        return None

    def delete_conversation(self, id: str):
        """
        Delete a conversation from the database
        """
        db = self.init_db()
        db.delete_item(id)
        self.update_conversations()

    # Prompt suggestions

    def reset_suggestions_prompt(self):
        """
        Reset the suggestions prompt
        """
        prompt = self.get_par_value("SUGGESTIONS_PROMPT_TEXT")
        prompt = prompt.format(
            timeframe=self.get_par_value("SUGGESTIONS_DEFAULT_TIMEFRAME"),
            app_type=self.get_par_value("SUGGESTIONS_DEFAULT_APP_TYPE"),
            app_subject=self.get_par_value("SUGGESTIONS_DEFAULT_APP_SUBJECT"),
            qty=self.get_par_value("SUGGESTIONS_QTY", 4),
        )
        st.session_state.suggestions_prompt_text = prompt

    def get_suggestions_from_ai(self, system_prompt: str, user_prompt: str
                                ) -> dict:
        """
        Get suggestions from the AI
        """
        # The model replacement for suggestions is to avoid use reasoning
        # models like o1-preview/o1-mini because they are expensive and
        # slow, and replace them with a less expensive model like GPT-4o-mini.
        model_replacement = self.get_par_value("SUGGESTIONS_MODEL_REPLACEMENT")
        llm_text_model = self.get_llm_text_model(model_replacement)
        if llm_text_model['error']:
            log_debug("get_suggestions_from_ai | llm_text_model "
                      f"ERROR: {llm_text_model}", debug=DEBUG)
            return llm_text_model
        # Get the model class
        llm_model = llm_text_model['class']
        # Get the suggestions from the AI
        llm_response = llm_model.query(system_prompt, user_prompt)
        log_debug("get_suggestions_from_ai | " +
                  f"response: {llm_response}", debug=DEBUG)
        if llm_response['error']:
            log_debug("get_suggestions_from_ai | llm_response "
                      f"ERROR: {llm_response}", debug=DEBUG)
            return llm_response
        # Clean the suggestions response
        suggestions = llm_response['response']
        suggestions = suggestions.replace("\n", "")
        suggestions = suggestions.replace("\r", "")
        suggestions = suggestions.replace("Suggestions:", "")
        suggestions = suggestions.strip()
        suggestions = suggestions.replace('```json', '')
        suggestions = suggestions.replace('```', '')
        suggestions = suggestions.replace("\\'", '')
        # Load the suggestions
        try:
            suggestions = json.loads(suggestions)
            log_debug("get_suggestions_from_ai | FINAL suggestions:"
                      f" {suggestions}", debug=DEBUG)
        except Exception as e:
            log_debug(f"get_suggestions_from_ai | ERROR {e}", debug=DEBUG)
            return self.get_par_value("DEFAULT_SUGGESTIONS")
        return suggestions

    def recycle_suggestions(self):
        """
        Recycle the suggestions from the AI
        """
        system_prompt = self.get_par_value("SUGGESTIONS_PROMPT_SYSTEM")
        # Prepare user prompt from the input text in the main form
        user_prompt = st.session_state.suggestions_prompt_text + \
            "\n\n" + self.get_par_value("SUGGESTIONS_PROMPT_SUFFIX")
        # Add the suggestion quantity
        user_prompt = user_prompt.replace(
            "{qty}",
            str(self.get_par_value("SUGGESTIONS_QTY", 4)))
        # Add the timeframe
        user_prompt = user_prompt.replace(
            "{timeframe}", str(self.get_par_value(
                "SUGGESTIONS_DEFAULT_TIMEFRAME", "48 hours")))
        # Get the suggestions from the selected LLM text model
        st.session_state.suggestion = self.get_suggestions_from_ai(
            system_prompt, user_prompt)

    def show_one_suggestion(self, suggestion: Any):
        """
        Show one suggestion in the main section
        """
        response = ""
        if suggestion:
            if isinstance(suggestion, dict):
                if "title" in suggestion:
                    response += suggestion.get("title") + "\n"
                if "description" in suggestion:
                    response += suggestion.get("description")
            else:
                response = suggestion
        if not response:
            response = "N/A"
        return response

    def show_suggestion_components(self, container: st.container):
        """
        Show the suggestion components in the main section
        """
        if "suggestions_prompt_text" not in st.session_state:
            self.reset_suggestions_prompt()

        if st.session_state.get("generate_suggestions"):
            with st.spinner("Generating suggestions..."):
                self.recycle_suggestions()

        if st.session_state.get("reset_suggestions_prompt"):
            self.reset_suggestions_prompt()

        if st.session_state.get("recycle_suggestions"):
            log_debug("RECYCLE_SUGGESTIONS | Recycling suggestions",
                      debug=DEBUG)
            if self.get_par_value("DYNAMIC_SUGGESTIONS", True):
                with st.spinner("Refreshing suggestions..."):
                    self.recycle_suggestions()
            elif not st.session_state.get("suggestion"):
                st.session_state.suggestion = \
                    self.get_par_value("DEFAULT_SUGGESTIONS")

        if not isinstance(st.session_state.suggestion, dict):
            st.session_state.suggestion = \
                self.get_par_value("DEFAULT_SUGGESTIONS")

        # Show the 4 suggestions in the main section
        if "error" in st.session_state.suggestion:
            with st.expander("ERROR loading suggestions..."):
                st.write(st.session_state.suggestion["error_message"])
        else:
            sug_col1, sug_col2, sug_col3 = st.columns(
                3, gap="small",
            )
            max_length = self.get_title_max_length()
            for i in range(self.get_par_value("SUGGESTIONS_QTY")):
                suggestion = self.show_one_suggestion(
                    st.session_state.suggestion.get(
                        f"s{i+1}"))
                suggestion = suggestion[:max_length] + "..." \
                    if len(suggestion) > max_length else suggestion
                if i % 2 != 0:
                    with sug_col1:
                        sug_col1.button(suggestion, key=f"s{i+1}")
                else:
                    with sug_col2:
                        sug_col2.button(suggestion, key=f"s{i+1}")
            with sug_col3:
                if self.get_par_value("DYNAMIC_SUGGESTIONS", True):
                    sug_col3.button(
                        ":recycle:",
                        key="recycle_suggestions",
                        help="Recycle suggestions buttons",
                    )
                with st.expander("Suggestions Prompt"):
                    st.session_state.suggestions_prompt_text = st.text_area(
                        "Prompt:",
                        st.session_state.suggestions_prompt_text,
                    )
                    st.button(
                        "Generate Suggestions",
                        key="generate_suggestions",
                    )
                    st.button(
                        "Reset Prompt",
                        key="reset_suggestions_prompt",
                    )

        # Process the suggestion button pushed
        # (must be done before the user input)
        for key in st.session_state.suggestion.keys():
            if st.session_state.get(key):
                st.session_state.question = \
                    self.show_one_suggestion(st.session_state.suggestion[key])
                break

    # Conversation titles

    def get_title_max_length(self):
        return self.get_par_value("CONVERSATION_TITLE_LENGTH", 100)

    def get_title_from_question(self, question: str) -> str:
        """
        Returns the title from the question
        """
        title = question
        title = title.replace("```json", "")
        title = title.replace("```", "")
        title = title.replace("\t", " ")
        title = title.replace("\n", " ")
        title = title.replace("\r", " ")
        title = title.strip()
        return title

    def get_conversation_title(self, conversation: dict):
        return conversation.get(
            "title",
            self.get_title_from_question(conversation['question'])
        )

    def generate_title_from_question(self, question: str) -> str:
        """
        Returns the title from the question
        """
        default_title = self.get_title_from_question(question)
        title_length = self.get_title_max_length()
        # Use small models for title generation
        model_replacement = self.get_par_value("SUGGESTIONS_MODEL_REPLACEMENT")
        llm_text_model = self.get_llm_text_model(model_replacement)
        if llm_text_model['error']:
            log_debug("generate_title_from_question | llm_text_model "
                      f"ERROR: {llm_text_model}", debug=DEBUG)
            return default_title
        llm_model = llm_text_model['class']
        # Prepare the prompt
        prompt = "Give me a title for this question " \
                 f"(max length: {title_length*2}): {question}"
        # Get the title from the AI
        llm_response = llm_model.query(prompt, "", unified=True)
        log_debug("GENERATE_TITLE_FROM_QUESTION | " +
                  f"response: {llm_response}", debug=DEBUG)
        if llm_response['error']:
            log_debug("generate_title_from_question | llm_response "
                      f"ERROR: {llm_response}", debug=DEBUG)
            return default_title
        title = llm_response['response']
        return title

    # Conversations management

    def show_conversations(self):
        """
        Show the conversations in the side bar
        """
        title_length = self.get_title_max_length()
        st.header("Previous answers")
        for conversation in st.session_state.conversations:
            col1, col2 = st.columns(2, gap="small")
            with col1:
                title = self.get_conversation_title(conversation)
                help_msg = \
                    f"{conversation['type'].capitalize()} generated on " \
                    f"{conversation['date_time']}\n\nID: {conversation['id']}"
                st.button(
                    title[:title_length],
                    key=f"{conversation['id']}",
                    help=help_msg)
            with col2:
                st.button(
                    "x",
                    key=f"del_{conversation['id']}",
                    on_click=self.delete_conversation,
                    args=(conversation['id'],))

    def set_last_retrieved_conversation(self, id: str, conversation: dict):
        """
        Set the last retrieved conversation
        """
        st.session_state.last_retrieved_conversation = dict(conversation)
        if "id" not in st.session_state.last_retrieved_conversation:
            st.session_state.last_retrieved_conversation["id"] = id

    def get_last_retrieved_conversation(self, id: str):
        """
        Get the last retrieved conversation. If "last_retrieved_conversation"
        entry is found and the id matches, return the buffered conversation.
        Otherwise, retrieve the conversation from the database.

        Args:
            id (str): The conversation ID.

        Returns:
            dict: The conversation dictionary, or None if not found.
        """
        if "last_retrieved_conversation" in st.session_state and \
           id == st.session_state.last_retrieved_conversation["id"]:
            conversation = dict(st.session_state.last_retrieved_conversation)
        else:
            conversation = self.get_conversation(id)
        if conversation:
            self.set_last_retrieved_conversation(id, conversation)
        return conversation

    def show_conversation_debug(self, conversation: dict):
        with st.expander("Detailed Response"):
            st.write(conversation)

    def show_cloud_resource(self, url: str, resource_type: str):
        if resource_type == "image":
            st.image(url)
        elif resource_type == "video":
            st.video(url)
        else:
            st.write(f"Not a video or image: {url}")

    def show_local_resource(self, url: str, resource_type: str):
        if resource_type in ["image", "video"]:
            return self.show_cloud_resource(url, resource_type)
        with open(url, "rb") as url:
            st.download_button(
                label="Download File",
                data=url,
                file_name=os.path.basename(url)
            )

    def verify_and_show_resource(self, url: str, resource_type: str):
        if is_an_url(url):
            self.show_cloud_resource(url, resource_type)
            return
        if not path_exists(url):
            st.write(f"ERROR E-IG-101: file not found: {url}")
        else:
            self.show_local_resource(url, resource_type)

    def show_conversation_content(
        self,
        id: str, container: st.container,
        additional_container: st.container
    ):
        """
        Show the conversation content
        """
        if not id:
            return
        conversation = self.get_last_retrieved_conversation(id)
        if not conversation:
            container.write("ERROR E-600: Conversation not found")
            return
        # log_debug(
        #     "SHOW_CONVERSATION_CONTENT | " +
        #     f"\n | conversation: {conversation}", debug=DEBUG
        # )
        if conversation.get('refined_prompt'):
            with additional_container.expander(
                 f"Enhanced Prompt for {conversation['type'].capitalize()}"):
                st.write(conversation['refined_prompt'])

        if conversation['type'] == "video":
            if conversation.get('answer'):
                # Check for list type entries, and show them individually
                if isinstance(conversation['answer'], list):
                    with container.container():
                        self.show_conversation_debug(conversation)
                        for url in conversation['answer']:
                            st.write(f"Video URL: {url}")
                            self.verify_and_show_resource(url, "video")
                else:
                    with container.container():
                        self.show_conversation_debug(conversation)
                        st.write(f"Video URL: {conversation['answer']}")
                        self.verify_and_show_resource(
                            conversation['answer'], "video")
            else:
                self.video_generation(
                    result_container=container,
                    question=conversation['question'],
                    previous_response=conversation['ttv_response'])

        elif conversation['type'] == "image":
            if conversation.get('answer'):
                # Check for list type entries, and show them individually
                if isinstance(conversation['answer'], list):
                    with container.container():
                        self.show_conversation_debug(conversation)
                        for url in conversation['answer']:
                            self.verify_and_show_resource(url, "image")
                else:
                    with container.container():
                        self.show_conversation_debug(conversation)
                        self.verify_and_show_resource(
                            conversation['answer'], "image")
            else:
                with container.container():
                    self.show_conversation_debug(conversation)
                    st.write("ERROR: No image found as answer")

        else:
            with container.container():
                self.show_conversation_debug(conversation)
                st.write(conversation['answer'])
                if conversation.get("subtype"):
                    if conversation["subtype"] in [
                        "generate_presentation",
                        "generate_app_presentation"
                    ]:
                        extra_button_text = ""
                        if conversation.get("presentation_file_path"):
                            extra_button_text = " again"
                        st.button(
                            f"Generate Presentation{extra_button_text}",
                            on_click=self.create_pptx,
                            args=(conversation,))
                        if conversation.get("presentation_file_path"):
                            self.verify_and_show_resource(
                                conversation["presentation_file_path"],
                                "other")

    def show_conversation_question(self, id: str):
        if not id:
            return
        conversation = self.get_last_retrieved_conversation(id)
        if not conversation:
            st.session_state.question = "ERROR E-700: Conversation not found"
        else:
            st.session_state.question = conversation['question']
            if conversation.get("form_data"):
                form_session_state_key = \
                    self.get_form_session_state_key(conversation)
                st.session_state[form_session_state_key] = \
                    conversation["form_data"]
                # log_debug("SHOW_CONVERSATION_QUESTION | "
                #           f"session_state_key: {form_session_state_key} | "
                #           "form_data: "
                #           f"{st.session_state[form_session_state_key]}",
                #           debug=DEBUG)

    def validate_question(self, question: str, assign_global: bool = True):
        """
        Validate the question
        """
        if not question:
            st.write("Please enter a question / prompt")
            return False
        # Update the user input in the conversation
        if assign_global:
            st.session_state.question = question
        return True

    # Data management

    def format_results(self, results: list):
        return "\n*".join(results)

    def attach_files(self, files):
        """
        Save the files to be attached to the LLM/model call
        """
        if "files_attached" not in st.session_state:
            st.session_state.files_to_attach = []
        if not files:
            return
        for file in files:
            if file:
                st.session_state.files_to_attach.append(file)

    def import_data(self, container: st.container):
        """
        Umport data from a uploaded JSON file into the database
        """

        def process_uploaded_file():
            """
            Process the uploaded file
            """
            uploaded_files = st.session_state.import_data_file
            st.session_state.dm_results = []
            with st.spinner(f"Processing {len(uploaded_files)} files..."):
                for uploaded_file in uploaded_files:
                    uploaded_file_path = uploaded_file.name
                    json_dict = json.loads(uploaded_file.getvalue())
                    db = self.init_db()
                    response = db.import_data(json_dict)
                    if response['error']:
                        item_result = f"File: {uploaded_file_path}" \
                                    f" | ERROR: {response['error_message']}"
                        log_debug(f"IMPORT_DATA | {item_result}", debug=DEBUG)
                        st.session_state.dm_results.append(item_result)
                        continue
                    item_result = f"File: {uploaded_file_path}" \
                                  f" | {response['result']}"
                    st.session_state.dm_results.append(item_result)

        container.file_uploader(
            "Choose a JSON file to perform the import",
            accept_multiple_files=True,
            type="json",
            on_change=process_uploaded_file,
            key="import_data_file",
        )

    def export_data(self, container: st.container):
        """
        Export data from the database and send it to the user as a JSON file
        """
        with st.spinner("Exporting data..."):
            db = self.init_db()
            response = db.export_data()
            if response['error']:
                container.write(f"ERROR {response['error_message']}")
                return
            container.download_button(
                label=f"{response['result']}. Click to download.",
                data=response['json'],
                file_name="data.json",
                mime="application/json",
            )

    def data_management_components(self):
        """
        Show data management components in the side bar
        """
        with st.expander("Data Management"):
            st.write("Import/export data with JSON files")
            sb_col1, sb_col2 = st.columns(2)
            with sb_col1:
                sb_col1.button(
                    "Import Data",
                    key="import_data")
            with sb_col2:
                sb_col2.button(
                    "Export Data",
                    key="export_data")

    # UI

    def get_title(self):
        """
        Returns the title of the app
        """
        return (f"{st.session_state.app_name_version}"
                f" {st.session_state.app_icon}")

    def show_button_of_type(self, button_config: dict, extra_kwargs: dict,
                            container: Any):
        """
        Show a button based on the button_config
        Args:
            button_config (dict): button configuration
                {
                    "text": "Answer Question",
                    "key": "generate_text",
                    "enable_config_name": "GENERATE_TEXT_ENABLED",
                    "type": "checkbox",
                }
        """
        submitted = None
        button_type = button_config.get("type", "button")
        if button_type == "checkbox":
            submitted = container.checkbox(
                button_config["text"],
                key=button_config["key"],
                **extra_kwargs)
        elif button_type == "spacer":
            container.write(button_config.get("text", ""))
        elif button_type == "submit":
            submitted = container.form_submit_button(
                button_config["text"])
        else:
            # Defaults to button
            submitted = container.button(
                button_config["text"],
                key=button_config["key"],
                **extra_kwargs)
        return submitted

    def show_buttons_row(
        self,
        buttons_config: list,
        fill_missing_spaces: bool = False
    ):
        """
        Show buttons based on the buttons_config
        Args:
            buttons_config (listo): list of buttons configurations
                [
                    # Button example with enable config
                    {
                        "text": "Answer Question",
                        "key": "generate_text",
                        "enable_config_name": "TEXT_GENERATION_ENABLED",
                    },
                    # Button example with a function and no enable config
                    {
                        "text": "Enhance prompt",
                        "key": "prompt_enhancement",
                        "on_change": cgsl.prompt_enhancement
                    },

        Returns:
            None
        """
        col = st.columns(len(buttons_config))
        col_index = 0
        submitted = []
        for button in buttons_config:
            extra_kwargs = {}
            for key in ["on_change", "on_click", "args"]:
                if button.get(key, None):
                    extra_kwargs[key] = button[key]
            if button.get("enable_config_name", None):
                with col[col_index]:
                    if self.get_par_value(button["enable_config_name"], True):
                        submitted.append(
                            self.show_button_of_type(
                                button,
                                extra_kwargs,
                                col[col_index]))
                        col_index += 1
                    else:
                        if fill_missing_spaces:
                            st.write("")
                            col_index += 1
            else:
                with col[col_index]:
                    submitted.append(
                        self.show_button_of_type(
                            button,
                            extra_kwargs,
                            col[col_index]))
                    col_index += 1
        return submitted

    def get_buttons_submitted_data(self, buttons_submitted: list,
                                   buttons_data: dict,
                                   submit_button_verification: bool = True):
        """
        Reduce the list of buttons submitted to a single boolean value
        to determine if the form was submitted
        """
        submitted = any(buttons_submitted)

        # log_debug(f"buttons_submitted: {buttons_submitted}", debug=DEBUG)

        buttons_submitted_data = {}
        if submitted:
            # Get the button submitted values
            # and create a dictionary with the form data

            curr_item = 0
            for i in range(len(buttons_data)):
                if not submit_button_verification or \
                   buttons_data[i].get("type") == "submit":
                    if buttons_data[i].get("enable_config_name", None):
                        if self.get_par_value(
                                buttons_data[i]["enable_config_name"], True):
                            # log_debug(f"buttons_data[{i}]: {buttons_data[i]}"
                            #     f" -> {buttons_submitted[curr_item]}",
                            buttons_submitted_data[buttons_data[i]["key"]] = \
                                buttons_submitted[curr_item]
                            curr_item += 1
                    else:
                        # log_debug(f"buttons_data[{i}]: {buttons_data[i]} "
                        #     f"-> {buttons_submitted[curr_item]}",
                        #     debug=DEBUG)
                        buttons_submitted_data[buttons_data[i]["key"]] = \
                            buttons_submitted[curr_item]
                        curr_item += 1
        return buttons_submitted_data

    def get_option_index(self, options: list, value: str):
        """
        Returns the index of the option in the list
        """
        for i, option in enumerate(options):
            if option == value:
                return i
        return 0

    def show_form_fields(self, fields_data: dict, form_data: dict):
        """
        Show the form
        """
        fields_values = {}
        for key in fields_data:
            field = fields_data.get(key)
            if not field.get("enabled", True):
                continue
            value = form_data.get(key, "")
            if field.get("type") == "selectbox":
                field_value = st.selectbox(
                    field.get("title"),
                    field.get("options", []),
                    # key=key,  # If this is set, the value is not assigned
                    help=field.get("help"),
                    index=self.get_option_index(
                        options=field.get("options", []),
                        value=value),
                )
            elif field.get("type") == "radio":
                field_value = st.radio(
                    field.get("title"),
                    field.get("options", []),
                    # key=key,  # If this is set, the value is not assigned
                    help=field.get("help"),
                    index=self.get_option_index(
                        options=field.get("options", []),
                        value=value),
                )
            elif field.get("type") == "text":
                field_value = st.text_input(
                    field.get("title"),
                    value,
                    # key=key,  # If this is set, the value is not assigned
                    help=field.get("help"),
                )
            else:
                field_value = st.text_area(
                    field.get("title"),
                    value,
                    # key=key,  # If this is set, the value is not assigned
                    help=field.get("help"),
                )
            fields_values[key] = field_value
        return fields_values

    def show_form_error(self, message: str):
        """
        Show a form submission error
        """
        show_popup(
            title="The following error(s) were found:",
            message=message,
            msg_type="error")

    def add_buttons_and_return_submitted(self, buttons_config: list):
        """
        Add the buttons to the page, then returns the submitted buttons and the
        buttons configuration
        """
        with st.container():
            submitted = self.show_buttons_row(buttons_config)
            return submitted, buttons_config

    def get_selected_feature(self, form: dict, features_data: dict):
        """
        Returns the selected feature
        """
        log_debug(f"get_selected_feature | form: {form}", debug=DEBUG)
        log_debug(f"get_selected_feature | features_data: {features_data}",
                  debug=DEBUG)
        selected_feature = None
        for key in form.get("buttons_submitted_data"):
            for feature in features_data:
                if form["buttons_submitted_data"].get(key) and \
                        key == feature:
                    selected_feature = feature
                    break
        return selected_feature

    def get_form_name(self, form_config: dict):
        """
        Returns the form session state key
        """
        form_name = form_config.get("name", "application_form")
        return f"{form_name}"

    def get_form_session_state_key(self, form_config: dict):
        """
        Returns the form session state key
        """
        form_name = self.get_form_name(form_config)
        form_session_state_key = form_config.get(
            "form_session_state_key",
            f"{form_name}_data")
        return form_session_state_key

    def show_form(self, form_config: dict):
        """
        Show the configured form
        """
        form_name = self.get_form_name(form_config)
        form_session_state_key = self.get_form_session_state_key(form_config)
        if form_session_state_key not in st.session_state:
            st.session_state[form_session_state_key] = {}
        form_data = st.session_state[form_session_state_key]

        fields_data = form_config.get("fields", {})

        # Clear the form data if it's not the first time the form is shown
        if form_name in st.session_state:
            del st.session_state[form_name]

        with st.form(form_name):
            st.title(form_config.get("title", "Application Form"))

            if form_config.get("subtitle"):
                st.write(form_config.get("subtitle"))

            fields_values = self.show_form_fields(fields_data, form_data)

            if form_config.get("suffix"):
                st.write(form_config.get("suffix"))

            func = form_config.get(
                "buttons_function",
                self.add_buttons_and_return_submitted)
            if form_config.get("buttons_config"):
                buttons_submitted, buttons_data = func(
                    form_config["buttons_config"])
            else:
                buttons_submitted, buttons_data = [], []

        buttons_submitted_data = self.get_buttons_submitted_data(
            buttons_submitted,
            buttons_data)
        if not buttons_submitted_data:
            return None

        st.session_state[form_session_state_key] = dict(fields_values)
        st.session_state[form_session_state_key].update({
            "buttons_submitted_data": buttons_submitted_data
        })
        return st.session_state[form_session_state_key]

    # No-form processing
    def process_no_form_buttons(
        self,
        forms_config_name: str,
        question: str,
        process_form_func: Callable,
        submit_form_func: Callable
    ):
        """
        Process No-Form buttons, like the ones for the
        the ideation-from-prompt feature
        """

        ideation_from_prompt_config = \
            st.session_state.forms_config[forms_config_name]
        ideation_from_prompt_buttons_config = \
            ideation_from_prompt_config.get("buttons_config")
        i = 0
        buttons_submitted = []
        process_form = False
        for button in ideation_from_prompt_buttons_config:
            button_was_clicked = True if st.session_state.get(button["key"]) \
                                else False
            if button_was_clicked:
                process_form = True
            buttons_submitted.append(button_was_clicked)
            i += 1
        data = {
            "buttons_submitted": buttons_submitted,
            "question": question,
        }
        if process_form:
            form = process_form_func(None, "process_form", data)
            if not question:
                self.show_form_error("No question / prompt to process")
            else:
                # Assign here the question to the session state because
                # the question assignment in the process_form_func()
                # when it call the llm is suppressed, to preserve the
                # original question
                st.session_state.question = question
                submit_form_func(
                    form,
                    ideation_from_prompt_config)

    # PPTX generation

    def create_pptx(self, conversation: dict):
        """
        Generates the PowerPoint slides
        """
        log_debug("CREATE_PPTX | enters...", debug=DEBUG)
        pptx_generator = PowerPointGenerator({
            "output_dir": self.params.get("output_dir", "./output"),
            "file_name": uuid.uuid4(),
        })
        answer = conversation.get("answer")
        if not answer:
            error_message = "Conversation answer is empty"
            log_debug(f"CREATE_PPTX | ERROR 1: {error_message}...",
                      debug=DEBUG)
            st.write(error_message)
            return
        if "```json" in answer:
            # Find the first occurrence of ```json, cut the text before it,
            # and remove the ```json and ``` characters
            answer = answer.split("```json")[1].replace("```json", "")
            answer = answer.replace("```", "")
        try:
            log_debug("CREATE_PPTX | answer:"
                      f" {answer}", debug=DEBUG)
            slides_config = json.loads(answer)
            log_debug("CREATE_PPTX | slides_config:"
                      f" {slides_config}", debug=DEBUG)
        except Exception as e:
            error_message = f"ERROR {e}"
            st.write(error_message)
            log_debug(f"CREATE_PPTX | ERROR 2: {error_message}...",
                      debug=DEBUG)
            return

        log_debug("CREATE_PPTX | creating presentation...", debug=DEBUG)

        result_file_path = pptx_generator.generate(slides_config)

        log_debug("CREATE_PPTX | result_file_path: "
                  f"{result_file_path}", debug=DEBUG)

        conversation["presentation_file_path"] = result_file_path
        self.update_conversation(conversation, conversation["id"])
        return result_file_path

    # AI

    def get_available_ai_providers(
        self,
        param_name: str,
        param_values: dict = None
    ) -> list:
        """
        Returns the available LLM providers based on the environment variables
        The model will be available if all its variables are set
        """
        if not param_values:
            param_values = os.environ
        result = []
        for model_name, model_attr in self.get_par_value(param_name).items():
            # log_debug(f"get_available_ai_providers | "
            #           '\nmodel_attr.get("active", True): '
            #           f'{model_attr.get("active", True)}'
            #           f"\nmodel_name: {model_name} | "
            #           f"\nmodel_attr: {model_attr}",
            #           debug=DEBUG)
            if not model_attr.get("active", True):
                continue
            model_to_add = model_name
            requirements = model_attr.get("requirements", [])
            for var_name in requirements:
                if not param_values.get(var_name):
                    model_to_add = None
                    break
            if model_to_add:
                result.append(model_to_add)
        return result

    def get_llm_provider(
        self,
        param_name: str,
        session_state_key: str
    ):
        """
        Returns the LLM provider
        """
        if session_state_key not in st.session_state:
            # return self.get_par_value(param_name)[0]
            provider_list = self.get_available_ai_providers(param_name)
            if not provider_list:
                return ''
            return provider_list[0]
        return st.session_state.get(session_state_key)

    def get_llm_model(
        self,
        parent_param_name: str,
        parent_session_state_key: str,
        param_name: str,
        session_state_key: str
    ):
        """
        Returns the LLM model
        """
        if session_state_key not in st.session_state:
            llm_provider = self.get_llm_provider(
                parent_param_name, parent_session_state_key)
            if not llm_provider:
                return None
            llm_models = self.get_par_value(
                param_name).get(llm_provider, [])
            if not llm_models:
                return None
            return llm_models[0]
        return st.session_state.get(session_state_key)

    def get_model_options(
        self,
        parent_param_name: str,
        parent_session_state_key: str,
        param_name: str,
    ):
        """
        Returns the model options for the LLM call
        """
        llm_provider = self.get_llm_provider(
            parent_param_name, parent_session_state_key)
        if not llm_provider:
            return []
        return self.get_par_value(param_name, {}).get(llm_provider, [])

    def get_llm_provider_index(
        self,
        param_name: str,
        session_state_key: str
    ):
        available_llm_providers = self.get_available_ai_providers(param_name)
        try:
            llm_provider_index = available_llm_providers.index(
                self.get_llm_provider(
                    param_name,
                    session_state_key
                ))
        except ValueError:
            llm_provider_index = 0
        return llm_provider_index

    def get_llm_model_index(
        self,
        parent_param_name: str,
        parent_session_state_key: str,
        param_name: str,
        session_state_key: str
    ):
        # log_debug(
        #   f">> get_llm_model_index:"
        #   f"\n | parent_param_name: {parent_param_name}"
        #   f"\n | parent_session_state_key: {parent_session_state_key}"
        #   f"\n | param_name: {param_name}"
        #   f"\n | session_state_key: {session_state_key}",
        #   debug=DEBUG)
        available_llm_models = self.get_model_options(
            parent_param_name,
            parent_session_state_key,
            param_name
        )
        selected_llm_model = self.get_llm_model(
            parent_param_name,
            parent_session_state_key,
            param_name,
            session_state_key
        )
        # log_debug(f">> get_llm_model_index: "
        #           "\n | available_llm_models: "
        #           f"{available_llm_models}"
        #           "\n | selected_llm_model: "
        #           f"{selected_llm_model}", debug=DEBUG)
        try:
            llm_model_index = available_llm_models.index(
                selected_llm_model)
        except ValueError:
            llm_model_index = 0
        # log_debug(f">> get_llm_model_index | llm_model_index: "
        #           f"{llm_model_index}", debug=DEBUG)
        return llm_model_index

    def set_session_flag(self, session_state_key: str,
                         flag_session_state_key: str):
        flag = False
        if session_state_key in st.session_state:
            if st.session_state.get(session_state_key):
                flag = True
        st.session_state[flag_session_state_key] = flag

    def get_model_configurations(self):
        """
        Returns the model configurations
        """
        model_configurations = {}
        for key in st.session_state:
            if key.startswith("model_config_par_"):
                par_name = key.replace("model_config_par_", "")
                model_configurations[par_name] = st.session_state[key]
        return model_configurations

    def get_llm_text_model(self, model_replacement: dict = None):
        """
        Returns the LLM text model
        """
        llm_parameters = {
            "llm_providers_complete_list":
                # self.get_par_value("LLM_PROVIDERS_COMPLETE_LIST"),
                self.get_par_value("LLM_PROVIDERS", {}).keys(),
            "no_system_prompt_allowed_providers":
                self.get_par_value("NO_SYSTEM_PROMPT_ALLOWED_PROVIDERS"),
            "no_system_prompt_allowed_models":
                self.get_par_value("NO_SYSTEM_PROMPT_ALLOWED_MODELS"),
            "llm_model_forced_values":
                self.get_par_value("LLM_MODEL_FORCED_VALUES"),
            "llm_model_params_naming":
                self.get_par_value("LLM_MODEL_PARAMS_NAMING"),
        }
        log_debug("GET_LLM_TEXT_MODEL | llm_parameters # 1: "
                  f"{llm_parameters}", debug=DEBUG)

        llm_parameters.update(self.get_model_configurations())
        log_debug("GET_LLM_TEXT_MODEL | llm_parameters # 2: "
                  f"{llm_parameters}", debug=DEBUG)

        result = get_default_resultset()
        result["llm_provider"] = self.get_llm_provider(
            "LLM_PROVIDERS",
            "llm_provider"
        )
        result["llm_model"] = self.get_llm_model(
            "LLM_PROVIDERS", "llm_provider",
            "LLM_AVAILABLE_MODELS", "llm_model"
        )
        if not result["llm_provider"]:
            result["error"] = True
            result["error_message"] = "LLM Provider not selected"
        elif not result["llm_model"]:
            result["error"] = True
            result["error_message"] = "LLM Model not selected"
        else:
            if model_replacement:
                # To avoid use the OpenAI reasoning models in the suggestions
                result["llm_model"] = model_replacement.get(
                    result["llm_model"], result["llm_model"])
            # The llm parameters will be available in the LLM class
            llm_parameters["provider"] = result["llm_provider"]
            llm_parameters["model_name"] = result["llm_model"]
            result["class"] = LlmProvider(llm_parameters)
        return result

    def text_generation(self, result_container: st.container,
                        question: str = None, other_data: dict = None,
                        settings: dict = None):
        if not other_data:
            other_data = {}
        if not settings:
            settings = {}
        if not question:
            question = st.session_state.question
        if not self.validate_question(question, settings.get("assign_global")):
            return
        llm_text_model_elements = self.get_llm_text_model()
        if llm_text_model_elements['error']:
            result_container.write(
                f"ERROR E-100-A: {llm_text_model_elements['error_message']}")
            return
        other_data.update({
            "ai_provider": llm_text_model_elements['llm_provider'],
            "ai_model": llm_text_model_elements['llm_model'],
        })
        with st.spinner("Procesing text generation..."):
            # Generating answer
            llm_text_model = llm_text_model_elements['class']
            if "system_prompt" in other_data:
                prompt = other_data["system_prompt"]
            else:
                prompt = "{question}"
            response = llm_text_model.query(
                prompt, question,
                (self.get_par_value("REFINE_LLM_PROMPT_TEXT") if
                 st.session_state.prompt_enhancement_flag else None)
            )
            if response['error']:
                other_data["error_message"] = (
                    f"ERROR E-100: {response['error_message']}")
            self.save_conversation(
                type="text",
                question=question,
                refined_prompt=response.get('refined_prompt'),
                answer=response.get('response'),
                other_data=other_data,
            )
            # result_container.write(response['response'])
            st.rerun()

    def image_generation(self, result_container: st.container,
                         question: str = None,
                         settings: dict = None):
        if not settings:
            settings = {}
        if not question:
            question = st.session_state.question
        if not self.validate_question(question, settings.get("assign_global")):
            return
        llm_provider = self.get_llm_provider(
            "TEXT_TO_IMAGE_PROVIDERS",
            "image_provider"
        )
        llm_model = self.get_llm_model(
            "TEXT_TO_IMAGE_PROVIDERS", "image_provider",
            "TEXT_TO_IMAGE_AVAILABLE_MODELS", "image_model"
        )
        llm_text_model_elements = self.get_llm_text_model()
        if llm_text_model_elements['error']:
            result_container.write(
                f"ERROR E-100-B: {llm_text_model_elements['error_message']}")
            return
        other_data = {
            "ai_provider": llm_provider,
            "ai_model": llm_model,
            "ai_text_model_provider": llm_text_model_elements['llm_provider'],
            "ai_text_model_model": llm_text_model_elements['llm_model'],
        }
        with st.spinner("Procesing image generation..."):
            model_params = {
                # "provider": self.get_par_or_env("TEXT_TO_IMAGE_PROVIDER"),
                "provider": llm_provider,
                "model_name": llm_model,
                "text_model_class": llm_text_model_elements['class'],
            }
            model_params.update(self.get_model_configurations())

            llm_model = ImageGenProvider(model_params)

            response = llm_model.image_gen(
                question,
                (self.get_par_value("REFINE_LLM_PROMPT_TEXT") if
                 st.session_state.prompt_enhancement_flag else None)
            )
            if response['error']:
                # result_container.write(
                #     f"ERROR E-IG-100: {response['error_message']}")
                other_data["error_message"] = (
                    f"ERROR E-IG-100: {response['error_message']}")
            self.save_conversation(
                type="image",
                question=question,
                refined_prompt=response.get('refined_prompt'),
                answer=response.get('response'),
                other_data=other_data,
            )
            # result_container.write(response['response'])
            st.rerun()

    def video_generation(
        self,
        result_container: st.container,
        question: str = None,
        previous_response: dict = None,
        settings: dict = None
    ):
        if not settings:
            settings = {}
        llm_provider = self.get_llm_provider(
            "TEXT_TO_VIDEO_PROVIDERS",
            "video_provider"
        )
        llm_model = self.get_llm_model(
            "TEXT_TO_VIDEO_PROVIDERS", "video_provider",
            "TEXT_TO_VIDEO_AVAILABLE_MODELS", "video_model"
        )

        llm_text_model_elements = self.get_llm_text_model()
        if llm_text_model_elements['error']:
            result_container.write(
                f"ERROR E-100-C: {llm_text_model_elements['error_message']}")
            return

        model_params = {
            # "provider": self.get_par_or_env("TEXT_TO_VIDEO_PROVIDER"),
            "provider": llm_provider,
            "model_name": llm_model,
            "text_model_class": llm_text_model_elements['class'],
        }
        model_params.update(self.get_model_configurations())
        ttv_model = TextToVideoProvider(model_params)

        if previous_response:
            response = previous_response.copy()
            video_id = response['id']
        else:
            video_id = get_new_item_id()
            if not question:
                question = st.session_state.question
            if not self.validate_question(question,
               settings.get("assign_global")):
                return
            with st.spinner("Requesting the video generation..."):
                # Requesting the video generation
                response = ttv_model.video_gen(
                    question,
                    (self.get_par_value("REFINE_VIDEO_PROMPT_TEXT") if
                     st.session_state.prompt_enhancement_flag else None)
                )
                if response['error']:
                    result_container.write(
                        f"ERROR E-200: {response['error_message']}")
                    return

        with st.spinner("Procesing video generation. It can take"
                        " 2+ minutes..."):
            #  Checking the video generation status
            video_url = None
            ttv_response = response.copy()
            ttv_response['id'] = video_id

            # Save a preliminar conversation with the video generation request
            # follow-up data in the ttv_response attribute
            other_data = {
                "ttv_response": ttv_response,
                "ai_provider": llm_provider,
                "ai_model": llm_model,
                "ai_text_model_provider":
                    llm_text_model_elements['llm_provider'],
                "ai_text_model_model": llm_text_model_elements['llm_model'],
            }
            self.save_conversation(
                type="video",
                question=question,
                refined_prompt=ttv_response.get('refined_prompt'),
                answer=video_url,
                other_data=other_data,
                id=video_id,
            )

            response = ttv_model.video_gen_followup(ttv_response)
            if response['error']:
                other_data["error_message"] = (
                    f"ERROR E-300: {response['error_message']}")
            elif response.get("video_url"):
                video_url = response["video_url"]
            else:
                other_data["error_message"] = (
                    "ERROR E-400: Video generation failed."
                    " No video URL. Try again later by clicking"
                    " the corresponding previous answer.")
                if response.get("ttv_followup_response"):
                    other_data["ttv_followup_response"] = \
                        response["ttv_followup_response"]

            if previous_response and other_data.get("error_message"):
                result_container.warning(other_data["error_message"])
                return

            # Save the conversation with the video generation result
            self.save_conversation(
                type="video",
                question=question,
                refined_prompt=ttv_response.get('refined_prompt'),
                answer=video_url,
                other_data=other_data,
                id=video_id,
            )

            if previous_response:
                result_container.video(video_url)
            else:
                st.rerun()

    # Gallery management

    def get_item_urls(self, item_type: str) -> dict:
        """
        Returns a list of video URLs
        Args:
            item_type (str): The type of item to get the URLs for.
                E.g. "video" or "image".
        Returns:
            dict: A standard response dictionary with a "urls" key, which is
                a list of URLs. Also includes a "error" and "error_message"
                keys to report any errors that occurred.
        """
        response = get_default_resultset()
        response['urls'] = []
        for conversation in st.session_state.conversations:
            if conversation['type'] == item_type:
                if conversation.get('answer'):
                    # Check for list type entries, and add them individually
                    # to the list so all entries must be strings urls
                    if isinstance(conversation['answer'], list):
                        for url in conversation['answer']:
                            response['urls'].append(url)
                    else:
                        response['urls'].append(conversation['answer'])
        return response

    def show_gallery(self, galley_type: str):
        """
        Show the gallery of videos or images
        """
        galley_type = galley_type.replace("_gallery", "").lower()
        gdata = {
            "video": {
                "title": "Video Gallery",
                "name": "videos",
                "type": "video",
            },
            "image": {
                "title": "Image Gallery",
                "name": "images",
                "type": "image",
            },
        }
        if not gdata.get(galley_type):
            return

        title = gdata[galley_type].get("title")
        name = gdata[galley_type].get("name")
        item_type = gdata[galley_type].get("type")

        head_col1, head_col2 = st.columns(
            2, gap="small",
            vertical_alignment="bottom")
        with head_col1:
            head_col1.title(
                self.get_title())
            head_col1.write(title)
        with head_col2:
            head_col2.button(
                f"Generate {name.capitalize()}",
                key="go_to_text_generation",
                on_click=self.set_query_param,
                args=("page", "home"),
            )

        # Define video URLs
        item_urls = self.get_item_urls(item_type)
        if not item_urls['urls']:
            st.write(f"** No {name} found. Try again later. **")
            return

        # Display videos in a 3-column layout
        columns = self.get_par_value(f"{item_type.upper()}_GALLERY_COLUMNS", 3)
        cols = st.columns(columns)
        for i, item_url in enumerate(item_urls['urls']):
            with cols[i % columns]:
                if item_type == "video":
                    st.video(item_url)
                elif item_type == "image":
                    st.image(item_url)

    # General functions

    def get_par_value(self, param_name: str, default_value: str = None):
        """
        Returns the parameter value. If the parameter value is a file path,
        it will be read and returned.
        """
        result = self.params.get(param_name, default_value)
        if result and isinstance(result, str) and result.startswith("[") \
           and result.endswith("]"):
            result = read_file(f"config/{result[1:-1]}")
        return result

    def get_par_or_env(self, param_name: str, default_value: str = None):
        """
        Returns the parameter value or the environment variable value
        """
        if os.environ.get(param_name):
            return os.environ.get(param_name)
        return self.get_par_value(param_name, default_value)

    def add_js_script(self, source: str):
        """
        Add a JS script to the page
        """
        # Reference:
        # Injecting JS?
        # https://discuss.streamlit.io/t/injecting-js/22651/5?u=carlos9
        # The following snippet could help you solve your cross-origin issue:
        div_id = uuid.uuid4()
        st.markdown(f"""
            <div style="display:none" id="{div_id}">
                <iframe src="javascript: \
                    var script = document.createElement('script'); \
                    script.type = 'text/javascript'; \
                    script.text = {html.escape(repr(source))}; \
                    var div = window.parent.document."""
                    """getElementById('{div_id}'); \
                    div.appendChild(script); \
                    div.parentElement.parentElement.parentElement."""
                    """style.display = 'none'; \
                "/>
            </div>
        """, unsafe_allow_html=True)
