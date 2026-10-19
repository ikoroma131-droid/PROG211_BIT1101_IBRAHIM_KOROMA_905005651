# Contributing to PRS

Thank you for helping to improve the Patient Record System.

1. Fork the repository and create a branch for your change.
2. Keep the privacy rules: **never add fields that identify a patient**
   (names, phone numbers, ID numbers, addresses, exact birth dates or
   free-text notes), and keep small-number suppression in every export.
3. Follow PEP 8, add type hints and a docstring to every new class and method.
4. Add or update tests in `tests/` and make sure they all pass:
   `python -m unittest discover -v`
5. Open a pull request that explains what you changed and why.

Ideas that would help most: encrypted storage with user log-in, translations
(Krio, Mende, Temne) and child-specific vital-sign ranges.
