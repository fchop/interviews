"""
################################################
###           DOCUMENTATION                  ###
################################################

This file allows users to specificy all parameters of the AI interviewer application. The parameters are stored in a
dictionary called INTERVIEW_PARAMETERS. You can specify multiple parameter sets for different types of interviews.
For example, one could randomize people into different interviews (e.g. about the stock market or about voting behaviors).
Each parameter set can be identified with a custom key (e.g. "STOCK_MARKET" or "VOTING"). You have to supply these
keys when making requests to the AI interviewer application to tell the application which parameter set to use.

We provide the parameter sets used in our paper as an example from which to build your own interview structure.
We also provide a template for additional interview configurations. You can add as many parameter sets as you like.

We describe all parameters that should be included in a parameter set below:


################################################
###           GENERAL PARAMETERS             ###
################################################

0) META DATA (OPTIONAL): The following parameters allow you to provide additional information about the interview configuration.
						 This may help with remembering the purpose of the configuration or provide additional context for yourself.
- _name (str): 			A name for the interview configuration (e.g. "STOCK_MARKET" or "VOTING")
- _description (str): 	A description of the interview configuration and its purpose.


1) OPTIONAL FEATURES: The following parameters active optional features of the AI interviewer application.

- summarize (book): 				whether to active the summarization agent for the interview (default: True)
- moderate_answers (bool): 			Whether the moderator agent should review answers from the interviewee and potentially flag them (default: True)
- moderate_questions (bool): 		whether AI-generated interview questions should be reviewed with OpenAI's moderation endpoint
									before sending them back to the interviewee (default: True)


2) INTERVIEW STRUCTURE and PRE-DETERMINED MESSAGES: The following parameters define the structure of the interview and
the messages that are displayed to the interviewee at various stages of the interview if specific conditions are met.
The first_question and the interview_plan variable are the most critical parameters.

- first_question (str): 			The opening question for the interview.
									All interviews will start with this message.
- interview_plan (list): 			The interview plan for the interviews. This is a list of dictionaries that define
									the scope and length of each subtopic
									of the following form [{"topic": str, "length": int}, ...] where:
									- topic (str): 		a description of the subtopic to be covered in the interview
									- length (int): 	the total number of questions to ask for this subtopic
									The topic description can be short or long, depending on the level of detail you want to provide.
									It could even mention specific follow-up questions that should be asked in specific circumstances.
									Feel free to experiment with the number of topics, the number of questions per topic,
									and the level of detail in the topic descriptions.
- closing_questions (str): 			List of pre-determined questions or comments (if any) with which to end the interview.
									An empty list is allowed.
- end_of_interview_message (str): 	Message to display to interviewees at the end of the interview (e.g. "Thank you for participating!")
									The messages ends with "---END---" to signal the front-end JavaScript the end of the interview.
									Remove this if you have a different way of managing the front-end.
- termination_message (str): 		Message to display to interviewees in the event the interviewee responds to an already concluded interview
- off_topic_message (str): 			Message to display to interviewees if their response has been flagged by the moderator agent
- flagged_message (str): 			Message to display to interviewees if their response has been flagged too often by the
									moderator agent (and the interview was terminated)
- max_flags_allowed (int): 			The maximum number of flagged messages allowed before an interview is terminated (default: 3)



################################################
### AI AGENT-SPECIFIC PARAMETERS AND PROMPTS ###
################################################

1) AGENT PARAMETERS:
Each AI agent (e.g., summary, transition, probe, moderator) has its own set of parameters that are provided as a dictionary with key-value pairs.
	- summary (dict): Parameters defining the behavior of the summary agent. 
	- transition (dict): Parameters defining the behavior of the transition agent.
	- probe (dict): Parameters defining the behavior of the probing agent.
	- moderator (dict): Parameters defining the behavior of the moderator agent.

Note: If you deactivate an optional agent (e.g. summary, moderator) or you have an interview with a single topic that does not require a topic transition,
you do not need to provide the corresponding agent parameters. For example, you could remove the "summary" dictionary entirely if you don't summarize
previous parts of the interview between topic transitions (remember to set "summarize" to False in this case).

2. DICTIONARY ELEMENTS:
Each of the above dictionaries should specify the following set of parameters:
	- prompt (str): the prompt that describes the task and desired behavior of the agent (feel free to modify according to your needs)
	- max_tokens (int): the maximum number of completion tokens the agent can generate in its response (default: 1000)
	- temperature (float): the temperature parameter for the LLM (default: 0.9)
	- model (str): the model to use for the agent (default: gpt-4o)

3. DETAILS ABOUT THE PROMPTS:
The prompts for the AI agent include placeholder variables that are programmatically replaced based on the current state of the interview.
The following placeholderes can be included in any prompt by including them in curly brackets (e.g. writing {topics} to include the list of topics
at the specified place in the prompt)):
 - {current_topic_history}: All verbatim questions and responses that are part of the current interview topic (see interview_plan variable).
                            These messages are formatted as follows:
								Interviewer: {question}
								Interviewee: {answer}
								Interviewer: {question} etc.
							This placeholder is typically used by all agents (except the moderator).
							It should not be omitted from the prompts.
 - {summary}: 				Summary of the interview up to the current interview topic (see *interview_plan* variable).
			  				Example: If the interview is currently in topic 3 of the *interview_plan*, then {summary} would cover topics 1 and 2.
							The messages for topic 3 would be included in full via the {current_topic_history} placeholder.
							If summarization has been turned off, then {summary} would contain the full conversation on topics 1 and 2
							in the same format as {current_topic_history}.
							This placeholder is used by all agents (except moderator).
 - {topics}:  				The list of all topic descriptions from the interview_plan variable
 							(e.g. all values of "topic" from the interview_plan variable)
							This placeholder is used by the summary agent to provide an overview of the interview structure.
 - {current_topic}: 		Description of the current interview topic as defined in the interview_plan
 							variable (e.g. the value of "topic" in the interview_plan).
							This placeholder is primarily used by the probing agent and the summary agent.
 - {next_interview_topic}: 	Description of the next interview topic as defined in the interview_plan variable
 							(e.g. the value of "topic" in the interview_plan for the next topic)
							This placeholder is typically used only by the transition agent to inform the agent
							about the next topic it should transition to.

See our paper for more details about how the individual parts of the AI interviewer application work.
"""


