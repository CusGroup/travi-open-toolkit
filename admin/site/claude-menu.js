(() => {
  const original = setupMenuBuilder;
  let observer;
  setupMenuBuilder = function () {
    if (observer) observer.disconnect();
    original();
    const form = document.querySelector('#menu-builder');
    const rows = document.querySelector('#menu-rows');
    const tr = (en, vi) => t(en, vi);
    const status = document.createElement('p');status.className='small-note';status.setAttribute('role','status');
    status.textContent=tr('Claude translation: checking configuration…','Dịch với Claude: đang kiểm tra cấu hình…');
    form.prepend(status);
    let configured=false;
    fetch('/api/ai/status').then(r=>{if(!r.ok)throw Error();return r.json()}).then(data=>{
      configured=data.configured===true;
      status.textContent=configured?tr('Claude API configured for an administrator pilot. Drafts require review; translations are never published automatically.','Claude API đã cấu hình cho thử nghiệm quản trị. Bản nháp cần duyệt; không tự xuất bản bản dịch.'):tr('Claude translation is not enabled on this deployment. The menu builder works without AI.','Dịch với Claude chưa bật trên bản triển khai này. Công cụ thực đơn vẫn hoạt động không cần AI.');
      attach();
    }).catch(()=>{status.textContent=tr('Cannot check Claude configuration. Your menu remains editable.','Không kiểm tra được cấu hình Claude. Bạn vẫn chỉnh sửa thực đơn được.');});
    const sample=document.createElement('button');sample.type='button';sample.className='button secondary';sample.textContent=tr('Load example items','Nạp món ví dụ');
    const sampleNote=document.createElement('p');sampleNote.className='small-note';sampleNote.textContent=tr('Examples are for trying the builder, not the café’s official products or prices.','Ví dụ dùng để thử công cụ, không phải món hay giá chính thức của quán.');
    document.querySelector('#add-item').before(sample,sampleNote);
    sample.onclick=()=>{
      if(!confirm(tr('Replace the current draft with two example items? Download your draft first if needed.','Thay bản nháp hiện tại bằng hai món ví dụ? Hãy tải bản nháp trước nếu cần.')))return;
      menuDraft={name:tr('Example café','Quán ví dụ'),phone:'',currency:'VND',items:[{name:'Trà đào',en:'Peach tea',desc:'',descen:'',category:tr('Tea','Trà'),price:'',image:'',available:'yes'},{name:'Cà phê đen',en:'Black coffee',desc:'',descen:'',category:tr('Coffee','Cà phê'),price:'',image:'',available:'yes'}]};
      try{localStorage.setItem('travi-menu-draft',JSON.stringify(menuDraft));}catch{}
      renderLabs();
    };
    function attach(){for(const row of rows.children){
      let button=row.querySelector('.claude-translate');
      if(button){button.disabled=!configured;continue;}
      button=document.createElement('button');button.type='button';button.className='button secondary claude-translate';button.textContent=tr('Translate with Claude · admin pilot','Dịch với Claude · thử nghiệm quản trị');button.disabled=!configured;
      row.append(button);
      button.onclick=async()=>{
        const name=row.querySelector('.item-name').value.trim(),description=row.querySelector('.item-desc').value.trim();
        if(!name){status.textContent=tr('Enter an item name first.','Nhập tên món trước.');return;}
        if(!confirm(tr('Send this item name and description to Anthropic for English translation? No photos, prices or customer information will be sent.','Gửi tên và mô tả món này đến Anthropic để dịch sang tiếng Anh? Không gửi ảnh, giá hay thông tin khách hàng.')))return;
        button.disabled=true;status.textContent=tr('Preparing translation draft…','Đang tạo bản dịch nháp…');
        try{
          const sessionResponse=await fetch('/api/admin/session',{cache:'no-store'});if(!sessionResponse.ok)throw Error(tr('Cannot check admin session.','Không kiểm tra được phiên quản trị.'));
          const session=await sessionResponse.json();
          if(!session.authenticated){status.replaceChildren(document.createTextNode(tr('Administrator login required. ','Cần đăng nhập quản trị. ')));const login=document.createElement('a');login.href='/admin';login.target='_blank';login.rel='noopener';login.textContent=tr('Open admin login, then retry','Mở đăng nhập rồi thử lại');status.append(login);return;}
          const response=await fetch('/api/ai/translate',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':session.csrf},body:JSON.stringify({name,description,consent:true})});
          const result=await response.json();if(!response.ok)throw Error(result.error||tr('Translation failed.','Dịch thất bại.'));
          if(!result.draft||typeof result.draft.name!=='string'||typeof result.draft.description!=='string')throw Error('Invalid draft');
          row.querySelector('.translation-review')?.remove();
          const review=document.createElement('div');review.className='translation-review';
          const heading=document.createElement('h3');heading.textContent=tr('Review the English draft','Kiểm tra bản nháp tiếng Anh');
          const originalText=document.createElement('p');originalText.textContent=tr('Original: ','Bản gốc: ')+name+(description?' — '+description:'');
          const titleLabel=document.createElement('label');titleLabel.textContent=tr('English name','Tên tiếng Anh');const title=document.createElement('input');title.maxLength=100;title.value=result.draft.name;titleLabel.append(title);
          const descLabel=document.createElement('label');descLabel.textContent=tr('English description','Mô tả tiếng Anh');const desc=document.createElement('textarea');desc.maxLength=300;desc.rows=3;desc.value=result.draft.description;descLabel.append(desc);
          const note=document.createElement('p');note.className='small-note';note.textContent=tr('Check names and ingredient facts. Approval updates the draft only; publish separately.','Kiểm tra tên và thông tin nguyên liệu. Duyệt chỉ cập nhật bản nháp; xuất bản riêng.');
          const approve=document.createElement('button');approve.type='button';approve.className='button';approve.textContent=tr('Approve into my draft','Duyệt vào bản nháp');
          const discard=document.createElement('button');discard.type='button';discard.className='remove-item';discard.textContent=tr('Discard','Bỏ bản dịch');discard.onclick=()=>review.remove();
          approve.onclick=()=>{
            if(row.querySelector('.item-name').value.trim()!==name||row.querySelector('.item-desc').value.trim()!==description){status.textContent=tr('Source text changed. Discard and request a new translation.','Nội dung gốc đã đổi. Bỏ và yêu cầu bản dịch mới.');return;}
            if(!title.value.trim()){title.focus();return;}
            row.querySelector('.item-en').value=title.value;row.querySelector('.item-descen').value=desc.value;
            row.querySelector('.item-en').dispatchEvent(new Event('input',{bubbles:true}));review.remove();status.textContent=tr('Translation approved into draft. Review the preview before publishing.','Đã duyệt vào bản nháp. Kiểm tra xem trước rồi mới xuất bản.');
          };
          review.append(heading,originalText,titleLabel,descLabel,note,approve,discard);row.append(review);status.textContent=tr('Draft ready for review. Nothing published.','Bản nháp sẵn sàng kiểm tra. Chưa xuất bản.');
        }catch(error){status.textContent=error.message;}finally{button.disabled=!configured;}
      };
    }}
    attach();observer=new MutationObserver(attach);observer.observe(rows,{childList:true});
  };
})();
