"""Fail-closed WSGI configuration for persistent, password-protected web hosting."""
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def prepare_web_environment(data_dir=None):
    data=Path(data_dir or os.environ.get('RESELL_DATA',ROOT/'data')).resolve()
    credentials=data/'mobile-access.json'
    if not os.environ.get('RESELL_PASSWORD'):
        if not credentials.is_file():
            raise RuntimeError('Webbstart blockerad: kör configure_web.py för att välja lösenord först.')
        password_hash=json.loads(credentials.read_text(encoding='utf-8')).get('password_hash','')
        if not isinstance(password_hash,str) or not password_hash.startswith('scrypt:'):
            raise RuntimeError('Webbstart blockerad: lösenordsfilen är ogiltig.')
        os.environ['RESELL_PASSWORD_HASH']=password_hash
    os.environ['RESELL_DATA']=str(data)
    os.environ['RESELL_HTTPS']='1'
    os.environ['RESELL_LAN']='0'
    # No API provider is enabled by deployment alone. Settings remain outside source control.
    settings_path=data/'web-settings.json'
    config=json.loads(settings_path.read_text(encoding='utf-8')) if settings_path.exists() else {}
    if not isinstance(config,dict):raise RuntimeError('Ogiltig webbkonfiguration.')
    provider=config.get('ai_provider','none')
    if provider not in ('none','gemini'):raise RuntimeError('Välj none eller gemini som AI-tjänst för webbdrift.')
    os.environ['AI_PROVIDER']=provider
    for source,target in [('gemini_api_key','GEMINI_API_KEY'),('gemini_model','GEMINI_MODEL')]:
        value=config.get(source,'')
        if not isinstance(value,str):raise RuntimeError('AI-inställningarna måste vara text.')
        os.environ[target]=value
    # This is the owner's confirmation, NOT a billing-state check against Google.
    os.environ['GEMINI_FREE_TIER_CONFIRMED']='1' if config.get('free_tier_confirmed') is True else '0'
    return data
