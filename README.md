# State Dataset Linkage Tool

Streamlit mock-data app for linking state datasets across public and restricted paths.

The app demonstrates:

- public statistical linkage with shared keys
- private/public linkage with pseudonymized private references
- restricted private/private linkage using Python PPRL methods
- dropdown selection for left and right datasets
- CSV upload for custom left and right datasets
- dropdown selection for the PPRL technique, with Bloom filter / hash embeddings as the default
- metadata-only dataset previews so source records are not displayed by default
- linked cross-reference records in results
- PPRL-style privacy controls and privacy-safe output release
- optional AI metadata plan using `st.secrets`
- optional AI-assisted geo/info linkage plan using metadata only

Mock testing datasets include person, geography, education, employment, wage, observed transition, public program statistics, and public O*NET-style skill scores.

The mock CSV files are stored parallel to `streamlit_app.py` in the app folder:

- `person.csv`
- `education.csv`
- `employment.csv`
- `wage.csv`
- `observed_transition.csv`
- `geography.csv`
- `program_stats.csv`
- `onet_skills.csv`

## Client Instructions

1. Choose **Mock datasets** or **Upload CSVs** in the sidebar.
2. Select the left and right datasets.
3. For uploaded files, classify each dataset as `public` or `restricted`.
4. Choose the PPRL technique. The default is **Bloom filter / hash embeddings**.
5. Use **Mock Data** to review metadata only: row counts, fields, data types, and identifier flags.
6. Use **Geo / Info Mapping** to review suggested geography fields, informational fields, and linkage keys.
7. Use **Linkage Package** to save the selected approach and privacy controls.
8. Use **Results** to create linked cross-reference records and aggregate summaries.

## Optional AI Setup

The app can generate an AI-assisted metadata plan, but only from schemas and classifications. Do not send raw restricted rows or direct identifiers.

When AI is enabled, the model recommends geography/info linkage keys from metadata only. Python then performs the local linkage on the selected datasets.

Create `.streamlit/secrets.toml` locally:

```toml
OPENAI_API_KEY = "your-new-key"
OPENAI_MODEL = "gpt-4.1-mini"
```

You can copy `.streamlit/secrets.toml.example` as a starting point. Never commit a real API key.

Then turn on **Use AI from st.secrets** in the sidebar.

## Run

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```
