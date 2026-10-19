"""Unit tests for Patient, HealthWorker, Visit and VitalSigns.

Run all tests with:  python -m unittest discover -v
"""

import unittest
from datetime import date, timedelta

from prs.models import HealthWorker, Patient, Visit, VitalSigns


class ModelTestCase(unittest.TestCase):
    def setUp(self) -> None:
        Patient.reset_counter()
        HealthWorker.reset_counter()


class TestPatient(ModelTestCase):
    def test_creates_patient_with_generated_id(self) -> None:
        patient = Patient(34, "f", " bo ")
        self.assertEqual(patient.patient_id, "PAT-0001")
        self.assertEqual((patient.age, patient.sex, patient.district), (34, "Female", "Bo"))
        self.assertEqual(patient.visits, ())

    def test_ids_are_unique_and_sequential(self) -> None:
        ids = tuple(Patient(20, "M", "Bo").patient_id for _ in range(3))
        self.assertEqual(ids, ("PAT-0001", "PAT-0002", "PAT-0003"))

    def test_sex_shortcuts_and_full_words(self) -> None:
        for text, expected in (("F", "Female"), ("male", "Male"), ("p", "Prefer not to say"),
                               ("PREFER NOT TO SAY", "Prefer not to say")):
            with self.subTest(text=text):
                self.assertEqual(Patient(30, text, "Bo").sex, expected)

    def test_rejects_invalid_inputs(self) -> None:
        for args in ((-1, "F", "Bo"), (121, "F", "Bo"), ("3.5", "F", "Bo"), ("", "F", "Bo"),
                     (30, "X", "Bo"), (30, "F", "Lagos")):
            with self.subTest(args=args), self.assertRaises(ValueError):
                Patient(*args)

    def test_failed_creation_does_not_use_an_id(self) -> None:
        with self.assertRaises(ValueError):
            Patient(30, "F", "Nowhere")
        self.assertEqual(Patient(30, "F", "Bo").patient_id, "PAT-0001")

    def test_age_group_static_method(self) -> None:
        cases = ((0, "0-4"), (4, "0-4"), (5, "5-14"), (24, "15-24"), (44, "25-44"),
                 (64, "45-64"), (65, "65+"))
        for age, group in cases:
            with self.subTest(age=age):
                self.assertEqual(Patient.age_group(age), group)

    def test_from_tuple_class_method(self) -> None:
        patient = Patient.from_tuple((67, "F", "Kenema"))
        self.assertIsInstance(patient, Patient)
        self.assertEqual(patient.district, "Kenema")

    def test_update_record_is_all_or_nothing(self) -> None:
        patient = Patient(30, "F", "Bo")
        with self.assertRaises(ValueError):
            patient.update_record(age=31, district="Atlantis")
        self.assertEqual((patient.age, patient.district), (30, "Bo"))
        patient.update_record(age="31", district="kenema")
        self.assertEqual((patient.age, patient.district), (31, "Kenema"))

    def test_add_visit_rejects_non_visits(self) -> None:
        with self.assertRaises(TypeError):
            Patient(30, "F", "Bo").add_visit(("2026-01-01", "Outpatient"))  # type: ignore[arg-type]

    def test_display_info_without_visits(self) -> None:
        text = Patient(30, "F", "Bo").display_info()
        self.assertIn("PAT-0001", text)
        self.assertIn("No visits recorded yet", text)


