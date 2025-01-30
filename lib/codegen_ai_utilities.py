"""
AI utilities
"""
from lib.codegen_ai_abstracts import LlmProviderAbstract
from lib.codegen_ai_provider_openai import (
    OpenaiLlm,
    OpenaiImageGen,
)
from lib.codegen_utilities import log_debug


DEBUG = False


class LlmProvider(LlmProviderAbstract):
    """
    Abstract class for LLM providers
    """
    def __init__(self, params: str):
        super().__init__(params)
        if self.params.get("provider") == "openai" or \
           self.params.get("provider") == "chat_openai":
            self.llm = OpenaiLlm(self.params)
        elif self.params.get("provider") == "groq":
            from lib.codegen_ai_provider_groq import GroqLlm
            self.llm = GroqLlm(self.params)
        elif self.params.get("provider") == "nvidia":
            from lib.codegen_ai_provider_nvidia import NvidiaLlm
            self.llm = NvidiaLlm(self.params)
        elif self.params.get("provider") == "ollama":
            from lib.codegen_ai_provider_ollama import OllamaLlm
            self.llm = OllamaLlm(self.params)
        elif self.params.get("provider") == "huggingface":
            from lib.codegen_ai_provider_huggingface import HuggingFaceLlm
            self.llm = HuggingFaceLlm(self.params)
        elif self.params.get("provider") == "together_ai":
            from lib.codegen_ai_provider_together_ai import TogetherAiLlm
            self.llm = TogetherAiLlm(self.params)
        elif self.params.get("provider") == "rhymes":
            from lib.codegen_ai_provider_rhymes import AriaLlm
            self.llm = AriaLlm(self.params)
        elif self.params.get("provider") == "xai":
            from lib.codegen_ai_provider_xai import XaiLlm
            self.llm = XaiLlm(self.params)
        elif self.params.get("provider") == "openrouter":
            from lib.codegen_ai_provider_openrouter import OpenRouterLlm
            self.llm = OpenRouterLlm(self.params)
        else:
            raise ValueError(
                f'Invalid LLM provider: {self.params.get("provider")}')
        self.init_llm()

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
        unified = unified or self.get_unified_flag()
        log_debug(
            "LLmProvider.query" +
            f"\n| provider: {self.llm.params.get('provider')}" +
            f"\n| model: {self.llm.params.get('model_name')}" +
            f"\n| unified: {unified}" +
            "\n| no_system_prompt_allowed_providers: "
            f"{self.llm.params.get('no_system_prompt_allowed_providers')}" +
            "\n| no_system_prompt_allowed_models: "
            f"{self.llm.params.get('no_system_prompt_allowed_models')}",
            DEBUG
        )
        llm_response = self.llm.query(
            prompt=prompt,
            question=question,
            prompt_enhancement_text=prompt_enhancement_text,
            unified=unified,
        )
        return llm_response


class ImageGenProvider(LlmProviderAbstract):
    """
    Abstract class for text-to-image providers
    """
    def __init__(self, params: str):
        self.params = params
        self.llm = None
        if self.params.get("provider") == "huggingface":
            from lib.codegen_ai_provider_huggingface import HuggingFaceImageGen
            self.llm = HuggingFaceImageGen(self.params)
        elif self.params.get("provider") == "openai":
            self.llm = OpenaiImageGen(self.params)
        else:
            raise ValueError(
                f'Invalid ImageGen provider: {self.params.get("provider")}')
        self.init_llm()

    def query(self, prompt: str, question: str,
              prompt_enhancement_text: str = None) -> dict:
        """
        Perform a LLM query request
        """
        return self.llm.query(
            prompt, question,
            prompt_enhancement_text)

    def image_gen(
        self,
        question: str,
        prompt_enhancement_text: str = None,
        image_extension: str = 'jpg',
    ) -> dict:
        """
        Perform a image generation request
        """
        return self.llm.image_gen(
            question=question,
            prompt_enhancement_text=prompt_enhancement_text,
            image_extension=image_extension)


class TextToVideoProvider(LlmProviderAbstract):
    """
    Abstract class for text-to-video providers
    """
    def __init__(self, params: str):
        self.params = params
        self.llm = None
        if self.params.get("provider") == "rhymes":
            from lib.codegen_ai_provider_rhymes import AllegroLlm
            self.llm = AllegroLlm(self.params)
        elif self.params.get("provider") == "openai":
            raise NotImplementedError
        else:
            raise ValueError(
                f'Invalid TextToVideo provider: {self.params.get("provider")}')
        self.init_llm()

    def query(self, prompt: str, question: str,
              prompt_enhancement_text: str = None) -> dict:
        """
        Perform a LLM query request
        """
        return self.llm.query(
            prompt, question,
            prompt_enhancement_text)

    def video_gen(
        self,
        question: str,
        prompt_enhancement_text: str = None
    ) -> dict:
        """
        Perform a video generation request
        """
        return self.llm.video_gen(question, prompt_enhancement_text)

    def image_gen(
        self,
        question: str,
        prompt_enhancement_text: str = None,
        image_extension: str = 'jpg',
    ) -> dict:
        """
        Perform a image generation request
        """
        return self.llm.image_gen(
            question=question,
            prompt_enhancement_text=prompt_enhancement_text,
            image_extension=image_extension)

    def video_gen_followup(
        self,
        request_response: dict,
        wait_time: int = 60
    ):
        """
        Perform a video generation request check
        """
        return self.llm.video_gen_followup(request_response, wait_time)
