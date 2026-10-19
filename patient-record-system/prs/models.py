"""Domain models for the Patient Record System (PRS).

Task 1 (OOP Basics): the classes ``Patient`` and ``HealthWorker`` model the
real world. Each has attributes and methods, and they interact: a health
worker records a visit, and that visit is added to the patient's record.

Task 3 (Methods): the classes use instance methods, class methods
(``@classmethod``) and static methods (``@staticmethod``).

Privacy by design (DPG): patients are identified only by a system-generated
code (e.g. PAT-0001). No names, phone numbers, national ID numbers, addresses
or free-text notes are stored, so a record cannot reveal who the patient is.
The link between a code and a real person stays in the clinic's own register.

Important: this is a record-keeping tool for learning purposes. It does not
diagnose illness; diagnoses are entered by qualified health workers.
"""

from __future__ import annotations

import re
from datetime import date
from typing import NamedTuple, Optional, Tuple, Union

DateInput = Union[date, str]  # a date object or text in YYYY-MM-DD format
Number = Union[int, float, str]  # numbers may arrive as text typed by a user

# Reference data is stored in tuples because it must never change while the
# program runs (immutable).
DISTRICTS: Tuple[str, ...] = (
    "Bo", "Bombali", "Bonthe", "Falaba", "Kailahun", "Kambia", "Karene",
    "Kenema", "Koinadugu", "Kono", "Moyamba", "Port Loko", "Pujehun",
    "Tonkolili", "Western Area Rural", "Western Area Urban",
)
SEXES: Tuple[str, ...] = ("Female", "Male", "Prefer not to say")
VISIT_TYPES: Tuple[str, ...] = (
    "Outpatient", "Follow-up", "Antenatal", "Immunisation", "Emergency",
)
DIAGNOSES: Tuple[str, ...] = (
    "Malaria", "Typhoid", "Respiratory infection", "Diarrhoeal disease",
    "Hypertension", "Diabetes", "Malnutrition", "Injury", "Routine check",
    "Other",
)
CHRONIC_CONDITIONS: Tuple[str, ...] = ("Hypertension", "Diabetes")
WORKER_ROLES: Tuple[str, ...] = (
    "Doctor", "Nurse", "Midwife", "Community Health Officer",
)
FIRST_VALID_DATE = date(2000, 1, 1)


