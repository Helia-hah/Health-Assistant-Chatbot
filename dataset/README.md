### 🗃️ Dataset
---
This project uses synthetic patient data generated with **Synthea™**, a tool that creates realistic (but not real) health records in multiple formats. I generated a dataset of 110 patients in CSV format by running the command below. You can find more details about Synthea on their [GitHub repository](https://github.com/synthetichealth/synthea).
<pre> run_synthea -p 110 </pre>

For building the chatbot, only selected tables and columns from the Synthea dataset are used:

- The **patients** table provides demographic details such as `Id` (unique identifier), BIRTHDATE, optional DEATHDATE, FIRST and LAST names, and GENDER. This helps identify users and segment them by age or gender.

- The **immunizations** table records administered vaccines, including PATIENT (reference to the individual), DATE, and vaccine DESCRIPTION.

- The **medications** table contains prescription data: START and STOP dates, medication DESCRIPTION, REASONDESCRIPTION, and DISPENSES (number of refills). Each row is linked to a PATIENT.

- The **observations** table includes clinical observations with DATE, PATIENT, DESCRIPTION (e.g., vital signs or lab tests), and recorded VALUE.

Together, these tables form a simplified but comprehensive patient profile used by the chatbot to generate informed responses.
