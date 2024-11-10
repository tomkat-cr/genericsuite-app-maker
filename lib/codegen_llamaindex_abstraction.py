"""
LlamaIndex abstraction

Reference:
https://docs.llamaindex.ai/en/stable/module_guides/models/llms/usage_custom/#example-using-a-custom-llm-model-advanced
"""

from typing import Any

from typing import ClassVar, List
from pydantic import ConfigDict

from llama_index.core.llms import (
    CustomLLM,
    CompletionResponse,
    CompletionResponseGen,
    LLMMetadata,
)
from llama_index.core.llms.callbacks import llm_completion_callback

from lib.codegen_ai_utilities import LlmProvider


class LlamaIndexCustomLLM(CustomLLM):
    context_window: int = 3900
    num_output: int = 256
    model_name: str = "unknown"
    final_response: str = "TBD"
    model_object: LlmProvider = None

    class Config:
        """
        This fix the warning:
            /home/adminuser/venv/lib/python3.12/site-packages/pydantic/
            _internal/_fields.py:132: UserWarning: Field "model_name" in
            LlamaIndexCustomLLM has conflict with protected namespace "model_".
            You may be able to resolve this warning by setting
            `model_config['protected_namespaces'] = ()`.
            warnings.warn(
            /home/adminuser/venv/lib/python3.12/site-packages/pydantic/
            _internal/_fields.py:132: UserWarning: Field "model_object" in
            LlamaIndexCustomLLM has conflict with protected namespace "model_".
            You may be able to resolve this warning by setting 
            `model_config['protected_namespaces'] = ()`.
            warnings.warn(
        """
        arbitrary_types_allowed = True
        protected_namespaces = ()

    @property
    def metadata(self) -> LLMMetadata:
        """Get LLM metadata."""
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.num_output,
            model_name=self.model_name,
        )

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        self.final_response = self.query_custom_llm(prompt)
        return CompletionResponse(text=self.final_response)

    @llm_completion_callback()
    def stream_complete(
        self, prompt: str, **kwargs: Any
    ) -> CompletionResponseGen:
        self.final_response = self.query_custom_llm(prompt)
        response = ""
        for token in self.final_response:
            response += token
            yield CompletionResponse(text=response, delta=token)

    def init_custom_llm(self, model_object: LlmProvider):
        self.model_object = model_object
        self.model_name = model_object.model_name

    def query_custom_llm(self, prompt: str, **kwargs: Any) -> dict:
        if not self.model_object:
            raise ValueError("Model object not initialized")
        llm_response = self.model_object.query(
            prompt="",
            question=prompt,
            prompt_enhancement_text="",
            unified=True,
        )
        if llm_response['error']:
            raise ValueError(f'ERROR: {llm_response["error_message"]}')
        return llm_response['response']
