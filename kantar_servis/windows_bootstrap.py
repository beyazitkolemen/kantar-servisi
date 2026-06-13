# -*- coding: utf-8 -*-
import sys

from .desktop import main


def run():
    # Gomme Windows baslaticisi, alt servis sureclerinin ayni EXE ile acilmasi
    # icin masaustu kodunun paketlenmis uygulama sozlesmesini kullanir.
    sys.frozen = True
    return main()


if __name__ == "__main__":
    raise SystemExit(run())
