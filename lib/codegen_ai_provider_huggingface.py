"""
HugginFace platform utilities
"""
from typing import Any
import os
import requests
import uuid

from lib.codegen_utilities import (
    log_debug,
    get_default_resultset,
    error_resultset,
)
from lib.codegen_ai_abstracts import LlmProviderAbstract


DEBUG = False

# from genericsuite.util.app_context import CommonAppContext
# from genericsuite.util.app_logger import log_debug
# from genericsuite.util.utilities import (
#     get_default_resultset,
#     error_resultset,
#     get_mime_type,
# )
# from genericsuite.util.aws import upload_nodup_file_to_s3

# from genericsuite_ai.config.config import Config

# DEBUG = False
# cac = CommonAppContext()


class HuggingFaceLlm(LlmProviderAbstract):
    """
    HuggingFace LLM class
    """
    def query(
        self,
        prompt: str,
        question: str,
        prompt_enhancement_text: str = None,
        unified: bool = False,
    ) -> dict:
        """
        Perform a HuggingFace request
        """
        response = get_default_resultset()
        # Always a single message
        unified = True
        pam_response = self.get_prompts_and_messages(
            user_input=question,
            system_prompt=prompt,
            prompt_enhancement_text=prompt_enhancement_text,
            unified=unified,
        )
        if pam_response['error']:
            return pam_response

        model_params = {
            "inputs": pam_response["messages"][0]["content"],
            "parameters": {
                # "do_sample": True,
                # "max_new_tokens": 1024,
                # "temperature": 0.5,
                # "top_p": 1,
                # "repetition_penalty": 1.1,
                # "top_k": 40,
                # "typical_p": 1,
                # "truncate": None,
            },
            "options": {
                "use_cache": True,
            },
        }
        model_name = self.model_name or \
            os.environ.get("HUGGINGFACE_MODEL_NAME")
        response_raw = self.hf_query(
            repo_id=model_name,
            payload=model_params,
        )
        log_debug(
            "huggingface_query | " +
            f"response_raw BEFORE CONVERSION: {response_raw}",
            debug=DEBUG)
        try:
            response_raw = response_raw.json()
            log_debug(
                "huggingface_query | " +
                f"response_raw AFTER CONVERSION: {response_raw}",
                debug=DEBUG)
            if response_raw.get('error'):
                return error_resultset(
                    error_message=response_raw['error'],
                    message_code='HF-E010',
                )
            response['response'] = response_raw['message']['content']
        except requests.exceptions.JSONDecodeError:
            response['response'] = response_raw.text
        except Exception as e:
            return error_resultset(
                error_message=f"ERROR {e}",
                message_code='HF-E020',
            )
        response['refined_prompt'] = pam_response['refined_prompt']
        return response

    def hf_query(self, repo_id: str, payload: dict) -> Any:
        """
        Perform a HuggingFace query

        Args:
            api_url (str): HuggingFace API URL
            payload (dict): HuggingFace payload

        Returns:
            Any: HuggingFace response
        """
        # https://huggingface.co/docs/api-inference/detailed_parameters
        api_key = self.api_key or \
            os.environ.get("HUGGINGFACE_API_KEY")
        headers = {
            "Authorization": f"Bearer {api_key}",
        }
        base_url = os.environ.get(
            "HUGGINGFACE_API_URL",
            "https://api-inference.huggingface.co/models")
        api_url = f'{base_url}/{repo_id}'
        return requests.post(api_url, headers=headers, json=payload)


class HuggingFaceImageGen(HuggingFaceLlm):
    """
    HuggingFace Image Generation class
    """
    def query(
        self,
        prompt: str,
        question: str,
        prompt_enhancement_text: str = None,
        unified: bool = False,
    ) -> dict:
        return self.query_from_text_model(
            prompt,
            question,
            prompt_enhancement_text,
            unified)

    def image_gen(
        self,
        question: str,
        prompt_enhancement_text: str = None,
        image_extension: str = 'jpg',
    ) -> dict:
        """
        HuggingFace image generation
        """
        ig_response = get_default_resultset()
        if not question:
            return error_resultset(
                error_message='No question supplied',
                message_code='HFIG-E010',
            )

        pam_response = self.get_prompts_and_messages(
            user_input=question,
            system_prompt="",
            prompt_enhancement_text=prompt_enhancement_text,
            unified=True,
        )
        if pam_response['error']:
            return pam_response

        if self.params.get("model_name"):
            img_model_name = self.params.get("model_name")
        else:
            img_model_name = os.environ.get("HUGGINGFACE_IMAGE_MODEL_NAME")
        if not img_model_name:
            return error_resultset(
                error_message='No model name supplied',
                message_code='HFIG-E020',
            )
        _ = DEBUG and log_debug(
            '1) huggingface_img_gen' +
            f'\n| question: {question}' +
            f'\n| api_url: {img_model_name}')

        image_bytes = self.hf_query(
            repo_id=img_model_name,
            payload={
                "inputs": pam_response["user_input"],
            }
        ).content

        # Generate a unique filename
        image_filename = f'hf_img_{uuid.uuid4()}.{image_extension}'
        target_path = os.environ.get("IMAGES_DIRECTORY", "./images")
        image_path = f'{target_path}/{image_filename}'

        # Create the temporary local file
        with open(image_path, 'wb') as f:
            f.write(image_bytes)

        # Store the image bytes in AWS
        # upload_result = upload_nodup_file_to_s3(
        #     file_path=image_path,
        #     original_filename=image_filename,
        #     bucket_name=settings.AWS_S3_CHATBOT_ATTACHMENTS_BUCKET,
        #     sub_dir=cac.app_context.get_user_id(),
        # )
        # if upload_result['error']:
        #     return error_resultset(
        #         error_message=upload_result['error_message'],
        #         message_code="HFIG-E030",
        #     )
        # Add the S3 URL to the response
        # upload_result['file_name'] = image_filename
        # upload_result['file_type'] = get_mime_type(image_filename)
        # upload_result['file_size'] = os.path.getsize(image_path)
        # ig_response['resultset'] = {'uploaded_file': upload_result}

        ig_response['response'] = image_path
        ig_response['refined_prompt'] = pam_response['refined_prompt']

        if DEBUG:
            log_debug('2) huggingface_img_gen | ig_response:')
            print(ig_response)

        return ig_response
