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


def create_silver_tables(bronze_data):
    results = pd.concat(bronze_data["results"], ignore_index=True)
    results = clean_column_names(results)
    results = clean_text_columns(results)

    clubs = clean_column_names(bronze_data["clubs"])
    clubs = clean_text_columns(clubs)

    certifications = clean_column_names(bronze_data["certifications"])
    certifications = clean_text_columns(certifications)

    if "dob" in results.columns:
        results["dob"] = pd.to_datetime(results["dob"], errors="coerce")

    if "dob" in certifications.columns:
        certifications["dob"] = pd.to_datetime(certifications["dob"], errors="coerce")

    if "age" in results.columns:
        results["age"] = pd.to_numeric(results["age"], errors="coerce")

    if "age" in certifications.columns:
        certifications["age"] = pd.to_numeric(certifications["age"], errors="coerce")

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
    athlete_cols = ["code", "gender", "dob", "age"]
    existing_athlete_cols = [col for col in athlete_cols if col in results.columns]

    dim_athlete = results[existing_athlete_cols].drop_duplicates().copy()
    dim_athlete = dim_athlete.rename(columns={"code": "athlete_code"})

    if "person_type" in certifications.columns:
        cert_person = certifications[["code", "person_type"]].drop_duplicates()
        cert_person = cert_person.rename(columns={"code": "athlete_code"})
        dim_athlete = dim_athlete.merge(cert_person, on="athlete_code", how="left")
    else:
        dim_athlete["person_type"] = None

    dim_athlete.insert(0, "athlete_id", range(1, len(dim_athlete) + 1))

    # DIM CLUB
    dim_club = clubs.copy()
    dim_club = dim_club.rename(columns={
        "name": "club_name"
    })

    keep_club_cols = [
        "group_number",
        "club_name",
        "primary_language",
        "city",
        "zipcode",
        "province",
        "country"
    ]

    keep_club_cols = [col for col in keep_club_cols if col in dim_club.columns]
    dim_club = dim_club[keep_club_cols].drop_duplicates().copy()

    if "group_number" in dim_club.columns:
        dim_club["group_number"] = dim_club["group_number"].astype(str).str.strip()

    dim_club.insert(0, "club_id", range(1, len(dim_club) + 1))

    # DIM SPORT
    dim_sport = results[["sport"]].drop_duplicates().copy()
    dim_sport["sport_code"] = dim_sport["sport"]
    dim_sport.insert(0, "sport_id", range(1, len(dim_sport) + 1))

    # DIM EVENT
    dim_event = results[["event", "sport"]].drop_duplicates().copy()
    dim_event = dim_event.merge(dim_sport, on="sport", how="left")
    dim_event = dim_event.rename(columns={"event": "event_name"})
    dim_event = dim_event[["event_name", "sport_id"]]
    dim_event.insert(0, "event_id", range(1, len(dim_event) + 1))

    # DIM DATE
    dim_date = results[["year"]].drop_duplicates().sort_values("year").copy()
    dim_date.insert(0, "date_id", range(1, len(dim_date) + 1))

    # DIM CERTIFICATION
    dim_certification = certifications.copy()
    dim_certification = dim_certification.rename(columns={
        "code": "athlete_code",
        "parents_consent": "parent_consent",
        "unified_partner_certificate": "unified_partner"
    })

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

    cert_cols = [col for col in cert_cols if col in dim_certification.columns]
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

    if "club" in fact_results.columns and "group_number" in dim_club.columns:
        fact_results["club"] = fact_results["club"].astype(str).str.strip()
        dim_club["group_number"] = dim_club["group_number"].astype(str).str.strip()

        fact_results = fact_results.merge(
            dim_club[["club_id", "group_number"]],
            left_on="club",
            right_on="group_number",
            how="left"
        )
    else:
        fact_results["club_id"] = None

    fact_results = fact_results.merge(
        dim_event,
        left_on="event",
        right_on="event_name",
        how="left"
    )

    fact_results = fact_results.merge(
        dim_date,
        on="year",
        how="left"
    )

    fact_keep_cols = [
        "athlete_id",
        "club_id",
        "event_id",
        "date_id",
        "role",
        "place",
        "score"
    ]

    fact_keep_cols = [col for col in fact_keep_cols if col in fact_results.columns]
    fact_results = fact_results[fact_keep_cols].copy()
    fact_results.insert(0, "result_id", range(1, len(fact_results) + 1))

    return {
        "dim_athlete": dim_athlete,
        "dim_club": dim_club,
        "dim_sport": dim_sport,
        "dim_event": dim_event,
        "dim_date": dim_date,
        "dim_certification": dim_certification,
        "fact_results": fact_results
    }