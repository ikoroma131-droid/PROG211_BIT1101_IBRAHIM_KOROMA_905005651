# Patient Record System (PRS)

An open-source, privacy-respecting Python program that helps clinics, health
posts and community health workers in Sierra Leone **keep simple digital
records of patient visits** and see which patients need follow-up. It is built
with Object-Oriented Programming (OOP) and designed to follow the **Digital
Public Goods (DPG) Standard**.

> **Module:** PROG211 Object-Oriented Programming 1, Limkokwing University of Creative Technology, Sierra Leone
> **Assignment:** Real-World Solutions under DPG Standards
> **Domain:** Health (Patient Record System)

> **Disclaimer:** PRS is a record-keeping tool built for learning. It does not
> diagnose illness or give medical advice. All sample data is fictional.

---

## 1. The problem

Many health posts still keep patient visits in paper registers. Paper records
are slow to search, easily damaged, and make it hard to answer important
questions: *Which patients with high blood pressure have not come back? How
many malaria cases did we see this quarter?* Digital records help, but health
information is very sensitive, so any system must protect patient privacy.

PRS gives each patient a coded record (for example `PAT-0001`) containing only
what is needed for care: age, sex, district and a history of visits with vital
signs and a diagnosis category. It highlights patients who need follow-up and
produces anonymised statistics that can be shared safely.

## 2. Features

| Feature | Description |
|---|---|
| Register patients | Coded ID, age, sex and district only. No names or contact details. |
| Register health workers | Staff code, role (Doctor, Nurse, Midwife, CHO) and district. |
| Record visits | Date, visit type, diagnosis, temperature, weight and optional blood pressure. |
| Patient history | Every visit in date order, with fever and blood-pressure flags. |
| Follow-up list | Patients with fever, stage 2 / crisis blood pressure or a chronic condition. |
| Diagnosis summary | Visits per diagnosis with percentages. |
| Anonymised export | Counts by district and diagnosis; small counts shown as `<5`. |
| Sample data | One menu option loads fictional demonstration data. |

## 3. Quick start

**Requirements:** Python 3.8 or newer. No extra packages are needed.

```bash
git clone https://github.com/<your-username>/patient-record-system.git
cd patient-record-system

python main.py                    # interactive menu program
python demo.py                    # guided demonstration of every requirement
python -m unittest discover -v    # run the 35 automated tests
```

On some computers the command is `python3` instead of `python`.

## 4. Project structure

```
patient-record-system/
├── prs/
│   ├── __init__.py      # package entry point
│   ├── models.py        # Patient, HealthWorker, Visit, VitalSigns
│   └── registry.py      # PatientRegistry (dictionary) + add/display functions
├── tests/
│   ├── test_models.py   # tests for the classes
│   └── test_registry.py # tests for the registry and the menu program
├── docs/
│   └── class_diagram.png
├── main.py              # interactive command-line program
├── demo.py              # non-interactive demonstration
├── CONTRIBUTING.md
├── LICENSE              # MIT open-source licence
└── README.md
```

## 5. How the assignment tasks are met

### Task 1: OOP basics (classes, attributes, objects)

| Class | Key attributes | Key methods |
|---|---|---|
| `Patient` | `patient_id`, `age`, `sex`, `district`, `visits` | `add_visit()`, `latest_visit()`, `needs_follow_up()`, `update_record()`, `display_info()` |
| `HealthWorker` | `worker_id`, `role`, `district`, `visits_recorded` | `record_visit()`, `display_info()` |
| `PatientRegistry` | `_patients`, `_workers` (dictionaries) | `add_patient()`, `get_patient()`, `diagnosis_summary()`, `follow_up_list()`, `export_statistics()` |
| `Visit`, `VitalSigns` | visit details and measurements | immutable NamedTuples; `VitalSigns` has `has_fever()` and `bp_category()` |

