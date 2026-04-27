import sys
import json
import subprocess
import re
from pathlib import Path
from PySide6.QtGui import QTextCursor

from PySide6.QtCore import QProcess, Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QLabel,
)
from app.character import sheet


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Dungeon Master")
        self.resize(900, 700)

        self.output = QTextEdit()
        self.output.setReadOnly(True)

        self.sheet_view = QTextEdit()
        self.sheet_view.setReadOnly(True)
        self.sheet_view.setMaximumWidth(320)

        sheet = self.load_character_sheet()
        self.sheet_view.setPlainText(self.format_character_sheet(sheet))

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Type your action here...")

        self.send_button = QPushButton("Send")

        self.roll_button = QPushButton("Roll")
        self.roll_button.setVisible(False)

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.input_line)
        bottom_row.addWidget(self.send_button)
        bottom_row.addWidget(self.roll_button)

        middle_row = QHBoxLayout()
        middle_row.addWidget(self.output, 3)
        middle_row.addWidget(self.sheet_view, 1)

        layout = QVBoxLayout()
        layout.addLayout(middle_row)
        layout.addLayout(bottom_row)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.process = QProcess(self)
        self.process.setProgram(sys.executable)
        self.process.setArguments(["-m", "app.main"])
        self.process.setProcessChannelMode(QProcess.MergedChannels)

        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_output)
        self.process.started.connect(self.on_started)
        self.process.finished.connect(self.on_finished)

        self.send_button.clicked.connect(self.send_input)
        self.input_line.returnPressed.connect(self.send_input)
        self.roll_button.clicked.connect(self.send_roll)

        self.process.start()

    def on_started(self):
        self.append_text("[System] Chat process started.\n")

    def on_finished(self):
        self.append_text("\n[System] Chat process ended.\n")
        self.send_button.setEnabled(False)
        self.input_line.setEnabled(False)
        self.roll_button.setEnabled(False)

    def read_output(self):
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        if data:
            self.append_text(data)

            lowered = data.lower()
            if "make a" in lowered and "check" in lowered:
                self.roll_button.setVisible(True)

    def format_text(self, text):
        text = (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )

        text = re.sub(
            r'"(.*?)"',
            r'<span style="color: #4aa3ff;">"\1"</span>',
            text
        )

        text = text.replace("\n", "<br>")
        return text

    def append_text(self, text):
        self.output.moveCursor(QTextCursor.MoveOperation.End)
        self.output.insertHtml(self.format_text(text))
        self.output.moveCursor(QTextCursor.MoveOperation.End)

    def send_input(self):
        text = self.input_line.text().strip()
        if not text:
            return

        self.append_text(f"{text}\n")
        self.process.write((text + "\n").encode("utf-8"))
        self.input_line.clear()

    def send_roll(self):
        self.append_text("I roll\n")
        self.process.write(("I roll\n").encode("utf-8"))
        self.roll_button.setVisible(False)
    
    def load_character_sheet(self):
        path = Path("app/data/character_sheet.json")
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    
    def format_character_sheet(self, sheet):
        abilities = sheet.get("abilities", {})
        skills = sheet.get("skills", {})
        hp = sheet.get("hp", {})

        ability_lines = []
        for key, value in abilities.items():
            ability_lines.append(f"{key.capitalize()}: {value}")

        skill_lines = []
        for key, value in skills.items():
            skill_lines.append(f"{key.replace('_', ' ').title()}: {value}")

        inventory = sheet.get("inventory", [])
        inventory_lines = "\n".join(f"- {item}" for item in inventory)

        return (
            f"Name: {sheet.get('name', '')}\n"
            f"Class: {sheet.get('class', '')}\n"
            f"Level: {sheet.get('level', '')}\n"
            f"HP: {hp.get('current', '')}/{hp.get('max', '')}\n"
            f"AC: {sheet.get('armor_class', '')}\n"
            f"Proficiency Bonus: {sheet.get('proficiency_bonus', '')}\n\n"
            f"Abilities:\n" + "\n".join(ability_lines) + "\n\n"
            f"Skills:\n" + "\n".join(skill_lines) + "\n\n"
            f"Inventory:\n{inventory_lines}"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())