"""
X AI (Grok) API
"""
import os

from lib.codegen_utilities import (
    log_debug,
    get_default_resultset,
)
from lib.codegen_ai_abstracts import LlmProviderAbstract
from lib.codegen_ai_provider_openai import get_openai_api_response


DEBUG = False


class OpenRouterLlm(LlmProviderAbstract):
    """
    OpenRouter LLM class
    """
    def query(
        self,
        prompt: str,
        question: str,
        prompt_enhancement_text: str = None,
        unified: bool = False,
    ) -> dict:
        """
        Perform a OpenRouter request
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
                "model": (self.model_name or
                          os.environ.get("OPENROUTER_MODEL_NAME")),
                "api_key": (self.api_key or
                            os.environ.get("OPENROUTER_API_KEY")),
                "base_url": "https://openrouter.ai/api/v1",
                "messages": pam_response['messages'],
            },
            for_openai_api=True,
        )
        # Get the LLM response
        log_debug("openrouter | " +
                  f"model_params: {model_params}", debug=DEBUG)
        response = get_openai_api_response(model_params)
        response['refined_prompt'] = pam_response['refined_prompt']
        log_debug("openrouter | " +
                  f"response: {response}", debug=DEBUG)
        return response
