#!/usr/bin/env python3
"""
Punto de entrada de ResiControl.
Ejecutar: python main.py  o  doble clic en resicontrol.exe
"""

from resicontrol import ResiControl


if __name__ == "__main__":
    app = ResiControl()
    app.mainloop()