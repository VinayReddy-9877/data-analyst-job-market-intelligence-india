-- Data Analyst Job Market Intelligence: Skill, Experience & Salary Analytics — India
-- PostgreSQL analytical star schema

CREATE SCHEMA IF NOT EXISTS job_market;

DROP VIEW IF EXISTS job_market.vw_job_skills CASCADE;
DROP VIEW IF EXISTS job_market.vw_jobs_enriched CASCADE;

DROP TABLE IF EXISTS job_market.bridge_job_skill CASCADE;
DROP TABLE IF EXISTS job_market.fact_jobs CASCADE;
DROP TABLE IF EXISTS job_market.dim_skill CASCADE;
DROP TABLE IF EXISTS job_market.dim_date CASCADE;
DROP TABLE IF EXISTS job_market.dim_location CASCADE;
DROP TABLE IF EXISTS job_market.dim_company CASCADE;
DROP TABLE IF EXISTS job_market.dim_role CASCADE;


CREATE TABLE job_market.dim_role (
    role_key BIGSERIAL PRIMARY KEY,
    role_family TEXT NOT NULL UNIQUE
);


CREATE TABLE job_market.dim_company (
    company_key BIGSERIAL PRIMARY KEY,
    company_name TEXT NOT NULL UNIQUE
);


CREATE TABLE job_market.dim_location (
    location_key BIGSERIAL PRIMARY KEY,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    location_name TEXT,
    location_scope TEXT NOT NULL,

    UNIQUE (
        city,
        state,
        location_name,
        location_scope
    )
);


CREATE TABLE job_market.dim_date (
    date_key DATE PRIMARY KEY,
    calendar_year INTEGER NOT NULL,
    calendar_month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    year_month TEXT NOT NULL,
    week_start DATE NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name TEXT NOT NULL,

    CHECK (calendar_month BETWEEN 1 AND 12),
    CHECK (day_of_week BETWEEN 0 AND 6)
);


CREATE TABLE job_market.dim_skill (
    skill_key BIGSERIAL PRIMARY KEY,
    skill TEXT NOT NULL UNIQUE,
    skill_category TEXT NOT NULL
);


CREATE TABLE job_market.fact_jobs (
    job_key BIGSERIAL PRIMARY KEY,
    job_id TEXT NOT NULL UNIQUE,

    role_key BIGINT NOT NULL
        REFERENCES job_market.dim_role(role_key),

    company_key BIGINT NOT NULL
        REFERENCES job_market.dim_company(company_key),

    location_key BIGINT NOT NULL
        REFERENCES job_market.dim_location(location_key),

    date_key DATE NOT NULL
        REFERENCES job_market.dim_date(date_key),

    source TEXT,
    source_family TEXT,
    source_provider TEXT,

    title TEXT NOT NULL,
    description TEXT,

    work_mode TEXT NOT NULL,

    experience_min_years NUMERIC(6,2),
    experience_max_years NUMERIC(6,2),
    experience_band TEXT NOT NULL,

    salary_min_source NUMERIC(18,2),
    salary_max_source NUMERIC(18,2),

    salary_min NUMERIC(18,2),
    salary_max NUMERIC(18,2),
    salary_midpoint NUMERIC(18,2),

    salary_is_predicted BOOLEAN,
    has_salary_source BOOLEAN NOT NULL,
    salary_analysis_eligible BOOLEAN NOT NULL,

    salary_normalization_status TEXT,
    salary_text_evidence TEXT,

    skill_count INTEGER NOT NULL,
    has_extracted_skill BOOLEAN NOT NULL,

    is_recent_90d BOOLEAN NOT NULL,
    is_complete_week BOOLEAN NOT NULL,

    contract_type TEXT,
    contract_time TEXT,
    redirect_url TEXT,

    CHECK (
        experience_min_years IS NULL
        OR experience_min_years >= 0
    ),

    CHECK (
        experience_max_years IS NULL
        OR experience_max_years >= 0
    ),

    CHECK (
        experience_min_years IS NULL
        OR experience_max_years IS NULL
        OR experience_max_years >= experience_min_years
    ),

    CHECK (
        salary_min IS NULL
        OR salary_min > 0
    ),

    CHECK (
        salary_max IS NULL
        OR salary_max > 0
    ),

    CHECK (
        salary_min IS NULL
        OR salary_max IS NULL
        OR salary_max >= salary_min
    ),

    CHECK (
        NOT salary_analysis_eligible
        OR (
            salary_min IS NOT NULL
            AND salary_max IS NOT NULL
            AND salary_midpoint IS NOT NULL
        )
    ),

    CHECK (skill_count >= 0)
);


