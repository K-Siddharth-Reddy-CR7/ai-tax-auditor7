# Investigation scripts

Read-only scripts used to verify every quantitative statement in `../repository_investigation.md`. They import `backend/server.py` directly and never modify repository files.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install flask flask-cors pandas numpy nbformat
export PYTHONDONTWRITEBYTECODE=1   # avoid writing __pycache__ into backend/
python 01_dataset_profile.py              # dataset shapes, nulls, CSV/JSON parity, distributions
python 02_pipeline_behaviour.py           # agentic vs. baseline on 400 transactions + edge cases
python 03_retrieval_and_latency.py        # retrieval behaviour, preliminary timing
python 04_catalog_and_tariff_checks.py    # catalogue self-match, EU duty consistency
python 05_dump_notebook.py "../../Majorpro (1).ipynb" > nb_dump.txt
```

Scripts use absolute paths to `/home/user/ai-tax-auditor7/`; edit the `R`/path constants if your checkout is elsewhere. The timing in script 03 is a preliminary sanity check, not a reportable experiment.
