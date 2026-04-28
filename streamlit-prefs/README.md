# Nurse Preference Elicitation (Streamlit)

A standalone Streamlit app for collecting nurse scheduling preferences. Lives entirely in this folder — does not touch the React/TS app.

## Views
1. **Compare schedules** — pairwise A/B preference judgments over generated months.
2. **Rank features** — order rules (no consecutive nights, weekends off, etc.) by importance.
3. **Build your ideal month** — fill a calendar with your dream shifts.
4. **Trade-offs** — sliders + forced choices for the harder questions.
5. **Day-by-day preferences** — rate every shift × weekday combo on a heatmap.

Each view exports a downloadable JSON payload for downstream use.

## Run

```bash
cd streamlit-prefs
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501.

## Theming
Colors and the IBM Plex Sans font are mirrored from `src/index.css` so this app feels like a sibling of the main UI. See `theme.py` for the shared CSS / shift palette.
