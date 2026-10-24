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
    "title": "Where a Port Fits in the SMR Supply Chain: Lessons from a Rotterdam Study",
    "date": "2026.10.23",
    "displayDate": "2026.10.23",
    "section": "news",
    "category": "SMR",
    "summary": "A SmartPort-commissioned study by Tractebel and Technopolis identifies 92 potential supply chain companies around Rotterdam and four port roles; entry requires quality systems, traceability and customer qualification, while maritime nuclear remains a long-term goal.",
    "thumbnail": "assets/images/news/2026-10-23-rotterdam-port-smr-supply-chain/thumbnail_01.png",
    "thumbnailAlt": "A crane lifting a large cylindrical module from a cargo ship onto the quay of a major port at sunrise",
    "url": "posts/news/2026-10-23-rotterdam-port-smr-supply-chain.html",
    "keywords": "SMR Small Modular Reactor Port Of Rotterdam Nuclear Supply Chain Module Transport ISO19443 Traceability Quality Management Nuclear Ships IMO SOLAS Tractebel Maritime Nuclear Netherlands Nuclear Energy"
  },
  {
    "title": "Finland Grants the World's First Operating Licence for a Spent Fuel Repository: What Comes Next for Posiva",
    "date": "2026.10.23",
    "displayDate": "2026.10.23",
    "section": "news",
    "category": "Fuel Cycle",
    "summary": "On 22 October 2026 Finland granted Posiva the world's first operating licence for a spent fuel encapsulation and final disposal facility, based on STUK's August safety assessment; commissioning and STUK approval come next, and no disposal start date has been disclosed.",
    "thumbnail": "assets/images/news/2026-10-23-posiva-spent-fuel-repository-licence/thumbnail_01.png",
    "thumbnailAlt": "Repository buildings beside a tunnel entrance into coastal bedrock in a Nordic pine forest",
    "url": "posts/news/2026-10-23-posiva-spent-fuel-repository-licence.html",
    "keywords": "Spent Fuel Final Disposal Repository Operating Licence Multi Barrier Engineered Barrier Encapsulation Posiva Olkiluoto STUK TVO Fortum Finland Radioactive Materials Nuclear Energy"
  },
  {
    "title": "From Government Test Reactor to Commercial License: What the NRC's New Rule Changes",
    "date": "2026.10.23",
    "displayDate": "2026.10.23",
    "section": "news",
    "category": "Policy & Regulation",
    "summary": "The NRC's October 22, 2026 final rule amends 10 CFR Parts 50 and 53 so applicants can show how prior DOE or Department of War authorization and test data meet NRC requirements; candidates such as Antares, Aalo, Last Energy and BWXT Pele sit at different demonstration stages.",
    "thumbnail": "assets/images/news/2026-10-23-nrc-rule-demonstration-reactor-data/thumbnail_01.png",
    "thumbnailAlt": "A compact test reactor module in a laboratory high bay, with review binders on a desk in the foreground",
    "url": "posts/news/2026-10-23-nrc-rule-demonstration-reactor-data.html",
    "keywords": "NRC Reactor Licensing Demonstration Data Final Rule DOE Reactor Pilot Program Zero Power Criticality Documented Safety Analysis Antares Aalo Last Energy BWXT INL Nuclear Energy"
  },
  {
    "title": "How Clean Is Clean Enough? Future Land Use and the Cleanup of U.S. Nuclear Sites",
    "date": "2026.10.23",
    "displayDate": "2026.10.23",
    "section": "news",
    "category": "Policy & Regulation",
    "summary": "GAO's October 2026 reports compare land use plans with cleanup decisions at six DOE sites, find residential assumptions driving deeper excavation at Hanford and Idaho, and recommend evaluating multiple future-use assumptions; DOE disagreed with that recommendation while both agencies agreed to a task force.",
    "thumbnail": "assets/images/news/2026-10-23-doe-cleanup-future-land-use/thumbnail_01.png",
    "thumbnailAlt": "Wide restored land in the arid American West with old industrial buildings in the distance",
    "url": "posts/news/2026-10-23-doe-cleanup-future-land-use.html",
    "keywords": "Nuclear Cleanup Future Land Use Cleanup Levels GAO DOE EPA Hanford Idaho Oak Ridge CERCLA Mixed Waste Exposure Pathways Residual Contamination Nuclear Energy"
  },
  {
    "title": "Keeping Warm Through the Long Lunar Night: Canada's Nuclear Heat and Power Research for Space",
    "date": "2026.10.23",
    "displayDate": "2026.10.23",
    "section": "news",
    "category": "Space Nuclear",
    "summary": "Within CAD 11.1 million for 16 space projects, the Canadian Space Agency funded Canadensys's tritium-based heater unit (CAD 499,997) and CSMC's isotope power concept (CAD 350,000); both are early-stage research ahead of design and testing.",
    "thumbnail": "assets/images/news/2026-10-23-canada-space-isotope-heat-power/thumbnail_01.png",
    "thumbnailAlt": "A small rover on the lunar surface at night with a softly glowing equipment box and Earth above the horizon",
    "url": "posts/news/2026-10-23-canada-space-isotope-heat-power.html",
    "keywords": "Space Nuclear Radioisotopes Tritium Radioisotope Heater Unit Isotope Power Lunar Exploration Lunar Night Canadian Space Agency CSA Canadensys CSMC CNL Canadian Centre For Space Isotopes Nuclear Energy"
  },
  {
    "title": "NRC Reform: What Changes Even When the Dose Limits Stay the Same",
    "date": "2026.09.29",
    "displayDate": "2026.09.29",
    "section": "news",
    "category": "Policy & Regulation",
    "summary": "The NRC's July 2026 proposed radiation protection rule keeps the 50 mSv and 1 mSv basic limits but changes dose-management, exception and reporting conditions, so cost-savings estimates and exposure data must be read as separate evidence.",
    "thumbnail": "assets/images/news/2026-09-29-nrc-reform-safety-evidence/thumbnail_01.png",
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
