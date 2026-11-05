"""Start the existing personal app on a trusted home LAN, with password login."""
import getpass
import ipaddress
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parent

def lan_addresses():
    try:
        addresses={row[4][0] for row in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET)}
    except socket.gaierror:
        return []
    return sorted(a for a in addresses if ipaddress.ip_address(a).is_private
                  and not ipaddress.ip_address(a).is_loopback
                  and not ipaddress.ip_address(a).is_link_local)

def password_hash(data_dir, reset=False, read_password=getpass.getpass):
    path=data_dir/'mobile-access.json'
    if path.exists() and not reset:
        config=json.loads(path.read_text(encoding='utf-8'))
        value=config.get('password_hash','')
        if not isinstance(value,str) or not value.startswith('scrypt:'):
            raise ValueError('Losenordsfilen kan inte lasas. Kor mobilstart med --reset-password.')
        return value
    print('Valj ett eget losenord for mobilinloggningen (minst 12 tecken).')
    print('Losenordet syns inte nar du skriver. Dela det inte i chatten.')
    while True:
        supplied=read_password('Losenord: ')
        if len(supplied)<12:
            print('Anvand minst 12 tecken.');continue
        if supplied!=read_password('Skriv samma losenord igen: '):
            print('Losenorden skiljer sig. Forsok igen.');continue
        value=generate_password_hash(supplied)
        break
    data_dir.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='mobile-access-',suffix='.tmp',dir=data_dir)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump({'password_hash':value},f)
        os.replace(name,path)
    finally:
        Path(name).unlink(missing_ok=True)
    return value

def main():
    data_dir=Path(os.environ.get('RESELL_DATA',ROOT/'data')).resolve()
    env=dict(os.environ)
    if not env.get('RESELL_PASSWORD'):
        env['RESELL_PASSWORD_HASH']=password_hash(data_dir,reset='--reset-password' in sys.argv)
    port=int(env.get('PORT','5000'))
    env.update(RESELL_HOST='0.0.0.0',RESELL_LAN='1')
    # Keep the already configured Ollama model and data directory in the child process.
    print('\nPLAGGVERKET PA MOBILEN',flush=True)
    print('Anslut mobilen och datorn till samma betrodda Wi-Fi.',flush=True)
    print('Oppna nagon av dessa adresser pa mobilen:',flush=True)
    addresses=lan_addresses()
    for address in addresses:print(f'  http://{address}:{port}',flush=True)
    if not addresses:print('  Ingen lokal IPv4-adress hittades. Kontrollera Wi-Fi och kor ipconfig.',flush=True)
    print('Logga in med ditt valda losenord. Lat datorn och detta fonster vara igang.',flush=True)
    print('Om Windows fragar om brandvagg: tillat endast privata natverk.',flush=True)
    print('Endast hemnat: HTTP ar okrypterat. Anvand inte pa oppet/delat Wi-Fi.',flush=True)
    print('Oppna inga portar i routern. Internetatkomst ingar inte.',flush=True)
    try:return subprocess.call([sys.executable,str(ROOT/'app.py')],cwd=ROOT,env=env)
    except KeyboardInterrupt:return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,json.JSONDecodeError) as e:
        print('Mobilstarten misslyckades: '+str(e),file=sys.stderr)
        raise SystemExit(1)
