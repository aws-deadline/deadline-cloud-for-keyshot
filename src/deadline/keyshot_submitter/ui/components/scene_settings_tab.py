# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
import os
from pathlib import Path

from PySide2.QtCore import QSize, Qt  # type: ignore
from PySide2.QtWidgets import (  # type: ignore
    QComboBox,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)

from keyshot_submitter.data_classes import KeyShotOutputFormat  #  type: ignore


"""
UI widgets for the Scene Settings tab.
"""

# Mappings needed to determine the file extension and property KeyShot will
# use to set the render output path and format
_KEYSHOT_OUTPUT_FORMATS: dict[str, KeyShotOutputFormat] = {
    "PNG": KeyShotOutputFormat("PNG", "png", "RENDER_OUTPUT_PNG"),
    "JPEG": KeyShotOutputFormat("JPEG", "jpg", "RENDER_OUTPUT_JPEG"),
    "EXR": KeyShotOutputFormat("EXR", "exr", "RENDER_OUTPUT_EXR"),
    "TIFF": KeyShotOutputFormat("TIFF", "tif", "RENDER_OUTPUT_TIFF8"),
    "TIFF 32-bit": KeyShotOutputFormat("TIFF 32-bit", "tif", "RENDER_OUTPUT_TIFF32"),
    "PSD": KeyShotOutputFormat("PSD", "psd", "RENDER_OUTPUT_PSD8"),
    "PSD 16-bit": KeyShotOutputFormat("PSD 16-bit", "psd", "RENDER_OUTPUT_PSD16"),
    "PSD 32-bit": KeyShotOutputFormat("PSD 32-bit", "psd", "RENDER_OUTPUT_PSD32"),
}


class FileSearchLineEdit(QWidget):
    """
    Widget used to contain a line edit and a button which opens a file search box.
    """

    def __init__(self, file_format=None, directory_only=False, parent=None):
        super().__init__(parent=parent)

        if directory_only and file_format is not None:
            raise ValueError("")

        self.file_format = file_format
        self.directory_only = directory_only

        lyt = QHBoxLayout(self)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.setMargin(0)

        self.edit = QLineEdit(self)
        self.btn = QPushButton("...", parent=self)
        self.btn.setMaximumSize(QSize(100, 40))
        self.btn.clicked.connect(self.get_file)

        lyt.addWidget(self.edit)
        lyt.addWidget(self.btn)

    def get_file(self):
        """
        Open a file picker to allow users to choose a file.
        """
        if self.directory_only:
            new_txt = QFileDialog.getExistingDirectory(
                self,
                "Open Directory",
                self.edit.text(),
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
            )
        else:
            new_txt = QFileDialog.getOpenFileName(self, "Select File", self.edit.text())

        if new_txt:
            self.edit.setText(new_txt)

    def setText(self, txt: str) -> None:  # pylint: disable=invalid-name
        """
        Sets the text of the internal line edit
        """
        self.edit.setText(str(txt))

    def text(self) -> str:
        """
        Retrieves the text from the internal line edit.
        """
        return self.edit.text()


