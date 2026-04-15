from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import time
import logging 
import random

def chat_to_string(chat:list, only_topic:int=None, until_topic:int=None) -> str:
    """ Convert messages from chat into one string. """
    topic_history = ""
    for message in chat:
        # If desire specific topic's chat history:
        if only_topic and message['topic_idx'] != only_topic: 
            continue
        if until_topic and message['topic_idx'] == until_topic:
            break
        if message["type"] == "question":
            topic_history += f'Interviewer: "{message['content']}"\n'
        if message["type"] == "answer":
            topic_history += f'Interviewee: "{message['content']}"\n'
    return topic_history.strip()

def fill_prompt_with_interview(template:str, topics:list, history:list, user_message:str=None) -> str:
    """ Fill the prompt template with parameters from current interview. """
    state = history[-1]
    current_topic_idx = min(int(state['topic_idx']), len(topics))
    next_topic_idx = min(current_topic_idx + 1, len(topics))
    current_topic_chat = chat_to_string(history, only_topic=current_topic_idx)
    prompt = template.format(
        topics='\n'.join([topic['topic'] for topic in topics]),
        question=state["content"],
        answer=user_message,
        summary=state['summary'] or chat_to_string(history, until_topic=current_topic_idx),
        current_topic=topics[current_topic_idx - 1]["topic"],
        next_interview_topic=topics[next_topic_idx - 1]["topic"],
        current_topic_history=current_topic_chat
    )
    logging.debug(f"Prompt to GPT:\n{prompt}")
    assert not re.findall(r"\{[^{}]+\}", prompt)
    return prompt 

def execute_queries(query, task_args:dict) -> dict:
    """ 
    Execute queries (concurrently if multiple).

    Args:
        query: function to execute
        task_args: (dict) of arguments for each task's query
    Returns:
        suggestions (dict): {task: output} 
    """
    st = time.time()
    suggestions = {}
    with ThreadPoolExecutor(max_workers=len(task_args)) as executor:
        futures = {
            executor.submit(query, **kwargs): task 
                for task, kwargs in task_args.items()
        }
        for future in as_completed(futures):
            task = futures[future]
            resp = future.result().choices[0].message.content.strip("\n\" '''")
            suggestions[task] = resp

    logging.info("OpenAI query took {:.2f} seconds".format(time.time() - st))
    logging.info(f"OpenAI query returned: {suggestions}")
    return suggestions


def get_randomised_programmes():
    programmes = [
        ("Conditional Cash Transfers (CCTs)", "These provide money to poor families, but only if they meet certain conditions, such as sending their children to school or getting regular health checkups.","CCTs are cash payments given to low-income families, but only if they meet specific requirements, like sending their children to school or attending health checkups. The goal is to reduce poverty while also encouraging long-term improvements in education and health."),

        ("Unconditional Cash Transfers (UCTs)", "These give money to people without any conditions. Recipients can decide how to use the funds themselves.", "UCTs provide money to people with no strings attached — recipients can use the funds however they choose. This approach trusts individuals to know their own needs best and is often faster and simpler to implement than conditional programmes."),

        ("Public Works Programmes" , "These offer temporary employment in infrastructure or community projects. People receive wages in exchange for their labor.", "Workfare programmes offer short-term jobs (like building roads or cleaning public spaces) to people who are unemployed or struggling financially, and pay them wages in return. The aim is to create both employment opportunities and community improvements at the same time."),

        ("In-Kind Transfers", "Instead of money, recipients receive goods like food, clothing, or hygiene products.", "In-kind transfers are such that instead of giving money, governments or aid groups provide essential goods like food, clothing, or hygiene products. These are often used in emergencies or in areas where markets don’t work well or prices are too high."),

        ("School Feeding Programmes", "These provide free meals to children at school to improve attendance and nutrition.", "School feeding programmes provide free meals to children while they are at school, ensuring they’re well-nourished and more likely to attend and concentrate in class.")
    ]
    random.shuffle(programmes)
    programme_map = {i + 1: programmes[i][0] for i in range(len(programmes))}
    programme_description_map = {i + 1: programmes[i][2] for i in range(len(programmes))}
    return programmes, programme_map, programme_description_map

def extract_programme_choice(user_input: str, map) -> str | None:
    """
    Extract a number 1–5 from user input and return the corresponding programme name.
    Accepts either digit ("3") or word ("three").
    Returns None if no valid match is found.
    """

    word_to_number = {
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5"
    }

    # Normalize input to lowercase
    normalized_input = user_input.lower()

    # Try to match digit
    digit_match = re.search(r"\b[1-5]\b", normalized_input)
    if digit_match:
        number = digit_match.group()
        return map.get(number)

    # Try to match written word
    for word, number in word_to_number.items():
        if re.search(rf"\b{word}\b", normalized_input):
            return map.get(number)

    return None
