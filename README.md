# SOB Data Pipeline

Python ETL pipeline for the Special Olympics Belgium data case.

## Project Structure

- `data/bronze`: raw Excel files
- `data/silver`: cleaned intermediate CSV files
- `data/gold`: final star schema CSV files
- `helpers`: Python helper functions
- `main.py`: runs the full pipeline

## Technologies

- Python
- Pandas
- MySQL
- GitHub
- Power BI

## Pipeline

1. Extract raw Excel files from the Bronze layer
2. Clean and standardize data into the Silver layer
3. Create final star schema tables in the Gold layer
4. Load Gold tables into MySQL

## Gold Tables

- `dim_athlete`
- `dim_certification`
- `dim_club`
- `dim_date`
- `dim_event`
- `dim_sport`
- `fact_results`

## Notes

The Gold tables are used for the Power BI semantic model.