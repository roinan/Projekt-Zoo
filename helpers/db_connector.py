import pyodbc


class DatabaseConnector:
    def __init__(self, driver, server, database, auth_type, username=None, password=None):
        self.driver = driver
        self.server = server
        self.database = database
        self.auth_type = auth_type
        self.username = username
        self.password = password
        self.conn = None

    def connect(self):
        if self.auth_type == "Windows Authentication":
            conn_str = (
                f"DRIVER={{{self.driver}}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                "Trusted_Connection=yes;"
            )
            print("Windows Login")
        else:
            conn_str = (
                f"DRIVER={{{self.driver}}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
            )
        try:
            self.conn = pyodbc.connect(conn_str)
        except Exception as e:
            raise Exception(f"Verbindungsfehler: {e}")

    def execute_query(self, query):
        if self.conn is None:
            raise Exception("Keine Verbindung zur Datenbank.")
        cursor = self.conn.cursor()
        try:
            cursor.execute(query)
            if cursor.description:  # SELECT-Abfrage liefert Ergebnisse
                columns = [column[0] for column in cursor.description]
                results = cursor.fetchall()
                return columns, results
            else:
                self.conn.commit()
                return None, None
        except Exception as e:
            raise Exception(f"Fehler beim Ausführen der Abfrage: {e}")
