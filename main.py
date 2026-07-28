import sys
import os

root_dir = os.path.abspath(os.path.dirname(__file__))
src_dir = os.path.join(root_dir, "src")

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from src.gui.app import TitanSapManipulatorApp


def main():
    app = TitanSapManipulatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
