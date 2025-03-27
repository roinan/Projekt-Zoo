import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QListWidget,
    QTextEdit, QTableWidget, QTableWidgetItem, QComboBox, QSplitter, QDialog
)
from PySide6.QtGui import QIcon
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
        if self.auth_type == "Windows Authentication":
            conn_str = (
                f"DRIVER={{{self.driver}}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                "Trusted_Connection=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{{self.driver}}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
            )
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
        self.setWindowTitle("Verbindung zur Datenbank")
        self.setMinimumWidth(300)
        self.db_connector = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Server:"))
        self.server_input = QLineEdit("(localdb)\\mssqllocaldb")
        layout.addWidget(self.server_input)

        layout.addWidget(QLabel("Datenbank:"))
        self.db_input = QLineEdit("Zoo")
        layout.addWidget(self.db_input)

        layout.addWidget(QLabel("Authentifizierung:"))
        self.auth_combo = QComboBox()
        self.auth_combo.addItems(["Windows Authentication", "SQL Server Authentication"])
        self.auth_combo.currentTextChanged.connect(self.toggle_auth_fields)
        layout.addWidget(self.auth_combo)

        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("Benutzername:"))
        layout.addWidget(self.user_input)
        layout.addWidget(QLabel("Passwort:"))
        layout.addWidget(self.pass_input)

        self.toggle_auth_fields(self.auth_combo.currentText())

        connect_btn = QPushButton("Verbinden")
        connect_btn.clicked.connect(self.try_connect)
        layout.addWidget(connect_btn)

    def toggle_auth_fields(self, mode):
        enable = mode == "SQL Server Authentication"
        self.user_input.setEnabled(enable)
        self.pass_input.setEnabled(enable)

    def try_connect(self):
        driver = "ODBC Driver 17 for SQL Server"
        server = self.server_input.text().strip()
        db = self.db_input.text().strip()
        auth = self.auth_combo.currentText()
        user = self.user_input.text().strip() if auth == "SQL Server Authentication" else None
        pwd = self.pass_input.text() if auth == "SQL Server Authentication" else None

        self.db_connector = DatabaseConnector(driver, server, db, auth, user, pwd)
        try:
            self.db_connector.connect()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))


class AddEmployeeDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neuen Mitarbeiter eintragen")
        self.setMinimumWidth(350)
        self.db = db
        self.init_ui()
        self.load_departments()
        self.load_activities()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.department_combo = QComboBox()
        self.department_combo.setEditable(True)
        layout.addWidget(QLabel("Abteilung:"))
        layout.addWidget(self.department_combo)

        self.activity_combo = QComboBox()
        self.activity_combo.setEditable(True)
        layout.addWidget(QLabel("Tätigkeit:"))
        layout.addWidget(self.activity_combo)

        self.first_name = QLineEdit()
        layout.addWidget(QLabel("Vorname:"))
        layout.addWidget(self.first_name)

        self.last_name = QLineEdit()
        layout.addWidget(QLabel("Nachname:"))
        layout.addWidget(self.last_name)

        self.street = QLineEdit()
        layout.addWidget(QLabel("Straße:"))
        layout.addWidget(self.street)

        self.zip_code = QLineEdit()
        layout.addWidget(QLabel("PLZ:"))
        layout.addWidget(self.zip_code)

        self.city = QLineEdit()
        layout.addWidget(QLabel("Ort:"))
        layout.addWidget(self.city)

        add_btn = QPushButton("Eintragen")
        add_btn.clicked.connect(self.insert_employee)
        layout.addWidget(add_btn)

    def load_departments(self):
        try:
            _, result = self.db.execute_query("SELECT Abt_ID, Bezeichnung FROM Abteilung;")
            self.department_combo.clear()
            for id_, name in result:
                self.department_combo.addItem(name, id_)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def load_activities(self):
        try:
            _, result = self.db.execute_query("SELECT Taetigkeiten_ID, Taetigkeiten_Name FROM Taetigkeiten;")
            self.activity_combo.clear()
            for id_, name in result:
                self.activity_combo.addItem(name, id_)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def insert_employee(self):
        dept = self.department_combo.currentData()
        act = self.activity_combo.currentData()
        fname = self.first_name.text().strip()
        lname = self.last_name.text().strip()
        street = self.street.text().strip()
        zip_code = self.zip_code.text().strip()
        city = self.city.text().strip()

        if not fname or not lname:
            QMessageBox.warning(self, "Pflichtfelder", "Vor- und Nachname sind erforderlich.")
            return

        query = """
        INSERT INTO Mitarbeiter (Abt_NR, Name, Vorname, Strasse, PLZ, Ort, Taetigkeiten_ID)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        try:
            cursor = self.db.conn.cursor()
            cursor.execute(query, dept, lname, fname, street, zip_code, city, act)
            self.db.conn.commit()
            QMessageBox.information(self, "Erfolg", "Mitarbeiter hinzugefügt.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.setWindowTitle("SQL Explorer")
        self.setWindowIcon(QIcon("eggplant.png"))
        self.db = db
        self.init_ui()
        self.populate_views()
        self.display_roles()

    def init_ui(self):
        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)

        top_bar = QHBoxLayout()
        self.role_display = QLabel("Rolle(n): ...")
        self.add_button = QPushButton("+ Mitarbeiter")
        self.add_button.setVisible(False)
        self.add_button.clicked.connect(self.show_add_dialog)
        top_bar.addStretch()
        top_bar.addWidget(self.role_display)
        top_bar.addWidget(self.add_button)
        layout.addLayout(top_bar)

        main_splitter = QSplitter(Qt.Horizontal)
        self.view_list = QListWidget()
        self.view_list.itemClicked.connect(self.load_view_query)
        main_splitter.addWidget(self.view_list)

        right_splitter = QSplitter(Qt.Vertical)

        query_section = QWidget()
        qlayout = QVBoxLayout(query_section)
        qlayout.addWidget(QLabel("SQL-Abfrage:"))
        self.query_input = QTextEdit()
        qlayout.addWidget(self.query_input)
        self.run_btn = QPushButton("Ausführen")
        self.run_btn.clicked.connect(self.execute_sql)
        qlayout.addWidget(self.run_btn)
        right_splitter.addWidget(query_section)

        result_section = QWidget()
        rlayout = QVBoxLayout(result_section)
        self.result_table = QTableWidget()
        rlayout.addWidget(self.result_table)
        right_splitter.addWidget(result_section)

        main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(1, 3)
        layout.addWidget(main_splitter)

    def show_add_dialog(self):
        dialog = AddEmployeeDialog(self.db, self)
        dialog.exec()

    def load_view_query(self, item):
        view = item.text()
        self.query_input.setText(f"SELECT * FROM {view};")
        self.execute_sql()

    def execute_sql(self):
        query = self.query_input.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "Hinweis", "Bitte geben Sie eine Abfrage ein.")
            return
        try:
            columns, rows = self.db.execute_query(query)
            self.display_results(columns, rows)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def display_results(self, headers, data):
        self.result_table.clear()
        if not headers:
            QMessageBox.information(self, "OK", "Abfrage erfolgreich. Keine Daten.")
            return
        self.result_table.setColumnCount(len(headers))
        self.result_table.setRowCount(len(data))
        self.result_table.setHorizontalHeaderLabels(headers)
        for i, row in enumerate(data):
            for j, val in enumerate(row):
                self.result_table.setItem(i, j, QTableWidgetItem(str(val)))
        self.result_table.resizeColumnsToContents()

    def populate_views(self):
        try:
            c, v = self.db.execute_query("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS;")
            self.view_list.clear()
            for row in v:
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
            else:
                self.role_display.setText("Rolle(n): Keine")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))


def main():
    app = QApplication(sys.argv)
    dlg = LoginDialog()
    apply_stylesheet(dlg, 'light_blue.xml', invert_secondary=True)
    if dlg.exec() == QDialog.Accepted:
        window = MainWindow(dlg.db_connector)
        apply_stylesheet(window, 'light_blue.xml', invert_secondary=True)
        window.show()
        sys.exit(app.exec())
    sys.exit()


if __name__ == '__main__':
    main()