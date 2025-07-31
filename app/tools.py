from patient import Patient
from cachetools import TTLCache
import json


# --- Patient Cache and Tool Logic ---
# Up to 150 patients in memory, each valid for 10 minutes
_patient_cache = TTLCache(maxsize=150, ttl=600)

def get_patient(patient_id):
    try:
        if patient_id not in _patient_cache:
            _patient_cache[patient_id] = Patient(patient_id)
        return _patient_cache[patient_id], None
    except ValueError:
        error_msg = f"Patient ID '{patient_id}' is not valid or not found."
        return None, error_msg
   
def get_patient_information(patient_id):
    patient, error = get_patient(patient_id)
    if error:
        return {"error": error}
    return patient.get_valid_summary()

def get_vital_plots(patient_id, start_date=None, end_date=None):
    patient, error = get_patient(patient_id)
    if error:
        return {"error": error}
    return patient.generate_vitals_plot(start_date=start_date, end_date=end_date)

def get_analysis_vitals(patient_id):
    patient, error = get_patient(patient_id)
    if error:
        return {"error": error}
    return patient.analyze_vitals()

def get_plot_out_of_range(patient_id):
    patient, error = get_patient(patient_id)
    if error:
        return {"error": error}
    return patient.plot_out_of_range()

    
# --- Tool Descriptions ---
patient_info_tool = {
    "name": "get_patient_information",
    "description": "Fetches health data for a patient ID, including demographics, meds, and vitals. For example, when a user asks 'What do you know about a particular patient?'",
    "parameters": {
        "type": "object",
        "properties": {
            "patient_id": {
                "type": "string",
                "description": "The ID of the patient to retrieve."
            }
        },
        "required":["patient_id"],
        "additionalProperties": False
    }
}

plot_vitals_tool = {
    "name": "get_vital_plots",
    "description": "Generates a line plot of a patient's vital signs or physical measurements (Height, Weight, BMI) over time. Can optionally filter results using start and end dates.",
    "parameters": {
        "type": "object",
        "properties": {
            "patient_id": {
                "type": "string",
                "description": "The ID of the patient to plot vitals for."
            },
            "start_date": {
                "type": "string",
                "description": "Start date (YYYY or full ISO format). Required if filtering by time. Must be retained if re-calling."
            },
            "end_date": {
                "type": "string",
                "description": "End date (YYYY or full ISO format). Required if filtering by time. Must be retained if re-calling."
            }
        },
        "required": ["patient_id"]
    }
}

analyze_vital_tool = {
    "name": "get_analysis_vitals",
    "description": (
        "Analyze a patient's vital signs to detect out-of-range values and instability events per admission. "
        "If no abnormalities or instabilities are detected, the corresponding result fields may be empty or omitted. "
        "Please include the numeric results and statistics provided by the function in your output."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "patient_id": {
                "type": "string",
                "description": "The ID of the patient to retrieve."
            }
        },
        "required":["patient_id"],
        "additionalProperties": False
    }
}

tools = [
    {"type": "function", "function": patient_info_tool},
    {"type": "function", "function": plot_vitals_tool},
    {"type": "function", "function": analyze_vital_tool}
]


# --- Tool Call Handler ---
def handle_tool_call(message):
    
    tool_call = message.tool_calls[0]
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    patient_id = arguments.get('patient_id')

    if function_name == "get_patient_information":
        info = get_patient_information(patient_id)
        response =  {
            "role": "tool",
            "content": json.dumps({"patient_id":patient_id, "info":info}),
            "tool_call_id": tool_call.id
        }
        return response, patient_id, False, None, None
    
    elif function_name == "get_vital_plots":
        
        start_date = arguments.get("start_date")  
        end_date = arguments.get("end_date")     
        image = get_vital_plots(patient_id, start_date=start_date, end_date=end_date)
        
        if image is not None:
            response = {
            "role": "tool",
            "content": f"Generated vitals plot for patient {patient_id}.",  
            "tool_call_id": tool_call.id
            }
            return response, patient_id, True, start_date, end_date
        else:
            response = {
                "role": "tool",
                "content": f"No vital signs available for patient {patient_id}.",
                "tool_call_id": tool_call.id
            }
            return response, patient_id, False, None, None

    elif function_name == "get_analysis_vitals":
        analysis = get_analysis_vitals(patient_id)
        response =  {
            "role": "tool",
            "content": json.dumps({"patient_id":patient_id, "analysis":analysis}),
            "tool_call_id": tool_call.id
        }
            
        return response, patient_id, True, None, None


