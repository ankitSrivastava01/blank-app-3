# PPRL Implementation Plan for a Researcher

## Positioning

You are the researcher. That means you can design, prototype, and submit the privacy-preserving record linkage method, but you should not receive raw private state data unless the data owners explicitly approve that under their governance rules.

In a PySyft-style workflow:

- you develop PPRL code using mock or synthetic data
- you submit the code, purpose, and requested outputs
- state owners review the code and privacy risk
- approved code runs near each state's private data
- only approved linkage outputs are released

PySyft can manage the secure workflow, review, execution, and release process. The actual PPRL algorithm must be implemented by you, an approved template, or an approved matching tool.

PySyft does not generate mock data or synthetic data. You or your data engineering team create those assets using Python, pandas, Faker, NumPy, SDV, Gretel.ai, Mostly AI, Mockaroo, or custom CSV files.

## What You Should Implement

The PPRL implementation should avoid sharing direct identifiers such as:

- name
- date of birth
- Social Security number
- student ID
- phone
- email
- address
- zip code

Instead, it should transform identifiers into privacy-preserving comparison features.

PPRL usually follows a blind matching pattern:

- participating organizations transform PII into encoded tokens or arrays before linkage
- Bloom filters can encode identifiers into mathematical arrays for approximate matching
- a neutral linkage agent, secure enclave, or state-controlled execution environment compares encoded values
- the matching party should not see raw names, dates of birth, addresses, SSNs, emails, or phone numbers
- only approved linkage outputs are released

These encodings are not a free pass to share data broadly. Bloom filters, hashes, salts, and tokens still require governance, parameter review, key management, and re-identification risk assessment.

Common approaches include:

- exact matching on salted hashes for stable fields
- phonetic encodings for names
- tokenization of names and addresses
- Bloom filter encodings
- hash embeddings
- n-gram similarity over encoded tokens
- probabilistic matching scores
- threshold-based match decisions

## Recommended Researcher Workflow

### 1. Define the Linkage Goal

Write a clear linkage purpose:

- Which datasets need to be linked?
- What population is in scope?
- What fields are needed for matching?
- What output do you need: linked IDs, match scores, aggregates, or summary quality metrics?
- Do you need person-level linked IDs, or only aggregate outcomes?

Example:

> Link state education records to workforce wage records to estimate aggregate employment and wage outcomes by credential program. The researcher requests only match group IDs, confidence scores, and aggregate outcome summaries.

### 2. Request State Data Access and Development Materials

Before implementing the PPRL code, request the materials needed to build realistic mock data:

- data dictionary
- table schema
- ERD
- metadata
- field definitions
- row-grain descriptions
- quality notes
- suppression rules

The state owner may approve the research request and provide these materials without releasing raw private records.

### 3. Build on Mock Data

Create synthetic data with the same structure as the private state data.

Example fields:

- first name
- last name
- date of birth
- address
- zip code
- student ID
- program
- graduation year
- wage quarter
- employer industry

Introduce realistic data quality problems:

- spelling variations
- nicknames
- missing DOB
- changed addresses
- hyphenated names
- transposed digits
- duplicated records

### 4. Implement Identifier Normalization

Normalize fields before encoding:

- lowercase text
- trim whitespace
- remove punctuation
- standardize date formats
- standardize phone and zip formats
- split names into tokens
- remove common suffixes

This should happen inside the approved execution environment when applied to private data.

### 5. Encode Identifiers

Use privacy-preserving encodings instead of raw identifiers.

Possible encoding strategy:

- salted hash for exact fields, such as DOB or student ID
- n-gram tokens for names and addresses
- Bloom filters for fuzzy comparison
- hash embeddings for approved cases where training data and assurance are available
- blocking keys to reduce the number of comparisons

Important: salts, keys, or secret parameters should be controlled by the data owner or trusted linkage environment, not exposed broadly.

