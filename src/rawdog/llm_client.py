import json
import os
from textwrap import dedent, indent
from typing import Optional

from litellm import completion, completion_cost

from rawdog.logging import log_conversation
from rawdog.parsing import parse_script
from rawdog.prompts import script_examples, script_prompt
from rawdog.utils import EnvInfo, rawdog_log_path


class LLMClient:

    def __init__(self, config: dict):
        # In general it's hard to know if the user needs an API key or which environment variables to set
        # We do a simple check here for the default case (gpt- models from openai).
        self.config = config
        if "gpt-" in config.get("llm_model"):
            env_api_key = os.getenv("OPENAI_API_KEY")
            config_api_key = config.get("llm_api_key")
            if config_api_key:
                os.environ["OPENAI_API_KEY"] = config_api_key
            elif not env_api_key:
                print(
                    "It looks like you're using a GPT model without an API key. "
                    "You can add your API key by setting the OPENAI_API_KEY environment variable "
                    "or by adding an llm_api_key field to ~/.rawdog/config.yaml. "
                    "If this was intentional, you can ignore this message."
                )

        self.conversation = [
            {"role": "system", "content": script_prompt},
            {"role": "system", "content": script_examples},
            {"role": "system", "content": EnvInfo().render_prompt()},
        ]

    def get_response(
        self,
        messages: list[dict[str, str]],
        stream=False,
    ) -> str:
        base_url = self.config.get("llm_base_url")
        model = self.config.get("llm_model")
        temperature = self.config.get("llm_temperature")
        custom_llm_provider = self.config.get("llm_custom_provider")

        log = {
            "model": model,
            "prompt": messages[-1]["content"],
            "response": None,
            "cost": None,
        }
        try:
            response = completion(
                base_url=base_url,
                model=model,
                messages=messages,
                temperature=float(temperature),
                custom_llm_provider=custom_llm_provider,
                stream=stream,
            )
            if stream:
                text = ""
                for part in response:
                    content = part.choices[0].delta.content
                    if content:
                        print(content, end="")
                        text += content
            else:
                text = (response.choices[0].message.content) or ""
            self.conversation.append({"role": "assistant", "content": text})
            log["response"] = text
            if custom_llm_provider:
                cost = 0
            else:
                cost = (
                    completion_cost(model=model, messages=messages, completion=text)
                    or 0
                )
            log["cost"] = f"{float(cost):.10f}"
            metadata = {
                "model": model,
                "cost": log["cost"],
            }
            log_conversation(self.conversation, metadata=metadata)
            return text
        except Exception as e:
            log["error"] = str(e)
            print(f"Error:\n", str(log))
            raise e
        finally:
            with open(rawdog_log_path, "a") as f:
                f.write(json.dumps(log) + "\n")

    def get_script(self, prompt: Optional[str] = None, stream=False):
        if prompt:
            self.conversation.append({"role": "user", "content": prompt})
        response = self.get_response(self.conversation, stream=stream)
        return parse_script(response)
