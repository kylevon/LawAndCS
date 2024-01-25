from openai import OpenAI
from dotenv import load_dotenv
import os
import re
from collections import namedtuple
import Levenshtein

Note = namedtuple('Note', 'input_citation guideline_citation explanation')

def is_substring_within_edit_distance(main_string, substring, max_distance=10):
    for i in range(len(main_string) - len(substring) + 1):
        if Levenshtein.distance(main_string[i:i+len(substring)], substring) <= max_distance:
            return True
    return False

def extract_notes(message: str) -> [str]:
    pattern = r"\[([^\]]*)\]{([^}{]*)}\(([^\(\)]*)\)"
    matches = re.findall(pattern, message)
    new_matches = []
    for match in matches:
        new_match = []
        for element in match:
            new_match.append(re.sub(r'\s+', ' ', element))
        new_matches.append(new_match)
    return [Note(*match) for match in new_matches]

def syntax_error_message(message: str) -> str:
    pattern = r"\[([^\]]*)\]{([^}{]*)}[^\(]"
    matches = re.findall(pattern, message)
    if len(matches) > 0:
        return f"You returned: this group: {matches[0][0:-1]}, and this pattern is incorrect because it is missing the (explanation) part."
    pattern = r"\[([^\]]*)\][^{]"
    matches = re.findall(pattern, message)
    if len(matches) > 0:
        return f"You returned a group with the first highlighted section: {matches[0][0:-1]}, but it did not include the" + " {citation from the guidelines}."
    return ""

def find_errors_from_ai(message: str, original_message: str) -> str:
    print(message)
    syntax_errors = syntax_error_message(message)
    if syntax_errors != "":
        return syntax_errors

    notes = extract_notes(message)
    if len(notes) == 0:
        return "There was NO group with the required format, that is: [The original text]{Citation from the guidelines}(Explanation of why this guideline is applied here) Make sure you are including all sections in the group."
    with open("legal_doc.txt", "r") as file:
        legal_text = file.read().strip()
    for note in notes:
        if not is_substring_within_edit_distance(original_message, note.input_citation):
            return f"You highlighted: [{note.input_citation}], but it did not appear in the original message."
        if not is_substring_within_edit_distance(legal_text, note.guideline_citation):
            highlight = "{" + note.guideline_citation + "}"
            return f"the highlighted text: {highlight} from the guidelines, does not appear in the guidelines!"
    return ""

def prompt(user_query: str) -> str:
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')

    client = OpenAI(api_key=api_key)

    messages = []

    model = "gpt-3.5-turbo"
    model = "gpt-4"


    with open("context.txt", "r") as context_file:
        system_msg = context_file.read().strip()  # Read the entire file content
        messages.append({"role": "system", "content": system_msg})

        messages.append({"role": "user", "content": user_query})
        response = client.chat.completions.create(model=model,
            messages=messages)
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        return extract_notes(reply)
        error_from_ai = find_errors_from_ai(reply, user_query)
        while error_from_ai != "":
            print(f"Error from ai: {error_from_ai}")
            messages.append(
                {"role": "user",
                 "content": error_from_ai})
            response = client.chat.completions.create(model=model,
                messages=messages)
            reply = response.choices[0].message.content
            error_from_ai = find_errors_from_ai(reply, user_query)
        return extract_notes(reply)


if __name__ == "__main__":
    print(prompt("""
     Anna punched jack, while one a nightout, outside of a pub.
    """))
