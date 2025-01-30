"""
LLM provider abstract class
"""
from lib.codegen_utilities import get_default_resultset
from lib.codegen_utilities import log_debug
from lib.codegen_ai_abstracts_constants import DEFAULT_PROMPT_ENHANCEMENT_TEXT


DEBUG = False


def prepare_model_params(model_params: dict, naming: dict = None) -> dict:
    """
    Returns the OpenAI API client and model configurations
    """
    naming = naming or {
        "model_name": "model",
    }
    model_params_naming = model_params.get("llm_model_params_naming", {})
    forced_values = model_params.get("llm_model_forced_values", {})

    # Parameters reference:
    # https://platform.openai.com/docs/api-reference/chat/create

    # Prepare the OpenAI client configurations
    client_config = {}
    for key in ["base_url", "api_key"]:
        if model_params.get(key):
            client_config[naming.get(key, key)] = model_params[key]

    # Prepare the OpenAI API request configurations
    model_config = {}
    for key in ["model", "model_name", "messages", "stop"]:
        if model_params.get(key):
            model_config[naming.get(key, key)] = model_params[key]
    for key in ["temperature", "top_p", "frequency_penalty",
                "presence_penalty"]:
        if model_params.get(key):
            model_config[naming.get(key, key)] = \
                float(model_params[key])
    for key in ["top_k", "max_tokens"]:
        if model_params.get(key):
            model_config[naming.get(key, key)] = int(model_params[key])
    for key in ["stream"]:
        if model_params.get(key):
            model_config[naming.get(key, key)] = model_params[key] == "1"
    # Rename model parameters depending on the model name
    log_debug(f"CODEGEN_AI_ABSTRACTS.PY | prepare_model_params"
              f"\n | model_params: {model_params}",
              debug=DEBUG)

    # Special cases
    if model_params.get("model"):

        # Model parameters renaming
        if model_params["model"] in model_params_naming:
            log_debug(
                "CODEGEN_AI_ABSTRACTS.PY | prepare_model_params"
                f"\n | model_params[model]: {model_params['model']} "
                f"\n | model_params_naming[model_params[\"model\"]]: "
                f"{model_params_naming[model_params['model']]} "
                f"\n | model_params_naming: {model_params_naming}",
                debug=DEBUG)
            for rename_from, rename_to in \
                    model_params_naming[model_params["model"]]:
                log_debug(
                    "CODEGEN_AI_ABSTRACTS.PY | prepare_model_params"
                    f"\n | REVIEW rename elements: {rename_from}, {rename_to}",
                    debug=DEBUG)
                if model_params.get(rename_from):
                    log_debug(
                        "CODEGEN_AI_ABSTRACTS.PY | prepare_model_params"
                        f"\n | ACTION rename: {rename_from}, {rename_to}",
                        debug=DEBUG)
                    model_config[rename_to] = model_params[rename_from]
                    del model_config[rename_from]

        # Model parameters forced values
        if model_params["model"] in forced_values:
            log_debug(
                "CODEGEN_AI_ABSTRACTS.PY | prepare_model_params"
                f"\n | model_params[model]: {model_params['model']} "
                f"\n | forced_values[model_params[\"model\"]]: "
                f"{forced_values[model_params['model']]} "
                f"\n | forced_values: {forced_values}",
                debug=DEBUG)
            for key, value in forced_values[model_params["model"]].items():
                model_config[key] = value

    log_debug(f"CODEGEN_AI_ABSTRACTS.PY | prepare_model_params"
              f"\n | client_config: {client_config}"
              f"\n | model_config: {model_config}",
              debug=DEBUG)

    return {
        "client_config": client_config,
        "model_config": model_config,
    }


