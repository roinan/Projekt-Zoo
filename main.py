import sys
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLineEdit,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QWidget,
    QMainWindow,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QMessageBox,
)

from helpers import login

from qt_material import apply_stylesheet


class MainWindow(QMainWindow):
    def __init__(self, db_connector):
        super().__init__()
        self.setWindowTitle("DB Abfragen App")
        self.db_connector = db_connector
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Hinweistext
        self.info_label = QLabel("Geben Sie Ihre SQL-Abfrage ein:")
        layout.addWidget(self.info_label)

        # Eingabefeld für SQL-Abfrage
        self.query_text = QTextEdit()
        layout.addWidget(self.query_text)

        # Button zum Ausführen der Abfrage
        self.execute_button = QPushButton("Abfrage ausführen")
        self.execute_button.clicked.connect(self.run_query)
        layout.addWidget(self.execute_button)

        # Tabelle zur Darstellung der Ergebnisse
        self.result_table = QTableWidget()
        layout.addWidget(self.result_table)

        central_widget.setLayout(layout)

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
