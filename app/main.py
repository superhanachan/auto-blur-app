import sys
import os
import torchvision

# Fix for PyInstaller --windowed crashes due to missing stdout/stderr
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

from gui import main

if __name__ == '__main__':
    main()
