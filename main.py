from helpers.extract import load_bronze_files
from helpers.transform import create_silver_tables, create_gold_tables
from helpers.load import save_tables
from helpers.database import load_gold_tables_to_mysql


def main():
    bronze_data = load_bronze_files("data/bronze")

    silver_tables = create_silver_tables(bronze_data)
    save_tables(silver_tables, "data/silver")

    gold_tables = create_gold_tables(silver_tables)
    save_tables(gold_tables, "data/gold")

    load_gold_tables_to_mysql(gold_tables)

    print("ETL pipeline finished successfully.")


if __name__ == "__main__":
    main()