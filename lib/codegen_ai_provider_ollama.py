"""
Ollama API
"""
import os

import ollama
from ollama import Client

from lib.codegen_utilities import (
    log_debug,
    get_default_resultset,
)
from lib.codegen_ai_abstracts import LlmProviderAbstract


DEBUG = False


class OllamaLlm(LlmProviderAbstract):
    """
    Ollama LLM class
    """
    def query(
        self,
        prompt: str,
        question: str,
        prompt_enhancement_text: str = None,
        unified: bool = False,
    ) -> dict:
        """
        Perform a Ollama request
        """
        response = get_default_resultset()
        pam_response = self.get_prompts_and_messages(
            user_input=question,
            system_prompt=prompt,
            prompt_enhancement_text=prompt_enhancement_text,
            unified=unified,
        )
        if pam_response['error']:
            return pam_response
        model_params = self.get_model_args(
            additional_params={
                "messages": pam_response['messages'],
            },
        )
        client_params = self.get_client_args(
            additional_params={
                "model": self.model_name or os.environ.get("OLLAMA_MODEL"),
            },
        )
        log_debug("ollama_query | " +
                  f"model_params: {model_params}", debug=DEBUG)
        if self.params.get("ollama_base_url"):
            client_params["base_url"] = self.params["ollama_base_url"]
        if client_params.get("base_url"):
            log_debug(
                "Using ollama client with base_url:" +
                f' {client_params.get("base_url")}', debug=DEBUG)
            self.log_debug("", debug=DEBUG)
            client = Client(host=client_params.get("base_url"))
            response_raw = client.chat(**model_params)
        else:
            response_raw = ollama.chat(**model_params)
        response['response'] = response_raw['message']['content']
        response['refined_prompt'] = pam_response['refined_prompt']
        log_debug("ollama_query | " +
                  f"response: {response}", debug=DEBUG)
        return response
