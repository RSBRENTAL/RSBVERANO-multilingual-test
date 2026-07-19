import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import language_paths
from src.validators import validate_languages

def test_ten_languages_and_catalan_path():
    paths = language_paths()
    assert validate_languages(paths)
    assert paths["ca"] == "/cat/"
