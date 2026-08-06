import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import language_paths
from src.validators import validate_languages

def test_ten_languages_and_catalan_path():
    paths = language_paths()
    assert validate_languages(paths)
    assert paths["ca"] == "/cat/"

import importlib
import src.config as config


def test_dotenv_auto_load(monkeypatch, tmp_path):
    env_file = config.ROOT / ".env"
    original = env_file.read_text(encoding="utf-8") if env_file.exists() else None
    try:
        env_file.write_text("SEO_TRACKER_TEST_ENV=loaded\n", encoding="utf-8")
        monkeypatch.delenv("SEO_TRACKER_TEST_ENV", raising=False)
        importlib.reload(config)
        assert config.env("SEO_TRACKER_TEST_ENV") == "loaded"
    finally:
        if original is None:
            env_file.unlink(missing_ok=True)
        else:
            env_file.write_text(original, encoding="utf-8")
        importlib.reload(config)
