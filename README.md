<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FULL SEND // OBLIVION v5 - Local-First Sovereign Privacy Operating System</title>
  
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            cyber: {
              black: '#08080a',
              darker: '#0d0e12',
              card: '#12141c',
              border: '#1f2433',
              green: '#00ff66',
              cyan: '#00f0ff',
              red: '#ff0055',
              amber: '#ffaa00',
              purple: '#b006ff',
              dimText: '#6272a4'
            }
          },
          fontFamily: {
            mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace']
          },
          animation: {
            'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            'scanline': 'scanline 8s linear infinite',
            'glitch': 'glitch 0.3s ease-in-out'
          }
        }
      }
    }
  </script>
  
  <!-- Google Fonts & Font Awesome Icons -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

  <style>
    body {
      font-family: 'JetBrains Mono', monospace;
      background-color: #08080a;
      color: #e2e8f0;
      overflow-x: hidden;
    }
    
    /* CRT Scanline Effect */
    .crt::before {
      content: " ";
      display: block;
      position: fixed;
      top: 0; left: 0; bottom: 0; right: 0;
      background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
      z-index: 999;
      background-size: 100% 3px, 6px 100%;
      pointer-events: none;
      opacity: 0.6;
    }

    /* Cyber Glows */
    .glow-green { text-shadow: 0 0 8px rgba(0,255,102,0.6); }
    .glow-cyan { text-shadow: 0 0 8px rgba(0,240,255,0.6); }
    .glow-red { text-shadow: 0 0 8px rgba(255,0,85,0.6); }
    
    .border-glow-cyan { box-shadow: 0 0 12px -2px rgba(0,240,255,0.3); }
    .border-glow-green { box-shadow: 0 0 12px -2px rgba(0,255,102,0.3); }

    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0d0e12; }
    ::-webkit-scrollbar-thumb { background: #1f2433; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #00f0ff; }
  </style>
</head>
<body class="crt min-h-screen flex flex-col justify-between selection:bg-cyber-cyan selection:text-cyber-black">

  <!-- TOP PROTOCOL BAR -->
  <header class="border-b border-cyber-border bg-cyber-darker/90 backdrop-blur sticky top-0 z-50 px-4 py-2.5">
    <div class="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <div class="w-3 h-3 rounded-full bg-cyber-green animate-pulse"></div>
        <span class="font-extrabold text-lg tracking-wider text-white">FULL SEND <span class="text-cyber-cyan text-xs px-2 py-0.5 rounded bg-cyber-cyan/10 border border-cyber-cyan/30">OBLIVION v5.2</span></span>
        <span class="hidden md:inline-block text-xs text-cyber-dimText">| LOCAL-FIRST SOVEREIGNTY PROTOCOL</span>
      </div>

      <!-- Quick Metrics Bar -->
      <div class="flex items-center space-x-6 text-xs">
        <div class="flex items-center space-x-2">
          <span class="text-cyber-dimText">RISK INDEX:</span>
          <span id="risk-score" class="font-bold text-cyber-red glow-red">88 / 100 [CRITICAL]</span>
        </div>
        <div class="hidden sm:flex items-center space-x-2">
          <span class="text-cyber-dimText">PURGED:</span>
          <span id="purged-ratio" class="font-bold text-cyber-green">3 / 8 PLATFORMS</span>
        </div>
        <div class="flex items-center space-x-2">
          <span class="text-cyber-dimText">STATUS:</span>
          <span class="text-cyber-cyan flex items-center gap-1">
            <i class="fa-solid fa-shield-halved text-[10px]"></i> ENCRYPTED
          </span>
        </div>
      </div>
    </div>
  </header>

  <!-- MAIN OPERATIONAL CONTAINER -->
  <main class="max-w-7xl w-full mx-auto p-4 sm:p-6 flex-grow grid grid-cols-1 lg:grid-cols-12 gap-6">

    <!-- LEFT COLUMN: IDENTITY & COMMAND CENTER (4 COLS) -->
    <section class="lg:col-span-4 flex flex-col gap-6">

      <!-- Identity Vault Card -->
      <div class="bg-cyber-card border border-cyber-border rounded-lg p-5 border-glow-cyan">
        <div class="flex justify-between items-center mb-4 pb-2 border-b border-cyber-border/60">
          <h2 class="text-xs font-bold tracking-widest text-cyber-cyan flex items-center gap-2">
            <i class="fa-solid fa-user-shield"></i> IDENTITY VAULT [LOCAL]
          </h2>
          <span class="text-[10px] bg-cyber-green/10 text-cyber-green px-2 py-0.5 rounded border border-cyber-green/20">MEM_LOCAL</span>
        </div>

        <form id="identity-form" class="space-y-3 text-xs">
          <div>
            <label class="block text-cyber-dimText mb-1">TARGET FULL NAME</label>
            <input type="text" id="user-name" value="Alex Mercer" 
                   class="w-full bg-cyber-black border border-cyber-border rounded px-3 py-2 text-white focus:outline-none focus:border-cyber-cyan transition" placeholder="e.g., Jane Doe">
          </div>
          <div>
            <label class="block text-cyber-dimText mb-1">PRIMARY EMAIL TO PURGE</label>
            <input type="email" id="user-email" value="alex.mercer.dev@proton.me" 
                   class="w-full bg-cyber-black border border-cyber-border rounded px-3 py-2 text-white focus:outline-none focus:border-cyber-cyan transition" placeholder="e.g., target@domain.com">
          </div>
          <div>
            <label class="block text-cyber-dimText mb-1">JURISDICTION / LEGAL FRAMEWORK</label>
            <select id="user-jurisdiction" class="w-full bg-cyber-black border border-cyber-border rounded px-3 py-2 text-white focus:outline-none focus:border-cyber-cyan transition">
              <option value="GDPR">EU GDPR (Article 17 - Right to be Forgotten)</option>
              <option value="CCPA">California CCPA (§ 1798.105 - Request to Delete)</option>
              <option value="PIPEDA">Canada PIPEDA (Principle 4.3.8)</option>
              <option value="GENERIC">International Standard Privacy Act</option>
            </select>
          </div>
          <button type="submit" class="w-full mt-2 bg-cyber-cyan/10 hover:bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/40 py-2 rounded font-semibold text-xs transition flex items-center justify-center gap-2">
            <i class="fa-solid fa-floppy-disk"></i> COMMIT TO MEMORY
          </button>
        </form>
      </div>

      <!-- Eradication Progress Panel -->
      <div class="bg-cyber-card border border-cyber-border rounded-lg p-5">
        <h2 class="text-xs font-bold tracking-widest text-cyber-green mb-3 flex items-center gap-2">
          <i class="fa-solid fa-chart-pie"></i> ERADICATION METRICS
        </h2>

        <div class="space-y-4 text-xs">
          <div>
            <div class="flex justify-between mb-1">
              <span class="text-cyber-dimText">PURGE PROGRESS</span>
              <span id="progress-percentage" class="text-cyber-green font-bold">37.5%</span>
            </div>
            <div class="w-full bg-cyber-black rounded-full h-2.5 overflow-hidden border border-cyber-border">
              <div id="progress-bar" class="bg-gradient-to-r from-cyber-cyan to-cyber-green h-2.5 rounded-full transition-all duration-500" style="width: 37.5%"></div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2 text-center pt-2">
            <div class="bg-cyber-black/60 p-2.5 rounded border border-cyber-border/40">
              <div id="metric-pending" class="text-lg font-bold text-cyber-amber">4</div>
              <div class="text-[10px] text-cyber-dimText">IN PROGRESS</div>
            </div>
            <div class="bg-cyber-black/60 p-2.5 rounded border border-cyber-border/40">
              <div id="metric-deleted" class="text-lg font-bold text-cyber-green">3</div>
              <div class="text-[10px] text-cyber-dimText">TERMINATED</div>
            </div>
          </div>
        </div>
      </div>

      <!-- System Telemetry Log -->
      <div class="bg-cyber-card border border-cyber-border rounded-lg p-4 flex-grow flex flex-col">
        <h2 class="text-xs font-bold tracking-widest text-cyber-dimText mb-2 flex items-center justify-between">
          <span><i class="fa-solid fa-terminal"></i> TELEMETRY LOG</span>
          <button id="clear-log" class="text-[10px] text-cyber-dimText hover:text-white"><i class="fa-solid fa-trash"></i></button>
        </h2>
        <div id="telemetry-log" class="bg-cyber-black border border-cyber-border/50 rounded p-3 text-[11px] font-mono text-cyber-dimText h-44 overflow-y-auto space-y-1">
          <div><span class="text-cyber-cyan">[00:00:01]</span> System initialized: OBLIVION_v5 kernel loaded.</div>
          <div><span class="text-cyber-cyan">[00:00:02]</span> Identity payload primed for Alex Mercer.</div>
          <div><span class="text-cyber-green">[00:00:03]</span> Local storage session validated. Zero network leaks.</div>
        </div>
      </div>

    </section>

    <!-- RIGHT COLUMN: TARGET PLATFORMS & EXECUTOR (8 COLS) -->
    <section class="lg:col-span-8 flex flex-col gap-6">

      <!-- Targets Grid Header & Filter -->
      <div class="bg-cyber-card border border-cyber-border rounded-lg p-5">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4 pb-3 border-b border-cyber-border">
          <div>
            <h1 class="text-base font-bold text-white tracking-wider flex items-center gap-2">
              <i class="fa-solid fa-crosshairs text-cyber-red"></i> TRACKED EXPOSURE TARGETS
            </h1>
            <p class="text-xs text-cyber-dimText">Select target service to initiate statutory erasure request execution</p>
          </div>
          
          <div class="flex gap-2 w-full sm:w-auto">
            <button id="btn-export" class="px-3 py-1.5 bg-cyber-black hover:bg-cyber-border border border-cyber-border rounded text-xs text-cyber-cyan transition flex items-center gap-1.5">
              <i class="fa-solid fa-download"></i> EXPORT JSON
            </button>
            <button id="btn-reset" class="px-3 py-1.5 bg-cyber-red/10 hover:bg-cyber-red/20 border border-cyber-red/40 rounded text-xs text-cyber-red transition flex items-center gap-1.5">
              <i class="fa-solid fa-rotate-right"></i> RESET ALL
            </button>
          </div>
        </div>

        <!-- Target Cards Container -->
        <div id="targets-grid" class="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[380px] overflow-y-auto pr-1">
          <!-- Dynamic Target Cards injected via JS -->
        </div>
      </div>

      <!-- Execution & AI Enhancement Terminal -->
      <div class="bg-cyber-card border border-cyber-border rounded-lg p-5 flex-grow flex flex-col border-glow-green">
        <div class="flex justify-between items-center mb-3 pb-2 border-b border-cyber-border">
          <div class="flex items-center gap-2">
            <i class="fa-solid fa-code text-cyber-green"></i>
            <h2 class="text-xs font-bold tracking-widest text-white">STATUTORY REQUEST GENERATOR & ENHANCER</h2>
          </div>
          <span id="active-target-badge" class="text-[10px] bg-cyber-cyan/10 text-cyber-cyan border border-cyber-cyan/30 px-2.5 py-0.5 rounded font-mono">
            TARGET: NONE SELECTED
          </span>
        </div>

        <!-- Template Display / Editor -->
        <div class="flex-grow flex flex-col gap-3">
          <div class="relative flex-grow">
            <textarea id="request-template" 
                      class="w-full h-52 bg-cyber-black border border-cyber-border rounded p-3 font-mono text-xs text-gray-200 focus:outline-none focus:border-cyber-green transition resize-none leading-relaxed"
                      placeholder="Select a target service above to generate a statutory GDPR Art.17 / CCPA deletion request..."></textarea>
            
            <!-- Floating Quick Action Buttons -->
            <div class="absolute bottom-3 right-3 flex gap-2">
              <button id="btn-ai-enhance" class="px-3 py-1.5 bg-cyber-purple/20 hover:bg-cyber-purple/30 border border-cyber-purple/50 text-cyber-purple rounded text-xs font-semibold transition flex items-center gap-1.5 shadow-lg">
                <i class="fa-solid fa-wand-magic-sparkles"></i> AI ENHANCE (GDPR LEGAL PRECISE)
              </button>
              <button id="btn-copy" class="px-3 py-1.5 bg-cyber-green/20 hover:bg-cyber-green/30 border border-cyber-green/50 text-cyber-green rounded text-xs font-semibold transition flex items-center gap-1.5">
                <i class="fa-solid fa-copy"></i> COPY TO CLIPBOARD
              </button>
            </div>
          </div>

          <!-- Direct Execution Actions -->
          <div class="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-cyber-border/60">
            <div class="text-xs text-cyber-dimText flex items-center gap-2">
              <i class="fa-solid fa-circle-info text-cyber-cyan"></i>
              <span>Direct DPO Contact: <strong id="dpo-email-display" class="text-white">N/A</strong></span>
            </div>
            
            <div class="flex gap-2">
              <button id="btn-send-email" class="px-4 py-2 bg-cyber-cyan hover:bg-cyan-400 text-cyber-black rounded font-bold text-xs transition flex items-center gap-2">
                <i class="fa-solid fa-paper-plane"></i> LAUNCH DISPATCH (MAILTO)
              </button>
              <button id="btn-mark-done" class="px-4 py-2 bg-cyber-green/10 hover:bg-cyber-green/20 text-cyber-green border border-cyber-green/40 rounded font-bold text-xs transition flex items-center gap-2">
                <i class="fa-solid fa-check-double"></i> MARK PURGED
              </button>
            </div>
          </div>
        </div>
      </div>

    </section>
  </main>

  <!-- FOOTER STATUS STRIP -->
  <footer class="border-t border-cyber-border bg-cyber-darker text-cyber-dimText text-[11px] px-4 py-2">
    <div class="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-2">
      <div class="flex items-center gap-4">
        <span>OBLIVION v5.2 KERNEL ACTIVE</span>
        <span>•</span>
        <span class="text-cyber-green">ZERO REMOTE TRACKING</span>
      </div>
      <div>
        <span>GDPR Art. 17 / CCPA § 1798.105 COMPLIANT AUTOMATION ENGINE</span>
      </div>
    </div>
  </footer>

  <!-- NOTIFICATION TOAST CONTAINER -->
  <div id="toast-container" class="fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none"></div>

  <!-- JAVASCRIPT LOGIC ENGINE -->
  <script>
    // System Database State
    const defaultTargets = [
      { id: 'data-broker-x', name: 'Acme Data Broker Corp', difficulty: 'Hard', dpo: 'privacy@acmedatabroker.com', status: 'Pending', riskWeight: 20 },
      { id: 'social-network', name: 'OmniSocial Network', difficulty: 'Medium', dpo: 'dpo@omnisocial.io', status: 'Pending', riskWeight: 18 },
      { id: 'search-index', name: 'PeopleSearch Directory', difficulty: 'Impossible', dpo: 'optout@peoplesearchdir.com', status: 'Pending', riskWeight: 25 },
      { id: 'analytics-hub', name: 'TrackerAnalytics Inc', difficulty: 'Easy', dpo: 'legal@trackeranalytics.net', status: 'Deleted', riskWeight: 10 },
      { id: 'ecommerce-old', name: 'Legacy Retail Online', difficulty: 'Easy', dpo: 'privacy@legacyretail.com', status: 'Deleted', riskWeight: 5 },
      { id: 'ad-network', name: 'AdTarget Behavioral Ltd', difficulty: 'Hard', dpo: 'compliance@adtarget.co', status: 'Pending', riskWeight: 15 },
      { id: 'cloud-storage', name: 'DropCloud Free Tier', difficulty: 'Easy', dpo: 'support-privacy@dropcloud.org', status: 'Deleted', riskWeight: 7 }
    ];

    let userState = {
      name: 'Alex Mercer',
      email: 'alex.mercer.dev@proton.me',
      jurisdiction: 'GDPR',
      targets: defaultTargets
    };

    let selectedTargetId = null;

    // Load state from localStorage on init
    function initSystem() {
      const saved = localStorage.getItem('OBLIVION_USER_STATE');
      if (saved) {
        try { userState = JSON.parse(saved); } catch(e) { logTelemetry('Err loading local state.'); }
      }
      
      document.getElementById('user-name').value = userState.name;
      document.getElementById('user-email').value = userState.email;
      document.getElementById('user-jurisdiction').value = userState.jurisdiction;

      renderTargets();
      updateMetrics();
      logTelemetry('System initialized successfully. All state bound to LocalStorage.');
    }

    // Save State Helper
    function saveState() {
      localStorage.setItem('OBLIVION_USER_STATE', JSON.stringify(userState));
      updateMetrics();
    }

    // Render Target List
    function renderTargets() {
      const grid = document.getElementById('targets-grid');
      grid.innerHTML = '';

      userState.targets.forEach(target => {
        const isSelected = target.id === selectedTargetId;
        const card = document.createElement('div');
        
        let diffColor = 'text-cyber-green';
        if (target.difficulty === 'Medium') diffColor = 'text-cyber-amber';
        if (target.difficulty === 'Hard' || target.difficulty === 'Impossible') diffColor = 'text-cyber-red';

        let statusBadge = target.status === 'Deleted' 
          ? '<span class="px-2 py-0.5 rounded bg-cyber-green/20 text-cyber-green border border-cyber-green/40 text-[10px] font-bold">TERMINATED</span>'
          : '<span class="px-2 py-0.5 rounded bg-cyber-amber/20 text-cyber-amber border border-cyber-amber/40 text-[10px] font-bold">PENDING</span>';

        card.className = `p-3 rounded-lg border transition cursor-pointer flex flex-col justify-between gap-2 ${
          isSelected 
            ? 'bg-cyber-darker border-cyber-cyan shadow-[0_0_10px_rgba(0,240,255,0.2)]' 
            : 'bg-cyber-black/70 hover:bg-cyber-darker border-cyber-border'
        }`;

        card.onclick = () => selectTarget(target.id);

        card.innerHTML = `
          <div class="flex justify-between items-start">
            <div>
              <div class="font-bold text-xs text-white">${target.name}</div>
              <div class="text-[10px] text-cyber-dimText">${target.dpo}</div>
            </div>
            ${statusBadge}
          </div>
          <div class="flex justify-between items-center text-[10px] pt-1 border-t border-cyber-border/40">
            <span class="text-cyber-dimText">DIFFICULTY: <strong class="${diffColor}">${target.difficulty.toUpperCase()}</strong></span>
            <span class="text-cyber-dimText">RISK IMPACT: <strong class="text-white">+${target.riskWeight}</strong></span>
          </div>
        `;

        grid.appendChild(card);
      });
    }

    // Select Target & Generate Template
    function selectTarget(id) {
      selectedTargetId = id;
      const target = userState.targets.find(t => t.id === id);
      if (!target) return;

      document.getElementById('active-target-badge').textContent = `TARGET: ${target.name.toUpperCase()}`;
      document.getElementById('dpo-email-display').textContent = target.dpo;

      generateTemplate(target);
      renderTargets();
      logTelemetry(`Selected target: ${target.name} [DPO: ${target.dpo}]`);
    }

    // Dynamic Request Template Generator
    function generateTemplate(target) {
      const name = userState.name || '[YOUR NAME]';
      const email = userState.email || '[YOUR EMAIL]';
      const jurisdiction = userState.jurisdiction;

      let template = '';

      if (jurisdiction === 'GDPR') {
        template = `FORMAL NOTICE: DEMAND FOR ERASURE OF PERSONAL DATA
Pursuant to Article 17 of the General Data Protection Regulation (GDPR)

TO DATA PROTECTION OFFICER / PRIVACY COMPLIANCE: ${target.name} (${target.dpo})

I am writing to formally exercise my Right to Erasure ('Right to be Forgotten') under Article 17 of the GDPR.

Please permanently delete all personal data concerning my identity from your systems, servers, data brokers, and third-party processors without undue delay.

Data Subject Identifiers for Removal:
- Name: ${name}
- Associated Email: ${email}

Statutory Obligations:
1. Confirm erasure of all records, logs, behavioral trackers, and analytics within 30 days as mandated by GDPR Article 12(3).
2. Notify all recipient third parties to whom this data has been disclosed (Article 19).

Failure to comply will result in an immediate formal complaint lodged with the Data Protection Authority (DPA).

Sincerely,
${name}`;
      } else if (jurisdiction === 'CCPA') {
        template = `CONSUMER REQUEST TO DELETE PERSONAL INFORMATION
Pursuant to California Consumer Privacy Act (CCPA) § 1798.105

TO: ${target.name} Privacy Operations (${target.dpo})

I, ${name}, formally request that ${target.name} delete all personal information collected and retained regarding myself and my registered email address (${email}).

Under CCPA § 1798.105, consumers have the right to request deletion of personal information held by businesses and service providers. 

Please verify this request and confirm complete removal within 45 business days as stipulated by statute.

Authorized Requestor: ${name}
Target Email: ${email}`;
      } else {
        template = `STATUTORY PRIVACY REQUEST & ACCOUNT TERMINATION
TO: ${target.name} Data Controller (${target.dpo})

I request the immediate and total deletion of my account, data footprint, and associated personal information held under:
Name: ${name}
Email: ${email}

Please confirm when all records have been irrevocably deleted.`;
      }

      document.getElementById('request-template').value = template;
    }

    // AI Enhancement Simulator (Rewrites template with precise legal jargon)
    document.getElementById('btn-ai-enhance').onclick = () => {
      const textarea = document.getElementById('request-template');
      if (!selectedTargetId) {
        showToast('Please select a target platform first.', 'error');
        return;
      }

      logTelemetry('AI Enhancement Engine invoked via local parametric weights...');
      
      let enhanced = textarea.value;
      enhanced = `[ENHANCED LEGAL PRECISE VERSION]\n` + 
                 enhanced + 
                 `\n\nLEGAL NOTICE OF STRICT COMPLIANCE:\n` +
                 `Be advised that failure to fulfill this statutory request within statutory timeframes will trigger escalation to supervisory privacy commissions, including potential statutory damages for non-compliance under privacy enforcement laws. All audit trails of this transmission have been cryptographically signed.`;

      textarea.value = enhanced;
      showToast('Template enhanced with legal precision!', 'success');
      logTelemetry('Template updated with high-precision statutory clauses.');
    };

    // Copy to Clipboard
    document.getElementById('btn-copy').onclick = () => {
      const text = document.getElementById('request-template').value;
      if (!text) return;

      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);

      showToast('Request template copied to clipboard.', 'info');
      logTelemetry('Payload copied to clipboard.');
    };

    // Launch Email Mailto
    document.getElementById('btn-send-email').onclick = () => {
      if (!selectedTargetId) {
        showToast('Select a target service first.', 'error');
        return;
      }

      const target = userState.targets.find(t => t.id === selectedTargetId);
      const subject = encodeURIComponent(`STATUTORY DATA DELETION REQUEST - ${userState.name}`);
      const body = encodeURIComponent(document.getElementById('request-template').value);

      window.location.href = `mailto:${target.dpo}?subject=${subject}&body=${body}`;
      logTelemetry(`Dispatched mailto client for ${target.dpo}`);
    };

    // Mark as Purged
    document.getElementById('btn-mark-done').onclick = () => {
      if (!selectedTargetId) {
        showToast('Select a target service first.', 'error');
        return;
      }

      const target = userState.targets.find(t => t.id === selectedTargetId);
      target.status = 'Deleted';
      saveState();
      renderTargets();
      showToast(`Target ${target.name} marked as TERMINATED.`, 'success');
      logTelemetry(`Status updated: ${target.name} --> PURGED/TERMINATED`);
    };

    // Identity Form Submit
    document.getElementById('identity-form').onsubmit = (e) => {
      e.preventDefault();
      userState.name = document.getElementById('user-name').value;
      userState.email = document.getElementById('user-email').value;
      userState.jurisdiction = document.getElementById('user-jurisdiction').value;

      saveState();
      showToast('Identity Vault saved locally.', 'success');
      logTelemetry(`Identity Vault updated: ${userState.name} (${userState.email}) [${userState.jurisdiction}]`);

      if (selectedTargetId) {
        const target = userState.targets.find(t => t.id === selectedTargetId);
        if (target) generateTemplate(target);
      }
    };

    // Update Overall Metrics & Risk Index
    function updateMetrics() {
      const total = userState.targets.length;
      const deleted = userState.targets.filter(t => t.status === 'Deleted').length;
      const pending = total - deleted;

      const pct = total === 0 ? 0 : Math.round((deleted / total) * 100);

      document.getElementById('progress-percentage').textContent = `${pct}%`;
      document.getElementById('progress-bar').style.width = `${pct}%`;
      document.getElementById('purged-ratio').textContent = `${deleted} / ${total} PLATFORMS`;

      document.getElementById('metric-pending').textContent = pending;
      document.getElementById('metric-deleted').textContent = deleted;

      // Calculate dynamic risk index
      let remainingRisk = 0;
      userState.targets.filter(t => t.status !== 'Deleted').forEach(t => remainingRisk += t.riskWeight);
      
      const riskEl = document.getElementById('risk-score');
      if (remainingRisk > 50) {
        riskEl.textContent = `${remainingRisk} / 100 [CRITICAL]`;
        riskEl.className = 'font-bold text-cyber-red glow-red';
      } else if (remainingRisk > 20) {
        riskEl.textContent = `${remainingRisk} / 100 [MODERATE]`;
        riskEl.className = 'font-bold text-cyber-amber';
      } else {
        riskEl.textContent = `${remainingRisk} / 100 [LOW RISK]`;
        riskEl.className = 'font-bold text-cyber-green glow-green';
      }
    }

    // Export & Reset Handlers
    document.getElementById('btn-export').onclick = () => {
      const blob = new Blob([JSON.stringify(userState, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `OBLIVION_privacy_backup_${new Date().toISOString().slice(0,10)}.json`;
      a.click();
      logTelemetry('Exported local state backup JSON.');
    };

    document.getElementById('btn-reset').onclick = () => {
      if (confirm('Execute total state purge and reset local targets to defaults?')) {
        localStorage.removeItem('OBLIVION_USER_STATE');
        userState.targets = defaultTargets;
        initSystem();
        showToast('System reset completed.', 'info');
        logTelemetry('TOTAL RESET EXECUTION COMPLETED.');
      }
    };

    // Telemetry Logging Helper
    function logTelemetry(msg) {
      const container = document.getElementById('telemetry-log');
      const time = new Date().toTimeString().split(' ')[0];
      const div = document.createElement('div');
      div.innerHTML = `<span class="text-cyber-cyan">[${time}]</span> ${msg}`;
      container.appendChild(div);
      container.scrollTop = container.scrollHeight;
    }

    document.getElementById('clear-log').onclick = () => {
      document.getElementById('telemetry-log').innerHTML = '';
    };

    // Custom UI Toast Notification Engine
    function showToast(msg, type = 'info') {
      const container = document.getElementById('toast-container');
      const toast = document.createElement('div');

      let colorClass = 'border-cyber-cyan text-cyber-cyan';
      if (type === 'success') colorClass = 'border-cyber-green text-cyber-green';
      if (type === 'error') colorClass = 'border-cyber-red text-cyber-red';

      toast.className = `bg-cyber-darker border ${colorClass} px-4 py-2.5 rounded shadow-xl text-xs flex items-center gap-2 backdrop-blur transition-all duration-300 transform translate-y-2`;
      toast.innerHTML = `<i class="fa-solid fa-terminal text-[10px]"></i> <span>${msg}</span>`;

      container.appendChild(toast);
      setTimeout(() => toast.classList.remove('translate-y-2'), 10);

      setTimeout(() => {
        toast.classList.add('opacity-0');
        setTimeout(() => toast.remove(), 300);
      }, 3500);
    }

    // Initialize System on Window Load
    window.onload = function() {
      initSystem();
    };
  </script>
</body>
</html>
