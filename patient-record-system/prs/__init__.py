"""Patient Record System (PRS).

An open-source, privacy-respecting tool that helps clinics and community
health workers in Sierra Leone keep simple patient visit records, built with
Object-Oriented Programming in Python.
"""

from prs.models import (
    DIAGNOSES,
    DISTRICTS,
    VISIT_TYPES,
    HealthWorker,
    Patient,
    Visit,
    VitalSigns,
)
from prs.registry import PatientRegistry, add_record, display_records

__all__ = (
    "DIAGNOSES",
    "DISTRICTS",
    "VISIT_TYPES",
    "HealthWorker",
    "Patient",
    "PatientRegistry",
    "Visit",
    "VitalSigns",
    "add_record",
    "display_records",
)

__version__ = "1.0.0"
