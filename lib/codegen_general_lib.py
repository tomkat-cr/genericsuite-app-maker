"""
Streamlit UI library
"""
from typing import Any
import os
# import time
import json
import uuid

from lib.codegen_utilities import (
    log_debug,
    # get_date_time,
    get_new_item_id,
    get_default_resultset,
    error_resultset,
    read_file,
)
# from lib.codegen_db import CodegenDatabase
from lib.codegen_ai_utilities import (
    TextToVideoProvider,
    LlmProvider,
    ImageGenProvider,
)
from lib.codegen_powerpoint import PowerPointGenerator


DEBUG = False


class GeneralLib:
    """
    General utilities class
    """
    def __init__(self, params: dict, session_state: dict = None):
        self.params = dict(params)
        self.session_state = session_state or {
            "model_config_par_temperature": 0.5,
            "model_config_par_max_tokens": 2048,
            "model_config_par_top_p": 1.0,
            "model_config_par_frequency_penalty": 0.0,
            "model_config_par_presence_penalty": 0.0,
        }

    # Conversations database

    # def init_db(self):
    #     """
    #     Initialize the JSON file database
    #     """
    #     db_type = os.getenv('DB_TYPE')
    #     db = None
    #     if db_type == 'json':
    #         db = CodegenDatabase("json", {
    #             "JSON_DB_PATH": os.getenv(
    #                 'JSON_DB_PATH',
    #                 self.get_par_value("CONVERSATION_DB_PATH")
    #             ),
    #         })
    #     if db_type == 'mongodb':
    #         db = CodegenDatabase("mongodb", {
    #             "MONGODB_URI": os.getenv('MONGODB_URI'),
    #             "MONGODB_DB_NAME": os.getenv('MONGODB_DB_NAME'),
    #             "MONGODB_COLLECTION_NAME": 
    #                  os.getenv('MONGODB_COLLECTION_NAME')
    #         })
    #     if not db:
    #         raise ValueError(f"Invalid DB_TYPE: {db_type}")
    #     return db

    # def update_conversation(
    #     self,
    #     item: dict = None,
    #     id: str = None
    # ):
    #     db = self.init_db()
    #     log_debug(f"UPDATE_CONVERSATION | id: {id} | item: {item}",
    #               debug=DEBUG)
    #     db.save_item(item, id)
    #     self.set_new_id(id)

    # def save_conversation(
    #     self, type: str,
    #     question: str,
    #     answer: str,
    #     title: str = None,
    #     refined_prompt: str = None,
    #     other_data: dict = None,
    #     id: str = None
    # ):
    #     """
    #     Save the conversation in the database
    #     """
    #     if not id:
    #         id = get_new_item_id()
    #     if not title:
    #         title = self.generate_title_from_question(question)
    #         title = title[:self.get_title_max_length()]
    #     db = self.init_db()
    #     item = {
    #         "type": type,
    #         "title": title,
    #         "question": question,
    #         "answer": answer,
    #         "refined_prompt": refined_prompt,
    #         "timestamp": time.time(),
    #     }
    #     if not other_data:
    #         other_data = {}
    #     item.update(other_data)
    #     db.save_item(item, id)
    #     self.update_conversations()
    #     self.recycle_suggestions()
    #     self.set_new_id(id)
    #     return id

    # def get_conversations(self):
    #     """
    #     Returns the conversations in the database
    #     """
    #     db = self.init_db()
    #     conversations = db.get_list("timestamp", "desc")
    #     # Add the date_time field to each conversation
    #     for conversation in conversations:
    #         conversation['date_time'] = get_date_time(
    #             conversation['timestamp'])
    #     return conversations

    # def get_conversation(self, id: str):
    #     """
    #     Returns the conversation in the database
    #     """
    #     db = self.init_db()
    #     conversation = db.get_item(id)
    #     if conversation:
    #         # Add the date_time field to the conversation
    #         conversation['date_time'] = get_date_time(
    #             conversation['timestamp'])
    #         return conversation
    #     return None

    # def delete_conversation(self, id: str):
    #     """
    #     Delete a conversation from the database
    #     """
    #     db = self.init_db()
    #     db.delete_item(id)
    #     self.update_conversations()

    # Input management

    def validate_question(self, question: str, assign_global: bool = True):
        """
        Validate the question
        """
        if not question:
            return error_resultset(
                error_message="Please enter a question / prompt",
                message_code="GL-VQ-E010"
            )
        # Update the user input in the conversation
        if assign_global:
            self.session_state["question"] = question
        return True

    # Prompt suggestions

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

    # Data management

    def format_results(self, results: list):
        return "\n*".join(results)

    # UI

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
            return error_resultset(
                error_message=error_message,
                message_code="GL-CPW-E010")
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
            log_debug(f"CREATE_PPTX | ERROR 2: {error_message}...",
                      debug=DEBUG)
            return error_resultset(
                error_message=error_message,
                message_code="GL-CPW-E020")

        log_debug("CREATE_PPTX | creating presentation...", debug=DEBUG)

        result_file_path = pptx_generator.generate(slides_config)

        log_debug("CREATE_PPTX | result_file_path: "
                  f"{result_file_path}", debug=DEBUG)

        result = get_default_resultset()
        result["presentation_file_path"] = result_file_path
        return result

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
        log_debug(f"get_available_ai_providers | param_name: {param_name}",
                  debug=DEBUG)
        for model_name, model_attr in self.get_par_value(param_name).items():
            # log_debug(f"get_available_ai_providers | "
            #           '\nmodel_attr.get("active", True): '
            #           f'{model_attr.get("active", True)}'
            #           f"\nmodel_name: {model_name} | "
            #           f"\nmodel_attr: {model_attr}",
            #            debug=DEBUG)
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
        log_debug(f"get_available_ai_providers | result: {result}",
                  debug=DEBUG)
        return result

    def get_llm_provider(
        self,
        param_name: str,
        session_state_key: str
    ):
        """
        Returns the LLM provider
        """
        default_llm_provider = self.get_par_value("DEFAULT_LLM_PROVIDER")
        if default_llm_provider:
            return default_llm_provider
        provider_list = self.get_available_ai_providers(param_name)
        if not provider_list:
            return ''
        return provider_list[0]

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
        llm_provider = self.get_llm_provider(
            parent_param_name, parent_session_state_key)
        if not llm_provider:
            return None
        llm_models = self.get_par_value(
            param_name).get(llm_provider, [])
        if not llm_models:
            return None
        return llm_models[0]

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

    def get_model_configurations(self):
        """
        Returns the model configurations
        """
        model_configurations = {}
        for key in self.session_state:
            if key.startswith("model_config_par_"):
                par_name = key.replace("model_config_par_", "")
                model_configurations[par_name] = self.session_state[key]
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

    def get_prompt_enhancement_flag(self):
        """
        Get prompt enhancement flag condition
        """
        if "prompt_enhancement_flag" in self.session_state:
            return self.session_state["prompt_enhancement_flag"]
        return os.environ.get("PROMPT_ENHANCEMENT_FLAG", '0') == '1'

    def text_generation(
        self,
        question: str = None,
        other_data: dict = None,
        settings: dict = None
    ):
        if not other_data:
            other_data = {}
        if not settings:
            settings = {}
        if not question:
            question = self.session_state.get("question")
        if not self.validate_question(question, settings.get("assign_global")):
            return error_resultset(
                error_message='Invalid question',
                message_code='GL-TG-E010',
            )
        llm_text_model_elements = self.get_llm_text_model()
        if llm_text_model_elements['error']:
            return error_resultset(
                error_message=llm_text_model_elements['error_message'],
                message_code='GL-TG-E020',
            )
        other_data.update({
            "ai_provider": llm_text_model_elements['llm_provider'],
            "ai_model": llm_text_model_elements['llm_model'],
        })
        # Generating answer
        llm_text_model = llm_text_model_elements['class']
        if "system_prompt" in other_data:
            prompt = other_data["system_prompt"]
        else:
            prompt = "{question}"
        response = llm_text_model.query(
            prompt, question,
            (self.get_par_value("REFINE_LLM_PROMPT_TEXT") if
                self.get_prompt_enhancement_flag() else None)
        )
        if response['error']:
            other_data["error_message"] = (
                f"ERROR E-100: {response['error_message']}")
        result = get_default_resultset()
        result["resultset"] = {
            "type": "text",
            "question": question,
            "refined_prompt": response.get('refined_prompt'),
            "answer": response.get('response'),
            "other_data": other_data,
        }
        return result

    def image_generation(
        self,
        question: str = None,
        settings: dict = None
    ):
        result = get_default_resultset()
        if not settings:
            settings = {}
        if not question:
            question = self.session_state.get("question")
        if not self.validate_question(question, settings.get("assign_global")):
            return error_resultset(
                error_message='Invalid question',
                message_code='GL-IG-E010',
            )
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
            return error_resultset(
                error_message=llm_text_model_elements['error_message'],
                message_code='GL-IG-E020',
            )
        other_data = {
            "ai_provider": llm_provider,
            "ai_model": llm_model,
            "ai_text_model_provider": llm_text_model_elements['llm_provider'],
            "ai_text_model_model": llm_text_model_elements['llm_model'],
        }
        model_params = {
            "provider": llm_provider,
            "model_name": llm_model,
            "text_model_class": llm_text_model_elements['class'],
        }
        model_params.update(self.get_model_configurations())

        llm_model = ImageGenProvider(model_params)

        response = llm_model.image_gen(
            question,
            (self.get_par_value("REFINE_LLM_PROMPT_TEXT") if
                self.get_prompt_enhancement_flag() else None)
        )
        if response['error']:
            result["error"] = True
            result["error_message"] = (
                f"ERROR GL-IG-100: {response['error_message']}")

        result.update({
            "type": "image",
            "question": question,
            "refined_prompt": response.get('refined_prompt'),
            "answer": response.get('response'),
            "other_data": other_data,
        })
        log_debug(f"image_generation | result: {result}", debug=DEBUG)
        return result

    def video_generation(
        self,
        question: str = None,
        previous_response: dict = None,
        settings: dict = None
    ):
        result = get_default_resultset()
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
            return error_resultset(
                error_message=llm_text_model_elements['error_message'],
                message_code='GL-VG-E020',
            )

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
                question = self.session_state.get("question")
            if not self.validate_question(question,
               settings.get("assign_global")):
                return error_resultset(
                    error_message='Invalid question',
                    message_code='GL-VG-E010',
                )
            # Requesting the video generation
            response = ttv_model.video_gen(
                question,
                (self.get_par_value("REFINE_VIDEO_PROMPT_TEXT") if
                    self.get_prompt_enhancement_flag() else None)
            )
            if response['error']:
                return error_resultset(
                    error_message=response['error_message'],
                    message_code='GL-VG-E020',
                )

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
        result["resultset"] = {
            "type": "video",
            "question": question,
            "refined_prompt": ttv_response.get('refined_prompt'),
            "answer": video_url,
            "other_data": other_data,
            "id": video_id,
        }

        response = ttv_model.video_gen_followup(ttv_response)
        if response['error']:
            result["error"] = True
            result["error_message"] = (
                f"ERROR GL-VG-E030: {response['error_message']}")
        elif response.get("video_url"):
            video_url = response["video_url"]
        else:
            result["error"] = True
            result["error_message"] = (
                "ERROR GL-VG-E040: Video generation failed."
                " No video URL. Try again later by clicking"
                " the corresponding previous answer.")
            if response.get("ttv_followup_response"):
                other_data["ttv_followup_response"] = \
                    response["ttv_followup_response"]

        if previous_response and result.get("error_message"):
            return error_resultset(
                error_message=result["error_message"],
                message_code='GL-VG-E050',
            )

        # Save the conversation with the video generation result
        result.update({
            "type": "video",
            "question": question,
            "refined_prompt": ttv_response.get('refined_prompt'),
            "answer": video_url,
            "other_data": other_data,
            "id": video_id,
        })
        log_debug(f"video_generation | result: {result}", debug=DEBUG)
        return result

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
