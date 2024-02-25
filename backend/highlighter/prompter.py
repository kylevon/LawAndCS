from openai import OpenAI
from dotenv import load_dotenv
import os
import re
from collections import namedtuple
import json
import Levenshtein

Note = namedtuple("Note", "input_citation guideline_citation explanation")


def is_substring_within_edit_distance(main_string, substring, max_distance=10):
    for i in range(len(main_string) - len(substring) + 1):
        if (
            Levenshtein.distance(main_string[i : i + len(substring)], substring)
            <= max_distance
        ):
            return True
    return False


def extract_notes(message: str) -> [str]:
    message = "".join(message.split("\n"))
    pattern = r"[^{]*(\[.*\]).*"
    json_match = re.search(pattern, message)
    if json_match is None:
        raise(Exception("Your JSON needs to be encapsulated by brackets: [], because it's a list."))
    json_str = json_match.group(1)
    return json.loads(json_str)


def find_errors_from_ai(message: str, original_message: str, guidelines: str) -> str:
    try:
        ai_out = extract_notes(message)
    except Exception as err:
        return f"Your message: {message} is not a valid json, this is the error message: {err}. You need to respond with a JSON, NOTHING else."
    for entry in ai_out:
        if len(entry) != 3:
            return f"The entry: {entry} did not have exactly 3 keys: case_text, guideline_text, comments"
        for key in "case_text", "guideline_text", "comments":
            if key not in entry:
                return f"The key: {key} is missing from {entry}. There must be exactly 3 keys: case_text, guideline_text, comments"
        case_text = re.sub(r"\s+", " ", entry["case_text"])
        guideline_text = re.sub(r"\s+", " ", entry["guideline_text"])
        if not is_substring_within_edit_distance(original_message, case_text):
            return f"The information from the case_text: {case_text}, is not in the original case"
        if not is_substring_within_edit_distance(guidelines, guideline_text):
            return f"The information from the guideline_text: {guideline_text}, is not in the original guidelines."
    return ""


def prompt(subguideline_name: str, user_query: str) -> str:
    print(f"Prompt called with subguideline_name: {subguideline_name}")
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    client = OpenAI(api_key=api_key)

    messages = []

    model = "gpt-3.5-turbo"
    model = "gpt-4"

    user_query = re.sub(r"\s+", " ", user_query)
    with open(f"guidelines/{subguideline_name}.txt", "r") as f:
        guidelines = re.sub(
            r"\s+", " ", f.read().strip()
        )  # Read the entire file content
    with open(f"guidelines/example_case.txt", "r") as f:
        example_input = f.read().strip()  # Read the entire file content
    with open(f"guidelines/example_{subguideline_name}.txt", "r") as f:
        example_output = f.read().strip()  # Read the entire file content

    context = f"""
You will generate a JSON from text provided using guidelines provided (grievous bodily harm). The guidelines explain the {subguideline_name.replace('_',' ')} factors.

In your output you will extract exact excerpts from the case provided, and will provide exact excerpts from the guidelines that are related, and comments. You will follow the syntax from the example exactly, no other text should be outputed. If there are no aspects to extract, then respond with an empty list, but do that VERY sparingly, it is rare that no factors appear. The guidelines extract should be as short as possible, with only pertinent parts.

These are the guidelines:

    {guidelines}

This is an example input:

    {example_input}

This is an example output:

    {example_output}
"""
    # print(context)
    user_query = re.sub(r"\s+", " ", user_query)
    messages.append({"role": "system", "content": context})
    messages.append({"role": "user", "content": user_query})
    # print(user_query)
    response = client.chat.completions.create(model=model, messages=messages)
    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
    error_from_ai = find_errors_from_ai(reply, user_query, guidelines)
    if error_from_ai != "":
        print(f"Error from ai: {error_from_ai}")
        messages.append({"role": "user", "content": error_from_ai})
        response = client.chat.completions.create(model=model, messages=messages)
        reply = response.choices[0].message.content
        error_from_ai = find_errors_from_ai(reply, user_query, guidelines)
    if error_from_ai == "":
        notes = extract_notes(reply)
        print(f"Output will be: {notes}")
        return notes
    else:
        print(f"Error from ai: {error_from_ai}")
        return []


if __name__ == "__main__":
    case = "Anna punched jack, while she was drunk, outside of a pub. Jack then had a severe bruising and lost vision on one eye"
    for factor in (
        "culpability",
        "harm",
        "mitigating_factors",
        "other_aggravating_factors",
        "statutory_aggravating_factors",
    ):
        print(prompt(factor, case))
