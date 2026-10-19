"""Guided demonstration of every assignment requirement.

Run with:  python demo.py

This script needs no keyboard input, so it produces the same sample output
every time. It is the quickest way for a marker to see Tasks 1, 2 and 3.
All patients and health workers shown are fictional.
"""

from __future__ import annotations

from prs import HealthWorker, Patient, PatientRegistry, add_record, display_records


def section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    # ------------------------------------------------------------------ #
    section("TASK 1 - Classes, attributes, objects and their interaction")
    # ------------------------------------------------------------------ #
    nurse = HealthWorker("Nurse", "Bo")                  # object creation
    adult = Patient(34, "F", "bo")                       # input is case-insensitive
    child = Patient(6, "Male", "Bo")
    print("Created:", nurse)
    print("Created:", adult)
    print("Created:", child)

    print("\nInteraction: the health worker records a visit and the patient stores it.")
    vitals = HealthWorker.build_vitals(38.9, 62, 118, 76)
    visit = nurse.record_visit(adult, "2026-03-02", "Outpatient", "Malaria", vitals)
    print("Visit saved:", visit.visit_date, visit.visit_type, visit.diagnosis)
    nurse.record_visit(adult, "2026-03-16", "Follow-up", "Routine check",
                       HealthWorker.build_vitals(36.8, 62, 116, 75))
    nurse.record_visit(child, "2026-04-10", "Outpatient", "malaria",
                       HealthWorker.build_vitals(39.2, 21))   # BP not measured
    print(adult.display_info())
    print(nurse.display_info())

    adult.update_record(age=35)
    print("\nAfter update_record(age=35):", adult.display_info(include_visits=False))

    # ------------------------------------------------------------------ #
    section("TASK 2 - Data structure: a dictionary keyed by unique ID")
    # ------------------------------------------------------------------ #
    registry = PatientRegistry()
    for record in (nurse, adult, child):
        print(f"add_record() stored {add_record(registry, record)}")  # simple add function
    print(f"\nDictionary look-up by key: registry.get_patient('PAT-0002') -> "
          f"{registry.get_patient('PAT-0002')!r}")
    print("\nLooping through the dictionary with display_records():\n")
    display_records(registry)                                       # simple display function

    print("\nOptional tuples: each visit and its vital signs are immutable NamedTuples:")
    first = adult.visits[0]
    print(f"   {first.vitals!r}")
    temperature, weight, systolic, diastolic = first.vitals          # tuple unpacking
    print(f"   Unpacked -> {temperature} C, {weight} kg, BP {systolic}/{diastolic}")
    try:
        first.diagnosis = "Typhoid"  # type: ignore[misc]
    except AttributeError:
        print("   Attempt to change a saved visit was blocked (tuples are immutable).")

    # ------------------------------------------------------------------ #
    section("TASK 3 - Instance, class and static methods")
    # ------------------------------------------------------------------ #
    print("Instance method  adult.visit_count()              ->", adult.visit_count())
    print("Instance method  child.needs_follow_up()          ->", child.needs_follow_up())
    print("Class method     HealthWorker.roles()             ->", HealthWorker.roles())
    print("Class method     Patient.from_tuple((67,'F','Kenema')) ->",
          Patient.from_tuple((67, "F", "Kenema")))
    print("Static method    Patient.age_group(6)             ->", Patient.age_group(6))
    print("Static method    HealthWorker.parse_blood_pressure('150/95') ->",
          HealthWorker.parse_blood_pressure("150/95"))

    # ------------------------------------------------------------------ #
    section("DPG - Privacy protection and input validation")
    # ------------------------------------------------------------------ #
    bad_inputs = (
        ("Patient(age='thirty', ...)", lambda: Patient("thirty", "F", "Bo")),
        ("Patient(..., district='Lagos')", lambda: Patient(30, "F", "Lagos")),
        ("visit dated in the future", lambda: nurse.record_visit(
            adult, "2099-01-01", "Outpatient", "Malaria", vitals)),
        ("antenatal visit for a male patient", lambda: nurse.record_visit(
            child, "2026-05-01", "Antenatal", "Routine check", vitals)),
        ("blood pressure '80/120'", lambda: HealthWorker.parse_blood_pressure("80/120")),
        ("temperature 55 C", lambda: HealthWorker.build_vitals(55, 60)),
    )
    for label, action in bad_inputs:
        try:
            action()
        except ValueError as error:
            print(f"Rejected {label}: {error}")

    # ------------------------------------------------------------------ #
    section("Reports with the full (fictional) sample data set")
    # ------------------------------------------------------------------ #
    Patient.reset_counter()
    HealthWorker.reset_counter()
    sample = PatientRegistry.with_sample_data()                     # class method constructor
    print(PatientRegistry.format_counts(sample.diagnosis_summary()))
    print("\nPatients needing follow-up:")
    for patient, reasons in sample.follow_up_list():
        print(f"   {patient.patient_id} ({patient.district}): " + "; ".join(reasons))
    rows, suppressed = sample.export_statistics("health_statistics.csv")
    print(f"\nExported {rows} rows to health_statistics.csv "
          f"({suppressed} small counts shown as '<5' for privacy).")


if __name__ == "__main__":
    main()
