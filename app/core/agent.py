import logging
from core.auxiliary import (
    execute_queries, 
    fill_prompt_with_interview, 
    chat_to_string
)
from io import BytesIO
from base64 import b64decode
from openai import OpenAI


class LLMAgent(object):
    """ Class to manage LLM-based agents. """
    def __init__(self, api_key, timeout:int=30, max_retries:int=3):
        self.client = OpenAI(api_key=api_key, timeout=timeout, max_retries=max_retries)
        logging.info("OpenAI client instantiated. Should happen only once!")

    def load_parameters(self, parameters:dict):
        """ Load interview guidelines for prompt construction. """
        self.parameters = parameters

    def transcribe(self, audio) -> str:
        """ Transcribe audio file. """
        audio_file = BytesIO(b64decode(audio))
        audio_file.name = "audio.webm"

        response = self.client.audio.transcriptions.create(
          model="whisper-1", 
          file=audio_file,
          language="en" # English language input
        )
        return response.text

    @staticmethod
    def is_legacy_model(model:str) -> bool:
        """ GPT-4-era models accept `temperature`; GPT-5/GPT-6 models only accept the default and use reasoning instead. """
        return model.startswith(("gpt-4", "gpt-3.5", "chatgpt-"))

    def construct_query(self, tasks:list, history:list, user_message:str=None) -> dict:
        """
        Construct OpenAI API chat-completions query for each task,
        defaults to `gpt-4o-mini` model, 300 token answer limit, and temperature of 0.
        For details see https://platform.openai.com/docs/api-reference/chat.

        Per-agent parameters in `parameters.py`:
        - model (str):            any chat-completions model, e.g. "gpt-4o", "gpt-4.1", "gpt-5.4", "gpt-6-sol".
        - max_tokens (int):       output limit, sent as `max_completion_tokens` (accepted by all models).
        - temperature (float):    only sent to GPT-4-era models; GPT-5/6 models reject non-default values.
        - reasoning_effort (str): GPT-5/6 models only, e.g. "none", "low", "medium", "high". Defaults to "none"
                                  so the interviewer answers quickly and reasoning tokens do not eat the output budget.
        """
        queries = {}
        for task in tasks:
            params = self.parameters[task]
            model = params.get('model', 'gpt-4o-mini')
            max_tokens = params.get('max_tokens', 300)
            query = {
                "messages": [{
                    "role":"user",
                    "content": fill_prompt_with_interview(
                        params['prompt'],
                        self.parameters['interview_plan'],
                        history,
                        user_message=user_message
                    )
                }],
                "model": model,
            }
            if self.is_legacy_model(model):
                query["max_completion_tokens"] = max_tokens
                query["temperature"] = params.get('temperature', 0)
            else:
                # Reasoning models need headroom even for one-word answers (e.g. the moderator's yes/no).
                query["max_completion_tokens"] = max(max_tokens, 16)
                # `extra_body` passes the parameter through regardless of the installed openai SDK version.
                query["extra_body"] = {"reasoning_effort": params.get('reasoning_effort', 'none')}
            queries[task] = query
        return queries

    def review_answer(self, message:str, history:list) -> bool:
        """ Moderate answers: Are they on topic? """
        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(['moderator'], history, message)
        )
        return "yes" in response["moderator"].lower()

    def review_question(self, next_question:str) -> bool:
        """ Moderate questions: Are they flagged by the moderation endpoint? """
        response = self.client.moderations.create(
            model="omni-moderation-latest",
            input=next_question,
        )
        return response.to_dict()["results"][0]["flagged"]
        
    def probe_within_topic(self, history:list) -> str:
        """ Return next 'within-topic' probing question. """
        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(['probe'], history)
        )
        return response['probe']

    def transition_topic(self, history:list) -> tuple[str, str]:
        """ 
        Determine next interview question transition from one topic
        cluster to the next. If have defined `summarize` model in parameters
        will also get summarization of interview thus far.
        """
        summarize = self.parameters.get('summarize')
        tasks = ['summary','transition'] if summarize else ['transition']
        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(tasks, history)
        )
        return response['transition'], response.get('summary', '')
