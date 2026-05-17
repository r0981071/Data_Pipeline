import pandas as pd


def clean_column_names(df):
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
    )
    return df


def clean_text_columns(df):
    df = df.copy()

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": None, "None": None, "": None})

    return df


def clean_age(df):
    df = df.copy()

    if "age" in df.columns:
        df["age"] = pd.to_numeric(df["age"], errors="coerce")
        df.loc[df["age"] > 120, "age"] = df.loc[df["age"] > 120, "age"] / 10
        df["age"] = df["age"].round().astype("Int64")

    return df


def normalize_text(value):
    if pd.isna(value):
        return None
    return str(value).strip().upper()


def clean_certification_columns(certifications):
    certifications = certifications.copy()

    certifications = certifications.rename(columns={
        "code": "athlete_code",
        "parents_consent_sob_has_this_certificate": "parent_consent",
        "mental_handicap_sob_has_this_certificate": "mental_handicap_certificate",
        "hap_sob_has_this_certificate": "hap_certificate",
        "unified_partner_sob_has_this_certificate": "unified_partner"
    })

    certificate_cols = [
        "mental_handicap_certificate",
        "parent_consent",
        "hap_certificate",
        "unified_partner"
    ]

    for col in certificate_cols:
        if col in certifications.columns:
            certifications[col] = certifications[col].fillna(0).astype(bool)

    return certifications


def create_silver_tables(bronze_data):
    results = pd.concat(bronze_data["results"], ignore_index=True)
    results = clean_column_names(results)
    results = clean_text_columns(results)

    clubs = clean_column_names(bronze_data["clubs"])
    clubs = clean_text_columns(clubs)

    certifications = clean_column_names(bronze_data["certifications"])
    certifications = clean_text_columns(certifications)
    certifications = clean_certification_columns(certifications)

    if "dob" in results.columns:
        results["dob"] = pd.to_datetime(results["dob"], errors="coerce")

    if "dob" in certifications.columns:
        certifications["dob"] = pd.to_datetime(certifications["dob"], errors="coerce")

    results = clean_age(results)
    certifications = clean_age(certifications)

    results = results.drop_duplicates()
    clubs = clubs.drop_duplicates()
    certifications = certifications.drop_duplicates()

    return {
        "cleaned_results": results,
        "cleaned_clubs": clubs,
        "cleaned_certifications": certifications
    }


def create_gold_tables(silver_tables):
    results = silver_tables["cleaned_results"].copy()
    clubs = silver_tables["cleaned_clubs"].copy()
    certifications = silver_tables["cleaned_certifications"].copy()

    # DIM ATHLETE
    athlete_from_results = results[["code", "gender", "dob", "age"]].drop_duplicates().copy()
    athlete_from_results = athlete_from_results.rename(columns={"code": "athlete_code"})
    athlete_from_results["person_type"] = None

    athlete_from_certifications = certifications[
        ["athlete_code", "gender", "dob", "age", "person_type"]
    ].drop_duplicates().copy()

    dim_athlete = pd.concat(
        [athlete_from_certifications, athlete_from_results],
        ignore_index=True
    )

    dim_athlete = dim_athlete.drop_duplicates(subset=["athlete_code"])
    dim_athlete.insert(0, "athlete_id", range(1, len(dim_athlete) + 1))

    # DIM CLUB
    dim_club = clubs.copy()
    dim_club = dim_club.rename(columns={"name": "club_name"})

    keep_club_cols = [
        "group_number",
        "club_name",
        "primary_language",
        "city",
        "zipcode",
        "province",
        "country"
    ]

    dim_club = dim_club[keep_club_cols].drop_duplicates().copy()
    dim_club["group_number"] = dim_club["group_number"].astype(str).str.strip()
    dim_club["club_name_clean"] = dim_club["club_name"].apply(normalize_text)
    dim_club.insert(0, "club_id", range(1, len(dim_club) + 1))

    # DIM SPORT
    dim_sport = results[["sport"]].drop_duplicates().copy()
    dim_sport.insert(0, "sport_id", range(1, len(dim_sport) + 1))

    # DIM EVENT
    dim_event_lookup = results[["event", "sport"]].drop_duplicates().copy()
    dim_event_lookup = dim_event_lookup.merge(dim_sport, on="sport", how="left")
    dim_event_lookup = dim_event_lookup.rename(columns={"event": "event_name"})
    dim_event_lookup.insert(0, "event_id", range(1, len(dim_event_lookup) + 1))

    dim_event = dim_event_lookup[["event_id", "event_name", "sport_id"]].copy()

    # DIM DATE
    dim_date = results[["year"]].drop_duplicates().sort_values("year").copy()
    dim_date.insert(0, "date_id", range(1, len(dim_date) + 1))

    # DIM CERTIFICATION
    dim_certification = certifications.copy()

    dim_certification = dim_certification.merge(
        dim_athlete[["athlete_id", "athlete_code"]],
        on="athlete_code",
        how="left"
    )

    cert_cols = [
        "athlete_id",
        "mental_handicap_certificate",
        "parent_consent",
        "hap_certificate",
        "unified_partner"
    ]

    dim_certification = dim_certification[cert_cols].drop_duplicates().copy()
    dim_certification.insert(0, "certification_id", range(1, len(dim_certification) + 1))

    # FACT RESULTS
    fact_results = results.copy()
    fact_results = fact_results.rename(columns={"code": "athlete_code"})

    fact_results = fact_results.merge(
        dim_athlete[["athlete_id", "athlete_code"]],
        on="athlete_code",
        how="left"
    )

    fact_results["club_clean"] = fact_results["club"].apply(normalize_text)

    fact_results = fact_results.merge(
        dim_club[["club_id", "club_name_clean"]],
        left_on="club_clean",
        right_on="club_name_clean",
        how="left"
    )

    fact_results = fact_results.merge(
        dim_event_lookup[["event_id", "event_name", "sport"]],
        left_on=["event", "sport"],
        right_on=["event_name", "sport"],
        how="left"
    )

    fact_results = fact_results.merge(
        dim_date,
        on="year",
        how="left"
    )

    fact_results = fact_results[
        [
            "athlete_id",
            "club_id",
            "event_id",
            "date_id",
            "role",
            "place",
            "score"
        ]
    ].copy()

    fact_results.insert(0, "result_id", range(1, len(fact_results) + 1))

    # Remove helper column from dim_club before export
    dim_club = dim_club.drop(columns=["club_name_clean"])

    return {
        "dim_athlete": dim_athlete,
        "dim_club": dim_club,
        "dim_sport": dim_sport,
        "dim_event": dim_event,
        "dim_date": dim_date,
        "dim_certification": dim_certification,
        "fact_results": fact_results
    }