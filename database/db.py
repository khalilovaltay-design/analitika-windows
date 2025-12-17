cur.execute("""
            CREATE TABLE IF NOT EXISTS investments
            (
                id
                INTEGER
                PRIMARY
                KEY
                AUTOINCREMENT,
                date
                TEXT,
                doctor_code
                TEXT,
                type
                TEXT, -- investment / debt / subsidy
                amount
                REAL,
                comment
                TEXT
            )
            """)
