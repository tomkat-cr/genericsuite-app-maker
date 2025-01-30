"""
Together AI API
"""
import os

from together import Together

from lib.codegen_utilities import (
    log_debug,
    get_default_resultset,
)
from lib.codegen_ai_abstracts import LlmProviderAbstract


DEBUG = False


class TogetherAiLlm(LlmProviderAbstract):
    """
    Together AI LLM class
    """
    def query(
        self,
        prompt: str,
        question: str,
        prompt_enhancement_text: str = None,
        unified: bool = False,
    ) -> dict:
        """
        Perform a Together AI request
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

        model_additional_params = {
            "model": self.model_name or os.environ.get(
                "TOGETHER_AI_MODEL_NAME"),
            "messages": pam_response['messages'],
            "max_tokens": self.params.get("max_tokens"),
            "temperature": self.params.get("temperature", 0.5),
            "top_p": self.params.get("top_p", 0.7),
            "top_k": self.params.get("top_k", 50),
            "stop": ["<|eot_id|>", "<|eom_id|>"],
            "repetition_penalty": self.params.get("repetition_penalty", 1),
            "stream": self.params.get("stream", False),
        }
        if os.environ.get("TOGETHER_AI_SAFETY_MODEL"):
            model_additional_params["safety_model"] = os.environ.get(
                "TOGETHER_AI_SAFETY_MODEL")
        model_params = self.get_model_args(
            additional_params=model_additional_params,
        )

        client_params = self.get_client_args(
            additional_params={
                "api_key": self.api_key or os.environ.get(
                    "TOGETHER_AI_API_KEY"),
            },
        )
        log_debug("together_ai_query | " +
                  f"model_params: {model_params}", debug=DEBUG)
        client = Together(**client_params)
        response_raw = client.chat.completions.create(**model_params)
        response['response'] = response_raw.choices[0].message.content
        response['refined_prompt'] = pam_response['refined_prompt']
        log_debug("together_ai_query | " +
                  f"response: {response}", debug=DEBUG)
        return response
