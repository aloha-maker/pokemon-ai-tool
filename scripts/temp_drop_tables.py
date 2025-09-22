import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'pokemon_battle.db')

def drop_tables():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print("Dropping tables: party_members, parties")
        cursor.execute("DROP TABLE IF EXISTS party_members")
        cursor.execute("DROP TABLE IF EXISTS parties")
        conn.commit()
        print("Tables dropped successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    drop_tables()
