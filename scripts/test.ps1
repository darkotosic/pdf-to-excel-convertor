$ErrorActionPreference = "Stop"
python -m pytest --cov=pdf_to_excel --cov-report=term-missing
