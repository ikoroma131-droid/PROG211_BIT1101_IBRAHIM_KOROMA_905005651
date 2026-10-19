"""Patient Record System - interactive command-line program.

Run with:  python main.py

Accessibility choices (DPG: inclusive design):
  * plain-language, numbered menus that work with screen readers;
  * no colours or symbols are needed to understand any message;
  * every input is checked and the user is told exactly how to fix mistakes;
  * text is case-insensitive and short answers are accepted (F/M/P);
  * runs offline on any computer with Python 3.8+ and no extra packages.
"""

from __future__ import annotations

import sys
from datetime import date
from typing import Callable, Optional, Tuple, TypeVar

from prs import (
    DIAGNOSES,
    DISTRICTS,
    VISIT_TYPES,
    HealthWorker,
    Patient,
    PatientRegistry,
    add_record,
    display_records,
)
from prs.models import WORKER_ROLES, check_range, match_option

APP_TITLE = "PATIENT RECORD SYSTEM (PRS) - Sierra Leone"
EXPORT_FILE = "health_statistics.csv"
T = TypeVar("T")

MENU: Tuple[Tuple[str, str], ...] = (
    ("1", "Register a patient"),
    ("2", "Register a health worker"),
    ("3", "Record a visit"),
    ("4", "View all records"),
    ("5", "View one patient's history"),
    ("6", "Patients needing follow-up"),
    ("7", "Diagnosis summary"),
    ("8", "Export anonymised statistics (CSV)"),
    ("9", "Load sample data"),
    ("0", "Exit"),
)


class UserExit(Exception):
    """Raised when the user closes input (Ctrl+D / Ctrl+Z) or presses Ctrl+C."""