import os
from dotenv import load_dotenv

load_dotenv()  # This reads from the .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


INTERVIEW_PARAMETERS = {
	
	# Social Assistance interview
    
	# TEMPLATE FOR ADDITIONAL INTERVIEW CONFIGURATIONS:
	"Social_Assistance": {
		# META DATA (OPTIONAL):
		"_name": "social_assistance",
		"_description": "interview structure to elicite opinions on social assistence programmes",
		# OPTIONAL FEATURES:
		"moderate_answers": False,
		"moderate_questions": False,
		"summarize": True,
		"max_flags_allowed": 3,
		# INTERVIEW STRUCTURE:
		"first_question": "I am interested in learning more about your views on poor people in your country. Can you describe what comes to mind when you think of the poorest in your country?",
		
		"interview_plan": [
			{
				"topic":"Explore the perceptions that the interviewee has of poor people in their country and understand why they have these perceptions. Do not yet mention social assistance programmes.",
				"length":3
                
			},
            
			# {
			# 	"topic": "Talk with AVA",
			# 	"length":2,
			# 	"ava_section": True
			# },
            
			{
                "topic": "Programme evidence",
				"length": 2,
                "type": "image_only",
				"image_filename": "transfers.png"
					
			},
            
			{
				"topic":"Discuss with the interviewee whether they think that the poor can be helped out of poverty (poverty trap argument), or whether they are inherently lower productivity and will be stuck there for life. Only ask one question at a time. Still do not mention social assistance programmes.",
				"length":2
			},
            
            
            
			{
				"topic": "Explain the types of social assistance.",
				"length":5,
				"dynamic_script": "explain_programmes",
                	
			},
            
            {
				"topic": "Ask the respondent of the social assistance programmes described which programme do they support the most?",
				"length":1,
                "scripted_message_favourite_programme": "Of these 5 programmes, please indicate which programme you prefer. Your response must be a single number from 1-5 corresponding to the programmes above"
			},
            
            {
				"topic": "Start this topic inidicating which social assistance programme they choose. Explore why they chose the specific programme as the one they support the most. What features of it appeal to them?",
				"length":1,
                "dynamic_script": "Repeat programme choice"
			},
            

            
			{
				"topic": "Converse with the interviewee about the effectiveness of the programme they selected.",
				"length":3,
                #"treatment": "programme_effectiveness",
					
			},
            
            
			{
				"topic": "Ask the respondent again what their preferred social assistance programme is in light of the evidence, and why?",
				"length":1
			},

			# etc.
		],
		"closing_questions": [
			"As we conclude our discussion, are there any perspectives or information you feel we haven't addressed that you'd like to share?",
			"Reflecting on our conversation, what would you identify as the main social assistance programme you support, and why?",
			# etc.
		],
		# OTHER PRE-DETERMINED MESSAGES:
		"termination_message": "The interview is over. Please proceed to the next page.---END---",
		"flagged_message": "Please note, too many of your messages have been identified as unusual input. Please proceed to the next page.---END---",
		"off_topic_message": "I might have misunderstood your response, but it seems you might be trying to steer the interview off topic or that you have provided me with too little context. Can you please try to answer the question again in a different way, preferably with more detail, or say so directly if you prefer not to answer the question?",
		"end_of_interview_message": "Thank you for sharing your insights and experiences today. Your input is invaluable to our research. Please proceed to the next page.---END---",
		# PROMPTS FOR THE AI AGENTS:
		"summary": {
			"prompt": 
            	"""
				CONTEXT: You're an AI proficient in conducting qualitative interviews for academic research. You conduct a qualitative interview with the goal of learning the interviewee's thoughts on different social assistance programmes for the poor.

				INPUTS:
				A. Interview Plan:
				{topics}

				B. Previous Conversation Summary:
				{summary}

				C. Current Topic:
				{current_topic}

				D. Current Conversation:
				{current_topic_history}

				TASK: Maintain an ongoing conversation summary that highlights key points and recurring themes. The goal is to ensure that future interviewers can continue exploring the perceptions and thoughts without having to read the full interview transcripts.

				GUIDELINES:
				1. Relevance: Prioritize and represent information based on their relevance and significance to understanding the interviewee's reasons for thinking how they do about the poor and social assistance programmes.
				2. Update the summary: Integrate the Current Conversation into the Previous Conversation Summary, ensuring a coherent and updated overview. Avoid adding redundant information.
				3. Structure: Your summary should follow the interview's chronology, starting with the first topic. Allocate space in the summary based on relevance for the research objective, not just its recency.
				4. Neutrality: Stay true to the interviewee's responses without adding your own interpretations of inferences.
				5. Sensitive topics: Document notable emotional responses or discomfort, so subsequent interviewers are aware of sensitive areas.
				6. Reasons: Keep an up-to-date overview of the interviewee's reasons for supporting a certain social assistance programme.

				YOUR RESPONSE: Your summary should be a succinct yet comprehensive account of the full interview, allowing other interviewers to continue the conversation.

			""",
			"temperature":0.7,
			"max_tokens": 1000,
			"model": "gpt-4o"
		},
        
		"transition": {
			"prompt": """

			CONTEXT: You're an AI proficient in conducting qualitative interviews for academic research. You conduct a qualitative interview with the goal of learning the interviewee's thoughts on different social assistance programmes for the poor.

				INPUTS:
				A. Previous Conversation Summary:
				{summary}

				B. Current Conversation:
				{current_topic_history}

				C. Next Interview Topic:
				{next_interview_topic}

				TASK: Introducing the Next Interview Topic from the interview plan by asking a transition question.

				GUIDELINES:
				1. Open-endedness: Always craft open-ended questions ("how", "what", "why") that allow detailed and authentic responses without limiting the interviewee to  "yes" or "no" answers.
				2. Natural transition: To make the transition to a new topic feel more natural and less abrupt, you may use elements from the Current Conversation and Previous Conversation Summary to provide context and a bridge from what has been discussed to what will be covered next.
				3. Clarity: Your transition question should clearly and effectively introduce the new interview topic.

				YOUR RESPONSE: Please provide the most suitable next probing question or statement in the interview. Do not prefix the question with "Interviewer: or similar.
			""",
            
			"temperature": 0.7,
			"model": "gpt-4o",
			"max_tokens": 300
		},
        
		"probe": {
			"prompt": """

				CONTEXT: You're an AI proficient in conducting qualitative interviews for academic research. You conduct a qualitative interview with the goal of learning the interviewee's thoughts on different social assistance programmes for the poor.
                INPUTS:
                
				A. Previous Conversation Summary:
				{summary}

				B. Current Interview Topic:
				{current_topic}

				C. Current Conversation:
				{current_topic_history}

				TASK: Your task is to formulate the next probing question or explanation for the Current Conversation. The question should align with the Current Interview Topic, helping us to better understand and systematically explore the interviewee's perceptions and reasoning of social assistance programmes.

				GENERAL GUIDELINES:
				1. Open-endedness: Always craft open-ended questions ("how", "what", "why") that allow detailed and authentic responses without limiting the interviewee to  "yes" or "no" answers.
				2. Neutrality: Use questions that are unbiased and don't lead the interviewee towards a particular answer. Don't judge or comment on what was said. It's also crucial not to offer any financial advice.
				3. Respect: Approach sensitive and personal topics with care. If the interviewee signals discomfort, respect their boundaries and move on.
				4. Relevance: Prioritize themes central to the interviewee's opinion on the poor. Don't ask for overly specific examples, details, or experiences that are unlikely to reveal new insights.
				5. Focus: Generally, avoid recaps. However, if revisiting earlier points, provide a concise reference for context. Ensure your probing question targets only one theme or aspect.
                6. Never ask more the one question in a single response.
                

				PROBING GUIDELINES:
				1. Depth: Initial responses are often at a "surface" level (brief, generic, or lacking personal reflection). Follow up on promising themes hinting at depth and alignment with the research objective, exploring the interviewee's reasons, motivations, opinions, and beliefs. 
				2. Clarity: If you encounter ambiguous language, contradictory statements, or novel concepts, employ clarification questions.
				3. Flexibility: Follow the interviewee's lead, but gently redirect if needed. Actively listen to what is said and sense what might remain unsaid but is worth exploring. Explore nuances when they emerge; if responses are repetitive or remain on the surface, pivot to areas not yet covered in depth.
                4. If giving explanations at the request of the interviewee, there is no need to ask a question, other than, 'do you have other questions?'. If they respond "no", then move on to your next question.

				YOUR RESPONSE: Please provide the most suitable next response in the interview. Do not prefix the question with "Interviewer: or similar.
                
		""",
			"temperature": 0.7,
			"model": "gpt-4o",
			"max_tokens": 300
		},
		"moderator": {
			"prompt": """

			You are monitoring a conversation that is part of an in-depth interview. The interviewer asks questions and the interviewee replies. The interview should stay on topic. The interviewee should try to respond to the question of the interviewer (but it is not important to answer all questions that are asked), express a wish to move on, or decline to respond. The interviewee is also allowed to say that they don't know, do not understand the question, or express uncertainty. Responses can be very short, as long as they have some connection with the question. The interviewee's response might contain spelling and grammar mistakes. Here is the last part of the conversation.

				Interviewer: '{question}'

				Interviewee: '{answer}'

				That is the end of the conversation. 

				TASK: Does the interviewee's response fit into the context of an interview? Importantly, please answer only with a single 'yes' or 'no'. 


		""",
			"model": "gpt-4o",
			"max_tokens": 2
		}
	},
    

	"Social_Assistance untreated": {
		# META DATA (OPTIONAL):
		"_name": "social_assistance",
		"_description": "interview structure to elicite opinions on social assistence programmes",
		# OPTIONAL FEATURES:
		"moderate_answers": True,
		"moderate_questions": True,
		"summarize": True,
		"max_flags_allowed": 3,
		# INTERVIEW STRUCTURE:
		"first_question": "I am interested in learning more about your views on poor people in your country. Can you describe what comes to mind when you think of the poorest in your country?",
		"interview_plan": [
			{
				"topic":"Explore the perceptions that the interviewee has of poor people in their country and understand why they have these perceptions. Do not yet mention social assistance programmes.",
				"length":4
			},
            
			{
				"topic": "Explain the types of social assistance.",
				"length":10,
				"dynamic_script": "explain_programmes"
					
					
			},
            
            {
				"topic": "Ask the respondent of the social assistance programmes described which programme do they support the most?",
				"length":1,
                "scripted_message_favourite_programme": "Of these 5 programmes, please indicate which programme you prefer. Your response must be a single number from 1-5 corresponding to the programmes above"
			},
            
            {
				"topic": "Start with: 'You selected [full name of selected social assistance programme]'. Explore why they chose the specific programme as the one they support the most. What features of it appeal to them?",
				"length":3
			},
            

			# etc.
		],
		"closing_questions": [
			"As we conclude our discussion, are there any perspectives or information you feel we haven't addressed that you'd like to share?",
			"Reflecting on our conversation, what would you identify as the main social assistance programme you support, and why?",
			# etc.
		],
		# OTHER PRE-DETERMINED MESSAGES:
		"termination_message": "The interview is over. Please proceed to the next page.---END---",
		"flagged_message": "Please note, too many of your messages have been identified as unusual input. Please proceed to the next page.---END---",
		"off_topic_message": "I might have misunderstood your response, but it seems you might be trying to steer the interview off topic or that you have provided me with too little context. Can you please try to answer the question again in a different way, preferably with more detail, or say so directly if you prefer not to answer the question?",
		"end_of_interview_message": "Thank you for sharing your insights and experiences today. Your input is invaluable to our research. Please proceed to the next page.---END---",
		# PROMPTS FOR THE AI AGENTS:
		"summary": {
			"prompt": 
            	"""
				CONTEXT: You're an AI proficient in conducting qualitative interviews for academic research. You conduct a qualitative interview with the goal of learning the interviewee's thoughts on different social assistance programmes for the poor.

				INPUTS:
				A. Interview Plan:
				{topics}

				B. Previous Conversation Summary:
				{summary}

				C. Current Topic:
				{current_topic}

				D. Current Conversation:
				{current_topic_history}

				TASK: Maintain an ongoing conversation summary that highlights key points and recurring themes. The goal is to ensure that future interviewers can continue exploring the perceptions and thoughts without having to read the full interview transcripts.

				GUIDELINES:
				1. Relevance: Prioritize and represent information based on their relevance and significance to understanding the interviewee's reasons for thinking how they do about the poor and social assistance programmes.
				2. Update the summary: Integrate the Current Conversation into the Previous Conversation Summary, ensuring a coherent and updated overview. Avoid adding redundant information.
				3. Structure: Your summary should follow the interview's chronology, starting with the first topic. Allocate space in the summary based on relevance for the research objective, not just its recency.
				4. Neutrality: Stay true to the interviewee's responses without adding your own interpretations of inferences.
				5. Sensitive topics: Document notable emotional responses or discomfort, so subsequent interviewers are aware of sensitive areas.
				6. Reasons: Keep an up-to-date overview of the interviewee's reasons for supporting a certain social assistance programme.

				YOUR RESPONSE: Your summary should be a succinct yet comprehensive account of the full interview, allowing other interviewers to continue the conversation.

			""",
			"temperature":0.7,
			"max_tokens": 1000,
			"model": "gpt-4o"
		},
        
		"transition": {
			"prompt": """

			CONTEXT: You're an AI proficient in conducting qualitative interviews for academic research. You conduct a qualitative interview with the goal of learning the interviewee's thoughts on different social assistance programmes for the poor.

				INPUTS:
				A. Previous Conversation Summary:
				{summary}

				B. Current Conversation:
				{current_topic_history}

				C. Next Interview Topic:
				{next_interview_topic}

				TASK: Introducing the Next Interview Topic from the interview plan by asking a transition question.

				GUIDELINES:
				1. Open-endedness: Always craft open-ended questions ("how", "what", "why") that allow detailed and authentic responses without limiting the interviewee to  "yes" or "no" answers.
				2. Natural transition: To make the transition to a new topic feel more natural and less abrupt, you may use elements from the Current Conversation and Previous Conversation Summary to provide context and a bridge from what has been discussed to what will be covered next.
				3. Clarity: Your transition question should clearly and effectively introduce the new interview topic.

				YOUR RESPONSE: Please provide the most suitable next probing question or statement in the interview. Do not prefix the question with "Interviewer: or similar.
			""",
            
			"temperature": 0.7,
			"model": "gpt-4o",
			"max_tokens": 300
		},
        
		"probe": {
			"prompt": """

				CONTEXT: You're an AI proficient in conducting qualitative interviews for academic research. You conduct a qualitative interview with the goal of learning the interviewee's thoughts on different social assistance programmes for the poor.
                INPUTS:
                
				A. Previous Conversation Summary:
				{summary}

				B. Current Interview Topic:
				{current_topic}

				C. Current Conversation:
				{current_topic_history}

				TASK: Your task is to formulate the next probing question or explanation for the Current Conversation. The question should align with the Current Interview Topic, helping us to better understand and systematically explore the interviewee's perceptions and reasoning of social assistance programmes.

				GENERAL GUIDELINES:
				1. Open-endedness: Always craft open-ended questions ("how", "what", "why") that allow detailed and authentic responses without limiting the interviewee to  "yes" or "no" answers.
				2. Neutrality: Use questions that are unbiased and don't lead the interviewee towards a particular answer. Don't judge or comment on what was said. It's also crucial not to offer any financial advice.
				3. Respect: Approach sensitive and personal topics with care. If the interviewee signals discomfort, respect their boundaries and move on.
				4. Relevance: Prioritize themes central to the interviewee's opinion on the poor. Don't ask for overly specific examples, details, or experiences that are unlikely to reveal new insights.
				5. Focus: Generally, avoid recaps. However, if revisiting earlier points, provide a concise reference for context. Ensure your probing question targets only one theme or aspect.
                6. Never ask more the one question in a single response.
                

				PROBING GUIDELINES:
				1. Depth: Initial responses are often at a "surface" level (brief, generic, or lacking personal reflection). Follow up on promising themes hinting at depth and alignment with the research objective, exploring the interviewee's reasons, motivations, opinions, and beliefs. 
				2. Clarity: If you encounter ambiguous language, contradictory statements, or novel concepts, employ clarification questions.
				3. Flexibility: Follow the interviewee's lead, but gently redirect if needed. Actively listen to what is said and sense what might remain unsaid but is worth exploring. Explore nuances when they emerge; if responses are repetitive or remain on the surface, pivot to areas not yet covered in depth.
                4. If giving explanations at the request of the interviewee, there is no need to ask a question, other than, do you have other questions. If they respond "no", then move on to your next question.

				YOUR RESPONSE: Please provide the most suitable next response in the interview. Do not prefix the question with "Interviewer: or similar.
                
		""",
			"temperature": 0.7,
			"model": "gpt-4o",
			"max_tokens": 300
		},
		"moderator": {
			"prompt": """

			You are monitoring a conversation that is part of an in-depth interview. The interviewer asks questions and the interviewee replies. The interview should stay on topic. The interviewee should try to respond to the question of the interviewer (but it is not important to answer all questions that are asked), express a wish to move on, or decline to respond. The interviewee is also allowed to say that they don't know, do not understand the question, or express uncertainty. Responses can be very short, as long as they have some connection with the question. The interviewee's response might contain spelling and grammar mistakes. Here is the last part of the conversation.

				Interviewer: '{question}'

				Interviewee: '{answer}'

				That is the end of the conversation. 

				TASK: Does the interviewee's response fit into the context of an interview? Importantly, please answer only with a single 'yes' or 'no'. 


		""",
			"model": "gpt-4o",
			"max_tokens": 2
		}
	},









































#-------------------------------------------
# Example used by Haaland and Chopra (2024)
#-------------------------------------------


	"STOCK_MARKET": {
		# META DATA (OPTIONAL):
		"_name": "STOCK_MARKET",
		"_description": "Interview structure to investigate stock market participation (or lack thereof).",
		# OPTIONAL FEATURES:
		"moderate_answers": True,
		"moderate_questions": True,
		"summarize": True,
		"max_flags_allowed": 3,
		# INTERVIEW STRUCTURE:
		"first_question": "I am interested in learning more about why you currently do not own any stocks or stock mutual funds. Can you help me understand the main factors or reasons why you are not participating in the stock market?",
		"interview_plan": [
			{
				"topic":"Explore the reasons behind the interviewee's choice to avoid the stock market.",
				"length":2
			},
			{
				"topic":"Delve into the perceived barriers or challenges preventing them from participating in the stock market.",
				"length":2
			},
			{
				"topic":"Explore a 'what if' scenario where the interviewee invest in the stock market. What would they do? What would it take to thrive? Probing questions should explore the hypothetical scenario.",
				"length":2
			},
			{
				"topic":"Prove for conditions or changes needed for the interviewee to consider investing in the stock market.",
				"length":2
			}
		],
		"closing_questions": [
			"As we conclude our discussion, are there any perspectives or information you feel we haven't addressed that you'd like to share?",
			"Reflecting on our conversation, what would you identify as the main reason you're not participating in the stock market?"
		],
		# OTHER PRE-DETERMINED MESSAGES:
		"termination_message": "The interview is over. Please proceed to the next page.---END---",
		"flagged_message": "Please note, too many of your messages have been identified as unusual input. Please proceed to the next page.---END---",
		"off_topic_message": "I might have misunderstood your response, but it seems you might be trying to steer the interview off topic or that you have provided me with too little context. Can you please try to answer the question again in a different way, preferably with more detail, or say so directly if you prefer not to answer the question?",
		"end_of_interview_message": "Thank you for sharing your insights and experiences today. Your input is invaluable to our research. Please proceed to the next page.---END---",
		# PROMPTS FOR THE AI AGENTS:
		"summary": { # for the summary agent
			"prompt": """
				CONTEXT: You're an AI proficient in summarizing qualitative interviews for academic research. You're overseeing the records of a semi-structured qualitative interview about the interviewee's reasons for not investing in the stock market.

				INPUTS:
				A. Interview Plan:
				{topics}

				B. Previous Conversation Summary:
				{summary}

				C. Current Topic:
				{current_topic}

				D. Current Conversation:
				{current_topic_history}

				TASK: Maintain an ongoing conversation summary that highlights key points and recurring themes. The goal is to ensure that future interviewers can continue exploring the reasons for non-participation without having to read the full interview transcripts.

				GUIDELINES:
				1. Relevance: Prioritize and represent information based on their relevance and significance to understanding the interviewee's reasons for not investing in the stock market.
				2. Update the summary: Integrate the Current Conversation into the Previous Conversation Summary, ensuring a coherent and updated overview. Avoid adding redundant information.
				3. Structure: Your summary should follow the interview's chronology, starting with the first topic. Allocate space in the summary based on relevance for the research objective, not just its recency.
				4. Neutrality: Stay true to the interviewee's responses without adding your own interpretations of inferences.
				5. Sensitive topics: Document notable emotional responses or discomfort, so subsequent interviewers are aware of sensitive areas.
				6. Reasons: Keep an up-to-date overview of the interviewee's reasons for non-participation.

				YOUR RESPONSE: Your summary should be a succinct yet comprehensive account of the full interview, allowing other interviewers to continue the conversation.
			""",
			"max_tokens": 1000,
			"model": "gpt-4o"
		},
		"transition": { # for the transition agent
			"prompt": """
				CONTEXT: You're an AI proficient in conducting qualitative interviews for academic research. You're guiding a semi-structured qualitative interview about the interviewee's reasons for not investing in the stock market.

				INPUTS:
				A. Previous Conversation Summary:
				{summary}

				B. Current Conversation:
				{current_topic_history}

				C. Next Interview Topic:
				{next_interview_topic}

				TASK: Introducing the Next Interview Topic from the interview plan by asking a transition question.

				GUIDELINES:
				1. Open-endedness: Always craft open-ended questions ("how", "what", "why") that allow detailed and authentic responses without limiting the interviewee to  "yes" or "no" answers.
				2. Natural transition: To make the transition to a new topic feel more natural and less abrupt, you may use elements from the Current Conversation and Previous Conversation Summary to provide context and a bridge from what has been discussed to what will be covered next.
				3. Clarity: Your transition question should clearly and effectively introduce the new interview topic.

				YOUR RESPONSE: Please provide the most suitable next transition question in the interview, without any other discussion, context, or remarks.
			""",
			"temperature": 0.7,
			"model": "gpt-4o",
			"max_tokens": 300
		},
		"probe": {  # for the probing agent
			"prompt": """
				CONTEXT: You're an AI proficient in conducting qualitative interviews for academic research. You conduct a qualitative interview with the goal of learning the interviewee's reasons for not investing in the stock market.

				INPUTS:
				A. Previous Conversation Summary:
				{summary}

				B. Current Interview Topic:
				{current_topic}

				C. Current Conversation:
				{current_topic_history}

				TASK: Your task is to formulate the next probing question for the Current Conversation. The question should align with the Current Interview Topic, helping us to better understand and systematically explore why the interviewee is not participating in the stock market.

				GENERAL GUIDELINES:
				1. Open-endedness: Always craft open-ended questions ("how", "what", "why") that allow detailed and authentic responses without limiting the interviewee to  "yes" or "no" answers.
				2. Neutrality: Use questions that are unbiased and don't lead the interviewee towards a particular answer. Don't judge or comment on what was said. It's also crucial not to offer any financial advice.
				3. Respect: Approach sensitive and personal topics with care. If the interviewee signals discomfort, respect their boundaries and move on.
				4. Relevance: Prioritize themes central to the interviewee's stock market non-participation. Don't ask for overly specific examples, details, or experiences that are unlikely to reveal new insights.
				5. Focus: Generally, avoid recaps. However, if revisiting earlier points, provide a concise reference for context. Ensure your probing question targets only one theme or aspect.

				PROBING GUIDELINES:
				1. Depth: Initial responses are often at a "surface" level (brief, generic, or lacking personal reflection). Follow up on promising themes hinting at depth and alignment with the research objective, exploring the interviewee's reasons, motivations, opinions, and beliefs. 
				2. Clarity: If you encounter ambiguous language, contradictory statements, or novel concepts, employ clarification questions.
				3. Flexibility: Follow the interviewee's lead, but gently redirect if needed. Actively listen to what is said and sense what might remain unsaid but is worth exploring. Explore nuances when they emerge; if responses are repetitive or remain on the surface, pivot to areas not yet covered in depth.

				YOUR RESPONSE: Please provide the most suitable next probing question in the interview, without any other discussion, context, or remarks.
			""",
			"temperature": 0.7,
			"model": "gpt-4o",
			"max_tokens": 300
		},
		"moderator": {  # for the moderator agent
			"prompt": """
				You are monitoring a conversation that is part of an in-depth interview. The interviewer asks questions and the interviewee replies. The interview should stay on topic. The interviewee should try to respond to the question of the interviewer (but it is not important to answer all questions that are asked), express a wish to move on, or decline to respond. The interviewee is also allowed to say that they don't know, do not understand the question, or express uncertainty. Responses can be very short, as long as they have some connection with the question. The interviewee's response might contain spelling and grammar mistakes. Here is the last part of the conversation.

				Interviewer: '{question}'

				Interviewee: '{answer}'

				That is the end of the conversation. 

				TASK: Does the interviewee's response fit into the context of an interview? Importantly, please answer only with a single 'yes' or 'no'. 
			""",
			"model": "gpt-4o-mini",
			"max_tokens": 2
		}
	}
}
