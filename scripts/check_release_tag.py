import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kantar_servis import __version__


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tag")
    args = parser.parse_args()
    beklenen = "v%s" % __version__
    if args.tag != beklenen:
        raise SystemExit("Surum uyusmazligi: etiket=%s, beklenen=%s" % (args.tag, beklenen))
    print("Surum etiketi dogrulandi: %s" % args.tag)


if __name__ == "__main__":
    main()
