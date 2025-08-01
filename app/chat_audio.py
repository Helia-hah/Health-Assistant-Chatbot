import json
import os
from dotenv import load_dotenv
from openai import OpenAI
import numpy as np
from io import BytesIO
from pydub import AudioSegment
from .tools import tools, handle_tool_call, get_vital_plots, get_plot_out_of_range

load_dotenv(override=True)
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not set. Please create a .env file with your API key.")
openai = OpenAI(api_key=openai_api_key)

MODEL = "gpt-4o-mini"
system_prompt = '''You are a helpful medical assistant. Give brief, accurate answers. If you don't know the answer, say so.
                Do not make anything up if you haven't been provided with relevant context.'''

def chat(history):

    messages = [{"role": "system", "content": system_prompt}] + history 
    response = openai.chat.completions.create(model=MODEL, messages=messages, tools=tools)
    image = None
    
    if response.choices[0].finish_reason=="tool_calls":
        tool_msg = response.choices[0].message
        response, patient_id, should_generate_image, start_date, end_date  = handle_tool_call(tool_msg)
        messages.append(tool_msg)
        messages.append(response)
        tool_call = tool_msg.tool_calls[0]
        tool_name = tool_call.function.name
        
        if should_generate_image:
            if tool_name == "get_vital_plots":
                image = get_vital_plots(patient_id, start_date=start_date, end_date=end_date)
            elif tool_name == "get_analysis_vitals":
                image = get_plot_out_of_range(patient_id)
            
        response = openai.chat.completions.create(model=MODEL, messages=messages)
        
    reply = response.choices[0].message.content
    history += [{"role":"assistant", "content":reply}]

    
    return history, image


def talker(message):
    response = openai.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=message
    )
    audio_bytes = BytesIO(response.content)
    audio_segment = AudioSegment.from_file(audio_bytes, format="mp3")

    samples = np.array(audio_segment.get_array_of_samples())

    return audio_segment.frame_rate, samples

def transcribe_audio(audio_path):
    with open(audio_path, "rb") as audio_file:
        transcript = openai.audio.translations.create(
            model="whisper-1", 
            file=audio_file,
        )
    return transcript.text

def submit_audio(audio_path, history):
    text = transcribe_audio(audio_path)
    history += [{"role": "user", "content": text}]
    return "", history


def do_entry(message, history):
    # Add the user message to the chat history 
    history += [{"role":"user", "content":message}]
    # Clear the input box and return updated chat history
    return "", history
        

def get_last_bot_message(history):
    return next(
        (msg["content"] for msg in reversed(history) if msg["role"] == "assistant"),
        "No assistant message found."
    )
