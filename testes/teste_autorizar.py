import json, sys
from playwright.sync_api import sync_playwright
import os
UMD = os.environ.get('UMD', 'node_modules/@supabase/supabase-js/dist/umd/supabase.js')  # supabase-js 2.118.0
PAG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'autorizar.html')
AUT = sys.argv[1] if len(sys.argv) > 1 else 'sim'
log = []
def rota(route):
    u = route.request.url; m = route.request.method
    log.append(m + ' ' + u.split('?')[0])
    if 'jsdelivr' in u: return route.fulfill(path=UMD, content_type='application/javascript')
    if 'fonts.' in u: return route.fulfill(body='', content_type='text/css')
    if u.endswith('icon-192.png'): return route.fulfill(body='')
    if '/auth/v1/token' in u:
        body = json.loads(route.request.post_data)
        if body.get('password') != 'certa': return route.fulfill(status=400, json={'error':'invalid_grant','error_description':'Invalid login credentials'})
        return route.fulfill(json={'access_token':'tok','token_type':'bearer','expires_in':3600,'expires_at':9999999999,'refresh_token':'r','user':{'id':'u1','email':body['email']}})
    if '/functions/v1/dados-rega/entrada' in u: return route.fulfill(json={'autorizado': AUT=='sim', 'nome':'Dalmar Santos'}, headers={'access-control-allow-origin':'*'})
    if '/oauth/authorizations/abc/consent' in u:
        return route.fulfill(json={'redirect_url':'https://claude.ai/api/mcp/auth_callback?code=xyz'})
    if '/oauth/authorizations/abc' in u:
        return route.fulfill(json={'authorization_id':'abc','client':{'name':'Claude'},'redirect_uri':'https://claude.ai/api/mcp/auth_callback','scope':'email'})
    if 'claude.ai' in u: return route.fulfill(body='<p>Claude callback</p>', content_type='text/html')
    return route.fulfill(status=404, body='')
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); pg.route('**/*', rota)
    pg.goto('https://cocopalma.github.io/rega-coco/autorizar.html?authorization_id=abc')
    pg.route('https://cocopalma.github.io/**', lambda r: r.fulfill(path=PAG, content_type='text/html') if 'autorizar.html' in r.request.url else rota(r))
    pg.goto('https://cocopalma.github.io/rega-coco/autorizar.html?authorization_id=abc'); pg.wait_for_selector('#u')
    pg.fill('#u', 'Dalmar'); pg.fill('#s', 'errada'); pg.click('#ok'); pg.wait_for_selector('.erro')
    print('1 senha errada:', pg.inner_text('.erro'))
    pg.fill('#u', 'Dalmar'); pg.fill('#s', 'certa'); pg.click('#ok')
    if AUT == 'sim':
        pg.wait_for_selector('#sim'); print('2 ecrã:', pg.inner_text('h1'), '|', pg.inner_text('#caixa').split('\n')[2][:90])
        pg.click('#sim'); pg.wait_for_url('https://claude.ai/**'); print('3 foi para:', pg.url)
    else:
        pg.wait_for_selector('#v'); print('2 ecrã:', pg.inner_text('h1')); pg.click('#v'); pg.wait_for_url('https://claude.ai/**'); print('3 foi para:', pg.url)
    print([l for l in log if 'supabase' in l])
    b.close()
