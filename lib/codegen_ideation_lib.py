"""
Ideation Library
"""
import os

from lib.codegen_utilities import (
    log_debug,
    get_default_resultset,
    error_resultset)
from lib.codegen_general_lib import GeneralLib

DEBUG = False


class IdeationLib(GeneralLib):
    """
    Ideation class
    """

    def process_ideation_form(self, form: dict, form_config: dict):
        """
        Process the ideation form
        """
        features_data = form_config.get("features_data", {})
        fields_data = form_config.get("fields", {})

        log_debug("process_ideation_form | form: " + f"{form}", debug=DEBUG)
        log_debug("process_ideation_form | form_config: " + f"{features_data}",
                  debug=DEBUG)

        # Validates the submitted form
        if not form:
            return error_resultset(
                error_message="No data received from the form",
                message_code='A-PIF-E030',
            )
        if not form.get("buttons_submitted_data"):
            return error_resultset(
                error_message="Missing buttons submitted data",
                message_code='A-PIF-E040',
            )

        # Verify button pressed
        selected_feature = self.get_selected_feature(form, features_data)
        if not selected_feature:
            return error_resultset(
                error_message="No button pressed... try again please",
                message_code='A-PIF-E050',
            )

        # Verify mandatory field
        error_message = ""
        for key in features_data.get(selected_feature).get("mandatory_fields"):
            if not form.get(key):
                field_name = fields_data.get(key, {}).get("title", key)
                error_message += f"{field_name}, "
        if error_message:
            error_message = error_message[:-2]
            return error_resultset(
                error_message=f"Missing field(s): {error_message}",
                message_code='A-PIF-E060',
            )

        template = features_data.get(selected_feature).get("template")
        if not template:
            self.show_form_error("Missing template")
            return

        system_prompt_template = features_data.get(selected_feature) \
            .get("system_prompt")
        if not system_prompt_template:
            return error_resultset(
                error_message="Missing system prompt",
                message_code='A-PIF-E070',
            )

        # Read the template file
        template_path = f"./config/{template}"
        if not os.path.exists(template_path):
            return error_resultset(
                error_message=f"Missing template file: {template_path}",
                message_code='A-PIF-E080',
            )
        with open(template_path, "r") as f:
            question = f.read()

        # Read the system prompt file
        system_prompt_path = f"./config/{system_prompt_template}"
        if not os.path.exists(system_prompt_path):
            return error_resultset(
                error_message="Missing system prompt file:"
                              f" {system_prompt_path}",
                message_code='A-PIF-E090',
            )
        with open(system_prompt_path, "r") as f:
            system_prompt = f.read()

        # Default values
        if "timeframe" not in form:
            form["timeframe"] = \
                self.get_par_value("IDEATION_DEFAULT_TIMEFRAME")
        if "quantity" not in form:
            form["quantity"] = self.get_par_value("IDEATION_DEFAULT_QTY")

        # Replace the placeholders with the user input
        final_form = {}
        for key in form:
            if key in [
                "screenshots",
                "buttons_submitted_data",
                "buttons_submitted"
            ]:
                continue
            log_debug(f"process_ideation_form | key: {key} | "
                      f"form[key]: {form[key]}", debug=DEBUG)
            final_form[key] = form[key]
            if form[key]:
                question = question.replace(f"{{{key}}}", form[key])

        form_name = self.get_form_name(form_config)
        form_session_state_key = self.get_form_session_state_key(form_config)
        other_data = {
            "subtype": selected_feature,
            "template": template,
            "system_prompt": system_prompt,
            "form_name": form_name,
            "form_data": final_form,
            "form_session_state_key": form_session_state_key,
        }

        log_debug("process_ideation_form | question: " + f"{question}"
                  "\n | other_data: " + f"{other_data}",
                  debug=DEBUG)

        # Call the LLM to generate the ideation
        response = self.text_generation(question, other_data,
                                        {"assign_global": False})

        log_debug("process_ideation_form | response: " + f"{response}",
                  debug=DEBUG)

        error_message = None
        if response['error']:
            return error_resultset(
                error_message=response['error_message'],
                message_code='A-PIF-E100',
            )

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
