(() => {
 let language='en';try{language=localStorage.getItem('travi-labs-language')==='vi'?'vi':'en';}catch{}
 let result=null,source='',fictional=false,requestId=0;
 const el=id=>document.getElementById(id), t=(a,b)=>language==='vi'?b:a;
 const money=cents=>new Intl.NumberFormat(language==='vi'?'vi-VN':'en-US',{style:'currency',currency:el('currency').value,maximumFractionDigits:2}).format(cents/100);
 function row(target,values){const tr=document.createElement('tr');for(const v of values){const td=document.createElement('td');td.textContent=String(v);tr.append(td);}target.append(tr);}
 function render(){
  document.documentElement.lang=language;document.querySelectorAll('[data-en]').forEach(e=>e.textContent=e.dataset[language]);el('language').textContent=language==='en'?'VI / EN':'EN / VI';
  el('results').hidden=!result;if(!result)return;
  el('source').textContent=(fictional?t('FICTIONAL SAMPLE — not TRAVI sales. ','DỮ LIỆU GIẢ LẬP — không phải doanh số TRAVI. '):t('Uploaded file: ','File đã chọn: '))+source+' · '+result.start+' → '+result.end;
  el('revenue').textContent=money(result.revenue_cents);el('quantity').textContent=result.quantity.toLocaleString();el('records').textContent=result.records.toLocaleString();
  el('products').replaceChildren();el('days').replaceChildren();
  for(const p of result.products)row(el('products'),[p.item,p.quantity,money(p.revenue_cents)]);
  for(const d of result.daily)row(el('days'),[d.date,d.quantity,money(d.revenue_cents)]);
 }
 function analyze(text,label,sample){
  const parsed=TraviSales.analyze(text,el('delimiter').value==='tab'?'\t':el('delimiter').value);
  result=parsed;source=label;fictional=sample;render();el('status').textContent=t('Calculated locally. No AI or upload used.','Đã tính trong trình duyệt. Không dùng AI hay upload.');
 }
 function clear(){requestId++;result=null;source='';fictional=false;el('csv-file').value='';el('status').textContent='';el('products').replaceChildren();el('days').replaceChildren();el('revenue').textContent='';el('quantity').textContent='';el('records').textContent='';el('source').textContent='';render();}
 el('csv-file').onchange=async()=>{
  const file=el('csv-file').files[0];if(!file)return;const ticket=++requestId;result=null;render();
  if(file.size>1024*1024){el('status').textContent=t('File exceeds 1 MB.','File vượt quá 1 MB.');return;}
  try{const text=await file.text();if(ticket!==requestId)return;analyze(text,file.name,false);}catch(error){if(ticket===requestId)el('status').textContent=t('Cannot calculate: ','Không tính được: ')+error.message;}
 };
 el('sample').onclick=()=>{requestId++;el('delimiter').value=',';el('currency').value='VND';el('csv-file').value='';analyze('date,item,quantity,unit_price\n2026-10-01,Example tea,4,35000\n2026-10-01,Example coffee,2,30000\n2026-10-02,Example tea,3,35000\n2026-10-02,Example coffee,3,30000',t('4 fictional records','4 bản ghi giả lập'),true);};
 el('delimiter').onchange=()=>{if(result)el('status').textContent=t('Choose your file again to apply the new separator.','Chọn lại file để áp dụng dấu phân cách mới.');};
 el('currency').onchange=render;
 el('clear').onclick=clear;
 el('language').onclick=()=>{language=language==='en'?'vi':'en';try{localStorage.setItem('travi-labs-language',language);}catch{}render();el('status').textContent='';};
 el('export').onclick=()=>{
  if(!result)return;
  const report={...result,currency:el('currency').value,fictional_sample:fictional,calculation:'quantity * unit_price; money values are in hundredths of the selected currency',limitations:'No separate discounts, refunds, tax or cost accounting. Missing dates are not assumed to be zero. No AI inference.',generated_at:new Date().toISOString()};
  const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='travi-sales-report.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 };
 render();
})();
