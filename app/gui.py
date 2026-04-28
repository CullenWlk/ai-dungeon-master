import sys
import json
import re
from pathlib import Path

from PySide6.QtGui import QTextCursor, QPixmap
from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
)

from app.character import sheet


def make_scaled_ui_image(source_path, output_path, scale):
    pixmap = QPixmap(str(source_path))
    scaled = pixmap.scaled(
        pixmap.width() * scale,
        pixmap.height() * scale,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.FastTransformation
    )
    scaled.save(str(output_path))


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Dungeon Master")
        self.resize(1100, 800)
        self.setMinimumSize(900, 700)

        self.output = QTextEdit()
        self.output.setReadOnly(True)

        self.sheet_view = QTextEdit()
        self.sheet_view.setReadOnly(True)

        font_id = QFontDatabase.addApplicationFont("app/assets/fonts/alagard.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        font_size = 15

        button_backer_source = Path("app/assets/UI_TravelBook_Bar02a.png")
        button_backer_scaled = Path("app/assets/UI_TravelBook_Bar02a_scaled.png")

        if not button_backer_scaled.exists():
            make_scaled_ui_image(button_backer_source, button_backer_scaled, 4)

        text_backer_slice = 20
        button_backer_slice = 10

        self.output.setStyleSheet(f"""
        QTextEdit {{
            font-family: "{font_family}";
            font-size: {font_size}px;
            color: black;
            border: none;
        }}
        """)

        self.sheet_view.setStyleSheet(f"""
        QTextEdit {{
            font-family: "{font_family}";
            font-size: {font_size}px;
            color: black;
            border: none;
        }}
        """)

        sheet = self.load_character_sheet()
        self.sheet_view.setPlainText(self.format_character_sheet(sheet))

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Type your action here...")
        self.input_line.setStyleSheet(f"""
        QLineEdit {{
            border-style: solid;
            border-width: {text_backer_slice}px;
            border-image: url("app/assets/UI_TravelBook_Frame04a_scaled.png") {text_backer_slice} {text_backer_slice} {text_backer_slice} {text_backer_slice} stretch stretch;
            font-family: "{font_family}";
            font-size: {font_size}px;
            color: black;
            border: none;
            padding: 6px;
        }}
        """)

        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet(f"""
        QPushButton {{
            border-style: solid;
            border-width: {button_backer_slice}px;
            border-image: url("app/assets/UI_TravelBook_Frame04a_scaled.png") {button_backer_slice} {button_backer_slice} {button_backer_slice} {button_backer_slice} stretch stretch;
            font-family: "{font_family}";
            font-size: {font_size}px;
            color: black;
            font-weight: bold;
            padding: 1px;
        }}
        """)

        self.roll_button = QPushButton("Roll")
        self.roll_button.setStyleSheet(f"""
        QPushButton {{
            border-style: solid;
            border-width: {button_backer_slice}px;
            border-image: url("app/assets/UI_TravelBook_Frame04a_scaled.png") {button_backer_slice} {button_backer_slice} {button_backer_slice} {button_backer_slice} stretch stretch;
            font-family: "{font_family}";
            font-size: {font_size}px;
            color: black;
            font-weight: bold;
            padding: 1px;
        }}
        QPushButton:hover {{
            background-color: rgba(250, 230, 190, 210);
        }}
        QPushButton:pressed {{
            background-color: rgba(210, 185, 145, 220);
        }}
        """)
        self.roll_button.setVisible(False)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.addWidget(self.input_line)
        bottom_row.addWidget(self.send_button)
        bottom_row.addWidget(self.roll_button)

        left_page = QWidget()
        left_page.setObjectName("leftPage")
        left_page.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        right_page = QWidget()
        right_page.setObjectName("rightPage")
        right_page.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        left_page_layout = QVBoxLayout(left_page)
        left_page_layout.setContentsMargins(55, 35, 45, 85)
        left_page_layout.setSpacing(10)
        left_page_layout.addWidget(self.output, 1)
        left_page_layout.addLayout(bottom_row)

        right_page_layout = QVBoxLayout(right_page)
        right_page_layout.setContentsMargins(45, 35, 55, 85)
        right_page_layout.setSpacing(10)
        right_page_layout.addWidget(self.sheet_view)

        page_row = QHBoxLayout()
        page_row.setSpacing(0)
        page_row.setContentsMargins(0, 0, 0, 0)
        page_row.addWidget(left_page)
        page_row.addWidget(right_page)

        pages_widget = QWidget()
        pages_widget.setLayout(page_row)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)
        layout.addWidget(pages_widget)

        container = QWidget()
        container.setObjectName("mainContainer")
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        container.setLayout(layout)

        cover_slice = 220
        page_slice = 220

        container.setStyleSheet(f"""
        #mainContainer {{
            border-style: solid;
            border-width: {cover_slice}px;
            border-image: url("app/assets/UI_TravelBook_BookCover01a_scaled.png") {cover_slice} {cover_slice} {cover_slice} {cover_slice} stretch stretch;
        }}
        """)

        left_page.setStyleSheet(f"""
        #leftPage {{
            border-style: solid;
            border-width: {page_slice}px;
            border-image: url("app/assets/UI_TravelBook_BookPageLeft01a_scaled.png") {page_slice} 180 350 {page_slice} stretch stretch;
        }}
        """)

        right_page.setStyleSheet(f"""
        #rightPage {{
            border-style: solid;
            border-width: {page_slice}px;
            border-image: url("app/assets/UI_TravelBook_BookPageRight01a_scaled.png") {page_slice} {page_slice} 350 195 stretch stretch;
        }}
        """)

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
            r'<span style="color: #c33b3e;">"\1"</span>',
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

        skill_groups = {
            "strength": ["athletics"],
            "dexterity": ["acrobatics", "sleight_of_hand", "stealth"],
            "constitution": [],
            "intelligence": ["arcana", "history", "investigation", "nature", "religion"],
            "wisdom": ["animal_handling", "insight", "medicine", "perception", "survival"],
            "charisma": ["deception", "intimidation", "performance", "persuasion"],
        }

        lines = []

        lines.append(f"Name: {sheet.get('name', '')}")
        lines.append(f"Class: {sheet.get('class', '')}")
        lines.append(f"Level: {sheet.get('level', '')}")
        lines.append(f"HP: {hp.get('current', '')}/{hp.get('max', '')}")
        lines.append(f"AC: {sheet.get('armor_class', '')}")
        lines.append(f"Proficiency Bonus: {sheet.get('proficiency_bonus', '')}")
        lines.append("")
        lines.append("Abilities and Skills:")

        for ability, grouped_skills in skill_groups.items():
            ability_name = ability.capitalize()
            ability_score = abilities.get(ability, "")

            lines.append("")
            lines.append(f"{ability_name}: {ability_score}")

            for skill in grouped_skills:
                skill_name = skill.replace("_", " ").title()
                skill_value = skills.get(skill, "")
                lines.append(f"    {skill_name}: {skill_value}")

        inventory = sheet.get("inventory", [])

        lines.append("")
        lines.append("Inventory:")

        for item in inventory:
            lines.append(f"    - {item}")

        return "\n".join(lines)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())