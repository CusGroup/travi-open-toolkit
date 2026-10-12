import sys,os,json,time,tempfile,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import claude_menu as ai
class TranslationTests(unittest.TestCase):
 def test_input_and_consent(self):
  self.assertEqual(ai.validate({'consent':True,'name':'Trà đào','description':''})['name'],'Trà đào')
  for body in [{'consent':False,'name':'Tea'}, {'consent':True,'name':'x'*101}, {'consent':True,'name':[]}]:
   with self.assertRaises(ValueError):ai.validate(body)
 def test_provider_draft(self):
  captured=[]
  class Response:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self,n):return json.dumps({'stop_reason':'tool_use','content':[{'type':'tool_use','name':'submit_translation','input':{'name':'Peach tea','description':'Invented extra fact'}}]}).encode()
  def opener(req,timeout):captured.append(req);return Response()
  with patch.dict(os.environ,{'ANTHROPIC_API_KEY':'sk-ant-test','ANTHROPIC_MODEL':'model-test'}):
   out=ai.translate({'name':'Trà đào','description':''},opener)
  self.assertEqual(out,{'name':'Peach tea','description':''})
  payload=json.loads(captured[0].data)
  self.assertEqual(json.loads(payload['messages'][0]['content']),{'name':'Trà đào','description':''})
  self.assertNotIn('sk-ant-test',captured[0].data.decode())
 def test_persistent_limit(self):
  with tempfile.TemporaryDirectory() as d,patch('claude_menu.time.time',return_value=123456):
   self.assertTrue(ai.reserve(Path(d)));self.assertTrue(ai.reserve(Path(d)));self.assertTrue(ai.reserve(Path(d)))
   self.assertFalse(ai.reserve(Path(d)))
 def test_http_auth_config_and_csrf(self):
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_GET(self):self.reply(404,{})
   def do_POST(self):self.reply(404,{})
   def auth(self):return {'csrf':'test-csrf'} if self.headers.get('Cookie')=='session=test' else None
   def reply(self,status,data,headers=None):
    raw=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
    for k,v in (headers or {}).items():self.send_header(k,v)
    self.end_headers();self.wfile.write(raw)
  with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'TRAVI_AI_ENABLED':'0'}):
   ai.install(Handler,Path(d));server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
   thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   base=f'http://127.0.0.1:{server.server_port}'
   def post(headers):
    req=urllib.request.Request(base+'/api/ai/translate',data=b'{"consent":true,"name":"Tea"}',headers=headers)
    try:
     with urllib.request.urlopen(req) as r:return r.status,json.load(r)
    except urllib.error.HTTPError as e:return e.code,json.load(e)
   try:
    with urllib.request.urlopen(base+'/api/ai/status') as r:self.assertFalse(json.load(r)['configured'])
    self.assertEqual(post({'Origin':base})[0],401)
    self.assertEqual(post({'Origin':'https://evil.example','Cookie':'session=test'})[0],403)
    self.assertEqual(post({'Origin':base,'Cookie':'session=test','X-CSRF-Token':'wrong'})[0],403)
    headers={'Origin':base,'Cookie':'session=test','X-CSRF-Token':'test-csrf'}
    self.assertEqual(post(headers)[0],503)
    with patch.dict(os.environ,{'TRAVI_AI_ENABLED':'1','ANTHROPIC_API_KEY':'sk-ant-test','ANTHROPIC_MODEL':'test'}),patch('claude_menu.translate',return_value={'name':'Tea','description':''}):
     status,result=post(headers);self.assertEqual(status,200);self.assertTrue(result['review_required']);self.assertEqual(result['provider'],'Claude')
   finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':unittest.main()
