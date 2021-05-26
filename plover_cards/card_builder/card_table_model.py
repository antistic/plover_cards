from PyQt5 import QtCore

COLUMNS = [
    {
        "name": "Count",
        "value": lambda card: card.frequency,
        "sort_key": lambda card: card.frequency,
    },
    {
        "name": "Count\n(shorter)",
        "value": lambda card: card.frequency_shorter,
        "sort_key": lambda card: card.frequency_shorter,
    },
    {
        "name": "Last Used",
        "value": lambda card: QtCore.QDateTime.fromSecsSinceEpoch(
            int(card.last_updated)
        )
        if card.last_updated
        else "",
        "sort_key": lambda card: card.last_updated if card.last_updated else 0,
    },
    {
        "name": "Translation",
        "value": lambda card: card.translation,
        "sort_key": lambda card: card.translation.lower(),
    },
    {
        "name": "Strokes",
        "value": lambda card: "(ignored)" if card.ignored else card.chosen_strokes,
        "sort_key": lambda card: card.chosen_strokes if card.chosen_strokes else "",
    },
    {
        "name": "Similar\nIgnored",
        "value": lambda card: ", ".join(card.similar_ignored),
        "sort_key": lambda card: card.similar_ignored if card.similar_ignored else [],
    },
]


class CardTableModel(QtCore.QAbstractTableModel):
    # pylint: disable=no-self-use
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards = None

    def set_cards_(self, cards):
        self.cards = cards
        self.sort(0, QtCore.Qt.DescendingOrder)

    def refresh_(self, card_index):
        self.dataChanged.emit(
            self.index(card_index, 0),
            self.index(card_index, self.columnCount()),
        )

    def rowCount(self, _parent=None):  # pylint: disable=invalid-name
        return len(self.cards)

    def columnCount(self, _parent=None):  # pylint: disable=invalid-name
        return len(COLUMNS)

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        card = self.cards[index.row()]

        return COLUMNS[index.column()]["value"](card)

    def headerData(self, column, orientation, role):  # pylint: disable=invalid-name
        if role != QtCore.Qt.DisplayRole or orientation != QtCore.Qt.Horizontal:
            return QtCore.QVariant()

        return COLUMNS[column]["name"]

    def sort(self, column, order=QtCore.Qt.AscendingOrder):
        self.cards.sort(
            key=COLUMNS[column]["sort_key"], reverse=order == QtCore.Qt.DescendingOrder
        )
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount(), self.columnCount()),
        )
