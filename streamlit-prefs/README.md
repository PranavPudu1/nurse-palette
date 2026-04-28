# Nurse Preferences — Quick Start

A short web app where a nurse answers a few questions about their ideal schedule. Below are step-by-step instructions to run it on a Mac. **Total time: ~5 minutes the first time, ~10 seconds every time after.**

---

## First-time setup (only do this once)

### 1. Open Terminal

Press `Cmd + Space`, type **Terminal**, press Enter. A black/white window opens.

### 2. Check if Python is installed

Copy and paste this line, then press Enter:

```bash
python3 --version
```

- If you see something like `Python 3.11.4`, you're good — skip to step 4.
- If you see `command not found`, do step 3.

### 3. Install Python (only if step 2 said "command not found")

In the same Terminal window, paste this and press Enter:

```bash
xcode-select --install
```

A pop-up will ask you to install developer tools. Click **Install** and wait a few minutes. When it finishes, run `python3 --version` again to confirm.

### 4. Install the app's dependencies

Paste this and press Enter:

```bash
cd ~/Desktop/nurse-palette/streamlit-prefs && pip3 install -r requirements.txt
```

You'll see a lot of text scroll by — that's normal. It takes 1–2 minutes. When you see your prompt return (a line ending in `$` or `%`), you're done.

---

## Running the app (every time)

### Open Terminal and paste:

```bash
cd ~/Desktop/nurse-palette/streamlit-prefs && streamlit run app.py
```

After a few seconds, your web browser will open automatically to the app at `http://localhost:8501`.

If the browser doesn't open on its own, click the link that Terminal shows.

### To stop the app

Go back to the Terminal window and press `Ctrl + C` (the **Control** key, not Command).

---

## Switching languages

In the top-right of the page there's a dropdown. Pick **English** or **한국어**. The whole app translates instantly.

## Saving answers

Each tab has a **Download** button at the bottom that saves a `.json` file with the responses. The file goes to your **Downloads** folder by default.

---

## Tabs at a glance

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
| `command not found: streamlit` | Run step 4 again |
| `Address already in use` | The app is already running in another Terminal — close that one or visit `http://localhost:8501` |
| The browser shows a blank page | Wait 5 seconds and refresh |
| Anything else | Close the Terminal window, open a new one, and start from "Running the app" |
