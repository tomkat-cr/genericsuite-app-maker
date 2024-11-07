"""
AI utilities
"""
from lib.codegen_ai_abstracts import LlmProviderAbstract
from lib.codegen_ai_provider_rhymes import (
    AriaLlm,
    AllegroLlm,
)
from lib.codegen_ai_provider_openai import (
    OpenaiLlm,
    OpenaiImageGen,
)
from lib.codegen_ai_provider_groq import GroqLlm
from lib.codegen_ai_provider_nvidia import NvidiaLlm
from lib.codegen_ai_provider_ollama import OllamaLlm
from lib.codegen_ai_provider_huggingface import (
    HuggingFaceLlm,
    HuggingFaceImageGen,
)


class LlmProvider(LlmProviderAbstract):
    """
    Abstract class for LLM providers
    """
    def __init__(self, params: str):
        self.params = params
        self.llm = None
        if self.params.get("provider") == "rhymes":
            self.llm = AriaLlm(self.params)
        elif self.params.get("provider") == "openai":
            self.llm = OpenaiLlm(self.params)
        elif self.params.get("provider") == "groq":
            self.llm = GroqLlm(self.params)
        elif self.params.get("provider") == "nvidia":
            self.llm = NvidiaLlm(self.params)
        elif self.params.get("provider") == "ollama":
            self.llm = OllamaLlm(self.params)
        elif self.params.get("provider") == "huggingface":
            self.llm = HuggingFaceLlm(self.params)
        else:
            raise ValueError("Invalid LLM provider")
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
            self.llm = HuggingFaceImageGen(self.params)
        elif self.params.get("provider") == "openai":
            self.llm = OpenaiImageGen(self.params)
        else:
            raise ValueError("Invalid LLM provider")
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
            self.llm = AllegroLlm(self.params)
        elif self.params.get("provider") == "openai":
            raise NotImplementedError
        else:
            raise ValueError("Invalid LLM provider")
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
