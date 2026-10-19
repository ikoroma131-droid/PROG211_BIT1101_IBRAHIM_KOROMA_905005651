"""Unit tests for the PatientRegistry, the add/display functions and the CLI."""

import csv
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import main
from prs import HealthWorker, Patient, PatientRegistry, add_record, display_records


def reset_ids() -> None:
    Patient.reset_counter()
    HealthWorker.reset_counter()


class TestAddAndLookUp(unittest.TestCase):
    def setUp(self) -> None:
        reset_ids()
        self.registry = PatientRegistry()
        self.worker = HealthWorker("Doctor", "Kenema")
        self.patient = Patient(41, "M", "Kenema")

    def test_add_record_stores_objects_by_id(self) -> None:
        self.assertEqual(add_record(self.registry, self.worker), "HW-0001")
        self.assertEqual(add_record(self.registry, self.patient), "PAT-0001")
        self.assertIs(self.registry.get_patient(" pat-0001 "), self.patient)
        self.assertIs(self.registry.get_worker("hw-0001"), self.worker)
        self.assertIsNone(self.registry.get_patient("PAT-9999"))
        self.assertEqual(len(self.registry), 1)
        self.assertIn("PAT-0001", self.registry)
        self.assertIn("HW-0001", self.registry)
        self.assertEqual(tuple(self.registry), (self.patient,))

    def test_rejects_duplicates_and_wrong_types(self) -> None:
        add_record(self.registry, self.patient)
        with self.assertRaises(ValueError):
            add_record(self.registry, self.patient)
        with self.assertRaises(TypeError):
            add_record(self.registry, "PAT-0001")  # type: ignore[arg-type]

    def test_display_functions(self) -> None:
        self.assertEqual(self.registry.display_patients(), "No patients registered yet.")
        self.assertEqual(self.registry.display_workers(), "No health workers registered yet.")
        add_record(self.registry, self.worker)
        add_record(self.registry, self.patient)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            display_records(self.registry)
        self.assertIn("HW-0001", buffer.getvalue())
        self.assertIn("PAT-0001", buffer.getvalue())


class TestReports(unittest.TestCase):
    def setUp(self) -> None:
        reset_ids()
        self.registry = PatientRegistry.with_sample_data()

    def test_sample_data_loaded(self) -> None:
        self.assertEqual(len(self.registry.workers()), 3)
        self.assertEqual(len(self.registry), 10)
        self.assertEqual(len(self.registry.all_visits()), 18)
        self.assertEqual(sum(w.visits_recorded for w in self.registry.workers()), 18)

    def test_diagnosis_summary(self) -> None:
        rows = self.registry.diagnosis_summary()
        self.assertEqual(rows[0], ("Malaria", 5))
        self.assertEqual(sum(count for _, count in rows), 18)
        table = PatientRegistry.format_counts(rows)
        self.assertIn("Total", table)
        self.assertEqual(PatientRegistry.format_counts(()), "No visits recorded yet.")

    def test_follow_up_and_condition_search(self) -> None:
        ids = tuple(p.patient_id for p, _ in self.registry.follow_up_list())
        self.assertEqual(ids, ("PAT-0002", "PAT-0003", "PAT-0004", "PAT-0005", "PAT-0007", "PAT-0010"))
        diabetic = self.registry.patients_with("diabetes")
        self.assertEqual(tuple(p.patient_id for p in diabetic), ("PAT-0007",))
        with self.assertRaises(ValueError):
            self.registry.patients_with("Flu")

    def test_export_is_aggregated_and_suppresses_small_counts(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "stats.csv"
            rows, suppressed = self.registry.export_statistics(path)
            content = path.read_text(encoding="utf-8")
            with path.open(encoding="utf-8", newline="") as handle:
                table = tuple(csv.reader(handle))
        self.assertEqual((rows, suppressed), (9, 8))
        self.assertEqual(tuple(table[0]), PatientRegistry.EXPORT_COLUMNS)
        self.assertIn(("Bo", "Malaria", "5"), tuple(tuple(r) for r in table))
        self.assertNotIn("PAT-", content)
        self.assertNotIn("HW-", content)
        self.assertNotIn("2026", content)


class TestCommandLine(unittest.TestCase):
    """Drive the interactive program with scripted keyboard input."""

    def run_cli(self, *answers: str) -> str:
        reset_ids()
        buffer = io.StringIO()
        with patch("builtins.input", side_effect=answers), redirect_stdout(buffer):
            self.assertEqual(main.run(), 0)
        return buffer.getvalue()

    def test_full_workflow(self) -> None:
        output = self.run_cli(
            "2", "2", "Bo",                                   # nurse in Bo
            "1", "34", "F", "1",                              # patient, district 1 = Bo
            "3", "HW-0001", "PAT-0001", "2026-03-02", "1", "malaria", "38.9", "62", "118/76",
            "5", "pat-0001",
            "4",
            "0",
        )
        self.assertIn("staff code HW-0001", output)
        self.assertIn("patient registered with code PAT-0001", output)
        self.assertIn("Outpatient visit on 2026-03-02 saved", output)
        self.assertIn("Follow-up recommended: fever (38.9 C)", output)
        self.assertIn("118/76 mmHg - Normal", output)
        self.assertIn("Goodbye", output)

    def test_blank_date_means_today_and_bp_optional(self) -> None:
        output = self.run_cli(
            "2", "Midwife", "Kono", "1", "2", "f", "kono",
            "3", "HW-0001", "PAT-0001", "", "Immunisation", "Routine check", "36.9", "11.5", "",
            "0",
        )
        self.assertIn("BP not measured", output)
        self.assertIn("saved for PAT-0001", output)

    def test_invalid_input_is_explained_not_crashed(self) -> None:
        output = self.run_cli("x", "3", "1", "old", "200", "30", "Z", "F", "Mars", "Bo", "0")
        self.assertIn("please type a number from 0 to 9", output)
        self.assertIn("Please register at least one health worker", output)
        self.assertIn("Age must be a whole number", output)
        self.assertIn("Age must be between 0 and 120", output)
        self.assertIn("Type F (Female)", output)
        self.assertIn("District not recognised", output)
        self.assertIn("PAT-0001", output)

    def test_too_many_wrong_answers_returns_to_menu(self) -> None:
        output = self.run_cli("1", "a", "b", "c", "0")
        self.assertIn("Too many invalid attempts", output)
        self.assertIn("Goodbye", output)

    def test_end_of_input_exits_cleanly(self) -> None:
        buffer = io.StringIO()
        with patch("builtins.input", side_effect=EOFError), redirect_stdout(buffer):
            self.assertEqual(main.run(), 0)
        self.assertIn("Goodbye", buffer.getvalue())

    def test_sample_data_and_reports(self) -> None:
        output = self.run_cli("9", "6", "7", "0")
        self.assertIn("Loaded 3 health workers, 10 patients and 18 visits", output)
        self.assertIn("PAT-0003 (Bo): blood pressure high (stage 2)", output)
        self.assertIn("Malaria", output)


if __name__ == "__main__":
    unittest.main()
