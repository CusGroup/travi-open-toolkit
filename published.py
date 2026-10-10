import json,re,secrets,hashlib,hmac,time
from urllib.parse import urlparse

def validate_menu(menu):
 if not isinstance(menu,dict):raise ValueError()
 for k,limit in [('name',100),('phone',30)]:
  if not isinstance(menu.get(k,''),str) or len(menu.get(k,''))>limit:raise ValueError()
 if not menu.get('name','').strip() or menu.get('currency') not in ['VND','USD','EUR','GBP']:raise ValueError()
 items=menu.get('items')
 if not isinstance(items,list) or not 1<=len(items)<=30:raise ValueError()
 clean={'name':menu['name'],'phone':menu.get('phone',''),'currency':menu['currency'],'items':[]}
 for item in items:
  row={}
  for key,limit in [('name',100),('en',100),('desc',300),('descen',300),('category',80),('price',30),('image',2800000),('available',3)]:
   value=item.get(key,'yes' if key=='available' else '')
   if not isinstance(value,str) or len(value)>limit:raise ValueError()
   row[key]=value
  if not row['name'].strip() or row['available'] not in ['yes','no']:raise ValueError()
  if row['price'] and (not re.fullmatch(r'\d+(?:\.\d{1,2})?',row['price']) or float(row['price'])>1e9):raise ValueError()
  image=row['image']
  if image:
   u=urlparse(image)
   if not (u.scheme=='https' and u.netloc and not u.username and not u.password) and not re.fullmatch(r'data:image/(?:png|jpeg|webp);base64,[A-Za-z0-9+/=]+',image):raise ValueError()
  clean['items'].append(row)
 if len(json.dumps(clean).encode())>7000000:raise ValueError()
 return clean

def post_menu(handler,body,path,db,buckets):
 ident=body.get('id','');key=body.get('key','')
 if ident:
  if not isinstance(ident,str) or not re.fullmatch(r'[a-f0-9]{24}',ident) or not isinstance(key,str):raise ValueError()
  with db() as c:r=c.execute('SELECT secret FROM published_menus WHERE id=?',(ident,)).fetchone()
  if not r or not hmac.compare_digest(r['secret'],hashlib.sha256(key.encode()).hexdigest()):return handler.reply(403,{'error':'Invalid edit key / Khóa chỉnh sửa không hợp lệ'})
 if path=='/api/published/delete':
  if not ident:raise ValueError()
  with db() as c:c.execute('DELETE FROM published_menus WHERE id=?',(ident,))
  return handler.reply(200,{'ok':True})
 menu=validate_menu(body['menu'])
 with db() as c:
  if not ident:
   now=time.time();ip=handler.client_address[0];recent=[v for v in buckets.get(ip,[]) if v>now-3600]
   if len(recent)>=5:return handler.reply(429,{'error':'Please retry later / Vui lòng thử lại sau'})
   if c.execute('SELECT count(*) FROM published_menus').fetchone()[0]>=500:return handler.reply(429,{'error':'Publishing capacity reached / Đã đạt giới hạn lưu trữ'})
   recent.append(now);buckets[ip]=recent;ident=secrets.token_hex(12);key=secrets.token_urlsafe(32)
   c.execute('INSERT INTO published_menus(id,secret,content) VALUES(?,?,?)',(ident,hashlib.sha256(key.encode()).hexdigest(),json.dumps(menu,ensure_ascii=False)))
  else:c.execute('UPDATE published_menus SET content=? WHERE id=?',(json.dumps(menu,ensure_ascii=False),ident))
 return handler.reply(200,{'id':ident,'key':key,'url':'/m/'+ident})
