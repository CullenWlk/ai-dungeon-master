import sys
import json
import re
from pathlib import Path

from PySide6.QtGui import QTextCursor, QPixmap
from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QDialog, QFormLayout, QCheckBox
from app.character.rules import SKILL_ABILITIES, calculate_skills
from PySide6.QtWidgets import QMessageBox
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
    QFrame,
    QGridLayout,
    QScrollArea,
    QSizePolicy,
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

class CharacterSetupDialog(QDialog):
    def __init__(self, font_family, font_size):
        super().__init__()

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.setWindowTitle("Character Setup")
        self.resize(800, 800)
        self.setMinimumSize(800, 600)

        self.use_default = False

        text_backer_slice = 7
        button_backer_slice = 10

        self.setStyleSheet(f"""
        QDialog {{
            background-color: rgb(255, 215, 168);
        }}

        QLabel {{
            font-family: "{font_family}";
            font-size: {font_size}px;
            color: black;
        }}

        QCheckBox {{
            font-family: "{font_family}";
            font-size: {font_size}px;
            color: black;
        }}
        """)

        def style_line_edit(field):
            field.setStyleSheet(f"""
            QLineEdit {{
                border-style: solid;
                border-width: {text_backer_slice}px;
                border-image: url("app/assets/UI_TravelBook_Frame04a_scaled.png") {text_backer_slice} {text_backer_slice} {text_backer_slice} {text_backer_slice} stretch stretch;
                font-family: "{font_family}";
                font-size: {font_size}px;
                color: black;
                padding: 4px;
            }}
            """)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Your name (first and last)")

        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Your age (in years)")

        self.race_input = QLineEdit()
        self.race_input.setPlaceholderText("Your race (human, elf, etc...)")

        self.sex_input = QLineEdit()
        self.sex_input.setPlaceholderText("Your sex (male, female)")

        self.class_input = QLineEdit()
        self.class_input.setPlaceholderText("Your class (fighter, wizard, etc...)")

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Your description (appearance, personality, etc...)")
        self.description_input.setStyleSheet(f"""
        QTextEdit {{
            border-style: solid;
            border-width: {text_backer_slice}px;
            border-image: url("app/assets/UI_TravelBook_Frame04a_scaled.png") {text_backer_slice} {text_backer_slice} {text_backer_slice} {text_backer_slice} stretch stretch;
            font-family: "{font_family}";
            font-size: {font_size}px;
            color: black;
            padding: 6px;
        }}
        """)

        self.level_input = QLineEdit()
        self.level_input.setPlaceholderText("Level")

        self.hp_input = QLineEdit()
        self.hp_input.setPlaceholderText("Health")

        self.ac_input = QLineEdit()
        self.ac_input.setPlaceholderText("Armor Class")

        self.prof_bonus_input = QLineEdit()
        self.prof_bonus_input.setPlaceholderText("Proficiency Bonus")

        self.str_input = QLineEdit()
        self.str_input.setPlaceholderText("Strength")

        self.dex_input = QLineEdit()
        self.dex_input.setPlaceholderText("Dexterity")

        self.con_input = QLineEdit()
        self.con_input.setPlaceholderText("Constitution")

        self.int_input = QLineEdit()
        self.int_input.setPlaceholderText("Intelligence")

        self.wis_input = QLineEdit()
        self.wis_input.setPlaceholderText("Wisdom")

        self.cha_input = QLineEdit()
        self.cha_input.setPlaceholderText("Charisma")

        for field in [
            self.name_input, self.age_input, self.race_input, self.sex_input,
            self.class_input, self.level_input, self.hp_input,
            self.ac_input, self.prof_bonus_input,
            self.str_input, self.dex_input, self.con_input,
            self.int_input, self.wis_input, self.cha_input
        ]:
            style_line_edit(field)

        self.skill_checks = {}

        self.default_button = QPushButton("Use Default Character")
        self.create_button = QPushButton("Create Custom Character")

        button_style = f"""
        QPushButton {{
            border-style: solid;
            border-width: {button_backer_slice}px;
            border-image: url("app/assets/UI_TravelBook_Frame04a_scaled.png") {button_backer_slice} {button_backer_slice} {button_backer_slice} {button_backer_slice} stretch stretch;
            font-family: "{font_family}";
            font-size: {font_size}px;
            color: black;
            font-weight: bold;
            padding: 2px;
        }}
        QPushButton:hover {{
            background-color: rgba(250, 230, 190, 210);
        }}
        QPushButton:pressed {{
            background-color: rgba(210, 185, 145, 220);
        }}
        """

        self.default_button.setStyleSheet(button_style)
        self.create_button.setStyleSheet(button_style)

        form_widget = QWidget()
        form_widget.setStyleSheet("background: transparent;")
        form_layout = QFormLayout(form_widget)

        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Age:", self.age_input)
        form_layout.addRow("Race:", self.race_input)
        form_layout.addRow("Sex:", self.sex_input)
        form_layout.addRow("Class:", self.class_input)
        form_layout.addRow("Description:", self.description_input)

        form_layout.addRow("Level:", self.level_input)
        form_layout.addRow("HP:", self.hp_input)
        form_layout.addRow("Armor Class:", self.ac_input)
        form_layout.addRow("Proficiency Bonus:", self.prof_bonus_input)

        form_layout.addRow("Strength:", self.str_input)
        form_layout.addRow("Dexterity:", self.dex_input)
        form_layout.addRow("Constitution:", self.con_input)
        form_layout.addRow("Intelligence:", self.int_input)
        form_layout.addRow("Wisdom:", self.wis_input)
        form_layout.addRow("Charisma:", self.cha_input)

        form_layout.addRow(QLabel("Skill Proficiencies:"))

        for skill in SKILL_ABILITIES:
            checkbox = QCheckBox(skill.replace("_", " ").title())
            self.skill_checks[skill] = checkbox
            form_layout.addRow(checkbox)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(form_widget)
        scroll_area.setStyleSheet("""
        QScrollArea {
            background: transparent;
            border: none;
        }

        QScrollArea > QWidget > QWidget {
            background: transparent;
        }

        QScrollBar:vertical {
            background: transparent;
            width: 5px;
        }

        QScrollBar::handle:vertical {
            background: rgb(229, 182, 127);
            min-height: 20px;
            border-radius: 2px;
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }

        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: transparent;
        }
        """)

        button_row = QHBoxLayout()
        button_row.addWidget(self.default_button)
        button_row.addWidget(self.create_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        main_layout.addLayout(button_row)

        self.setLayout(main_layout)

        self.default_button.clicked.connect(self.choose_default)
        self.create_button.clicked.connect(self.validate_and_accept)

    def choose_default(self):
        self.use_default = True
        self.accept()

    def get_character_data(self):
        if self.use_default:
            return None

        proficiency_bonus = int(self.prof_bonus_input.text())

        abilities = {
            "strength": int(self.str_input.text()),
            "dexterity": int(self.dex_input.text()),
            "constitution": int(self.con_input.text()),
            "intelligence": int(self.int_input.text()),
            "wisdom": int(self.wis_input.text()),
            "charisma": int(self.cha_input.text()),
        }

        proficient_skills = [
            skill for skill, checkbox in self.skill_checks.items()
            if checkbox.isChecked()
        ]

        skills = calculate_skills(
            abilities=abilities,
            proficient_skills=proficient_skills,
            proficiency_bonus=proficiency_bonus
        )

        return {
            "name": self.name_input.text().strip(),
            "age": self.age_input.text().strip(),
            "race": self.race_input.text().strip(),
            "sex": self.sex_input.text().strip(),
            "class": self.class_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
            "level": int(self.level_input.text()),
            "hp": {
                "current": int(self.hp_input.text()),
                "max": int(self.hp_input.text())
            },
            "armor_class": int(self.ac_input.text()),
            "proficiency_bonus": proficiency_bonus,
            "abilities": abilities,
            "skills": skills,
            "inventory": {}
        }

    def validate_and_accept(self):
        required_line_edits = [
            ("Name", self.name_input),
            ("Age", self.age_input),
            ("Race", self.race_input),
            ("Sex", self.sex_input),
            ("Class", self.class_input),
            ("Level", self.level_input),
            ("HP", self.hp_input),
            ("Armor Class", self.ac_input),
            ("Proficiency Bonus", self.prof_bonus_input),
            ("Strength", self.str_input),
            ("Dexterity", self.dex_input),
            ("Constitution", self.con_input),
            ("Intelligence", self.int_input),
            ("Wisdom", self.wis_input),
            ("Charisma", self.cha_input),
        ]

        for label, field in required_line_edits:
            if not field.text().strip():
                QMessageBox.warning(self, "Missing Field", f"{label} cannot be empty.")
                return

        if not self.description_input.toPlainText().strip():
            QMessageBox.warning(self, "Missing Field", "Description cannot be empty.")
            return

        numeric_fields = [
            ("Age", self.age_input),
            ("Level", self.level_input),
            ("HP", self.hp_input),
            ("Armor Class", self.ac_input),
            ("Proficiency Bonus", self.prof_bonus_input),
            ("Strength", self.str_input),
            ("Dexterity", self.dex_input),
            ("Constitution", self.con_input),
            ("Intelligence", self.int_input),
            ("Wisdom", self.wis_input),
            ("Charisma", self.cha_input),
        ]

        for label, field in numeric_fields:
            try:
                int(field.text().strip())
            except ValueError:
                QMessageBox.warning(self, "Invalid Field", f"{label} must be a whole number.")
                return

        self.accept()

    def closeEvent(self, event):
        self.reject()
        event.accept()


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Dungeon Master")
        self.resize(1400, 800)
        self.setMinimumSize(1400, 800)

        font_id = QFontDatabase.addApplicationFont("app/assets/fonts/alagard.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        font_size = 15

        self.run_character_setup(font_family, font_size)

        fancy_frame_source = Path("app/assets/UI_TravelBook_Slot04a.png")
        fancy_frame_scaled = Path("app/assets/UI_TravelBook_Slot04a_scaled.png")

        if not fancy_frame_scaled.exists():
            make_scaled_ui_image(fancy_frame_source, fancy_frame_scaled, 4)

        text_backer_slice = 7
        button_backer_slice = 10

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(f"""
        QTextEdit {{
            font-family: "{font_family}";
            font-size: {font_size}px;
            color: black;
            border: none;
        }}

        QScrollBar:vertical {{
            background: transparent;
            width: 5px;
            margin: 0px;
        }}

        QScrollBar::handle:vertical {{
            background: rgb(229, 182, 127);
            min-height: 20px;
            border-radius: 2px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: rgb(200, 160, 110);
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
        """)

        character_sheet = self.load_character_sheet()
        self.character_panel = self.build_character_panel(character_sheet, font_family, font_size)

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
        right_page_layout.addWidget(self.character_panel)

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

    def run_character_setup(self, font_family, font_size):
        dialog = CharacterSetupDialog(font_family, font_size)
        result = dialog.exec()

        if not result:
            QApplication.quit()
            sys.exit(0)

        current_sheet_path = Path("app/data/current_character_sheet.json")
        current_context_path = Path("app/data/current_session_context.json")
        default_sheet_path = Path("app/data/character_sheet.json")
        default_context_path = Path("app/data/session_context.json")

        character_data = dialog.get_character_data()

        if character_data is None:
            if current_sheet_path.exists():
                current_sheet_path.unlink()

            with open(default_sheet_path, "r", encoding="utf-8") as f:
                default_char = json.load(f)

            with open(default_context_path, "r", encoding="utf-8") as f:
                context_data = json.load(f)

            template = context_data.get("character", "")

            character_text = (
                template
                .replace("{{name}}", default_char.get("name", "Unknown"))
                .replace("{{age}}", str(default_char.get("age", "Unknown")))
                .replace("{{race}}", default_char.get("race", "Unknown"))
                .replace("{{sex}}", default_char.get("sex", "Unknown"))
                .replace("{{class}}", default_char.get("class", "Unknown"))
                .replace("{{description}}", default_char.get("description", "Unknown"))
            )

            context_data["character"] = character_text

            with open(current_context_path, "w", encoding="utf-8") as f:
                json.dump(context_data, f, indent=2)

            return

        with open(current_sheet_path, "w", encoding="utf-8") as file:
            json.dump(character_data, file, indent=2)

        default_context_path = Path("app/data/session_context.json")

        with open(default_context_path, "r", encoding="utf-8") as file:
            context_data = json.load(file)

        character_template = context_data.get("character", "")

        character_text = (
            character_template
            .replace("{{name}}", character_data["name"])
            .replace("{{age}}", str(character_data["age"]))
            .replace("{{race}}", character_data["race"])
            .replace("{{sex}}", character_data["sex"])
            .replace("{{class}}", character_data["class"])
            .replace("{{description}}", character_data["description"])
        )

        context_data["character"] = character_text

        with open(current_context_path, "w", encoding="utf-8") as file:
            json.dump(context_data, file, indent=2)

    def make_value_field(self, value, font_family, font_size):
        field = QLineEdit(str(value))
        field.setAlignment(Qt.AlignmentFlag.AlignCenter)
        field.setStyleSheet(f"""
        QLineEdit {{
            font-family: "{font_family}";
            font-size: {font_size}px;
            color: black;
            background: transparent;
            border: none;
        }}
        """)
        return field

    def make_basic_stat_box(self, label_text, value, font_family, font_size):
        box = QFrame()
        text_backer_slice = 10
        box.setStyleSheet(f"""
        QFrame {{
            background: transparent;
            border-style: solid;
            border-width: {text_backer_slice}px;
            border-image: url("app/assets/UI_TravelBook_Frame04a_scaled.png") {text_backer_slice} {text_backer_slice} {text_backer_slice} {text_backer_slice} stretch stretch;
        }}
        QLabel {{
            color: black;
            border: none;
        }}
        """)

        layout = QVBoxLayout(box)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        label = QLabel(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"""
        QLabel {{
            font-family: "{font_family}";
            font-size: {font_size}px;
            font-weight: bold;
        }}
        """)

        field = self.make_value_field(value, font_family, font_size)

        layout.addWidget(label)
        layout.addWidget(field)

        return box

    def make_skill_box(self, ability_name, ability_value, skill_list, font_family, font_size):
        box = QFrame()
        box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        fancy_frame_slice = 20
        box.setStyleSheet(f"""
        QFrame {{
            background: transparent;
            border-style: solid;
            border-width: {fancy_frame_slice}px;
            border-image: url("app/assets/UI_TravelBook_Slot04a_scaled.png") {fancy_frame_slice} {fancy_frame_slice} {fancy_frame_slice} {fancy_frame_slice} stretch stretch;
        }}
        QLabel {{
            color: black;
            border: none;
        }}
        """)

        layout = QVBoxLayout(box)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        top_row = QHBoxLayout()

        ability_label = QLabel(ability_name)
        ability_label.setStyleSheet(f"""
        QLabel {{
            font-family: "{font_family}";
            font-size: {font_size}px;
            font-weight: bold;
        }}
        """)

        ability_field = self.make_value_field(ability_value, font_family, font_size)
        ability_field.setMaximumWidth(45)

        top_row.addWidget(ability_label)
        top_row.addStretch()
        top_row.addWidget(ability_field)

        layout.addLayout(top_row)

        for skill_name, skill_value in skill_list:
            row = QHBoxLayout()

            skill_label = QLabel(skill_name)
            skill_label.setStyleSheet(f"""
            QLabel {{
                font-family: "{font_family}";
                font-size: {font_size - 1}px;
            }}
            """)

            skill_field = self.make_value_field(skill_value, font_family, font_size - 1)
            skill_field.setMaximumWidth(40)

            row.addWidget(skill_label)
            row.addStretch()
            row.addWidget(skill_field)

            layout.addLayout(row)

        return box

    def build_character_panel(self, sheet, font_family, font_size):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
        QScrollArea {
            background: transparent;
            border: none;
        }

        QScrollArea > QWidget > QWidget {
            background: transparent;
        }

        QScrollBar:vertical {
            background: transparent;
            width: 5px;
            margin: 0px 0px 0px 5px;
        }

        QScrollBar::handle:vertical {
            background: rgb(229, 182, 127);
            min-height: 20px;
            border-radius: 2px;
        }

        QScrollBar::handle:vertical:hover {
            background: rgb(200, 160, 110);
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }

        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: transparent;
        }
        """)

        panel = QWidget()
        panel.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        name = QLabel(sheet.get("name", ""))
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fancy_frame_slice = 20
        name.setStyleSheet(f"""
        QLabel {{
            font-family: "{font_family}";
            font-size: {font_size + 8}px;
            font-weight: bold;
            color: black;
            border-style: solid;
            border-width: {fancy_frame_slice}px;
            border-image: url("app/assets/UI_TravelBook_Slot04a_scaled.png") {fancy_frame_slice} {fancy_frame_slice} {fancy_frame_slice} {fancy_frame_slice} stretch stretch;
        }}
        """)
        layout.addWidget(name)

        hp = sheet.get("hp", {})

        basic_grid = QGridLayout()
        basic_grid.setSpacing(6)

        basic_stats = [
            ("Class", sheet.get("class", "")),
            ("Level", sheet.get("level", "")),
            ("HP", f"{hp.get('current', '')}/{hp.get('max', '')}"),
            ("AC", sheet.get("armor_class", "")),
            ("Prof", sheet.get("proficiency_bonus", "")),
        ]

        for index, (label, value) in enumerate(basic_stats):
            basic_grid.addWidget(
                self.make_basic_stat_box(label, value, font_family, font_size),
                0,
                index
            )

        layout.addLayout(basic_grid)

        abilities = sheet.get("abilities", {})
        skills = sheet.get("skills", {})

        skill_groups = [
            ("Strength", abilities.get("strength", ""), [
                ("Athletics", skills.get("athletics", "")),
            ]),
            ("Dexterity", abilities.get("dexterity", ""), [
                ("Acrobatics", skills.get("acrobatics", "")),
                ("Sleight Of Hand", skills.get("sleight_of_hand", "")),
                ("Stealth", skills.get("stealth", "")),
            ]),
            ("Constitution", abilities.get("constitution", ""), []),
            ("Intelligence", abilities.get("intelligence", ""), [
                ("Arcana", skills.get("arcana", "")),
                ("History", skills.get("history", "")),
                ("Investigation", skills.get("investigation", "")),
                ("Nature", skills.get("nature", "")),
                ("Religion", skills.get("religion", "")),
            ]),
            ("Wisdom", abilities.get("wisdom", ""), [
                ("Animal Handling", skills.get("animal_handling", "")),
                ("Insight", skills.get("insight", "")),
                ("Medicine", skills.get("medicine", "")),
                ("Perception", skills.get("perception", "")),
                ("Survival", skills.get("survival", "")),
            ]),
            ("Charisma", abilities.get("charisma", ""), [
                ("Deception", skills.get("deception", "")),
                ("Intimidation", skills.get("intimidation", "")),
                ("Performance", skills.get("performance", "")),
                ("Persuasion", skills.get("persuasion", "")),
            ]),
        ]

        skill_grid = QGridLayout()
        skill_grid.setSpacing(6)
        skill_grid.setAlignment(Qt.AlignmentFlag.AlignTop)

        for index, group in enumerate(skill_groups):
            row = index // 2
            col = index % 2
            skill_grid.addWidget(
                self.make_skill_box(*group, font_family, font_size),
                row,
                col
            )

        layout.addLayout(skill_grid)

        inventory_title = QLabel("Inventory")
        inventory_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inventory_title.setStyleSheet(f"""
        QLabel {{
            font-family: "{font_family}";
            font-size: {font_size + 2}px;
            font-weight: bold;
            color: black;
            border-style: solid;
            border-width: {fancy_frame_slice}px;
            border-image: url("app/assets/UI_TravelBook_Slot04a_scaled.png") {fancy_frame_slice} {fancy_frame_slice} {fancy_frame_slice} {fancy_frame_slice} stretch stretch;
        }}
        """)
        layout.addWidget(inventory_title)

        inventory_box = QTextEdit()
        inventory_box.setPlainText("\n".join(sheet.get("inventory", [])))
        inventory_box.setMaximumHeight(90)
        text_backer_slice = 7
        inventory_box.setStyleSheet(f"""
        QTextEdit {{
            font-family: "{font_family}";
            font-size: {font_size}px;
            color: black;
            background: transparent;
            border-style: solid;
            border-width: {text_backer_slice}px;
            border-image: url("app/assets/UI_TravelBook_Frame04a_scaled.png") {text_backer_slice} {text_backer_slice} {text_backer_slice} {text_backer_slice} stretch stretch;
        }}

        QScrollBar:vertical {{
            background: transparent;
            width: 5px;
            margin: 0px;
        }}

        QScrollBar::handle:vertical {{
            background: rgb(229, 182, 127);
            min-height: 20px;
            border-radius: 2px;
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
        """)
        layout.addWidget(inventory_box)

        scroll.setWidget(panel)
        return scroll

    def on_started(self):
        self.append_text("[System] Chat process started.\n")

    def on_finished(self):
        self.append_text("\n[System] Chat process ended.\n")
        self.send_button.setEnabled(False)
        self.input_line.setEnabled(False)
        self.roll_button.setEnabled(False)
        self.cleanup_session_files()

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

        text = re.sub(
            r'\[(.*?)\]',
            r'<span style="color: #4aa3ff;">[\1]</span>',
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
        session_path = Path("app/data/current_character_sheet.json")
        default_path = Path("app/data/character_sheet.json")

        path = session_path if session_path.exists() else default_path

        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    
    def cleanup_session_files(self):
        temp_files = [
            Path("app/data/current_character_sheet.json"),
            Path("app/data/current_session_context.json"),
        ]

        for path in temp_files:
            if path.exists():
                path.unlink()

    def closeEvent(self, event):
        self.cleanup_session_files()
        event.accept()

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
    
    def closeEvent(self, event):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.write(("quit\n").encode("utf-8"))
            self.process.waitForFinished(2000)

        self.cleanup_session_files()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())