class SceneSettingsWidget(QWidget):
    """
    Widget containing all top level scene settings.
    """

    def __init__(self, initial_settings, parent=None):
        super().__init__(parent=parent)

        self.developer_options = (
            os.environ.get("DEADLINE_ENABLE_DEVELOPER_OPTIONS", "").upper() == "TRUE"
        )
        self._build_ui(initial_settings)
        self._configure_settings(initial_settings)

    def _build_ui(self, settings):
        lyt = QGridLayout(self)

        lyt.addWidget(QLabel("Output Name"), 1, 0)
        self.output_name_text = QLineEdit(self)
        lyt.addWidget(self.output_name_text, 1, 1)
        self.output_name_text.textChanged.connect(self.output_file_path_changed)

        lyt.addWidget(QLabel("Output Folder"), 2, 0)
        self.output_folder_text = FileSearchLineEdit(directory_only=True)
        lyt.addWidget(self.output_folder_text, 2, 1)
        self.output_folder_text.edit.textChanged.connect(self.output_file_path_changed)

        lyt.addWidget(QLabel("Output Format"), 3, 0)
        self.output_format = QComboBox(self)
        self.output_format.addItems(_KEYSHOT_OUTPUT_FORMATS.keys())
        lyt.addWidget(self.output_format, 3, 1)
        self.output_format.currentTextChanged.connect(self.output_file_path_changed)

        self._filename_display = QLabel("")
        filename_font = self._filename_display.font()
        filename_font.setItalic(True)
        filename_font.setPointSize(filename_font.pointSize() - 2)
        self._filename_display.setFont(filename_font)
        lyt.addWidget(self._filename_display, 4, 0, 1, 2)

        self.frame_override_chck = QCheckBox("Override Frame Range", self)
        self.frame_override_txt = QLineEdit(self)
        lyt.addWidget(self.frame_override_chck, 5, 0)
        lyt.addWidget(self.frame_override_txt, 5, 1)
        self.frame_override_chck.stateChanged.connect(self.activate_frame_override_changed)

        self.include_alpha_chk = QCheckBox("Include Alpha", self)
        lyt.addWidget(self.include_alpha_chk, 6, 0, 1, 2)

        self.render_layers_chk = QCheckBox("Render Layers", self)
        lyt.addWidget(self.render_layers_chk, 7, 0, 1, 2)

        if self.developer_options:
            self.include_adaptor_wheels = QCheckBox(
                "Developer Option: Include Adaptor Wheels", self
            )
            lyt.addWidget(self.include_adaptor_wheels, 8, 0, 1, 2)

        lyt.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding), 12, 0)

    def _configure_settings(self, settings):
        self.output_name_text.setText(settings.output_name)
        self.output_folder_text.setText(settings.output_folder)
        output_format_display_name = _KEYSHOT_OUTPUT_FORMATS["PNG"].display_name  # Default to PNG
        for display_name_key, output_format in _KEYSHOT_OUTPUT_FORMATS.items():
            if output_format.keyshot_property_name == settings.output_format:
                output_format_display_name = display_name_key
                break
        self.output_format.setCurrentText(output_format_display_name)
        self.frame_override_chck.setChecked(settings.override_frame_range)
        self.frame_override_txt.setEnabled(settings.override_frame_range)
        self.frame_override_txt.setText(settings.frame_list)

        if self.developer_options:
            self.include_adaptor_wheels.setChecked(settings.include_adaptor_wheels)

    def update_settings(self, settings):
        """
        Update a scene settings object with the latest values.
        """
        settings.output_name = self.output_name_text.text()
        settings.output_folder = self.output_folder_text.text()
        settings.output_format = _KEYSHOT_OUTPUT_FORMATS[
            self.output_format.currentText()
        ].keyshot_property_name
        settings.output_file_path = self._filename_display.text()

        settings.override_frame_range = self.frame_override_chck.isChecked()
        settings.frame_list = self.frame_override_txt.text()

        if self.developer_options:
            settings.include_adaptor_wheels = self.include_adaptor_wheels.isChecked()
        else:
            settings.include_adaptor_wheels = False

    def activate_frame_override_changed(self, state):
        """
        Set the activated/deactivated status of the Frame override text box
        """
        self.frame_override_txt.setEnabled(state == Qt.Checked)

    def output_file_path_changed(self):
        """
        Update the output file path display if any of the name, folder or
        extension are changed in the UI.
        """
        folder = self.output_folder_text.text()
        filename = self.output_name_text.text()
        frame_token = "%d"
        extension = _KEYSHOT_OUTPUT_FORMATS[self.output_format.currentText()].file_extension
        self._filename_display.setText(str(Path(f"{folder}/{filename}.{frame_token}.{extension}")))
