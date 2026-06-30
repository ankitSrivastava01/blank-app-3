# Linkage Tool Flow Using PySyft and PPRL

Tool to link state datasets for analysis. Supports both non-restricted public statistical data and restricted private data.

## Purpose

This flow describes how a linkage tool can support state dataset integration while separating public statistical linkage from restricted person-level linkage.

The core distinction is:

- **Non-restricted / public statistical data** can often be linked directly using shared public keys and standardized fields.
- **Restricted / private data** should use privacy-preserving record linkage, secure execution, state-owner approval, and disclosure-controlled output release.

## 1. Data Sources

State datasets may include:

- education
- workforce
- employment
- wage
- program
- other state data

## 2. Ingestion and Metadata

The linkage tool ingests datasets and captures metadata.

Required metadata may include:

- table schema
- data dictionary
- ERD
- field definitions
- data source
- refresh cadence
- row grain
- privacy classification
- allowed use

The tool validates format and structure before linkage.

## 3. Data Classification

Each dataset is classified before linkage.

Classification questions:

- Is the data non-restricted / public statistical data?
- Is the data restricted / private?
- Does it include person-level records?
- Does it include direct or indirect identifiers?
- Is PPRL required?
- Is PySyft required for governed execution?

## Data Type Decision

```text
Data Sources
    |
    v
Ingestion and Metadata
    |
    v
Data Classification
    |
    v
Data Type?
    |
    +--> Flow A: Non-Restricted / Public Statistical Data
    |
    +--> Flow B: Restricted / Private Data Using PPRL + PySyft
```

## Flow A: Non-Restricted / Public Statistical Data

Use this path when data is public, aggregate, statistical, or otherwise non-restricted.

### A1. Standardize and Prepare

Actions:

- standardize fields
- apply code crosswalks
- normalize state, year, county, program, SOC, CIP, NAICS, and other shared keys
- handle missing values
- validate field types
- validate public-use constraints

### A2. Direct Linkage and Integration

Actions:

- link using shared keys
- merge and integrate datasets
- use public statistical identifiers such as state, year, county, program, SOC, CIP, or NAICS
- avoid unnecessary person-level linkage

### A3. Analysis and Output

Actions:

- compute statistics
- generate reports
- create dashboards
- store linked public analytical dataset

### Public Outputs

Allowed outputs may include:

- aggregate reports
- dashboards
- trend analysis
- cross-state comparisons
- program outcomes

## Flow B: Restricted / Private Data Using PPRL + PySyft

Use this path when data is restricted, private, person-level, or includes identifiers.

### B1. Access Request

Researchers or analysts request access for a research project.

The request should include:

- research purpose
- datasets requested
- linkage purpose
- fields required
- expected outputs
- disclosure-control plan

### B2. State Review and Approval

The state data owner reviews:

- purpose
- data use agreement
- legal requirements
- privacy requirements
- requested datasets
- requested usage

The owner approves or rejects the request.

### B3. Metadata and Mock/Proxy Data

If approved, the state owner provides development materials such as:

- approved metadata
- schema
- data dictionary
- ERD
- mock data
- proxy data

These materials support development and testing without exposing private records.

## Important PySyft Boundary

PySyft does **not** create mock data, synthetic data, or PPRL algorithms.

Researchers or data engineering teams provide:

- mock data
- synthetic data
- PPRL algorithm
- analytics code

PySyft provides:

- request workflow
- review workflow
- approval workflow
- secure code execution
- code-to-data execution
- audit trail
- approved output release

### B4. Develop and Test Using Mock Data

Researchers:

- develop linkage logic
- develop analysis code
- test using mock/proxy data
- validate outputs
- package code for submission

### B5. PPRL Linkage When Needed

When restricted identifiers are needed for linkage, use PPRL.

PPRL relies on cryptographic transformation and blind matching to protect privacy:

- **Obfuscation:** participating organizations encode PII such as names, dates of birth, addresses, or IDs into irreversible or hard-to-reverse tokens using approved cryptographic keys, salts, or privacy-preserving encodings.
- **Bloom filters:** a common PPRL method encodes identifiers into mathematical arrays that support approximate comparison without directly sharing the original identifiers.
- **Linkage:** encoded data can be compared by a neutral linkage agent, secure enclave, or state-controlled execution environment. The matching party compares encoded values without seeing the raw underlying personal data.

