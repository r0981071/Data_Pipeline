from sqlalchemy import create_engine, text


def load_gold_tables_to_mysql(gold_tables):
    username = "root"
    password = "root"
    host = "localhost"
    port = "3306"
    database = "sob_data_case"

    server_engine = create_engine(
        f"mysql+pymysql://{username}:{password}@{host}:{port}"
    )

    with server_engine.connect() as connection:
        connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {database}"))
        connection.commit()

    database_engine = create_engine(
        f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
    )

    for table_name, dataframe in gold_tables.items():
        dataframe.to_sql(
            name=table_name,
            con=database_engine,
            if_exists="replace",
            index=False
        )
        print(f"Loaded {table_name} into MySQL")