"""Run in a private hosting console, never in a public web endpoint."""
import json
import os
from pathlib import Path
import sys
from mobile_start import password_hash

if __name__=='__main__':
    root=Path(__file__).resolve().parent
    data=Path(os.environ.get('RESELL_DATA',root/'data')).resolve()
    password_hash(data,reset='--reset-password' in sys.argv)
    config=data/'web-settings.json'
    if not config.exists():
        fd=os.open(config,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump({'ai_provider':'none','gemini_api_key':'','gemini_model':'','free_tier_confirmed':False},f,indent=2)
    print('Losenord forberett. AI ar avstangd i den nya webbkonfigurationen.')
    print('Forvara data/web-settings.json privat. Dela aldrig API-nycklar i chatten eller GitHub.')
