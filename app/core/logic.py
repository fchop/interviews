import logging
import os
from parameters import INTERVIEW_PARAMETERS, OPENAI_API_KEY
from core.manager import InterviewManager
from core.agent import LLMAgent
from core.auxiliary import extract_programme_choice


def connect_to_database():
    """ Instantiate specific backend database. """
    if os.getenv("DATABASE") == "DYNAMODB":
        # For AWS, leverage Dynamo database
        from database.dynamo import DynamoDB
        return DynamoDB(os.environ['DYNAMO_TABLE'])
    from database.file import FileWriter
    return FileWriter()

agent = LLMAgent(OPENAI_API_KEY)
db = connect_to_database()

def load_interview_session(session_id:str) -> dict:
    """ Return interview session history to user. """
    return db.load_remote_session(session_id)

def delete_interview_session(session_id:str):
    """ Delete existing interview saved to database. """
    db.delete_remote_session(session_id)

def resume_interview_session(session_id:str, interview_id:str, user_message:str) -> InterviewManager:
    """ Return InterviewManager object of existing session. """
    interview = InterviewManager(db, session_id)
    interview.resume_session(INTERVIEW_PARAMETERS[interview_id])
    logging.info("Generating next question for session '{}', user message '{}'".format(
        session_id, 
        user_message
    ))   
    return interview

def begin_interview_session(session_id:str, interview_id:str) -> dict:
    """ Return response with starting question of new interview session. """
    if not INTERVIEW_PARAMETERS.get(interview_id):
        raise ValueError(f"Invalid interview parameters '{interview_id}' specified!")
    parameters = INTERVIEW_PARAMETERS[interview_id]
    interview = InterviewManager(db, session_id)
    interview.begin_session(parameters)
    message = parameters['first_question']
    interview.add_chat_to_session(message, type='question')
    logging.info("Beginning {} interview session '{}' with prompt '{}'".format(
        interview_id, 
        session_id, 
        message
    ))
    return {'session_id':session_id, 'interview_id':interview_id, 'message':message}

def retrieve_sessions(sessions:list=None) -> dict:
    """ Return specified or all existing interview sessions. """
    return db.retrieve_sessions(sessions)

def transcribe(audio:str) -> dict:
    """ Return audio file transcription using OpenAI Whisper API """
    logging.critical(f"Audio is: {type(audio)}...")
    transcription = agent.transcribe(audio)
    logging.info(f"Returning transcription text: '{transcription}'")
    return {'transcription':transcription}

def next_question(session_id:str, interview_id:str, user_message:str=None) -> dict:
    try:
        interview = resume_interview_session(session_id, interview_id, user_message)
        parameters = interview.parameters
    except AssertionError:
        return begin_interview_session(session_id, interview_id)

    if interview.is_terminated():
        return {'session_id': session_id, 'message': parameters['termination_message']}

    agent.load_parameters(parameters)

    if parameters.get('moderate_answers') and parameters.get('moderator'):
        on_topic = agent.review_answer(user_message, interview.get_history())
        if not on_topic:
            interview.flag_risk(user_message)
        if interview.flagged_too_often():
            interview.update_session()
            return {'session_id': session_id, 'message': parameters['flagged_message']}
        if not on_topic:
            interview.update_session()
            return {'session_id': session_id, 'message': parameters['off_topic_message']}

    interview.add_chat_to_session(user_message, type="answer")

    #Print out topics and current topic
    current_topic = interview.get_current_topic()
    current_question_idx = interview.get_current_topic_question()
    print(f"Current topic index: {current_topic}. Current question index: {current_question_idx}")
    topic_data = parameters['interview_plan'][current_topic - 1]
    if current_topic < len(parameters['interview_plan']):
        next_topic_data = parameters['interview_plan'][current_topic]
        print(f"Next topic data: {next_topic_data['topic']}")
    else:
        next_topic_data = None
        print("No next topic data (this is the last topic).")

    print(f"Current topic data: {topic_data['topic']}")
    print(f"Next topic data: {next_topic_data['topic'] if next_topic_data else 'None'}")

    if "explain_programmes" in topic_data.values():
        programme_map = interview.current_state.get('programme_description_map', {})
        programme_explanation = extract_programme_choice(user_message, programme_map)
        if programme_explanation:
            interview.current_state["programme_explanation"] = programme_explanation

    if "scripted_message_favourite_programme" in topic_data:
        programme_map = interview.current_state.get("programme_map", {})
        favourite = extract_programme_choice(user_message, programme_map)
        if favourite:
            interview.current_state["favourite_programme"] = favourite

    if "explain_programmes" in topic_data.values() and user_message.strip().lower() in ["ok", "ok.", "okay", "that's clear", "got it", "no"]:
        next_question, summary = agent.transition_topic(interview.get_history(), interview.current_state)
        interview.update_transition(summary)
        if isinstance(next_question, dict):
            interview.add_chat_to_session(next_question["text"], type="question")
            return {
                "session_id": session_id,
                "message": next_question["text"],
                "image_url": next_question.get("image_url")
            }
        else:
            interview.add_chat_to_session(next_question, type="question")
            return {
                "session_id": session_id,
                "message": next_question
            }
    #-----------------------------------
    # Invoke AVA
    #-----------------------------------
    if topic_data["topic"] == "Talk with AVA":
        pass
    #-----------------------------------
    # Continue as normal
    #-----------------------------------
    num_topics = len(parameters['interview_plan'])
    current_topic_idx = interview.get_current_topic()
    on_last_topic = current_topic_idx == num_topics

    current_question_idx = interview.get_current_topic_question()
    num_questions = parameters['interview_plan'][current_topic_idx - 1]['length']
    on_last_question = current_question_idx >= num_questions

    if on_last_topic and on_last_question:
        next_question = interview.get_final_question()
        interview.update_closing()
        if not next_question:
            interview.terminate()
            interview.update_session()
            return {'session_id': session_id, 'message': parameters['end_of_interview_message']}

    elif on_last_question:
        transition_response, summary = agent.transition_topic(interview.get_history(), interview.current_state)
        interview.update_transition(summary)

        if isinstance(transition_response, dict):
            interview.add_chat_to_session(transition_response["text"], type="question")
            return {
                "session_id": session_id,
                "message": transition_response["text"],
                "image_url": transition_response.get("image_url")
            }
        else:
            interview.add_chat_to_session(transition_response, type="question")
            return {
                "session_id": session_id,
                "message": transition_response
            }

    else:
        next_question = agent.probe_within_topic(interview.get_history(), interview.current_state)
        interview.update_probe()

    interview.add_chat_to_session(next_question, type="question")

    if parameters.get('moderate_questions'):
        if agent.review_question(next_question):
            interview.terminate(reason="question_flagged")
            interview.update_session()
            return {'session_id': session_id, 'message': parameters['end_of_interview_message']}
    
    
    return {'session_id': session_id, 'message': next_question}