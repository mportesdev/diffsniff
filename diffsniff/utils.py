from collections import namedtuple
import filecmp
import os
from pathlib import Path
import shutil

ItemInfo = namedtuple('ItemInfo', 'equal unique mtimes left_to_right')


def compare_one_way(this_path, other_path, ignore_dirs=(), ignore_files=(),
                    skip=(), reverse=False):
    result = {}
    dirs_to_prune = shutil.ignore_patterns(*ignore_dirs)
    files_to_prune = shutil.ignore_patterns(*ignore_files)

    # walk `this_path` and compare files with `other_path`
    for this_abspath, subdirs, files in os.walk(this_path):

        # prune list of subdirs and list of files
        for subdir in dirs_to_prune(this_abspath, subdirs):
            subdirs.remove(subdir)
        for file in files_to_prune(this_abspath, files):
            files.remove(file)

        # relative path of the currently walked dir to the root of walk
        rel_path = os.path.relpath(this_abspath, this_path)

        for filename in files:
            # file relative path (this is the string stored in `result`)
            item_name = Path(filename if rel_path == '.'
                             else os.path.join(rel_path,
                                               filename)).as_posix()
            assert '\\' not in item_name

            if item_name in skip:
                continue

            # absolute paths of files
            file_here = os.path.join(this_abspath, filename)
            assert os.path.samefile(file_here,
                                    os.path.join(this_path, item_name))
            file_there = os.path.join(other_path, item_name)

            if not os.path.exists(file_there):
                # unique file
                item_info = ItemInfo(equal=False, unique=True, mtimes=None,
                                     left_to_right=not reverse)

            elif not filecmp.cmp(file_here, file_there, shallow=False):
                # unequal files of the same name
                mtime_here = os.path.getmtime(file_here)
                mtime_there = os.path.getmtime(file_there)
                item_info = ItemInfo(equal=False, unique=False,
                                     mtimes=(mtime_there, mtime_here)
                                     if reverse else (mtime_here, mtime_there),
                                     left_to_right=reverse
                                     if mtime_there > mtime_here else not reverse)
            else:
                # equal files
                item_info = ItemInfo(equal=True, unique=False, mtimes=None,
                                     left_to_right=None)

            result[item_name] = item_info

    return result


def set_fg_color(widget, color):
    palette = widget.palette()
    palette.setColor(palette.WindowText, color)
    widget.setPalette(palette)