class LlmProviderAbstract:
    """
    Abstract class for LLM providers
    """
    def __init__(self, params: dict):
        self.params = params
        self.provider = self.params.get("provider")
        self.api_key = self.params.get("api_key")
        self.model_name = self.params.get("model_name")
        self.naming = self.params.get("naming") or {
            "model_name": "model",
        }
        self.llm = None

    def init_llm(self):
        """
        Abstract method for initializing the LLM
        """
        pass

    def query(
        self,
        prompt: str,
        question: str,
        prompt_enhancement_text: str = None,
        unified: bool = False,
    ) -> dict:
        """
        Abstract method for querying the LLM
        """
        raise NotImplementedError

    def video_gen(
        self,
        question: str,
        prompt_enhancement_text: str = None
    ) -> dict:
        """
        Abstract method for video or other llm/model type request
        """
        raise NotImplementedError

    def image_gen(
        self,
        question: str,
        prompt_enhancement_text: str = None,
        image_extension: str = 'jpg',
    ) -> dict:
        """
        Abstract method for image request
        """
        raise NotImplementedError

    def video_gen_followup(
        self,
        request_response: dict,
        wait_time: int = 60
    ):
        """
        Perform a video or other llm/model type generation request check
        """
        raise NotImplementedError

    def query_from_text_model(
        self,
        prompt: str,
        question: str,
        prompt_enhancement_text: str = None,
        unified: bool = False,
    ) -> dict:
        result = get_default_resultset()
        if not self.params.get("text_model_class"):
            result["error"] = True
            result["error_message"] = "Text model class not provided"
            return result
        return self.params["text_model_class"].query(
            prompt,
            question,
            prompt_enhancement_text,
            unified)

    def prompt_enhancer(
        self,
        question: str,
        prompt_enhancement_text: str = None
    ) -> dict:
        """
        Perform a prompt enhancement request
        """
        response = get_default_resultset()
        if not prompt_enhancement_text:
            prompt_enhancement_text = DEFAULT_PROMPT_ENHANCEMENT_TEXT
        log_debug("PROMPT_ENHANCER"
                  "\n | prompt_enhancement_text: "
                  f"\n{prompt_enhancement_text}"
                  "\n | question:"
                  f"\n{question}",
                  debug=DEBUG)
        llm_response = self.query(prompt_enhancement_text, question)
        log_debug("PROMPT_ENHANCER | llm_response: " + f"{llm_response}",
                  debug=DEBUG)
        if llm_response['error']:
            return llm_response
        refined_prompt = llm_response['response']
        # Clean the refined prompt
        refined_prompt = refined_prompt.replace("\n", " ")
        refined_prompt = refined_prompt.replace("\r", " ")
        refined_prompt = refined_prompt.replace("Refined Prompt:", "")
        refined_prompt = refined_prompt.replace("Enhanced Prompt (Output):",
                                                "")
        refined_prompt = refined_prompt.replace("Enhanced Prompt:", "")
        refined_prompt = refined_prompt.replace("**Enhanced Prompt**:", "")
        refined_prompt = refined_prompt.replace("**Enhanced Prompt**", "")
        refined_prompt = refined_prompt.strip()
        refined_prompt = refined_prompt.replace('"', '')
        response['response'] = refined_prompt
        return response

    def get_messages_array(
        self,
        system_prompt: str,
        user_input: str,
        unified: bool = False,
    ) -> dict:
        """
        Return the messages array for the LLM call in the format expected by
        the OpenAI API.
        The messages array is a list of dictionaries, where each dictionary
        represents a message with a role (system or user) and a content.
        * If the system prompt is not None, it is added as the first message
        with the role "system".
        * If the system prompt is None, the user input is used as the first
        message with the role "user" (no system prompt).
        * If the system prompt has the "{question}" token, there'll be only
        one message with the role "user" and its content will be the system
        prompt with the question token replaced with the user input.
        The user input must have content always.

        Args:
            system_prompt (str): The system prompt for the LLM call.
            user_input (str): The user input for the LLM call.
            unified (bool): Whether to use the unified prompt or not.
                Defaults to False.
                It turns True if the system prompt has the "{question}" token
                or not set.

        Returns:
            dict: The messages array for the LLM call.
        """
        if not system_prompt or "{question}" in system_prompt:
            unified = True
        if unified:
            # Check if the system prompt string has the "{question}" string
            if system_prompt:
                unified_prompt = f"{system_prompt}\n{user_input}"
            else:
                unified_prompt = f"{user_input}"
            if unified_prompt and "{question}" in unified_prompt:
                unified_prompt = unified_prompt.replace(
                    "{question}", f"{user_input}")
            messages = [
                {
                    'role': 'user',
                    'content': unified_prompt.strip()
                }
            ]
        else:
            messages = [
                {
                    'role': 'system',
                    'content': system_prompt.strip()
                },
                {
                    'role': 'user',
                    'content': user_input.strip()
                }
            ]
        return messages

    def get_prompts_and_messages(
        self,
        system_prompt: str,
        user_input: str,
        prompt_enhancement_text: str = None,
        unified: bool = False,
    ) -> dict:
        """
        Perform a LLM refined prompt request and messages array generation
        It's a wrapper for the get_messages_array and get_refined_prompt
        methods.

        Args:
            system_prompt (str): The system prompt for the LLM call.
            user_input (str): The user input for the LLM call.
            prompt_enhancement_text (str): The prompt enhancement text.
                None or empty means there'll be no prompt enhancement.
                Defaults to None.
            unified (bool): Whether to use the unified prompt or not.
                Defaults to False.
                It turns True if the system prompt has the "{question}" token
                or not set.

        Returns:
            dict: a standard response array, including the refined system
                prompt, user input and messages array for the LLM call.
                The structure is:
                {
                    "error": bool,
                    "error_message": str,
                    "resulltset": dict,
                    "system_prompt": str,
                    "user_input": str,
                    "messages": list,
                    "refined_prompt": str,
                }
        """
        response = get_default_resultset()
        # "system_prompt" attributte in the response will be empty if
        # not system_prompt provided or equals to "{question}",
        # meaning that the system_prompt will be the question
        # and there'll be only user role message in the messages array
        response["system_prompt"] = system_prompt if system_prompt \
            or system_prompt != "{question}" else ""
        response["user_input"] = user_input
        response["refined_prompt"] = None

        if not prompt_enhancement_text:
            response["messages"] = self.get_messages_array(
                system_prompt=response["system_prompt"],
                user_input=response["user_input"],
                unified=unified,
            )
            return response

        if response["system_prompt"] and \
           response["system_prompt"] != "{question}":
            # Refine only the system prompt...
            llm_response = self.prompt_enhancer(
                response["system_prompt"], prompt_enhancement_text)
            if llm_response['error']:
                return llm_response
            response["refined_prompt"] = llm_response['response'] if \
                llm_response['response'] != response["system_prompt"] \
                else None
            response["system_prompt"] = llm_response['response']
        else:
            # There's no system prompt, so the user input has or is the
            # prompt... lets refine it
            if response["user_input"]:
                llm_response = self.prompt_enhancer(
                    response["user_input"], prompt_enhancement_text)
                if llm_response['error']:
                    return llm_response
                response["refined_prompt"] = llm_response['response'] if \
                    llm_response['response'] != response["user_input"] \
                    else None
                response["user_input"] = llm_response['response']

        response["messages"] = self.get_messages_array(
            system_prompt=response["system_prompt"],
            user_input=response["user_input"],
            unified=unified,
        )
        return response

    def get_model_args(
        self,
        additional_params: dict = None,
        for_openai_api: bool = False
    ):
        """
        Returns the model parameters for the LLM call

        Args:
            messages (list): The messages array for the LLM call.
                Defaults to None.
            for_openai_api (bool): Whether to return the model parameters for
                the OpenAI API or not. Defaults to False.

        Returns:
            dict: The model parameters for the LLM call.
        """
        if not additional_params:
            additional_params = {}
        params = self.params.copy()
        params.update(additional_params)
        model_params = prepare_model_params(
            params, self.naming)["model_config"]
        if for_openai_api:
            model_params["provider"] = self.provider
            model_params["api_key"] = params.get("api_key")
            model_params["base_url"] = params.get("base_url")
            model_params["stop"] = params.get("stop")
        if params.get('model', params.get('model_name')) == 'ollama':
            if model_params.get('temperature'):
                model_params['options'] = {
                    "temperature": model_params['temperature']
                }
                del model_params['temperature']
        return model_params

    def get_client_args(self, additional_params: dict = None):
        """
        Returns the client configuration for the LLM call
        """
        if not additional_params:
            additional_params = {}
        params = self.params.copy()
        params.update(additional_params)
        return prepare_model_params(params, self.naming)["client_config"]

    def get_unified_flag(self):
        """
        Returns the unified flag.
        Returns:
            bool: True if the model or provider is not allowed
                  to have a system prompt
        """
        unified = False
        nspa_provider = \
            self.params.get("no_system_prompt_allowed_providers", [])
        nspa_model = self.params.get("no_system_prompt_allowed_models", [])
        log_debug(
            "GET_UNIFIED_FLAG # 1" +
            f"\n| provider: {self.provider}" +
            f"\n| model: {self.model_name}" +
            f"\n| nspa_provider: {nspa_provider}" +
            f"\n| nspa_model: {nspa_model}",
            debug=DEBUG)
        if self.provider in nspa_provider or self.model_name in nspa_model:
            unified = True
        log_debug(
            "GET_UNIFIED_FLAG # 2" +
            f"\n| unified: {unified}",
            debug=DEBUG)
        return unified
