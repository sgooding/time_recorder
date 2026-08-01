import sys
import csv
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox, QTableWidgetItem
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, Qt
from time_recorder.ui_time_recorder import Ui_MainWindow
from datetime import datetime, UTC
from PySide6.QtWidgets import QHeaderView

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.tableWidget.setColumnCount(3)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setHorizontalHeaderLabels(["start", "stop", "description"])
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.verticalHeader().setVisible(False)
        # self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tableWidget.itemChanged.connect(self.on_item_change)

        self.currentTime.setText("Current Time: {}".format(datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")))
        self.menu_File.triggered.connect(self.handle_file_menu)
        self.menu_File.addAction(self.action_Save)
        self.menu_File.addAction(self.action_Load)
        self.menu_File.addAction(self.actionE_xit)

        # Access widgets directly via their objectName set in Designer
        self.startButton.clicked.connect(self.handle_click)
        self.stopButton.clicked.connect(self.handle_stop_click)
        self.update_timer = QTimer()
        self.update_timer.setInterval(100)
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start()

        self.data = {"start": [], "stop": [], "description": []}

    def handle_file_menu(self, action):
        if action == self.action_Save:
            self.save_file_callback()
        elif action == self.action_Load:
            self.load_file_callback()
        elif action == self.actionE_xit:
            QApplication.quit()

    def update(self):
        self.currentTime.setText("Current Time: {}".format(datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")))

    def on_item_change(self, item):
        row = item.row()
        col = item.column()

        if col == 2:  # Description column
            if row >= len(self.data["description"]):
                print(f"Extending description list to accommodate row {row}")
                self.data["description"].append(item.text())
            else:
                self.data["description"][row] = item.text()

        for row in range(self.tableWidget.rowCount()):
            start_time = self.data["start"][row] if row < len(self.data["start"]) else None
            stop_time = self.data["stop"][row] if row < len(self.data["stop"]) else None
            description = self.data["description"][row] if row < len(self.data["description"]) else ""
            print(f"Row {row}: Start: {start_time}, Stop: {stop_time}, Description: {description}")

    def handle_click(self):
        now_utc = datetime.now(UTC)
        self.tableWidget.setRowCount(self.tableWidget.rowCount() + 1)
        item = QTableWidgetItem("{}".format(now_utc.strftime("%Y-%m-%d %H:%M:%S")))
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tableWidget.setItem(self.tableWidget.rowCount() - 1, 0,item)
        self.data["start"].append(int(now_utc.timestamp()*1e9))  # Store as nanoseconds since epoch

    def handle_stop_click(self):
        now_utc = datetime.now(UTC)
        item = QTableWidgetItem("{}".format(now_utc.strftime("%Y-%m-%d %H:%M:%S")))
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tableWidget.setItem(self.tableWidget.rowCount() - 1, 1, item)
        self.data["stop"].append(int(now_utc.timestamp()*1e9))  # Store as nanoseconds since epoch

    def save_file_callback(self):
        """Callback to open a Save Dialog and write table data to disk."""
        # 1. Open the native Save File window interface
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Table Data",                 # Dialog Title text
            "exported_data.csv",               # Default suggested filename
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)" # File type options
        )

        # 2. Exit early if user cancels or closes the window without choosing a path
        if not file_path:
            return

        try:
            # 3. Open file descriptor and serialize QTableWidget grid strings
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Fetch column titles dynamically from horizontal headers
                headers = [self.tableWidget.horizontalHeaderItem(c).text() 
                           for c in range(self.tableWidget.columnCount())]
                writer.writerow(headers)

                # Iterate through grid rows to pull out text values
                for r in range(self.tableWidget.rowCount()):
                    row_items = []
                    for c in range(self.tableWidget.columnCount()):
                        item = self.tableWidget.item(r, c)
                        item_text = item.text() if item else ""
                        if( c < 2 ):
                            # convert time columns back to nanoseconds since epoch for storage
                            if item_text:
                                dt = datetime.strptime(item_text, "%Y-%m-%d %H:%M:%S")
                                item_text = str(int(dt.replace(tzinfo=UTC).timestamp() * 1e9))
                            
                        # Fallback to an empty string if a coordinate contains no cell object
                        row_items.append(item_text)

                    writer.writerow(row_items)

            # 4. Notify user of a successful operational write
            QMessageBox.information(self, "Success", "File exported successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save file to disk:\n{str(e)}")

    def load_file_callback(self):
        """Callback to handle file selection and loading data into the table."""
        # Open file dialog browser filtering strictly for CSV files
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Data File", 
            "", 
            "CSV Files (*.csv);;All Files (*)"
        )

        # Exit early if user cancels the file dialog picker
        if not file_path:
            return

        try:
            with open(file_path, newline='', encoding='utf-8') as file:
                reader = list(csv.reader(file))
                
                if not reader:
                    raise ValueError("The selected CSV file is empty.")

                # Extract the first row as columns headers
                headers = reader[0]
                data_rows = reader[1:]

                # Temporarily block signals to avoid triggering 'itemChanged' during load
                self.tableWidget.blockSignals(True)

                # Reset structural grid size to match the CSV dimensions
                self.tableWidget.setColumnCount(len(headers))
                self.tableWidget.setRowCount(len(data_rows))
                self.tableWidget.setHorizontalHeaderLabels(headers)

                # Inject matrix data
                for row_idx, row_data in enumerate(data_rows):
                    for col_idx, cell_value in enumerate(row_data):
                        # Convert time columns from nanoseconds since epoch to formatted string
                        if col_idx < 2 and cell_value:  # Assuming first two columns are time
                            try:
                                nanoseconds = int(cell_value)
                                dt = datetime.fromtimestamp(nanoseconds / 1e9, tz=UTC)
                                cell_value = dt.strftime("%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                # If conversion fails, keep the original value
                                pass
                        self.tableWidget.setItem(row_idx, col_idx, QTableWidgetItem(cell_value))

                # Re-enable table modification signals
                self.tableWidget.blockSignals(False)
                
        except Exception as e:
            QMessageBox.critical(self, "Loading Error", f"Could not parse file:\n{str(e)}")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
