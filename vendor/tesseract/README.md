# Optional Tesseract bundle

For a fully offline deployment, place an official Tesseract Windows distribution
here before building. Include `tesseract.exe`, its runtime DLLs, and
`tessdata/{srp,srp_latn,eng}.traineddata`. These are intentionally not committed
because they are binary third-party artifacts. Preserve the upstream Apache 2.0
license and notices when redistributing it.
