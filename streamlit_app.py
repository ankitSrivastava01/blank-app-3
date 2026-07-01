from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


ACCENT = "#00334d"
APP_DIR = Path(__file__).resolve().parent
MOCK_DATA_FILES = {
    "person": "person.csv",
    "education": "education.csv",
    "wage": "wage.csv",
    "employment": "employment.csv",
    "observed_transition": "observed_transition.csv",
    "geography": "geography.csv",
    "public_person_geo": "public_person_geo.csv",
    "onet_skills": "onet_skills.csv",
    "lehd_public": "lehd_public.csv",
    "cps_public": "cps_public.csv",
    "program_stats": "program_stats.csv",
}
DIRECT_IDENTIFIERS = {"first_name", "last_name", "dob", "phone", "email", "address", "mailing_address", "zip", "student_id", "ssn_last4"}
GEO_FIELDS = {"state", "county", "zip", "zip_prefix", "mail_zip_prefix", "state_fips", "county_fips", "region", "geography_type"}
INFO_FIELDS = {
    "soc_code",
    "cip_code",
    "naics_code",
    "program",
    "industry",
    "sector",
    "quarter",
    "year",
    "cohort_year",
    "graduation_year",
    "education_level",
    "labor_force_status",
    "email_domain",
    "completion_status",
    "transition_type",
    "transition_status",
    "employment_status",
}


@dataclass(frozen=True)
class LinkageSettings:
    data_source: str
    left_dataset: str
    right_dataset: str
    left_classification: str
    right_classification: str
    pprl_technique: str
    salt: str
    auto_threshold: float
    review_threshold: float
    use_ai: bool
    ai_model: str


