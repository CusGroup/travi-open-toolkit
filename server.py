import os,json,sqlite3,re,io
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import parse_qs,urlsplit
from published import post_menu
DATA=Path(os.environ.get('DATA_DIR','/data'));DATA.mkdir(parents=True,exist_ok=True)
ROOT=Path(__file__).parent/'site';buckets={}
def db():
 c=sqlite3.connect(DATA/'menus.sqlite');c.row_factory=sqlite3.Row;return c
with db() as c:c.execute('CREATE TABLE IF NOT EXISTS published_menus(id TEXT PRIMARY KEY,secret TEXT NOT NULL,content TEXT NOT NULL)')
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**k):super().__init__(*a,directory=str(ROOT),**k)
 def log_message(self,*a):pass
 def end_headers(self):
  self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');super().end_headers()
 def reply(self,status,data):
  raw=json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  path=urlsplit(self.path).path
  if re.fullmatch(r'/m/[a-f0-9]{24}',path):self.path='/published-menu.html'
  if re.fullmatch(r'/api/published/[a-f0-9]{24}',path):
   with db() as c:r=c.execute('SELECT content FROM published_menus WHERE id=?',(path.rsplit('/',1)[1],)).fetchone()
   return self.reply(200,json.loads(r['content'])) if r else self.reply(404,{'error':'Menu not found'})
  if path=='/api/menu-qr':
   ident=parse_qs(urlsplit(self.path).query).get('id',[''])[0]
   if not re.fullmatch(r'[a-f0-9]{24}',ident):return self.reply(400,{'error':'Invalid ID'})
   import qrcode,qrcode.image.svg
   image=qrcode.make(os.environ.get('PUBLIC_BASE_URL','http://localhost:8080').rstrip('/')+'/m/'+ident,image_factory=qrcode.image.svg.SvgPathImage);stream=io.BytesIO();image.save(stream);raw=stream.getvalue()
   self.send_response(200);self.send_header('Content-Type','image/svg+xml');self.send_header('Content-Length',str(len(raw)));self.end_headers();return self.wfile.write(raw)
  super().do_GET()
 def do_POST(self):
  origin=self.headers.get('Origin');host=self.headers.get('Host','')
  if origin and origin not in ['https://'+host,'http://'+host]:return self.reply(403,{'error':'Invalid origin'})
  try:
   if self.path not in ['/api/published/save','/api/published/delete']:return self.reply(404,{'error':'Not found'})
   size=int(self.headers.get('Content-Length','0'))
   if not 1<=size<=8000000:return self.reply(413,{'error':'Payload too large'})
   return post_menu(self,json.loads(self.rfile.read(size)),self.path,db,buckets)
  except (ValueError,TypeError,KeyError):self.reply(400,{'error':'Invalid menu'})
  except Exception:self.reply(500,{'error':'Unable to save menu'})
if __name__=='__main__':ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()
