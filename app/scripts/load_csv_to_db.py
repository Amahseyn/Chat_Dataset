import pandas as pd
from database.session import SessionLocal, init_db
from models.property_model import Property

def load_csv_to_db(csv_file_path):
    df = pd.read_csv(csv_file_path)
    df = df.head(100)  # Limit to first 100 rows for testing

    db = SessionLocal()
    for _, row in df.iterrows():
        prop = Property(**row.to_dict())
        db.add(prop)
    db.commit()
    db.close()
    print("✅ CSV data loaded into the database successfully!")

if __name__ == "__main__":
    init_db()
    csv_file_path = "data/data.csv"  # Adjust the path as necessary
    load_csv_to_db(csv_file_path)