PPRL actions may include:

- generate privacy-preserving linkage tokens
- encrypt, hash, or tokenize identifiers
- generate Bloom-filter-style encodings
- use hash embeddings when approved training data and assurance are available
- match records across datasets without exposing identifiers
- create a project-level person identifier, such as `project_person_id`

Restricted data can include PPRS/PPRL-style encryption or tokenization mechanisms to protect identifiers during matching.

Bloom filters and related encodings should still be treated as sensitive. They reduce exposure of raw PII, but they require key management, parameter review, attack-risk assessment, and approval before production use.

The ONS Data Science Campus PPRL toolkit describes an experimental approach using Bloom filters, hash embeddings, secure cloud enclaves, and an "eyes-off" linkage pattern. That framing fits this tool as an optional restricted-data linkage approach, subject to state-owner approval and independent assurance.

### B6. Submit Code Through PySyft

Researchers submit tested code through PySyft.

The submission should define:

- inputs
- outputs
- privacy rules
- PPRL method
- linkage thresholds
- requested release fields

PySyft registers the request and creates an audit trail.

### B7. State Code Review

The state data owner reviews submitted code for:

- approved purpose
- privacy compliance
- disclosure control
- output rules
- PPRL/tokenization approach
- linkage quality risks

Possible decisions:

- approve
- reject
- request changes

### B8. Secure Execution in State Environment

If approved:

- code executes on restricted data inside the state environment
- researcher does not see or access raw data
- PPRL tokens are used for linkage
- approved analysis code produces requested results

### B9. Output Review and Disclosure Control

The state owner reviews generated results.

Disclosure controls may include:

- cell suppression
- threshold rules
- removal of direct identifiers
- review of linked IDs
- review of match scores
- re-identification risk checks

### B10. Approved Output to Researchers

Only approved outputs are released.

Approved outputs may include:

- aggregate outputs
- linkage quality metrics
- approved pseudonymous linkage IDs
- match scores
- summaries
- dashboard-ready statistical tables

No person-level raw data is shared unless explicitly approved under the applicable governance process.

## Example Restricted Data Linkage

```text
Dataset A: Education
    - name
    - DOB
    - student ID
    - CIP code
    - credential

Dataset B: Employment / Wage
    - SSN
    - employer ID
    - quarter
    - wage

Dataset C: Program
    - name
    - DOB
    - program type
    - completion

PPRL Tokenization
    - generate linkage tokens
    - create project_person_id for matched records

Linked Analytical Output
    - aggregate only
    - total count
    - employment rate
    - median wage
    - program outcomes
    - transition metrics
    - linkage quality
```

## Decision Guide

| Data Type | Person-Level Data? | Identifiers Present? | PPRL Needed? | PySyft Needed? | Linkage Approach |
| --- | --- | --- | --- | --- | --- |
| Public aggregate / statistical data | No | No | No | No | Direct linkage using keys |
| De-identified person-level data | Yes | No, direct identifiers removed | Maybe | Maybe | Controlled linkage, PySyft optional |
| Restricted person-level data | Yes | Yes | Yes | Yes | PPRL + secure execution with PySyft |
| Multi-agency restricted data | Yes | Yes | Yes | Yes | PPRL inside state + PySyft execution |

## Key Principles

- Raw restricted data never leaves the state environment.
- PPRL protects privacy during linkage.
- PySyft controls secure execution and output release.
- Researchers receive only approved, privacy-safe outputs.
- A full audit trail supports transparency and compliance.
- Layered security should be used for restricted linkage, including approved algorithms, encryption, secure execution environments, output review, and audit logs.

## Plain-English Summary

For public statistical data, the linkage tool can standardize fields and link directly using shared public keys.

For restricted state data, the researcher develops mock data, PPRL logic, and analytics code. The code is submitted through PySyft, reviewed by the state owner, executed inside the state environment, and released only after output review and disclosure control.

## References

- ONS Data Science Campus, "Developing a Privacy Preserving Record Linkage toolkit": https://datasciencecampus.ons.gov.uk/developing-a-privacy-preserving-record-linkage-toolkit/
