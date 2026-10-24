const posts = [
{
  "title": "The Nucleus Gets a Bulk Discount — Mass Defect and Binding Energy",
  "date": "2026.10.24",
  "displayDate": "2026.10.24",
  "section": "theory",
  "category": "Nuclear & Radiation Basics",
  "summary": "An assembled nucleus always weighs less than its separate protons and neutrons, and that missing mass, about 0.75% for helium-4, is the binding energy that explains why both fission and fusion release energy.",
  "thumbnail": "assets/images/theory/001-mass-defect/thumbnail.png",
  "thumbnailAlt": "A silver balance scale with four loose spheres on one pan and the same four spheres packed into a tight cluster on the other, the cluster side sitting slightly higher",
  "url": "posts/theory/001-mass-defect.html",
  "keywords": "mass defect binding energy binding energy per nucleon atomic nucleus helium-4 atomic mass unit nuclear fission nuclear fusion nuclear physics basics"
},
{
  "title": "NRC Reform: What Changes Even When the Dose Limits Stay the Same",
  "date": "2026.09.29",
  "displayDate": "2026.09.29",
  "section": "news",
  "category": "Policy & Regulation",
  "summary": "The NRC's July 2026 proposed radiation protection rule keeps the 50 mSv and 1 mSv basic limits but changes dose-management, exception and reporting conditions, so cost-savings estimates and exposure data must be read as separate evidence.",
  "thumbnail": "assets/images/news/2026-09-29-nrc-reform-safety-evidence/en/thumbnail_01.png",
  "thumbnailAlt": "Dosimeter, papers and safety glasses on a desk with the text NRC Radiation Protection Proposed Rule: read the limits and the conditions together",
  "url": "posts/news/2026-09-29-nrc-reform-safety-evidence.html",
  "keywords": "NRC radiation protection proposed rule 10 CFR Part 20 dose limits ALARA planned dose limit extension public dose regulatory analysis occupational exposure"
}

];
const view=document.body.dataset.section||"news";
const ALL="All";
const esc=s=>String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
const list=document.querySelector("#post-list"),empty=document.querySelector("#empty-state"),search=document.querySelector("#search"),filters=document.querySelector(".filters");let buttons=[...document.querySelectorAll("[data-filter]")],active=ALL;
document.querySelectorAll("[data-view-link]").forEach(link=>link.classList.toggle("active",link.dataset.viewLink===view));
if(view==="theory"){document.querySelector("#board-eyebrow").textContent="NUCLEAR THEORY";document.querySelector("#board-title").textContent="Nuclear Theory";empty.textContent="No nuclear theory posts in this category yet.";const categories=[...new Set(posts.filter(p=>p.section==="theory").map(p=>p.category))];filters.innerHTML=`<button class="selected" type="button" data-filter="${ALL}">All posts</button>${categories.map(c=>`<button type="button" data-filter="${esc(c)}">${esc(c)}</button>`).join("")}`;buttons=[...filters.querySelectorAll("[data-filter]")]}
function render(){const q=search.value.trim().toLowerCase();const filtered=posts.filter(p=>p.section===view&&(active===ALL||p.category===active)&&(`${p.title} ${p.summary} ${p.keywords}`.toLowerCase().includes(q))).sort((a,b)=>b.date.localeCompare(a.date));list.innerHTML=filtered.map(p=>`<a class="post" href="${p.url}"><img class="post-thumb" src="${p.thumbnail}" alt="${esc(p.thumbnailAlt)}"><div class="post-copy"><div class="post-meta"><strong>${esc(p.category)}</strong>${p.displayDate}</div><h3>${esc(p.title)}</h3><p>${esc(p.summary)}</p></div><span class="arrow" aria-hidden="true">→</span></a>`).join("");empty.hidden=filtered.length!==0}search.addEventListener("input",render);buttons.forEach(b=>b.addEventListener("click",()=>{active=b.dataset.filter;buttons.forEach(x=>x.classList.toggle("selected",x===b));render()}));render();
