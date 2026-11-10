"""Hosting/auth setup and provider contract tests. No paid or live AI calls."""
import importlib
import io
import json
import os
from pathlib import Path
from urllib.error import HTTPError
import pytest
from werkzeug.security import generate_password_hash

@pytest.fixture
def hosted(tmp_path,monkeypatch):
    for name in ['RESELL_PASSWORD','RESELL_PASSWORD_HASH','AI_PROVIDER','GEMINI_API_KEY','GEMINI_MODEL','GEMINI_FREE_TIER_CONFIRMED','OLLAMA_MODEL']:
        monkeypatch.setenv(name,os.environ.get(name,''))
        monkeypatch.delenv(name,raising=False)
    monkeypatch.setenv('RESELL_DATA',str(tmp_path));monkeypatch.setenv('RESELL_HTTPS','1');monkeypatch.setenv('RESELL_LAN','0')
    import app;importlib.reload(app)
    return app,tmp_path

def test_hosting_fails_closed_and_enforces_https_cookie(hosted,monkeypatch):
    app,path=hosted
    from web_runtime import prepare_web_environment
    with pytest.raises(RuntimeError,match='lösenord'):prepare_web_environment(path)
    (path/'mobile-access.json').write_text(json.dumps({'password_hash':generate_password_hash('test-only-web-password')}))
    monkeypatch.setenv('RESELL_LAN','1')
    prepare_web_environment(path)
    importlib.reload(app)
    c=app.app.test_client();base='https://personal-app.example.test'
    assert c.get('/api/state',base_url=base).status_code==401
    r=c.get('/login',base_url=base)
    assert 'Secure' in r.headers['Set-Cookie'] and 'HttpOnly' in r.headers['Set-Cookie']
    with c.session_transaction(base_url=base) as s:nonce=s['login_nonce']
    assert c.post('/login',base_url=base,data={'nonce':nonce,'password':'test-only-web-password'}).status_code==302
    data=c.get('/api/state',base_url=base).json
    assert data['ai']['provider']=='none' and not data['ai']['configured']
    # Restarting the app retains the same storage/session key, rather than a temporary database.
    token=data['csrf'];d=c.post('/api/items',base_url=base,headers={'X-CSRF-Token':token},json={}).json
    importlib.reload(app)
    assert app.item_get(d['id'])['id']==d['id']


def test_free_confirmation_required_no_request_without_it(hosted,monkeypatch):
    app,path=hosted
    monkeypatch.setenv('AI_PROVIDER','gemini');monkeypatch.setenv('GEMINI_API_KEY','test-only-api-key');monkeypatch.setenv('GEMINI_MODEL','fixture-free-model')
    monkeypatch.setattr(app,'urlopen',lambda *a,**kw:pytest.fail('AI must remain disabled'))
    assert not app.ai_status()['configured']
    with pytest.raises(Exception) as e:app.generate_ai('test')
    assert e.value.code==503
    monkeypatch.setenv('AI_PROVIDER','none')
    with pytest.raises(Exception) as e:app.generate_ai('test')
    assert e.value.code==503


def test_gemini_text_and_image_request_has_server_side_key(hosted,monkeypatch):
    app,path=hosted
    monkeypatch.setenv('AI_PROVIDER','gemini');monkeypatch.setenv('GEMINI_API_KEY','test-only-api-key');monkeypatch.setenv('GEMINI_MODEL','fixture-free-model');monkeypatch.setenv('GEMINI_FREE_TIER_CONFIRMED','1')
    seen=[]
    def request(req,timeout):
        assert req.full_url.startswith('https://generativelanguage.googleapis.com/')
        assert 'test-only-api-key' not in req.full_url
        assert req.get_header('X-goog-api-key')=='test-only-api-key'
        body=json.loads(req.data);seen.append(body)
        return io.BytesIO(json.dumps({'candidates':[{'content':{'parts':[{'text':json.dumps({'label_text':'Fixture only'})}]}}]}).encode())
    monkeypatch.setattr(app,'urlopen',request)
    assert app.generate_ai('Fixture prompt',['aW1hZ2U='])=={'label_text':'Fixture only'}
    assert seen[0]['contents'][0]['parts'][1]['inlineData']['mimeType']=='image/jpeg'
    assert seen[0]['generationConfig']['responseMimeType']=='application/json'
    assert 'test-only-api-key' not in json.dumps(app.ai_status())


def test_free_quota_error_does_not_retry_or_fallback(hosted,monkeypatch):
    app,path=hosted
    monkeypatch.setenv('AI_PROVIDER','gemini');monkeypatch.setenv('GEMINI_API_KEY','test-only-api-key');monkeypatch.setenv('GEMINI_MODEL','fixture-free-model');monkeypatch.setenv('GEMINI_FREE_TIER_CONFIRMED','1')
    calls=[]
    def quota(req,timeout):calls.append(req);raise HTTPError(req.full_url,429,'quota',{},None)
    monkeypatch.setattr(app,'urlopen',quota)
    monkeypatch.setattr(app,'ollama',lambda *a,**kw:pytest.fail('No fallback'))
    with pytest.raises(Exception) as e:app.generate_ai('test')
    assert e.value.code==503 and 'kvoten' in e.value.description and len(calls)==1
