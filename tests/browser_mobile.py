"""Password login and native upload-source controls in a mobile-sized browser.
Uses a disposable server/database. Does not emulate actual phone camera hardware.
"""
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen
from urllib.error import HTTPError
from PIL import Image
import pillow_heif
from werkzeug.security import generate_password_hash
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
PASSWORD='test-only-mobile-password'

def photo(fmt='JPEG'):
    im=Image.new('RGB',(90,110),(21,81,51));buf=io.BytesIO()
    if fmt=='HEIF':pillow_heif.from_pillow(im).save(buf,quality=100)
    else:im.save(buf,format=fmt)
    return buf.getvalue()

with tempfile.TemporaryDirectory() as tmp:
    env={**os.environ,'RESELL_DATA':tmp,'RESELL_PASSWORD_HASH':generate_password_hash(PASSWORD),'RESELL_LAN':'1','RESELL_HOST':'127.0.0.1','PORT':'5023'}
    env.pop('RESELL_PASSWORD',None);env.pop('OLLAMA_MODEL',None)
    proc=subprocess.Popen([sys.executable,str(ROOT/'app.py')],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                urlopen('http://127.0.0.1:5023/login').close();break
            except OSError:time.sleep(.1)
        try:urlopen('http://127.0.0.1:5023/api/state');raise AssertionError('API must require login')
        except HTTPError as e:assert e.code==401
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('response',lambda r:print('HTTP',r.status,r.url,r.text()[:300]) if r.status>=400 else None)
            page.goto('http://127.0.0.1:5023/')
            page.get_by_label('Lösenord',exact=True).fill(PASSWORD)
            page.get_by_role('button',name='Logga in',exact=True).click()
            page.get_by_role('button',name='Skapa mitt första utkast').click()
            page.get_by_role('tab',name='2. Bilder').click()
            assert page.locator('#cameraInput').get_attribute('capture')=='environment'
            for picker in ['#cameraInput','#libraryInput','#filesInput']:expect(page.locator(picker)).not_to_be_visible()
            with page.expect_file_chooser() as chosen:page.get_by_role('button',name='Ta foto',exact=True).click()
            assert not chosen.value.is_multiple()
            chosen.value.set_files({'name':'kamera.jpg','mimeType':'image/jpeg','buffer':photo()})
            expect(page.locator('#uploadQueue')).to_contain_text('1 valda bilder')
            with page.expect_file_chooser() as chosen:page.get_by_role('button',name='Bildbibliotek',exact=True).click()
            assert chosen.value.is_multiple()
            chosen.value.set_files([{'name':'bibliotek.png','mimeType':'image/png','buffer':photo('PNG')},{'name':'etikett.heic','mimeType':'image/heic','buffer':photo('HEIF')}])
            expect(page.locator('#uploadQueue')).to_contain_text('3 valda bilder')
            # Cancelling a picker retains the previous selection.
            page.locator('#cameraInput').set_input_files([])
            expect(page.locator('#uploadQueue')).to_contain_text('3 valda bilder')
            with page.expect_file_chooser() as chosen:page.get_by_role('button',name='Välj filer',exact=True).click()
            chosen.value.set_files({'name':'fil.jpg','mimeType':'image/jpeg','buffer':photo()})
            expect(page.locator('#uploadQueue')).to_contain_text('4 valda bilder')
            # The queue survives navigation to another step.
            page.get_by_role('tab',name='1. Plagget').click()
            page.get_by_role('tab',name='2. Bilder').click()
            expect(page.locator('#uploadQueue')).to_contain_text('4 valda bilder')
            page.locator('#uploadQueue').get_by_role('button',name='Ta bort',exact=True).last.click()
            expect(page.locator('#uploadQueue')).to_contain_text('3 valda bilder')
            page.get_by_role('button',name='Ladda upp bilder',exact=True).click()
            expect(page.locator('.photo')).to_have_count(3)
            expect(page.locator('#uploadQueue')).to_contain_text('Inga bilder valda')
            page.wait_for_function("() => [...document.querySelectorAll('.beforeafter img')].every(im => im.complete && im.naturalWidth > 0)")
            page.reload();page.get_by_role('button',name='Öppna plagg').click()
            page.get_by_role('tab',name='2. Bilder').click()
            expect(page.locator('.photo')).to_have_count(3)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path='/tmp/plaggverket-upload-mobile.png',full_page=True)
            page.get_by_role('button',name='Min stil & inställningar').click()
            page.get_by_role('button',name='Logga ut',exact=True).click()
            page.get_by_role('button',name='Logga in',exact=True).wait_for()
            assert not errors,errors
            browser.close()
        print('PASS: mobile login, camera/library/file pickers, mixed HEIC upload, cancellation, queue persistence, reload, image rendering, logout; no browser errors or overflow')
    finally:
        proc.terminate();proc.wait(timeout=5)
