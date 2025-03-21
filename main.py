import sys
from PySide6 import QtCore
from PySide6.QtWidgets import (
    QApplication, QDialog, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QWidget, QMainWindow, QTableWidget, QTableWidgetItem,
    QTextEdit, QMessageBox, QListWidget, QSplitter
)

from helpers import login

from qt_material import apply_stylesheet


class MainWindow(QMainWindow):
    def __init__(self, db_connector):
        super().__init__()
        self.setWindowTitle("DB Abfragen App")
        self.db_connector = db_connector
        self.setup_ui()
        self.load_views()
        self.load_user_roles()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        # Header: Anzeige der Benutzerrolle oben rechts
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        self.role_label = QLabel("Rolle(n): Unbekannt")
        header_layout.addWidget(self.role_label)
        main_layout.addLayout(header_layout)

        # Splitter: Links Views-Liste, rechts Abfrage- und Ergebnisbereich
        splitter = QSplitter(QtCore.Qt.Horizontal)

        # Links: Liste der verfügbaren Views
        self.views_list = QListWidget()
        # Hier wird nun auf itemClicked reagiert, sodass die View direkt ausgeführt wird
        self.views_list.itemClicked.connect(self.view_selected)
        splitter.addWidget(self.views_list)

        # Rechts: Abfrageeingabe und Ergebnisanzeige
        query_widget = QWidget()
        query_layout = QVBoxLayout()

        self.info_label = QLabel("Geben Sie Ihre SQL-Abfrage ein:")
        query_layout.addWidget(self.info_label)
        self.query_text = QTextEdit()
        query_layout.addWidget(self.query_text)

        self.execute_button = QPushButton("Abfrage ausführen")
        self.execute_button.clicked.connect(self.run_query)
        query_layout.addWidget(self.execute_button)

        self.result_table = QTableWidget()
        query_layout.addWidget(self.result_table)

        query_widget.setLayout(query_layout)
        splitter.addWidget(query_widget)
        splitter.setStretchFactor(1, 3)  # Mehr Platz für den Abfragebereich

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)

    def view_selected(self, item):
        view_name = item.text()
        # Automatische Abfrageausführung der angeklickten View
        query = f"SELECT * FROM {view_name};"
        self.query_text.setText(query)
        self.run_query()

    def run_query(self):
        query = self.query_text.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie eine SQL-Abfrage ein.")
            return
        try:
            columns, results = self.db_connector.execute_query(query)
            if columns and results is not None:
                self.populate_table(columns, results)
            else:
                QMessageBox.information(self, "Erfolg", "Abfrage erfolgreich ausgeführt. Keine Ergebnisse zum Anzeigen.")
                self.result_table.clear()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def populate_table(self, columns, data):
        self.result_table.clear()
        self.result_table.setColumnCount(len(columns))
        self.result_table.setRowCount(len(data))
        self.result_table.setHorizontalHeaderLabels(columns)
        for row_idx, row in enumerate(data):
            for col_idx, cell in enumerate(row):
                self.result_table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell)))
        self.result_table.resizeColumnsToContents()

    def load_views(self):
        query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS;"
        try:
            columns, results = self.db_connector.execute_query(query)
            if columns and results is not None:
                self.views_list.clear()
                for row in results:
                    self.views_list.addItem(row[0])
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Views: {e}")

    def load_user_roles(self):
        query = """
        SELECT dp.name AS DatabaseRole
        FROM sys.database_role_members drm
        JOIN sys.database_principals dp ON drm.role_principal_id = dp.principal_id
        JOIN sys.database_principals up ON drm.member_principal_id = up.principal_id
        WHERE up.name = USER_NAME();
        """
        try:
            columns, results = self.db_connector.execute_query(query)
            if results and len(results) > 0:
                roles = [row[0] for row in results]
                self.role_label.setText("Rolle(n): " + ", ".join(roles))
            else:
                self.role_label.setText("Rolle(n): Keine")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Rollen: {e}")


def main():
    app = QApplication(sys.argv)
    login_dialog = login.LoginDialog()
    apply_stylesheet(login_dialog, 'light_blue.xml')
    if login_dialog.exec() == QDialog.Accepted:
        db_connector = login_dialog.db_connector
        main_window = MainWindow(db_connector)
        apply_stylesheet(main_window, 'light_blue.xml')
        main_window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
