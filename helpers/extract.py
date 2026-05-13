from pathlib import Path
import pandas as pd


def load_bronze_files(bronze_path):
    bronze_path = Path(bronze_path)
    files = list(bronze_path.glob("*.xlsx"))

    data = {
        "results": [],
        "clubs": None,
        "certifications": None
    }

    for file in files:
        name = file.name.lower()

        if "clubs" in name:
            data["clubs"] = pd.read_excel(file)

        elif "certifications" in name:
            data["certifications"] = pd.read_excel(file)

        elif "results" in name:
            year = "".join([char for char in file.stem if char.isdigit()])
            df = pd.read_excel(file)
            df["year"] = int(year)
            data["results"].append(df)

    return data