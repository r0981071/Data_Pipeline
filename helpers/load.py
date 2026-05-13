from pathlib import Path


def save_tables(tables, output_path):
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    for table_name, dataframe in tables.items():
        file_path = output_path / f"{table_name}.csv"
        dataframe.to_csv(file_path, index=False, encoding="utf-8-sig")
        print(f"Saved {file_path}")