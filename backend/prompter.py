from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=api_key)

messages = []

with open("context.txt", "r") as context_file:
    system_msg = context_file.read().strip()  # Read the entire file content
    messages.append({"role": "system", "content": system_msg})

with open("query.txt", "r") as file:
    user_message = file.read().strip()

    if user_message != "quit()":
        messages.append({"role": "user", "content": user_message})
        response = client.chat.completions.create(model="gpt-4",
        messages=messages)
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})

        with open("answer.txt", "w") as output:
            output.write("\n" + reply + "\n")

