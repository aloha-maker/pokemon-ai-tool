import os

def win_safe_path(path):
    """Windows長パス対応"""
    if os.name == 'nt':
        return "\\\\?\\" + os.path.abspath(path)
    return path
