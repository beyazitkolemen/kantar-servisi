import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kantar_servis import __version__

BUILD_DIR = ROOT / ".build-assets"


def version_tuple():
    parcalar = [int(parca) for parca in __version__.split(".")]
    while len(parcalar) < 4:
        parcalar.append(0)
    return tuple(parcalar[:4])


def generate_icon():
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (256, 256), (15, 23, 42, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((14, 14, 242, 242), radius=50, fill=(37, 99, 235, 255))
    draw.rounded_rectangle((52, 55, 204, 109), radius=17, fill=(239, 246, 255, 255))
    draw.rectangle((71, 130, 185, 194), fill=(255, 255, 255, 255))
    draw.rectangle((90, 146, 105, 180), fill=(37, 99, 235, 255))
    draw.rectangle((121, 136, 136, 180), fill=(37, 99, 235, 255))
    draw.rectangle((152, 154, 167, 180), fill=(37, 99, 235, 255))
    image.save(
        BUILD_DIR / "app.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


def generate_version_info():
    surum = version_tuple()
    metin = """VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={surum},
    prodvers={surum},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '041F04E6',
        [
          StringStruct('CompanyName', 'LISDEP'),
          StringStruct('FileDescription', 'Kantar Servisi'),
          StringStruct('FileVersion', '{surum_metni}'),
          StringStruct('InternalName', 'KantarServisi'),
          StringStruct('LegalCopyright', 'Copyright (c) 2026'),
          StringStruct('OriginalFilename', 'KantarServisi.exe'),
          StringStruct('ProductName', 'Kantar Servisi'),
          StringStruct('ProductVersion', '{surum_metni}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1055, 1254])])
  ]
)
""".format(surum=surum, surum_metni=__version__)
    (BUILD_DIR / "version_info.txt").write_text(metin, encoding="utf-8")


if __name__ == "__main__":
    generate_icon()
    generate_version_info()
    print("Windows build varliklari olusturuldu: %s" % BUILD_DIR)
