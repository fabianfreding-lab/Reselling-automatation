import io, json, zipfile, importlib
import pytest
from PIL import Image, ImageDraw

@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv('RESELL_DATA',str(tmp_path));monkeypatch.delenv('RESELL_PASSWORD',raising=False);monkeypatch.delenv('OLLAMA_MODEL',raising=False);monkeypatch.delenv('RESELL_PASSWORD_HASH',raising=False);monkeypatch.delenv('RESELL_LAN',raising=False)
    import app
    importlib.reload(app);app.app.config['TESTING']=True
    c=app.app.test_client();h={'X-CSRF-Token':c.get('/api/state').json['csrf']}
    return app,c,h

def photo():
    im=Image.new('RGB',(100,100),'white');ImageDraw.Draw(im).rectangle((30,20,70,80),fill=(20,40,90));b=io.BytesIO();im.save(b,'PNG');return b.getvalue()
def post(c,h,d,route,**body):return c.post('/api/items/'+d['id']+'/'+route,headers=h,json={'revision':d['revision'],**body})
def patch(c,h,d,**body):return c.patch('/api/items/'+d['id'],headers=h,json={'revision':d['revision'],**body})
def ready(c,h):
    d=c.post('/api/items',headers=h,json={}).json
    d=patch(c,h,d,size='M',condition='Bra',facts={'kind':'Tröja','brand':'Exempel','color':'blå'},defects='Litet hål vid sömmen').json
    d=post(c,h,d,'confirm',confirmed=True).json
    d=c.post('/api/items/'+d['id']+'/images',headers=h,data={'revision':str(d['revision']),'role':'produkt','images':(io.BytesIO(photo()),'plagg.png')}).json
    d=post(c,h,d,'image/'+d['images'][0]['id'],action='approve').json
    d=post(c,h,d,'generate').json
    return patch(c,h,d,ads={p:{'price':150} for p in ['vinted','plick']}).json

def test_complete_flow(env):
    app,c,h=env;d=ready(c,h)
    assert 'Litet hål' in d['ads']['vinted']['description']
    assert c.get('/api/items/'+d['id']+'/export').status_code==409
    assert post(c,h,d,'approve',confirmed=False).status_code==400
    d=post(c,h,d,'approve',confirmed=True).json;assert d['approved']
    r=c.get('/api/items/'+d['id']+'/export');assert r.status_code==200
    z=zipfile.ZipFile(io.BytesIO(r.data));assert z.read('vinted/bilder/01-omslag.png')==photo();assert 'plick/annons.txt' in z.namelist()
    assert app.app.test_client().get('/api/items/'+d['id']).json['approved']
    assert post(c,h,d,'publication',platform='vinted',url='https://vinted.se/items/1',confirmed=False).status_code==400
    for p,url in [('vinted','https://vinted.se/items/1'),('plick','https://plick.se/annons/1')]:d=post(c,h,d,'publication',platform=p,url=url,confirmed=True).json
    d=post(c,h,d,'sale',confirmed=True,platform='vinted',date='2026-01-01',price=140,fees=5,shipping=10,other=3).json
    assert d['profit'] is None and d['ads']['plick']['removal_needed']
    d=patch(c,h,d,purchase=50).json;assert d['profit']==72
    d=post(c,h,d,'removed',confirmed=True,platform='plick').json;assert not d['ads']['plick']['removal_needed']
    assert c.get('/api/export/csv').status_code==200
    assert c.get('/api/export/all').status_code==200
    assert c.delete('/api/items/'+d['id'],headers=h,json={'revision':d['revision'],'confirmed':True}).status_code==200
    assert not list((app.DATA/'images').iterdir())

def test_uncertain_facts_and_changed_approval(env):
    app,c,h=env;d=ready(c,h)
    d['analysis']={'questions':['Vilket material?']};d['facts_confirmed']=False;d=app.save(d,d['revision'])
    assert post(c,h,d,'confirm',confirmed=True).status_code==400
    assert post(c,h,d,'generate').status_code==400
    d=post(c,h,d,'confirm',confirmed=True,answers='Material är okänt, utelämna.').json
    d=post(c,h,d,'approve',confirmed=True).json
    d=patch(c,h,d,facts={**d['facts'],'brand':'Ändrat'}).json
    assert not d['approved'] and not d['facts_confirmed']
    assert c.get('/api/items/'+d['id']+'/export').status_code==409

