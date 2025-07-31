import os
import pandas as pd
import gradio as gr

from app.patient import Patient
from app.data_preprocessor import DataPreprocessor
from app.chat_audio import (
        chat,
        talker,
        transcribe_audio,
        submit_audio,
        do_entry,
        get_last_bot_message
    )

def run_chatbot():

    BASE_DIR = os.path.dirname(__file__)
    DATASET_DIR = os.path.join(BASE_DIR, "dataset")

    patients = pd.read_csv(os.path.join(DATASET_DIR, 'patients.csv'))
    immunizations = pd.read_csv(os.path.join(DATASET_DIR, 'immunizations.csv'))
    medications = pd.read_csv(os.path.join(DATASET_DIR, 'medications.csv'))
    observations = pd.read_csv(os.path.join(DATASET_DIR, 'observations.csv'))

    # Preprocess
    preprocessor = DataPreprocessor(patients, immunizations, medications, observations)
    patients, immunizations, medications, observations = preprocessor.preprocess()

    # Assign to Patient class
    Patient.patients = patients
    Patient.immunizations = immunizations
    Patient.medications = medications
    Patient.observations = observations

    css_path = os.path.join(BASE_DIR, "styles.css")
    with open(css_path, "r") as f:
        css = f.read()

    with gr.Blocks(title="HealthBot Assistant",css=css) as ui:
        gr.Markdown("# HealthBot Assistant")
        with gr.Row():
            chatbot = gr.Chatbot(height=500, type="messages")  #
            image_output = gr.Image(height=500)                
        with gr.Row():
            entry = gr.Textbox(label="Chat with our AI Health Assistant:", elem_id="chat-entry", lines=5)  
            send_btn = gr.Button("📩 Send Message", elem_id="send-btn")
            mic_input = gr.Audio(type="filepath", label="Record your question", interactive=True, elem_id="mic-input")
            mic_button = gr.Button("🎤 Send Voice", elem_id="mic-btn")        
        
        with gr.Row():
            read_button = gr.Button("🔊 Read Aloud", elem_id="read-aloud-btn")
            clear = gr.Button("🗑️ Clear", elem_id="clear-btn")                          

        with gr.Row():
            audio_output = gr.Audio(label="Read Aloud", interactive=False, elem_id="small-audio")


        # When user submits a message:
        # 1. Call do_entry() to add user message to history and clear input box
        # 2. Then call chat() passing updated history and return updated chat + image
        send_btn.click(do_entry, inputs=[entry, chatbot], outputs=[entry, chatbot]).then(
            chat, inputs=chatbot, outputs=[chatbot, image_output]
        ).then(
            fn=lambda: [None, None],  # clear both audio_output and mic_input
            inputs=None,
            outputs=[audio_output, mic_input]
        )

        # When "Read Answer" is clicked, get the last bot message and generate audio
        read_button.click(
            fn=lambda history: talker(get_last_bot_message(history)),
            inputs=chatbot,
            outputs=audio_output
        )

        mic_button.click(
            submit_audio,
            inputs=[mic_input, chatbot],
            outputs=[entry, chatbot]
        ).then(
            chat,
            inputs=chatbot,
            outputs=[chatbot, image_output]
        ).then(
            fn=lambda: None,  # Clear audio output after response
            inputs=None,
            outputs=audio_output
        )

        # Clear button clears the chat (resets chatbot, image_output, audio_output, mic_input to empty)
        clear.click(
            fn=lambda: ([], None, None, None), 
            inputs=None,
            outputs=[chatbot, image_output, audio_output, mic_input],
            queue=False
        )


    ui.launch(inbrowser=True)


if __name__ == "__main__":
    run_chatbot()