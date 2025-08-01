import pandas as pd

class DataPreprocessor:
    
    def __init__(self, patients, immunizations, medications, observations):
        self.patients = patients
        self.immunizations = immunizations
        self.medications = medications
        self.observations = observations

    def preprocess(self):
        self._clean_patients()
        self._clean_immunizations()
        self._clean_medications()
        self._process_observations()
        return self.patients, self.immunizations, self.medications, self.observations

    def _clean_patients(self):
        self.patients = self.patients[['Id','BIRTHDATE','FIRST','LAST','GENDER','DEATHDATE']]

    def _clean_immunizations(self):
        self.immunizations = self.immunizations[['PATIENT','DATE','DESCRIPTION']]

    def _clean_medications(self):
        self.medications = self.medications[['PATIENT','START','STOP','DESCRIPTION','REASONDESCRIPTION']]

    def _process_observations(self):
        obs = self.observations
        obs = obs[['DATE','PATIENT','DESCRIPTION','VALUE','UNITS']]
        obs = obs.sort_values(["PATIENT","DATE"]).reset_index(drop=True)
        obs['DATE'] = pd.to_datetime(obs['DATE'])
        obs['time_diff'] = obs.groupby('PATIENT')['DATE'].diff()
        obs['new_admission'] = (obs['time_diff'] > pd.Timedelta(days=1)) 
        obs['ADMISSION_ID'] = obs.groupby('PATIENT')['new_admission'].cumsum().astype(int)
        self.observations = obs.drop(columns=['new_admission','time_diff'])
