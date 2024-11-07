"""
Streamlit UI library
"""
import os
import time
import json

import streamlit as st

from lib.codegen_utilities import (
    log_debug,
    get_date_time,
    get_new_item_id,
    get_default_resultset,
)
from lib.codegen_db import CodegenDatabase
from lib.codegen_ai_utilities import (
    TextToVideoProvider,
    LlmProvider,
    ImageGenProvider,
)


DEBUG = True


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
        if "new_id" not in st.session_state:
            st.session_state.new_id = None
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
                    self.params["CONVERSATION_DB_PATH"]),
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

    def save_conversation(
        self, type: str,
        question: str,
        answer: str,
        refined_prompt: str = None,
        other_data: dict = None,
        id: str = None
    ):
        """
        Save the conversation in the database
        """
        if not id:
            id = get_new_item_id()
        db = self.init_db()
        item = {
            "type": type,
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

    def get_suggestions_from_ai(self, prompt: str, qty: int = 4) -> dict:
        """
        Get suggestions from the AI
        """
        llm_model = LlmProvider({
            "provider": os.environ.get("LLM_PROVIDER"),
        })
        llm_response = llm_model.query(prompt, qty)
        log_debug("get_suggestions_from_ai | " +
                  f"response: {llm_response}", debug=DEBUG)
        if llm_response['error']:
            return llm_response
        suggestions = llm_response['response']
        suggestions = suggestions.replace("\n", "")
        suggestions = suggestions.replace("\r", "")
        suggestions = suggestions.replace("Suggestions:", "")
        suggestions = suggestions.strip()
        suggestions = suggestions.replace('```json', '')
        suggestions = suggestions.replace('```', '')
        try:
            suggestions = json.loads(suggestions)
        except Exception as e:
            log_debug(f"get_suggestions_from_ai | ERROR {e}", debug=DEBUG)
            return self.params["DEFAULT_SUGGESTIONS"]
        return suggestions

    def recycle_suggestions(self):
        """
        Recycle the suggestions from the AI
        """
        st.session_state.suggestion = self.get_suggestions_from_ai(
            self.params["SUGGESTIONS_PROMPT_TEXT"],
            self.params["SUGGESTIONS_QTY"]
        )

    def show_one_suggestion(self, suggestion: any):
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
        if st.session_state.get("recycle_suggestions"):
            log_debug("RECYCLE_SUGGESTIONS | Recycling suggestions",
                      debug=DEBUG)
            if self.params.get("DYNAMIC_SUGGESTIONS", True):
                with st.spinner("Recycling suggestions..."):
                    self.recycle_suggestions()
            elif not st.session_state.get("suggestion"):
                st.session_state.suggestion = \
                    self.params["DEFAULT_SUGGESTIONS"]

        # Show the 4 suggestions in the main section
        if "error" in st.session_state.suggestion:
            with st.expander("ERROR loading suggestions..."):
                st.write(st.session_state.suggestion["error_message"])
        else:
            sug_col1, sug_col2, sug_col3 = st.columns(
                3, gap="small",
            )
            for i in range(self.params["SUGGESTIONS_QTY"]):
                if i % 2 != 0:
                    with sug_col1:
                        sug_col1.button(self.show_one_suggestion(
                            st.session_state.suggestion.get(
                                f"s{i+1}")), key=f"s{i+1}")
                else:
                    with sug_col2:
                        sug_col2.button(self.show_one_suggestion(
                            st.session_state.suggestion.get(
                                f"s{i+1}")), key=f"s{i+1}")
            if self.params.get("DYNAMIC_SUGGESTIONS", True):
                with sug_col3:
                    sug_col3.button(
                        ":recycle:",
                        key="recycle_suggestions",
                        help="Recycle suggestions buttons",
                    )

        # Process the suggestion button pushed
        # (must be done before the user input)
        for key in st.session_state.suggestion.keys():
            if st.session_state.get(key):
                st.session_state.question = \
                    self.show_one_suggestion(st.session_state.suggestion[key])
                break

    # Conversations management

    def show_conversations(self):
        """
        Show the conversations in the side bar
        """
        title_length = self.params["CONVERSATION_TITLE_LENGTH"]
        st.header("Previous answers")
        for conversation in st.session_state.conversations:
            col1, col2 = st.columns(2, gap="small")
            with col1:
                st.button(
                    conversation['question'][:title_length],
                    key=f"{conversation['id']}",
                    help=f"{conversation['type'].capitalize()} generated on " +
                        f"{conversation['date_time']}")
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
        log_debug(
            "SHOW_CONVERSATION_CONTENT | " +
            f"\n | conversation: {conversation}", debug=DEBUG
        )
        if conversation.get('refined_prompt'):
            with additional_container.expander(
                 f"Enhanced Prompt for {conversation['type'].capitalize()}"):
                st.write(conversation['refined_prompt'])
        if conversation['type'] == "video":
            if conversation.get('answer'):
                # Check for list type entries, and show them individually
                if isinstance(conversation['answer'], list):
                    for url in conversation['answer']:
                        container.video(url)
                else:
                    container.video(conversation['answer'])
            else:
                self.video_generation(
                    result_container=container,
                    question=conversation['question'],
                    previous_response=conversation['ttv_response'])
        if conversation['type'] == "image":
            if conversation.get('answer'):
                # Check for list type entries, and show them individually
                if isinstance(conversation['answer'], list):
                    for url in conversation['answer']:
                        container.image(url)
                else:
                    container.image(conversation['answer'])
            else:
                container.write("ERROR: No image found as answer")
        else:
            container.write(conversation['answer'])

    def show_conversation_question(self, id: str):
        if not id:
            return
        conversation = self.get_last_retrieved_conversation(id)
        if not conversation:
            st.session_state.question = "ERROR E-700: Conversation not found"
        else:
            st.session_state.question = conversation['question']

    def validate_question(self, question: str):
        """
        Validate the question
        """
        if not question:
            st.write("Please enter a question / prompt")
            return False
        # Update the user input in the conversation
        st.session_state.question = question
        return True

    # Data management

    def format_results(self, results: list):
        return "\n*".join(results)

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

    def prompt_enhancement(self):
        """
        Prompt enhancement checkbox callback
        """
        st.session_state.prompt_enhancement_flag = False
        if "prompt_enhancement" in st.session_state:
            if st.session_state.prompt_enhancement:
                st.session_state.prompt_enhancement_flag = True

    def video_generation(
        self,
        result_container: st.container,
        question: str = None,
        previous_response: dict = None
    ):
        ttv_model = TextToVideoProvider({
            "provider": os.environ.get("TEXT_TO_VIDEO_PROVIDER"),
        })
        if previous_response:
            response = previous_response.copy()
            video_id = response['id']
        else:
            video_id = get_new_item_id()
            if not question:
                question = st.session_state.question
            if not self.validate_question(question):
                return
            with st.spinner("Requesting the video generation..."):
                # Requesting the video generation
                response = ttv_model.video_gen(
                    question,
                    (self.params["REFINE_VIDEO_PROMPT_TEXT"] if
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
            }
            self.save_conversation(
                type="video",
                question=question,
                refined_prompt=ttv_response['refined_prompt'],
                answer=video_url,
                other_data=other_data,
                id=video_id,
            )

            response = ttv_model.video_gen_followup(ttv_response)
            if response['error']:
                result_container.write(
                    f"ERROR E-300: {response['error_message']}")
                return

            if not response.get("video_url"):
                result_container.write(
                    "ERROR E-400: Video generation failed."
                    " No video URL. Try again later by clicking"
                    " the corresponding previous answer.")
                if response.get("ttv_followup_response"):
                    other_data["ttv_followup_response"] = \
                        response["ttv_followup_response"]
            else:
                video_url = response["video_url"]

            # Save the conversation with the video generation result
            self.save_conversation(
                type="video",
                question=question,
                refined_prompt=ttv_response['refined_prompt'],
                answer=video_url,
                other_data=other_data,
                id=video_id,
            )
            # result_container.video(video_url)
            st.rerun()

    def text_generation(self, result_container: st.container,
                        question: str = None):
        if not question:
            question = st.session_state.question
        if not self.validate_question(question):
            return

        with st.spinner("Procesing text generation..."):
            # Generating answer
            llm_model = LlmProvider({
                "provider": os.environ.get("LLM_PROVIDER"),
            })
            prompt = "{question}"
            response = llm_model.query(
                prompt, question,
                (self.params["REFINE_LLM_PROMPT_TEXT"] if
                 st.session_state.prompt_enhancement_flag else None)
            )
            if response['error']:
                result_container.write(
                    f"ERROR E-100: {response['error_message']}")
                return
            self.save_conversation(
                type="text",
                question=question,
                refined_prompt=response['refined_prompt'],
                answer=response['response'],
            )
            # result_container.write(response['response'])
            st.rerun()

    def image_generation(self, result_container: st.container,
                         question: str = None):
        if not question:
            question = st.session_state.question
        if not self.validate_question(question):
            return

        with st.spinner("Procesing image generation..."):
            llm_model = ImageGenProvider({
                "provider": os.environ.get("TEXT_TO_IMAGE_PROVIDER"),
            })
            response = llm_model.image_gen(
                question,
                (self.params["REFINE_LLM_PROMPT_TEXT"] if
                 st.session_state.prompt_enhancement_flag else None)
            )
            if response['error']:
                result_container.write(
                    f"ERROR E-IG-100: {response['error_message']}")
                return
            self.save_conversation(
                type="image",
                question=question,
                refined_prompt=response['refined_prompt'],
                answer=response['response'],
            )
            # result_container.write(response['response'])
            st.rerun()

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
                f"{st.session_state.app_name} {st.session_state.app_icon}")
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
        columns = self.params.get(f"{item_type.upper()}_GALLERY_COLUMNS", 3)
        cols = st.columns(columns)
        for i, item_url in enumerate(item_urls['urls']):
            with cols[i % columns]:
                if item_type == "video":
                    st.video(item_url)
                elif item_type == "image":
                    st.image(item_url)

    def get_par_or_env(self, param_name: str, default_value: str = None):
        """
        Returns the parameter value or the environment variable value
        """
        if os.environ.get(param_name):
            return os.environ.get(param_name)
        if self.params.get(param_name):
            return self.params.get(param_name)
        return default_value


def read_config_file(file_path: str):
    """
    Reads a JSON file and returns its content as a dictionary
    """
    with open(file_path, 'r') as f:
        config = json.load(f)
    return config


def get_app_config():
    """
    Returns the app configuration
    """
    config_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "../config/app_config.json")
    return read_config_file(config_file_path)
