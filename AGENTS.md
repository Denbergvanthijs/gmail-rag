# In general

- Use the `gmail-rag` Miniconda environment for all development and checks (`conda activate gmail-rag`)
- Before completing a code task, always run all of the following commands:

  ```bash
  python -m ruff check . --fix
  python -m ruff format .
  python -m ty check
  python -m pytest --cov --cov-report=term-missing
  ```

- Use **Graphify** to understand code relationships and **Ponytail** to identify and remove unnecessary complexity.
- Follow existing project conventions. Prefer simple solutions over unnecessary abstractions and dependencies.
- See `./github/copilot-instructions.md` and `README.md` for further instructions and guidance.

## Code formatting

- Use blank lines to separate logically distinct blocks of code.
- Add a blank line after completed control-flow blocks (`if/else`,
  `for`, `while`, `try/except`) when subsequent statements represent
  a new logical step.
- Separate variable initialization, conditional logic, processing,
  and return statements with blank lines where appropriate.
- Avoid unnecessary blank lines within closely related statements.
- Follow PEP 8 and Ruff formatting conventions.
