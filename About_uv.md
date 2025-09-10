## ⚡ About `uv`

We are using [`uv`](https://github.com/astral-sh/uv) as our package and environment manager instead of the old combo (`pip` + `venv` + `requirements.txt`).  
Think of `uv` as a **super-fast, all-in-one tool** for Python projects.

### 🔑 What `uv` Does for Us
1. **Virtual Environments (venv)**
   - Creates a local `.venv` folder inside the repo.
   - Keeps all dependencies isolated from the system Python (no version conflicts).

2. **Dependency Management**
   - We define dependencies in `pyproject.toml` (instead of `requirements.txt`).
   - When we run `uv sync`, `uv` installs everything and locks exact versions in `uv.lock`.
   - Teammates will always have the **same package versions** → no "works on my machine" issues.

3. **Speed**
   - `uv` is written in Rust → it’s way faster than pip/conda.
   - Installs are cached and reused across projects.

4. **Reproducibility**
   - `uv.lock` ensures every teammate and deployment server gets identical libraries.
   - No more surprises when running code in different environments.

5. **Ease of Use**
   - One tool for everything (env + install + lock).
   - Example workflow:
     ```bash
     uv venv        # Create virtual environment
     uv sync        # Install deps from pyproject.toml
     uv add numpy   # Add new dependency
     uv run main.py # Run code inside the venv
     ```

---

### 🚀 Why This Helps Us in the Hackathon
- **Fast setup**: new teammate just clones repo → `uv venv` → `uv sync` → ready to code.
- **Consistency**: everyone runs the same Python version + same package versions.
- **Scalability**: if we later add tools (Black, Ruff, Mypy, pytest), `uv` manages them easily.
- **Future-proof**: Google Cloud or any server we deploy to can replicate our setup instantly using `uv.lock`.

In short:  
👉 `uv` saves time, avoids dependency hell, and keeps our team’s environment perfectly in sync.
