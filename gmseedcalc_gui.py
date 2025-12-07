"""Simple PyQt5 UI for gmseedcalc seed/key operations."""

from __future__ import annotations

import sys
from typing import Dict, Tuple

from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QWidget,
)
from PyQt5.QtCore import Qt

from calc_logic import WORD, get_key, table_gmlan, table_others, table_class2

# Map human-friendly names to the backing opcode tables.
TABLES: Dict[str, Tuple[int, ...]] = {
    "GMLAN": table_gmlan,
    "Other": table_others,
    "Class2": table_class2,
}


class SeedKeyCalculator(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GM 2 byte Seed/Key Calculator")
        self.setMinimumSize(540, 400)

        self.seed_input = QLineEdit()
        self.seed_input.setPlaceholderText("e.g. 0102")
        self.seed_input.setMaxLength(4)
        self.seed_input.textChanged.connect(self._normalize_seed_text)

        self.algo_input = QLineEdit()
        self.algo_input.setPlaceholderText("e.g. 238")
        self.algo_input.setMaxLength(4)
        self.algo_input.setFixedWidth(80)

        self.brute_force_checkbox = QCheckBox("Brute force all")
        self.brute_force_checkbox.stateChanged.connect(self._toggle_brute_force)

        self.table_select = QComboBox()
        self.table_select.addItems(TABLES.keys())

        self.calculate_button = QPushButton("Calculate")
        self.calculate_button.clicked.connect(self.calculate)

        self.key_output = QLineEdit()
        self.key_output.setReadOnly(True)
        self.key_output.setPlaceholderText("0x0000")

        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_key)

        self.brute_results = QPlainTextEdit()
        self.brute_results.setReadOnly(True)
        self.brute_results.setPlaceholderText("Brute-force results will appear here when enabled.")

        self._build_layout()

    def _build_layout(self) -> None:
        layout = QGridLayout()

        layout.addWidget(QLabel("Seed (hex)"), 0, 0)
        layout.addWidget(self.seed_input, 0, 1)

        algo_row = QHBoxLayout()
        algo_row.addWidget(self.algo_input)
        algo_row.addWidget(self.brute_force_checkbox)
        algo_row.addStretch()

        layout.addWidget(QLabel("Algorithm"), 1, 0)
        layout.addLayout(algo_row, 1, 1)

        layout.addWidget(QLabel("Table"), 2, 0)
        layout.addWidget(self.table_select, 2, 1)

        layout.addWidget(self.calculate_button, 3, 0, 1, 2)

        key_row = QHBoxLayout()
        key_row.addWidget(self.key_output)
        key_row.addWidget(self.copy_button)

        layout.addWidget(QLabel("Key"), 4, 0)
        layout.addLayout(key_row, 4, 1)

        layout.addWidget(QLabel("Brute-force output"), 5, 0)
        layout.addWidget(self.brute_results, 5, 1)

        self.setLayout(layout)

    def _normalize_seed_text(self, value: str) -> None:
        self.seed_input.blockSignals(True)
        self.seed_input.setText(value.upper())
        self.seed_input.blockSignals(False)

    def _toggle_brute_force(self, state: int) -> None:
        brute_enabled = state == Qt.Checked
        self.algo_input.setDisabled(brute_enabled)
        if not brute_enabled:
            self.brute_results.clear()

    def _current_table(self) -> Tuple[int, ...]:
        return TABLES[self.table_select.currentText()]

    def calculate(self) -> None:
        seed_text = self.seed_input.text().strip()
        if not seed_text:
            self._show_error("Please enter a seed in hexadecimal format.")
            return

        try:
            seed_val = int(seed_text, 16)
        except ValueError:
            self._show_error("Seed must be a hexadecimal value (e.g. 0A1B).")
            return

        table = self._current_table()

        if self.brute_force_checkbox.isChecked():
            self._run_brute_force(seed_val, table)
            return

        algo_text = self.algo_input.text().strip()
        if not algo_text:
            self._show_error("Please enter an algorithm number or enable brute force.")
            return

        try:
            algo = int(algo_text)
        except ValueError:
            self._show_error("Algorithm must be a decimal number.")
            return

        if algo < 0:
            self._show_error("Algorithm number must be non-negative.")
            return

        if algo * 13 + 12 >= len(table):
            self._show_error("Algorithm index is out of range for the selected table.")
            return

        key = get_key(WORD(seed_val), algo, table)
        self.key_output.setText(f"0x{key.value:04X}")
        self.brute_results.clear()

    def _run_brute_force(self, seed: int, table: Tuple[int, ...]) -> None:
        limit = len(table) // 13
        lines = []
        for algo in range(1, limit):
            key = get_key(WORD(seed), algo, table)
            lines.append(f"Algo {algo:03d}: 0x{key.value:04X}")

        result_text = "\n".join(lines) if lines else "No algorithms available for this table."
        self.brute_results.setPlainText(result_text)
        self.key_output.clear()

    def copy_key(self) -> None:
        key_text = self.key_output.text().strip()
        if not key_text:
            self._show_error("No key to copy. Calculate a key first or select one from the list.")
            return
        QApplication.clipboard().setText(key_text)

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Input error", message)


def main() -> None:
    app = QApplication(sys.argv)
    window = SeedKeyCalculator()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