The ONS Data Science Campus PPRL toolkit is a useful reference for the restricted-data path because it discusses Bloom filters, hash embeddings, secure cloud enclaves, and "eyes-off" linkage. Treat that toolkit as an experimental reference pattern that still requires state-owner approval and independent assurance before production use.

### 6. Block Candidate Pairs

Blocking reduces comparisons.

Examples:

- same birth year
- same zip prefix
- same phonetic last-name code
- same credential year
- same county

Blocking should be privacy-reviewed because overly specific blocking keys can still leak sensitive patterns.

### 7. Score Candidate Matches

Create match scores using approved encoded features.

Example scoring inputs:

- name similarity
- DOB agreement
- zip agreement
- address token similarity
- student ID hash agreement
- program or graduation-year consistency

The output should be a score and decision, not raw identifiers.

### 8. Set Match Thresholds

Define thresholds before running on private data.

Example:

- score >= 0.92: auto-match
- score 0.80 to 0.92: clerical review or owner-only review
- score < 0.80: non-match

Thresholds should be reviewed by the state owner because false matches and missed matches can affect policy conclusions.

### 9. Package Analysis Code and Define Requested Outputs

Package the PPRL code with the downstream analytics code.

Define the exact requested outputs, such as:

- pseudonymous linked IDs
- match scores
- match status
- aggregate wage summaries
- CTOT transition summaries
- O*NET occupation summaries
- dashboard-ready aggregate tables

### 10. Submit Code Through PySyft

Submit:

- PPRL code
- purpose statement
- mock data tests
- expected outputs
- privacy risk explanation
- match threshold rules
- requested released fields

The state owner reviews the request before execution.

### 11. Approved Execution Near Private Data

If approved, the PPRL code runs inside the state-controlled environment.

The researcher should not receive:

- raw identifiers
- raw private rows
- unapproved record-level extracts
- reusable secret salts or keys

### 12. State Owner Reviews Outputs

After execution, the state owner reviews outputs before release.

The owner can approve release, reject release, or request changes to the code or disclosure controls.

### 13. Release Approved Outputs

Possible approved outputs:

- linkage quality summary
- match counts
- match rates by group
- aggregate outcome tables
- pseudonymous linked IDs
- match confidence scores
- owner-approved linked analysis file

For many research projects, aggregate outputs are safer than releasing person-level linked IDs.

### 14. Perform CTOT/O*NET Analysis

After approved results are released, use them for downstream analysis:

- CTOT transition analysis
- O*NET skill and occupation mapping
- dashboards
- reports
- publication-ready findings

## What PySyft Allows

PySyft can allow PPRL as an approved workflow:

- researcher writes PPRL code
- owner reviews the code
- approved code runs near private state data
- outputs are checked before release

PySyft is not the PPRL algorithm itself. It is the secure workflow layer around the PPRL algorithm.

## What State Owners Must Decide

Each state owner should decide:

- whether PPRL is allowed
- which identifiers can be used for matching
- whether salts or keys are state-controlled
- whether matching happens locally or through a trusted service
- which outputs can be released
- whether linked IDs can leave the state environment
- whether small-cell suppression is required

## Researcher Submission Checklist

Before submitting your PPRL job, prepare:

- project purpose
- data fields requested for matching
- mock data examples
- linkage code
- scoring method
- threshold rules
- privacy risk notes
- expected output schema
- validation plan
- disclosure-control plan

## Suggested Output Schema

For a safer linked output, request only fields like:

| Field | Description |
| --- | --- |
| link_group_id | Pseudonymous ID for matched records |
| source_state | State or data owner source |
| match_score | Confidence score |
| match_status | auto_match, review, or non_match |
| program_group | Approved education grouping |
| outcome_group | Approved workforce outcome grouping |

Avoid requesting names, DOBs, addresses, phone numbers, emails, or raw student IDs.

## Plain-English Summary

As the researcher, you can build the PPRL method, but you should build and test it on mock data first. Then you submit it through PySyft. The state owner reviews it, approves it if appropriate, and runs it near private state data. PySyft allows this workflow, but the PPRL algorithm is yours or comes from an approved matching tool.
