from datetime import datetime
import difflib
from pathlib import Path
import shutil

from PySide2 import QtCore, QtGui, QtWidgets

from diffsniff import etc
from diffsniff import utils


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Diff Sniff')

        self.main_widget = MainWidget(self)
        self.setCentralWidget(self.main_widget)
        self.create_menu()

    def create_menu(self):
        menu_bar = self.menuBar()
        menu_file = menu_bar.addMenu('&File')

        item_compare = QtWidgets.QAction(get_icon('glasses'), '&Compare', self)
        item_compare.triggered.connect(self.main_widget.compare)
        item_compare.setShortcut(QtGui.QKeySequence('Ctrl+C'))
        menu_file.addAction(item_compare)

        item_presets = QtWidgets.QAction(get_icon('presets'), '&Presets...',
                                         self)
        item_presets.triggered.connect(self.main_widget.open_presets)
        item_presets.setShortcut(QtGui.QKeySequence('Ctrl+P'))
        menu_file.addAction(item_presets)

        item_quit = QtWidgets.QAction(get_icon('quit'), '&Quit', self)
        item_quit.triggered.connect(self.close)
        item_quit.setShortcut(QtGui.QKeySequence('Ctrl+Q'))
        menu_file.addAction(item_quit)

    def run(self, app):
        self.show()
        app.exec_()


