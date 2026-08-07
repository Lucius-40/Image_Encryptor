# Fourier-Domain Image Encryptor

Double Random Phase Encoding (DRPE) based image encryption using 2D DFT/IDFT.

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/<your-username>/fourier-image-encryptor.git
cd fourier-image-encryptor
```

**2. Create a virtual environment**

```powershell
# Windows
py -m venv venv
```

```bash
# macOS/Linux
python3 -m venv venv
```

**3. Activate the virtual environment**

```powershell
# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

> If you get an execution-policy error on Windows, run this once:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

```bash
# macOS/Linux
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt once it's active.

**4. Install dependencies**

```bash
pip install -r requirements.txt
```

**5. Run the app**

```bash
streamlit run app.py
```

This opens the app automatically in your browser (usually at `http://localhost:8501`).

**6. Deactivate when done**

```bash
deactivate
```

**If you add a new package**, install it, then update the manifest and commit it:

```bash
pip install <package-name>
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Add <package-name> dependency"
```

---

## Branching and Merging PRs into `main`

We don't commit directly to `main`. Each feature or fix gets its own branch and a Pull Request (PR).

**1. Make sure your local `main` is up to date**

```bash
git checkout main
git pull origin main
```

**2. Create a new branch for your work**

```bash
git checkout -b feature/short-description
```

Examples: `feature/drpe-core`, `feature/streamlit-gui`, `fix/key-generation-bug`

**3. Make your changes, then stage and commit**

```bash
git add .
git commit -m "Describe what you changed"
```

**4. Push the branch to GitHub**

```bash
git push -u origin feature/short-description
```

(After the first push, you can just use `git push` for that branch.)

**5. Open a Pull Request**

- Go to the repo on GitHub — it usually shows a banner prompting "Compare & pull request" for your just-pushed branch. Click it.
- Set the base branch to `main` and the compare branch to yours.
- Add a short description of what the branch does.
- Click **Create pull request**.

**6. Review**

- Ask your partner to review the PR (or review theirs).
- Leave comments if changes are needed; push additional commits to the same branch — they'll automatically appear in the open PR.

**7. Merge**

- Once approved and any conflicts are resolved, click **Merge pull request** on GitHub, then **Confirm merge**.
- Delete the branch on GitHub (there's a button right after merging) to keep things tidy.

**8. Sync your local `main` after merging**

```bash
git checkout main
git pull origin main
```

