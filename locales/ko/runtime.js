/* Local display translation only. Never change enum values, URLs or identifiers. */
(() => {
  'use strict';
  const words = window.GNN_KO_WORDS;
  function translate(value) {
    if (value == null) return value;
    const raw=String(value), s=raw.trim();
    let out=words[s];
    if (out === undefined) {
      const rules = [
        [/^View all (.+) posts →$/,m=>`${translate(m[1])} 전체 보기 →`],
        [/^Page (\d+) of (\d+) · (\d+) posts$/,m=>`${m[1]} / ${m[2]}쪽 · 게시물 ${m[3]}편`],
        [/^Page (\d+) of (\d+) · 10 records per page$/,m=>`${m[1]} / ${m[2]}쪽 · 쪽당 10건`],
        [/^Page (\d+)$/,m=>`${m[1]}쪽`],
        [/^(\d+) records · showing the first 10$/,m=>`${m[1]}건 · 첫 10건 표시`],
        [/^(\d+) records \((\d+) unit records, (\d+) project records\) · (\d+)–(\d+) shown$/,m=>`${m[1]}건(호기 ${m[2]}건, 사업 ${m[3]}건) · ${m[4]}–${m[5]}건 표시`],
        [/^(\d+) records at this location$/,m=>`이 위치의 기록 ${m[1]}건`],
        [/^PRIS fields checked: (.+)$/,m=>`PRIS 항목 확인일: ${m[1]}`],
        [/^Baseline only · source review: (.+) · not revalidated$/,m=>`기존 자료만 있음 · 출처 검토일: ${m[1]} · 재검증하지 않음`],
        [/^(.+) · checked (\d{4}-\d{2}-\d{2})$/,m=>`${translate(m[1])} · 확인일 ${m[2]}`],
        [/^Checked: (.+)$/,m=>`확인일: ${m[1]}`],
        [/^Baseline stage: (.+)\. Current PRIS inventory: (.+)\.$/,m=>`기존 단계: ${m[1].split('; ').map(translate).join('·')}. 현재 PRIS 분류: ${translate(m[2])}.`],
        [/^(.+) · Net: (.+)$/,m=>`${translate(m[1])} · 순전기출력: ${m[2]}`],
        [/^(.+): show site details$/,m=>`${m[1].replace(/ and (\d+) other records$/, ' 외 $1건')}: 부지 상세 정보 보기`],
        [/^(\d+) of (\d+) selected records mapped at (\d+) locations · (\d+) without a plotted site location\. Shared markers show all co-located records\. Site coordinates retain their baseline review date; no administrative centroids plotted\. Natural Earth geographic context\.$/,m=>`선택한 ${m[2]}건 중 ${m[1]}건을 ${m[3]}개 위치에 표시 · ${m[4]}건은 지도 위치 없음. 같은 부지의 기록은 하나의 표시에 함께 표시합니다. 좌표는 기존 검토일 기준이며 행정구역 중심점은 표시하지 않습니다. Natural Earth 지리 자료.`],
        [/^(.+) archive — page (\d+)$/,m=>`${translate(m[1])} 글 모음 — ${m[2]}쪽`],
        [/^Browse (.+) articles, page (\d+) of (\d+)\.$/,m=>`${translate(m[1])} 게시물 · ${m[2]} / ${m[3]}쪽`],
        [/^(.+): (\d+) articles$/,m=>`${translate(m[1])}: ${m[2]}편`]
      ];
      for(const [pattern,format] of rules){const m=s.match(pattern);if(m){out=format(m);break;}}
      if(out===undefined && s.includes(' | ')) out=s.split(' | ').map(translate).join(' | ');
      if(out===undefined && s.includes(' · ')) out=s.split(' · ').map(translate).join(' · ');
      if(out===undefined && s.endsWith(' →')) out=translate(s.slice(0,-2))+' →';
      if(out===undefined && s.startsWith('← ')) out='← '+translate(s.slice(2));
    }
    return out===undefined ? raw : raw.replace(s,out);
  }
  function localize(root) {
    if(root.nodeType===Node.TEXT_NODE){
      if(!root.parentElement?.closest('script,style,[data-original-language]')){
        const s=translate(root.nodeValue);if(s!==root.nodeValue)root.nodeValue=s;
      }
      return;
    }
    if(root.nodeType!==Node.ELEMENT_NODE && root!==document)return;
    if(root.nodeType===Node.ELEMENT_NODE){
      if(root.matches('script,style,[data-original-language]'))return;
      for(const a of ['aria-label','alt','placeholder'])if(root.hasAttribute(a)){
        const s=translate(root.getAttribute(a));if(s!==root.getAttribute(a))root.setAttribute(a,s);
      }
    }
    for(const child of root.childNodes)localize(child);
  }
  window.GNN_KO={translate,localize};localize(document);
  new MutationObserver(changes=>{
    for(const c of changes){if(c.type==='characterData')localize(c.target);else for(const n of c.addedNodes)localize(n);}
  }).observe(document.documentElement,{childList:true,subtree:true,characterData:true});
})();