class MainWidget(QtWidgets.QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        browse_button_1 = QtWidgets.QPushButton('Browse...')
        browse_button_1.setFixedWidth(etc.TEXT_BUTTON_WIDTH)
        browse_button_1.clicked.connect(self.open_dir_1)
        self.dir_label_1 = QtWidgets.QLabel()
        self.default_fg_color = QtGui.QColor(self.dir_label_1.foregroundRole())
        dir_layout_1 = QtWidgets.QHBoxLayout()
        dir_layout_1.addWidget(browse_button_1)
        dir_layout_1.addWidget(self.dir_label_1)

        swap_button = QtWidgets.QPushButton(get_icon('swap'), '')
        swap_button.setFixedWidth(etc.ICON_BUTTON_WIDTH)
        swap_button.clicked.connect(self.swap_paths)

        browse_button_2 = QtWidgets.QPushButton('Browse...')
        browse_button_2.setFixedWidth(etc.TEXT_BUTTON_WIDTH)
        browse_button_2.clicked.connect(self.open_dir_2)
        self.dir_label_2 = QtWidgets.QLabel()
        dir_layout_2 = QtWidgets.QHBoxLayout()
        dir_layout_2.addWidget(browse_button_2)
        dir_layout_2.addWidget(self.dir_label_2)

        self.compare_button = QtWidgets.QPushButton(get_icon('glasses'),
                                                    'Compare')
        self.compare_button.setFixedWidth(etc.TEXT_AND_ICON_BUTTON_WIDTH)
        self.compare_button.setFixedHeight(50)
        self.compare_button.clicked.connect(self.compare)

        self.preset = 'default'
        self.paths_from_preset(self.preset)

        # todo: refactor to a single grid layout with set column widths
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(dir_layout_1)
        main_layout.addWidget(swap_button, alignment=QtCore.Qt.AlignCenter)
        main_layout.addLayout(dir_layout_2)
        main_layout.addWidget(self.compare_button,
                              alignment=QtCore.Qt.AlignCenter)
        self.setLayout(main_layout)

    def open_dir_1(self):
        path = self.get_dir_path(self.dir_path_1)

        if path:
            self.dir_path_1 = path
            self.refresh_display()

    def open_dir_2(self):
        path = self.get_dir_path(self.dir_path_2)

        if path:
            self.dir_path_2 = path
            self.refresh_display()

    def get_dir_path(self, default_path):
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(self, '',
                                                              str(default_path))
        if dir_path:
            return Path(dir_path)

    def open_presets(self):
        PresetsDialog(self)

    def paths_from_preset(self, preset_name: str):
        self.dir_path_1 = Path(etc.presets[preset_name].path_1)
        self.dir_path_2 = Path(etc.presets[preset_name].path_2)

        self.ignore_dirs = etc.presets[preset_name].ignore_dirs
        self.ignore_files = etc.presets[preset_name].ignore_files
        self.refresh_display()

    def swap_paths(self):
        self.dir_path_1, self.dir_path_2 = self.dir_path_2, self.dir_path_1
        self.refresh_display()

    def refresh_display(self):
        self.dir_label_1.setText(str(self.dir_path_1))
        if self.dir_path_1.exists():
            utils.set_fg_color(self.dir_label_1, self.default_fg_color)
            self.dir_label_1.setToolTip('')
        else:
            utils.set_fg_color(self.dir_label_1,
                               QtGui.QColor(*etc.LIGHT))
            self.dir_label_1.setToolTip('Directory does not exist')

        self.dir_label_2.setText(str(self.dir_path_2))
        if self.dir_path_2.exists():
            utils.set_fg_color(self.dir_label_2, self.default_fg_color)
            self.dir_label_2.setToolTip('')
        else:
            utils.set_fg_color(self.dir_label_2,
                               QtGui.QColor(*etc.LIGHT))
            self.dir_label_2.setToolTip('Directory does not exist')

        # update the state of the Compare button
        # (disabled if one or both paths do not exist)
        if self.dir_path_1.exists() and self.dir_path_2.exists():
            self.compare_button.setDisabled(False)
        else:
            self.compare_button.setDisabled(True)

    def compare(self):
        ResultDialog(self)


class FileItem(QtWidgets.QFrame):

    def __init__(self, parent, dir_path_1, dir_path_2, mtimes, item_name,
                 unique, left_to_right):
        super().__init__(parent)
        self.parent = parent
        self.left_abs_path = dir_path_1 / item_name
        self.right_abs_path = dir_path_2 / item_name

        if mtimes:
            left_mtime, right_mtime = mtimes
            self.left_time = datetime.fromtimestamp(left_mtime).isoformat(
                ' ', 'seconds')
            self.right_time = datetime.fromtimestamp(right_mtime).isoformat(
                ' ', 'seconds')

        left_label = QtWidgets.QLabel('' if unique and not left_to_right
                                      else item_name)
        right_label = QtWidgets.QLabel('' if unique and left_to_right
                                       else item_name)

        if unique:
            copy_button = QtWidgets.QPushButton(get_icon(
                'right' if left_to_right else 'left'), '')
            copy_button.setToolTip('Copy file')
            # Delete button
            second_button = QtWidgets.QPushButton(get_icon('trash'), '')
            second_button.setToolTip('Delete file')
            second_button.clicked.connect(self.delete_left if left_to_right
                                          else self.delete_right)
        else:
            copy_button = QtWidgets.QPushButton(get_icon(
                'overright' if left_to_right else 'overleft'), '')
            copy_button.setToolTip('Copy file (overwrite)')
            # Diff button
            second_button = QtWidgets.QPushButton(get_icon('diff'), '')
            second_button.setToolTip('Show unified diff')
            second_button.clicked.connect(self.diff_left_vs_right
                                          if left_to_right
                                          else self.diff_right_vs_left)
            utils.set_fg_color(right_label if left_to_right else left_label,
                               QtGui.QColor(*etc.LIGHT))
            left_label.setToolTip(self.left_time)
            right_label.setToolTip(self.right_time)

        copy_button.clicked.connect(self.copy_right if left_to_right
                                    else self.copy_left)
        copy_button.setFixedWidth(etc.ICON_BUTTON_WIDTH)
        second_button.setFixedWidth(etc.ICON_BUTTON_WIDTH)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(left_label)
        layout.addWidget(copy_button)
        layout.addWidget(second_button)
        layout.addWidget(right_label)
        self.setLayout(layout)

    def copy_right(self):
        destination_dir = self.right_abs_path.parent
        if not destination_dir.exists():
            destination_dir.mkdir(parents=True)

        shutil.copy2(str(self.left_abs_path), str(destination_dir))
        self.setDisabled(True)

    def copy_left(self):
        destination_dir = self.left_abs_path.parent
        if not destination_dir.exists():
            destination_dir.mkdir(parents=True)

        shutil.copy2(str(self.right_abs_path), str(destination_dir))
        self.setDisabled(True)

    def diff_right_vs_left(self):
        DiffDialog(self.left_abs_path, self.right_abs_path,
                   self.left_time, self.right_time)

    def diff_left_vs_right(self):
        DiffDialog(self.right_abs_path, self.left_abs_path,
                   self.right_time, self.left_time)

    def delete_left(self):
        self.left_abs_path.unlink()
        self.setDisabled(True)

    def delete_right(self):
        self.right_abs_path.unlink()
        self.setDisabled(True)


class ResultDialog(QtWidgets.QDialog):

    def __init__(self, parent):
        super().__init__()
        self.setWindowTitle('Comparison results')

        self.dir_path_1 = parent.dir_path_1
        self.dir_path_2 = parent.dir_path_2
        self.ignore_dirs = parent.ignore_dirs
        self.ignore_files = parent.ignore_files

        self.layout = QtWidgets.QVBoxLayout()

        item_counter = None
        for item_counter, file_item in enumerate(self.file_items()):
            self.layout.addWidget(file_item)
        if item_counter is None:
            self.layout.addWidget(QtWidgets.QLabel('No difference.'))

        close_button = QtWidgets.QPushButton('Close')
        close_button.setFixedWidth(etc.TEXT_BUTTON_WIDTH)
        close_button.clicked.connect(self.close)

        self.layout.addWidget(close_button, alignment=QtCore.Qt.AlignCenter)
        self.setLayout(self.layout)
        self.exec_()

    def file_items(self):
        names = utils.compare_one_way(self.dir_path_1, self.dir_path_2,
                                      self.ignore_dirs, self.ignore_files)

        names.update(utils.compare_one_way(self.dir_path_2, self.dir_path_1,
                                           self.ignore_dirs, self.ignore_files,
                                           skip=names, reverse=True))

        for item_name, item_info in names.items():
            if item_info.equal:
                continue
            yield FileItem(self, self.dir_path_1, self.dir_path_2,
                           item_info.mtimes, item_name,
                           item_info.unique, item_info.left_to_right)


class PresetsDialog(QtWidgets.QDialog):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Choose a preset')

        self.preset_list = QtWidgets.QListWidget()

        # todo: control `show_all` setting with a checkbutton labelled
        #  "Show all presets"
        show_all = False

        for preset_name in sorted(etc.presets):
            item = QtWidgets.QListWidgetItem(preset_name)
            if (show_all or Path(etc.presets[preset_name].path_1).exists()
                    and Path(etc.presets[preset_name].path_2).exists()):
                self.preset_list.addItem(item)
                if preset_name == self.parent.preset:
                    item.setSelected(True)

        ok_button = QtWidgets.QPushButton('OK')
        ok_button.setFixedWidth(etc.TEXT_BUTTON_WIDTH)
        ok_button.clicked.connect(self.confirm)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.preset_list)
        layout.addWidget(ok_button, alignment=QtCore.Qt.AlignCenter)
        self.setLayout(layout)
        self.exec_()

    def confirm(self):
        try:
            self.parent.preset = self.preset_list.selectedItems()[0].text()
        except IndexError:
            # do nothing if no selection
            pass
        else:
            self.parent.paths_from_preset(self.parent.preset)
            self.close()


