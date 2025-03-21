from PySide6 import QtWidgets
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox

class AddEmployeeDialog(QDialog):
    def __init__(self, db_connector, parent=None):
        super().__init__(parent)
        self.db_connector = db_connector
        self.setWindowTitle("Mitarbeiter hinzufügen")
        self.setup_ui()
        self.load_departments()
        self.load_activities()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Dropdown für Abteilung (mit Suchfunktion, da editierbar)
        layout.addWidget(QLabel("Abteilung:"))
        self.department_combo = QtWidgets.QComboBox()
        self.department_combo.setEditable(True)  # Ermöglicht Eingabe zur Suche
        layout.addWidget(self.department_combo)

        # Dropdown für Tätigkeiten (mit Suchfunktion)
        layout.addWidget(QLabel("Tätigkeit:"))
        self.activity_combo = QtWidgets.QComboBox()
        self.activity_combo.setEditable(True)
        layout.addWidget(self.activity_combo)

        # Vorname
        layout.addWidget(QLabel("Vorname:"))
        self.first_name_edit = QLineEdit()
        layout.addWidget(self.first_name_edit)

        # Nachname
        layout.addWidget(QLabel("Nachname:"))
        self.last_name_edit = QLineEdit()
        layout.addWidget(self.last_name_edit)

        # Strasse
        layout.addWidget(QLabel("Strasse:"))
        self.street_edit = QLineEdit()
        layout.addWidget(self.street_edit)

        # PLZ
        layout.addWidget(QLabel("PLZ:"))
        self.plz_edit = QLineEdit()
        layout.addWidget(self.plz_edit)

        # Ort
        layout.addWidget(QLabel("Ort:"))
        self.city_edit = QLineEdit()
        layout.addWidget(self.city_edit)

        # Button zum Hinzufügen
        self.add_button = QPushButton("Hinzufügen")
        self.add_button.clicked.connect(self.add_employee)
        layout.addWidget(self.add_button)

    def load_departments(self):
        # Annahme: Tabelle "Abteilungen" mit Spalten Abt_NR und Name
        query = "SELECT Abt_ID, Bezeichnung FROM Abteilung;"
        try:
            cols, results = self.db_connector.execute_query(query)
            if results:
                self.department_combo.clear()
                for row in results:
                    # row[0]: Abt_NR, row[1]: Name
                    self.department_combo.addItem(row[1], row[0])
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Abteilungen: {e}")

    def load_activities(self):
        # Annahme: Tabelle "Taetigkeiten" mit Spalten Taetigkeiten_ID und Name
        query = "SELECT Taetigkeiten_ID, Taetigkeiten_Name FROM Taetigkeiten;"
        try:
            cols, results = self.db_connector.execute_query(query)
            if results:
                self.activity_combo.clear()
                for row in results:
                    # row[0]: Taetigkeiten_ID, row[1]: Name
                    self.activity_combo.addItem(row[1], row[0])
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Tätigkeiten: {e}")

    def add_employee(self):
        # Ausgewählte Abteilung und Tätigkeit aus den Comboboxes holen
        dept_index = self.department_combo.currentIndex()
        if dept_index < 0:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie eine Abteilung aus.")
            return
        department_id = self.department_combo.itemData(dept_index)

        act_index = self.activity_combo.currentIndex()
        if act_index < 0:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie eine Tätigkeit aus.")
            return
        activity_id = self.activity_combo.itemData(act_index)

        # Weitere Felder auslesen
        first_name = self.first_name_edit.text().strip()
        last_name = self.last_name_edit.text().strip()
        street = self.street_edit.text().strip()
        plz = self.plz_edit.text().strip()
        city = self.city_edit.text().strip()

        if not first_name or not last_name:
            QMessageBox.warning(self, "Fehler", "Vorname und Nachname sind Pflichtfelder.")
            return

        # Annahme: Mitarbeiter-Tabelle hat die Spalten:
        # Abt_NR, Name (Nachname), Vorname, Strasse, PLZ, Ort, Taetigkeiten_ID
        query = """
        INSERT INTO Mitarbeiter (Abt_NR, Name, Vorname, Strasse, PLZ, Ort, Taetigkeiten_ID)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        try:
            cursor = self.db_connector.conn.cursor()
            cursor.execute(query, department_id, last_name, first_name, street, plz, city, activity_id)
            self.db_connector.conn.commit()
            QMessageBox.information(self, "Erfolg", "Mitarbeiter erfolgreich hinzugefügt.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Hinzufügen des Mitarbeiters: {e}")
