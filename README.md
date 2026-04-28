# Nurse Preferences — Quick Start

A short web app where a nurse answers a few questions about their ideal schedule. **Total time: ~5 minutes the first time, ~10 seconds every time after.**

Pick your computer below and follow only that section.

- [Mac instructions](#mac)
- [Windows instructions](#windows)

---

## Mac

### First-time setup (only do this once)

#### 1. Open Terminal
Press `Cmd + Space`, type **Terminal**, press Enter.

#### 2. Check if Python is installed
Paste and press Enter:
```bash
python3 --version
```
- If you see something like `Python 3.11.4`, skip to step 4.
- If you see `command not found`, do step 3.

#### 3. Install Python (only if step 2 said "command not found")
```bash
xcode-select --install
```
A pop-up will ask you to install developer tools. Click **Install**. When it finishes, run `python3 --version` again to confirm.

#### 4. Install the app's dependencies
```bash
cd ~/Desktop/nurse-palette/streamlit-prefs && pip3 install -r requirements.txt
```
Takes 1–2 minutes. Done when your prompt returns (a line ending in `$` or `%`).

### Running the app (every time)

```bash
cd ~/Desktop/nurse-palette/streamlit-prefs && streamlit run app.py
```
The browser opens automatically to `http://localhost:8501`.

**To stop:** go back to Terminal and press `Ctrl + C` (the **Control** key, not Command).

---

## Windows

### First-time setup (only do this once)

#### 1. Open Command Prompt
Press the `Windows` key, type **cmd**, press Enter. A black window opens.

#### 2. Check if Python is installed
Paste and press Enter:
```cmd
python --version
```
- If you see something like `Python 3.11.4`, skip to step 4.
- If you see `'python' is not recognized…` or it opens the Microsoft Store, do step 3.

#### 3. Install Python (only if step 2 didn't work)
1. Open https://www.python.org/downloads/ in your browser.
2. Click the big yellow **Download Python** button and run the installer.
3. **IMPORTANT:** on the first installer screen, check the box that says **"Add python.exe to PATH"** at the bottom.
4. Click **Install Now** and wait.
5. **Close Command Prompt and reopen it** (very important — it needs to pick up the new install).
6. Run `python --version` again to confirm.

#### 4. Install the app's dependencies
```cmd
cd %USERPROFILE%\Desktop\nurse-palette\streamlit-prefs
pip install -r requirements.txt
```
Takes 1–2 minutes. Done when your prompt returns (a line ending in `>`).

### Running the app (every time)

```cmd
cd %USERPROFILE%\Desktop\nurse-palette\streamlit-prefs
streamlit run app.py
```
The browser opens automatically to `http://localhost:8501`.

**To stop:** go back to Command Prompt and press `Ctrl + C`.

---

## Using the app (both Mac and Windows)

### Switching languages
Top-right of the page is a dropdown. Pick **English** or **한국어** — the whole app translates instantly.

### Saving answers
Each tab has a **Download** button at the bottom that saves a `.json` file with the responses to your **Downloads** folder.

### Tabs at a glance
1. **Background** — open questions in three formats. Pick the one that's easiest.
2. **Compare** — pick the better of two example months.
3. **Rank** — order scheduling rules by what matters most.
4. **Ideal** — draw your perfect month on a calendar.
5. **Trade-offs** — sliders for the harder questions.
6. **Day prefs** — rate each shift / weekday combination.

---

## Troubleshooting

| If you see… | Try this |
|---|---|
| `command not found: streamlit` (Mac) or `'streamlit' is not recognized` (Windows) | Run "Install the app's dependencies" again |
| `Address already in use` / `Port 8501 is already in use` | The app is already running in another window — close that one, or just visit `http://localhost:8501` |
| The browser shows a blank page | Wait 5 seconds and refresh |
| Windows: `'python' is not recognized` after installing Python | Close Command Prompt, reopen it. If still failing, the "Add python.exe to PATH" checkbox was missed — reinstall Python from python.org and make sure that box is checked |
| Mac: pip3 says "permission denied" | Try `pip3 install --user -r requirements.txt` instead |
| Anything else | Close the Terminal/Command Prompt window, open a new one, and start from "Running the app" |

---

## Project links

**Lovable project:** https://lovable.dev/projects/REPLACE_WITH_PROJECT_ID
