from PyQt5 import QtWidgets


def setup_checkbox_section(checkbox, section):
    def action():
        if checkbox.isChecked():
            for item in section:
                item.setEnabled(True)
        else:
            for item in section:
                item.setEnabled(False)

    action()
    checkbox.stateChanged.connect(action)


def setup_browse(parent, button, line_edit, title, location, extensions):
    def action():
        filename = QtWidgets.QFileDialog.getOpenFileName(
            parent, title, location, f"{extensions};;All Files (*)"
        )[0]
        line_edit.setText(filename)

    button.clicked.connect(action)


def on_checkbox(checkbox, on_checked, on_unchecked):
    def action():
        if checkbox.isChecked():
            on_checked()
        else:
            on_unchecked()

    action()
    checkbox.stateChanged.connect(action)


def on_combobox(combobox, on_new_text, on_clear):
    def action(new_text):
        if new_text == "":
            on_clear()
        else:
            on_new_text(new_text)

    action(combobox.currentText())
    combobox.currentTextChanged.connect(action)


def combobox_set_items(combobox, new_items, default):
    combobox.clear()
    combobox.insertItems(0, new_items)

    index = combobox.findText(default)
    if index > -1:
        combobox.setCurrentIndex(index)
