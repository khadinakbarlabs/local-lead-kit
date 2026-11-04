(() => {
  'use strict';
  const key=window.looksyBootstrap.session;
  const $=id=>document.getElementById(id);
  const e=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safe=value=>{try{const url=new URL(value);return ['https:','http:'].includes(url.protocol)&&!url.username&&!url.password?url.href:'';}catch{return '';}};
  const hostname=value=>{try{return new URL(value).hostname.replace(/^www\./,'');}catch{return String(value??'');}};
  const money=value=>Number(value).toLocaleString('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2});
  const readable=value=>String(value??'').replaceAll('_',' ');
  const chip=(value,style='')=>`<span class="chip ${style}">${e(value)}</span>`;
  const link=(url,text)=>safe(url)?`<a href="${e(safe(url))}" target="_blank" rel="noopener noreferrer">${e(text??hostname(url))} ↗</a>`:'Not available';
  const field=(label,value)=>`<div class="field"><span>${e(label)}</span><b>${e(value||'Not available')}</b></div>`;
  const linkField=(label,url,text)=>`<div class="field"><span>${e(label)}</span>${link(url,text)}</div>`;
  let selected='',kind='businesses',offset=0,query='',job=null,rowIndex=0,busy=false;

  function message(text=''){$('message').textContent=text;$('message').hidden=!text;}
  async function api(path,body){
    const options={headers:{'X-Looksy-Key':key}};
    if(body!==undefined){options.method='POST';options.headers['Content-Type']='application/json';options.body=JSON.stringify(body);}
    const response=await fetch(path,options);const result=await response.json();
    if(!response.ok)throw Error(result.error||'The action could not complete.');
    return result;
  }
  function show(name){for(const view of ['create','plan','result'])$(view+'-view').hidden=view!==name;}
  function stat(value,label,text=false){return `<div class="stat ${text?'text':''}"><b>${e(value)}</b><span>${e(label)}</span></div>`;}
  async function listJobs(){
    const data=await api('/api/jobs');$('connection').textContent=data.configured?'Apify configured':'Connection needed';
    $('connection').className='chip '+(data.configured?'':'muted');
    $('saved-jobs').innerHTML='<option value="">Saved campaigns</option>'+data.jobs.map(j=>`<option value="${e(j.id)}">${e(j.request.niche)} · ${e(j.request.locations.join(', '))}</option>`).join('');
    if(selected)$('saved-jobs').value=selected;
    return data.jobs;
  }
  async function loadJob(id,reset=true){
    if(reset){offset=0;rowIndex=0;query='';$('search').value='';}
    selected=id;window.location.hash=id;
    job=await api('/api/job?id='+encodeURIComponent(id)+'&kind='+kind+'&offset='+offset+'&q='+encodeURIComponent(query));
    $('saved-jobs').value=id;
    if(job.status==='PLANNED')renderPlan();else renderResults();
  }
  function renderPlan(){
    show('plan');$('plan-title').textContent=job.request.niche;
    $('plan-summary').innerHTML=stat(job.request.target.toLocaleString(),'Business target')+stat(job.request.locations.length,'Territories')+stat(money(job.request.budget_usd),'Run allowance')+stat(job.request.include_contacts?'Included':'Off','Contact research',true);
    $('plan-copy').innerHTML=`<p>Research <b>${e(job.request.niche)}</b> in <b>${e(job.request.locations.join(' · '))}</b>.</p><p>${e(job.plan.cost_note)}</p><p class="hint">Actual coverage may be lower than the target. Partial results and uncertain addresses stay labeled.</p>`;
    $('source-details').innerHTML='<div class="sources">'+job.plan.actors.map(a=>`<div class="source"><h3>${e(a.slug.split('/')[1].replaceAll('-',' '))}</h3><p>Build ${e(a.build_number)}</p>${link(a.store_url,'Current Actor page')}${Object.entries(a.pricing.events).map(([name,v])=>`<div class="price-row">${e(v.title||name)} · ${e(typeof v.price_usd==='number'?'$'+v.price_usd:'See account pricing')}</div>`).join('')}</div>`).join('')+'</div>';
    $('approve-button').textContent='Approve & start · '+money(job.request.budget_usd)+' allowance';
  }
  function renderResults(){
    show('result');const s=job.summary||{};
    $('result-eyebrow').textContent=job.imported?'READ-ONLY SAVED RUNS':'YOUR CAMPAIGN';
    $('result-title').textContent=job.request.niche+' · '+job.request.locations.join(', ');
    $('result-status').textContent=readable(job.status);$('result-status').className='chip '+(['PARTIAL','ATTENTION','WAITING'].includes(job.status)?'amber':'');
    $('run-message').textContent=(job.progress||{}).message||'Review your campaign.';
    $('run-message').className='run-message '+(job.status==='ATTENTION'?'attention':'');
    $('result-stats').innerHTML=stat(s.businesses??'—','Businesses found')+stat(s.unique_emails??'—','Unique extracted addresses')+stat(job.request.target,'Requested target')+stat(s.partial?'Partial':s.businesses===0?'Empty':'Review','Coverage',true);
    document.querySelectorAll('[data-kind]').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.kind===kind)));
    $('analysis-controls').hidden=kind!=='analysis';$('review-offer').value=$('review-offer').value||job.request.offer||'';
    $('analysis-status').textContent=job.analysis_status==='AWAITING_ASSISTANT'?'Waiting for your active assistant.':['COMPLETE','PARTIAL'].includes(job.analysis_status)?`${s.ai_reviewed||job.total} businesses reviewed.`:'';
    $('export-button').disabled=!job.total;$('resume-button').hidden=!['WAITING','ATTENTION'].includes(job.status)||job.imported;
    renderRows();
  }
  function renderRows(){
    const rows=job.rows||[];
    $('rows').innerHTML=rows.length?rows.map((row,i)=>{
      const title=kind==='contacts'?row.business_name:kind==='analysis'?(row.business_name||(row.note||'').slice(0,100)):row.business_name;
      const sub=kind==='contacts'?row.email:kind==='analysis'?row.confidence:hostname(row.website);
      const status=kind==='contacts'?row.validation_status:kind==='analysis'?'AI note':readable(row.coverage);
      return `<button class="row ${i===rowIndex?'active':''}" data-row="${i}"><span class="row-icon">${kind==='contacts'?'@':kind==='analysis'?'✦':'⌖'}</span><div><strong>${e(title)}</strong><small>${e(sub)}</small></div>${chip(status,kind==='contacts'?'amber':'muted')}</button>`;
    }).join(''):'<div class="empty">'+(kind==='analysis'?'No AI research notes yet. Add your offer and request a review.':'No rows in this view yet. Useful partial results will appear when the stage finishes.')+'</div>';
    $('page-info').textContent=job.total?`${offset+1}–${Math.min(offset+rows.length,job.total)} of ${job.total}`:'0 rows';
    $('previous').disabled=offset===0;$('next').disabled=offset+rows.length>=job.total;
    $('rows').querySelectorAll('[data-row]').forEach(b=>b.addEventListener('click',()=>{rowIndex=Number(b.dataset.row);renderRows();}));
    const row=rows[Math.min(rowIndex,rows.length-1)];
    if(!row){$('detail').innerHTML='<div class="eyebrow">RESEARCH WITH CONTEXT</div><h2>A useful next step starts with evidence.</h2><p class="hint">Keep source context and review uncertain entries before using a list.</p>';return;}
    if(kind==='businesses')$('detail').innerHTML='<div class="eyebrow">SELECTED BUSINESS</div><h2>'+e(row.business_name)+'</h2>'+field('LOCATION',row.address)+field('PHONE',row.phone)+linkField('WEBSITE',row.website)+field('CONTACT RESULT',row.email_count+' addresses · '+readable(row.coverage))+linkField('MAPS SOURCE',row.maps_source,'Open the listing');
    else if(kind==='contacts')$('detail').innerHTML='<div class="eyebrow">CONTACT TO REVIEW</div><h2>'+e(row.email)+'</h2>'+chip(row.validation_status,'amber')+field('BUSINESS',row.business_name)+linkField('SOURCE WEBSITE',row.source_website)+field('CHECK REASONS',readable(row.validation_reason))+field('EXTRACTION REVIEW',readable(row.extraction_review))+'<p class="hint">Source context is not exact per-email page provenance. Individual mailbox deliverability was not confirmed.</p>';
    else $('detail').innerHTML='<div class="eyebrow">AI-ASSISTED RESEARCH NOTE</div><h2>'+e(row.business_name||'Review the evidence.')+'</h2>'+field('NOTE',row.note)+field('CONFIDENCE',row.confidence)+field('NEXT STEP',row.next_step||'Review the business and its sources.')+'<div class="field"><span>SOURCES</span>'+row.sources.map(url=>link(url)).join('<br>')+'</div><p class="hint">A research note does not establish buying intent.</p>';
  }
  async function action(fn){if(busy)return;busy=true;message();try{await fn();}catch(error){message(error.message);}finally{busy=false;document.querySelectorAll('.primary').forEach(b=>b.disabled=false);}}
  $('campaign-form').addEventListener('submit',event=>{event.preventDefault();action(async()=>{
    $('plan-button').disabled=true;$('plan-button').textContent='Checking current sources…';
    const form=new FormData(event.target);const data={niche:form.get('niche'),locations:form.get('locations'),target:Number(form.get('target')),budget_usd:Number(form.get('budget_usd')),include_contacts:form.has('include_contacts'),analysis:form.has('analysis'),offer:form.get('offer')};
    try{const result=await api('/api/plan',data);await listJobs();await loadJob(result.id);}finally{$('plan-button').innerHTML='Review my campaign <span>↗</span>';}
  });});
  document.querySelectorAll('[data-target]').forEach(button=>button.addEventListener('click',()=>{$('target').value=button.dataset.target;document.querySelectorAll('[data-target]').forEach(b=>b.classList.toggle('selected',b===button));}));
  $('target').addEventListener('input',()=>document.querySelectorAll('[data-target]').forEach(b=>b.classList.toggle('selected',Number(b.dataset.target)===Number($('target').value))));
  $('new-button').addEventListener('click',()=>{selected='';job=null;window.location.hash='';$('saved-jobs').value='';message();show('create');});
  $('edit-button').addEventListener('click',()=>show('create'));
  $('saved-jobs').addEventListener('change',()=>{if($('saved-jobs').value)action(()=>loadJob($('saved-jobs').value));});
  $('approve-button').addEventListener('click',()=>action(async()=>{$('approve-button').disabled=true;await api('/api/approve',{id:selected,hash:job.plan.hash});await loadJob(selected,false);}));
  $('resume-button').addEventListener('click',()=>action(async()=>{await api('/api/resume',{id:selected});await loadJob(selected,false);}));
  document.querySelectorAll('[data-kind]').forEach(button=>button.addEventListener('click',()=>action(async()=>{kind=button.dataset.kind;rowIndex=0;offset=0;await loadJob(selected,false);} )));
  let searchTimer;$('search').addEventListener('input',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>action(async()=>{query=$('search').value;offset=0;rowIndex=0;await loadJob(selected,false);}),250);});
  $('previous').addEventListener('click',()=>action(async()=>{offset=Math.max(0,offset-50);rowIndex=0;await loadJob(selected,false);}));
  $('next').addEventListener('click',()=>action(async()=>{offset+=50;rowIndex=0;await loadJob(selected,false);}));
  $('export-button').addEventListener('click',()=>action(async()=>{const response=await fetch('/api/export?id='+selected+'&kind='+kind,{headers:{'X-Looksy-Key':key}});if(!response.ok)throw Error('The export could not be read.');const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download='looksy-'+kind+'.csv';a.click();URL.revokeObjectURL(url);}));
  $('request-analysis').addEventListener('click',()=>action(async()=>{await api('/api/analysis-request',{id:selected,offer:$('review-offer').value});await loadJob(selected,false);}));
  setInterval(()=>{if(selected&&!busy&&job&&(['RUNNING','QUEUED','WAITING'].includes(job.status)||job.analysis_status==='AWAITING_ASSISTANT'))action(()=>loadJob(selected,false));},3500);
  action(async()=>{const jobs=await listJobs();const hash=window.location.hash.slice(1);if(jobs.some(j=>j.id===hash))await loadJob(hash);else if(jobs.length)await loadJob(jobs[0].id);else show('create');});
})();
