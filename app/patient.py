from datetime import datetime, date
import json
import tiktoken
import io
import pandas as pd
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from collections import defaultdict
from io import BytesIO


class Patient:

    patients = None
    immunizations = None
    observations = None
    medications = None

    encoding = tiktoken.encoding_for_model("gpt-4o")
    VITAL_SIGNS = [
        "Diastolic Blood Pressure",
        "Systolic Blood Pressure", 
        "Heart rate", 
        "Respiratory rate"
    ]

    PHYSICAL_CHARACTERISTICS = [
        "Body Height", 
        "Body Weight", 
        "Body mass index (BMI) [Ratio]"
    ]

    # Define fixed colours for each measurement
    COLOR_MAP = {
        "Body Height": "#0084ff",
        "Body Weight": "#1ebd8d",
        "Body mass index (BMI) [Ratio]": "#a9c748",
        "Diastolic Blood Pressure": "#5415b3",
        "Systolic Blood Pressure": "#9359eb",
        "Heart rate": "#bd361e",
        "Respiratory rate": "#b31598"
    }

    VITAL_SIGNS_NORMAL_RANGES = {
        "Diastolic Blood Pressure": {"min": 60, "max": 80},      # mm Hg
        "Systolic Blood Pressure": {"min": 90, "max": 120},      # mm Hg
        "Heart rate": {"min": 60, "max": 100},                   # beats per minute
        "Respiratory rate": {"min": 12, "max": 20},              # breaths per minute
    }  

    VITAL_SIGN_INSTABILITY_THRESHOLDS = {
        "Heart rate": {
            "sudden_change": 12,             # bpm
            "cv": 0.2,
            "max_sudden_fluctuations": 4
        },
        "Systolic Blood Pressure": {
            "sudden_change": 18,             # mmHg
            "cv": 0.15,
            "max_sudden_fluctuations": 2
        },
        "Diastolic Blood Pressure": {
            "sudden_change": 10,             # mmHg
            "cv": 0.15,
            "max_sudden_fluctuations": 2
        },
        "Respiratory rate": {
            "sudden_change": 5,              # breaths/min
            "cv": 0.25,
            "max_sudden_fluctuations": 3
        }
    }


    def __init__(self, patient_id):
        self.patient_id = patient_id
        patient_rows = Patient.patients[Patient.patients["Id"] == self.patient_id].copy()

        if patient_rows.empty:
            raise ValueError(f"No patient found with ID: {patient_id}")
        self.patient_row = patient_rows.iloc[0]
        self.first_name = ''.join(c for c in self.patient_row["FIRST"] if not c.isdigit())
        self.last_name = ''.join(c for c in self.patient_row["LAST"] if not c.isdigit())


    def general_info(self):
        gender = self.patient_row["GENDER"]
        birthdate = datetime.strptime(self.patient_row["BIRTHDATE"], "%Y-%m-%d")
        age = (date.today() - birthdate.date()).days // 365

        if pd.notnull(self.patient_row["DEATHDATE"]):
            deathdate = datetime.strptime(self.patient_row["DEATHDATE"], "%Y-%m-%d")
            age = (deathdate.date() - birthdate.date()).days // 365
            return (
                f"Full name: {self.first_name} {self.last_name}\n"
                f"### Demographics\n"
                f"- Age: {age} -- Death Date:{deathdate.date()}\n"
                f"- Gender: {gender}"
            )
            
        return (
            f"Full name: {self.first_name} {self.last_name}\n"
            f"### Demographics\n"
            f"- Age: {age}\n"
            f"- Gender: {gender}"
        )

    def vaccines_info(self, max_entries=None):
        patient_vaccines = Patient.immunizations[Patient.immunizations["PATIENT"] == self.patient_id].copy()
        if patient_vaccines.empty:
            return "### Immunizations\n- No immunizations recorded."

        patient_vaccines["DATE"] = pd.to_datetime(patient_vaccines["DATE"])
        # Sort from oldest to newest (recent ones last)
        patient_vaccines = patient_vaccines.sort_values(by="DATE", ascending=True)
        # Apply threshold if given (only keep most recent N entries)
        if max_entries is not None:
            patient_vaccines = patient_vaccines.tail(max_entries)
            
        vaccine_summary = "\n".join(
            f"- {d}: {desc}"
            for d, desc in zip(patient_vaccines["DATE"], patient_vaccines["DESCRIPTION"])
        )

        return "### Immunizations\n" + "\n".join(vaccine_summary)


    def observations_info(self, max_entries=None):
        patient_obs = Patient.observations[Patient.observations["PATIENT"] == self.patient_id].copy()
        if patient_obs.empty:
            return "### Observations\n- No observations recorded."

        patient_obs["DATE"] = pd.to_datetime(patient_obs["DATE"])
        # Sort from oldest to newest (recent ones last)
        patient_obs = patient_obs.sort_values(by="DATE", ascending=True)
        # Apply threshold if given (only keep most recent N entries)
        if max_entries is not None:
            patient_obs = patient_obs.tail(max_entries)
    
        observation_summary = [
            f"- {date}: {desc} = {value}" + (f" {units}" if pd.notnull(units) else "")
            for date, desc, value, units in zip(
                patient_obs["DATE"],
                patient_obs["DESCRIPTION"],
                patient_obs["VALUE"],
                patient_obs["UNITS"]
            )
        ]
        return "### Observations\n" + "\n".join(observation_summary)


    def medications_info(self, max_entries=None):
        patient_meds = Patient.medications[Patient.medications["PATIENT"] == self.patient_id].copy()
        if patient_meds.empty:
            return "### Medications\n- No medications recorded."

        patient_meds["START"] = pd.to_datetime(patient_meds["START"])
        # Sort from oldest to newest (recent ones last)
        patient_meds = patient_meds.sort_values(by="START", ascending=True)
        # Apply threshold if given (only keep most recent N entries)
        if max_entries is not None:
            patient_meds = patient_meds.tail(max_entries)
    
        medication_summary = [
            f"- {start} to {stop}: {desc} (Reason: {reason})"
            for start, stop, desc, reason in zip(
                patient_meds["START"],
                patient_meds["STOP"],
                patient_meds["DESCRIPTION"],
                patient_meds["REASONDESCRIPTION"]
            )
        ]
        return "### Medications\n" + "\n".join(medication_summary)


    def get_summary(self,max_entries=None):
        return "\n\n".join([
            self.general_info(),
            self.vaccines_info(max_entries),
            self.observations_info(max_entries),
            self.medications_info(max_entries)
        ])

    def get_valid_summary(self, max_entries=None):
        summary_text = self.get_summary()
        tokens = self.encoding.encode(summary_text)
        
        if len(tokens) >= 200_000:
            summary_text = self.get_summary(max_entries=200)
            tokens = self.encoding.encode(summary_text)

        return summary_text


    def plot_patient_metrics(self, axis, measures, filtered_obs, title, bbox_to_anchor, ncol):
        for desc in measures:
            subset = filtered_obs[filtered_obs["DESCRIPTION"] == desc]
            if subset.empty:
                continue
            dates = subset["DATE"]
            values = pd.to_numeric(subset["VALUE"], errors="coerce")
            unit = subset["UNITS"].dropna().iloc[0] if not subset["UNITS"].dropna().empty else ""
            label = f"{desc} ({unit})" 
            axis.plot(dates, values, marker='o', label=label, color=Patient.COLOR_MAP.get(desc, 'gray'))
        
        axis.set_title(f"{title} for {self.first_name} {self.last_name}")
        axis.set_ylabel("Measurement")
        axis.legend(loc='lower center', bbox_to_anchor=bbox_to_anchor, ncol=ncol, frameon=False)
        axis.grid(True)

    def plot_out_of_range(self):

        fig, ax = plt.subplots(figsize=(10, 6))
        
        self.plot_patient_metrics(
            axis=ax,
            measures=Patient.VITAL_SIGNS,
            filtered_obs=Patient.observations[Patient.observations["PATIENT"] == self.patient_id],
            title="Vital Signs",
            bbox_to_anchor=(0.5, -0.3),
            ncol=4
        )
        
        out_of_range_points = self.extract_out_of_range_points()
        if not out_of_range_points:
            return None  # No data to plot
        labeled = False
        # Plot out-of-range points in red
        for point in out_of_range_points:
            date = pd.to_datetime(point["DATE"]).tz_localize(None)
            ax.plot(
                date,
                point["VALUE"],
                marker='o',
                color='red',
                markersize=8,
                linestyle='None',
                label='Out of Range' if not labeled else None
            )
            labeled = True

        plt.tight_layout()
        ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.25), ncol=3, frameon=False)

        
        buf = BytesIO()
        fig.savefig(buf, format="PNG", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return Image.open(buf)


    def generate_vitals_plot(self, start_date=None, end_date=None):
    
        filtered_obs = Patient.observations[
            (Patient.observations["PATIENT"] == self.patient_id) &
            (Patient.observations["DESCRIPTION"].isin(Patient.PHYSICAL_CHARACTERISTICS + Patient.VITAL_SIGNS))
        ]

        if filtered_obs.empty:
            return None  # No data to plot

        filtered_obs = filtered_obs.copy()
        filtered_obs["DATE"] = pd.to_datetime(filtered_obs["DATE"], errors="coerce")
        # Remove timezone info safely
        filtered_obs["DATE"] = filtered_obs["DATE"].dt.tz_localize(None)

        # Filter by date range
        if start_date:
            filtered_obs = filtered_obs[filtered_obs["DATE"] >= pd.to_datetime(start_date)]
        if end_date:
            filtered_obs = filtered_obs[filtered_obs["DATE"] <= pd.to_datetime(end_date)]

        if filtered_obs.empty:
            return None


        fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

        self.plot_patient_metrics(axes[0], Patient.PHYSICAL_CHARACTERISTICS, filtered_obs, "Physical Characteristics", bbox_to_anchor=(0.5, -0.25), ncol=3)
        self.plot_patient_metrics(axes[1], Patient.VITAL_SIGNS, filtered_obs, "Vital Signs", bbox_to_anchor=(0.5, -0.5), ncol=4)
        axes[1].set_xlabel("Date")
        plt.setp(axes[1].xaxis.get_majorticklabels(), rotation=45)
        plt.tight_layout()
        plt.subplots_adjust(hspace=0.45, bottom=0.35)


        buf = BytesIO()
        fig.savefig(buf, format="PNG", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return Image.open(buf)


    def out_of_range_detection(self, dataset):

        admission_id = dataset["ADMISSION_ID"].iloc[0]
    
        out_of_range_records = []  
        dataset = dataset.copy()
        dataset["VALUE"] = pd.to_numeric(dataset["VALUE"], errors="coerce")

        for sign, limits in Patient.VITAL_SIGNS_NORMAL_RANGES.items():
            mask = (dataset["DESCRIPTION"] == sign) & (
                (dataset["VALUE"] < limits["min"]) | (dataset["VALUE"] > limits["max"])
            )
            filtered = dataset.loc[mask, ["DESCRIPTION", "DATE", "VALUE"]]
            filtered["DATE"] = filtered["DATE"].astype(str)

            if not filtered.empty:
                out_of_range_records.extend(
                    filtered.rename(columns={"DESCRIPTION": "vital_sign"}).to_dict(orient="records")
                )

        if out_of_range_records:
            return {admission_id: {"out_of_range": out_of_range_records}}
        else:
            return None


    def detect_instability(self, dataset):
    
        admission_id = dataset["ADMISSION_ID"].iloc[0]

        instabilities = []

        for sign, thresholds in Patient.VITAL_SIGN_INSTABILITY_THRESHOLDS.items():
        
            mask = dataset["DESCRIPTION"] == sign
            filtered = dataset.loc[mask, ["DESCRIPTION", "DATE", "VALUE"]].copy()

            # instability_df = pd.DataFrame()
            filtered = filtered.copy()
            values = pd.to_numeric(filtered["VALUE"], errors="coerce")

            if values.empty or len(values)==1:
                continue

            mean = values.mean()
            std = values.std()
            # Coefficient of Variation: A normalized measure of spread
            cv = std / mean if mean != 0 else 0

            # Sudden changes
            sudden_changes = values.diff().abs().gt(thresholds["sudden_change"]).sum()

            # Rolling standard deviation (local variability)
            rolling_std_max = values.rolling(window=3, min_periods=2).std().max()

            # Flags
            is_cv_high = bool( cv > thresholds["cv"])
            is_sudden_fluctuation = bool(sudden_changes > thresholds["max_sudden_fluctuations"])
            is_high_rolling_std = bool(rolling_std_max > thresholds["sudden_change"])  # optional, adjust as needed


            unstable = is_cv_high or is_sudden_fluctuation or is_high_rolling_std

            if unstable:
                instabilities.append({
                    "vital_sign": sign,
                    "mean": round(mean, 2),
                    "std_dev": round(std, 2),
                    "coefficient_of_variation": round(cv, 3),
                    f"sudden_changes_>{thresholds['sudden_change']}": int(sudden_changes),
                    "max_rolling_std": round(rolling_std_max, 2),
                    "unstable": unstable,
                    "reasons": {
                        "cv_exceeds_threshold": is_cv_high,
                        "sudden_fluctuations_exceed": is_sudden_fluctuation,
                        "high_local_variability": is_high_rolling_std 
                    }
                })
    
        return {admission_id: {"instabilities": instabilities}}

        
    def analyze_vitals(self):
        filtered_dataset = Patient.observations[Patient.observations["PATIENT"] == self.patient_id].copy()

        combined = defaultdict(lambda: {"out_of_range": [], "instabilities": []})
 

        for func in [self.out_of_range_detection, self.detect_instability]:
            results = filtered_dataset.groupby("ADMISSION_ID", group_keys=False).apply(func).dropna().tolist()

            for res in results:
                for adm_id, data in res.items():
                    adm_id_clean = int(adm_id) if isinstance(adm_id, (np.integer,)) else adm_id
                    combined[adm_id_clean]["out_of_range"].extend(data.get("out_of_range", []))
                    combined[adm_id_clean]["instabilities"].extend(data.get("instabilities", []))

        return dict(combined) if combined else None


    def extract_out_of_range_points(self):
        analyze_vitals_output = self.analyze_vitals()
        if not analyze_vitals_output:
            return []
        out_of_range_points = []
        for adm_id, data in analyze_vitals_output.items():
            out_of_range_points.extend(data.get("out_of_range", []))
        return out_of_range_points
          


