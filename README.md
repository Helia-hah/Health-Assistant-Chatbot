# Health Assistant Chatbot
## 📁 Project Structure:
The following is the structure of this project repository:

```
your-project/
│
├── app/
│   ├── __init__.py
│   ├── main.py               # Entry point to run the app
│   ├── patient.py            # Patient data management
│   ├── data_preprocessor.py  # Data loading and cleaning
│   ├── chat_audio.py         # Chat logic, TTS, and ASR
│   ├── tools.py              # Tool functions for the chatbot
│   ├── style.css             # 🎯 CSS for the Gradio UI
│
├── dataset/
│   ├── patients.csv
│   ├── medications.csv
│   ├── observations.csv
│   ├── immunizations.csv
├── requirements.txt
├── .env                     # ⚠️ Not tracked in Git. Stores your OpenAI API key.
├── README.md
```

---
### 🗃️ Dataset
This project uses synthetic patient data generated with **Synthea™**, a tool that creates realistic (but not real) health records in multiple formats. I generated a dataset of 110 patients in CSV format by running the command below. You can find more details about Synthea on their [GitHub repository](https://github.com/synthetichealth/synthea).
<pre> run_synthea -p 110 </pre>
