(function(root){
 'use strict';
 function parseCSV(text,delimiter=','){
  if(![',',';','\t'].includes(delimiter))throw Error('Invalid delimiter');
  text=text.replace(/^\uFEFF/,'');let rows=[],row=[],field='',quoted=false,closed=false;
  const push=()=>{row.push(field);field='';closed=false;};
  const finish=()=>{push();if(row.some(x=>x.trim()!==''))rows.push(row);row=[];if(rows.length>5001)throw Error('Maximum 5000 data records');};
  for(let i=0;i<text.length;i++){
   const c=text[i];
   if(quoted){if(c==='"'){if(text[i+1]==='"'){field+='"';i++;}else{quoted=false;closed=true;}}else field+=c;continue;}
   if(c==='"'){if(field!==''||closed)throw Error('Unexpected quote');quoted=true;continue;}
   if(c===delimiter){push();continue;}
   if(c==='\r'||c==='\n'){if(c==='\r'&&text[i+1]==='\n')i++;finish();continue;}
   if(closed)throw Error('Unexpected text after closing quote');field+=c;
  }
  if(quoted)throw Error('Unclosed quoted field');if(field!==''||row.length||closed)finish();return rows;
 }
 function money(value){
  value=value.trim();if(!/^\d+(\.\d{1,2})?$/.test(value))throw Error('unit_price must use a decimal point, no thousands separators');
  const [whole,decimal='']=value.split('.');const n=Number(whole)*100+Number(decimal.padEnd(2,'0'));
  if(!Number.isSafeInteger(n)||n>100000000000)throw Error('unit_price out of range');return n;
 }
 function analyze(text,delimiter=','){
  const rows=parseCSV(text,delimiter);if(rows.length<2)throw Error('Include a header and at least one data record');
  const headers=rows.shift().map(x=>x.trim().toLowerCase());if(new Set(headers).size!==headers.length)throw Error('Duplicate column names');
  const index=Object.fromEntries(['date','item','quantity','unit_price'].map(k=>{const i=headers.indexOf(k);if(i<0)throw Error('Missing column: '+k);return[k,i];}));
  const entries=[];const products=new Map(),days=new Map();let total=0,quantity=0;
  rows.forEach((row,i)=>{
   try{
    if(row.length!==headers.length)throw Error('Column count does not match header');
    const date=row[index.date].trim(),item=row[index.item].trim(),q=row[index.quantity].trim();
    if(!/^\d{4}-\d{2}-\d{2}$/.test(date))throw Error('date must be YYYY-MM-DD');
    const parsed=new Date(date+'T00:00:00Z');if(!Number.isFinite(+parsed)||parsed.toISOString().slice(0,10)!==date)throw Error('Invalid calendar date');
    if(!item||item.length>100)throw Error('item must contain 1–100 characters');
    if(!/^\d+$/.test(q)||Number(q)<1||Number(q)>1000000)throw Error('quantity must be a positive integer, maximum 1000000');
    const qty=Number(q),price=money(row[index.unit_price]),amount=qty*price;
    if(!Number.isSafeInteger(amount)||!Number.isSafeInteger(total+amount))throw Error('Revenue exceeds safe calculation limit');
    entries.push({date,item,quantity:qty,revenue_cents:amount});total+=amount;quantity+=qty;
    const p=products.get(item)||{item,quantity:0,revenue_cents:0};p.quantity+=qty;p.revenue_cents+=amount;products.set(item,p);
    const day=days.get(date)||{date,quantity:0,revenue_cents:0};day.quantity+=qty;day.revenue_cents+=amount;days.set(date,day);
   }catch(e){throw Error('Record '+(i+2)+': '+e.message);}
  });
  const daily=[...days.values()].sort((a,b)=>a.date.localeCompare(b.date));
  return {entries,records:rows.length,quantity,revenue_cents:total,start:daily[0].date,end:daily.at(-1).date,products:[...products.values()].sort((a,b)=>b.revenue_cents-a.revenue_cents||a.item.localeCompare(b.item)),daily};
 }
 function validDate(s){if(!/^\d{4}-\d{2}-\d{2}$/.test(s||''))return false;const d=new Date(s+'T00:00:00Z');return Number.isFinite(+d)&&d.toISOString().slice(0,10)===s;}
 function summarize(entries,from,to){
  if(!validDate(from)||!validDate(to)||from>to)throw Error('Choose a valid date range');
  const products=new Map(),days=new Map();let revenue=0,quantity=0,records=0;
  for(const e of entries){if(e.date<from||e.date>to)continue;revenue+=e.revenue_cents;quantity+=e.quantity;records++;const p=products.get(e.item)||{item:e.item,quantity:0,revenue_cents:0};p.quantity+=e.quantity;p.revenue_cents+=e.revenue_cents;products.set(e.item,p);const d=days.get(e.date)||{date:e.date,quantity:0,revenue_cents:0};d.quantity+=e.quantity;d.revenue_cents+=e.revenue_cents;days.set(e.date,d);}
  const daily=[...days.values()].sort((a,b)=>a.date.localeCompare(b.date));
  return{start:from,end:to,records,quantity,revenue_cents:revenue,observed_days:daily.length,calendar_days:(Date.parse(to+'T00:00:00Z')-Date.parse(from+'T00:00:00Z'))/86400000+1,average_unit_price_cents:quantity?revenue/quantity:null,products:[...products.values()].sort((a,b)=>b.revenue_cents-a.revenue_cents||b.quantity-a.quantity||a.item.localeCompare(b.item)),daily};
 }
 function compare(current,previous){
  if(!(current.end<previous.start||previous.end<current.start))throw Error('Comparison periods must not overlap');
  if(!current.records||!previous.records)throw Error('Each comparison period needs supplied records');
  const change=(a,b)=>({absolute:a-b,percent:b===0?null:(a-b)/b*100});
  return{current,previous,revenue_change:change(current.revenue_cents,previous.revenue_cents),quantity_change:change(current.quantity,previous.quantity),same_calendar_length:current.calendar_days===previous.calendar_days};
 }
 const api={parseCSV,analyze,summarize,compare};if(typeof module==='object'&&module.exports)module.exports=api;else root.TraviSales=api;
})(typeof globalThis==='undefined'?this:globalThis);
