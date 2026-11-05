"""Real mobile browser flow; starts its own disposable server and data directory."""
import io, os, subprocess, sys, tempfile, time
from pathlib import Path
from urllib.request import urlopen
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright, expect

root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    env={**os.environ,'RESELL_DATA':tmp+'/data','PORT':'5019','RESELL_HOST':'127.0.0.1'}
    env.pop('RESELL_PASSWORD',None)
    env.pop('RESELL_PASSWORD_HASH',None)
    env.pop('RESELL_LAN',None)
    proc=subprocess.Popen([sys.executable,str(root/'app.py')],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                urlopen('http://127.0.0.1:5019').close();break
            except OSError:time.sleep(.1)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('response',lambda r:print('HTTP ERROR',r.status,r.url,r.text()) if r.status>=400 else None)
            page.goto('http://127.0.0.1:5019')
            page.get_by_role('button',name='Skapa mitt första utkast').click()
            page.get_by_label('Namn i ditt lager').fill('Tidigare namn')
            page.get_by_role('button',name='Spara nu').click()
            page.route('**/api/items/*',lambda r: r.abort() if r.request.method=='PATCH' else r.continue_())
            page.get_by_label('Namn i ditt lager').fill('Blå tröja')
            page.wait_for_function("Object.keys(localStorage).some(k=>k.startsWith('plaggverket.unsaved.'))")
            page.reload();page.wait_for_selector('#inventory')
            page.unroute('**/api/items/*')
            page.once('dialog',lambda d:d.accept())
            page.get_by_role('button',name='Öppna plagg').click()
            assert page.get_by_label('Namn i ditt lager').input_value()=='Blå tröja'
            page.get_by_label('Storlek *',exact=True).fill('M')
            page.get_by_label('Skick *',exact=True).select_option('Bra')
            page.get_by_label('Plaggtyp *',exact=True).fill('Tröja')
            page.get_by_label('Färg',exact=True).fill('blå')
            page.get_by_role('button',name='Spara nu').click()
            page.get_by_label('Jag har kontrollerat uppgifterna').check()
            page.get_by_role('button',name='Bekräfta fakta',exact=True).click()
            page.get_by_text('Fakta bekräftade',exact=True).wait_for()
            page.get_by_role('tab',name='2. Bilder').click()
            im=Image.new('RGB',(400,500),'white');ImageDraw.Draw(im).rectangle((120,80,280,420),fill='#31517f');path=tmp+'/test.png';im.save(path)
            page.locator('#filesInput').set_input_files(path)
            page.get_by_role('button',name='Ladda upp bilder',exact=True).click()
            page.get_by_role('button',name='Byt bakgrund',exact=True).click()
            page.get_by_role('button',name='Godkänn bilden',exact=True).click()
            page.get_by_role('tab',name='3. Text & pris').click()
            page.get_by_role('button',name='Skapa regelbaserat textförslag',exact=True).click()
            expect(page.locator('[data-field="ads.vinted.description"]')).not_to_have_value('')
            prices=page.get_by_label('Annonspris (kr)',exact=True)
            prices.nth(0).fill('150');prices.nth(1).fill('150')
            page.get_by_role('button',name='Spara nu').click()
            page.reload();page.wait_for_selector('#inventory')
            page.get_by_role('button',name='Öppna plagg').click()
            assert page.get_by_label('Namn i ditt lager').input_value()=='Blå tröja'
            page.get_by_role('tab',name='4. Granska & exportera').click()
            page.get_by_label('Jag har granskat och godkänner exakt').check()
            page.get_by_role('button',name='Godkänn innehållet',exact=True).click()
            page.get_by_role('link',name='Ladda ned annonser & bilder (ZIP)').wait_for()
            with page.expect_download() as info:page.get_by_role('link',name='Ladda ned annonser & bilder (ZIP)').click()
            info.value.save_as(tmp+'/export.zip')
            assert Path(tmp+'/export.zip').stat().st_size>100
            page.get_by_role('tab',name='5. Försäljning').click()
            page.locator('#sale-price').fill('140')
            page.get_by_label('Jag bekräftar försäljningen').check()
            page.get_by_role('button',name='Spara försäljning').click()
            page.get_by_role('heading',name='Vinst: Okänd').wait_for()
            page.get_by_label('Inköpspris (kr), lämna tomt om okänt').fill('50')
            page.get_by_role('button',name='Spara nu').click()
            page.get_by_role('heading',name='Vinst: 90').wait_for()
            page.get_by_role('button',name='← Mitt lager').click()
            page.get_by_role('heading',name='Blå tröja').wait_for()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path='/tmp/plaggverket-mobile.png',full_page=True)
            assert not errors,errors
            browser.close()
            print('PASS: mobile upload → facts → background → text → review → ZIP → sale; reload persistence; offline text recovery; no browser errors or horizontal overflow')
    finally:
        proc.terminate();proc.wait(timeout=5)
