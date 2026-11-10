"""Set the account's WSGI file to execute this file; see deploy/GRATIS.md."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from web_runtime import prepare_web_environment
prepare_web_environment()
from app import app as application
