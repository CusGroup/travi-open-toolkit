from published import post_menu
import os,json,sqlite3,secrets,hashlib,hmac,time,base64,re
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from http.cookies import SimpleCookie
from pathlib import Path
ROOT=Path(__file__).parent/'site'; DATA=Path(os.environ.get('DATA_DIR','/data')); DATA.mkdir(parents=True,exist_ok=True); (DATA/'uploads').mkdir(exist_ok=True)
PASSWORD=os.environ['ADMIN_PASSWORD']; USER=os.environ.get('ADMIN_USER','admin'); SALT=os.urandom(16)
HASH=hashlib.scrypt(PASSWORD.encode(),salt=SALT,n=16384,r=8,p=1); del PASSWORD
sessions={}; attempts={}; publish_buckets={}
def db():
 c=sqlite3.connect(DATA/'menu.sqlite'); c.row_factory=sqlite3.Row; return c
with db() as c:
 c.execute('CREATE TABLE IF NOT EXISTS published_menus (id TEXT PRIMARY KEY, secret TEXT NOT NULL, content TEXT NOT NULL)')
 c.execute('CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL, price INTEGER NOT NULL, description TEXT NOT NULL, image TEXT NOT NULL, available INTEGER NOT NULL, visible INTEGER NOT NULL, position INTEGER NOT NULL)')
DEFAULT_SETTINGS={'brand': 'Demo Café', 'tagline': 'Your neighborhood café', 'phone': '', 'email': '', 'address': '', 'company': '', 'company_en': '', 'tax': '', 'activity_date': '', 'hero_title': 'Welcome to Demo Café', 'hero_subtitle': 'Customize this page in the admin panel.', 'hero2_title': 'Make yourself at home', 'story_title': 'Our story', 'story_body': 'Add your own café story here.', 'menu_intro': 'Contact us for availability and prices.', 'logo': '/assets/placeholder.svg', 'hero_image': '/assets/placeholder.svg', 'space_image': '/assets/placeholder.svg', 'primary_color': '#114e2e', 'header_color': '#101510', 'show_story': True, 'show_menu': True, 'show_gallery': True, 'show_store': True}
def settings():
 with db() as c:
  row=c.execute("SELECT value FROM settings WHERE key='website'").fetchone()
 return dict(DEFAULT_SETTINGS,**(json.loads(row[0]) if row else {}))
