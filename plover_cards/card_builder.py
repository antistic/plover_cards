from pathlib import Path

from enum import IntEnum

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui

from plover.oslayer.config import CONFIG_DIR as PLOVER_CONFIG_DIR
from plover.gui_qt.tool import Tool

from .anki_utils import ANKI_BASE_DIR, get_models
from .cards import Cards
from .config import read_config, save_config
from .card_builder_ui import Ui_CardBuilder
from .card_suggestions import CardSuggestions


class CardTableColumn(IntEnum):
    FREQUENCY = 0
    TRANSLATION = 1
    STROKES = 2
    IGNORED = 3


class CardTableModel(QtCore.QAbstractTableModel):
    # pylint: disable=no-self-use
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards = None

    def set_cards_(self, cards):
        self.cards = cards
        self.sort(CardTableColumn.FREQUENCY, QtCore.Qt.DescendingOrder)

    def refresh_(self, card_index):
        self.dataChanged.emit(
            self.index(card_index, 0),
            self.index(card_index, self.columnCount()),
        )

    def rowCount(self, _parent=None):  # pylint: disable=invalid-name
        return len(self.cards)

    def columnCount(self, _parent=None):  # pylint: disable=invalid-name
        return 4

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        card = self.cards[index.row()]

        if index.column() == CardTableColumn.FREQUENCY:
            return card.frequency
        if index.column() == CardTableColumn.TRANSLATION:
            return card.translation
        if index.column() == CardTableColumn.STROKES:
            if card.ignored:
                return "(ignored)"
            return card.chosen_strokes
        if index.column() == CardTableColumn.IGNORED:
            return ", ".join(card.similar_ignored)
        return "??"

    def headerData(self, section, orientation, role):  # pylint: disable=invalid-name
        if role != QtCore.Qt.DisplayRole or orientation != QtCore.Qt.Horizontal:
            return QtCore.QVariant()

        if section == CardTableColumn.FREQUENCY:
            return "Count"
        if section == CardTableColumn.TRANSLATION:
            return "Translation"
        if section == CardTableColumn.STROKES:
            return "Stroke"
        if section == CardTableColumn.IGNORED:
            return "Similar\nIgnored"

        return "??"

    def sort(self, column, order=QtCore.Qt.AscendingOrder):
        def key(card):
            if column == CardTableColumn.FREQUENCY:
                return card.frequency
            if column == CardTableColumn.TRANSLATION:
                return card.translation.lower()
            if column == CardTableColumn.STROKES:
                if card.chosen_strokes is not None:
                    return card.chosen_strokes
            if column == CardTableColumn.IGNORED:
                if card.similar_ignored is not None:
                    return card.similar_ignored
            return ""

        self.cards.sort(key=key, reverse=order == QtCore.Qt.DescendingOrder)
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount(), self.columnCount()),
        )


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

        self.config = read_config()

        self.setup_disable_start_if_invalid()
        self.clear_output.setChecked(
            self.config["options"]["clear_output_on_start"] == "True"
        )
        self.setup_file_inputs()
        self.setup_buttons()
        self.setup_suggestions()
        self.custom_strokes.textChanged.connect(self.on_custom_stroke)

        self.current_card_index = 0
        self.cards = None
        self.card_view_model = None

        self.pages.setCurrentIndex(0)
        self.start.setFocus()
        self.show()

    def setup_file_inputs(self):
        self.anki_path.textChanged.connect(self.update_note_types)

        self.anki_path.setText(self.config["paths"]["anki_collection"])
        self.anki_browse.clicked.connect(
            self.on_browse(
                self.anki_path,
                "Open Anki collection",
                ANKI_BASE_DIR,
                "Anki Collections (*.anki2)",
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

    def update_note_types(self, anki_path):
        self.note_type.clear()
        for i, model in enumerate(get_models(anki_path)):
            self.note_type.addItem(model.name, str(model.id))
            if model.name == self.config["anki"]["note_type"]:
                self.note_type.setCurrentIndex(i)

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
            self.ignore_path,
            self.output_path,
        ]

        def on_text_changed(new_text):
            if new_text == "":
                self.start.setEnabled(False)
                return

            if (
                all((input.text() != "" for input in text_inputs))
                and self.note_type.currentText() != ""
            ):
                self.start.setEnabled(True)
            else:
                self.start.setEnabled(False)

        for text_input in text_inputs:
            text_input.textChanged.connect(on_text_changed)

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
        self.card_view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive
        )
        self.card_view.clicked.connect(self.on_card_click)

        self.num_ignored.setText(f"{self.cards.num_ignored} ignored")

    def on_start(self):
        # update config
        self.config["paths"] = {
            "anki_collection": self.anki_path.text(),
            "ignore": self.ignore_path.text(),
            "output": self.output_path.text(),
        }
        self.config["anki"]["note_type"] = self.note_type.currentText()
        self.config["options"]["clear_output_on_start"] = str(
            self.clear_output.isChecked()
        )
        save_config(self.config)

        # clear output
        if self.config["options"]["clear_output_on_start"] == "True":
            Path(self.output_path.text()).write_text("")

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
        (num_notes, num_ignored) = self.cards.save()
        save_config(self.config)
        self.close()

        save_msg = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.NoIcon,
            "Finished",
            (
                f"{num_notes} note(s) saved to {self.config['paths']['output']}\n"
                f"{num_ignored} word(s) added to the ignore file\n"
                "\nYou can now import into Anki"
            ),
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
