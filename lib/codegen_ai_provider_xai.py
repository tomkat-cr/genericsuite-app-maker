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


class XaiLlm(LlmProviderAbstract):
    """
    X AI (Grok) LLM class
    """
    def query(
        self,
        prompt: str,
        question: str,
        prompt_enhancement_text: str = None,
        unified: bool = False,
    ) -> dict:
        """
        Perform a X AI (Grok) request
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
                          os.environ.get("XAI_MODEL_NAME")),
                "api_key": (self.api_key or
                            os.environ.get("XAI_API_KEY")),
                "base_url": "https://api.x.ai/v1",
                "messages": pam_response['messages'],
            },
            for_openai_api=True,
        )
        # Get the LLM response
        log_debug("x_grok | " +
                  f"model_params: {model_params}", debug=DEBUG)
        response = get_openai_api_response(model_params)
        response['refined_prompt'] = pam_response['refined_prompt']
        log_debug("x_grok | " +
                  f"response: {response}", debug=DEBUG)
        return response

# -------------

# import os
# from openai import OpenAI

# XAI_API_KEY = os.getenv("XAI_API_KEY")
# client = OpenAI(
#     api_key=XAI_API_KEY,
#     base_url=,
# )

# completion = client.chat.completions.create(
#     model="grok-beta",
#     messages=[
#         {"role": "system", "content": "You are Grok, a chatbot inspired
#  by"abs the Hitchhikers Guide to the Galaxy."},
#         {"role": "user", "content": "What is the meaning of life, the u
# niverse, and everything?"},
#     ],
# )

# print(completion.choices[0].message)
