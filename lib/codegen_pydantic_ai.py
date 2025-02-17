from typing import Callable, Any
# from typing import Type
import os

from dataclasses import dataclass

from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    TextPart
)
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI
import nest_asyncio

from lib.codegen_utilities import log_debug, fix_ollama_url


DEBUG = False

# To fix the error "This event loop is already running"
nest_asyncio.apply()


@dataclass
class PydanticAIDeps:
    """Base class for Pydantic AI dependencies"""
    pass


@dataclass
class PydanticAIDepsOpenAI(PydanticAIDeps):
    openai_client: AsyncOpenAI


@dataclass
class PydanticAIDepsAnthropic(PydanticAIDeps):
    anthropic_client: Any


@dataclass
class PydanticAIDepsGroq(PydanticAIDeps):
    groq_client: Any


class PydanticAiLib:

    def __init__(
        self,
        params: dict,
        getenv_func: Callable = os.getenv,
        PydanticAIDepsClass: Any = PydanticAIDepsOpenAI
    ):
        self.params = params or {}
        self.getenv_func = getenv_func
        self.PydanticAIDepsClass = PydanticAIDepsClass

        self.error_message = None
        self.pydantic_ai_agent = None

        self.llm_provider = None
        self.model = None
        self.model_params = {}
        self.model_settings = {}
        self.for_openai_api = True

        self.init_sequence()

    def init_sequence(self):
        self.set_default_llm_provider()

        self.pydantic_ai_deps = self.params.get("pydantic_ai_deps", {})

        self.system_prompt = self.params.get("system_prompt")
        if self.params.get("max_tokens"):
            self.model_settings["max_tokens"] = \
                self.params.get("max_tokens")
        self.model_settings["temperature"] = \
            self.params.get("temperature", 0.5)
        self.model_settings["top_p"] = self.params.get("top_p", 0.7)
        self.model_settings["top_k"] = self.params.get("top_k", 50)
        self.model_settings["stream"] = self.params.get("stream", False)

        # OpenAI-compatible Models

        if self.llm_provider == "openai":
            # OpenAI
            self.model_name = self.get_llm_model_name("OPENAI_MODEL_NAME")
            self.model_params["api_key"] = self.getenv_func("OPENAI_API_KEY")

        elif self.llm_provider == "openrouter":
            # OpenRouter
            self.model_name = self.get_llm_model_name("OPENROUTER_MODEL_NAME")
            self.model_params["api_key"] = \
                self.getenv_func("OPENROUTER_API_KEY")
            self.model_params["base_url"] = "https://openrouter.ai/api/v1"

        elif self.llm_provider == "aimlapi":
            # AI/ML API
            self.model_name = self.get_llm_model_name("AIMLAPI_MODEL_NAME")
            self.model_params["api_key"] = self.getenv_func("AIMLAPI_API_KEY")
            self.model_params["base_url"] = "https://api.aimlapi.com"

        elif self.llm_provider == "nvidia":
            # Nvidia
            self.model_name = self.get_llm_model_name("NVIDIA_MODEL_NAME")
            self.model_params["api_key"] = self.getenv_func("NVIDIA_API_KEY")
            self.model_params["base_url"] = \
                "https://integrate.api.nvidia.com/v1"

        elif self.llm_provider == "xai":
            # xAI (Grok)
            self.model_name = self.get_llm_model_name("XAI_MODEL_NAME")
            self.model_params["api_key"] = self.getenv_func("XAI_API_KEY")
            self.model_params["base_url"] = "https://api.x.ai/v1"

        elif self.llm_provider == "rhymes":
            # Rhymes Aria
            self.model_name = self.get_llm_model_name("RHYMES_MODEL_NAME")
            self.model_params["api_key"] = \
                self.getenv_func("RHYMES_ARIA_API_KEY")
            self.model_params["base_url"] = "https://api.rhymes.ai/v1"
            self.model_settings["stop"] = ["\n"]

        elif self.llm_provider == "together_ai":
            # Toghether AI
            self.model_name = self.get_llm_model_name("TOGETHER_AI_MODEL_NAME")
            self.model_params["api_key"] = \
                self.getenv_func("TOGETHER_AI_API_KEY")
            self.model_params["base_url"] = "https://api.together.xyz/v1"
            self.model_settings["stop"] = ["<|eot_id|>", "<|eom_id|>"]
            self.model_settings["repetition_penalty"] = \
                self.params.get("repetition_penalty", 1)

        elif self.llm_provider == "ollama":
            # Ollama
            self.model_name = self.get_llm_model_name("OLLAMA_MODEL_NAME")
            self.model_params["base_url"] = self.getenv_func("OLLAMA_BASE_URL")
            if not self.model_params["base_url"]:
                self.model_params["base_url"] = "http://localhost:11434/v1"
            else:
                self.model_params["base_url"] = fix_ollama_url(
                    self.model_params["base_url"])
            self.model_settings = {
                "options": dict(self.model_settings)
            }

        # Other LLM providers

        elif self.llm_provider == "anthropic":
            # Anthropic
            try:
                from pydantic_ai.models.anthropic import AnthropicModel
                from anthropic import AsyncAnthropic
            except ImportError:
                log_debug("Anthropic not installed", DEBUG)
                self.error_message = "Anthropic not installed"
                return
            self.for_openai_api = False
            self.model_name = self.get_llm_model_name("ANTHROPIC_MODEL_NAME")
            self.model_params["api_key"] = \
                self.getenv_func("ANTHROPIC_API_KEY")

            self.pydantic_ai_deps["anthropic_client"] = \
                AsyncAnthropic(**self.model_params)
            self.model = AnthropicModel(self.model_name, **self.model_params)
            self.PydanticAIDepsClass = PydanticAIDepsAnthropic

        elif self.llm_provider == "groq":
            # Groq
            try:
                from pydantic_ai.models.groq import GroqModel
                from groq import AsyncGroq
            except ImportError:
                log_debug("Groq not installed", DEBUG)
                self.error_message = "Groq not installed"
                return
            self.for_openai_api = False
            self.model_name = self.get_llm_model_name("GROQ_MODEL_NAME")
            self.model_params["api_key"] = self.getenv_func("GROQ_API_KEY")

            self.pydantic_ai_deps["groq_client"] = \
                AsyncGroq(**self.model_params)
            self.model = GroqModel(self.model_name, **self.model_params)
            self.PydanticAIDepsClass = PydanticAIDepsGroq

        else:
            log_debug(f"Invalid LLM provider: {self.llm_provider}", DEBUG)
            self.error_message = f"Invalid LLM provider: {self.llm_provider}"
            return

        if self.for_openai_api:
            self.model = OpenAIModel(self.model_name, **self.model_params)
            self.pydantic_ai_deps["openai_client"] = \
                AsyncOpenAI(**self.model_params)

        log_debug(f"PydanticAI params: {self.params}", DEBUG)
        log_debug(f"PydanticAI llm_provider: {self.llm_provider}", DEBUG)
        log_debug(f"PydanticAI model_name: {self.model_name}", DEBUG)
        log_debug(f"PydanticAI model_params: {self.model_params}", DEBUG)
        log_debug(f"PydanticAI model_settings: {self.model_settings}", DEBUG)
        log_debug(f"PydanticAI for_openai_api: {self.for_openai_api}", DEBUG)
        log_debug(
            f"PydanticAI pydantic_ai_deps: {self.pydantic_ai_deps}", DEBUG)
        log_debug(f"PydanticAI model: {self.model}", DEBUG)
        log_debug(f"PydanticAI error message: {self.error_message}", DEBUG)

    # Parameters utilities

    def set_default_llm_provider(self):
        self.llm_provider = \
            self.get_default_llm_provider("DEFAULT_LLM_PROVIDER")
        if not self.llm_provider and not self.error_message:
            self.error_message = "No DEFAULT_LLM_PROVIDER set"

        if self.error_message:
            log_debug(f"ERROR: {self.error_message}", DEBUG)
            # Continue with openai to avoid raise an error until
            # run_agent is called
            self.llm_provider = "openai"

    def get_par_val(self, par_name: str, default_value: str = None):
        """
        Get the value of a parameter. If it exists in the own parameters,
        return it. Otherwise, return the value of the environment variable
        with the same name.

        Args:
            par_name (str): The name of the parameter
            default_value (str, optional): The default value to return if the
                parameter is not found. Defaults to None.

        Returns:
            str: The value of the parameter
        """
        if par_name in self.params:
            return self.params.get(par_name, default_value)
        return self.getenv_func(par_name, default_value)

    # Error utilities

    def get_error_message(self) -> str:
        """
        Return the error message, normally thrown by the constructor.
        """
        return self.error_message

    # PydanticAI dependencies utilities

    def get_pydantic_ai_deps(self) -> dict:
        """
        Return the dependencies for the PydanticAI agent.
        """
        return self.pydantic_ai_deps

    def set_pydantic_ai_deps(self, value: dict) -> None:
        """
        Set the dependencies for the PydanticAI agent.
        """
        self.pydantic_ai_deps = dict(value)

    def get_pydantic_ai_deps_class(self) -> type:
        """
        Return the class for the PydanticAI dependencies.
        """
        return self.PydanticAIDepsClass

    def set_pydantic_ai_deps_class(self, value: type) -> None:
        """
        Set the class for the PydanticAI dependencies.
        """
        self.PydanticAIDepsClass = value

    # LLM provider and AI model utilities

    def get_available_ai_providers(
        self,
        config_param_name: str = "LLM_PROVIDERS",
        param_values: dict = None
    ) -> list:
        """
        Returns the available LLM providers name list which are active and
        have all their variables set.

        Args:
            config_param_name (str): the configuration parameter/envvar name
                to get the LLM providers from
            param_values (dict): the env var values. Defaults to the OS
                environment.

        Returns:
            list: the LLM providers name list
        """
        if not param_values:
            param_values = os.environ
        result = []
        log_debug("get_available_ai_providers"
                  f" | config_param_name: {config_param_name}",
                  debug=DEBUG)
        providers = self.getenv_func(config_param_name)
        if not providers:
            return result
        for model_name, model_attr in providers.items():
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

    def get_default_llm_provider(
        self,
        envvar_name: str,
    ) -> str:
        """
        Returns the LLM provider

        Args:
            envvar_name (str): the env var name to get the LLM
                provider name from

        Returns:
            str: the LLM provider name
        """
        # Get the provider list from the app configuration
        provider_list = self.get_available_ai_providers()
        if not provider_list:
            self.error_message = "No LLM Providers found with API Keys and" \
                                 "/or other requirements met"
            return None

        # Try to get from env var
        default_llm_provider = self.getenv_func(envvar_name)
        # log_debug(f"get_default_llm_provider [1]"
        #           f"\n | envvar_name: {envvar_name}"
        #           f"\n | default_llm_provider: {default_llm_provider}",
        #           debug=DEBUG)

        # If no default is set, return the first available
        if not default_llm_provider:
            default_llm_provider = provider_list[0]

        # If default is set, return it if it's in the provider list
        # If is not there, it could be because requirements are not met
        # or it's a not supported provider
        if default_llm_provider not in provider_list:
            self.error_message = \
                f"Provider '{default_llm_provider}' requirements not met"
            return None

        log_debug(f"get_default_llm_provider [2]"
                  f"\n | default_llm_provider: {default_llm_provider}",
                  debug=DEBUG)

        return default_llm_provider

    def get_llm_model_name(
        self,
        param_name: str,
        default: str = None
    ) -> str:
        """
        Returns the LLM model name

        Args:
            param_name (str): the configuration parameter/envvar name
                to get the LLM model name from
            default (str): the default value to return if the parameter
                is not set

        Returns:
            str: the LLM model name or None if not found
        """
        # Get the model name from the configuration/env var
        model_name = self.getenv_func(param_name, default)
        if model_name:
            return model_name
        # Available models for each provider
        llm_available_models = self.getenv_func("LLM_AVAILABLE_MODELS")
        # log_debug(
        #     "get_llm_model_name [1]"
        #     f"\n | llm_provider: {self.llm_provider}"
        #     f"\n | llm_available_models: {llm_available_models}",
        #     debug=DEBUG)
        if not llm_available_models:
            return None
        if self.llm_provider in llm_available_models:
            llm_models = llm_available_models[self.llm_provider]
        if len(llm_models) == 0:
            # Get the first model for the provider
            return None
        model_name = llm_models[0]
        log_debug(f"get_llm_model_name [2] | model_name: {model_name}", DEBUG)
        return model_name

    # Agent utilities

    def convert_messages(self, conversation_history: list) -> list:
        """
        Convert a list of messages with role and content to a list of
        dictionaries compatible with PydanticAI.

        Args:
            conversation_history (list): the conversation history. Each element
                is a dictionary with the following keys: "role" and "content".
                "role" can be "human" or "agent" and "content" is the message.

        Returns:
            list: the conversation history converted to a list of dictionaries
                compatible with PydanticAI
        """
        # Convert conversation history to format expected by agent
        log_debug(f">>> conversation_history:\n{conversation_history}", DEBUG)
        messages = []
        for msg in conversation_history:
            msg_type = msg["role"]
            msg_content = msg["content"]
            result = ModelRequest(
                    parts=[UserPromptPart(content=msg_content)]
                ) \
                if msg_type == "human" else \
                ModelResponse(
                    parts=[TextPart(content=msg_content)]
                )
            messages.append(result)
        return messages

    def set_pydantic_ai_agent(self, agent: Agent = None) -> None:
        """
        Sets the PydanticAI agent.

        Args:
            agent (Agent): the PydanticAI agent
        """
        self.pydantic_ai_agent = agent

    def get_pydantic_ai_agent(self, system_prompt: str = None) -> Agent:
        """
        Assigns and returns the PydanticAI agent. If it's not created yet,
        create it.

        Args:
            system_prompt (str): the system prompt. If not provided, it will
                throw a ValueError exception.

        Returns:
            Agent: the PydanticAI agent
        """
        if system_prompt:
            self.system_prompt = system_prompt

        if not self.pydantic_ai_agent:
            # Agent() Reference: https://ai.pydantic.dev/api/agent/
            self.pydantic_ai_agent = Agent(
                self.model,
                system_prompt=system_prompt,
                deps_type=self.PydanticAIDepsClass,
                retries=2
            )

        log_debug(
            ">>> PydanticAiLib.get_pydantic_ai_agent:"
            f"\n | model: {self.model}"
            # f"\n | system_prompt: {system_prompt}"
            f"\n | pydantic_ai_agent: {self.pydantic_ai_agent}",
            debug=DEBUG
        )

        return self.pydantic_ai_agent

    # Agent entry point

    def run_agent(
        self,
        user_input: str,
        messages: list,
        deps: dict = None
    ) -> str:
        """
        Run the agent with non-streaming text for the user_input prompt,
        system_prompt and deps, message history and dependencies
        for the PydanticAI agent.

        Args:
            user_input (str): the user input prompt
            messages (list): the message history (list of dictionaries)
            deps (dict): the dependencies. If not provided, it will
                throw a ValueError exception.

        Returns:
            str: the agent response
        """

        if self.get_error_message():
            return self.get_error_message()

        if not self.pydantic_ai_agent:
            self.pydantic_ai_agent = self.get_pydantic_ai_agent()

        # Prepare dependencies
        if not deps:
            deps = self.PydanticAIDepsClass(**self.pydantic_ai_deps)

        # Prepare messages
        messages = self.convert_messages(messages)

        log_debug(
            ">>> PydanticAiLib.run_agent [1]:"
            f"\n | user_input: {user_input}"
            f"\n | model_settings: {self.model_settings}"
            f"\n | deps: {deps}"
            f"\n | messages: {messages}",
            debug=DEBUG)

        # Run the agent in a stream
        result = self.pydantic_ai_agent.run_sync(
            user_input,
            deps=deps,
            message_history=messages,
            model_settings=self.model_settings
        )
        log_debug(f">>> PydanticAiLib.run_agent [2]: {result.data}",
                  debug=DEBUG)
        return result.data
