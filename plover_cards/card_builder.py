import os
from pathlib import Path

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import uic

from plover.oslayer.config import CONFIG_DIR as PLOVER_CONFIG_DIR
from plover.gui_qt.tool import Tool

from .anki_utils import ANKI_BASE_DIR, get_models
from .cards import Cards
from .config import read_config, save_config
from .card_builder_ui import Ui_CardBuilder


class CardTableModel(QtCore.QAbstractTableModel):
    def set_cards_(self, cards):
        self.cards = cards

    def refresh_(self, card_index):
        self.dataChanged.emit(self.index(card_index, 0), self.index(card_index, 1))

    def rowCount(self, parent):
        return len(self.cards)

    def columnCount(self, parent):
        return 3

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        card = self.cards[index.row()]

        if index.column() == 0:
            return card.translation
        if index.column() == 1:
            if card.ignored:
                return "(ignored)"
            return card.chosen_strokes
        if index.column() == 2:
            return ", ".join(card.similar_ignored)
        return "??"

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole or orientation != QtCore.Qt.Horizontal:
            return QtCore.QVariant()

        if section == 0:
            return "Translation"
        if section == 1:
            return "Stroke"
        if section == 2:
            return "Similar Ignored"

        return "??"


class CardBuilder(Tool, Ui_CardBuilder):
    TITLE = "Card Builder"
    ICON = ":/plover_cards/cards.svg"
    ROLE = "cardbuilder"

    def __init__(self, engine):
        super(CardBuilder, self).__init__(engine)
        self.setupUi(self)

        self.config = read_config()

        self.setup_disable_start_if_invalid()
        self.clear_output.setChecked(
            self.config["options"]["clear_output_on_start"] == "True"
        )
        self.setup_file_inputs()
        self.setup_buttons()
        self.setup_suggestions()

        self.pages.setCurrentIndex(0)
        self.start.setFocus()
        self.show()

    def setup_file_inputs(self):
        self.anki_path.textChanged.connect(self.update_card_types)

        self.anki_path.setText(self.config["paths"]["anki_collection"])
        self.anki_browse.clicked.connect(
            self.on_browse(
                self.anki_path,
                "Open Anki collection",
                ANKI_BASE_DIR,
                "Anki Collections (*.anki2)",
            )
        )

        self.clippy_path.setText(self.config["paths"]["clippy"])
        self.clippy_browse.clicked.connect(
            self.on_browse(
                self.clippy_path,
                "Open clippy file",
                PLOVER_CONFIG_DIR,
                "Text Files (*.txt)",
            )
        )

        self.strokes_path.setText(self.config["paths"]["strokes_log"])
        self.strokes_browse.clicked.connect(
            self.on_browse(
                self.strokes_path,
                "Open strokes log",
                PLOVER_CONFIG_DIR,
                "Log Files (*.log)",
            )
        )

        self.ignore_path.setText(self.config["paths"]["ignore"])
        self.ignore_browse.clicked.connect(
            self.on_browse(
                self.ignore_path,
                "Open ignore file",
                PLOVER_CONFIG_DIR,
                "Text Files (*.txt)",
            )
        )

        self.output_path.setText(self.config["paths"]["output"])
        self.output_browse.clicked.connect(
            self.on_browse(
                self.output_path,
                "Open output file",
                PLOVER_CONFIG_DIR,
                "Text Files (*.txt)",
            )
        )

    def update_card_types(self, anki_path):
        self.card_type.clear()
        for i, model in enumerate(get_models(anki_path)):
            self.card_type.addItem(model.name, str(model.id))
            if model.name == self.config["anki"]["card_type"]:
                self.card_type.setCurrentIndex(i)

    def on_browse(self, label, title, location, extensions):
        def func():
            filename = QtWidgets.QFileDialog.getOpenFileName(
                self, title, location, f"{extensions};;All Files (*)"
            )[0]
            label.setText(filename)

        return func

    def setup_disable_start_if_invalid(self):
        text_inputs = [
            self.anki_path,
            self.clippy_path,
            self.strokes_path,
            self.ignore_path,
            self.output_path,
        ]

        def on_text_changed(str):
            if str == "":
                self.start.setEnabled(False)
                return

            if all([input.text() != "" for input in text_inputs]):
                self.start.setEnabled(True)
            else:
                self.start.setEnabled(False)

        for input in text_inputs:
            input.textChanged.connect(on_text_changed)

    def setup_buttons(self):
        self.start.clicked.connect(self.on_start)
        self.prev_card.clicked.connect(self.on_prev_card)
        self.next_card.clicked.connect(self.on_next_card)
        self.ignore_card.clicked.connect(self.on_ignore_card)
        self.clear_card.clicked.connect(self.on_clear_card)
        self.finish.clicked.connect(self.on_finish)
        self.save.clicked.connect(self.on_save)

    def setup_suggestions(self):
        self.suggestions_model = QtGui.QStandardItemModel(self.suggestions)
        self.suggestions.setModel(self.suggestions_model)
        self.suggestions.clicked.connect(self.on_suggestion_click)

    def setup_cards(self):
        self.cards = Cards(
            self.anki_path.text(),
            self.card_type.currentData(),
            self.clippy_path.text(),
            self.strokes_path.text(),
            self.ignore_path.text(),
            self.output_path.text(),
        )
        self.current_card_index = 0
        self.card_view_model = CardTableModel(self.card_view)
        self.card_view_model.set_cards_(self.cards)
        self.card_view.setModel(self.card_view_model)
        self.card_view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.card_view.clicked.connect(self.on_card_click)

    def on_start(self):
        self.config["paths"] = {
            "anki_collection": self.anki_path.text(),
            "clippy": self.clippy_path.text(),
            "strokes_log": self.strokes_path.text(),
            "ignore": self.ignore_path.text(),
            "output": self.output_path.text(),
        }
        self.config["anki"]["card_type"] = self.card_type.currentText()
        self.config["options"]["clear_output_on_start"] = str(
            self.clear_output.isChecked()
        )
        save_config(self.config)

        self.setup_cards()
        if self.config["options"]["clear_output_on_start"]:
            Path(self.output_path.text()).write_text("")

        self.pages.setCurrentIndex(1)
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

        self.suggestions.show()

    def on_prev_card(self):
        self.current_card_index -= 1
        self.show_card()

    def on_next_card(self):
        self.current_card_index += 1
        self.show_card()

    def on_clear_card(self):
        self.suggestions.clearSelection()
        self.cards.choose_strokes(self.current_card_index, None)
        self.card_view_model.refresh_(self.current_card_index)

    def on_ignore_card(self):
        self.cards.ignore(self.current_card_index)
        self.card_view_model.refresh_(self.current_card_index)

    def on_suggestion_click(self, list_item):
        self.cards.choose_strokes(self.current_card_index, list_item.data())
        self.card_view_model.refresh_(self.current_card_index)

    def on_card_click(self, list_item):
        self.current_card_index = list_item.row()
        self.show_card()

    def on_finish(self):
        self.clear_strokes.setChecked(self.config["options"]["clear_strokes"] == "True")
        self.clear_clippy.setChecked(self.config["options"]["clear_clippy"] == "True")
        self.pages.setCurrentIndex(2)
        self.save.setFocus()

    def on_save(self):
        self.cards.save()

        self.config["options"]["clear_strokes"] = str(self.clear_strokes.isChecked())
        self.config["options"]["clear_clippy"] = str(self.clear_clippy.isChecked())
        save_config(self.config)

        if self.clear_strokes.isChecked():
            self.cards.clear_strokes()
        if self.clear_clippy.isChecked():
            self.cards.clear_clippy()
        self.close()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    dialog = CardBuilder({})
    app.exec_()