import sys
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt
from qt_material import apply_stylesheet
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
        conn_str = (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
        )
        if self.auth_type == "Windows Authentication":
            conn_str += "Trusted_Connection=yes;"
        else:
            conn_str += f"UID={self.username};PWD={self.password};"
        self.conn = pyodbc.connect(conn_str)

    def execute_query(self, query):
        if self.conn is None:
            raise Exception("Keine Verbindung zur Datenbank.")
        cursor = self.conn.cursor()
        cursor.execute(query)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            data = cursor.fetchall()
            return columns, data
        self.conn.commit()
        return None, None


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login zur Datenbank")
        self.setFixedSize(350, 320)
        self.db_connector = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.server_input = QLineEdit("(localdb)\\mssqllocaldb")
        self.db_input = QLineEdit("Zoo")
        self.auth_combo = QComboBox()
        self.auth_combo.addItems(["Windows Authentication", "SQL Server Authentication"])
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.auth_combo.currentTextChanged.connect(self.toggle_auth_fields)

        for label, widget in [
            ("Server:", self.server_input),
            ("Datenbank:", self.db_input),
            ("Authentifizierung:", self.auth_combo),
            ("Benutzername:", self.user_input),
            ("Passwort:", self.pass_input)
        ]:
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)

        self.toggle_auth_fields(self.auth_combo.currentText())

        connect_btn = QPushButton("Verbinden")
        connect_btn.setMinimumHeight(35)
        connect_btn.clicked.connect(self.try_connect)
        layout.addStretch()
        connect_btn.setStyleSheet("margin-bottom: 10px;")
        layout.addWidget(connect_btn)

    def toggle_auth_fields(self, text):
        enabled = text == "SQL Server Authentication"
        self.user_input.setEnabled(enabled)
        self.pass_input.setEnabled(enabled)

    def try_connect(self):
        self.db_connector = DatabaseConnector(
            driver="ODBC Driver 17 for SQL Server",
            server=self.server_input.text(),
            database=self.db_input.text(),
            auth_type=self.auth_combo.currentText(),
            username=self.user_input.text() if self.user_input.isEnabled() else None,
            password=self.pass_input.text() if self.pass_input.isEnabled() else None
        )
        try:
            self.db_connector.connect()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Verbindungsfehler", str(e))


class AddEmployeeDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Mitarbeiter hinzufügen")
        self.setMinimumSize(400, 400)
        self.init_ui()
        self.load_departments()
        self.load_activities()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.department_combo = QComboBox()
        self.department_combo.setEditable(True)
        self.activity_combo = QComboBox()
        self.activity_combo.setEditable(True)
        self.first_name = QLineEdit()
        self.last_name = QLineEdit()
        self.street = QLineEdit()
        self.zip_code = QLineEdit()
        self.city = QLineEdit()

        for label, widget in [
            ("Abteilung:", self.department_combo),
            ("Tätigkeit:", self.activity_combo),
            ("Vorname:", self.first_name),
            ("Nachname:", self.last_name),
            ("Straße:", self.street),
            ("PLZ:", self.zip_code),
            ("Ort:", self.city)
        ]:
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)

        add_btn = QPushButton("Eintragen")
        add_btn.setMinimumHeight(35)
        add_btn.clicked.connect(self.insert_employee)
        layout.addWidget(add_btn)

    def load_departments(self):
        try:
            _, result = self.db.execute_query("SELECT Abt_ID, Bezeichnung FROM Abteilung;")
            for id_, name in result:
                self.department_combo.addItem(name, id_)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def load_activities(self):
        try:
            _, result = self.db.execute_query("SELECT Taetigkeiten_ID, Taetigkeiten_Name FROM Taetigkeiten;")
            for id_, name in result:
                self.activity_combo.addItem(name, id_)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def insert_employee(self):
        values = [
            self.department_combo.currentData(), self.last_name.text(), self.first_name.text(),
            self.street.text(), self.zip_code.text(), self.city.text(), self.activity_combo.currentData()
        ]
        if not values[1] or not values[2]:
            QMessageBox.warning(self, "Pflichtfeld", "Vorname und Nachname sind erforderlich.")
            return
        try:
            self.db.conn.cursor().execute(
                "INSERT INTO Mitarbeiter (Abt_NR, Name, Vorname, Strasse, PLZ, Ort, Taetigkeiten_ID) VALUES (?, ?, ?, ?, ?, ?, ?);",
                *values
            )
            self.db.conn.commit()
            QMessageBox.information(self, "Erfolg", "Mitarbeiter hinzugefügt.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("SQL Explorer")
        self.setWindowIcon(QIcon("eggplant.png"))
        self.setMinimumSize(1000, 600)
        self.init_ui()
        self.populate_views()
        self.display_roles()

    def init_ui(self):
        wrapper = QWidget()
        self.setCentralWidget(wrapper)

        # Kein Layout, wir machen alles direkt
        wrapper.setStyleSheet("background-color: transparent;")
        self.role_display = QLabel("Rolle(n): unbekannt", wrapper)
        self.role_display.setFont(QFont("Segoe UI", 9))
        self.role_display.setStyleSheet("""
            border: 2px solid #9C27B0;
            border-radius: 3px;
            padding: 1px;
            margin: 0px;
        """)
        self.role_display.move(10, 10)  # feste Position ganz oben links
        self.role_display.adjustSize()  # passt Größe exakt dem Text an

        # Rest der GUI mit Layout
        main_layout = QVBoxLayout(wrapper)
        main_layout.setContentsMargins(0, 30, 0, 0)  # oben etwas Platz für Label
        main_layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(10, 0, 10, 0)

        self.add_button = QPushButton("+ Mitarbeiter")
        self.add_button.setVisible(False)
        self.add_button.clicked.connect(self.show_add_dialog)

        header.addStretch()
        header.addWidget(self.add_button)
        main_layout.addLayout(header)

        split_main = QSplitter(Qt.Horizontal)

        split_right = QSplitter(Qt.Vertical)

        query_widget = QWidget()
        query_layout = QVBoxLayout(query_widget)
        query_layout.addWidget(QLabel("SQL-Abfrage:"))
        self.query_input = QTextEdit()
        query_layout.addWidget(self.query_input)
        self.run_btn = QPushButton("Ausführen")
        self.run_btn.setMinimumHeight(30)
        self.run_btn.clicked.connect(self.execute_sql)
        query_layout.addWidget(self.run_btn)
        split_right.addWidget(query_widget)

        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        self.result_table = QTableWidget()
        result_layout.addWidget(self.result_table)
        split_right.addWidget(result_widget)

        split_main.addWidget(split_right)
        self.view_list = QListWidget()
        self.view_list.itemClicked.connect(self.load_view_query)
        split_main.addWidget(self.view_list)
        split_main.setStretchFactor(0, 3)
        split_main.setStretchFactor(1, 1)
        main_layout.addWidget(split_main)

    def show_add_dialog(self):
        dlg = AddEmployeeDialog(self.db, self)
        dlg.exec()

    def load_view_query(self, item):
        view = item.text()
        self.query_input.setText(f"SELECT * FROM {view};")
        self.execute_sql()

    def execute_sql(self):
        query = self.query_input.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie eine SQL-Abfrage ein.")
            return
        try:
            cols, rows = self.db.execute_query(query)
            self.populate_table(cols, rows)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def populate_table(self, cols, rows):
        self.result_table.clear()
        if not cols:
            QMessageBox.information(self, "OK", "Abfrage ausgeführt. Keine Daten.")
            return
        self.result_table.setColumnCount(len(cols))
        self.result_table.setRowCount(len(rows))
        self.result_table.setHorizontalHeaderLabels(cols)
        for r, row in enumerate(rows):
            for c, cell in enumerate(row):
                self.result_table.setItem(r, c, QTableWidgetItem(str(cell)))
        self.result_table.resizeColumnsToContents()

    def populate_views(self):
        try:
            _, results = self.db.execute_query("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS;")
            self.view_list.clear()
            for row in results:
                self.view_list.addItem(row[0])
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def display_roles(self):
        query = """
        SELECT dp.name
        FROM sys.database_role_members drm
        JOIN sys.database_principals dp ON drm.role_principal_id = dp.principal_id
        JOIN sys.database_principals up ON drm.member_principal_id = up.principal_id
        WHERE up.name = USER_NAME();
        """
        try:
            _, roles = self.db.execute_query(query)
            if roles:
                role_names = [r[0] for r in roles]
                self.role_display.setText("Rolle(n): " + ", ".join(role_names))
                if "VERWALTUNG" in role_names:
                    self.add_button.setVisible(True)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))


def main():
    app = QApplication(sys.argv)
    dlg = LoginDialog()
    apply_stylesheet(dlg, 'dark_purple.xml', invert_secondary=False)
    if dlg.exec() == QDialog.Accepted:
        window = MainWindow(dlg.db_connector)
        apply_stylesheet(window, 'dark_purple.xml', invert_secondary=False)
        window.show()
        sys.exit(app.exec())
    sys.exit()


if __name__ == '__main__':
    main()
