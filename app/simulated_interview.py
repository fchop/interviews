import logging
from parameters import INTERVIEW_PARAMETERS, OPENAI_API_KEY
from core.manager import InterviewManager
from core.agent import LLMAgent
from core.sim_agent import SimulatedIntervieweeAgent
from database.file import FileWriter
from scripts.Clean_interview import clean_interview_output

# Setup logging
logging.basicConfig(level=logging.INFO)

# Pick your interview ID
interview_id = "Social_Assistance"
session_id = "sim - kenyan"

 # SIMULATED RESPONDENT
simulated_persona =  """
        You are a rich person in a rich European country where unconditional cash transfers are prevalent as part of government welfare. 
        Keep any responses to a max of 100 words. 
        You must respond exactly to the question being asked.
		You have very little knowledge, and so feel free to ask 
        questions about transfer programmes if you aren't sure.
        Speak in a heavy kenyan accent and intonation. If told to respond with a number,
        you must respond only with a single number"""

# Load config
parameters = INTERVIEW_PARAMETERS[interview_id]

# Instantiate agents
db = FileWriter()
interview = InterviewManager(db, session_id)
interview.begin_session(parameters)

interviewer = LLMAgent(api_key=OPENAI_API_KEY)
interviewer.load_parameters(parameters)

sim_user = SimulatedIntervieweeAgent(api_key=OPENAI_API_KEY, persona_prompt=simulated_persona)

interview.add_chat_to_session("What comes to mind when you think of the poorest in your country?", type="question")
interview.add_chat_to_session("They work really hard.", type="answer")

# Start interview loop
while not interview.is_terminated():
    if interview.get_current_topic() > len(parameters['interview_plan']):
        interview.terminate("exceeded_topic_index")
        print("Interview terminated: exceeded_topic_index")
        break

    current_topic = interview.get_current_topic()
    current_question = interview.get_current_topic_question()
    topic_data = parameters['interview_plan'][current_topic - 1]
    num_questions = topic_data['length']
    num_topics = len(parameters['interview_plan'])
    
    on_last_topic = current_topic == num_topics
    on_last_question = current_question >= num_questions

    print(f"\n--- Topic {current_topic}/{num_topics}, Question {current_question}/{num_questions} ---")

    # Check if we're at the end of the interview (last topic, last question)
    if on_last_topic and on_last_question:
        # Handle closing questions
        next_question = interview.get_final_question()
        interview.update_closing()
        if not next_question:
            # No more closing questions
            interview.terminate("completed")
            print("Interview terminated: completed")
            break
        message = next_question
        
    elif on_last_question:
        # Transition to next topic
        message, summary = interviewer.transition_topic(interview.get_history(), interview.current_state)
        interview.update_transition(summary)
        
    else:
        # Continue within current topic
        message = interviewer.probe_within_topic(interview.get_history(), interview.current_state)
        interview.update_probe()
    
    # Handle message that might be a dict (e.g., with image_url)
    if isinstance(message, dict):
        message_text = message.get("text", "")
        logging.info(f"Interviewer: {message_text} [Image: {message.get('image_url', 'N/A')}]")
        interview.add_chat_to_session(message_text, type="question")
        # For simulated respondent, just acknowledge the image
        user_reply = sim_user.respond(interview.get_history(), message_text)
    else:
        message_text = message
        logging.info(f"Interviewer: {message_text}")
        interview.add_chat_to_session(message_text, type="question")
        # Simulated response
        user_reply = sim_user.respond(interview.get_history(), message_text)
    
    logging.info(f"Simulated Respondent: {user_reply}")
    interview.add_chat_to_session(user_reply, type="answer")

# Save final session
interview.update_session()
logging.info("Simulated interview complete.")

# Clean the output
clean_interview_output(session_id=session_id)
