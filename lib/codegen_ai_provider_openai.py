"""
OpenAI API
"""
import os

from openai import OpenAI
from openai.resources.images import ImagesResponse

from lib.codegen_utilities import (
    log_debug,
    get_default_resultset,
)
from lib.codegen_ai_abstracts import (
    LlmProviderAbstract,
    prepare_model_params,
)


DEBUG = False


def get_openai_api_response(model_params: dict, naming: dict = None) -> dict:
    """
    Returns the OpenAI API response for a LLM request
    """
    response = get_default_resultset()
    configs = prepare_model_params(model_params, naming)
    # Initialize the OpenAI client
    try:
        client = OpenAI(**configs["client_config"])
    except Exception as e:
        response['error'] = True
        response['error_message'] = str(e)
        return response
    # Process the question and text
    try:
        llm_response = client.chat.completions.create(
            **configs["model_config"])
    except Exception as e:
        response['error'] = True
        response['error_message'] = str(e)

    if not response['error']:
        log_debug("get_openai_api_response | " +
                  f"{model_params.get('provider', 'Provider N/A')} " +
                  f" LLM response: {llm_response}", debug=DEBUG)
        try:
            if configs["model_config"].get('stream', False):
                response['response'] = ""
                for chunk in llm_response:
                    if chunk.choices[0].delta.content is not None:
                        print(chunk.choices[0].delta.content, end="")
                        response['response'] += chunk.choices[0].delta.content
            else:
                response['response'] = llm_response.choices[0].message.content

        except Exception as e:
            response['error'] = True
            response['error_message'] = str(e)
    return response


class OpenaiLlm(LlmProviderAbstract):
    """
    OpenAI LLM class
    """
    def query(
        self,
        prompt: str,
        question: str,
        prompt_enhancement_text: str = None,
        unified: bool = False,
    ) -> dict:
        """
        Perform a OpenAI request
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
                "api_key": self.api_key or os.environ.get("OPENAI_API_KEY"),
                "model": self.model_name or os.environ.get("OPENAI_MODEL"),
                "messages": pam_response['messages'],
            },
            for_openai_api=True,
        )
        # Get the LLM response
        log_debug("openai_query | " +
                  f"model_params: {model_params}", debug=DEBUG)
        response = get_openai_api_response(model_params)
        response['refined_prompt'] = pam_response['refined_prompt']
        log_debug("openai_query | " +
                  f"response: {response}", debug=DEBUG)
        return response


class OpenaiImageGen(OpenaiLlm):
    """
    OpenAI Image generation class
    """
    def image_gen(
        self,
        question: str,
        prompt_enhancement_text: str = None,
        image_extension: str = 'jpg',
    ) -> dict:
        """
        Perform an OpenAI image generation request
        """
        response = get_default_resultset()
        pam_response = self.get_prompts_and_messages(
            user_input=question,
            system_prompt="",
            prompt_enhancement_text=prompt_enhancement_text,
            unified=True,
        )
        if pam_response['error']:
            return pam_response

        ig_model_name = os.environ.get("OPENAI_IMAGE_GEN_MODEL")
        model_params = {
            # "model": "dall-e-3",
            "model": ig_model_name,
            "prompt": pam_response["user_input"],
            "size": self.params.get("size", "1024x1024"),
            "quality": self.params.get("quality", "standard"),
            "n": 1,
        }

        log_debug("openai_image_gen | " +
                  f"model_params: {model_params}", debug=DEBUG)

        # Get the LLM response
        client = OpenAI(
            api_key=self.api_key or os.environ.get("OPENAI_API_KEY")
        )
        # Process the question and image
        ig_response = client.images.generate(**model_params)

        log_debug(f"openai_image_gen | {ig_model_name}"
                  f" | ig_response: {ig_response}",
                  debug=DEBUG)

        # The 'ImagesResponse' object has an attribute 'data' which is a
        # list of 'Image' objects.
        # We should iterate over this list and extract the URL from each
        # 'Image' object if it exists.

        # Check if the 'ig_response' is an instance of 'ImagesResponse'
        # and extract the URLs from the 'data' attribute
        if isinstance(ig_response, ImagesResponse):
            # Assuming each 'Image' object in the 'data' list has a
            # 'url' attribute
            image_urls = [image.url for image in ig_response.data
                          if hasattr(image, 'url')]
            response['response'] = image_urls
        else:
            # Handle other types of responses or raise an error
            response['error'] = True
            response['error_message'] = "ERROR [IAIG-E030] Unexpected " + \
                "response type received from image generation API."

        response['refined_prompt'] = pam_response['refined_prompt']
        log_debug("openai_image_gen | " +
                  f"response: {response}", debug=DEBUG)
        return response