def test_publication_retry_and_revision_conflicts(env):
    app,c,h=env;d=ready(c,h);d=post(c,h,d,'approve',confirmed=True).json
    assert post(c,h,d,'publish',confirmed=True).status_code==501
    assert not app.item_get(d['id'])['ads']['vinted']['published']
    d=post(c,h,d,'publication',platform='vinted',url='https://vinted.se/items/1',confirmed=True).json;stale=d.copy()
    d=post(c,h,d,'publication',platform='vinted',url='https://vinted.se/items/1',confirmed=True).json
    assert post(c,h,stale,'publication',platform='vinted',url='https://vinted.se/items/1',confirmed=True).status_code==409
    assert post(c,h,d,'publication',platform='vinted',url='https://vinted.se/items/2',confirmed=True).status_code==409
    assert post(c,h,d,'publication',platform='plick',url='https://evil.example/items/1',confirmed=True).status_code==400
    assert len(c.get('/api/state').json['items'])==1

def test_pricing_requires_evidence(env):
    _,c,h=env;d=c.post('/api/items',headers=h,json={}).json
    assert post(c,h,d,'price').status_code==400
    assert post(c,h,d,'comparisons',price=200,evidence='sold',observed='2026-01-01',note='Liknande',verified=True).status_code==400
    d=post(c,h,d,'comparisons',price=200,evidence='asking',observed='2026-01-01',note='Samma märke, typ, storlek och skick').json
    d=post(c,h,d,'price').json
    assert d['pricing']['suggested']==200 and 'annonserade priser' in d['pricing']['reason']
    assert d['ads']['vinted']['price'] is None

def test_background_preserves_foreground_and_original(env):
    app,c,h=env;d=ready(c,h);x=d['images'][0]
    d=post(c,h,d,'image/'+x['id'],action='background',background='gray',tolerance=15).json
    im=Image.open(app.imagepath(d['images'][0]['edited']))
    assert im.getpixel((50,50))==(20,40,90) and im.getpixel((0,0))!=(255,255,255)
    assert app.imagepath(x['original']).read_bytes()==photo()
    assert not d['images'][0]['approved']
    d=c.post('/api/items/'+d['id']+'/images',headers=h,data={'revision':str(d['revision']),'role':'etikett','images':(io.BytesIO(photo()),'etikett.png')}).json
    assert post(c,h,d,'image/'+d['images'][1]['id'],action='background').status_code==400

def test_security_and_style(env,monkeypatch):
    app,c,h=env
    assert c.post('/api/items',json={}).status_code==403
    assert c.get('/api/state',headers={'Host':'evil.example'}).status_code==403
    style=c.post('/api/style/infer',headers=h,json={'examples':'Byxor storlek S 🌿\n\nEn röd kjol 🌿'}).json
    assert style['emoji']=='🌿'
    assert c.post('/api/settings',headers=h,json={'style':style}).status_code==200
    assert c.post('/api/settings',headers=h,json={'correction':{'guidance':'kortare','use':False}}).status_code==400
    d=ready(c,h);assert 'kjol' not in d['ads']['vinted']['description']
    assert patch(c,h,d,purchase='nan').status_code==400
    z=zipfile.ZipFile(io.BytesIO(c.get('/api/export/all').data));assert json.loads(z.read('data.json'))['settings']['style']['examples']==style['examples']
    assert c.delete('/api/all',headers=h,json={'confirm':'RADERA ALLT'}).status_code==200
    assert c.get('/api/state').json['items']==[]
    monkeypatch.setattr(app,'PASSWORD','test-password')
    assert c.get('/').status_code==302 and c.get('/api/state').status_code==401
    c.get('/login')
    with c.session_transaction() as s:nonce=s['login_nonce']
    assert c.post('/login',data={'password':'test-password','nonce':nonce}).status_code==302
    assert c.get('/api/state').status_code==200

def test_personal_opening_uses_only_current_facts(env):
    app,c,h=env
    profile={**app.STYLE,'examples':'Säljer nu denna röda jacka från GammaltMärke. Modell X.','opening':'Säljer nu: {färg} {plagg}{från_märke}.','closing':'Skriv gärna om du undrar något.\nTack för titten 🌿','emoji':''}
    assert c.post('/api/settings',headers=h,json={'style':profile}).status_code==200
    d=ready(c,h)
    for p in ['vinted','plick']:
        description=d['ads'][p]['description']
        assert description.startswith('Säljer nu: blå Tröja från Exempel.\n')
        assert description.endswith(profile['closing'])
        assert 'GammaltMärke' not in description and 'Modell X' not in description
        assert 'Litet hål vid sömmen' in description
    d=patch(c,h,d,facts={**d['facts'],'brand':'','color':''}).json
    d=post(c,h,d,'confirm',confirmed=True).json
    d=post(c,h,d,'generate').json
    assert d['ads']['plick']['description'].startswith('Säljer nu: Tröja.\n')

