from datetime import datetime
import logging
import random
from core.auxiliary import get_randomised_programmes
from core.AVA import get_llm_response

programmes = [
    ("Conditional Cash Transfers (CCTs)", "These provide money..."),
    ("Unconditional Cash Transfers (UCTs)", "These give money..."),
    ("Public Works Programmes", "These offer temporary employment..."),
    ("In-Kind Transfers", "Recipients receive goods..."),
    ("School Feeding Programmes", "These provide free meals...")
]

class InterviewManager(object):
    """
    Class to manage the conversation history for an interview 
    between the user and the AI-interviewer.

    Args:
        client: database manager
        session_id: (str) unique interview session key
    """
    def __init__(self, client, session_id:str):
        self.client = client
        self.session_id = session_id
    

    def begin_session(self, parameters:dict):
        """ Set starting interview session variables. """
        logging.info(f"Starting new session '{self.session_id}'")
        programmes, programme_map, programme_description_map = get_randomised_programmes()

        self.history = []           # List of 'states', i.e. messages
        self.current_state = {
            'order': 0,                         # index of message
            'session_id': self.session_id,      # always store session_id
            'topic_idx': 1,                     # topic index
            'question_idx': 1,                  # within-topic question index
            'finish_idx': 1,                    # closing question index
            'flagged_messages': 0,              # count of flagged messages
            'terminated': False,                # whether termination signal been sent
            'summary': '',                      # running summary
            'type': 'question',                 # question or answer
            'content': None,                    # content
            'programmes':programmes,
            'programme_map': programme_map,
            'programme_description_map':programme_description_map
        }
        self.parameters = parameters

    def resume_session(self, parameters:dict):
        """ Load (remote) history into current Interview object. """
        self.history = self.client.load_remote_session(self.session_id)
        assert len(self.history) >= 1 
        assert self.history[-1].get('session_id') == self.session_id
        # Set current state equal to last
        self.current_state = self.history[-1].copy()
        self.parameters = parameters
        logging.info(f"Resumed existing interview session '{self.session_id}'")

    def get_history(self):
        """ Return interview session history. """
        return self.history

    def is_terminated(self) -> bool:
        """ If interview has been terminated. """
        return self.current_state['terminated']

    def flag_risk(self, message:str):
        """ Flag possible security risk. """
        logging.warning(f"Flagging message '{message}' for possible risk...")
        self.current_state["flagged_messages"] += 1

    def flagged_too_often(self) -> bool:
        """ Check if the conversation has been flagged too often. """
        if self.current_state['flagged_messages'] >= self.parameters.get('max_flags_allowed', 3):
            self.terminate("security_flags_exceeded")
            return True        
        return False

    def add_chat_to_session(self, message:str, type:str):
        """ Add to chat transcript to remote database """ 
        self.current_state['order'] += 1
        self.current_state['time'] = str(datetime.now()) 
        self.current_state['content'] = message
        self.current_state['type'] = type
        self.history.append(self.current_state.copy())
        self.client.update_remote_session(self.session_id, self.history)


    def terminate(self, reason:str="end_of_interview"):
        """ Record termination of interview. """
        self.current_state["terminated"] = True
        logging.info(f"Terminating interview because: '{reason}'")

    def update_summary(self, summary:str):
        """ Update summary of prior interview. """
        self.current_state["summary"] = summary

    def get_current_topic(self) -> int:
        """ Return topic index. """
        return min(int(self.current_state["topic_idx"]), len(self.parameters['interview_plan']))

    def get_current_topic_question(self) -> int:
        """ Return question index within topic. """
        return int(self.current_state["question_idx"])

    def get_final_question(self) -> str:
        """ Get next "final" (i.e. closing) interviewer question/comment. """
        final_questions = self.parameters.get('closing_questions', [])
        try:
            out = final_questions[int(self.current_state["finish_idx"]) - 1]
        except IndexError:
            out = ""
        else:
            # Increment counter of which 'final' question we are on
            self.current_state["finish_idx"] += 1
        return out

    def update_transition(self, summary:str):
        """ 
        Having transitioned, update topic counter (and reset question). 
        
        If summary agent is provided, also update interview summary of 
        prior topics covered for future context.
        """
        self.current_state["question_idx"] = 1  
        self.current_state["topic_idx"] += 1

        logging.info(f"Moved to topic index: {self.current_state['topic_idx']}")

        if self.parameters.get('summary'):
            self.update_summary(summary)

        

    def update_closing(self):
        self.current_state["question_idx"] = 99  
        self.current_state["topic_idx"] = 99

    def update_probe(self):
        """ Having probed within topic, simply increment question counter. """ 
        self.current_state["question_idx"] += 1  

    def update_session(self):
        """ Update current state in remote database """ 
        self.history[-1] = self.current_state
        self.client.update_remote_session(self.session_id, self.history)
   
    @staticmethod
    def ask_ava(user_message: str) -> str:
        """
        Send a question to the AVA LLM and return its response.
        """
        messages = [
            {"role": "system", "content": "You are a helpful assistant knowledgeable about evidence on poverty programs. Be very brief in your response."},
            {"role": "user", "content": user_message}
        ]
        return get_llm_response(messages)