CREATE TABLE job_market.bridge_job_skill (
    job_key BIGINT NOT NULL
        REFERENCES job_market.fact_jobs(job_key)
        ON DELETE CASCADE,

    skill_key BIGINT NOT NULL
        REFERENCES job_market.dim_skill(skill_key)
        ON DELETE CASCADE,

    PRIMARY KEY (
        job_key,
        skill_key
    )
);


CREATE INDEX idx_fact_jobs_role_key
    ON job_market.fact_jobs(role_key);

CREATE INDEX idx_fact_jobs_company_key
    ON job_market.fact_jobs(company_key);

CREATE INDEX idx_fact_jobs_location_key
    ON job_market.fact_jobs(location_key);

CREATE INDEX idx_fact_jobs_date_key
    ON job_market.fact_jobs(date_key);

CREATE INDEX idx_fact_jobs_experience_band
    ON job_market.fact_jobs(experience_band);

CREATE INDEX idx_fact_jobs_salary_eligible
    ON job_market.fact_jobs(salary_analysis_eligible);

CREATE INDEX idx_fact_jobs_recent_90d
    ON job_market.fact_jobs(is_recent_90d);

CREATE INDEX idx_fact_jobs_complete_week
    ON job_market.fact_jobs(is_complete_week);

CREATE INDEX idx_fact_jobs_work_mode
    ON job_market.fact_jobs(work_mode);

CREATE INDEX idx_location_scope
    ON job_market.dim_location(location_scope);

CREATE INDEX idx_bridge_job_skill_skill_key
    ON job_market.bridge_job_skill(skill_key);


CREATE OR REPLACE VIEW job_market.vw_jobs_enriched AS
SELECT
    f.job_key,
    f.job_id,
    f.title,

    r.role_family,
    c.company_name,

    l.city,
    l.state,
    l.location_name,
    l.location_scope,

    f.work_mode,

    f.experience_min_years,
    f.experience_max_years,
    f.experience_band,

    f.salary_min_source,
    f.salary_max_source,

    f.salary_min,
    f.salary_max,
    f.salary_midpoint,

    f.salary_is_predicted,
    f.has_salary_source,
    f.salary_analysis_eligible,
    f.salary_normalization_status,
    f.salary_text_evidence,

    f.skill_count,
    f.has_extracted_skill,

    f.is_recent_90d,
    f.is_complete_week,

    f.source,
    f.source_family,
    f.source_provider,

    f.date_key AS posted_date,
    d.calendar_year,
    d.calendar_month,
    d.month_name,
    d.year_month,
    d.week_start,
    d.day_of_week,
    d.day_name,

    f.contract_type,
    f.contract_time,
    f.redirect_url

FROM job_market.fact_jobs AS f

JOIN job_market.dim_role AS r
    ON f.role_key = r.role_key

JOIN job_market.dim_company AS c
    ON f.company_key = c.company_key

JOIN job_market.dim_location AS l
    ON f.location_key = l.location_key

JOIN job_market.dim_date AS d
    ON f.date_key = d.date_key;


CREATE OR REPLACE VIEW job_market.vw_job_skills AS
SELECT
    f.job_key,
    f.job_id,
    f.title,

    r.role_family,
    c.company_name,

    l.city,
    l.state,
    l.location_name,
    l.location_scope,

    f.work_mode,
    f.experience_band,

    f.salary_midpoint,
    f.salary_analysis_eligible,

    f.is_recent_90d,
    f.is_complete_week,

    f.date_key AS posted_date,

    s.skill,
    s.skill_category

FROM job_market.bridge_job_skill AS b

JOIN job_market.fact_jobs AS f
    ON b.job_key = f.job_key

JOIN job_market.dim_skill AS s
    ON b.skill_key = s.skill_key

JOIN job_market.dim_role AS r
    ON f.role_key = r.role_key

JOIN job_market.dim_company AS c
    ON f.company_key = c.company_key

JOIN job_market.dim_location AS l
    ON f.location_key = l.location_key;


    