def test_mobile_lan_login_guards_images_exports_and_sessions(env,monkeypatch):
    app,c,h=env
    from werkzeug.security import generate_password_hash
    monkeypatch.setattr(app,'LAN_ONLY',True)
    monkeypatch.setattr(app,'PASSWORD_HASH',generate_password_hash('test-only-mobile-password'))
    lan={'REMOTE_ADDR':'192.168.1.40'}
    host={'Host':'192.168.1.20:5000'}
    for route in ['/api/state','/media/not-an-image.png','/api/export/all','/api/export/csv']:
        assert c.get(route,headers=host,environ_overrides=lan).status_code==401
    assert c.get('/login',headers={'Host':'evil.example'},environ_overrides=lan).status_code==403
    assert c.get('/login',headers=host,environ_overrides={'REMOTE_ADDR':'8.8.8.8'}).status_code==403
    c.get('/login',headers=host,environ_overrides=lan)
    with c.session_transaction(base_url='http://192.168.1.20:5000') as sess:nonce=sess['login_nonce']
    r=c.post('/login',data={'nonce':nonce,'password':'test-only-mobile-password'},headers=host,environ_overrides=lan)
    assert r.status_code==302
    assert c.get('/api/state',headers=host,environ_overrides=lan).status_code==200
    # Changing the configured password invalidates an already signed-in browser.
    monkeypatch.setattr(app,'PASSWORD_HASH',generate_password_hash('another-test-mobile-password'))
    assert c.get('/api/state',headers=host,environ_overrides=lan).status_code==401


def test_mobile_password_setup_persists_only_hash(tmp_path):
    from mobile_start import password_hash
    from werkzeug.security import check_password_hash
    values=iter(['short','long-test-password','different-password','long-test-password','long-test-password'])
    value=password_hash(tmp_path,read_password=lambda prompt:next(values))
    assert check_password_hash(value,'long-test-password')
    assert 'long-test-password' not in (tmp_path/'mobile-access.json').read_text()
    assert password_hash(tmp_path,read_password=lambda prompt:pytest.fail('Must reuse saved hash'))==value
    changed=password_hash(tmp_path,reset=True,read_password=lambda prompt:'replacement-test-password')
    assert changed!=value and check_password_hash(changed,'replacement-test-password')


def test_heic_mobile_photo_keeps_source_and_exports_viewable_png(env):
    app,c,h=env
    import pillow_heif
    im=Image.new('RGB',(80,100),(31,61,91))
    file=io.BytesIO();pillow_heif.from_pillow(im).save(file,quality=100)
    original=file.getvalue()
    d=ready(c,h)
    d=c.post('/api/items/'+d['id']+'/images',headers=h,data={'revision':str(d['revision']),'role':'etikett','images':(io.BytesIO(original),'etikett.heic')}).json
    x=d['images'][-1]
    assert x['original'].endswith('.heic') and x['preview'].endswith('.png')
    assert app.imagepath(x['original']).read_bytes()==original
    assert c.get('/media/'+x['preview']).mimetype=='image/png'
    with Image.open(io.BytesIO(original)) as decoded:
        assert Image.open(app.imagepath(x['preview'])).getpixel((40,50))==decoded.convert('RGB').getpixel((40,50))
    d=post(c,h,d,'image/'+x['id'],action='approve').json
    d=post(c,h,d,'approve',confirmed=True).json
    archive=zipfile.ZipFile(io.BytesIO(c.get('/api/items/'+d['id']+'/export').data))
    assert any(name.startswith('vinted/bilder/02') and name.endswith('.png') for name in archive.namelist())
    backup=zipfile.ZipFile(io.BytesIO(c.get('/api/export/all').data))
    assert backup.read('images/'+x['original'])==original
    assert 'images/'+x['preview'] in backup.namelist()


def test_invalid_mobile_image_retains_draft(env):
    _,c,h=env;d=ready(c,h)
    r=c.post('/api/items/'+d['id']+'/images',headers=h,data={'revision':str(d['revision']),'images':(io.BytesIO(b'not an image'),'broken.heic')})
    assert r.status_code==400
    stored=c.get('/api/items/'+d['id']).json
    assert stored['revision']==d['revision'] and len(stored['images'])==1


def test_parallel_login_page_load_does_not_invalidate_form(env,monkeypatch):
    app,c,h=env;monkeypatch.setattr(app,'PASSWORD','test-only-password')
    c.get('/login')
    with c.session_transaction() as sess:nonce=sess['login_nonce']
    # Browsers may request icons or users may open another login tab before submitting.
    assert c.get('/favicon.ico').status_code==200
    c.get('/login')
    assert c.post('/login',data={'nonce':nonce,'password':'test-only-password'}).status_code==302
    assert c.get('/api/state').status_code==200
