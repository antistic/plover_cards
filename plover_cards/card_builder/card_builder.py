from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui

from plover.oslayer.config import CONFIG_DIR as PLOVER_CONFIG_DIR
from plover.gui_qt.tool import Tool

from plover_cards import anki_utils
from plover_cards import config
from plover_cards.plover_hook.card_suggestions import CardSuggestions

from .cards import Cards
from .card_builder_ui import Ui_CardBuilder
from .card_table_model import COLUMNS, CardTableModel
from . import utils


class CardBuilder(Tool, Ui_CardBuilder):
    TITLE = "Card Builder"
    ICON = ":/plover_cards/cards.svg"
    ROLE = "cardbuilder"

    def __init__(self, engine):
        super().__init__(engine)
        self.engine = engine

        hook = self.engine._running_extensions.get("plover_cards_hook")
        if hook:
            self.card_suggestions = hook.card_suggestions
            self.card_suggestions.save()
        else:
            self.card_suggestions = CardSuggestions()

        self.setupUi(self)

        self.config = config.read()

        self.setup_settings()
        self.setup_buttons()
        self.setup_suggestions()
        self.custom_strokes.textChanged.connect(self.on_custom_stroke)

        self.current_card_index = 0
        self.cards = None
        self.card_view_model = None

        self.pages.setCurrentIndex(0)
        self.start.setFocus()
        self.show()

    def config_connect(self, widget, section, option, radio_value=None):
        if isinstance(widget, QtWidgets.QLineEdit):
            widget.setText(self.config.get(section, option))

            def update_config(new_text):
                self.config[section][option] = new_text

            widget.textChanged.connect(update_config)
        elif isinstance(widget, QtWidgets.QCheckBox):
            widget.setChecked(self.config.getboolean(section, option))

            def update_config():
                if widget.isChecked():
                    self.config[section][option] = "yes"
                else:
                    self.config[section][option] = "no"

            widget.stateChanged.connect(update_config)
        elif isinstance(widget, QtWidgets.QComboBox):
            widget.setCurrentText(self.config.get(section, option))

            def update_config(new_text):
                if new_text != "":
                    self.config[section][option] = new_text

            widget.currentTextChanged.connect(update_config)
        elif isinstance(widget, QtWidgets.QRadioButton):
            if self.config.get(section, option) == radio_value:
                widget.setChecked(True)
            else:
                widget.setChecked(False)

            def update_config():
                if widget.isChecked():
                    self.config[section][option] = radio_value

            widget.toggled.connect(update_config)
        else:
            raise Exception(f"unknown widget type for {widget}")

    def setup_settings(self):
        # connect to config
        self.config_connect(self.use_ignore, "compare_ignore", "enabled")
        self.config_connect(self.ignore_path, "compare_ignore", "file_path")

        self.config_connect(self.compare_to_anki, "compare_to_anki", "enabled")
        self.config_connect(self.anki_query, "compare_to_anki", "query")
        self.config_connect(self.anki_compare_field, "compare_to_anki", "compare_field")

        self.config_connect(self.output_to_csv, "output_csv", "enabled")
        self.config_connect(self.output_path, "output_csv", "file_path")
        self.config_connect(
            self.overwrite_output, "output_csv", "write_method", "Overwrite"
        )
        self.config_connect(self.append_output, "output_csv", "write_method", "Append")

        self.config_connect(self.add_to_anki, "add_to_anki", "enabled")
        self.config_connect(self.deck, "add_to_anki", "deck")
        self.config_connect(self.note_type, "add_to_anki", "note_type")
        self.config_connect(self.translation_field, "add_to_anki", "translation_field")
        self.config_connect(self.strokes_field, "add_to_anki", "strokes_field")
        self.config_connect(self.tags, "add_to_anki", "tags")

        # set up sections
        utils.setup_checkbox_section(
            self.use_ignore, [self.ignore_label, self.ignore_path, self.ignore_browse]
        )
        utils.setup_checkbox_section(
            self.compare_to_anki,
            [
                self.anki_query_label,
                self.anki_query,
                self.anki_compare_field_label,
                self.anki_compare_field,
            ],
        )
        utils.setup_checkbox_section(
            self.output_to_csv,
            [
                self.output_label,
                self.output_path,
                self.output_browse,
                self.write_method_label,
                self.overwrite_output,
                self.append_output,
            ],
        )
        utils.setup_checkbox_section(
            self.add_to_anki,
            [
                self.deck_label,
                self.deck,
                self.note_type_label,
                self.note_type,
                self.translation_field_label,
                self.translation_field,
                self.strokes_field_label,
                self.strokes_field,
                self.tags_label,
                self.tags,
            ],
        )

        # set up browse
        utils.setup_browse(
            self,
            self.ignore_browse,
            self.ignore_path,
            "Open ignore file",
            PLOVER_CONFIG_DIR,
            "Text Files (*.txt)",
        )
        utils.setup_browse(
            self,
            self.output_browse,
            self.output_path,
            "Open output file",
            PLOVER_CONFIG_DIR,
            "Text Files (*.txt);;CSV Files (*.csv)",
        )

        # request anki_connect permission
        try:
            result = anki_utils.invoke("requestPermission")
            if result["permission"] != "granted":
                raise Exception("Anki connect permisson denied")
        except Exception:
            self.compare_to_anki.setChecked(False)
            self.compare_to_anki.setEnabled(False)
            self.add_to_anki.setChecked(False)
            self.add_to_anki.setEnabled(False)

        # set up comboboxes
        utils.on_checkbox(
            self.compare_to_anki,
            lambda: utils.combobox_set_items(
                self.anki_compare_field,
                anki_utils.all_field_names(),
                self.config["compare_to_anki"]["compare_field"],
            ),
            self.deck.clear,
        )
        utils.on_checkbox(
            self.add_to_anki,
            lambda: utils.combobox_set_items(
                self.deck,
                anki_utils.invoke("deckNames"),
                self.config["add_to_anki"]["deck"],
            ),
            self.deck.clear,
        )
        utils.on_checkbox(
            self.add_to_anki,
            lambda: utils.combobox_set_items(
                self.note_type,
                anki_utils.invoke("modelNames"),
                self.config["add_to_anki"]["note_type"],
            ),
            self.note_type.clear,
        )
        utils.on_combobox(
            self.note_type,
            lambda new_text: utils.combobox_set_items(
                self.translation_field,
                anki_utils.invoke("modelFieldNames", modelName=new_text),
                self.config["add_to_anki"]["translation_field"],
            ),
            self.translation_field.clear,
        )
        utils.on_combobox(
            self.note_type,
            lambda new_text: utils.combobox_set_items(
                self.strokes_field,
                anki_utils.invoke("modelFieldNames", modelName=new_text),
                self.config["add_to_anki"]["strokes_field"],
            ),
            self.strokes_field.clear,
        )

    def setup_buttons(self):
        self.start.clicked.connect(self.on_start)
        self.prev_card.clicked.connect(self.on_prev_card)
        self.next_card.clicked.connect(self.on_next_card)
        self.ignore_card.clicked.connect(self.on_ignore_card)
        self.clear_card.clicked.connect(self.on_clear_card)
        self.finish.clicked.connect(self.on_finish)

    def setup_suggestions(self):
        self.suggestions_model = QtGui.QStandardItemModel(self.suggestions)
        self.suggestions.setModel(self.suggestions_model)
        self.suggestions.clicked.connect(self.on_suggestion_click)

    def setup_cards(self):
        self.cards = Cards(self.config, self.card_suggestions)

        self.card_view_model = CardTableModel(self.card_view)
        self.card_view_model.set_cards_(self.cards)
        self.card_view.setModel(self.card_view_model)
        header = self.card_view.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self.show_header_menu)
        self.card_view.clicked.connect(self.on_card_click)

        self.num_ignored.setText(f"{self.cards.num_ignored} ignored")

        if not self.config.getboolean("compare_ignore", "enabled"):
            self.ignore_card.hide()

            if not self.config.getboolean("compare_to_anki", "enabled"):
                index = next(
                    i
                    for i, col in enumerate(COLUMNS)
                    if col["name"] == "Similar\nIgnored"
                )
                header.hideSection(index)

    def show_header_menu(self, position):
        menu = QtWidgets.QMenu()
        header = self.card_view.horizontalHeader()
        for i, column in enumerate(COLUMNS):
            if column["name"] == "Translation" or column["name"] == "Strokes":
                continue
            action = menu.addAction(column["name"])
            action.setCheckable(True)
            action.setChecked(not header.isSectionHidden(i))

            def on_toggle(checked, i=i):
                if checked:
                    header.showSection(i)
                else:
                    header.hideSection(i)

            action.toggled.connect(on_toggle)

        menu.exec_(self.card_view.mapToGlobal(position))

    def on_start(self):
        config.save(self.config)

        self.setup_cards()

        self.pages.setCurrentIndex(1)
        if len(self.cards) > 0:
            self.show_card()

    def show_card(self):
        if self.current_card_index == 0:
            self.prev_card.setEnabled(False)
        else:
            self.prev_card.setEnabled(True)

        if self.current_card_index == len(self.cards) - 1:
            self.next_card.setEnabled(False)
            self.finish.setFocus()
        else:
            self.next_card.setEnabled(True)
            self.next_card.setFocus()

        self.progress.setText(
            f"Suggestion {self.current_card_index + 1} of {len(self.cards)}"
        )
        self.card_view.setCurrentIndex(
            self.card_view_model.index(self.current_card_index, 0)
        )

        card = self.cards[self.current_card_index]

        self.translation.setText(card.translation)

        self.suggestions_model.clear()
        self.custom_strokes.setText("")
        for suggestion in card.stroke_suggestions:
            item = QtGui.QStandardItem(suggestion)
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.suggestions_model.appendRow(item)
            if suggestion == card.chosen_strokes:
                self.suggestions.setCurrentIndex(
                    self.suggestions_model.indexFromItem(item)
                )

        if not card.ignored and card.chosen_strokes is None:
            index = self.suggestions_model.index(0, 0)
            self.suggestions.setCurrentIndex(index)
            self.on_suggestion_click(index)

        if (
            card.chosen_strokes is not None
            and self.suggestions.currentIndex().row() == -1
        ):
            self.custom_strokes.setText(card.chosen_strokes)

        self.suggestions.show()

    def on_prev_card(self):
        self.current_card_index -= 1
        self.show_card()

    def on_next_card(self):
        self.current_card_index += 1
        self.show_card()

    def on_clear_card(self):
        self.cards.choose_strokes(self.current_card_index, None)

        self.suggestions.clearSelection()
        self.custom_strokes.setText("")
        self.card_view_model.refresh_(self.current_card_index)

    def on_ignore_card(self):
        self.cards.ignore(self.current_card_index)

        self.suggestions.clearSelection()
        self.custom_strokes.setText("")
        self.card_view_model.refresh_(self.current_card_index)

    def on_suggestion_click(self, list_item):
        self.cards.choose_strokes(self.current_card_index, list_item.data())

        self.custom_strokes.setText("")
        self.card_view_model.refresh_(self.current_card_index)

    def on_custom_stroke(self, new_text):
        if new_text != "":
            self.cards.choose_strokes(self.current_card_index, new_text)
        else:
            self.cards.choose_strokes(self.current_card_index, None)

        self.suggestions.clearSelection()
        self.card_view_model.refresh_(self.current_card_index)

    def on_card_click(self, list_item):
        self.current_card_index = list_item.row()
        self.show_card()

    def on_finish(self):
        self.cards.save()
        self.close()

        message = []
        if self.config.getboolean("add_to_anki", "enabled"):
            message.append(f"{self.cards.num_added} note(s) added to anki")
        if self.config.getboolean("output_csv", "enabled"):
            message.append(
                f"{self.cards.num_saved} note(s) saved to {self.config['output_csv']['file_path']}"
            )
        if self.config.getboolean("compare_ignore", "enabled"):
            message.append(
                f"{len(self.cards.new_ignored)} entries added to ignore file"
            )

        if len(message) > 0:
            save_msg = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.NoIcon,
                "Finished",
                "\n".join(message),
                QtWidgets.QMessageBox.Ok,
            )
            save_msg.exec_()


if __name__ == "__main__":

    class EngineMock:
        def __init__(self):
            self._running_extensions = {}

    app = QtWidgets.QApplication([])
    dialog = CardBuilder(EngineMock())
    app.exec_()
