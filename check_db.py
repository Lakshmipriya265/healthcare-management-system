import sqlite3

try:
    conn = sqlite3.connect('healthcare.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    print(f"Tables found: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")
    
    if not tables:
        print("\nNo tables found. Database needs initialization.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
