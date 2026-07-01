# State Dataset Linkage Tool

Streamlit mock-data app for linking state datasets across public and restricted paths.

The app demonstrates:

- public statistical linkage with shared keys
- private/public linkage with pseudonymized private references
- restricted private/private linkage using Python PPRL methods
- 12 built-in demo scenarios: 4 public, 4 private encrypted, and 4 mixed
- dropdown selection for left and right datasets
- CSV upload for any client-provided left and right datasets
- dropdown selection for the linkage method, including direct public linkage, LLM-assisted linkage, and PPRL methods
- metadata-only dataset previews so source records are not displayed by default
- linked cross-reference records in results
- PPRL-style privacy controls and privacy-safe output release
- optional AI metadata plan using `st.secrets`
- optional AI-assisted linkage enhancement using metadata only

Mock testing datasets include person, geography, education, employment, wage, observed transition, public person/geography records, public program statistics, public O*NET-style skill scores, public LEHD-style workforce statistics, and public CPS-style labor force statistics.

The mock CSV files are stored parallel to `streamlit_app.py` in the app folder:

- `person.csv`
- `education.csv`
- `employment.csv`
- `wage.csv`
- `observed_transition.csv`
- `geography.csv`
- `public_person_geo.csv`
- `program_stats.csv`
- `onet_skills.csv`
- `lehd_public.csv`
- `cps_public.csv`

## Client Instructions

1. Choose **Mock datasets** or **Upload CSVs** in the sidebar. Clients can upload any two CSV files they want to link.
2. For mock data, choose one of the 12 demo scenarios or choose **Custom pair**.
3. For uploaded files, classify each dataset as `public` or `restricted`.
4. Choose the linkage method. Options include **Direct public key linkage**, **LLM-assisted linkage**, and PPRL methods such as **Bloom filter / hash embeddings**.
5. Use **Mock Data** to review metadata only: row counts, fields, data types, and identifier flags.
6. Use **Geo / Info Mapping** to review suggested geography fields, informational fields, and linkage keys.
7. Use **Linkage Package** to save the selected approach and privacy controls.
8. Use **Results** to create linked cross-reference records and aggregate summaries.

For non-restricted public data such as public person/geography records, O*NET, LEHD-style, CPS-style, geography, or program statistics, the app uses direct shared-key linkage only. No encryption or PPRL is required for the public demo path.

## Built-In Demo Scenarios

Public / no encryption:

- Public person geography + geography
- LEHD + CPS
- Program statistics + O*NET
- LEHD + geography

Private encrypted / PPRL:

- Education + wage
- Person + wage
- Education + employment
- Person + education

Mixed private/public:

- Education + O*NET
- Wage + LEHD
- Employment + geography
- Education + program statistics

## Optional AI Setup

The app can generate an AI-assisted metadata plan, but only from schemas and classifications. Do not send raw restricted rows or direct identifiers.

When AI is enabled, the model recommends geography/info linkage keys from metadata only. Python then performs the local linkage on the selected datasets.

Create `.streamlit/secrets.toml` locally:

```toml
OPENAI_API_KEY = "your-new-key"
OPENAI_MODEL = "gpt-4.1-mini"
```

You can copy `.streamlit/secrets.toml.example` as a starting point. Never commit a real API key.

Then turn on **Use AI to enhance linkage** in the sidebar.

## Run

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```
