from openai import OpenAI

class SimulatedIntervieweeAgent:
    def __init__(self, api_key, persona_prompt, model="gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.persona_prompt = persona_prompt
        self.model = model

    def respond(self, history, interviewer_question: str) -> str:
        messages = [{"role": "system", "content": self.persona_prompt}]
        for msg in history[-5:]:  # most recent 5 turns
            role = "user" if msg["type"] == "question" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": interviewer_question})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=100,
            temperature=0.9
        )
        return response.choices[0].message.content.strip()