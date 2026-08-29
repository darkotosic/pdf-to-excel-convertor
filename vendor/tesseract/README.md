# Tesseract release bundle

For a fully offline deployment, place an official Tesseract Windows distribution
here before building by running `scripts/prepare_tesseract.ps1`. Include
`tesseract.exe`, its runtime DLLs, and
`tessdata/{srp,srp_latn,eng,osd}.traineddata`. These are intentionally not committed
because they are binary third-party artifacts. Preserve the upstream Apache 2.0
license and notices when redistributing it.

Official releases fail closed if this directory is incomplete. The preparation
script copies a complete, already-trusted Windows installation; it never
downloads or substitutes binaries.
