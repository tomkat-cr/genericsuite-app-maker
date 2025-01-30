
"""
Rhymes APIs
"""
import os
import time

import requests
import json

from lib.codegen_utilities import (
    log_debug,
    get_default_resultset,
)
from lib.codegen_ai_provider_openai import get_openai_api_response
from lib.codegen_ai_abstracts import LlmProviderAbstract

DEBUG = False

RHYMES_SUCCESS_RESPONSES = ["success", "Success", '成功']


class AriaLlm(LlmProviderAbstract):
    """
    Aria LLM class
    """
    def query(
        self,
        prompt: str,
        question: str,
        prompt_enhancement_text: str = None,
        unified: bool = False,
    ) -> dict:
        """
        Perform a Aria request
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
                          os.environ.get("RHYMES_MODEL_NAME")),
                "api_key": (self.api_key or
                            os.environ.get("RHYMES_ARIA_API_KEY")),
                "base_url": "https://api.rhymes.ai/v1",
                "stop": ["<|im_end|>"],
                "messages": pam_response['messages'],
            },
            for_openai_api=True,
        )
        # Get the OpenAI API response
        log_debug("aria_query | " +
                  f"model_params: {model_params}", debug=DEBUG)
        response = get_openai_api_response(model_params)
        response['refined_prompt'] = pam_response['refined_prompt']
        log_debug("aria_query | " +
                  f"response: {response}", debug=DEBUG)
        return response


class AllegroLlm(LlmProviderAbstract):
    """
    Allegro text-to-video LLM class
    """
    def video_gen(
        self,
        question: str,
        prompt_enhancement_text: str = None
    ) -> dict:
        """
        Perform a Allegro video generation request
        """
        return self.allegro_request_video(question, prompt_enhancement_text)

    def video_gen_followup(
        self,
        request_response: dict,
        wait_time: int = 60
    ):
        """
        Perform a Allegro video generation request check
        """
        return self.allegro_check_video_generation(request_response, wait_time)

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

    def allegro_query(self, model_params: dict) -> dict:
        """
        Perform a Allegro video generation request
        """
        response = get_default_resultset()
        headers = {
            "Authorization": f"{model_params.get('api_key')}",
            "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
        }
        headers.update(model_params.get("headers", {}))
        query = model_params.get("query", {})
        payload = model_params.get("payload", {})
        rhymes_endpoint = model_params.get(
            "base_url", "https://api.rhymes.ai/v1/generateVideoSyn")

        query_string = "&".join([f"{key}={value}" for key, value
                                in query.items()])
        if query_string:
            api_url = f"{rhymes_endpoint}?{query_string}"
        else:
            api_url = rhymes_endpoint

        log_debug("allegro_query | " +
                  f"\nAPI URL: {api_url}" +
                  f"\nAPI headers: {headers}" +
                  f"\nAPI payload: {payload}"
                  f"\nAPI method: {model_params.get('method', 'POST')}",
                  debug=DEBUG)
        try:
            if model_params.get("method", "POST") == "POST":
                model_response = requests.post(
                    api_url, headers=headers,
                    json=payload)
            else:
                model_response = requests.get(api_url, headers=headers)
        except Exception as e:
            response['error'] = True
            response['error_message'] = str(e)
            return response

        if model_response.status_code != 200:
            response['error'] = True
            response['error_message'] = \
                "Request failed with status " \
                f"code {model_response.status_code}"
            return response

        log_debug("allegro_query | API response:" +
                  f"\n{model_response.json()}", debug=DEBUG)
        response['response'] = model_response.json()
        return response

    def allegro_request_video(self, question: str,
                              prompt_enhancement_text: str):
        """
        Perform a Allegro video generation request
        """
        response = get_default_resultset()
        pam_response = self.get_prompts_and_messages(
            user_input=question,
            system_prompt=None,
            prompt_enhancement_text=prompt_enhancement_text,
        )
        if pam_response['error']:
            return pam_response

        rand_seed = int(time.time())
        model_params = {
            "api_key": os.environ.get("RHYMES_ALLEGRO_API_KEY"),
            "headers": {
                "Content-Type": "application/json",
            },
            "payload": {
                # "refined_prompt": refined_prompt,
                "refined_prompt": pam_response['refined_prompt'],
                "user_prompt": question,
                "num_step": 50,
                "rand_seed": rand_seed,
                "cfg_scale": 7.5,
            }
        }

        log_debug("allegro_request_video | GENERATE VIDEO | " +
                  f"model_params: {model_params}", debug=DEBUG)

        response = self.allegro_query(model_params)
        response['refined_prompt'] = pam_response['refined_prompt']

        log_debug("allegro_request_video | GENERATION RESULT | " +
                  f"response: {response}", debug=DEBUG)

        if response['error']:
            return response

        if (response["response"].get("message") and
           response["response"]['message'] not in RHYMES_SUCCESS_RESPONSES) \
           or not response["response"].get("data"):
            message = response["response"].get("message",
                                               "No message and no data")
            response['error'] = True
            response['error_message'] = message

        return response

    def allegro_check_video_generation(
        self,
        allegro_response: dict,
        wait_time: int = 60
    ):
        """
        Perform a Allegro video generation request check
        """
        request_id = allegro_response["response"]["data"]
        log_debug("allegro_check_video_generation | " +
                  f"request_id: {request_id}", debug=DEBUG)

        model_params = {
            "api_key": os.environ.get("RHYMES_ALLEGRO_API_KEY"),
            "base_url": 'https://api.rhymes.ai/v1/videoQuery',
            "query": {
                "requestId": request_id,
            },
            "method": "GET",
        }
        log_debug("allegro_check_video_generation | WAIT FOR VIDEO | " +
                  f"model_params: {model_params}", debug=DEBUG)

        video_url = None
        for i in range(10):
            log_debug(f"allegro_check_video_generation | VERIFICATION TRY {i}",
                      debug=DEBUG)
            # Send the follow-up request to the Allegro API
            response = self.allegro_query(model_params)
            log_debug(f"allegro_check_video_generation | VERIFICATION {i} | " +
                      f"response: {response}", debug=DEBUG)
            if response['error']:
                response["ttv_followup_response"] = response["error_message"]
                return response
            if response["response"]['message'] in RHYMES_SUCCESS_RESPONSES \
               and response["response"].get('data'):
                if isinstance(response["response"]["data"], str):
                    # Verify if the string has a json content
                    if "{" in response["response"]["data"] and \
                       response["response"]["data"].endswith("}"):
                        # Get the response["response"]["data"] string from the
                        # first "{"
                        first_bracket = response["response"]["data"].find("{")
                        response["response"]["data"] = \
                            json.loads(
                                response["response"]["data"][first_bracket:]
                            )
                if isinstance(response["response"]["data"], str):
                    video_url = response["response"]["data"]
                else:
                    # The response is a dictionary with an error message
                    # E.g. { "code": 503, "type": "InternalServerException",
                    #        "message": "Prediction failed" }
                    response["ttv_followup_response"] = \
                        response["response"]["data"]
                    response["error"] = True
                    response["error_message"] = \
                        f"[E-RH-ALL-100] Video generation failed" \
                        f" (request_id: {request_id}," \
                        f' response: {response["ttv_followup_response"]})'
                break
            time.sleep(wait_time)

        if not video_url:
            response["error"] = True
            response["error_message"] = response.get("error_message") or \
                f"[E-RH-ALL-200] Video generation failed" \
                f" (request_id: {request_id}, response: {response})"

        response['video_url'] = video_url
        return response
