from pathlib import Path
from platformdirs import user_config_path
from pydantic import BaseModel, Field
import json


class Settings(BaseModel):
    tesseract_cmd: Path | None = None
    dpi: int = Field(default=300, ge=150, le=600)
    confidence_threshold: float = Field(default=0.35, ge=0, le=1)

    @classmethod
    def load(cls) -> "Settings":
        path = user_config_path("pdf-to-excel-converter") / "settings.json"
        return cls.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else cls()

    def save(self) -> None:
        path = user_config_path("pdf-to-excel-converter") / "settings.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.model_dump(mode="json"), indent=2), encoding="utf-8")
