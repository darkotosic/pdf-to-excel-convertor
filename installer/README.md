# Windows installer

`scripts/build_release.ps1` supplies the authoritative `pyproject.toml` version
to this definition and compiles it with Inno Setup 6. The per-user installer
contains the complete onedir distribution, creates a Start Menu shortcut, and
offers (but does not force) a desktop shortcut.

Do not invoke the definition without `/DAppVersion=<version>`. Its stable AppId
must never be regenerated, or Windows upgrade/uninstall identity will break.
