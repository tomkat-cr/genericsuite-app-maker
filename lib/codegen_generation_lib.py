"""
Code Generation Library
"""
import os

from lib.codegen_utilities import (
    # log_debug,
    get_default_resultset,
    error_resultset)
from lib.codegen_general_lib import GeneralLib
from lib.codegen_schema_generator import JsonGenerator

DEBUG = False


class CodeGenLib(GeneralLib):
    """
    Code generation class
    """

    def process_json_and_code_generation(self, question: str = None):
        """
        Generates the JSON file and GS python code for Tools
        """
        if not question:
            return error_resultset(
                error_message='No question supplied',
                message_code='A-PJACG-E010',
            )
        if not self.validate_question(question):
            return error_resultset(
                error_message='Invalid question supplied',
                message_code='A-PJACG-E020',
            )

        llm_text_model_elements = self.get_llm_text_model()
        if llm_text_model_elements['error']:
            return error_resultset(
                error_message=llm_text_model_elements['error_message'],
                message_code='A-PJACG-E030',
            )

        other_data = {
            "ai_provider": llm_text_model_elements['llm_provider'],
            "ai_model": llm_text_model_elements['llm_model'],
            "template": "json_and_code_generation",
        }

        params = {
            "user_input_text": question,
            "use_embeddings": os.environ.get('USE_EMBEDDINGS', '1') == '1',
            "embeddings_sources_dir": self.get_par_value(
                "EMBEDDINGS_SOURCES_DIR", "./embeddings_sources"),
            "provider": llm_text_model_elements['llm_provider'],
            "model": llm_text_model_elements['llm_model'],
        }
        json_generator = JsonGenerator(params=params)
        response = json_generator.generate_json()
        if response['error']:
            other_data["error_message"] = (
                f"A-PJACG-E040: {response['error_message']}")

        other_data.update(response.get('other_data', {}))
        result = get_default_resultset()
        result['resultset'] = {
            "type": "text",
            "question": question,
            "refined_prompt": response.get('refined_prompt'),
            "answer": response.get(
                'response',
                "No response. Check the Detailed Response section."),
            "other_data": other_data,
        }
        return result
