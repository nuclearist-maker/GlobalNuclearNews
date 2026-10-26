/* Progressive enhancement; the static first page and downloads work without JS. */
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
  function map(rows) {
    const mapped = rows.filter(r => r.coordinates && r.coordinates[0] >= -60 && r.coordinates[0] <= 84);
    $('map-points').innerHTML = mapped.map(r => {const [x,y] = xy(r.coordinates);return `<circle cx="${x}" cy="${y}" r="2.8" class="${r.status==='Suspended Operation'?'suspended':''}"><title>${esc(r.name)} · ${esc(r.country)} · ${esc(r.status)}</title></circle>`;}).join('');
    $('map-caption').textContent = `${mapped.length} of ${rows.length} selected records mapped · ${rows.length-mapped.length} without a plotted site location. Co-located units overlap. Site coordinates retain their baseline review date; no administrative centroids plotted. Natural Earth geographic context.`;
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
    const response = await fetch('assets/data/reactors.json');if(!response.ok)throw new Error('Dataset unavailable');
    const data = await response.json();records = data.records.filter(r=>r.board===board);
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
      const response = await fetch('assets/data/world-outline.json');if(!response.ok)throw new Error('Map unavailable');const world=await response.json();
      $('map-land').innerHTML = world.polygons.map(points => '<path d="'+points.map(([lon,lat],i)=>{const [x,y]=xy([lat,lon]);return (i?'L':'M')+x.toFixed(2)+','+y.toFixed(2);}).join(' ')+'Z"/>').join('');
      $('reactor-map').hidden=false;
    } catch { /* A map failure does not remove the independently usable register. */ }
  }
  init().catch(()=>{$('data-error').textContent='The interactive dataset could not load. The first 10 records remain below; use the JSON download for the full register.';$('data-error').hidden=false;});
})();