class DiffDialog(QtWidgets.QDialog):

    def __init__(self, old_abs_path, new_abs_path, old_iso_time, new_iso_time):
        super().__init__()
        self.setWindowTitle('Diff')
        layout = QtWidgets.QVBoxLayout()

        try:
            with open(old_abs_path, encoding='utf-8') as f:
                old_contents = f.readlines()
            with open(new_abs_path, encoding='utf-8') as f:
                new_contents = f.readlines()
        except UnicodeDecodeError:
            layout.addWidget(QtWidgets.QLabel('Not a UTF-8 text file.'))
        else:
            self.resize(940, 600)
            diff = difflib.unified_diff(old_contents, new_contents,
                                        fromfile=str(old_abs_path),
                                        tofile=str(new_abs_path),
                                        fromfiledate=old_iso_time,
                                        tofiledate=new_iso_time)

            diff_display = QtWidgets.QTextEdit()
            diff_display.setFont(QtGui.QFont('Liberation Mono', 10))
            diff_display.setReadOnly(True)
            html_lines = []
            for line in diff:
                if line.startswith('+'):
                    html_lines.append('\x3cpre style="background-color: '
                                      f'#a0f0a0"\x3e{line}\x3c/pre\x3e')
                elif line.startswith('-'):
                    html_lines.append('\x3cpre style="background-color: '
                                      f'#f0a0a0"\x3e{line}\x3c/pre\x3e')
                else:
                    html_lines.append(f'\x3cpre\x3e{line}\x3c/pre\x3e')

            diff_display.append(''.join(html_lines))
            layout.addWidget(diff_display)

        self.setLayout(layout)
        self.exec_()


def get_icon(icon_name):
    path_to_icon = etc.BASEDIR / 'icons/{}.png'.format(icon_name)
    return QtGui.QIcon(str(path_to_icon))


def main():
    main_app = QtWidgets.QApplication()
    main_window = MainWindow()
    main_window.run(main_app)


if __name__ == '__main__':
    main()