class TestVitalSigns(ModelTestCase):
    def test_build_vitals_with_and_without_bp(self) -> None:
        self.assertEqual(HealthWorker.build_vitals("37.25", "60", "120", "80"),
                         VitalSigns(37.2, 60.0, 120, 80))
        self.assertEqual(HealthWorker.build_vitals(37, 11.5), VitalSigns(37.0, 11.5, None, None))

    def test_build_vitals_rejects_bad_values(self) -> None:
        bad = ((29, 60), (46, 60), ("hot", 60), (37, 0), (37, 301), (37, 60, 120, None),
               (37, 60, 80, 120), (37, 60, 120.5, 80), (37, 60, 300, 80))
        for args in bad:
            with self.subTest(args=args), self.assertRaises(ValueError):
                HealthWorker.build_vitals(*args)

    def test_fever_and_bp_categories(self) -> None:
        self.assertTrue(VitalSigns(38.0, 60).has_fever())
        self.assertFalse(VitalSigns(37.9, 60).has_fever())
        cases = (((None, None), "Not measured"), ((115, 75), "Normal"), ((125, 75), "Elevated"),
                 ((132, 78), "High (stage 1)"), ((118, 84), "High (stage 1)"),
                 ((145, 85), "High (stage 2)"), ((185, 100), "Hypertensive crisis"))
        for (sys_bp, dia_bp), expected in cases:
            with self.subTest(bp=(sys_bp, dia_bp)):
                self.assertEqual(VitalSigns(37, 60, sys_bp, dia_bp).bp_category(), expected)

    def test_parse_blood_pressure(self) -> None:
        self.assertEqual(HealthWorker.parse_blood_pressure(" 120 / 80 "), (120, 80))
        self.assertEqual(HealthWorker.parse_blood_pressure(""), (None, None))
        for text in ("120", "120/80/60", "abc/80", "80/120"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                HealthWorker.parse_blood_pressure(text)


class TestHealthWorkerAndVisits(ModelTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.nurse = HealthWorker("nurse", "Bo")
        self.patient = Patient(34, "F", "Bo")
        self.vitals = HealthWorker.build_vitals(37, 60, 118, 76)

    def test_creates_worker(self) -> None:
        self.assertEqual((self.nurse.worker_id, self.nurse.role), ("HW-0001", "Nurse"))
        with self.assertRaises(ValueError):
            HealthWorker("Pilot", "Bo")
        with self.assertRaises(ValueError):
            HealthWorker("Doctor", "Accra")

    def test_record_visit_links_worker_and_patient(self) -> None:
        visit = self.nurse.record_visit(self.patient, "2026-03-02", "outpatient", "malaria", self.vitals)
        self.assertIsInstance(visit, Visit)
        self.assertIsInstance(visit, tuple)
        self.assertEqual(visit.visit_date, date(2026, 3, 2))
        self.assertEqual((visit.visit_type, visit.diagnosis, visit.worker_id),
                         ("Outpatient", "Malaria", "HW-0001"))
        self.assertEqual(self.patient.visits, (visit,))
        self.assertEqual(self.nurse.visits_recorded, 1)

    def test_visits_are_kept_in_date_order(self) -> None:
        for when in ("2026-05-01", "2026-01-01", "2026-03-01"):
            self.nurse.record_visit(self.patient, when, "Outpatient", "Malaria", self.vitals)
        dates = tuple(v.visit_date.isoformat() for v in self.patient.visits)
        self.assertEqual(dates, ("2026-01-01", "2026-03-01", "2026-05-01"))
        self.assertEqual(self.patient.latest_visit().visit_date, date(2026, 5, 1))  # type: ignore[union-attr]

    def test_record_visit_rejects_bad_data(self) -> None:
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        bad = ((tomorrow, "Outpatient", "Malaria"), ("1999-12-31", "Outpatient", "Malaria"),
               ("02/03/2026", "Outpatient", "Malaria"), ("2026-03-02", "Surgery", "Malaria"),
               ("2026-03-02", "Outpatient", "Flu"))
        for when, kind, dx in bad:
            with self.subTest(case=(when, kind, dx)), self.assertRaises(ValueError):
                self.nurse.record_visit(self.patient, when, kind, dx, self.vitals)
        with self.assertRaises(TypeError):
            self.nurse.record_visit("PAT-0001", "2026-03-02", "Outpatient", "Malaria", self.vitals)  # type: ignore[arg-type]
        self.assertEqual(self.patient.visit_count(), 0)
        self.assertEqual(self.nurse.visits_recorded, 0)

    def test_antenatal_visit_not_allowed_for_male_patient(self) -> None:
        male = Patient(30, "M", "Bo")
        with self.assertRaises(ValueError):
            self.nurse.record_visit(male, "2026-03-02", "Antenatal", "Routine check", self.vitals)

    def test_visits_are_immutable(self) -> None:
        visit = self.nurse.record_visit(self.patient, "2026-03-02", "Outpatient", "Malaria", self.vitals)
        with self.assertRaises(AttributeError):
            visit.diagnosis = "Typhoid"  # type: ignore[misc]

    def test_needs_follow_up(self) -> None:
        self.assertEqual(self.patient.needs_follow_up(), ())
        feverish = HealthWorker.build_vitals(39.0, 60, 150, 95)
        self.nurse.record_visit(self.patient, "2026-03-02", "Outpatient", "Hypertension", feverish)
        reasons = self.patient.needs_follow_up()
        self.assertEqual(len(reasons), 3)
        self.assertIn("fever (39.0 C)", reasons)
        self.assertIn("chronic condition: Hypertension", reasons)
        self.assertTrue(self.patient.has_condition("hypertension"))
        self.assertFalse(self.patient.has_condition("Malaria"))

    def test_display_info(self) -> None:
        self.nurse.record_visit(self.patient, "2026-03-02", "Outpatient", "Malaria",
                                HealthWorker.build_vitals(38.5, 60))
        text = self.patient.display_info()
        self.assertIn("2026-03-02", text)
        self.assertIn("FEVER", text)
        self.assertIn("BP not measured", text)
        self.assertIn("Visits recorded: 1", self.nurse.display_info())


if __name__ == "__main__":
    unittest.main()
