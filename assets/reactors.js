/* Progressive enhancement; the static first page works without JS. */
(() => {
  'use strict';
  const board = document.body.dataset.reactorBoard;
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? 'Unknown').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let records = [], page = 1;
  const pageSize = 10;
  const fields = pairs => '<dl>' + pairs.map(([k,v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('') + '</dl>';
  const capacity = v => v === null ? 'Unknown' : `${v.toLocaleString('en-US')} MWe`;
  function card(r) {
    const statusLabel = r.status + (r.businessState && r.businessState !== 'Active' && r.businessState !== 'Unknown' ? ` · ${r.businessState}` : '');
    const freshness = r.verification === 'PRIS inventory fields' ? `PRIS fields checked: ${r.verifiedOn}` : r.verifiedOn ? `${r.verification} · checked ${r.verifiedOn}` : `Baseline only · source review: ${r.baselineReviewed} · not revalidated`;
    const detail = [['Facility scope',r.scope],['Project state',r.businessState],['Operator',r.operator],['Gross capacity',capacity(r.grossMWe)],['Construction date',r.constructionDate],['First grid connection',r.gridDate],['Commercial operation',r.commercialDate],['Baseline review',r.baselineReviewed],['Source observation date',r.sourceAsOf || 'See linked source'],['Site coordinates reviewed',r.coordinates ? r.coordinateAsOf : 'Not mapped']];
    const links = r.sources.filter(s => /^https?:\/\//.test(s.url)).map(s => `<li><a href="${esc(s.url)}" rel="noopener">${esc(s.title)}</a></li>`).join('');
    return `<article class="reactor-record"><div class="record-heading"><h3>${esc(r.name)}</h3><span class="status-tag">${esc(statusLabel)}</span></div><p class="freshness ${r.verifiedOn ? 'checked' : 'baseline'}">${esc(freshness)}</p>${fields([['Country',r.country],['Technology',r.model || r.type],['Net capacity',capacity(r.netMWe)],['Record unit',r.rowUnit]])}<details><summary>Details &amp; sources</summary>${r.statusNote ? `<p>${esc(r.statusNote)}</p>` : ''}${fields(detail)}<ul>${links}</ul></details></article>`;
  }
  function selected() {
    const query = $('reactor-search').value.trim().toLocaleLowerCase(), country = $('reactor-country').value, status = $('reactor-status').value, evidence = $('reactor-evidence').value;
    return records.filter(r => (!country || r.country === country) && (!status || r.status === status) && (!evidence || (evidence === 'current' ? !!r.verifiedOn : !r.verifiedOn)) && (!query || [r.name,r.site,r.country,r.model,r.type,r.operator,r.id].join(' ').toLocaleLowerCase().includes(query)));
  }
  const xy = ([lat,lon]) => [(lon+180)*1000/360,(84-lat)*440/144];
  let mapGroups = [], view = {x:0,y:0,w:1000,h:440};
  const mapSvg = () => $('reactor-map').querySelector('svg');
  function closeInfo() { $('map-info').hidden = true; }
  function showInfo(index) {
    const group = mapGroups[index]; if(!group) return;
    $('map-info-body').innerHTML = `<h3>${group.length===1?'Reactor overview':`${group.length} records at this location`}</h3>` + group.map(r => `<section><strong>${esc(r.name)}</strong><p>${esc(r.country)} · ${esc(r.status)}${r.businessState && !['Active','Unknown'].includes(r.businessState)?' · '+esc(r.businessState):''}</p><p>${esc(r.model || r.type || 'Technology unknown')} · Net: ${capacity(r.netMWe)}</p><small>${r.verifiedOn?'Checked: '+esc(r.verifiedOn):'Baseline only · '+esc(r.baselineReviewed)}</small></section>`).join('');
    $('map-info').hidden = false;
  }
  function updateView() {
    view.x = Math.max(0,Math.min(1000-view.w,view.x)); view.y = Math.max(0,Math.min(440-view.h,view.y));
    mapSvg().setAttribute('viewBox',`${view.x} ${view.y} ${view.w} ${view.h}`);
    $('map-zoom-level').textContent = `${(1000/view.w).toFixed(1)}×`;
    $('map-zoom-in').disabled = view.w<=125; $('map-zoom-out').disabled = view.w>=1000;
    for(const marker of $('map-points').children) marker.setAttribute('r',4.5*view.w/1000);
  }
  function zoom(factor,center) {
    const w=Math.max(125,Math.min(1000,view.w/factor)), ratio=w/view.w;
    const c=center || {x:view.x+view.w/2,y:view.y+view.h/2};
    view={x:c.x-(c.x-view.x)*ratio,y:c.y-(c.y-view.y)*ratio,w,h:w*.44};updateView();
  }
  function setupMap() {
    const svg=mapSvg(); let drag=null, moved=false;
    const position=e=>{const p=svg.createSVGPoint();p.x=e.clientX;p.y=e.clientY;return p.matrixTransform(svg.getScreenCTM().inverse());};
    $('map-zoom-in').addEventListener('click',()=>zoom(1.5));
    $('map-zoom-out').addEventListener('click',()=>zoom(1/1.5));
    $('map-reset').addEventListener('click',()=>{view={x:0,y:0,w:1000,h:440};updateView();closeInfo();});
    $('map-info-close').addEventListener('click',()=>{closeInfo();svg.focus({preventScroll:true});});
    const reveal=e=>{const marker=e.target.closest('[data-site]');if(marker)showInfo(Number(marker.dataset.site));};
    svg.addEventListener('pointerover',reveal);svg.addEventListener('focusin',reveal);
    svg.addEventListener('click',e=>{if(!moved)reveal(e);});
    svg.addEventListener('keydown',e=>{
      if(e.key==='Escape'){closeInfo();return;}
      if((e.key==='Enter'||e.key===' ') && e.target.matches('[data-site]')){e.preventDefault();reveal(e);return;}
      if(e.key==='+'||e.key==='='){e.preventDefault();zoom(1.5);}
      else if(e.key==='-'){e.preventDefault();zoom(1/1.5);}
      else if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){e.preventDefault();view.x+=(e.key==='ArrowRight'?1:e.key==='ArrowLeft'?-1:0)*view.w*.1;view.y+=(e.key==='ArrowDown'?1:e.key==='ArrowUp'?-1:0)*view.h*.1;updateView();}
    });
    svg.addEventListener('wheel',e=>{if(!e.ctrlKey)return;e.preventDefault();zoom(e.deltaY<0?1.2:1/1.2,position(e));},{passive:false});
    svg.addEventListener('pointerdown',e=>{if(e.button!==0)return;moved=false;drag={id:e.pointerId,x:e.clientX,y:e.clientY,start:position(e),view:{...view}};});
    svg.addEventListener('pointermove',e=>{
      if(!drag||drag.id!==e.pointerId)return;
      if(!moved && Math.hypot(e.clientX-drag.x,e.clientY-drag.y)<5)return;
      if(!moved){svg.setPointerCapture(e.pointerId);moved=true;closeInfo();}
      const matrix=svg.getScreenCTM();view.x=drag.view.x-(e.clientX-drag.x)/matrix.a;view.y=drag.view.y-(e.clientY-drag.y)/matrix.d;updateView();
    });
    const end=e=>{if(drag?.id===e.pointerId){if(svg.hasPointerCapture(e.pointerId))svg.releasePointerCapture(e.pointerId);drag=null;}};
    svg.addEventListener('pointerup',end);svg.addEventListener('pointercancel',end);
    document.addEventListener('keydown',e=>{if(e.key==='Escape')closeInfo();});updateView();
  }
  function map(rows) {
    const mapped = rows.filter(r => r.coordinates && r.coordinates[0] >= -60 && r.coordinates[0] <= 84);
    const groups=new Map();for(const r of mapped){const key=r.coordinates.join(',');if(!groups.has(key))groups.set(key,[]);groups.get(key).push(r);}mapGroups=[...groups.values()];closeInfo();
    $('map-points').innerHTML = mapGroups.map((group,i) => {const r=group[0],[x,y] = xy(r.coordinates);return `<circle cx="${x}" cy="${y}" r="${4.5*view.w/1000}" data-site="${i}" tabindex="0" role="button" aria-label="${esc(r.name)}${group.length>1?' and '+(group.length-1)+' other records':''}: show site details" aria-controls="map-info" class="${group.every(r=>r.status==='Suspended Operation')?'suspended':''}"/>`;}).join('');
    $('map-caption').textContent = `${mapped.length} of ${rows.length} selected records mapped at ${mapGroups.length} locations · ${rows.length-mapped.length} without a plotted site location. Shared markers show all co-located records. Site coordinates retain their baseline review date; no administrative centroids plotted. Natural Earth geographic context.`;
  }
  function render(scroll = false) {
    const result = selected(), totalPages = Math.max(1,Math.ceil(result.length/pageSize));
    page = Math.min(page,totalPages);
    const offset = (page-1)*pageSize, slice = result.slice(offset,offset+pageSize);
    const projects = result.filter(r => r.rowUnit==='Project').length;
    $('reactor-result-count').textContent = `${result.length} records (${result.length-projects} unit records, ${projects} project records) · ${result.length ? offset+1 : 0}–${Math.min(offset+pageSize,result.length)} shown`;
    $('reactor-list').innerHTML = slice.length ? slice.map(card).join('') : '<p class="empty">No records match these filters. Try another search or reset the filters.</p>';
    const pages = [...new Set([1,...Array.from({length:5},(_,i)=>page-2+i).filter(n=>n>=1 && n<=totalPages),totalPages])].sort((a,b)=>a-b);
    const button = (n,label,disabled=false) => `<button type="button" data-page="${n}"${disabled?' disabled':''}${n===page && /^\d+$/.test(label)?' aria-current="page"':''} aria-label="${/^\d+$/.test(label)?'Page '+label:label}">${label}</button>`;
    let nums = '', previous = 0;
    for(const n of pages){if(previous && n>previous+1)nums+='<span aria-hidden="true">…</span>';nums+=button(n,String(n));previous=n;}
    $('reactor-pagination').innerHTML = button(page-1,'Previous',page===1)+nums+button(page+1,'Next',page===totalPages)+`<span class="page-status">Page ${page} of ${totalPages} · 10 records per page</span>`;
    $('reactor-pagination').hidden = result.length<=pageSize;
    map(result);
    if(scroll)$('reactor-result-count').scrollIntoView({block:'start',behavior:'auto'});
  }
  async function init() {
    const data = window.REACTOR_DISPLAY.inventory;records = data.records.filter(r=>r.board===board);
    setupMap();
    for(const country of [...new Set(records.map(r=>r.country))].sort())$('reactor-country').add(new Option(country,country));
    const label = board==='operating' ? 'All fleet records (including suspended)' : 'All project stages';
    $('reactor-status').add(new Option(label,''));
    for(const status of [...new Set(records.map(r=>r.status))].sort())$('reactor-status').add(new Option(status,status));
    if(board==='operating')$('reactor-status').value='Operational';
    $('data-controls').hidden=false;
    $('data-controls').addEventListener('submit',e=>e.preventDefault());
    for(const id of ['reactor-search','reactor-country','reactor-status','reactor-evidence'])$(id).addEventListener(id==='reactor-search'?'input':'change',()=>{page=1;render();});
    $('data-controls').addEventListener('reset',e=>{e.preventDefault();$('reactor-search').value='';$('reactor-country').value='';$('reactor-evidence').value='';$('reactor-status').value=board==='operating'?'Operational':'';page=1;render();});
    $('reactor-pagination').addEventListener('click',e=>{const button=e.target.closest('button[data-page]');if(button&&!button.disabled){page=Number(button.dataset.page);render(true);$('reactor-pagination').querySelector('[aria-current="page"]')?.focus({preventScroll:true});}});
    render();
    try {
      const world=window.REACTOR_DISPLAY.world;
      $('map-land').innerHTML = world.polygons.map(points => '<path d="'+points.map(([lon,lat],i)=>{const [x,y]=xy([lat,lon]);return (i?'L':'M')+x.toFixed(2)+','+y.toFixed(2);}).join(' ')+'Z"/>').join('');
      $('reactor-map').hidden=false;
    } catch { /* A map failure does not remove the independently usable register. */ }
  }
  init().catch(()=>{$('data-error').textContent='The interactive dataset could not load. The first 10 records remain below; reload the page to try again.';$('data-error').hidden=false;});
})();