def init_state() -> None:
    defaults = {
        "submitted_package": {},
        "ai_suggestion": "",
        "uploaded_left_df": pd.DataFrame(),
        "uploaded_right_df": pd.DataFrame(),
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_demo() -> None:
    for key in ["submitted_package", "ai_suggestion", "uploaded_left_df", "uploaded_right_df"]:
        st.session_state.pop(key, None)
    init_state()


def style_page() -> None:
    st.markdown(
        f"""
        <style>
        html, body, [class*="st-"], .stMarkdown, .stText, p, span, label, div {{
            color: #4b5563;
        }}
        h1, h2, h3, .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            color: #4b5563;
        }}
        div.stButton > button[kind="primary"] {{
            background-color: {ACCENT};
            border-color: {ACCENT};
            color: #f8fafc;
        }}
        .callout {{
            background: #f3f8fb;
            border-left: 4px solid {ACCENT};
            padding: 0.85rem 1rem;
            margin: 0.5rem 0 1rem;
        }}
        .pill {{
            display: inline-block;
            color: #4b5563;
            border: 1px solid {ACCENT};
            border-radius: 999px;
            padding: 0.22rem 0.68rem;
            font-weight: 700;
            margin: 0.25rem 0 0.8rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def load_mock_csv(dataset_key: str) -> pd.DataFrame:
    csv_path = APP_DIR / MOCK_DATA_FILES[dataset_key]
    if not csv_path.exists():
        st.error(f"Missing mock CSV: `{csv_path.name}`. Keep the CSV files in the same folder as `streamlit_app.py`.")
        return pd.DataFrame()
    return pd.read_csv(csv_path, dtype=str)


@st.cache_data
def private_person() -> pd.DataFrame:
    return load_mock_csv("person")


@st.cache_data
def private_education() -> pd.DataFrame:
    return load_mock_csv("education")


@st.cache_data
def private_wage() -> pd.DataFrame:
    return load_mock_csv("wage")


@st.cache_data
def private_employment() -> pd.DataFrame:
    return load_mock_csv("employment")


@st.cache_data
def private_transition() -> pd.DataFrame:
    return load_mock_csv("observed_transition")


@st.cache_data
def public_geography() -> pd.DataFrame:
    return load_mock_csv("geography")


@st.cache_data
def public_person_geo() -> pd.DataFrame:
    return load_mock_csv("public_person_geo")


@st.cache_data
def public_onet() -> pd.DataFrame:
    return load_mock_csv("onet_skills")


@st.cache_data
def public_lehd() -> pd.DataFrame:
    return load_mock_csv("lehd_public")


@st.cache_data
def public_cps() -> pd.DataFrame:
    return load_mock_csv("cps_public")


@st.cache_data
def public_program_stats() -> pd.DataFrame:
    return load_mock_csv("program_stats")


def normalize(value: object) -> str:
    text = "" if pd.isna(value) else str(value).lower().strip()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def zip_prefix(value: object) -> str:
    return re.sub(r"\D", "", str(value))[:3]


def birth_year(value: object) -> str:
    text = str(value)
    return text[:4] if len(text) >= 4 else ""


def email_domain(value: object) -> str:
    text = "" if pd.isna(value) else str(value).lower().strip()
    return text.split("@", 1)[1] if "@" in text else ""


def qgrams(value: object, n: int = 2) -> set[str]:
    text = normalize(value).replace(" ", "")
    if not text:
        return set()
    if len(text) <= n:
        return {text}
    return {text[index : index + n] for index in range(len(text) - n + 1)}


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 0.0
    return len(left & right) / len(left | right)


def salted_hash(value: object, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{normalize(value)}".encode("utf-8")).hexdigest()


def mask_identifiers(df: pd.DataFrame) -> pd.DataFrame:
    masked = df.copy()
    for column in masked.columns:
        if column in DIRECT_IDENTIFIERS:
            if column == "email":
                masked[column] = "masked@example.org"
            elif column == "phone":
                masked[column] = "555-XXX-XXXX"
            elif column == "dob":
                masked[column] = "YYYY-MM-DD"
            elif column == "zip":
                masked[column] = masked[column].astype(str).str[:2] + "***"
            else:
                masked[column] = "[masked]"
    return masked


def dataset_catalog() -> dict[str, dict[str, Any]]:
    return {
        "Private person records": {"df": private_person(), "classification": "restricted"},
        "Private education records": {"df": private_education(), "classification": "restricted"},
        "Private employment records": {"df": private_employment(), "classification": "restricted"},
        "Private wage records": {"df": private_wage(), "classification": "restricted"},
        "Private observed transition records": {"df": private_transition(), "classification": "restricted"},
        "Public person geography sample": {"df": public_person_geo(), "classification": "public"},
        "Public geography reference": {"df": public_geography(), "classification": "public"},
        "Public O*NET skill scores": {"df": public_onet(), "classification": "public"},
        "Public LEHD workforce statistics": {"df": public_lehd(), "classification": "public"},
        "Public CPS labor force sample": {"df": public_cps(), "classification": "public"},
        "Public program statistics": {"df": public_program_stats(), "classification": "public"},
    }


def demo_scenarios() -> dict[str, dict[str, str]]:
    return {
        "Public 1 - Public person geography + geography": {
            "left": "Public person geography sample",
            "right": "Public geography reference",
            "route": "public / no encryption",
        },
        "Public 2 - LEHD + CPS": {
            "left": "Public LEHD workforce statistics",
            "right": "Public CPS labor force sample",
            "route": "public / no encryption",
        },
        "Public 3 - Program statistics + O*NET": {
            "left": "Public program statistics",
            "right": "Public O*NET skill scores",
            "route": "public / no encryption",
        },
        "Public 4 - LEHD + geography": {
            "left": "Public LEHD workforce statistics",
            "right": "Public geography reference",
            "route": "public / no encryption",
        },
        "Private encrypted 1 - Education + wage": {
            "left": "Private education records",
            "right": "Private wage records",
            "route": "private / encrypted PPRL",
        },
        "Private encrypted 2 - Person + wage": {
            "left": "Private person records",
            "right": "Private wage records",
            "route": "private / encrypted PPRL",
        },
        "Private encrypted 3 - Education + employment": {
            "left": "Private education records",
            "right": "Private employment records",
            "route": "private / encrypted PPRL",
        },
        "Private encrypted 4 - Person + education": {
            "left": "Private person records",
            "right": "Private education records",
            "route": "private / encrypted PPRL",
        },
        "Mixed 1 - Education + O*NET": {
            "left": "Private education records",
            "right": "Public O*NET skill scores",
            "route": "mixed private/public",
        },
        "Mixed 2 - Wage + LEHD": {
            "left": "Private wage records",
            "right": "Public LEHD workforce statistics",
            "route": "mixed private/public",
        },
        "Mixed 3 - Employment + geography": {
            "left": "Private employment records",
            "right": "Public geography reference",
            "route": "mixed private/public",
        },
        "Mixed 4 - Education + program statistics": {
            "left": "Private education records",
            "right": "Public program statistics",
            "route": "mixed private/public",
        },
    }


def infer_classification(df: pd.DataFrame) -> str:
    if df.empty:
        return "public"
    if any(column in DIRECT_IDENTIFIERS for column in df.columns):
        return "restricted"
    if any(column in df.columns for column in ["person_id", "student_id", "ssn_last4", "education_record_id", "workforce_record_id"]):
        return "restricted"
    return "public"


def selected_datasets(settings: LinkageSettings) -> tuple[str, pd.DataFrame, str, pd.DataFrame]:
    catalog = dataset_catalog()
    if settings.data_source == "Upload CSVs":
        return settings.left_dataset, st.session_state.uploaded_left_df, settings.right_dataset, st.session_state.uploaded_right_df
    return settings.left_dataset, catalog[settings.left_dataset]["df"], settings.right_dataset, catalog[settings.right_dataset]["df"]


def classify_pair(left_name: str, right_name: str, left_classification: str | None = None, right_classification: str | None = None) -> str:
    catalog = dataset_catalog()
    left = left_classification or catalog.get(left_name, {}).get("classification", "public")
    right = right_classification or catalog.get(right_name, {}).get("classification", "public")
    if left == "public" and right == "public":
        return "non-restricted / public statistical"
    if left == "restricted" and right == "restricted":
        return "restricted / private"
    return "mixed private/public"


def heuristic_schema_mapping(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for left_col in left.columns:
        best_col = None
        best_score = 0.0
        for right_col in right.columns:
            score = SequenceMatcher(None, left_col, right_col).ratio()
            if left_col == right_col:
                score = 1.0
            if score > best_score:
                best_score = score
                best_col = right_col
        rows.append(
            {
                "left_field": left_col,
                "suggested_right_field": best_col,
                "confidence": round(best_score, 2),
                "suggested_use": "join key" if left_col == best_col and left_col in {"soc_code", "cip_code", "state", "county", "year"} else "review",
            }
        )
    return pd.DataFrame(rows)


def field_role(column: str) -> str:
    if column in DIRECT_IDENTIFIERS:
        return "direct_identifier"
    if column in GEO_FIELDS:
        return "geographic_key"
    if column in INFO_FIELDS:
        return "informational_linkage_key"
    if column.endswith("_id") or column in {"person_id", "education_record_id", "employment_record_id", "workforce_record_id", "transition_id"}:
        return "record_key"
    return "analysis_field"


def linkage_feature_summary(df: pd.DataFrame) -> dict[str, list[str]]:
    return {
        "geographic_fields": [column for column in df.columns if field_role(column) == "geographic_key"],
        "informational_fields": [column for column in df.columns if field_role(column) == "informational_linkage_key"],
        "record_key_fields": [column for column in df.columns if field_role(column) == "record_key"],
        "direct_identifier_fields": [column for column in df.columns if field_role(column) == "direct_identifier"],
    }


def safe_schema_payload(left_name: str, left: pd.DataFrame, right_name: str, right: pd.DataFrame) -> dict[str, Any]:
    def describe(df: pd.DataFrame) -> list[dict[str, str]]:
        rows = []
        for col in df.columns:
            rows.append(
                {
                    "field": col,
                    "dtype": str(df[col].dtype),
                    "privacy": "direct_identifier" if col in DIRECT_IDENTIFIERS else "analysis_or_key_field",
                    "field_role": field_role(col),
                }
            )
        return rows

    return {
        "left_dataset": left_name,
        "right_dataset": right_name,
        "left_schema": describe(left),
        "right_schema": describe(right),
        "left_linkage_features": linkage_feature_summary(left),
        "right_linkage_features": linkage_feature_summary(right),
        "instruction": (
            "Suggest linkage using geographic and informational fields first, such as county, state, zip_prefix, "
            "SOC, CIP, program, industry, quarter, transition, and status fields. For restricted data, recommend "
            "PPRL tokenization for direct identifiers. Do not request raw private values."
        ),
    }


def streamlit_secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def ai_linkage_plan(payload: dict[str, Any], settings: LinkageSettings) -> str:
    api_key = streamlit_secret("OPENAI_API_KEY")
    if not api_key:
        return "AI is enabled, but `OPENAI_API_KEY` is not configured in Streamlit secrets."

    try:
        from openai import OpenAI
    except ImportError:
        return "AI is enabled, but the `openai` package is not installed. Install requirements and restart the app."

    safe_payload = {
        **payload,
        "left_classification": settings.left_classification,
        "right_classification": settings.right_classification,
        "selected_linkage_method": settings.pprl_technique,
        "privacy_rule": "Use metadata only. Do not request or infer raw PII values. Recommend privacy-safe linkage steps and outputs.",
    }
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=settings.ai_model,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a privacy-preserving record linkage advisor. "
                    "Return concise JSON with keys: linkage_type, recommended_keys, blocking_fields, "
                    "geo_linkage_plan, info_linkage_plan, pprl_encoding, linkage_token_plan, risks, "
                    "release_outputs, client_next_steps. Prefer geographic and informational fields before "
                    "identifier-based PPRL. Never ask for raw PII or source rows."
                ),
            },
            {"role": "user", "content": json.dumps(safe_payload)},
        ],
    )
    return response.output_text


def parse_ai_plan(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return {}
    return {}


def metadata_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in df.columns:
        rows.append(
            {
                "field": column,
                "dtype": str(df[column].dtype),
                "privacy_class": "direct_identifier" if column in DIRECT_IDENTIFIERS else "analysis_or_linkage_field",
                "non_null_count": int(df[column].notna().sum()),
                "unique_count": int(df[column].nunique(dropna=True)),
            }
        )
    return pd.DataFrame(rows)


def dataset_summary(name: str, df: pd.DataFrame, classification: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["Dataset", name],
            ["Classification", classification],
            ["Rows", len(df)],
            ["Columns", len(df.columns)],
            ["Direct identifier fields", ", ".join([column for column in df.columns if column in DIRECT_IDENTIFIERS]) or "None"],
        ],
        columns=["Metadata", "Value"],
    )


def direct_public_link(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
    keys = [
        key
        for key in [
            "public_person_id",
            "person_group_id",
            "zip_prefix",
            "county",
            "state",
            "state_fips",
            "county_fips",
            "soc_code",
            "cip_code",
            "naics_code",
            "industry",
            "year",
            "quarter",
            "cohort_year",
            "graduation_year",
        ]
        if key in left.columns and key in right.columns
    ]
    if not keys:
        keys = [key for key in left.columns if key in right.columns and key not in DIRECT_IDENTIFIERS]
    if not keys:
        return pd.DataFrame()
    return left.merge(right, on=keys[:1], how="left", suffixes=("_left", "_right"))


def private_public_link(private_df: pd.DataFrame, public_df: pd.DataFrame) -> pd.DataFrame:
    working_private = private_df.copy()
    working_public = public_df.copy()
    if "zip" in working_private.columns:
        working_private["zip_prefix"] = working_private["zip"].astype(str).str[:3]

    shared_keys = [key for key in ["soc_code", "cip_code", "zip_prefix", "county", "state"] if key in working_private.columns and key in working_public.columns]
    if not shared_keys:
        return pd.DataFrame()

    linked = working_private.merge(working_public, on=shared_keys[:1], how="left", suffixes=("_private", "_public"))
    safe_cols = [
        "person_id",
        "education_record_id",
        "employment_record_id",
        "program",
        "cip_code",
        "soc_code",
        "graduation_year",
        "county",
        "state",
        "region",
        "public_population",
        "geography_type",
        "onet_title",
        "sector",
        "technical_skill_score",
        "digital_skill_score",
        "social_skill_score",
    ]
    result = linked[[col for col in safe_cols if col in linked.columns]].copy()
    for col in ["person_id", "education_record_id", "employment_record_id"]:
        if col in result.columns:
            result[col] = result[col].apply(lambda value: salted_hash(value, "release")[:12])
            result = result.rename(columns={col: f"pseudonymous_{col}"})
    return result


def safe_linked_output(linked: pd.DataFrame) -> pd.DataFrame:
    safe = linked[[column for column in linked.columns if column not in DIRECT_IDENTIFIERS]].copy()
    for column in ["person_id", "education_record_id", "employment_record_id", "workforce_record_id", "transition_id"]:
        for actual_column in [column, f"{column}_left", f"{column}_right"]:
            if actual_column in safe.columns:
                safe[actual_column] = safe[actual_column].apply(lambda value: salted_hash(value, "release")[:12])
                safe = safe.rename(columns={actual_column: f"pseudonymous_{actual_column}"})
    return safe


def candidate_geo_info_keys(left: pd.DataFrame, right: pd.DataFrame) -> list[str]:
    priority = ["zip_prefix", "county", "state", "soc_code", "cip_code", "program", "industry", "sector", "quarter", "transition_type", "employment_status"]
    return [key for key in priority if key in left.columns and key in right.columns and key not in DIRECT_IDENTIFIERS]


def ai_recommended_keys(plan: dict[str, Any], left: pd.DataFrame, right: pd.DataFrame) -> list[str]:
    keys: list[str] = []
    for field in ["recommended_keys", "blocking_fields"]:
        value = plan.get(field, [])
        if isinstance(value, str):
            value = [value]
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    keys.append(item)
                elif isinstance(item, dict):
                    keys.extend([str(v) for v in item.values() if isinstance(v, str)])
    valid = []
    for key in keys:
        normalized = key.strip()
        if normalized in left.columns and normalized in right.columns and normalized not in DIRECT_IDENTIFIERS and normalized not in valid:
            valid.append(normalized)
    return valid


def ai_assisted_local_link(left: pd.DataFrame, right: pd.DataFrame, plan: dict[str, Any]) -> tuple[pd.DataFrame, list[str]]:
    working_left = left.copy()
    working_right = right.copy()
    if "zip" in working_left.columns and "zip_prefix" not in working_left.columns:
        working_left["zip_prefix"] = working_left["zip"].astype(str).str[:3]
    if "zip" in working_right.columns and "zip_prefix" not in working_right.columns:
        working_right["zip_prefix"] = working_right["zip"].astype(str).str[:3]

    keys = ai_recommended_keys(plan, working_left, working_right)
    if not keys:
        keys = candidate_geo_info_keys(working_left, working_right)
    if not keys:
        return pd.DataFrame(), []

    linked = working_left.merge(working_right, on=keys[:1], how="left", suffixes=("_left", "_right"))
    output = safe_linked_output(linked)
    output["ai_link_key"] = keys[0]
    output["ai_linkage_basis"] = "metadata_recommended_geo_info_key"
    return output, keys


def pprl_score(left_row: pd.Series, right_row: pd.Series, settings: LinkageSettings) -> dict[str, Any]:
    left_name = f"{left_row.get('first_name', '')} {left_row.get('last_name', '')}"
    right_name = f"{right_row.get('first_name', '')} {right_row.get('last_name', '')}"
    name_score = jaccard(qgrams(left_name), qgrams(right_name)) if left_name.strip() and right_name.strip() else 0.0
    address_score = jaccard(qgrams(left_row.get("address", "")), qgrams(right_row.get("address", "")))
    dob_match = salted_hash(left_row.get("dob", ""), settings.salt) == salted_hash(right_row.get("dob", ""), settings.salt) and bool(left_row.get("dob", ""))
    zip_match = salted_hash(zip_prefix(left_row.get("zip", "")), settings.salt) == salted_hash(zip_prefix(right_row.get("zip", "")), settings.salt) and bool(left_row.get("zip", ""))
    soc_match = left_row.get("soc_code") == right_row.get("soc_code")
    person_match = left_row.get("person_id") == right_row.get("person_id") and bool(left_row.get("person_id", ""))
    student_match = left_row.get("student_id") == right_row.get("student_id") and bool(left_row.get("student_id", ""))
    score = round((0.28 * name_score) + (0.2 * float(dob_match)) + (0.12 * float(zip_match)) + (0.1 * address_score) + (0.14 * float(soc_match)) + (0.1 * float(person_match)) + (0.06 * float(student_match)), 3)
    if score >= settings.auto_threshold:
        status = "auto_match"
    elif score >= settings.review_threshold:
        status = "owner_review"
    else:
        status = "non_match"
    left_ref = left_row.get("education_record_id") or left_row.get("person_id") or left_row.get("employment_record_id") or left_row.get("transition_id") or "left"
    right_ref = right_row.get("workforce_record_id") or right_row.get("education_record_id") or right_row.get("employment_record_id") or right_row.get("person_id") or "right"
    seed = f"{left_ref}:{right_ref}"
    return {
        "project_person_id": salted_hash(seed, "project")[:14],
        "left_record_ref": salted_hash(left_ref, "release")[:12],
        "right_record_ref": salted_hash(right_ref, "release")[:12],
        "program": left_row.get("program", right_row.get("program", "")),
        "industry": right_row.get("industry", left_row.get("industry", "")),
        "soc_code": left_row.get("soc_code", right_row.get("soc_code", "")),
        "match_score": score,
        "match_status": status,
        "annual_wage": right_row.get("annual_wage", left_row.get("annual_wage", 0)),
    }


def pprl_private_link(left: pd.DataFrame, right: pd.DataFrame, settings: LinkageSettings) -> tuple[pd.DataFrame, pd.DataFrame]:
    candidates = []
    for _, left_row in left.iterrows():
        for _, right_row in right.iterrows():
            same_birth_year = "dob" in left.columns and "dob" in right.columns and birth_year(left_row["dob"]) == birth_year(right_row["dob"])
            same_zip_prefix = "zip" in left.columns and "zip" in right.columns and zip_prefix(left_row["zip"]) == zip_prefix(right_row["zip"])
            same_soc = "soc_code" in left.columns and "soc_code" in right.columns and left_row["soc_code"] == right_row["soc_code"]
            same_person = "person_id" in left.columns and "person_id" in right.columns and left_row["person_id"] == right_row["person_id"]
            same_student = "student_id" in left.columns and "student_id" in right.columns and left_row["student_id"] == right_row["student_id"]
            same_record = any(key in left.columns and key in right.columns and left_row[key] == right_row[key] for key in ["education_record_id", "employment_record_id", "workforce_record_id"])
            if same_birth_year or same_zip_prefix or same_soc or same_person or same_student or same_record:
                candidates.append(pprl_score(left_row, right_row, settings))

    if not candidates:
        columns = ["project_person_id", "left_record_ref", "right_record_ref", "program", "industry", "soc_code", "match_score", "match_status"]
        summary_columns = ["program", "industry", "match_status", "linked_records", "average_match_score", "median_wage"]
        return pd.DataFrame(columns=columns), pd.DataFrame(columns=summary_columns)

    scored = pd.DataFrame(candidates).sort_values("match_score", ascending=False)
    best = scored.drop_duplicates("left_record_ref", keep="first").reset_index(drop=True)
    released = best[best["match_status"].isin(["auto_match", "owner_review"])].copy()
    released["annual_wage"] = pd.to_numeric(released["annual_wage"], errors="coerce")
    summary = (
        released.groupby(["program", "industry", "match_status"], dropna=False)
        .agg(linked_records=("project_person_id", "count"), average_match_score=("match_score", "mean"), median_wage=("annual_wage", "median"))
        .reset_index()
    )
    if not summary.empty:
        summary["average_match_score"] = summary["average_match_score"].round(3)
        summary["median_wage"] = summary["median_wage"].round(0).astype(int)
    return released.drop(columns=["annual_wage"]), summary


def run_linkage(settings: LinkageSettings) -> tuple[pd.DataFrame, pd.DataFrame | None, str]:
    left_name, left, right_name, right = selected_datasets(settings)
    classification = classify_pair(left_name, right_name, settings.left_classification, settings.right_classification)
    if left.empty or right.empty:
        return pd.DataFrame(), None, "Upload or select two datasets before running linkage."
    if settings.use_ai:
        payload = safe_schema_payload(left_name, left, right_name, right)
        ai_text = ai_linkage_plan(payload, settings)
        st.session_state.ai_suggestion = ai_text
        plan = parse_ai_plan(ai_text)
        linked, keys = ai_assisted_local_link(left, right, plan)
        if keys:
            return linked, None, f"AI-assisted local linkage using metadata-selected key `{keys[0]}`. Raw rows were not sent to AI."
    if classification == "non-restricted / public statistical":
        return direct_public_link(left, right), None, "Direct public key linkage using shared public fields."
    if classification == "mixed private/public":
        return private_public_link(left, right), None, "Private-to-public linkage by SOC/CIP keys with private IDs pseudonymized."
    return (*pprl_private_link(left, right, settings), f"{settings.pprl_technique} with privacy-safe release fields.")


def linked_record_view(linked: pd.DataFrame) -> pd.DataFrame:
    preferred = [
        "project_person_id",
        "pseudonymous_person_id",
        "pseudonymous_education_record_id",
        "pseudonymous_employment_record_id",
        "pseudonymous_record_ref",
        "left_record_ref",
        "right_record_ref",
        "match_score",
        "match_status",
        "public_person_id",
        "person_group_id",
        "state",
        "county",
        "zip_prefix",
        "soc_code",
        "cip_code",
        "naics_code",
        "year",
        "quarter",
        "program",
        "industry",
        "education_level",
        "labor_force_status",
        "public_person_count",
        "public_jobs",
        "public_hires",
        "average_monthly_earnings",
        "employment_rate",
        "median_weekly_earnings",
        "public_completers",
        "public_employment_rate",
        "onet_title",
        "technical_skill_score",
        "digital_skill_score",
        "region",
        "public_population",
    ]
    cols = [col for col in preferred if col in linked.columns]
    if cols:
        return linked[cols].copy()
    safe_keys = [col for col in linked.columns if col not in DIRECT_IDENTIFIERS]
    return linked[safe_keys[:10]].copy()


def sidebar() -> LinkageSettings:
    with st.sidebar:
        st.header("Linkage Controls")
        if st.button("Clear all / reset demo", width="stretch"):
            reset_demo()
            st.rerun()

        data_source = st.selectbox("Dataset source", ["Mock datasets", "Upload CSVs"])
        catalog = dataset_catalog()
        dataset_names = list(catalog.keys())

        if data_source == "Mock datasets":
            scenarios = demo_scenarios()
            scenario_name = st.selectbox("Demo linkage scenario", ["Custom pair", *scenarios.keys()])
            left_default = "Private education records"
            right_default = "Public O*NET skill scores"
            if scenario_name != "Custom pair":
                scenario = scenarios[scenario_name]
                left_default = scenario["left"]
                right_default = scenario["right"]
                st.caption(f"{scenario['route']}: `{left_default}` + `{right_default}`")
            left_dataset = st.selectbox("Dataset 1", dataset_names, index=dataset_names.index(left_default))
            right_dataset = st.selectbox("Dataset 2", dataset_names, index=dataset_names.index(right_default))
            left_classification = catalog[left_dataset]["classification"]
            right_classification = catalog[right_dataset]["classification"]
        else:
            left_upload = st.file_uploader("Upload left CSV", type=["csv"], key="left_csv_upload")
            right_upload = st.file_uploader("Upload right CSV", type=["csv"], key="right_csv_upload")

            if left_upload is not None:
                st.session_state.uploaded_left_df = pd.read_csv(left_upload)
                left_dataset = left_upload.name
            else:
                left_dataset = "Uploaded left CSV"
                st.session_state.uploaded_left_df = pd.DataFrame()

            if right_upload is not None:
                st.session_state.uploaded_right_df = pd.read_csv(right_upload)
                right_dataset = right_upload.name
            else:
                right_dataset = "Uploaded right CSV"
                st.session_state.uploaded_right_df = pd.DataFrame()

            left_classification = st.selectbox(
                "Left data classification",
                ["restricted", "public"],
                index=0 if infer_classification(st.session_state.uploaded_left_df) == "restricted" else 1,
            )
            right_classification = st.selectbox(
                "Right data classification",
                ["restricted", "public"],
                index=0 if infer_classification(st.session_state.uploaded_right_df) == "restricted" else 1,
            )

        pprl_technique = st.selectbox(
            "Linkage method",
            [
                "Direct public key linkage",
                "LLM-assisted linkage",
                "PPRL Bloom filter / hash embeddings",
                "PPRL salted hash + q-grams",
                "Secure Multi-Party Computation (SMC)",
                "Linkage Honest Broker (LHB)",
                "Asymmetric key cryptography",
                "PPRL secure enclave / eyes-off execution",
            ],
        )
        auto_threshold = st.slider("PPRL auto-match threshold", 0.70, 0.98, 0.86, 0.01)
        review_threshold = st.slider("PPRL review threshold", 0.50, 0.90, 0.72, 0.01)
        llm_method_selected = pprl_technique == "LLM-assisted linkage"
        use_ai_toggle = st.toggle("Use AI to enhance linkage", value=llm_method_selected)
        use_ai = llm_method_selected or use_ai_toggle
        ai_model = streamlit_secret("OPENAI_MODEL", "gpt-4.1-mini")
        if use_ai:
            if streamlit_secret("OPENAI_API_KEY"):
                st.caption(f"AI enhancement enabled with `{ai_model}` from Streamlit secrets. Only metadata is sent.")
            else:
                st.caption("AI enhancement is on, but `OPENAI_API_KEY` is missing from Streamlit secrets.")

    return LinkageSettings(
        data_source=data_source,
        left_dataset=left_dataset,
        right_dataset=right_dataset,
        left_classification=left_classification,
        right_classification=right_classification,
        pprl_technique=pprl_technique,
        salt="demo-controlled-salt",
        auto_threshold=auto_threshold,
        review_threshold=review_threshold,
        use_ai=use_ai,
        ai_model=ai_model,
    )


def workflow_tab(settings: LinkageSettings) -> None:
    left_name, left, right_name, right = selected_datasets(settings)
    classification = classify_pair(left_name, right_name, settings.left_classification, settings.right_classification)

    st.header("Linkage Tool Flow")
    st.markdown(
        """
        <div class="callout">
        The tool links state datasets using the least-sensitive path available. Public statistical data uses direct keys.
        Restricted person-level data uses PPRL-style privacy controls and privacy-safe output release.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write(f"**Selected pair:** {left_name} + {right_name}")
    st.write(f"**Data classification:** {classification}")
    st.write(f"**Selected linkage method:** {settings.pprl_technique}")

    st.subheader("Client instructions")
    instructions = pd.DataFrame(
        [
            ["1", "Choose data source", "Use mock datasets or upload two CSV files from the sidebar."],
            ["2", "Select datasets", "Pick the left and right datasets to link."],
            ["3", "Classify data", "For uploads, mark each file as public or restricted."],
            ["4", "Choose linkage method", "Use direct linkage for public data, LLM-assisted planning for metadata review, or PPRL for restricted linkage."],
            ["5", "Review metadata", "Open Mock Data to inspect schemas, field types, identifier flags, and row counts."],
            ["6", "Review mapping", "Open Schema Mapping to see proposed join keys and fields needing review."],
            ["7", "Save package", "Open Linkage Package to record the selected technique, outputs, and privacy controls."],
            ["8", "Run linkage", "Open Results to generate linked cross-reference records and aggregate summaries."],
        ],
        columns=["Step", "Action", "Client note"],
    )
    st.dataframe(instructions, hide_index=True, width="stretch")

    flow = pd.DataFrame(
        [
            ["1", "Ingest datasets", "Capture schema, data dictionary, ERD, row grain, and privacy classification."],
            ["2", "Classify data", "Decide public direct linkage vs. restricted PPRL/PySyft route."],
            ["3A", "Public route", "Standardize fields and link with public keys such as SOC, CIP, year, county, or program."],
            ["3B", "Restricted route", "Create mock data, choose a restricted linkage method, and run privacy-preserving matching."],
            ["4", "Python assistance", "Use deterministic Python heuristics on metadata to suggest linkage keys and risks."],
            ["5", "PPRL method", "For restricted data, use salted hashes, q-grams, Bloom-filter-style encodings, or hash embeddings as approved."],
            ["6", "Output release", "Release public linked tables or privacy-safe restricted outputs only."],
        ],
        columns=["Step", "Stage", "Action"],
    )
    st.dataframe(flow, hide_index=True, width="stretch")

    decision = pd.DataFrame(
        [
            ["Public aggregate/statistical", "No", "No", "No", "No", "Direct key linkage"],
            ["Mixed private/public", "Maybe", "Maybe", "Maybe", "Maybe", "Public keys plus pseudonymized private refs"],
            ["Restricted person-level", "Yes", "Yes", "Yes", "Yes", "PPRL + PySyft-style secure execution"],
        ],
        columns=["Data type", "Person-level?", "Identifiers?", "PPRL needed?", "PySyft needed?", "Approach"],
    )
    st.subheader("Decision guide")
    st.dataframe(decision, hide_index=True, width="stretch")

    st.subheader("Method summary")
    st.write("Open **Instructions & Methods** for client instructions and detailed method explanations.")


def instructions_tab(settings: LinkageSettings) -> None:
    left_name, left, right_name, right = selected_datasets(settings)
    classification = classify_pair(left_name, right_name, settings.left_classification, settings.right_classification)

    st.header("Instructions & Methods")
    st.markdown(
        """
        <div class="callout">
        Use this tab as the client guide. Public data can be linked directly with shared keys. Restricted private
        data should use approved PPRL methods. AI is optional and only enhances metadata review and key selection.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Current selection")
    st.dataframe(
        pd.DataFrame(
            [
                ["Left dataset", left_name],
                ["Right dataset", right_name],
                ["Classification", classification],
                ["Linkage method", settings.pprl_technique],
                ["AI enhancement", "On - metadata only" if settings.use_ai else "Off"],
            ],
            columns=["Item", "Value"],
        ),
        hide_index=True,
        width="stretch",
    )

    st.subheader("Client instructions")
    st.dataframe(
        pd.DataFrame(
            [
                ["1", "Choose a scenario", "Use a 4/4/4 built-in scenario or select Custom pair."],
                ["2", "Upload client CSVs", "For client files, choose Upload CSVs and classify each file as public or restricted."],
                ["3", "Review metadata", "Check row counts, columns, direct identifier flags, geo fields, and info fields."],
                ["4", "Choose linkage method", "Use direct public keys for public data; use PPRL for restricted data."],
                ["5", "Optionally enable AI", "AI can suggest keys and risks from metadata only; it should not receive raw private rows or PII."],
                ["6", "Save package", "Record datasets, purpose, requested outputs, selected technique, and privacy controls."],
                ["7", "Run linkage", "Review linked cross-reference output and aggregate summaries."],
                ["8", "Release safely", "Public outputs may be exported directly; restricted outputs should stay pseudonymized/aggregate."],
            ],
            columns=["Step", "Instruction", "Client note"],
        ),
        hide_index=True,
        width="stretch",
    )

    st.subheader("Public methods - no encryption")
    st.dataframe(
        pd.DataFrame(
            [
                ["Direct geo linkage", "Joins public records on fields like state, county, ZIP prefix, region, or FIPS.", "Public geography, LEHD, CPS, program area comparisons."],
                ["Direct person/group linkage", "Joins on public or already-approved IDs such as public_person_id or person_group_id.", "Non-restricted public person/group summaries."],
                ["Direct occupation/program linkage", "Joins on SOC, CIP, NAICS, program, industry, year, or quarter.", "O*NET, LEHD, CPS, credential, and workforce summaries."],
                ["Uploaded public CSV linkage", "Client uploads any two public CSVs and marks both as public.", "The app chooses shared non-PII keys and creates linked output."],
            ],
            columns=["Method", "What it does", "Best fit"],
        ),
        hide_index=True,
        width="stretch",
    )

    st.subheader("Restricted PPRL methods")
    st.markdown(
        """
        <div class="callout">
        PPRL protects privacy by transforming identifiers before matching. Participating organizations encode
        fields such as names, dates of birth, and addresses into tokens or mathematical representations. A
        linkage agent or secure execution environment compares encoded values without seeing the raw PII.
        </div>
        """,
        unsafe_allow_html=True,
    )
    methods = pd.DataFrame(
            [
                ["LLM-assisted linkage", "Uses an LLM to review metadata and recommend keys, blocking fields, risks, and outputs.", "Useful for unfamiliar schemas; raw private rows and PII should not be sent."],
                ["Salted hashes", "Exact or near-exact encoded comparisons for stable identifiers.", "Useful for IDs, DOB, ZIP prefixes, and controlled blocking fields."],
            ["Q-gram similarity", "Fuzzy comparison over tokenized names and addresses.", "Useful for typos, spelling variants, and abbreviations."],
            ["Bloom filter encoding", "Converts sensitive attributes into cryptographic hashed bit-arrays.", "Default PPRL technique for similarity scoring without exposing original text."],
            ["Hash embeddings", "Embedding extension of Bloom-filter linkage that can learn associations from matched examples.", "Useful when training data and assurance are available."],
            ["Secure Multi-Party Computation", "Allows parties to jointly evaluate matching functions while keeping inputs private.", "Useful for high-assurance multi-party restricted linkage."],
            ["Linkage Honest Broker", "A neutral broker or blind enclave receives only encoded tokens and returns anonymized cross-reference IDs.", "Useful when a centralized trusted linkage agent is acceptable."],
            ["Asymmetric key cryptography", "Uses public/private key pairs to avoid a single shared network secret.", "Useful when sites need stronger local key control."],
            ["Secure enclave / eyes-off execution", "Run linkage where operators and researchers cannot inspect raw identifiers.", "Useful for multi-owner restricted linkage."],
        ],
        columns=["Method", "What it does", "Where it fits"],
    )
    st.dataframe(methods, hide_index=True, width="stretch")

    st.subheader("Mixed private/public methods")
    st.dataframe(
        pd.DataFrame(
            [
                ["Private-to-public key linkage", "Restricted rows are linked to public reference data using SOC, CIP, ZIP prefix, county, state, year, or quarter.", "Education + O*NET, wage + LEHD, employment + geography."],
                ["Pseudonymous private references", "Private record IDs are transformed before release while public fields remain readable.", "Mixed outputs where the researcher needs a cross-reference but not raw private IDs."],
                ["Aggregate release", "The output is summarized as counts, rates, scores, medians, or distributions.", "Dashboards, trend reporting, wage summaries, and public comparison outputs."],
                ["Owner review", "For sensitive mixed outputs, the data owner reviews linkage results before release.", "Any private/public result with re-identification or small-cell risk."],
            ],
            columns=["Method", "What it does", "Best fit"],
        ),
        hide_index=True,
        width="stretch",
    )

    st.subheader("AI enhancement option")
    st.dataframe(
        pd.DataFrame(
            [
                ["Purpose", "AI reviews metadata and suggests linkage keys, blocking fields, privacy risks, and release outputs."],
                ["Inputs", "Dataset names, classifications, column names, data types, and field roles only."],
                ["Not allowed", "Do not send raw restricted rows, names, DOB, phone, email, address, SSN, or student IDs to AI."],
                ["Execution", "Python performs linkage locally after AI suggests a metadata plan."],
                ["When useful", "Messy schemas, unfamiliar client CSVs, unclear geo/info keys, or mixed public/private linkage planning."],
            ],
            columns=["Area", "Guidance"],
        ),
        hide_index=True,
        width="stretch",
    )


def data_tab(settings: LinkageSettings) -> None:
    left_name, left, right_name, right = selected_datasets(settings)
    st.header("Data Preview")
    st.write("Use mock datasets or upload two CSV files. This view shows metadata only, not source records.")

    classification = classify_pair(left_name, right_name, settings.left_classification, settings.right_classification)
    if left.empty or right.empty:
        st.warning("Upload two CSV files or switch to mock datasets.")

    left_tab, right_tab, testing_tab, metadata_tab = st.tabs([left_name, right_name, "All mock metadata", "Metadata JSON"])
    with left_tab:
        st.dataframe(dataset_summary(left_name, left, settings.left_classification), hide_index=True, width="stretch")
        st.dataframe(metadata_table(left), hide_index=True, width="stretch")
    with right_tab:
        st.dataframe(dataset_summary(right_name, right, settings.right_classification), hide_index=True, width="stretch")
        st.dataframe(metadata_table(right), hide_index=True, width="stretch")
    with testing_tab:
        catalog = dataset_catalog()
        for dataset_name, spec in catalog.items():
            st.subheader(dataset_name)
            st.dataframe(dataset_summary(dataset_name, spec["df"], spec["classification"]), hide_index=True, width="stretch")
            st.dataframe(metadata_table(spec["df"]), hide_index=True, width="stretch")
            file_name = dataset_name.lower().replace(" ", "_").replace("*", "").replace("/", "_") + ".csv"
            st.download_button(
                f"Download {dataset_name} CSV",
                spec["df"].to_csv(index=False),
                file_name,
                "text/csv",
                key=f"download_{file_name}",
            )
    with metadata_tab:
        payload = safe_schema_payload(left_name, left, right_name, right)
        st.json(payload)


def schema_mapping_tab(settings: LinkageSettings) -> None:
    left_name, left, right_name, right = selected_datasets(settings)
    st.header("Geo / Info Schema Mapping")
    st.write("Python proposes field mappings using column names, geography keys, and informational linkage fields.")

    if left.empty or right.empty:
        st.warning("Upload two CSV files or switch to mock datasets before mapping.")
        return

    st.subheader("Python heuristic mapping")
    st.dataframe(heuristic_schema_mapping(left, right), hide_index=True, width="stretch")

    payload = safe_schema_payload(left_name, left, right_name, right)
    left_features = linkage_feature_summary(left)
    right_features = linkage_feature_summary(right)
    st.subheader("Geo and info fields")
    st.json(
        {
            "left_dataset": left_name,
            "left_geographic_fields": left_features["geographic_fields"],
            "left_informational_fields": left_features["informational_fields"],
            "right_dataset": right_name,
            "right_geographic_fields": right_features["geographic_fields"],
            "right_informational_fields": right_features["informational_fields"],
        }
    )
    st.subheader("Metadata-only schema payload")
    st.json(payload)

    st.subheader("AI geo/info linkage plan")
    if not settings.use_ai:
        st.info("Turn on `Use AI to enhance linkage` in the sidebar to generate a metadata-only AI linkage plan.")
    else:
        if st.button("Generate AI geo/info plan", type="primary"):
            st.session_state.ai_suggestion = ai_linkage_plan(payload, settings)
        if st.session_state.ai_suggestion:
            st.code(st.session_state.ai_suggestion, language="json")


def submit_tab(settings: LinkageSettings) -> None:
    left_name, left, right_name, right = selected_datasets(settings)
    classification = classify_pair(left_name, right_name, settings.left_classification, settings.right_classification)
    st.header("Linkage Package")

    if left.empty or right.empty:
        st.warning("Upload two CSV files or switch to mock datasets before building the linkage package.")
        return

    purpose = st.text_area(
        "Research purpose",
        value="Link state education, wage, and public O*NET-style data to produce privacy-safe analytical outputs for CTOT dashboards and reporting.",
        height=100,
    )
    package = {
        "dataset_source": settings.data_source,
        "dataset_pair": f"{left_name} + {right_name}",
        "classification": classification,
        "linkage_method": settings.pprl_technique,
        "geo_fields": {
            "left": linkage_feature_summary(left)["geographic_fields"],
            "right": linkage_feature_summary(right)["geographic_fields"],
        },
        "informational_fields": {
            "left": linkage_feature_summary(left)["informational_fields"],
            "right": linkage_feature_summary(right)["informational_fields"],
        },
        "left_dataset": left_name,
        "right_dataset": right_name,
        "requested_outputs": ["linked analytical output", "match quality metrics", "aggregate summaries"],
        "privacy_controls": ["mask direct identifiers", "use PPRL for restricted identifiers", "release privacy-safe outputs"],
    }
    st.json(package)

    if st.button("Save linkage package", type="primary"):
        st.session_state.submitted_package = {"purpose": purpose, **package}
        st.success("Linkage package saved for this demo.")


def results_tab(settings: LinkageSettings) -> None:
    st.header("Linked Output")
    left_name, left, right_name, right = selected_datasets(settings)
    classification = classify_pair(left_name, right_name, settings.left_classification, settings.right_classification)

    if left.empty or right.empty:
        st.warning("Upload two CSV files or switch to mock datasets before running linkage.")
        return

    linked, summary, note = run_linkage(settings)
    linked_view = linked_record_view(linked)
    st.success(note)
    if settings.use_ai and st.session_state.ai_suggestion:
        with st.expander("AI metadata linkage plan", expanded=False):
            st.code(st.session_state.ai_suggestion, language="json")
    st.subheader("Linked cross-reference records")
    st.dataframe(linked_view, hide_index=True, width="stretch")
    st.download_button("Download linked records", linked_view.to_csv(index=False), "linked_records.csv", "text/csv")

    if summary is not None:
        st.subheader("Released aggregate summary")
        st.dataframe(summary, hide_index=True, width="stretch")
        st.download_button("Download summary", summary.to_csv(index=False), "linked_summary.csv", "text/csv")


def main() -> None:
    st.set_page_config(page_title="State Dataset Linkage Tool", page_icon=":material/hub:", layout="wide")
    init_state()
    style_page()
    settings = sidebar()

    st.title("State Dataset Linkage Tool")
    st.caption("Mock-data app for public direct linkage, private/public linkage, and restricted PPRL-style matching.")

    workflow, instructions, data, mapping, submit, results = st.tabs(
        ["Flow", "Instructions & Methods", "Mock Data", "Geo / Info Mapping", "Linkage Package", "Results"]
    )
    with workflow:
        workflow_tab(settings)
    with instructions:
        instructions_tab(settings)
    with data:
        data_tab(settings)
    with mapping:
        schema_mapping_tab(settings)
    with submit:
        submit_tab(settings)
    with results:
        results_tab(settings)


if __name__ == "__main__":
    main()
