from collections import namedtuple
from pathlib import Path

# path to the app's directory
BASEDIR = Path(__file__).parent.parent

# color to highlight older files & missing dirs
LIGHT = (160, 0, 80, 128)

# button widths
TEXT_BUTTON_WIDTH = 90
ICON_BUTTON_WIDTH = 40
TEXT_AND_ICON_BUTTON_WIDTH = 130

# a class for presets
Preset = namedtuple('Preset', 'path_1 path_2 ignore_dirs ignore_files')

# presets dictionary
presets = {
    'default': Preset(
        path_1=str(BASEDIR / 'test_path_left'),
        path_2=str(BASEDIR / 'test_path_right'),
        ignore_dirs=(),
        ignore_files=()
    )
}
