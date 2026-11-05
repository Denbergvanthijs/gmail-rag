# gmail-rag

## Installatie op Windows

Open de projectmap in VS Code en voer in de PowerShell-terminal uit:

```powershell
conda create --name gmail-rag python=3.14
conda activate gmail-rag
python -m pip install --upgrade pip cython wheel
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Selecteer daarna in VS Code de interpreter van de `gmail-rag` Conda-omgeving.

## Tests en kwaliteitschecks

```powershell
python -m pytest
python -m pytest --cov --cov-report=term-missing
python -m ruff check . --fix
python -m ruff format .
python -m ty check
```