**Interaction between objects:** a `HealthWorker` records a visit for a
`Patient`. `worker.record_visit(patient, ...)` validates the details, creates
a `Visit` stamped with the worker's code, adds it to the patient's history
with `patient.add_visit(...)`, and increases the worker's `visits_recorded`.

![Class diagram](docs/class_diagram.png)

### Task 2: Python data structure (dictionary)

The single data structure chosen is the **dictionary**. Objects are stored with
their unique code as the key:

```python
self._patients = {"PAT-0001": <Patient>, "PAT-0002": <Patient>, ...}
self._workers  = {"HW-0001": <HealthWorker>, ...}
```

This gives instant look-up by code (`registry.get_patient("PAT-0001")`) and
makes duplicate codes impossible. The simple functions required by the brief
are in `prs/registry.py`:

```python
add_record(registry, record)   # adds a Patient or HealthWorker to the dictionary
display_records(registry)      # loops through the dictionary and prints every record
```

**Optional tuples (bonus):** tuples are used wherever data must not change:
each `Visit` and its `VitalSigns` are `NamedTuple`s, so a saved visit cannot
be altered (this protects the integrity of the medical record); reference data
such as districts, visit types, diagnoses and roles are tuples; and report rows
and follow-up reasons are returned as tuples. Tuple unpacking is used in
`Patient.from_tuple()` and when reading vital signs.

### Task 3: Instance, class and static methods

| Type | Examples |
|---|---|
| Instance methods | `record_visit()`, `add_visit()`, `needs_follow_up()`, `display_info()`, `update_record()` |
| Class methods (`@classmethod`) | `Patient.generate_id()`, `Patient.from_tuple()`, `HealthWorker.roles()`, `PatientRegistry.with_sample_data()` |
| Static methods (`@staticmethod`) | `Patient.validate_age()`, `Patient.age_group()`, `HealthWorker.parse_date()`, `HealthWorker.build_vitals()`, `HealthWorker.parse_blood_pressure()` |

## 6. Alignment with the Digital Public Goods Standard

| # | DPG indicator | How PRS meets it |
|---|---|---|
| 1 | Relevance to the Sustainable Development Goals | Supports **SDG 3 (Good Health and Well-being)** by helping health workers keep accurate records, follow up patients with fever or high blood pressure, and track common diseases such as malaria. |
| 2 | Use of an approved open licence | Released under the **MIT Licence** (see `LICENSE`). |
| 3 | Clear ownership | Copyright holder stated in `LICENSE`; code publicly hosted on GitHub. |
| 4 | Platform independence | Pure Python standard library: no paid software, no internet connection and no proprietary dependencies. |
| 5 | Documentation | This README, docstrings on every class and method, a guided `demo.py` and 35 automated tests. |
| 6 | Mechanism for extracting data | Menu option 8 exports statistics to **CSV**, an open format. |
| 7 | Adherence to privacy and applicable laws | **No direct identifiers are stored**: no names, phone numbers, national ID numbers, addresses or exact birth dates. Patients are pseudonymised with a generated code that only the clinic's own register links to a person. Diagnoses are chosen from a fixed list, with no free-text notes that could leak personal details. |
| 8 | Adherence to standards and best practices | PEP 8 style, type hints, ISO 8601 dates (`YYYY-MM-DD`), standard public-health age bands, input validation and unit tests. |
| 9 | Do no harm by design | Exported statistics contain only counts by district and diagnosis. Counts below 5 are replaced by `<5` (small-number suppression) so a rare case cannot point to one person. Saved visits cannot be edited, which prevents silent changes to medical history. |

### Inclusive and accessible design

- Plain-language, numbered menus that work well with screen readers; no
  information depends on colour.
- Options can be chosen by **number or name**, and text is case-insensitive.
- Short answers are accepted (`F`, `M`, `P`), and pressing Enter uses today's
  date or skips an unmeasured blood pressure.
- Every error explains how to fix it; after three wrong answers the user goes
  back to the main menu instead of being trapped.