def check_range(value: Number, name: str, low: float, high: float) -> float:
    """Convert ``value`` to a number and check it lies between low and high."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number.") from None
    if not low <= number <= high:
        raise ValueError(f"{name} must be between {low:g} and {high:g}.")
    return number


def match_option(value: str, options: Tuple[str, ...]) -> Optional[str]:
    """Return the option that matches ``value`` (ignoring case and extra
    spaces), or None. Used for districts, diagnoses, roles and so on."""
    cleaned = " ".join((value or "").split()).lower()
    for option in options:
        if option.lower() == cleaned:
            return option
    return None


# --------------------------------------------------------------------------- #
# Immutable records (tuples)
# --------------------------------------------------------------------------- #
class VitalSigns(NamedTuple):
    """Measurements taken at a visit. Blood pressure is optional because it is
    not measured at every visit (for example, infant immunisations)."""

    temperature_c: float
    weight_kg: float
    systolic: Optional[int] = None
    diastolic: Optional[int] = None

    def has_fever(self) -> bool:
        """A temperature of 38.0 °C or higher is recorded as a fever."""
        return self.temperature_c >= 38.0

    def bp_category(self) -> str:
        """Blood pressure category based on the American Heart Association
        adult ranges. Returns 'Not measured' if BP was not taken."""
        if self.systolic is None or self.diastolic is None:
            return "Not measured"
        s, d = self.systolic, self.diastolic
        if s > 180 or d > 120:
            return "Hypertensive crisis"
        if s >= 140 or d >= 90:
            return "High (stage 2)"
        if s >= 130 or d >= 80:
            return "High (stage 1)"
        if s >= 120:
            return "Elevated"
        return "Normal"

    def summary(self) -> str:
        """One readable line describing the vital signs."""
        bp = (
            f"{self.systolic}/{self.diastolic} mmHg - {self.bp_category()}"
            if self.systolic is not None and self.diastolic is not None
            else "BP not measured"
        )
        fever = " FEVER" if self.has_fever() else ""
        return f"{self.temperature_c:.1f} C{fever} | {self.weight_kg:g} kg | {bp}"


class Visit(NamedTuple):
    """One visit to a health facility. Immutable: once a visit is saved it
    cannot be edited, which protects the integrity of the medical record."""

    visit_date: date
    visit_type: str
    diagnosis: str
    vitals: VitalSigns
    worker_id: str


# --------------------------------------------------------------------------- #
# Patient
# --------------------------------------------------------------------------- #
class Patient:
    """A patient, identified by a pseudonymous code instead of a name."""

    ID_PREFIX = "PAT"
    MAX_AGE = 120
    _next_number = 1  # class attribute shared by every Patient object

    def __init__(self, age: Number, sex: str, district: str) -> None:
        clean_age = Patient.validate_age(age)
        clean_sex = Patient.normalise_sex(sex)
        if clean_sex is None:
            raise ValueError("Sex must be Female, Male or Prefer not to say (F/M/P).")
        clean_district = match_option(district, DISTRICTS)
        if clean_district is None:
            raise ValueError(f"Unknown district: '{district}'.")

        # The ID is only created after every check has passed.
        self.patient_id: str = Patient.generate_id()
        self.age: int = clean_age
        self.sex: str = clean_sex
        self.district: str = clean_district
        self._visits: Tuple[Visit, ...] = ()

    # ---- class methods ---------------------------------------------------- #
    @classmethod
    def generate_id(cls) -> str:
        """Create the next unique patient code, e.g. PAT-0001."""
        new_id = f"{cls.ID_PREFIX}-{cls._next_number:04d}"
        cls._next_number += 1
        return new_id

    @classmethod
    def reset_counter(cls) -> None:
        """Restart ID numbering (used by the automated tests)."""
        cls._next_number = 1

    @classmethod
    def from_tuple(cls, data: Tuple[Number, str, str]) -> "Patient":
        """Alternative constructor: build a Patient from (age, sex, district)."""
        age, sex, district = data
        return cls(age, sex, district)

    # ---- static methods --------------------------------------------------- #
    @staticmethod
    def validate_age(value: Number) -> int:
        """Check that an age is a whole number of years between 0 and 120."""
        text = str(value).strip()
        if not re.fullmatch(r"\d{1,3}", text):
            raise ValueError("Age must be a whole number of years, e.g. 34.")
        age = int(text)
        if age > Patient.MAX_AGE:
            raise ValueError(f"Age must be between 0 and {Patient.MAX_AGE}.")
        return age

    @staticmethod
    def normalise_sex(value: str) -> Optional[str]:
        """Accept full words or the shortcuts F, M and P."""
        shortcuts = {"f": "Female", "m": "Male", "p": "Prefer not to say"}
        cleaned = (value or "").strip().lower()
        return shortcuts.get(cleaned) or match_option(cleaned, SEXES)

    @staticmethod
    def age_group(age: int) -> str:
        """Standard public-health age bands used in reports."""
        if age < 5:
            return "0-4"
        if age < 15:
            return "5-14"
        if age < 25:
            return "15-24"
        if age < 45:
            return "25-44"
        if age < 65:
            return "45-64"
        return "65+"

    # ---- instance methods ------------------------------------------------- #
    @property
    def visits(self) -> Tuple[Visit, ...]:
        """All visits, oldest first (read-only tuple)."""
        return self._visits

    def add_visit(self, visit: Visit) -> None:
        """Add a visit to this patient's history, keeping date order.

        Normally called by ``HealthWorker.record_visit``, which validates the
        visit details first.
        """
        if not isinstance(visit, Visit):
            raise TypeError("visit must be a Visit record.")
        self._visits = tuple(sorted(self._visits + (visit,), key=lambda v: v.visit_date))

    def visit_count(self) -> int:
        """Number of recorded visits."""
        return len(self._visits)

    def latest_visit(self) -> Optional[Visit]:
        """The most recent visit, or None if the patient has no visits."""
        return self._visits[-1] if self._visits else None

    def has_condition(self, diagnosis: str) -> bool:
        """True if the diagnosis appears in any visit."""
        wanted = match_option(diagnosis, DIAGNOSES)
        return any(v.diagnosis == wanted for v in self._visits)

    def needs_follow_up(self) -> Tuple[str, ...]:
        """Reasons this patient should be followed up (empty if none).

        Based on the latest visit: fever, stage 2 or crisis blood pressure,
        or any chronic condition on record.
        """
        latest = self.latest_visit()
        if latest is None:
            return ()
        reasons: Tuple[str, ...] = ()
        if latest.vitals.has_fever():
            reasons += (f"fever ({latest.vitals.temperature_c:.1f} C)",)
        if latest.vitals.bp_category() in ("High (stage 2)", "Hypertensive crisis"):
            reasons += (f"blood pressure {latest.vitals.bp_category().lower()}",)
        reasons += tuple(
            f"chronic condition: {c}" for c in CHRONIC_CONDITIONS if self.has_condition(c)
        )
        return reasons

    def update_record(
        self, age: Optional[Number] = None, district: Optional[str] = None
    ) -> None:
        """Update age and/or district. All checks run before anything changes."""
        new_age = Patient.validate_age(age) if age is not None else self.age
        new_district = self.district
        if district is not None:
            matched = match_option(district, DISTRICTS)
            if matched is None:
                raise ValueError(f"Unknown district: '{district}'.")
            new_district = matched
        self.age, self.district = new_age, new_district

    def display_info(self, include_visits: bool = True) -> str:
        """Return a readable summary of the patient and their visit history."""
        lines: Tuple[str, ...] = (
            f"Patient {self.patient_id} | Age {self.age} ({Patient.age_group(self.age)})"
            f" | {self.sex} | {self.district} | Visits: {self.visit_count()}",
        )
        if include_visits:
            if not self._visits:
                lines += ("   No visits recorded yet.",)
            for v in self._visits:
                lines += (
                    f"   {v.visit_date.isoformat()} {v.visit_type:<12} {v.diagnosis:<22}"
                    f" by {v.worker_id}",
                    f"      Vitals: {v.vitals.summary()}",
                )
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"Patient(patient_id={self.patient_id!r}, age={self.age!r}, "
            f"sex={self.sex!r}, district={self.district!r})"
        )


# --------------------------------------------------------------------------- #
# HealthWorker
# --------------------------------------------------------------------------- #
class HealthWorker:
    """A health worker who records patient visits, identified by staff code."""

    ID_PREFIX = "HW"
    _next_number = 1

    def __init__(self, role: str, district: str) -> None:
        clean_role = match_option(role, WORKER_ROLES)
        if clean_role is None:
            raise ValueError(f"Role must be one of: {', '.join(WORKER_ROLES)}.")
        clean_district = match_option(district, DISTRICTS)
        if clean_district is None:
            raise ValueError(f"Unknown district: '{district}'.")

        self.worker_id: str = HealthWorker.generate_id()
        self.role: str = clean_role
        self.district: str = clean_district
        self.visits_recorded: int = 0

    # ---- class methods ---------------------------------------------------- #
    @classmethod
    def generate_id(cls) -> str:
        """Create the next unique staff code, e.g. HW-0001."""
        new_id = f"{cls.ID_PREFIX}-{cls._next_number:04d}"
        cls._next_number += 1
        return new_id

    @classmethod
    def reset_counter(cls) -> None:
        """Restart ID numbering (used by the automated tests)."""
        cls._next_number = 1

    @classmethod
    def roles(cls) -> str:
        """The supported roles as one readable line."""
        return ", ".join(WORKER_ROLES)

    # ---- static methods --------------------------------------------------- #
    @staticmethod
    def parse_date(value: DateInput) -> date:
        """Turn 'YYYY-MM-DD' text (or a date) into a date, rejecting dates in
        the future or before the year 2000."""
        if isinstance(value, date):
            visit_date = value
        else:
            try:
                visit_date = date.fromisoformat(str(value).strip())
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format, e.g. 2026-03-15.") from None
        if not FIRST_VALID_DATE <= visit_date <= date.today():
            raise ValueError("Date cannot be in the future or before 2000-01-01.")
        return visit_date

    @staticmethod
    def build_vitals(
        temperature_c: Number,
        weight_kg: Number,
        systolic: Optional[Number] = None,
        diastolic: Optional[Number] = None,
    ) -> VitalSigns:
        """Validate measurements and return a VitalSigns record.

        Blood pressure is optional: leave both values as None (or empty text)
        if it was not measured.
        """
        temperature = round(check_range(temperature_c, "Temperature (C)", 30, 45), 1)
        weight = round(check_range(weight_kg, "Weight (kg)", 0.5, 300), 1)
        sys_bp, dia_bp = HealthWorker.check_blood_pressure(systolic, diastolic)
        return VitalSigns(temperature, weight, sys_bp, dia_bp)

    @staticmethod
    def check_blood_pressure(
        systolic: Optional[Number], diastolic: Optional[Number]
    ) -> Tuple[Optional[int], Optional[int]]:
        """Validate a blood pressure pair. Returns (None, None) if not measured."""
        blank = (None, "")
        if systolic in blank and diastolic in blank:
            return None, None
        if systolic in blank or diastolic in blank:
            raise ValueError("Enter both systolic and diastolic blood pressure, or neither.")
        sys_bp = check_range(systolic, "Systolic BP", 50, 260)  # type: ignore[arg-type]
        dia_bp = check_range(diastolic, "Diastolic BP", 30, 160)  # type: ignore[arg-type]
        if not sys_bp.is_integer() or not dia_bp.is_integer():
            raise ValueError("Blood pressure must be whole numbers, e.g. 120/80.")
        if sys_bp <= dia_bp:
            raise ValueError("Systolic BP (top number) must be higher than diastolic.")
        return int(sys_bp), int(dia_bp)

    @staticmethod
    def parse_blood_pressure(text: str) -> Tuple[Optional[int], Optional[int]]:
        """Read blood pressure typed as '120/80'. Empty text means not measured."""
        cleaned = (text or "").replace(" ", "")
        if not cleaned:
            return None, None
        parts = cleaned.split("/")
        if len(parts) != 2:
            raise ValueError("Type blood pressure as two numbers, e.g. 120/80.")
        return HealthWorker.check_blood_pressure(parts[0], parts[1])

    # ---- instance methods ------------------------------------------------- #
    def record_visit(
        self,
        patient: Patient,
        visit_date: DateInput,
        visit_type: str,
        diagnosis: str,
        vitals: VitalSigns,
    ) -> Visit:
        """Validate and save a visit to the patient's record.

        This is the main interaction between the two classes: the health
        worker creates the Visit and the Patient object stores it.
        """
        if not isinstance(patient, Patient):
            raise TypeError("patient must be a Patient object.")
        if not isinstance(vitals, VitalSigns):
            raise TypeError("vitals must be a VitalSigns record.")
        clean_date = HealthWorker.parse_date(visit_date)
        clean_type = match_option(visit_type, VISIT_TYPES)
        if clean_type is None:
            raise ValueError(f"Visit type must be one of: {', '.join(VISIT_TYPES)}.")
        clean_diagnosis = match_option(diagnosis, DIAGNOSES)
        if clean_diagnosis is None:
            raise ValueError(f"Diagnosis must be one of: {', '.join(DIAGNOSES)}.")
        if clean_type == "Antenatal" and patient.sex == "Male":
            raise ValueError("An antenatal visit cannot be recorded for a male patient.")

        visit = Visit(clean_date, clean_type, clean_diagnosis, vitals, self.worker_id)
        patient.add_visit(visit)
        self.visits_recorded += 1
        return visit

    def display_info(self) -> str:
        """Return a readable summary of the health worker."""
        return (
            f"Health worker {self.worker_id} | {self.role} | {self.district} | "
            f"Visits recorded: {self.visits_recorded}"
        )

    def __repr__(self) -> str:
        return (
            f"HealthWorker(worker_id={self.worker_id!r}, role={self.role!r}, "
            f"district={self.district!r})"
        )
