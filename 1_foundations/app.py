from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr

from rag_setup import create_vector_store

import sqlite3

load_dotenv(override=True)

def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


# def record_user_details(email, name="Name not provided", notes="not provided"):
#     push(f"Recording {name} with email {email} and notes {notes}")
#     return {"recorded": "ok"}

_last_recorded = {"question": None, "email": None}

def record_user_details(email, name="Name not provided", notes="not provided"):
    global _last_recorded
    if email != _last_recorded.get("email"):
        push(f"Recording {name} with email {email} and notes {notes}")
        _last_recorded["email"] = email
    return {"recorded": "ok"}

def record_unknown_question(question):
    global _last_recorded
    if question != _last_recorded.get("question"):
        push(f"Recording {question}")
        _last_recorded["question"] = question
    return {"recorded": "ok"}

# def record_unknown_question(question):
#     push(f"Recording {question}")
#     return {"recorded": "ok"}

def query_faq(question):
    """
    Reads FAQ database and returns the answer for a matching question.
    """
    conn = sqlite3.connect("faq.db")  # connect to your SQLite DB
    cursor = conn.cursor()
    
    cursor.execute("SELECT answer FROM faq WHERE question LIKE ?", (f"%{question}%",))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0]
    else:
        return "Sorry, I don't know the answer to that."

faq_tool_json = {
    "name": "query_faq",
    "description": "Looks up common Q&A from a read-only SQLite database",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The question from the user"}
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]

tools.append({"type": "function", "function": faq_tool_json})

class Me:

    def __init__(self, kb_collection):

        self.kb_collection = kb_collection
        self.openai = OpenAI(api_key=os.getenv("GEMINI_API_KEY"), base_url="https://generativelanguage.googleapis.com/v1beta/openai/")

        self.name = "Priya"
        reader = PdfReader("me/Profile.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

    def retrieve_context(self, question, k=3):
        results = self.kb_collection.query(
            query_texts=[question],
            n_results=k
        )
        retrieved_texts = [doc for doc in results['documents'][0] if doc]
        return "\n".join(retrieved_texts)
        
    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
            particularly questions related to {self.name}'s career, background, skills and experience. \
            Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
            You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
            Always try to use query_faq if the user's question matches a known FAQ. \
            Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
            If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
            If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history=[]):
        if not history:
            history = [{"role": "assistant", "content": "Hi, I'm Priya. Ask me anything about my background, education, or projects 😆"}]

        retrieved_context = self.retrieve_context(message)
        system_content = self.system_prompt() + "\n\n## Retrieved Context:\n" + retrieved_context

        messages = [{"role": "system", "content": system_content}] + history + [{"role": "user", "content": message}]

        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gemini-1.5-flash", messages=messages, tools=tools)

            if response.choices[0].finish_reason == "tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content

    

if __name__ == "__main__":
    # Step 1: Initialize the RAG vector store
    kb_collection = create_vector_store()
    
    # Step 2: Initialize your agent with the RAG knowledge base
    me = Me(kb_collection)
    
    # Step 3: Launch Gradio interface
    gr.ChatInterface(
        fn=me.chat,
        type="messages"
    ).launch()
