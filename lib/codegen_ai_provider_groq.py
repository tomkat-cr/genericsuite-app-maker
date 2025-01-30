"""
Groq API
"""
import os

from groq import Groq

from lib.codegen_utilities import (
    log_debug,
    get_default_resultset,
)
from lib.codegen_ai_abstracts import LlmProviderAbstract


DEBUG = False


class GroqLlm(LlmProviderAbstract):
    """
    Groq LLM class
    """
    def query(
        self,
        prompt: str,
        question: str,
        prompt_enhancement_text: str = None,
        unified: bool = False,
    ) -> dict:
        """
        Perform a Groq request
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
                "model": self.model_name or os.environ.get("GROQ_MODEL_NAME"),
                "messages": pam_response['messages'],
            },
        )
        client_params = self.get_client_args(
            additional_params={
                "api_key": self.api_key or os.environ.get("GROQ_API_KEY"),
            },
        )
        log_debug("groq_query | " +
                  f"model_params: {model_params}", debug=DEBUG)
        client = Groq(**client_params)
        response_raw = client.chat.completions.create(**model_params)
        response['response'] = response_raw.choices[0].message.content
        response['refined_prompt'] = pam_response['refined_prompt']
        log_debug("groq_query | " +
                  f"response: {response}", debug=DEBUG)
        return response
