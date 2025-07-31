# 🩺 Health Assistant Chatbot
**Health Assistant Chatbot** is a Gradio-based interactive application that leverages OpenAI's GPT (gpt-4o-mini) to assist health professionals in querying and visualizing patient data. It supports both text and voice input and provides text-to-speech responses for accessibility.

## 📁 Project Structure:
The following is the structure of this project repository:
```
Health-Assistant-Chatbot/
│
├── app/
│   ├── __init__.py
│   ├── main.py              
│   ├── patient.py            
│   ├── data_preprocessor.py  
│   ├── chat_audio.py         
│   ├── tools.py              
│   ├── style.css             # 🎯 CSS for the Gradio UI
│
├── dataset/
│   ├── patients.csv
│   ├── medications.csv
│   ├── observations.csv
│   ├── immunizations.csv
├── .env                     # ⚠️ Not tracked in Git. Stores your OpenAI API key.
├── README.md
```

---
### 🗃️ Dataset
This project uses synthetic patient data generated with **Synthea™**, a tool that creates realistic (but not real) health records in multiple formats. I generated a dataset of 110 patients in CSV format by running the command below. You can find more details about Synthea on their [GitHub repository](https://github.com/synthetichealth/synthea).
<pre> run_synthea -p 110 </pre>