- "Prefer not to say" is offered for sex.
- Works fully offline on low-cost computers.

### Modular and reusable

The `prs` package contains no `input()` calls, so its classes can be reused by
a web app, a tablet app or an SMS service without changes. `main.py` is just
one interface built on top of them.

## 7. Example usage (sample input and output)

### Registering a health worker and a patient

```
Choose an option (0-9): 2

Register a health worker
------------------------
    1. Doctor                   2. Nurse                    3. Midwife
    4. Community Health Officer
Role (number or name): 2
Facility district (number or name): Bo
Success: health worker registered with staff code HW-0001.

Choose an option (0-9): 1

Register a patient
------------------
Privacy notice: no names, phone numbers or ID numbers are collected.
Keep the patient code shown at the end in the clinic's own register.
Age in years: thirty
  Error: Age must be a whole number of years, e.g. 34. (2 attempt(s) left)
Age in years: 34
Sex (F / M / P = prefer not to say): F
District (number or name): 1
Success: patient registered with code PAT-0001.
```

### Recording a visit

```
Choose an option (0-9): 3

Record a visit
--------------
Your staff code: HW-0001
Patient code: PAT-0001
Visit date YYYY-MM-DD (press Enter for today): 2026-03-02
Visit type (number or name): 1
Diagnosis (number or name): malaria
Temperature in C (e.g. 37.2): 38.9
Weight in kg (e.g. 64.5): 62
Blood pressure e.g. 120/80 (press Enter if not measured): 118/76
Success: Outpatient visit on 2026-03-02 saved for PAT-0001.
Vitals: 38.9 C FEVER | 62 kg | 118/76 mmHg - Normal
Follow-up recommended: fever (38.9 C).
```

### Follow-up list and diagnosis summary (after loading sample data)

```
Patients needing follow-up
--------------------------
PAT-0002 (Bo): fever (39.2 C)
PAT-0003 (Bo): blood pressure high (stage 2); chronic condition: Hypertension
PAT-0004 (Bo): fever (38.4 C)
PAT-0005 (Bo): fever (39.6 C)
PAT-0007 (Kenema): chronic condition: Diabetes
PAT-0010 (Bo): fever (38.6 C)
Total: 6 patient(s).

Diagnosis                 Visits    Share
-----------------------------------------
Malaria                        5      28%
Routine check                  4      22%
Diabetes                       2      11%
Hypertension                   2      11%
Typhoid                        2      11%
Diarrhoeal disease             1       6%
Injury                         1       6%
Respiratory infection          1       6%
-----------------------------------------
Total                         18
```

### Anonymised statistics export (`health_statistics.csv`)

```
district,diagnosis,visits
Bo,Hypertension,<5
Bo,Malaria,5
Bo,Routine check,<5
...
```

### Using the classes in your own code

```python
from prs import HealthWorker, Patient, PatientRegistry, add_record, display_records

registry = PatientRegistry()
nurse = HealthWorker("Nurse", "Bo")
patient = Patient(34, "F", "Bo")

vitals = HealthWorker.build_vitals(38.9, 62, 118, 76)
nurse.record_visit(patient, "2026-03-02", "Outpatient", "Malaria", vitals)

add_record(registry, nurse)
add_record(registry, patient)
display_records(registry)
print(patient.needs_follow_up())   # ('fever (38.9 C)',)
```

## 8. Testing

```bash
python -m unittest discover -v
```

The 35 tests cover object creation, every validation rule, vital-sign
categories, follow-up logic, the dictionary registry, the anonymised export and
complete scripted sessions of the menu program.

## 9. Limitations and future work

- Data is kept in memory while the program runs; encrypted storage in a file
  or database would be the next step, with user log-in and access control.
- Translations into Krio, Mende and Temne would make the tool more inclusive.
- Blood-pressure categories use adult ranges; child-specific ranges could be added.

## 10. Licence

Released under the [MIT Licence](LICENSE).