with db() as c:
 c.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY,value TEXT NOT NULL)')
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**k): super().__init__(*a,directory=str(ROOT),**k)
 def log_message(self,fmt,*args): pass
 def end_headers(self):
  self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Referrer-Policy','same-origin'); self.send_header('X-Frame-Options','SAMEORIGIN'); super().end_headers()
 def reply(self,status,data,headers={}):
  raw=json.dumps(data,ensure_ascii=False).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(raw)))
  for k,v in headers.items(): self.send_header(k,v)
  self.end_headers(); self.wfile.write(raw)
 def auth(self):
  cookie=SimpleCookie()
  try: cookie.load(self.headers.get('Cookie','')); token=cookie.get('travi_session'); s=sessions.get(token.value if token else '')
  except Exception: return None
  return s if s and s['expires']>time.time() else None
 def do_GET(self):
  path=self.path.split('?')[0]
  if re.fullmatch(r'/m/[a-f0-9]{24}',path): self.path='/published-menu.html'
  if re.fullmatch(r'/api/published/[a-f0-9]{24}',path):
   with db() as c: row=c.execute('SELECT content FROM published_menus WHERE id=?',(path.rsplit('/',1)[1],)).fetchone()
   return self.reply(200,json.loads(row['content'])) if row else self.reply(404,{'error':'Menu not found'})
  if path=='/api/menu-qr':
   from urllib.parse import parse_qs,urlsplit
   ident=parse_qs(urlsplit(self.path).query).get('id',[''])[0]
   if not re.fullmatch(r'[a-f0-9]{24}',ident):return self.reply(400,{'error':'Invalid ID'})
   import qrcode,qrcode.image.svg,io
   host=os.environ.get('PUBLIC_BASE_URL','http://localhost:8080').rstrip('/')
   qr=qrcode.make(host+'/m/'+ident,image_factory=qrcode.image.svg.SvgPathImage); out=io.BytesIO();qr.save(out);raw=out.getvalue()
   self.send_response(200);self.send_header('Content-Type','image/svg+xml');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
  if path in ['/api/settings','/api/admin/settings']:
   if path.startswith('/api/admin/') and not self.auth(): return self.reply(401,{'error':'Vui lòng đăng nhập'})
   return self.reply(200,settings())
  if path=='/api/menu' or path=='/api/admin/products':
   if path.endswith('products') and not self.auth(): return self.reply(401,{'error':'Vui lòng đăng nhập'})
   with db() as c: rows=c.execute('SELECT * FROM products '+('WHERE visible=1 ' if path=='/api/menu' else '')+'ORDER BY position,id').fetchall()
   return self.reply(200,[dict(r) for r in rows])
  if path=='/api/admin/session':
   s=self.auth(); return self.reply(200,{'authenticated':bool(s),'csrf':s['csrf'] if s else ''})
  if path in ['/admin','/admin/']: self.path='/admin.html'
  if path.startswith('/uploads/'):
   name=path.removeprefix('/uploads/')
   if '/' in name or '..' in name: return self.reply(404,{'error':'Không tìm thấy'})
   file=DATA/'uploads'/name
   if not file.is_file(): return self.reply(404,{'error':'Không tìm thấy'})
   raw=file.read_bytes(); self.send_response(200); self.send_header('Content-Type','image/png' if name.endswith('.png') else 'image/jpeg' if name.endswith('.jpg') else 'image/webp'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw); return
  super().do_GET()
 def do_POST(self):
  try: self.post()
  except (ValueError,KeyError,TypeError): self.reply(400,{'error':'Dữ liệu không hợp lệ'})
  except Exception: self.reply(500,{'error':'Không thể lưu. Thử lại hoặc kiểm tra máy chủ.'})
 def post(self):
  # Reject cross-origin writes, including login.
  origin=self.headers.get('Origin')
  if origin and origin not in ['https://'+self.headers.get('Host',''),'http://'+self.headers.get('Host','')]: return self.reply(403,{'error':'Yêu cầu không hợp lệ'})
  size=int(self.headers.get('Content-Length','0'))
  if size<1 or size>8_000_000: return self.reply(413,{'error':'Ảnh hoặc dữ liệu quá lớn'})
  body=json.loads(self.rfile.read(size)); path=self.path
  if path in ['/api/published/save','/api/published/delete']:return post_menu(self,body,path,db,publish_buckets)
  if path=='/api/admin/login':
   ip=self.client_address[0]; now=time.time(); bucket=[t for t in attempts.get(ip,[]) if now-t<900]; attempts[ip]=bucket
   if len(bucket)>=10: return self.reply(429,{'error':'Thử lại sau 15 phút'})
   bucket.append(now)
   candidate=hashlib.scrypt(str(body.get('password','')).encode(),salt=SALT,n=16384,r=8,p=1)
   if body.get('username')!=USER or not hmac.compare_digest(candidate,HASH): return self.reply(401,{'error':'Sai tài khoản hoặc mật khẩu'})
   attempts[ip]=[]; sessions.update({k:v for k,v in list(sessions.items()) if v['expires']>now})
   for k in list(sessions):
    if sessions[k]['expires']<=now: del sessions[k]
   token=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(32); sessions[token]={'csrf':csrf,'expires':now+28800}
   secure='; Secure' if os.environ.get('COOKIE_SECURE','1')=='1' else ''
   return self.reply(200,{'csrf':csrf},{'Set-Cookie':f'travi_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800{secure}'})
  s=self.auth()
  if not s: return self.reply(401,{'error':'Vui lòng đăng nhập lại'})
  if not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),s['csrf']): return self.reply(403,{'error':'Phiên không hợp lệ'})
  if path=='/api/admin/settings':
   values=settings()
   for key,value in body.items():
    if key not in DEFAULT_SETTINGS: raise ValueError()
    if isinstance(DEFAULT_SETTINGS[key],bool):
     if not isinstance(value,bool): raise ValueError()
    else:
     if not isinstance(value,str) or len(value)>5000: raise ValueError()
     if key.endswith('_color') and not re.fullmatch(r'#[0-9a-fA-F]{6}',value): raise ValueError()
     if key in ['logo','hero_image','space_image'] and not re.fullmatch(r'/(?:assets|uploads)/[a-zA-Z0-9_.-]+',value): raise ValueError()
     if key=='phone' and not re.fullmatch(r'\+?[0-9 ()-]{6,24}',value): raise ValueError()
     if key=='email' and not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',value): raise ValueError()
    values[key]=value
   with db() as c: c.execute('INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)',('website',json.dumps(values,ensure_ascii=False)))
   return self.reply(200,{'ok':True})
  if path=='/api/admin/logout':
   cookie=SimpleCookie(self.headers.get('Cookie')); sessions.pop(cookie['travi_session'].value,None); return self.reply(200,{'ok':True},{'Set-Cookie':'travi_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0; Secure'})
  if path=='/api/admin/upload':
   raw=base64.b64decode(body['data'],validate=True)
   if len(raw)>5_000_000: return self.reply(413,{'error':'Ảnh tối đa 5 MB'})
   ext='.png' if raw.startswith(b'\x89PNG\r\n\x1a\n') else '.jpg' if raw.startswith(b'\xff\xd8\xff') else '.webp' if raw[:4]==b'RIFF' and raw[8:12]==b'WEBP' else None
   if not ext: return self.reply(400,{'error':'Chỉ nhận ảnh PNG, JPG, WEBP'})
   name=secrets.token_hex(16)+ext; (DATA/'uploads'/name).write_bytes(raw); return self.reply(200,{'url':'/uploads/'+name})
  if path=='/api/admin/delete':
   with db() as c: c.execute('DELETE FROM products WHERE id=?',(int(body['id']),))
   return self.reply(200,{'ok':True})
  if path=='/api/admin/save':
   name=str(body['name']).strip(); category=str(body['category']).strip(); price=int(body.get('price') or 0); description=str(body.get('description','')); image=str(body.get('image','')); position=int(body.get('position',0))
   if not name or len(name)>160 or not category or len(category)>80 or price<0 or price>100_000_000 or len(description)>2000: raise ValueError()
   if image and not (image.startswith('/uploads/') or image in ['/assets/travi_menu.jpg','/assets/travi.jpg']): raise ValueError()
   values=(name,category,price,description,image,int(bool(body.get('available'))),int(bool(body.get('visible'))),position)
   with db() as c:
    if body.get('id'):
     cursor=c.execute('UPDATE products SET name=?,category=?,price=?,description=?,image=?,available=?,visible=?,position=? WHERE id=?',values+(int(body['id']),))
     if not cursor.rowcount: return self.reply(404,{'error':'Món không còn tồn tại'})
    else: c.execute('INSERT INTO products(name,category,price,description,image,available,visible,position) VALUES(?,?,?,?,?,?,?,?)',values)
   return self.reply(200,{'ok':True})
  self.reply(404,{'error':'Không tìm thấy'})
ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()
