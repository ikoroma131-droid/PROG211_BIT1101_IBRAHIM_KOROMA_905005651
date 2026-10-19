"""The PatientRegistry: where all Patient and HealthWorker objects are stored.

Task 2 (Python Data Structures): the chosen data structure is the
**dictionary**. Objects are stored with their unique ID as the key, e.g.
``{"PAT-0001": <Patient>, "PAT-0002": <Patient>}``, so any record can be
found instantly by its code. Tuples (optional bonus) are used for data that
must not change, such as visits, vital signs and report rows.

The simple functions ``add_record`` and ``display_records`` at the bottom of
this module add and display records from the dictionary.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterator, Optional, Tuple, Union

from prs.models import DIAGNOSES, HealthWorker, Patient, Visit, match_option

CountRow = Tuple[str, int]                      # (label, number of visits)
FollowUpRow = Tuple[Patient, Tuple[str, ...]]   # (patient, reasons)


class PatientRegistry:
    """Stores patients and health workers in dictionaries keyed by their IDs."""

    # Privacy rule for shared statistics: any count below this number is
    # replaced by "<5" so that rare cases cannot point to one individual.
    MIN_CELL_COUNT = 5
    EXPORT_COLUMNS: Tuple[str, ...] = ("district", "diagnosis", "visits")

    def __init__(self) -> None:
        self._patients: Dict[str, Patient] = {}
        self._workers: Dict[str, HealthWorker] = {}

    # ---- adding records --------------------------------------------------- #
    def add_patient(self, patient: Patient) -> Patient:
        """Store a patient under its patient_id."""
        if not isinstance(patient, Patient):
            raise TypeError("Only Patient objects can be added as patients.")
        if patient.patient_id in self._patients:
            raise ValueError(f"Patient {patient.patient_id} is already registered.")
        self._patients[patient.patient_id] = patient
        return patient

    def add_worker(self, worker: HealthWorker) -> HealthWorker:
        """Store a health worker under its worker_id."""
        if not isinstance(worker, HealthWorker):
            raise TypeError("Only HealthWorker objects can be added as workers.")
        if worker.worker_id in self._workers:
            raise ValueError(f"Health worker {worker.worker_id} is already registered.")
        self._workers[worker.worker_id] = worker
        return worker

    # ---- looking records up ----------------------------------------------- #
    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Return the patient with this code (case-insensitive), or None."""
        return self._patients.get((patient_id or "").strip().upper())

    def get_worker(self, worker_id: str) -> Optional[HealthWorker]:
        """Return the health worker with this code (case-insensitive), or None."""
        return self._workers.get((worker_id or "").strip().upper())

    def patients(self) -> Tuple[Patient, ...]:
        """All patients, in the order they were registered."""
        return tuple(self._patients.values())

    def workers(self) -> Tuple[HealthWorker, ...]:
        """All health workers, in the order they were registered."""
        return tuple(self._workers.values())

    def __len__(self) -> int:
        return len(self._patients)

    def __contains__(self, record_id: object) -> bool:
        return isinstance(record_id, str) and (
            record_id.upper() in self._patients or record_id.upper() in self._workers
        )

    def __iter__(self) -> Iterator[Patient]:
        """Looping over the registry loops over its patients."""
        return iter(self._patients.values())

    def all_visits(self) -> Tuple[Tuple[Patient, Visit], ...]:
        """Every visit in the registry, paired with its patient."""
        return tuple((p, v) for p in self._patients.values() for v in p.visits)

    # ---- displaying records ----------------------------------------------- #
    def display_patients(self, include_visits: bool = True) -> str:
        """All patients as readable text."""
        if not self._patients:
            return "No patients registered yet."
        separator = "\n\n" if include_visits else "\n"
        return separator.join(p.display_info(include_visits) for p in self._patients.values())

    def display_workers(self) -> str:
        """All health workers as readable text."""
        if not self._workers:
            return "No health workers registered yet."
        return "\n".join(w.display_info() for w in self._workers.values())

    # ---- analysis --------------------------------------------------------- #
    def diagnosis_summary(self) -> Tuple[CountRow, ...]:
        """Number of visits for each diagnosis, most common first."""
        counts: Dict[str, int] = {}
        for _, visit in self.all_visits():
            counts[visit.diagnosis] = counts.get(visit.diagnosis, 0) + 1
        return tuple(sorted(counts.items(), key=lambda row: (-row[1], row[0])))

    def district_diagnosis_counts(self) -> Tuple[Tuple[str, str, int], ...]:
        """Visits counted by (district, diagnosis), sorted alphabetically."""
        counts: Dict[Tuple[str, str], int] = {}
        for patient, visit in self.all_visits():
            key = (patient.district, visit.diagnosis)
            counts[key] = counts.get(key, 0) + 1
        return tuple((d, dx, n) for (d, dx), n in sorted(counts.items()))

    def follow_up_list(self) -> Tuple[FollowUpRow, ...]:
        """Patients whose latest visit or history means they need follow-up."""
        return tuple(
            (patient, reasons)
            for patient in self._patients.values()
            if (reasons := patient.needs_follow_up())
        )

    def patients_with(self, diagnosis: str) -> Tuple[Patient, ...]:
        """All patients who have ever had the given diagnosis."""
        if match_option(diagnosis, DIAGNOSES) is None:
            raise ValueError(f"Unknown diagnosis '{diagnosis}'.")
        return tuple(p for p in self._patients.values() if p.has_condition(diagnosis))

    @staticmethod
    def format_counts(rows: Tuple[CountRow, ...], label: str = "Diagnosis") -> str:
        """Turn (label, count) rows into an aligned text table."""
        if not rows:
            return "No visits recorded yet."
        total = sum(count for _, count in rows)
        header = f"{label:<24}{'Visits':>8}{'Share':>9}"
        body = tuple(
            f"{name:<24}{count:>8}{count / total:>9.0%}" for name, count in rows
        )
        footer = f"{'Total':<24}{total:>8}"
        divider = "-" * len(header)
        return "\n".join((header, divider) + body + (divider, footer))

    # ---- anonymised statistics export (DPG: extracting data safely) ------- #
    def export_statistics(self, path: Union[str, Path]) -> Tuple[int, int]:
        """Write visit counts by district and diagnosis to a CSV file.

        No patient codes, ages, sexes or dates are exported. Counts below
        MIN_CELL_COUNT are written as "<5" (small-number suppression), a
        standard public-health method for preventing re-identification.

        Returns (rows written, rows suppressed).
        """
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        rows_written = suppressed = 0
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(PatientRegistry.EXPORT_COLUMNS)
            for district, diagnosis, count in self.district_diagnosis_counts():
                if count < PatientRegistry.MIN_CELL_COUNT:
                    writer.writerow((district, diagnosis, f"<{PatientRegistry.MIN_CELL_COUNT}"))
                    suppressed += 1
                else:
                    writer.writerow((district, diagnosis, count))
                rows_written += 1
        return rows_written, suppressed

    # ---- alternative constructor ------------------------------------------ #
    @classmethod
    def with_sample_data(cls) -> "PatientRegistry":
        """Create a registry pre-filled with invented demonstration data.

        Every record is fictional and represents no real person.
        """
        registry = cls()
        workers = tuple(
            registry.add_worker(HealthWorker(role, district))
            for role, district in (
                ("Nurse", "Bo"),
                ("Doctor", "Kenema"),
                ("Community Health Officer", "Port Loko"),
            )
        )
        patient_data: Tuple[Tuple[int, str, str], ...] = (
            (34, "F", "Bo"), (6, "M", "Bo"), (58, "M", "Bo"), (25, "F", "Bo"),
            (2, "F", "Bo"), (41, "M", "Kenema"), (67, "F", "Kenema"),
            (19, "F", "Port Loko"), (45, "M", "Port Loko"), (12, "M", "Bo"),
        )
        patients = tuple(registry.add_patient(Patient.from_tuple(d)) for d in patient_data)

        # (patient, worker, date, visit type, diagnosis, temp, weight, sys, dia)
        visits = (
            (0, 0, "2026-03-02", "Outpatient", "Malaria", 38.9, 62, 118, 76),
            (0, 0, "2026-03-16", "Follow-up", "Routine check", 36.8, 62, 116, 75),
            (1, 0, "2026-04-10", "Outpatient", "Malaria", 39.2, 21, None, None),
            (2, 0, "2026-01-20", "Outpatient", "Hypertension", 36.9, 81, 158, 96),
            (2, 0, "2026-04-22", "Follow-up", "Hypertension", 36.7, 80, 146, 92),
            (3, 0, "2026-05-05", "Antenatal", "Routine check", 36.6, 64, 112, 70),
            (3, 0, "2026-06-18", "Outpatient", "Malaria", 38.4, 65, 110, 72),
            (4, 0, "2026-02-14", "Immunisation", "Routine check", 36.9, 11.5, None, None),
            (4, 0, "2026-07-01", "Emergency", "Malaria", 39.6, 11.8, None, None),
            (9, 0, "2026-08-11", "Outpatient", "Malaria", 38.6, 38, None, None),
            (5, 1, "2026-02-03", "Outpatient", "Typhoid", 38.7, 74, 128, 82),
            (5, 1, "2026-02-17", "Follow-up", "Typhoid", 37.0, 73, 124, 80),
            (6, 1, "2026-03-09", "Outpatient", "Diabetes", 36.8, 70, 134, 84),
            (6, 1, "2026-06-09", "Follow-up", "Diabetes", 36.7, 69, 132, 82),
            (7, 2, "2026-04-01", "Antenatal", "Routine check", 36.7, 58, 108, 68),
            (7, 2, "2026-05-28", "Outpatient", "Respiratory infection", 37.9, 59, 110, 70),
            (8, 2, "2026-07-15", "Outpatient", "Diarrhoeal disease", 37.4, 77, 122, 78),
            (8, 2, "2026-09-02", "Emergency", "Injury", 36.9, 77, 136, 86),
        )
        for p, w, when, kind, dx, temp, weight, sys_bp, dia_bp in visits:
            vitals = HealthWorker.build_vitals(temp, weight, sys_bp, dia_bp)
            workers[w].record_visit(patients[p], when, kind, dx, vitals)
        return registry


# --------------------------------------------------------------------------- #
# Simple functions to add and display records (Task 2)
# --------------------------------------------------------------------------- #
def add_record(registry: PatientRegistry, record: Union[Patient, HealthWorker]) -> str:
    """Add a Patient or HealthWorker to the registry's dictionary; return its ID."""
    if isinstance(record, Patient):
        return registry.add_patient(record).patient_id
    if isinstance(record, HealthWorker):
        return registry.add_worker(record).worker_id
    raise TypeError("Record must be a Patient or a HealthWorker.")


def display_records(registry: PatientRegistry) -> None:
    """Loop through the dictionaries and print every worker and patient."""
    print("=== Health Workers ===")
    print(registry.display_workers())
    print()
    print("=== Patients and Visit History ===")
    print(registry.display_patients())

