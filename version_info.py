# -*- coding: utf-8 -*-
"""
Generate a PyInstaller-compatible VSVersionInfo structure.

Run standalone to preview:  python version_info.py
Used by trip.spec at build time via exec().
"""

from PyInstaller.utils.win32.versioninfo import (
    VSVersionInfo,
    FixedFileInfo,
    StringFileInfo,
    StringTable,
    StringStruct,
    VarFileInfo,
    VarStruct,
)

# ── Keep in sync with src/constants.py & installer.iss ──
_MAJOR = 2
_MINOR = 3
_PATCH = 0
_BUILD = 0

version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(_MAJOR, _MINOR, _PATCH, _BUILD),
        prodvers=(_MAJOR, _MINOR, _PATCH, _BUILD),
        mask=0x3F,
        flags=0x0,
        OS=0x40004,          # VOS_NT_WINDOWS32
        fileType=0x1,        # VFT_APP
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo([
            StringTable(
                "040904B0",  # Lang=US English, CharSet=Unicode
                [
                    StringStruct("CompanyName", "GoblinRules"),
                    StringStruct("FileDescription", "TRIP — Tray IP Monitor"),
                    StringStruct("FileVersion", f"{_MAJOR}.{_MINOR}.{_PATCH}.{_BUILD}"),
                    StringStruct("InternalName", "TRIP"),
                    StringStruct("LegalCopyright", "Copyright © 2025 GoblinRules. MIT License."),
                    StringStruct("OriginalFilename", "TRIP.exe"),
                    StringStruct("ProductName", "TRIP — Tray IP"),
                    StringStruct("ProductVersion", f"{_MAJOR}.{_MINOR}.{_PATCH}.{_BUILD}"),
                ],
            )
        ]),
        VarFileInfo([VarStruct("Translation", [0x0409, 1200])]),  # US English, Unicode
    ],
)

if __name__ == "__main__":
    print(version_info)
