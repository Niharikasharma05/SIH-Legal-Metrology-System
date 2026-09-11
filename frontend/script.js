// ============================================================
  // CONFIG — the one line that connects this frontend to a backend.
  // Expected to be a FastAPI service (see footnote/uvicorn command
  // in the Report page above). If this URL is unreachable, the
  // scan button below fails gracefully with an on-screen message.
  // ============================================================
  const API_URL = "http://localhost:8000/api/compliance/scans";

  // ============================================================
  // i18n — English / Hindi text dictionary, applied to every
  // element tagged with data-i18n="key" in the HTML above.
  // ============================================================
  const I18N = {
    en: {
      login_eyebrow:"SECURE SIGN-IN", login_title:"Welcome back", officer_id:"Officer ID", access_key:"Access key",
      open_workspace:"Open workspace", login_note:"This portal is for authorised enforcement officers. Enter any Officer ID and key to continue in this demo build.",
      nav_dashboard:"Dashboard", nav_report:"Report", nav_rules:"Rule Desk", nav_inspections:"Inspections", nav_analytics:"Analytics", sign_out:"Sign out",
      field_workspace:"FIELD WORKSPACE", good_morning:"Good morning,", dashboard_lede:"Your compliance desk is ready. Start with a package label to run a live scan.",
      quick_scan:"Quick scan", quick_scan_sub:"Turn the next label in front of you into a decision you can stand behind.",
      click_upload:"Click to upload", a_label_photo:"a label photo", product_name_optional:"Product name (optional)", scan_now:"Scan Now",
      todays_posture:"TODAY'S POSTURE", field_ready:"Field ready", no_scans_yet:"No scans run yet this session. Run your first scan to populate live signals.",
      compliance_report:"Compliance Report", report_lede:"Result of your most recent scan.", no_scan_yet:"No scan yet. Run one from the Dashboard's Quick Scan card.",
      backend_note:"Backend must be running locally at",
      reference_desk:"REFERENCE DESK", rule_desk_title:"The rule desk",
      rule_desk_lede:"All 34 rules of the Legal Metrology (Packaged Commodities) Rules, 2011 — for field orientation, not a substitute for the notified legislation.",
      evidence_trail:"EVIDENCE TRAIL", inspections_title:"Inspections", inspections_lede:"A record of scanned packages and their compliance outcome.",
      violation_register:"Violation register", col_product:"Product", col_scanned:"Scanned", col_status:"Status", col_issues:"Issues",
      signal:"SIGNAL", analytics_title:"Analytics", analytics_lede:"Aggregate view of this session's scans.",
      scans_session:"Scans this session", compliant_rate:"Compliant rate", violations_flagged:"Violations flagged",
      issue_breakdown:"Issue breakdown", run_scans_hint:"Run a few scans to see the breakdown here.",
    },
    hi: {
      login_eyebrow:"सुरक्षित प्रवेश", login_title:"वापसी पर स्वागत है", officer_id:"अधिकारी आईडी", access_key:"पासकोड",
      open_workspace:"कार्यक्षेत्र खोलें", login_note:"यह पोर्टल अधिकृत प्रवर्तन अधिकारियों के लिए है। इस डेमो में जारी रखने हेतु कोई भी आईडी और पासकोड दर्ज करें।",
      nav_dashboard:"डैशबोर्ड", nav_report:"रिपोर्ट", nav_rules:"नियम संदर्भ", nav_inspections:"निरीक्षण", nav_analytics:"विश्लेषण", sign_out:"साइन आउट",
      field_workspace:"कार्यक्षेत्र", good_morning:"नमस्ते,", dashboard_lede:"आपका अनुपालन डेस्क तैयार है। एक पैकेज लेबल से स्कैन शुरू करें।",
      quick_scan:"त्वरित जाँच", quick_scan_sub:"सामने के लेबल को एक स्पष्ट निर्णय में बदलें।",
      click_upload:"अपलोड करने हेतु क्लिक करें", a_label_photo:"लेबल की फोटो", product_name_optional:"उत्पाद नाम (वैकल्पिक)", scan_now:"अभी स्कैन करें",
      todays_posture:"आज की स्थिति", field_ready:"क्षेत्र हेतु तैयार", no_scans_yet:"अभी तक कोई स्कैन नहीं हुआ। पहला स्कैन चलाएँ।",
      compliance_report:"अनुपालन रिपोर्ट", report_lede:"आपके नवीनतम स्कैन का परिणाम।", no_scan_yet:"अभी कोई स्कैन नहीं। डैशबोर्ड से त्वरित जाँच चलाएँ।",
      backend_note:"बैकएंड स्थानीय रूप से यहाँ चल रहा होना चाहिए",
      reference_desk:"संदर्भ डेस्क", rule_desk_title:"नियम संदर्भ डेस्क",
      rule_desk_lede:"Legal Metrology (Packaged Commodities) Rules, 2011 के सभी 34 नियम — क्षेत्रीय संदर्भ हेतु, अधिसूचित कानून का विकल्प नहीं।",
      evidence_trail:"साक्ष्य लॉग", inspections_title:"निरीक्षण", inspections_lede:"स्कैन किए गए उत्पादों और उनके अनुपालन परिणाम का रिकॉर्ड।",
      violation_register:"उल्लंघन रजिस्टर", col_product:"उत्पाद", col_scanned:"स्कैन समय", col_status:"स्थिति", col_issues:"समस्याएँ",
      signal:"संकेत", analytics_title:"विश्लेषण", analytics_lede:"इस सत्र के स्कैन का सारांश।",
      scans_session:"इस सत्र में स्कैन", compliant_rate:"अनुपालन दर", violations_flagged:"उल्लंघन चिह्नित",
      issue_breakdown:"समस्या विवरण", run_scans_hint:"विवरण देखने हेतु कुछ स्कैन चलाएँ।",
    }
  };
  let currentLang = 'en';

  // Applies the current language dictionary to every data-i18n element.
  function applyLang(lang) {
    currentLang = lang;
    document.getElementById('langEn').classList.toggle('active', lang === 'en');
    document.getElementById('langHi').classList.toggle('active', lang === 'hi');
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (I18N[lang][key]) el.textContent = I18N[lang][key];
    });
  }
  document.getElementById('langEn').addEventListener('click', () => applyLang('en'));
  document.getElementById('langHi').addEventListener('click', () => applyLang('hi'));

  // ============================================================
  // LOGIN — DEMO MODE: accepts any non-empty ID + key.
  // No password check, no backend auth call. Flagged as a
  // known limitation — production version would connect to a
  // real officer credential system.
  // ============================================================
  document.getElementById('loginBtn').addEventListener('click', () => {
    const id = document.getElementById('officerIdInput').value.trim();
    const key = document.getElementById('accessKeyInput').value.trim();
    if (!id || !key) { alert('Enter an Officer ID and access key to continue.'); return; }
    document.getElementById('officerNameDisplay').textContent = id;
    document.getElementById('avatarInitial').textContent = id.charAt(0).toUpperCase();
    document.getElementById('greetName').textContent = id.split('-')[0] || id;
    document.body.classList.add('signed-in');
  });
  document.getElementById('signOutBtn').addEventListener('click', () => {
    document.body.classList.remove('signed-in');
    document.getElementById('officerIdInput').value = '';
    document.getElementById('accessKeyInput').value = '';
    goto('dashboard');
  });

  // ============================================================
  // NAVIGATION — simple show/hide between the 5 pages, no router.
  // ============================================================
  document.querySelectorAll('.navitem').forEach(item => item.addEventListener('click', () => goto(item.dataset.page)));
  function goto(page) {
    document.querySelectorAll('.navitem').forEach(n => n.classList.toggle('active', n.dataset.page === page));
    document.querySelectorAll('.page').forEach(p => p.classList.toggle('active', p.id === 'page-' + page));
  }

  // ============================================================
  // SCAN FLOW — upload handling + the actual API call.
  // sessionScans holds every result from this browser tab only:
  // it is NOT persisted to a database, so it resets on refresh.
  // ============================================================
  let selectedFile = null;
  let sessionScans = [];
  const dropZone = document.getElementById('dropZoneDash');
  const fileInput = document.getElementById('fileInput');
  const previewWrap = document.getElementById('previewWrap');
  const previewImg = document.getElementById('previewImg');
  const scanBtn = document.getElementById('scanBtn');
  const statusEl = document.getElementById('status');

  dropZone.addEventListener('click', () => fileInput.click());
  dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
  dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.classList.remove('dragover'); if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]); });
  fileInput.addEventListener('change', e => { if (e.target.files.length) handleFile(e.target.files[0]); });

  // Called once a file is selected (via click or drag-drop). Shows a preview
  // and enables the Scan button. No file-type/size validation is done here yet.
  function handleFile(file) {
    selectedFile = file;
    previewImg.src = URL.createObjectURL(file);
    previewWrap.style.display = 'block';
    scanBtn.disabled = false;
    statusEl.textContent = ''; statusEl.className = '';
  }

  // The actual "Scan Now" action: packages the image + optional product name
  // into multipart form data and POSTs it to the FastAPI backend at API_URL.
  // On success, prepends the returned result to sessionScans and re-renders
  // every page that depends on it. On failure (e.g. backend not running),
  // shows a clear on-screen error instead of failing silently.
  scanBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    scanBtn.disabled = true;
    statusEl.className = ''; statusEl.textContent = currentLang === 'hi' ? 'जाँच जारी है…' : 'Running OCR + compliance check…';
    const formData = new FormData();
    formData.append('file', selectedFile);
    const productName = document.getElementById('productNameInput').value;
    if (productName) formData.append('productName', productName);
    try {
      const res = await fetch(API_URL, { method: 'POST', body: formData });
      if (!res.ok) throw new Error(`Server responded ${res.status}`);
      const data = await res.json();
      sessionScans.unshift(data);
      renderAll();
      goto('scan');
    } catch (err) {
      statusEl.className = 'error';
      statusEl.textContent = `Couldn't reach the backend at localhost:8000. (${err.message})`;
    } finally { scanBtn.disabled = false; }
  });

  // ============================================================
  // RENDERING — turns sessionScans into the Dashboard posture card,
  // the Report page, the Inspections table, and the Analytics stats.
  // These six fields are what the compliance engine actually checks
  // per scan (mapped to specific rules — see comment above each):
  //   mrp                  -> Rule 6
  //   netQuantity          -> Rules 6, 11, 12, 13
  //   manufactureDate      -> Rule 6
  //   manufacturerAddress  -> Rules 6, 10
  //   consumerCare         -> Rule 6
  //   fontCheck            -> Rule 7 (numeral height)
  // ============================================================
  const FIELD_LABELS_EN = { mrp:"Maximum Retail Price", netQuantity:"Net Quantity", manufactureDate:"Date of Manufacture", manufacturerAddress:"Manufacturer/Packer Address", consumerCare:"Consumer Care Details", fontCheck:"Font & Readability (Rule 7)" };

  function renderAll() { renderPosture(); renderReport(sessionScans[0]); renderInspections(); renderAnalytics(); }

  // Dashboard "Today's Posture" card — quick summary of how the session is going.
  function renderPosture() {
    const violations = sessionScans.filter(s => s.status === 'VIOLATION').length;
    const headline = document.getElementById('postureHeadline');
    const body = document.getElementById('postureBody');
    if (sessionScans.length === 0) return;
    if (violations > 0) {
      headline.textContent = currentLang === 'hi' ? `${violations} उल्लंघन आज` : `${violations} violation${violations===1?'':'s'} today`;
      body.textContent = currentLang === 'hi' ? 'निरीक्षण अनुभाग में समीक्षा करें।' : 'Review flagged scans in Inspections before closing your round.';
    } else {
      headline.textContent = I18N[currentLang].field_ready;
      body.textContent = currentLang === 'hi' ? 'इस सत्र के सभी स्कैन अनुपालित रहे।' : 'All scans this session came back compliant.';
    }
  }

  // Renders the full compliance report for the most recent scan:
  // status banner, per-field declaration list, and any flagged issues.
  function renderReport(data) {
    if (!data) return;
    document.getElementById('reportEmpty').style.display = 'none';
    document.getElementById('reportContent').style.display = 'block';
    const header = document.getElementById('resultHeader');
    header.className = 'result-header ' + data.status;
    header.textContent = data.status === 'COMPLIANT' ? '✓  All mandatory declarations detected'
      : data.status === 'VIOLATION' ? '⚠  Violation — core declaration missing' : '△  Minor issues found';
    const declList = document.getElementById('declList');
    declList.innerHTML = '';
    ['mrp','netQuantity','manufactureDate','manufacturerAddress','consumerCare','fontCheck'].forEach(key => {
      const row = document.createElement('div');
      row.className = 'decl-row';
      row.innerHTML = `<span>${FIELD_LABELS_EN[key]}</span><span class="decl-value">${data[key]}</span>`;
      declList.appendChild(row);
    });
    const issuesBox = document.getElementById('issuesBox');
    if (data.issues && data.issues.length) {
      issuesBox.style.display = 'block';
      issuesBox.innerHTML = `<strong>Issues found:</strong><ul>${data.issues.map(i => `<li>${i}</li>`).join('')}</ul>`;
    } else { issuesBox.style.display = 'none'; }

    const officer = document.getElementById('officerNameDisplay').textContent;
    document.getElementById('printMeta').textContent =
      `${data.productName || 'Untitled scan'}  ·  Scanned ${new Date(data.scannedAt).toLocaleString()}  ·  Officer: ${officer}`;
  }

  // Renders the Inspections table — one row per scan, newest first.
  // NOTE: this is session-only data (see sessionScans above), not a
  // persistent audit log yet.
  function renderInspections() {
    document.getElementById('inspCount').textContent = `${sessionScans.length} record${sessionScans.length===1?'':'s'}`;
    const body = document.getElementById('inspBody');
    body.innerHTML = '';
    if (sessionScans.length === 0) { body.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--muted);">No scans yet this session.</td></tr>`; return; }
    sessionScans.forEach(s => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td><strong>${s.productName || 'Untitled scan'}</strong></td>
        <td style="color:var(--muted);">${new Date(s.scannedAt).toLocaleTimeString()}</td>
        <td><span class="pill ${s.status}">${s.status}</span></td>
        <td style="color:var(--muted);">${s.issues.length ? s.issues.length + ' issue' + (s.issues.length===1?'':'s') : '—'}</td>`;
      body.appendChild(tr);
    });
  }

  // Renders the Analytics page: total scans, compliant %, violations,
  // and a simple bar-chart breakdown of which issues recur most often.
  function renderAnalytics() {
    const total = sessionScans.length;
    document.getElementById('anTotal').textContent = total;
    const compliant = sessionScans.filter(s => s.status === 'COMPLIANT').length;
    document.getElementById('anCompliant').textContent = total ? Math.round((compliant/total)*100) + '%' : '0%';
    document.getElementById('anViolations').textContent = sessionScans.filter(s => s.status === 'VIOLATION').length;
    const counts = {};
    sessionScans.forEach(s => s.issues.forEach(i => { counts[i] = (counts[i]||0)+1; }));
    const entries = Object.entries(counts).sort((a,b) => b[1]-a[1]);
    const bars = document.getElementById('issueBars');
    if (!entries.length) { bars.innerHTML = `<p style="color:var(--muted); font-size:12px;">${I18N[currentLang].run_scans_hint}</p>`; return; }
    const max = entries[0][1];
    bars.innerHTML = entries.map(([label, count], i) => `
      <div class="bar-row">
        <div class="bar-label"><span>${label}</span><span style="color:var(--muted);">${count}</span></div>
        <div class="bar-track"><div class="bar-fill" style="width:${(count/max)*100}%; background:${i%2===0?'var(--green)':'var(--orange)'};"></div></div>
      </div>`).join('');
  }

  // ============================================================
  // RULE DESK DATA — all 34 rules of the Legal Metrology
  // (Packaged Commodities) Rules, 2011, used as officer reference
  // material. NOTE: only a subset of these (Rules 6, 7, 10, 11,
  // 12, 13) are the ones the scan engine actually validates
  // against a label photo — the rest (registration, inspection
  // powers, penalties, etc.) are procedural/legal-authority rules
  // that can't be checked from an image.
  // ============================================================
  const RULES = [
    { n:1, ch:"Chapter I — Preliminary", title:"Short title and commencement", summary:"These rules are called the Legal Metrology (Packaged Commodities) Rules, 2011, and came into force on 1 April 2011." },
    { n:2, ch:"Chapter I — Preliminary", title:"Definitions", summary:"Defines key terms used throughout the rules — manufacturer, packer, dealer, net quantity, principal display panel, retail/wholesale package, and more." },
    { n:3, ch:"Chapter II — Retail Packages", title:"Applicability of the chapter", summary:"This chapter's provisions don't apply to packages over 25kg/25L (except cement/fertilizer bags up to 50kg) or to industrial/institutional buyers." },
    { n:4, ch:"Chapter II — Retail Packages", title:"Regulation for pre-packing and sale", summary:"No commodity may be pre-packed for sale unless the package bears all declarations required under these rules." },
    { n:5, ch:"Chapter II — Retail Packages", title:"Standard package sizes", summary:"Commodities listed in the Second Schedule must be packed only in the standard quantities specified there." },
    { n:6, ch:"Chapter II — Retail Packages", title:"Mandatory declarations", summary:"Every package must declare the manufacturer/packer/importer's name & address, the commodity's common name, net quantity, month & year of manufacture, retail sale price, dimensions (where relevant), and consumer-care contact details." },
    { n:7, ch:"Chapter II — Retail Packages", title:"Principal display panel — numeral height", summary:"Sets minimum letter/numeral heights on the principal display panel based on the package's declared net quantity (see Tables I & II)." },
    { n:8, ch:"Chapter II — Retail Packages", title:"Where declarations must appear", summary:"All declarations must appear on the principal display panel, kept clear of surrounding printed matter." },
    { n:9, ch:"Chapter II — Retail Packages", title:"Manner of declaration", summary:"Declarations must be legible, prominent, printed in a contrasting colour, and in Hindi (Devanagari) or English." },
    { n:10, ch:"Chapter II — Retail Packages", title:"Declaration of name & address", summary:"Requires a complete, identifiable address of the manufacturer, packer, or importer on every package." },
    { n:11, ch:"Chapter II — Retail Packages", title:"General provisions on quantity declaration", summary:"Net quantity must exclude packaging weight and reflect what the consumer actually receives." },
    { n:12, ch:"Chapter II — Retail Packages", title:"Manner of declaring quantity", summary:"Quantity must be declared in standard units (mass, length, area, volume, or number) and must avoid vague qualifiers like 'approximately' or 'about'." },
    { n:13, ch:"Chapter II — Retail Packages", title:"Units of weight, measure or number", summary:"Specifies which metric unit to use (grams vs kilograms, millilitres vs litres, etc.) depending on the declared quantity." },
    { n:14, ch:"Chapter II — Retail Packages", title:"Declarations for dimensioned commodities", summary:"Items like bedsheets, towels, and sarees must also declare their finished dimensions." },
    { n:15, ch:"Chapter II — Retail Packages", title:"Declarations where price depends on size/weight", summary:"If a commodity's price depends on its dimensions or weight, both must be declared together." },
    { n:16, ch:"Chapter II — Retail Packages", title:"Declarations for sheet-type products", summary:"Products like tissues or foil must state the number of usable sheets and their dimensions." },
    { n:17, ch:"Chapter II — Retail Packages", title:"Declarations for container-type commodities", summary:"Bags, boxes, and similar containers must declare their count and dimensions in a prescribed format." },
    { n:18, ch:"Chapter II — Retail Packages", title:"Provisions for wholesale/retail dealers", summary:"Dealers cannot sell non-compliant packages, cannot sell above the declared MRP, and cannot alter or obscure the printed price." },
    { n:19, ch:"Chapter II — Retail Packages", title:"Inspection at manufacturer/packer premises", summary:"Empowers Legal Metrology Officers to inspect, sample, and test packages for compliance at the manufacturing site." },
    { n:20, ch:"Chapter II — Retail Packages", title:"Action after inspection", summary:"Details the seizure and enforcement steps to be taken if a manufacturer's packages fail inspection." },
    { n:21, ch:"Chapter II — Retail Packages", title:"Inspection at wholesale/retail premises", summary:"Allows testing at a dealer's premises, typically only after a complaint, suspected tampering, or missing declarations." },
    { n:22, ch:"Chapter II — Retail Packages", title:"Maximum permissible error", summary:"Establishes the allowed margin of error in declared net quantity, detailed in the First Schedule." },
    { n:23, ch:"Chapter II — Retail Packages", title:"Deceptive packaging", summary:"Packages designed to visually exaggerate their contents must be re-packed/re-labelled, or else seized." },
    { n:24, ch:"Chapter III — Wholesale Packages", title:"Wholesale package declarations", summary:"Every wholesale package must declare the manufacturer/importer's details, the commodity's identity, and the total quantity or count inside." },
    { n:25, ch:"Chapter IV — Export & Import", title:"Restrictions on export packages sold in India", summary:"Export-only packages cannot be sold domestically unless re-labelled to meet these rules." },
    { n:26, ch:"Chapter V — Exemptions", title:"Exemptions", summary:"Certain small packages (10g/10ml or less), restaurant/hotel fast food, specific drug formulations, and large agricultural produce packs are exempt." },
    { n:27, ch:"Chapter VI — Registration", title:"Registration of manufacturers, packers & importers", summary:"Anyone who pre-packs or imports commodities must register their name and address with the Director or Controller." },
    { n:28, ch:"Chapter VI — Registration", title:"Registration of a shorter address", summary:"Allows registering an abbreviated address for use on labels, if the Controller finds it sufficiently identifiable." },
    { n:29, ch:"Chapter VI — Registration", title:"Register of manufacturers/packers", summary:"The Controller maintains a public register of all registered manufacturers and packers, open for inspection without fee." },
    { n:30, ch:"Chapter VI — Registration", title:"Circulation of manufacturer/packer lists", summary:"Registered manufacturer/packer lists are compiled state-wise and circulated to enable sampling and inspection." },
    { n:31, ch:"Chapter VII — General", title:"Advertisements", summary:"Advertisements quoting a retail price must also state the net quantity, in the same font size as the price." },
    { n:32, ch:"Chapter VII — General", title:"Penalty for contravention", summary:"Sets fines — up to ₹4,000 for registration-related violations, ₹2,000 for other unspecified contraventions." },
    { n:33, ch:"Chapter VII — General", title:"Power to relax", summary:"Allows the Central Government to relax specific provisions for a manufacturer or packer in genuine, justified cases." },
    { n:34, ch:"Chapter VII — General", title:"Repeal and savings", summary:"Repeals the earlier 1977 Rules, while preserving rights, actions, and proceedings already underway under them." },
  ];

  // Wires up the "Download Report as PDF" button. NOTE: this uses the
  // browser's native print dialog (window.print()), not a real PDF
  // generation library — the user must choose "Save as PDF" in the
  // print dialog themselves.
  document.getElementById('downloadPdfBtn').addEventListener('click', () => {
    goto('scan');
    setTimeout(() => window.print(), 100);
  });

  // Renders the Rule Desk list, grouped by chapter, with live search
  // filtering across rule number, title, summary, and chapter name.
  function renderRules(filter = "") {
    const list = document.getElementById('ruleList');
    list.innerHTML = '';
    let lastChapter = null;
    const q = filter.trim().toLowerCase();
    RULES.forEach(r => {
      if (q && !(r.title.toLowerCase().includes(q) || r.summary.toLowerCase().includes(q) || r.ch.toLowerCase().includes(q) || String(r.n) === q)) return;
      if (r.ch !== lastChapter) {
        const chDiv = document.createElement('div');
        chDiv.className = 'chapter-label';
        chDiv.textContent = r.ch;
        list.appendChild(chDiv);
        lastChapter = r.ch;
      }
      const row = document.createElement('div');
      row.className = 'rule-row';
      row.innerHTML = `<span class="rule-num">${String(r.n).padStart(2,'0')}</span><span class="rule-title">${r.title}</span><div class="rule-summary">${r.summary}</div>`;
      row.addEventListener('click', () => row.classList.toggle('open'));
      list.appendChild(row);
    });
  }
  document.getElementById('ruleSearch').addEventListener('input', e => renderRules(e.target.value));

  // ---------- Initial render on page load ----------
  renderRules();
  renderAll();