# --------------------------------------------------------------------------- #
# Input helpers
# --------------------------------------------------------------------------- #
def ask(prompt: str) -> str:
    """Read one line of input, turning Ctrl+C / end-of-input into UserExit."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        raise UserExit from None


def ask_until_valid(prompt: str, convert: Callable[[str], T], attempts: int = 3) -> Optional[T]:
    """Ask repeatedly until ``convert`` accepts the answer.

    Returns the converted value, or None after too many invalid attempts so
    the user is never trapped in a loop.
    """
    for attempt in range(1, attempts + 1):
        answer = ask(prompt)
        try:
            return convert(answer)
        except ValueError as error:
            remaining = attempts - attempt
            hint = f" ({remaining} attempt(s) left)" if remaining else ""
            print(f"  Error: {error}{hint}")
    print("  Too many invalid attempts. Returning to the main menu.")
    return None


def choose_from(options: Tuple[str, ...], name: str) -> Callable[[str], str]:
    """Build a converter that accepts an option by name or by its number."""

    def convert(text: str) -> str:
        if text.isdigit() and 1 <= int(text) <= len(options):
            return options[int(text) - 1]
        matched = match_option(text, options)
        if matched is None:
            raise ValueError(f"{name} not recognised. Type its number or its name.")
        return matched

    return convert


def show_options(options: Tuple[str, ...]) -> None:
    """Print options numbered from 1, three per line."""
    cells = tuple(f"{i:>2}. {option}" for i, option in enumerate(options, start=1))
    for start in range(0, len(cells), 3):
        print("   " + "".join(f"{cell:<28}" for cell in cells[start:start + 3]).rstrip())


def show_heading(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


# --------------------------------------------------------------------------- #
# Menu actions
# --------------------------------------------------------------------------- #
def register_patient(registry: PatientRegistry) -> None:
    show_heading("Register a patient")
    print("Privacy notice: no names, phone numbers or ID numbers are collected.")
    print("Keep the patient code shown at the end in the clinic's own register.")
    age = ask_until_valid("Age in years: ", Patient.validate_age)
    if age is None:
        return

    def to_sex(text: str) -> str:
        sex = Patient.normalise_sex(text)
        if sex is None:
            raise ValueError("Type F (Female), M (Male) or P (Prefer not to say).")
        return sex

    sex = ask_until_valid("Sex (F / M / P = prefer not to say): ", to_sex)
    if sex is None:
        return
    show_options(DISTRICTS)
    district = ask_until_valid("District (number or name): ", choose_from(DISTRICTS, "District"))
    if district is None:
        return
    patient = Patient(age, sex, district)
    add_record(registry, patient)
    print(f"Success: patient registered with code {patient.patient_id}.")


def register_worker(registry: PatientRegistry) -> None:
    show_heading("Register a health worker")
    show_options(WORKER_ROLES)
    role = ask_until_valid("Role (number or name): ", choose_from(WORKER_ROLES, "Role"))
    if role is None:
        return
    show_options(DISTRICTS)
    district = ask_until_valid("Facility district (number or name): ", choose_from(DISTRICTS, "District"))
    if district is None:
        return
    worker = HealthWorker(role, district)
    add_record(registry, worker)
    print(f"Success: health worker registered with staff code {worker.worker_id}.")


def record_visit(registry: PatientRegistry) -> None:
    show_heading("Record a visit")
    if not registry.workers() or not registry.patients():
        print("Please register at least one health worker (option 2) and one patient (option 1).")
        return

    def to_worker(text: str) -> HealthWorker:
        worker = registry.get_worker(text)
        if worker is None:
            raise ValueError("No health worker with that code (example: HW-0001).")
        return worker

    def to_patient(text: str) -> Patient:
        patient = registry.get_patient(text)
        if patient is None:
            raise ValueError("No patient with that code (example: PAT-0001).")
        return patient

    def to_date(text: str) -> date:
        return date.today() if not text else HealthWorker.parse_date(text)

    worker = ask_until_valid("Your staff code: ", to_worker)
    if worker is None:
        return
    patient = ask_until_valid("Patient code: ", to_patient)
    if patient is None:
        return
    visit_date = ask_until_valid("Visit date YYYY-MM-DD (press Enter for today): ", to_date)
    if visit_date is None:
        return
    show_options(VISIT_TYPES)
    visit_type = ask_until_valid("Visit type (number or name): ", choose_from(VISIT_TYPES, "Visit type"))
    if visit_type is None:
        return
    show_options(DIAGNOSES)
    diagnosis = ask_until_valid("Diagnosis (number or name): ", choose_from(DIAGNOSES, "Diagnosis"))
    if diagnosis is None:
        return
    temperature = ask_until_valid(
        "Temperature in C (e.g. 37.2): ", lambda t: check_range(t, "Temperature (C)", 30, 45)
    )
    if temperature is None:
        return
    weight = ask_until_valid(
        "Weight in kg (e.g. 64.5): ", lambda w: check_range(w, "Weight (kg)", 0.5, 300)
    )
    if weight is None:
        return
    bp = ask_until_valid(
        "Blood pressure e.g. 120/80 (press Enter if not measured): ",
        HealthWorker.parse_blood_pressure,
    )
    if bp is None:
        return
    try:
        vitals = HealthWorker.build_vitals(temperature, weight, bp[0], bp[1])
        visit = worker.record_visit(patient, visit_date, visit_type, diagnosis, vitals)
    except ValueError as error:
        print(f"  Error: {error} The visit was not saved.")
        return
    print(f"Success: {visit.visit_type} visit on {visit.visit_date.isoformat()} saved "
          f"for {patient.patient_id}.")
    print(f"Vitals: {visit.vitals.summary()}")
    reasons = patient.needs_follow_up()
    if reasons:
        print("Follow-up recommended: " + "; ".join(reasons) + ".")


def view_one_patient(registry: PatientRegistry) -> None:
    show_heading("View one patient's history")
    patient = registry.get_patient(ask("Patient code: "))
    if patient is None:
        print("No patient with that code.")
        return
    print(patient.display_info())
    reasons = patient.needs_follow_up()
    print("Follow-up: " + ("; ".join(reasons) if reasons else "none needed"))


def follow_up(registry: PatientRegistry) -> None:
    show_heading("Patients needing follow-up")
    rows = registry.follow_up_list()
    if not rows:
        print("No patients currently need follow-up.")
        return
    for patient, reasons in rows:
        print(f"{patient.patient_id} ({patient.district}): " + "; ".join(reasons))
    print(f"Total: {len(rows)} patient(s).")


def diagnosis_summary(registry: PatientRegistry) -> None:
    show_heading("Diagnosis summary (all visits)")
    print(PatientRegistry.format_counts(registry.diagnosis_summary()))


def export_statistics(registry: PatientRegistry) -> None:
    show_heading("Export anonymised statistics")
    try:
        rows, suppressed = registry.export_statistics(EXPORT_FILE)
    except OSError as error:
        print(f"  Error: could not write the file ({error}).")
        return
    print(f"Success: {rows} row(s) of visit counts written to '{EXPORT_FILE}'.")
    print(f"For privacy, {suppressed} small count(s) were shown as "
          f"'<{PatientRegistry.MIN_CELL_COUNT}' and no patient codes were exported.")


def load_sample(registry: PatientRegistry) -> PatientRegistry:
    show_heading("Load sample data")
    if registry.patients() or registry.workers():
        answer = ask("This replaces the current data. Continue? (y/n): ").lower()
        if answer not in ("y", "yes"):
            print("Cancelled. Your data has not changed.")
            return registry
    Patient.reset_counter()
    HealthWorker.reset_counter()
    sample = PatientRegistry.with_sample_data()
    print(f"Loaded {len(sample.workers())} health workers, {len(sample)} patients and "
          f"{len(sample.all_visits())} visits (all fictional).")
    return sample


# --------------------------------------------------------------------------- #
# Main loop
# --------------------------------------------------------------------------- #
def print_menu() -> None:
    print()
    print("=" * len(APP_TITLE))
    print(APP_TITLE)
    print("=" * len(APP_TITLE))
    for key, label in MENU:
        print(f"  {key}. {label}")


def run() -> int:
    registry = PatientRegistry()
    print("Welcome! Type the number of an option and press Enter.")
    try:
        while True:
            print_menu()
            choice = ask("Choose an option (0-9): ")
            if choice == "1":
                register_patient(registry)
            elif choice == "2":
                register_worker(registry)
            elif choice == "3":
                record_visit(registry)
            elif choice == "4":
                show_heading("All records")
                display_records(registry)
            elif choice == "5":
                view_one_patient(registry)
            elif choice == "6":
                follow_up(registry)
            elif choice == "7":
                diagnosis_summary(registry)
            elif choice == "8":
                export_statistics(registry)
            elif choice == "9":
                registry = load_sample(registry)
            elif choice == "0":
                print("Goodbye. Thank you for using PRS.")
                return 0
            else:
                print("  Error: please type a number from 0 to 9.")
    except UserExit:
        print("\nInput closed. Goodbye.")
        return 0


if __name__ == "__main__":
    sys.exit(run())
