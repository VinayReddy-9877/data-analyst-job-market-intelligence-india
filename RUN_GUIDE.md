# Run Guide

This guide describes how to run the Data Analyst Job Market Intelligence project locally on Windows using PowerShell, Python 3.10+, PostgreSQL, Jupyter, and Power BI Desktop.

Run the commands from the project root:

```text
Data Analyst Job Market Intelligence Skill, Experience and Salary Analytics — India/
```

## 1. Create the Python Environment

Open PowerShell in the project root and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Build the Analytical Dataset

Run:

```powershell
python .\scripts\build_analytical_dataset.py
```

Expected core counts:

```text
Processed jobs:          4,035
Skill bridge rows:       6,213
Unique extracted skills: 44
```

The processed outputs are written to:

```text
data/processed/job_postings_clean.csv
data/processed/job_skills_bridge.csv
```

## 3. Run Analytical Validation

Run:

```powershell
python .\scripts\validate_analysis.py
```

The validation should confirm the analytical contract, including:

```text
Unique analytical jobs:       4,035
Job-skill bridge rows:         6,213
Unique normalized skills:         44
Salary-analysis eligible jobs:   110
```

A successful run should end with:

```text
ANALYTICAL VALIDATION PASS
```

## 4. Configure PostgreSQL

Create a PostgreSQL database named:

```text
job_market
```

Set the connection variables in the current PowerShell session:

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="job_market"
$env:PGUSER="postgres"

$sec = Read-Host "Enter PostgreSQL password" -AsSecureString
$env:PGPASSWORD = [System.Net.NetworkCredential]::new("", $sec).Password
```

## 5. Load the PostgreSQL Star Schema

Run:

```powershell
python .\scripts\load_to_postgres.py
```

Expected database counts:

```text
Fact jobs:               4,035
Bridge job-skill rows:   6,213
Unique skills:              44
Salary-eligible jobs:      110
```

The project uses the PostgreSQL schema:

```text
job_market
```

Core model objects include:

```text
job_market.dim_role
job_market.dim_company
job_market.dim_location
job_market.dim_date
job_market.dim_skill
job_market.fact_jobs
job_market.bridge_job_skill
```

Reporting views:

```text
job_market.vw_jobs_enriched
job_market.vw_job_skills
```

## 6. Run the SQL Analysis

Open the following file in pgAdmin Query Tool while connected to the `job_market` database:

```text
sql/analysis_queries.sql
```

Execute the script against the `job_market` schema.

The SQL analysis includes CTEs, window functions, ranking, conditional aggregation, skill co-occurrence, salary analysis, percentiles, and descriptive trend calculations.

## 7. Execute the Jupyter Notebook

Run:

```powershell
jupyter nbconvert --to notebook --execute ".\notebooks\analysis.ipynb" --inplace
```

The notebook performs the Python EDA and statistical analysis and writes analytical outputs under the project reporting folders.

## 8. Open the Power BI Dashboard

The Power BI project is stored at:

```text
dashboard/DataAnalystJobMarketIntelligence.pbip
```

Open that `.pbip` file in Power BI Desktop.

The `.pbip` file must remain beside its associated Power BI project folders in `dashboard/`.

## 9. Power BI PostgreSQL Connection

Use:

```text
Server:   localhost
Database: job_market
Schema:   job_market
```

The reporting layer uses the project PostgreSQL model and reporting views.

If Power BI asks for approval to run a native query, review the query and approve the read-only `SELECT` / `WITH ... SELECT` statements used by the project.

## 10. Refresh the Dashboard

In Power BI Desktop:

1. Open `dashboard/DataAnalystJobMarketIntelligence.pbip`.
2. Confirm the PostgreSQL connection to `localhost / job_market`.
3. Click **Home → Refresh**.
4. Allow the model to finish loading.
5. Confirm the report pages render with the expected analytical results.

Core dashboard checks:

```text
Analytical jobs:              4,035
Known companies:              1,364
Unique specific-city labels:     96
Skill-tagged jobs:            1,744
Salary-analysis jobs:           110
Median validated salary:      ₹9.50L
SQL jobs:                       850
Bengaluru jobs:               1,073
```

## 11. Dashboard Supporting Files

Power BI supporting documentation and screenshots are stored under:

```text
dashboard/
```

Key files include:

```text
dashboard/DAX_MEASURES
dashboard/DASHBOARD_CALCULATIONS.md
dashboard/KPI_EXPECTED_VALUES.md
dashboard/POWERBI_ANALYSIS_RESULTS.md
dashboard/POWERBI_VALIDATED_RESULTS.xlsx
dashboard/Dashboard_Images/
```

## 12. Final Analytical Contract

A complete local run should remain consistent with:

```text
Raw source vacancies:          4,046
Final analytical jobs:         4,035
Job-skill relationships:       6,213
Normalized skills:                44
Skill-tagged jobs:             1,744
Salary-analysis eligible jobs:   110
```

The raw source count and analytical count are intentionally different: the raw snapshot contains 4,046 unique source vacancies, while the analytical inclusion and validation rules retain 4,035 jobs for reporting.
