"""Generate a PyInstaller Windows version resource from pyproject.toml."""

import argparse
from pathlib import Path
import tomllib


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pyproject", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--company", default="")
    parser.add_argument("--copyright", default="")
    args = parser.parse_args()
    project = tomllib.loads(args.pyproject.read_text(encoding="utf-8"))["project"]
    version = project["version"]
    numeric = tuple(int(part) for part in version.split(".")[:4])
    numeric += (0,) * (4 - len(numeric))
    fields = {
        "CompanyName": args.company,
        "FileDescription": "PDF to Excel Converter",
        "FileVersion": version,
        "InternalName": "PDF-to-Excel",
        "LegalCopyright": args.copyright,
        "OriginalFilename": "PDF-to-Excel.exe",
        "ProductName": "PDF to Excel Converter",
        "ProductVersion": version,
    }
    strings = ",\n".join(f"StringStruct({key!r}, {value!r})" for key, value in fields.items())
    content = f"""VSVersionInfo(ffi=FixedFileInfo(filevers={numeric}, prodvers={numeric}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)), kids=[StringFileInfo([StringTable('040904B0', [{strings}])]), VarFileInfo([VarStruct('Translation', [1033, 1200])])])\n"""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
