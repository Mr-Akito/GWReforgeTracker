/**
 * GUILD WARS REFORGED QUEST TRACKER v1.0.3
 * HTML5 Application Logic & Adaptive 60 FPS Animation Engine
 */

(function () {
  'use strict';

  // --- APPLICATION STATE ---
  let backend = null;
  let hasInitialProfSync = false;
  let lastProfileSynced = null;

  // Internal In-App Wiki Browser Navigation Stack
  let wikiHistory = [];
  let wikiHistoryIndex = -1;

  let state = {
    currentProfile: 'Default',
    profiles: ['Default'],
    currentProfession: 'All Professions',
    currentCampaign: 'All',
    statusFilter: 'All Quests',
    profFilter: 'All Professions',
    searchText: '',
    selectedQuestName: null,
    questDb: {},
    questMeta: {},
    questStatus: {},
    lockedQuests: [],
    preferences: {
      color_scheme: 'classic',
      dark_mode: true,
      show_hidden: false,
      show_locked: true,
      show_timestamps: true,
      low_gpu_mode: false,
      animation_level: 'reduced',
      cursor_light: 'subtle',
      liquid_wave_anim: true,
      card_density: 'comfortable',
      auto_close: false
    }
  };

  const PROFESSIONS_LIST = [
    'All Professions', 'Warrior', 'Ranger', 'Monk', 'Necromancer', 'Mesmer',
    'Elementalist', 'Assassin', 'Ritualist', 'Paragon', 'Dervish'
  ];

  const MUTUALLY_EXCLUSIVE_MAP = {
    'Imperial Assistance': ['Red Tape'],
    'Red Tape': ['Imperial Assistance'],
    'Secrets in the Shadow': ['For a Price'],
    'For a Price': ['Secrets in the Shadow'],
    'Loyal \'til the End': ['Money on the Side'],
    'Money on the Side': ['Loyal \'til the End'],
    'A Peaceful Solution': ['A Loose Cannon'],
    'A Loose Cannon': ['A Peaceful Solution'],
    'Death with Honor': ['The Rite of Valor'],
    'The Rite of Valor': ['Death with Honor'],
    'A Burning Desire': ['Douse Your Enthusiasm'],
    'Douse Your Enthusiasm': ['A Burning Desire'],
    'Refuse to Drink': ['Drink from the Chalice of Corruption'],
    'Drink from the Chalice of Corruption': ['Refuse to Drink'],
    'Defend Droknar\'s Forge': ['The Hero\'s Challenge'],
    'The Hero\'s Challenge': ['Defend Droknar\'s Forge'],
    'Securing the Iron Mines': ['Defend the Temple of War'],
    'Defend the Temple of War': ['Securing the Iron Mines']
  };

  const MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  // --- TIMESTAMP FORMATTER ('Month DD, YYYY, HH:MM am/pm') ---
  function formatQuestTimestamp(input) {
    if (!input) {
      const now = new Date();
      return formatDateObj(now);
    }
    if (input instanceof Date) {
      return formatDateObj(input);
    }
    const str = String(input).trim();
    if (!str) return '';

    // Check if already formatted as 'Month DD, YYYY, HH:MM am/pm'
    const exactMatch = /^([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4}),\s*(\d{1,2}):(\d{2})\s*(am|pm)$/i.exec(str);
    if (exactMatch) {
      const mName = exactMatch[1].charAt(0).toUpperCase() + exactMatch[1].slice(1).toLowerCase();
      const day = String(exactMatch[2]).padStart(2, '0');
      const year = exactMatch[3];
      const hr = String(exactMatch[4]).padStart(2, '0');
      const min = exactMatch[5];
      const ampm = exactMatch[6].toLowerCase();
      return `${mName} ${day}, ${year}, ${hr}:${min} ${ampm}`;
    }

    // Check legacy format 'MM / DD / YYYY HH:MM AM/PM'
    const slashMatch = /^(\d{1,2})\s*\/\s*(\d{1,2})\s*\/\s*(\d{4})\s+(\d{1,2}):(\d{2})\s*(AM|PM)$/i.exec(str);
    if (slashMatch) {
      const mIdx = parseInt(slashMatch[1], 10) - 1;
      const mName = MONTH_NAMES[mIdx] || 'January';
      const day = String(slashMatch[2]).padStart(2, '0');
      const year = slashMatch[3];
      const hr = String(slashMatch[4]).padStart(2, '0');
      const min = slashMatch[5];
      const ampm = slashMatch[6].toLowerCase();
      return `${mName} ${day}, ${year}, ${hr}:${min} ${ampm}`;
    }

    const parsed = new Date(str);
    if (!isNaN(parsed.getTime())) {
      return formatDateObj(parsed);
    }
    return str;
  }

  function formatDateObj(dt) {
    const mName = MONTH_NAMES[dt.getMonth()];
    const day = String(dt.getDate()).padStart(2, '0');
    const year = dt.getFullYear();
    let hr = dt.getHours() % 12;
    if (hr === 0) hr = 12;
    const hrStr = String(hr).padStart(2, '0');
    const minStr = String(dt.getMinutes()).padStart(2, '0');
    const ampm = dt.getHours() < 12 ? 'am' : 'pm';
    return `${mName} ${day}, ${year}, ${hrStr}:${minStr} ${ampm}`;
  }

  // --- INITIALIZATION ---
  document.addEventListener('DOMContentLoaded', () => {
    detectClientDisplayProfile();
    initAuroraCanvas();
    initSpotlightTracking();
    initUIEvents();
    setupQWebChannel();
  });

  // --- Aurora Canvas Background ---
  let auroraRafId = null;
  let auroraCtx = null;
  let auroraCanvas = null;

  function stopAuroraCanvas() {
    if (auroraRafId) {
      cancelAnimationFrame(auroraRafId);
      auroraRafId = null;
    }
    if (auroraCtx && auroraCanvas) {
      auroraCtx.clearRect(0, 0, auroraCanvas.width, auroraCanvas.height);
    }
  }

  function startAuroraCanvas() {
    if (auroraRafId) return;
    if (state.preferences.low_gpu_mode || state.preferences.animation_level === 'minimal') {
      stopAuroraCanvas();
      return;
    }
    if (auroraCanvas && typeof window.drawAuroraGlobal === 'function') {
      auroraRafId = requestAnimationFrame(window.drawAuroraGlobal);
    }
  }

  function initAuroraCanvas() {
    const canvas = document.getElementById('aurora-canvas');
    if (!canvas) return;
    auroraCanvas = canvas;
    const ctx = canvas.getContext('2d', { alpha: true });
    auroraCtx = ctx;
    let width = 0;
    let height = 0;
    let lastFrameTime = 0;

    function resize() {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize, { passive: true });
    resize();

    function createOrbSprite(radius, colorStr) {
      const off = document.createElement('canvas');
      off.width = radius * 2;
      off.height = radius * 2;
      const oCtx = off.getContext('2d');
      const grad = oCtx.createRadialGradient(radius, radius, 0, radius, radius, radius);
      grad.addColorStop(0, colorStr);
      grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      oCtx.fillStyle = grad;
      oCtx.beginPath();
      oCtx.arc(radius, radius, radius, 0, Math.PI * 2);
      oCtx.fill();
      return off;
    }

    const orbs = [
      { x: width * 0.2, y: height * 0.3, r: 220, vx: 0.14, vy: 0.10, sprite: createOrbSprite(220, 'rgba(212, 175, 55, 0.045)') },
      { x: width * 0.75, y: height * 0.4, r: 250, vx: -0.12, vy: 0.13, sprite: createOrbSprite(250, 'rgba(34, 197, 94, 0.035)') },
      { x: width * 0.45, y: height * 0.78, r: 200, vx: 0.10, vy: -0.11, sprite: createOrbSprite(200, 'rgba(96, 165, 250, 0.035)') }
    ];

    function drawAurora(timestamp) {
      auroraRafId = null;

      if (state.preferences.low_gpu_mode || state.preferences.animation_level === 'minimal') {
        stopAuroraCanvas();
        return;
      }

      // Suspend RAF rendering while modals or wizards are open to prevent compositor flicker
      if (document.querySelector('.modal-backdrop.open')) {
        auroraRafId = requestAnimationFrame(drawAurora);
        return;
      }

      auroraRafId = requestAnimationFrame(drawAurora);

      // Moderate canvas refresh to ~30 FPS (33ms) to eliminate GPU compositor load
      if (timestamp - lastFrameTime < 33) {
        return;
      }
      lastFrameTime = timestamp;

      ctx.clearRect(0, 0, width, height);
      for (let i = 0; i < orbs.length; i++) {
        const orb = orbs[i];
        orb.x += orb.vx;
        orb.y += orb.vy;
        if (orb.x < -100 || orb.x > width + 100) orb.vx *= -1;
        if (orb.y < -100 || orb.y > height + 100) orb.vy *= -1;
        ctx.drawImage(orb.sprite, orb.x - orb.r, orb.y - orb.r);
      }
    }
    window.drawAuroraGlobal = drawAurora;

    if (!state.preferences.low_gpu_mode && state.preferences.animation_level !== 'minimal') {
      auroraRafId = requestAnimationFrame(drawAurora);
    }
  }

  // --- Cursor Spotlight ---
  function initSpotlightTracking() {
    const panels = document.querySelectorAll('.spotlight-panel');
    panels.forEach(panel => {
      let rafPending = false;
      let lastX = -600;
      let lastY = -600;

      panel.addEventListener('mousemove', e => {
        if (state.preferences.low_gpu_mode || state.preferences.cursor_light === 'off') {
          return;
        }
        lastX = e.clientX;
        lastY = e.clientY;
        if (!rafPending) {
          rafPending = true;
          requestAnimationFrame(() => {
            const rect = panel.getBoundingClientRect();
            panel.style.setProperty('--mouse-x', `${lastX - rect.left}px`);
            panel.style.setProperty('--mouse-y', `${lastY - rect.top}px`);
            rafPending = false;
          });
        }
      }, { passive: true });
    });
  }

  // --- Python Backend Channel ---
  function setupQWebChannel() {
    if (typeof QWebChannel !== 'undefined' && typeof qt !== 'undefined' && qt.webChannelTransport) {
      new QWebChannel(qt.webChannelTransport, channel => {
        backend = channel.objects.pyBridge;
        window.backend = backend;

        backend.data_changed.connect(onBackendDataChanged);
        if (backend.quest_status_updated) {
          backend.quest_status_updated.connect(onQuestStatusDelta);
        }
        if (backend.preferences_updated) {
          backend.preferences_updated.connect(onPreferencesUpdated);
        }
        backend.sync_progress.connect(onSyncProgress);
        backend.sync_finished.connect(onSyncFinished);
        backend.wiki_content_ready.connect(onWikiContentReady);
        if (backend.update_check_result) {
          backend.update_check_result.connect(onUpdateCheckResult);
        }
        if (backend.export_progression_ready) {
          backend.export_progression_ready.connect(onExportProgressionReady);
        }
        if (backend.import_progression_finished) {
          backend.import_progression_finished.connect(onImportProgressionFinished);
        }

        backend.request_initial_data();
      });
    } else {
      console.warn('Qt WebChannel not detected. Running in standalone preview mode.');
      initMockData();
    }
  }

  function onBackendDataChanged(jsonStr) {
    try {
      const data = JSON.parse(jsonStr);
      updateFullState(data);
    } catch (e) {
      console.error('Error parsing backend state data:', e);
    }
  }

  function onQuestStatusDelta(jsonStr) {
    try {
      const payload = JSON.parse(jsonStr);
      if (payload.quest_status) {
        state.questStatus = payload.quest_status;
      }
      if (payload.locked_quests) {
        state.lockedQuests = payload.locked_quests;
      }
      syncQuestStatusAcrossUI(payload.quest_name || '');
    } catch (e) {
      console.error('Error parsing quest status delta:', e);
    }
  }

  function onPreferencesUpdated(jsonStr) {
    try {
      const prefs = JSON.parse(jsonStr);
      state.preferences = Object.assign({}, state.preferences, prefs);
      applyPreferencesToDOM();
      renderQuestList(false);
      updateProgressDisplay();
    } catch (e) {
      console.error('Error parsing preferences update:', e);
    }
  }

  function updateFullState(data) {
    const profileChanged = data.current_profile && data.current_profile !== lastProfileSynced;
    if (data.current_profile) {
      state.currentProfile = data.current_profile;
      lastProfileSynced = data.current_profile;
    }
    if (data.profiles) state.profiles = data.profiles;
    if (data.profession) {
      state.currentProfession = data.profession;
      if (!hasInitialProfSync || profileChanged) {
        state.profFilter = data.profession;
        hasInitialProfSync = true;
      }
    }
    if (data.preferences) {
      state.preferences = Object.assign({}, state.preferences, data.preferences);
    } else {
      if (data.color_scheme) state.preferences.color_scheme = data.color_scheme;
      if (data.dark_mode !== undefined) state.preferences.dark_mode = data.dark_mode;
    }
    if (data.quest_db) state.questDb = data.quest_db;
    if (data.quest_meta) state.questMeta = data.quest_meta;
    if (data.quest_status) state.questStatus = data.quest_status;
    if (data.locked_quests) state.lockedQuests = data.locked_quests;

    applyPreferencesToDOM();
    renderProfileSection();
    renderProfessionFilterDropdown();
    renderQuestList(false);
    syncActiveDossierStatus();
    annotateWikiQuestLinks();
    updateProgressDisplay();

    // Check for first launch setup onboarding
    if (data.is_first_run) {
      openFirstLaunchSetupModal();
    }
  }

  // --- Preferences & Theme ---
  function syncSwitchClasses() {
    document.querySelectorAll('.switch input[type="checkbox"]').forEach(cb => {
      const sw = cb.closest('.switch');
      if (sw) sw.classList.toggle('is-checked', Boolean(cb.checked));
    });
  }

  function applyPreferencesToDOM() {
    const p = state.preferences;
    const b = document.body;

    // Color scheme (Classic vs Alternate Yellow/Green)
    b.classList.remove('scheme-classic', 'scheme-alternate');
    b.classList.add(p.color_scheme === 'alternate' ? 'scheme-alternate' : 'scheme-classic');

    // Theme Mode (Dark vs Light)
    b.classList.remove('theme-dark', 'theme-light');
    b.classList.add(p.dark_mode ? 'theme-dark' : 'theme-light');

    // Low GPU / Performance Mode
    b.classList.toggle('low-gpu-mode', Boolean(p.low_gpu_mode));
    const gpuBtn = document.getElementById('btn-gpu-toggle');
    if (gpuBtn) {
      gpuBtn.classList.toggle('active-mode', Boolean(p.low_gpu_mode));
      gpuBtn.title = p.low_gpu_mode
        ? 'Low GPU Mode: ON (Click to disable)'
        : 'Low GPU Mode: OFF (Click to enable)';
    }
    const settingsGpuToggle = document.getElementById('toggle-low-gpu');
    if (settingsGpuToggle) {
      settingsGpuToggle.checked = Boolean(p.low_gpu_mode);
    }
    const setupGpuToggle = document.getElementById('setup-low-gpu');
    if (setupGpuToggle) {
      setupGpuToggle.checked = Boolean(p.low_gpu_mode);
    }

    if (p.low_gpu_mode || p.animation_level === 'minimal') {
      stopAuroraCanvas();
    } else {
      startAuroraCanvas();
    }

    // Animation Intensity
    b.classList.remove('anim-full', 'anim-reduced', 'anim-minimal');
    b.classList.add(`anim-${p.animation_level || 'reduced'}`);

    // Cursor Trailing Light
    b.classList.remove('cursor-light-off', 'cursor-light-subtle', 'cursor-light-standard');
    b.classList.add(`cursor-light-${p.cursor_light || 'subtle'}`);

    // Liquid Wave Bar Motion
    b.classList.toggle('no-liquid-wave', !p.liquid_wave_anim);

    // Card Density
    b.classList.toggle('density-compact', p.card_density === 'compact');

    // Card Timestamps
    b.classList.toggle('hide-card-timestamps', !p.show_timestamps);

    syncSwitchClasses();
  }

  // --- Campaign Tabs ---
  function initTabSlider() {
    const slider = document.getElementById('tab-pill-slider');
    const tabs = document.querySelectorAll('.tab-item');
    const activeTab = document.querySelector('.tab-item.active');

    function positionSlider(tabEl, animate = true) {
      if (!tabEl || !slider) return;
      const track = document.getElementById('campaign-nav-track');
      const trackRect = track.getBoundingClientRect();
      const tabRect = tabEl.getBoundingClientRect();
      const leftOffset = tabRect.left - trackRect.left;
      const targetWidth = tabRect.width;

      const useAnim = animate && !state.preferences.low_gpu_mode && state.preferences.animation_level !== 'minimal';
      if (useAnim && typeof anime !== 'undefined') {
        anime.remove(slider);
        anime({
          targets: slider,
          translateX: leftOffset,
          width: targetWidth,
          duration: 240,
          easing: 'easeOutCubic'
        });
      } else {
        slider.style.transform = `translateX(${leftOffset}px)`;
        slider.style.width = `${targetWidth}px`;
      }
    }

    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        state.currentCampaign = tab.getAttribute('data-campaign');
        document.getElementById('reset-campaign-label').textContent = state.currentCampaign;
        positionSlider(tab, true);

        const viewport = document.getElementById('quest-list-viewport');
        if (viewport) viewport.scrollTop = 0;

        renderQuestList(true);
        updateProgressDisplay();
      });
    });

    if (activeTab) {
      setTimeout(() => positionSlider(activeTab, false), 50);
    }
    window.addEventListener('resize', () => {
      const currentActive = document.querySelector('.tab-item.active');
      if (currentActive) positionSlider(currentActive, false);
    }, { passive: true });
  }

  // --- Quest List Rendering ---
  function renderQuestList(allowEntranceAnim = false) {
    const container = document.getElementById('quest-list-scroll');
    const viewport = document.getElementById('quest-list-viewport');
    if (!container) return;

    const prevScrollTop = viewport ? viewport.scrollTop : 0;
    container.innerHTML = '';

    const currentCampaign = state.currentCampaign;
    let listData = [];

    if (currentCampaign === 'All') {
      const order = ['Prophecies', 'Factions', 'Nightfall', 'Eye of the North', 'Beyond', 'LDoA'];
      order.forEach(camp => {
        if (state.questDb[camp]) {
          listData.push(`--- ${camp.toUpperCase()} ---`);
          listData = listData.concat(state.questDb[camp]);
        }
      });
    } else {
      listData = state.questDb[currentCampaign] || [];
    }

    const search = state.searchText.toLowerCase().trim();
    const mode = state.statusFilter;
    const profFilter = state.profFilter.toLowerCase();
    const isProfAll = (state.profFilter === 'All Professions');
    const showHidden = Boolean(state.preferences.show_hidden);
    const showLocked = Boolean(state.preferences.show_locked);

    let currentSectionHeader = null;
    let currentSectionQuests = [];
    const fragment = document.createDocumentFragment();
    let visibleCount = 0;

    for (let i = 0; i < listData.length; i++) {
      const item = listData[i];
      if (item.includes('---')) {
        if (currentSectionHeader && currentSectionQuests.length > 0) {
          fragment.appendChild(currentSectionHeader);
          for (let j = 0; j < currentSectionQuests.length; j++) {
            fragment.appendChild(currentSectionQuests[j]);
          }
        }
        currentSectionHeader = document.createElement('div');
        currentSectionHeader.className = 'quest-section-header';
        currentSectionHeader.textContent = item.replace(/---/g, '').trim();
        currentSectionQuests = [];
      } else {
        const questName = item;
        const statusData = state.questStatus[questName] || { status: 0, timestamp: null, is_hidden: false };
        const meta = state.questMeta[questName] || {};
        const isHidden = Boolean(statusData.is_hidden);
        const isLocked = state.lockedQuests.includes(questName);

        if (isHidden && !showHidden) continue;
        if (isLocked && !showLocked) continue;

        if (search && !questName.toLowerCase().includes(search) && !(meta.location || '').toLowerCase().includes(search)) {
          continue;
        }

        if (mode === 'Not Started' && statusData.status !== 0) continue;
        if (mode === 'In Progress' && statusData.status !== 1) continue;
        if (mode === 'Completed' && statusData.status !== 2) continue;

        const profReq = (meta.profession || '').toLowerCase();
        if (!isProfAll && profReq && !profReq.includes(profFilter)) {
          continue;
        }

        const card = createQuestCard(questName, statusData, meta, isLocked);
        currentSectionQuests.push(card);
        visibleCount++;
      }
    }

    if (currentSectionHeader && currentSectionQuests.length > 0) {
      fragment.appendChild(currentSectionHeader);
      for (let j = 0; j < currentSectionQuests.length; j++) {
        fragment.appendChild(currentSectionQuests[j]);
      }
    }

    container.appendChild(fragment);

    const countLabel = document.getElementById('visible-count-label');
    if (countLabel) {
      countLabel.textContent = `Showing ${visibleCount} quest${visibleCount === 1 ? '' : 's'}`;
    }

    if (!allowEntranceAnim && viewport) {
      viewport.scrollTop = prevScrollTop;
    }

    // Only animate top 14 visible cards when explicitly switching tabs in Full animation mode
    if (
      allowEntranceAnim &&
      !state.preferences.low_gpu_mode &&
      state.preferences.animation_level === 'full' &&
      typeof anime !== 'undefined'
    ) {
      const topCards = Array.from(container.querySelectorAll('.quest-card')).slice(0, 14);
      if (topCards.length > 0) {
        anime({
          targets: topCards,
          translateY: [8, 0],
          opacity: [0.25, 1],
          delay: anime.stagger(8),
          easing: 'easeOutQuad',
          duration: 160
        });
      }
    }
  }

  function createQuestCard(name, statusData, meta, isLocked) {
    const card = document.createElement('div');
    card.className = 'quest-card';
    if (statusData.status === 1) card.classList.add('status-in-progress');
    if (statusData.status === 2) card.classList.add('status-completed');
    if (isLocked) card.classList.add('locked');
    if (state.selectedQuestName === name) card.classList.add('active-selected');

    card.setAttribute('data-quest', name);

    // Checkbox
    const checkbox = document.createElement('div');
    checkbox.className = 'quest-checkbox';
    checkbox.title = isLocked ? 'Locked by mutually exclusive quest' : 'Click to cycle quest status';
    checkbox.innerHTML = `
      <div class="icon-in-progress"></div>
      <svg class="icon-check" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="3">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
    `;

    checkbox.addEventListener('click', e => {
      e.stopPropagation();
      const currentlyLocked = state.lockedQuests.includes(name);
      if (currentlyLocked) return;
      cycleQuestStatus(name);
    });

    // Content
    const content = document.createElement('div');
    content.className = 'quest-card-content';

    const topRow = document.createElement('div');
    topRow.className = 'quest-card-top';

    const title = document.createElement('span');
    title.className = 'quest-title-text';
    title.textContent = name;
    topRow.appendChild(title);

    if (meta.profession) {
      const pBadge = document.createElement('span');
      pBadge.className = 'prof-badge';
      pBadge.textContent = meta.profession.replace('primary or secondary', '').replace('primary', '').trim().toUpperCase();
      topRow.appendChild(pBadge);
    }

    if (statusData.is_hidden) {
      const hBadge = document.createElement('span');
      hBadge.className = 'hidden-badge';
      hBadge.textContent = 'HIDDEN';
      topRow.appendChild(hBadge);
    }

    if (isLocked) {
      const lockBadge = document.createElement('span');
      lockBadge.className = 'lock-badge';
      lockBadge.textContent = '🔒 LOCKED';
      topRow.appendChild(lockBadge);
    }

    content.appendChild(topRow);

    // Dossier timestamp display

    card.appendChild(checkbox);
    card.appendChild(content);

    card.addEventListener('click', () => {
      document.querySelectorAll('.quest-card.active-selected').forEach(c => c.classList.remove('active-selected'));
      card.classList.add('active-selected');
      selectQuest(name);
    });

    return card;
  }

  // --- State Synchronization ---
  function syncQuestStatusAcrossUI(changedQuestName) {
    // If a status filter is active or hidden filter requires adding/removing nodes, re-render while preserving scroll
    if (state.statusFilter !== 'All Quests' || !changedQuestName) {
      renderQuestList(false);
    } else {
      // In-place DOM update
      const cards = document.querySelectorAll('.quest-card');
      cards.forEach(card => {
        const qName = card.getAttribute('data-quest');
        if (!qName) return;
        const st = state.questStatus[qName] || { status: 0, timestamp: null, is_hidden: false };
        const isLocked = state.lockedQuests.includes(qName);

        // If hidden and not showing hidden, remove card
        if (st.is_hidden && !state.preferences.show_hidden) {
          card.remove();
          return;
        }

        card.classList.toggle('status-in-progress', st.status === 1);
        card.classList.toggle('status-completed', st.status === 2);
        card.classList.toggle('locked', isLocked);

        // Update lock badge
        const topRow = card.querySelector('.quest-card-top');
        const existingLock = card.querySelector('.lock-badge');
        if (isLocked && !existingLock && topRow) {
          const lb = document.createElement('span');
          lb.className = 'lock-badge';
          lb.textContent = '🔒 LOCKED';
          topRow.appendChild(lb);
        } else if (!isLocked && existingLock) {
          existingLock.remove();
        }
      });
    }

    syncActiveDossierStatus();
    annotateWikiQuestLinks();
    updateProgressDisplay();
  }

  function cycleQuestStatus(questName) {
    const current = (state.questStatus[questName] || {}).status || 0;
    let next = 0;
    if (current === 0) next = 1;
    else if (current === 1) next = 2;
    else next = 0;

    setQuestStatus(questName, next);
  }

  function setQuestStatus(questName, nextStatus) {
    // Optimistic local state update so UI responds in 0ms
    const prevHidden = (state.questStatus[questName] || {}).is_hidden || false;
    const formattedTs = nextStatus === 2 ? formatQuestTimestamp(new Date()) : null;
    state.questStatus[questName] = {
      status: nextStatus,
      timestamp: formattedTs,
      is_hidden: prevHidden
    };
    recalculateMutualLocks();
    syncQuestStatusAcrossUI(questName);

    if (backend && backend.set_quest_status) {
      backend.set_quest_status(questName, nextStatus);
    }
  }

  function recalculateMutualLocks() {
    const locked = [];
    Object.keys(state.questStatus).forEach(q => {
      const st = state.questStatus[q].status;
      if ((st === 1 || st === 2) && MUTUALLY_EXCLUSIVE_MAP[q]) {
        MUTUALLY_EXCLUSIVE_MAP[q].forEach(partner => {
          const pStatus = (state.questStatus[partner] || {}).status;
          if (pStatus !== 1 && pStatus !== 2 && !locked.includes(partner)) {
            locked.push(partner);
          }
        });
      }
    });
    state.lockedQuests = locked;
  }

  // --- Quest Selection & Wiki View ---
  function selectQuest(questName) {
    state.selectedQuestName = questName;
    const meta = state.questMeta[questName] || {};

    document.getElementById('dossier-welcome').style.display = 'none';
    const dossierActive = document.getElementById('dossier-active');
    dossierActive.style.display = 'flex';

    document.getElementById('dossier-title').textContent = questName;
    document.getElementById('dossier-campaign-badge').textContent = meta.campaign || state.currentCampaign;
    document.getElementById('dossier-location-badge').textContent = meta.location || 'Tyria';

    const profBadge = document.getElementById('dossier-prof-badge');
    if (meta.profession) {
      profBadge.textContent = meta.profession.toUpperCase();
    } else {
      profBadge.textContent = 'ALL PROFESSIONS';
    }

    syncActiveDossierStatus();
    loadWikiArticle(questName);
  }

  function syncActiveDossierStatus() {
    const questName = state.selectedQuestName;
    if (!questName) return;

    const statusData = state.questStatus[questName] || { status: 0, timestamp: null, is_hidden: false };
    const status = statusData.status || 0;
    const isLocked = state.lockedQuests.includes(questName);

    // 1. Update Dossier Header Timestamp
    const timeBadge = document.getElementById('dossier-timestamp');
    if (status === 2 && statusData.timestamp) {
      timeBadge.textContent = `Completed: ${formatQuestTimestamp(statusData.timestamp)}`;
      timeBadge.style.display = 'inline-block';
    } else {
      timeBadge.style.display = 'none';
    }

    // 2. Update Dossier Status Pill Buttons
    const buttons = document.querySelectorAll('.status-pill-btn');
    buttons.forEach(b => {
      const s = parseInt(b.getAttribute('data-status'), 10);
      b.classList.toggle('active', s === status);
      b.disabled = isLocked && s !== 0;
    });

    // 3. Update Dossier Status Chip Badge
    const statusBadge = document.getElementById('dossier-status-badge');
    statusBadge.classList.remove('chip-in-progress', 'chip-completed');
    if (isLocked && status === 0) {
      statusBadge.textContent = 'LOCKED (EXCLUSIVE)';
    } else if (status === 2) {
      statusBadge.textContent = 'COMPLETED';
      statusBadge.classList.add('chip-completed');
    } else if (status === 1) {
      statusBadge.textContent = 'IN PROGRESS';
      statusBadge.classList.add('chip-in-progress');
    } else {
      statusBadge.textContent = 'NOT STARTED';
    }

    // 4. Update Hide/Unhide Button Text
    const hideBtn = document.getElementById('btn-dossier-hide');
    if (hideBtn) {
      hideBtn.textContent = statusData.is_hidden ? 'Unhide Quest' : 'Hide Quest';
    }

    // 5. Update Mutually Exclusive Banner
    const warnBanner = document.getElementById('exclusive-warning-banner');
    if (MUTUALLY_EXCLUSIVE_MAP[questName]) {
      const partner = MUTUALLY_EXCLUSIVE_MAP[questName].join(', ');
      document.getElementById('exclusive-warning-details').textContent = isLocked
        ? `Locked because opposing quest '${partner}' is currently active or completed.`
        : `Mutually exclusive with '${partner}'. Accepting or completing one locks the other.`;
      warnBanner.style.display = 'flex';
    } else {
      warnBanner.style.display = 'none';
    }

    // 6. Update Inline Wiki Entry Status Sync Bar
    const syncDot = document.getElementById('wiki-sync-dot');
    const syncLabel = document.getElementById('wiki-sync-label');
    const syncTime = document.getElementById('wiki-sync-time');

    if (syncDot && syncLabel) {
      syncDot.classList.remove('dot-in-progress', 'dot-completed');
      if (status === 2) {
        syncDot.classList.add('dot-completed');
        syncLabel.textContent = 'Wiki Entry Status: Completed';
        syncTime.textContent = statusData.timestamp ? `(${formatQuestTimestamp(statusData.timestamp)})` : '';
      } else if (status === 1) {
        syncDot.classList.add('dot-in-progress');
        syncLabel.textContent = 'Wiki Entry Status: In Progress';
        syncTime.textContent = '';
      } else {
        syncLabel.textContent = isLocked ? 'Wiki Entry Status: Locked (Exclusive)' : 'Wiki Entry Status: Not Started';
        syncTime.textContent = '';
      }
      setGenericDropdownValue(
        'wiki-inline-status-label',
        'wiki-inline-status-menu',
        'wiki-inline-status-value',
        String(status),
        status === 2 ? 'Completed' : (status === 1 ? 'In Progress' : 'Not Started')
      );
      const btnInline = document.getElementById('wiki-inline-status-btn');
      if (btnInline) {
        btnInline.disabled = (isLocked && status === 0);
      }
    }
  }

  function formatWikiDisplayUrl(target) {
    if (!target) return 'https://wiki.guildwars.com';
    if (target.startsWith('http://') || target.startsWith('https://')) return target;
    if (target.startsWith('/wiki/')) return `https://wiki.guildwars.com${target}`;
    return `https://wiki.guildwars.com/wiki/${encodeURIComponent(target.replace(/ /g, '_'))}`;
  }

  function updateWikiNavControls() {
    const btnBack = document.getElementById('btn-wiki-back');
    const btnForward = document.getElementById('btn-wiki-forward');
    const urlDisplay = document.getElementById('wiki-nav-url-display');
    if (btnBack) btnBack.disabled = (wikiHistoryIndex <= 0);
    if (btnForward) btnForward.disabled = (wikiHistoryIndex >= wikiHistory.length - 1);
    if (urlDisplay && wikiHistoryIndex >= 0 && wikiHistory[wikiHistoryIndex]) {
      urlDisplay.textContent = formatWikiDisplayUrl(wikiHistory[wikiHistoryIndex].url);
    }
  }

  function resolveQuestNameFromUrlOrTitle(urlOrTarget, title) {
    if (!urlOrTarget && !title) return '';
    if (urlOrTarget && state.questMeta[urlOrTarget]) return urlOrTarget;
    if (title && state.questMeta[title]) return title;

    let stripped = urlOrTarget || '';
    if (stripped.startsWith('https://wiki.guildwars.com/wiki/')) {
      stripped = stripped.replace('https://wiki.guildwars.com/wiki/', '');
    } else if (stripped.startsWith('/wiki/')) {
      stripped = stripped.replace('/wiki/', '');
    }
    stripped = decodeURIComponent(stripped).replace(/_\(quest\)$/i, '').replace(/_/g, ' ').trim();
    if (state.questMeta[stripped]) return stripped;

    if (title) {
      let tStripped = decodeURIComponent(title).replace(/_\(quest\)$/i, '').replace(/_/g, ' ').trim();
      if (state.questMeta[tStripped]) return tStripped;
    }
    return '';
  }

  function navigateToWiki(urlOrQuest, pageTitle = '', isHistoryNav = false) {
    if (!urlOrQuest) return;

    // Clear previous article content while loading new entry
    const bodyContainer = document.getElementById('wiki-article-body');
    const overlay = document.getElementById('wiki-loading-overlay');
    if (bodyContainer) bodyContainer.innerHTML = '';
    if (overlay) overlay.style.display = 'flex';

    if (!isHistoryNav) {
      if (wikiHistoryIndex < wikiHistory.length - 1) {
        wikiHistory = wikiHistory.slice(0, wikiHistoryIndex + 1);
      }
      wikiHistory.push({ url: urlOrQuest, title: pageTitle || urlOrQuest });
      wikiHistoryIndex = wikiHistory.length - 1;
    }

    updateWikiNavControls();

    const matchedQuest = resolveQuestNameFromUrlOrTitle(urlOrQuest, pageTitle);
    const welcome = document.getElementById('dossier-welcome');
    const dossierActive = document.getElementById('dossier-active');
    const statusGroup = document.querySelector('.status-btn-group');
    const utilityBtns = document.querySelector('.dossier-utility-btns');
    const syncControls = document.getElementById('wiki-sync-controls');
    const profBadge = document.getElementById('dossier-prof-badge');
    const statusBadge = document.getElementById('dossier-status-badge');
    const timeBadge = document.getElementById('dossier-timestamp');
    const campBadge = document.getElementById('dossier-campaign-badge');
    const locBadge = document.getElementById('dossier-location-badge');
    const titleEl = document.getElementById('dossier-title');
    const warnBanner = document.getElementById('exclusive-warning-banner');

    if (matchedQuest) {
      state.selectedQuestName = matchedQuest;
      const meta = state.questMeta[matchedQuest] || {};
      if (welcome) welcome.style.display = 'none';
      if (dossierActive) dossierActive.style.display = 'flex';
      if (statusGroup) statusGroup.style.display = 'flex';
      if (utilityBtns) utilityBtns.style.display = 'flex';
      if (syncControls) syncControls.style.display = 'flex';
      if (profBadge) {
        profBadge.style.display = '';
        profBadge.textContent = meta.profession ? meta.profession.toUpperCase() : 'ALL PROFESSIONS';
      }
      if (statusBadge) statusBadge.style.display = '';
      if (titleEl) titleEl.textContent = matchedQuest;
      if (campBadge) campBadge.textContent = meta.campaign || state.currentCampaign;
      if (locBadge) locBadge.textContent = meta.location || 'Tyria';

      syncActiveDossierStatus();

      document.querySelectorAll('.quest-card').forEach(c => {
        c.classList.toggle('active-selected', c.getAttribute('data-quest') === matchedQuest);
      });
    } else {
      // Sublink / Reference wiki article navigation: Suppress quest completion options
      state.selectedQuestName = null;
      if (welcome) welcome.style.display = 'none';
      if (dossierActive) dossierActive.style.display = 'flex';
      if (statusGroup) statusGroup.style.display = 'none';
      if (utilityBtns) utilityBtns.style.display = 'none';
      if (syncControls) syncControls.style.display = 'none';
      if (profBadge) profBadge.style.display = 'none';
      if (statusBadge) statusBadge.style.display = 'none';
      if (timeBadge) timeBadge.style.display = 'none';
      if (warnBanner) warnBanner.style.display = 'none';
      if (titleEl) titleEl.textContent = pageTitle || urlOrQuest;
      if (campBadge) campBadge.textContent = 'Guild Wars Wiki';
      if (locBadge) locBadge.textContent = 'Reference Article';

      document.querySelectorAll('.quest-card').forEach(c => {
        c.classList.remove('active-selected');
      });
    }

    if (backend && backend.request_wiki_page) {
      backend.request_wiki_page(urlOrQuest, pageTitle);
    } else if (backend && backend.request_wiki_html) {
      backend.request_wiki_html(urlOrQuest);
    } else {
      setTimeout(() => {
        if (overlay) overlay.style.display = 'none';
        const meta = state.questMeta[urlOrQuest] || {};
        if (bodyContainer) {
          bodyContainer.innerHTML = `
            <h2>${pageTitle || urlOrQuest}</h2>
            <p><strong>Campaign:</strong> ${meta.campaign || 'Guild Wars'}</p>
            <p><strong>Region / Location:</strong> ${meta.location || 'Tyria'}</p>
            <p><strong>Class Restriction:</strong> ${meta.profession || 'Available to all professions'}</p>
            <hr>
            <h3>Walkthrough &amp; Intelligence</h3>
            <p>Cached locally for high-speed offline access with internal forward/backward navigation.</p>
          `;
        }
        annotateWikiQuestLinks();
      }, 80);
    }
  }

  function loadWikiArticle(questName) {
    navigateToWiki(questName, questName, false);
  }

  function onWikiContentReady(title, cleanHtml, url) {
    const overlay = document.getElementById('wiki-loading-overlay');
    const bodyContainer = document.getElementById('wiki-article-body');
    if (overlay) overlay.style.display = 'none';

    if (bodyContainer) {
      bodyContainer.innerHTML = cleanHtml;

      // Handle internal navigation for hyperlinks and wiki sublinks
      bodyContainer.querySelectorAll('a').forEach(a => {
        const href = a.getAttribute('href') || '';
        if (!href || href.startsWith('#')) return;

        const targetQuest = resolveQuestNameFromUrlOrTitle(href, a.textContent.trim());
        if (targetQuest) {
          a.setAttribute('data-linked-quest', targetQuest);
        }

        a.addEventListener('click', e => {
          e.preventDefault();
          if (targetQuest) {
            selectQuest(targetQuest);
          } else {
            navigateToWiki(href, a.textContent.trim(), false);
          }
        });
      });
    }

    annotateWikiQuestLinks();
    updateWikiNavControls();
  }

  // Synchronize status badges on quest links inside the Wiki article
  function annotateWikiQuestLinks() {
    const bodyContainer = document.getElementById('wiki-article-body');
    if (!bodyContainer) return;

    bodyContainer.querySelectorAll('.wiki-quest-link-badge').forEach(b => b.remove());

    bodyContainer.querySelectorAll('a[data-linked-quest]').forEach(a => {
      const qName = a.getAttribute('data-linked-quest');
      const st = (state.questStatus[qName] || {}).status || 0;
      if (st === 1 || st === 2) {
        const badge = document.createElement('span');
        badge.className = `wiki-quest-link-badge ${st === 2 ? 'badge-completed' : 'badge-in-progress'}`;
        badge.textContent = st === 2 ? '✓ Completed' : '● In Progress';
        a.insertAdjacentElement('afterend', badge);
      }
    });
  }

  // --- Progress Tracker ---
  function updateProgressDisplay() {
    let completed = 0;
    let inProgress = 0;
    let total = 0;

    const currentCampaign = state.currentCampaign;
    let listData = [];

    if (currentCampaign === 'All') {
      const order = ['Prophecies', 'Factions', 'Nightfall', 'Eye of the North', 'Beyond', 'LDoA'];
      order.forEach(c => {
        if (state.questDb[c]) listData = listData.concat(state.questDb[c]);
      });
    } else {
      listData = state.questDb[currentCampaign] || [];
    }

    const prof = state.profFilter.toLowerCase();
    const isProfAll = (state.profFilter === 'All Professions');
    const showHidden = Boolean(state.preferences.show_hidden);

    const seenQuests = new Set();

    for (let i = 0; i < listData.length; i++) {
      const item = listData[i];
      if (!item || item.includes('---') || seenQuests.has(item)) continue;
      seenQuests.add(item);

      const meta = state.questMeta[item] || {};
      const profReq = (meta.profession || '').toLowerCase();
      if (!isProfAll && profReq && !profReq.includes(prof)) continue;

      // Exclude locked mutually exclusive quests from achievable denominator
      if (state.lockedQuests.includes(item)) continue;

      const st = state.questStatus[item] || {};
      if (st.is_hidden && !showHidden) continue;

      total++;
      if (st.status === 2) completed++;
      else if (st.status === 1) inProgress++;
    }

    const rawPercent = total > 0 ? (completed / total) * 100 : 0;
    let displayPercentStr = '0%';
    if (completed === 0 || total === 0) {
      displayPercentStr = '0%';
    } else if (completed >= total) {
      displayPercentStr = '100%';
    } else if (Number.isInteger(Number(rawPercent.toFixed(1)))) {
      displayPercentStr = `${Math.round(rawPercent)}%`;
    } else {
      displayPercentStr = `${rawPercent.toFixed(1)}%`;
    }

    const titleEl = document.getElementById('progress-campaign-title');
    if (titleEl) {
      titleEl.textContent = currentCampaign === 'All'
        ? 'ALL CAMPAIGNS PROGRESSION'
        : `${currentCampaign.toUpperCase()} PROGRESSION`;
    }

    const inProgEl = document.getElementById('in-progress-count-text');
    if (inProgEl) {
      inProgEl.textContent = `${inProgress} In Progress`;
    }

    const percentEl = document.getElementById('liquid-percent-text');
    const ratioEl = document.getElementById('liquid-ratio-text');
    const liquidFill = document.getElementById('fluid-liquid-fill');

    if (ratioEl) ratioEl.textContent = `${completed} / ${total}`;
    if (percentEl) percentEl.textContent = displayPercentStr;

    if (liquidFill) {
      const visualWidth = completed > 0 ? Math.max(rawPercent, 1.5) : 0;
      anime && anime.remove(liquidFill);
      liquidFill.style.width = `${visualWidth}%`;
    }
  }

  // --- Theme Transition ---
  function toggleThemeSmoothly(forcedDarkState = null) {
    const newDark = forcedDarkState !== null ? forcedDarkState : !state.preferences.dark_mode;
    state.preferences.dark_mode = newDark;

    const settingsDarkToggle = document.getElementById('toggle-dark-mode');
    if (settingsDarkToggle) {
      settingsDarkToggle.checked = newDark;
    }

    // Interactive button animation
    if (typeof anime !== 'undefined') {
      anime.remove('#theme-icon');
      anime({
        targets: '#theme-icon',
        rotate: newDark ? [0, 360] : [360, 0],
        scale: [
          { value: 0.72, duration: 110, easing: 'easeOutQuad' },
          { value: 1.16, duration: 180, easing: 'easeOutQuad' },
          { value: 1.0, duration: 150, easing: 'easeOutElastic(1, .6)' }
        ],
        duration: 440
      });
    }

    // Hardware-accelerated 60 FPS cubic-bezier transition
    document.body.classList.add('theme-transitioning');
    applyPreferencesToDOM();

    if (backend && backend.set_theme) {
      backend.set_theme(newDark);
    }

    setTimeout(() => {
      document.body.classList.remove('theme-transitioning');
    }, 420);
  }

  // --- UI Event Listeners ---
  function initUIEvents() {
    initTabSlider();

    // Quick Low GPU Mode Toggle Button in Header
    const gpuToggleBtn = document.getElementById('btn-gpu-toggle');
    if (gpuToggleBtn) {
      gpuToggleBtn.addEventListener('click', () => {
        state.preferences.low_gpu_mode = !state.preferences.low_gpu_mode;
        applyPreferencesToDOM();
        if (backend && backend.save_preferences_json) {
          backend.save_preferences_json(JSON.stringify(state.preferences));
        }
      });
    }

    // Theme Toggle Button in Header (Fluid 60 FPS animation)
    document.getElementById('btn-theme-toggle').addEventListener('click', () => {
      toggleThemeSmoothly();
    });

    // Sync Scheme Option Cards helper
    function syncSchemeOptionCards() {
      document.querySelectorAll('#modal-settings .scheme-option-card').forEach(card => {
        const r = card.querySelector('input[type="radio"]');
        card.classList.toggle('active', Boolean(r && r.checked));
      });
      document.querySelectorAll('#modal-initial-setup .scheme-option-card').forEach(card => {
        const r = card.querySelector('input[type="radio"]');
        card.classList.toggle('active', Boolean(r && r.checked));
      });
    }

    // Open Settings Modal
    document.getElementById('btn-settings').addEventListener('click', () => {
      const p = state.preferences;
      const classicRadio = document.getElementById('scheme-classic-radio');
      const altRadio = document.getElementById('scheme-alternate-radio');
      if (classicRadio) classicRadio.checked = (p.color_scheme !== 'alternate');
      if (altRadio) altRadio.checked = (p.color_scheme === 'alternate');
      syncSchemeOptionCards();

      const darkToggle = document.getElementById('toggle-dark-mode');
      if (darkToggle) darkToggle.checked = Boolean(p.dark_mode);

      setGenericDropdownValue(
        'density-select-label',
        'density-select-menu',
        'density-select-value',
        p.card_density || 'comfortable',
        p.card_density === 'compact' ? 'Compact (High Information Density)' : 'Comfortable (Standard)'
      );

      const lowGpu = document.getElementById('toggle-low-gpu');
      if (lowGpu) lowGpu.checked = Boolean(p.low_gpu_mode);

      setGenericDropdownValue(
        'anim-select-label',
        'anim-select-menu',
        'anim-select-value',
        p.animation_level || 'reduced',
        p.animation_level === 'full'
          ? 'Full Animations (Smooth Transitions)'
          : (p.animation_level === 'minimal' ? 'Minimal / Instant' : 'Moderated (Balanced)')
      );

      setGenericDropdownValue(
        'cursor-select-label',
        'cursor-select-menu',
        'cursor-select-value',
        p.cursor_light || 'subtle',
        p.cursor_light === 'off' ? 'Off (Disabled)' : (p.cursor_light === 'standard' ? 'Standard Aura' : 'Subtle (Low Opacity)')
      );

      const liquidWave = document.getElementById('toggle-liquid-wave');
      if (liquidWave) liquidWave.checked = Boolean(p.liquid_wave_anim);

      const showLocked = document.getElementById('toggle-show-locked');
      if (showLocked) showLocked.checked = Boolean(p.show_locked);

      const showHidden = document.getElementById('toggle-show-hidden');
      if (showHidden) showHidden.checked = Boolean(p.show_hidden);

      const autoClose = document.getElementById('toggle-auto-close');
      if (autoClose) autoClose.checked = Boolean(p.auto_close);

      syncSwitchClasses();
      openModal('modal-settings');
    });

    // Save Settings Button
    document.getElementById('btn-save-settings').addEventListener('click', () => {
      const schemeRadio = document.querySelector('input[name="color-scheme"]:checked');
      const updatedPrefs = {
        color_scheme: schemeRadio ? schemeRadio.value : 'classic',
        dark_mode: document.getElementById('toggle-dark-mode')?.checked ?? true,
        card_density: document.getElementById('density-select-value')?.value || 'comfortable',
        low_gpu_mode: document.getElementById('toggle-low-gpu')?.checked ?? false,
        animation_level: document.getElementById('anim-select-value')?.value || 'reduced',
        cursor_light: document.getElementById('cursor-select-value')?.value || 'subtle',
        liquid_wave_anim: document.getElementById('toggle-liquid-wave')?.checked ?? true,
        show_locked: document.getElementById('toggle-show-locked')?.checked ?? true,
        show_hidden: document.getElementById('toggle-show-hidden')?.checked ?? false,
        auto_close: document.getElementById('toggle-auto-close')?.checked ?? false
      };

      state.preferences = Object.assign({}, state.preferences, updatedPrefs);
      applyPreferencesToDOM();

      if (backend && backend.save_preferences_json) {
        backend.save_preferences_json(JSON.stringify(state.preferences));
      } else if (backend && backend.save_settings) {
        backend.save_settings(updatedPrefs.color_scheme, updatedPrefs.dark_mode, updatedPrefs.show_hidden);
      }

      const saveBtn = document.getElementById('btn-save-settings');
      saveBtn.textContent = 'Saved ✓';
      setTimeout(() => {
        saveBtn.textContent = 'Save Preferences';
        closeModal('modal-settings');
        renderQuestList(false);
        updateProgressDisplay();
      }, 350);
    });

    // Instant Settings Interaction: Palette Option Cards & Radios
    document.querySelectorAll('.scheme-option-card').forEach(card => {
      card.addEventListener('click', () => {
        const radio = card.querySelector('input[type="radio"]');
        if (radio && !radio.checked) {
          radio.checked = true;
          radio.dispatchEvent(new Event('change', { bubbles: true }));
        }
      });
    });

    document.querySelectorAll('input[name="color-scheme"]').forEach(radio => {
      radio.addEventListener('change', () => {
        state.preferences.color_scheme = radio.value;
        syncSchemeOptionCards();
        document.body.classList.add('theme-transitioning');
        applyPreferencesToDOM();
        renderQuestList(false);
        updateProgressDisplay();
        setTimeout(() => document.body.classList.remove('theme-transitioning'), 400);
      });
    });

    document.querySelectorAll('input[name="setup-color-scheme"]').forEach(radio => {
      radio.addEventListener('change', () => {
        syncSchemeOptionCards();
      });
    });

    // Instant Settings Interaction: Dark Mode Toggle
    const toggleDarkMode = document.getElementById('toggle-dark-mode');
    if (toggleDarkMode) {
      toggleDarkMode.addEventListener('change', (e) => {
        syncSwitchClasses();
        toggleThemeSmoothly(e.target.checked);
      });
    }

    // Instant Settings Interaction: Low GPU Mode Toggle
    const settingsLowGpu = document.getElementById('toggle-low-gpu');
    if (settingsLowGpu) {
      settingsLowGpu.addEventListener('change', (e) => {
        state.preferences.low_gpu_mode = e.target.checked;
        syncSwitchClasses();
        applyPreferencesToDOM();
        if (backend && backend.save_preferences_json) {
          backend.save_preferences_json(JSON.stringify(state.preferences));
        }
      });
    }

    // Instant Settings Interaction: Liquid Wave Toggle
    const toggleLiquidWave = document.getElementById('toggle-liquid-wave');
    if (toggleLiquidWave) {
      toggleLiquidWave.addEventListener('change', (e) => {
        state.preferences.liquid_wave_anim = e.target.checked;
        syncSwitchClasses();
        applyPreferencesToDOM();
      });
    }

    // Instant Settings Interaction: Show Locked Toggle
    const toggleShowLocked = document.getElementById('toggle-show-locked');
    if (toggleShowLocked) {
      toggleShowLocked.addEventListener('change', (e) => {
        state.preferences.show_locked = e.target.checked;
        syncSwitchClasses();
        renderQuestList(false);
      });
    }

    // Instant Settings Interaction: Show Hidden Toggle
    const toggleShowHidden = document.getElementById('toggle-show-hidden');
    if (toggleShowHidden) {
      toggleShowHidden.addEventListener('change', (e) => {
        state.preferences.show_hidden = e.target.checked;
        syncSwitchClasses();
        renderQuestList(false);
        updateProgressDisplay();
      });
    }

    // Instant Settings Interaction: Auto Close Toggle
    const toggleAutoClose = document.getElementById('toggle-auto-close');
    if (toggleAutoClose) {
      toggleAutoClose.addEventListener('change', (e) => {
        state.preferences.auto_close = e.target.checked;
        syncSwitchClasses();
        if (backend && backend.set_auto_close) {
          backend.set_auto_close(e.target.checked);
        }
      });
    }

    // Make entire .toggle-row clickable for maximum responsiveness without double-toggling
    document.querySelectorAll('#modal-settings .toggle-row, #modal-initial-setup .toggle-row').forEach(row => {
      row.addEventListener('click', (e) => {
        // If clicked directly on the input checkbox or switch, the input handles it natively!
        if (
          e.target.tagName === 'INPUT' ||
          e.target.closest('.switch') ||
          e.target.closest('.custom-select-wrapper') ||
          e.target.closest('button') ||
          e.target.closest('a')
        ) {
          return;
        }
        const checkbox = row.querySelector('input[type="checkbox"]');
        if (checkbox) {
          checkbox.checked = !checkbox.checked;
          syncSwitchClasses();
          checkbox.dispatchEvent(new Event('change', { bubbles: true }));
        }
      });
    });

    // Settings Maintenance Actions
    const btnSettingsQrSync = document.getElementById('btn-settings-qr-sync');
    if (btnSettingsQrSync) {
      btnSettingsQrSync.addEventListener('click', () => {
        closeModal('modal-settings');
        openQrSyncModal();
      });
    }

    const btnCopyPairingUrl = document.getElementById('btn-copy-pairing-url');
    if (btnCopyPairingUrl) {
      btnCopyPairingUrl.addEventListener('click', () => {
        const urlInput = document.getElementById('qr-pairing-url');
        if (urlInput) {
          urlInput.select();
          navigator.clipboard.writeText(urlInput.value).then(() => {
            btnCopyPairingUrl.textContent = 'Copied ✓';
            setTimeout(() => { btnCopyPairingUrl.textContent = 'Copy'; }, 1800);
          }).catch(() => {
            btnCopyPairingUrl.textContent = 'Copied ✓';
            setTimeout(() => { btnCopyPairingUrl.textContent = 'Copy'; }, 1800);
          });
        }
      });
    }

    document.getElementById('btn-settings-rename-char').addEventListener('click', () => {
      closeModal('modal-settings');
      openEditProfileModal();
    });

    document.getElementById('btn-settings-unhide-all').addEventListener('click', () => {
      if (backend && backend.unhide_all_quests) {
        backend.unhide_all_quests();
      } else {
        Object.keys(state.questStatus).forEach(q => {
          state.questStatus[q].is_hidden = false;
        });
        renderQuestList(false);
        updateProgressDisplay();
      }
      const btn = document.getElementById('btn-settings-unhide-all');
      btn.textContent = 'All Quests Unhidden ✓';
      setTimeout(() => {
        btn.textContent = 'Unhide All Quests';
      }, 2000);
    });

    document.getElementById('btn-settings-clear-cache').addEventListener('click', () => {
      if (backend && backend.clear_wiki_cache) {
        backend.clear_wiki_cache();
      }
      const btn = document.getElementById('btn-settings-clear-cache');
      btn.textContent = 'Wiki Cache Cleared ✓';
      setTimeout(() => {
        btn.textContent = 'Clear Wiki Cache';
      }, 2000);
    });

    // Reopen Setup Wizard Button from Settings
    const btnReopenSetup = document.getElementById('btn-settings-reopen-setup');
    if (btnReopenSetup) {
      btnReopenSetup.addEventListener('click', () => {
        closeModal('modal-settings');
        openFirstLaunchSetupModal();
      });
    }

    // Dismiss Settings Guide Callout
    const btnDismissCallout = document.getElementById('btn-dismiss-callout');
    if (btnDismissCallout) {
      btnDismissCallout.addEventListener('click', () => {
        const callout = document.getElementById('settings-guide-callout');
        if (callout) callout.style.display = 'none';
      });
    }

    // Finish First Launch Setup Button
    const btnFinishSetup = document.getElementById('btn-finish-setup');
    if (btnFinishSetup) {
      btnFinishSetup.addEventListener('click', () => {
        const heroName = document.getElementById('setup-profile-name').value.trim() || 'Hero';
        const heroProf = document.getElementById('setup-profile-prof-value').value || 'All Professions';
        const schemeRadio = document.querySelector('input[name="setup-color-scheme"]:checked');
        const scheme = schemeRadio ? schemeRadio.value : 'classic';
        const lowGpu = document.getElementById('setup-low-gpu').checked;

        state.preferences.color_scheme = scheme;
        state.preferences.low_gpu_mode = lowGpu;
        state.currentProfession = heroProf;
        state.profFilter = heroProf;
        applyPreferencesToDOM();

        if (backend) {
          if (state.currentProfile === 'Default') {
            backend.rename_profile('Default', heroName, heroProf);
          } else {
            backend.set_profile_profession(heroProf);
          }
          backend.save_preferences_json(JSON.stringify(state.preferences));
          backend.complete_first_run();
        } else {
          state.currentProfile = heroName;
          renderProfileSection();
          renderProfessionFilterDropdown();
          renderQuestList(false);
          updateProgressDisplay();
        }

        closeModal('modal-initial-setup');

        // Show guide callout pointing to the gear
        const callout = document.getElementById('settings-guide-callout');
        if (callout) callout.style.display = 'block';
      });
    }

    // Internal In-App Wiki Browser Navigation Buttons
    const btnWikiBack = document.getElementById('btn-wiki-back');
    if (btnWikiBack) {
      btnWikiBack.addEventListener('click', () => {
        if (wikiHistoryIndex > 0) {
          wikiHistoryIndex--;
          const item = wikiHistory[wikiHistoryIndex];
          navigateToWiki(item.url, item.title, true);
        }
      });
    }

    const btnWikiForward = document.getElementById('btn-wiki-forward');
    if (btnWikiForward) {
      btnWikiForward.addEventListener('click', () => {
        if (wikiHistoryIndex < wikiHistory.length - 1) {
          wikiHistoryIndex++;
          const item = wikiHistory[wikiHistoryIndex];
          navigateToWiki(item.url, item.title, true);
        }
      });
    }

    const btnWikiReload = document.getElementById('btn-wiki-reload');
    if (btnWikiReload) {
      btnWikiReload.addEventListener('click', () => {
        if (wikiHistoryIndex >= 0 && wikiHistory[wikiHistoryIndex]) {
          const item = wikiHistory[wikiHistoryIndex];
          navigateToWiki(item.url, item.title, true);
        }
      });
    }

    // Initialize Custom Animated Modal Profession Dropdowns
    initModalSelectDropdown('setup-profile-prof-wrapper', 'setup-profile-prof-btn', 'setup-profile-prof-label', 'setup-profile-prof-menu', 'setup-profile-prof-value');
    initModalSelectDropdown('new-profile-prof-wrapper', 'new-profile-prof-btn', 'new-profile-prof-label', 'new-profile-prof-menu', 'new-profile-prof-value');
    initModalSelectDropdown('edit-profile-prof-wrapper', 'edit-profile-prof-btn', 'edit-profile-prof-label', 'edit-profile-prof-menu', 'edit-profile-prof-value');

    // Initialize Custom Animated Settings Dropdowns
    initGenericCustomDropdown(
      'density-select-wrapper',
      'density-select-btn',
      'density-select-label',
      'density-select-menu',
      'density-select-value',
      [
        { value: 'comfortable', label: 'Comfortable (Standard)' },
        { value: 'compact', label: 'Compact (High Information Density)' }
      ],
      (val) => {
        state.preferences.card_density = val;
        applyPreferencesToDOM();
        renderQuestList(false);
      }
    );

    initGenericCustomDropdown(
      'anim-select-wrapper',
      'anim-select-btn',
      'anim-select-label',
      'anim-select-menu',
      'anim-select-value',
      [
        { value: 'full', label: 'Full Animations (Liquid bars, orbs, transitions)' },
        { value: 'reduced', label: 'Reduced (Stable, low GPU motion)' },
        { value: 'minimal', label: 'Minimal (Static UI, zero GPU overhead)' }
      ],
      (val) => {
        state.preferences.animation_level = val;
        applyPreferencesToDOM();
      }
    );

    initGenericCustomDropdown(
      'cursor-select-wrapper',
      'cursor-select-btn',
      'cursor-select-label',
      'cursor-select-menu',
      'cursor-select-value',
      [
        { value: 'off', label: 'Disabled (No halo)' },
        { value: 'subtle', label: 'Subtle Gold (Gentle glow)' },
        { value: 'standard', label: 'Standard Aura' }
      ],
      (val) => {
        state.preferences.cursor_light = val;
        applyPreferencesToDOM();
      }
    );

    // Settings Menu Check for Updates Button
    const btnSettingsCheckUpdates = document.getElementById('btn-settings-check-updates');
    if (btnSettingsCheckUpdates) {
      btnSettingsCheckUpdates.addEventListener('click', () => {
        closeModal('modal-settings');
        openModal('modal-release-notes');
        if (backend && backend.check_for_updates) {
          backend.check_for_updates();
        }
      });
    }

    // Initialize Custom Animated Wiki Inline Status Dropdown
    initGenericCustomDropdown(
      'wiki-inline-status-wrapper',
      'wiki-inline-status-btn',
      'wiki-inline-status-label',
      'wiki-inline-status-menu',
      'wiki-inline-status-value',
      [
        { value: '0', label: 'Not Started' },
        { value: '1', label: 'In Progress' },
        { value: '2', label: 'Completed' }
      ],
      (val) => {
        if (!state.selectedQuestName) return;
        const targetStatus = parseInt(val, 10);
        setQuestStatus(state.selectedQuestName, targetStatus);
      }
    );

    // Release Notes & GitHub Updates Modal Triggers
    const btnReleaseNotes = document.getElementById('btn-release-notes');
    if (btnReleaseNotes) {
      btnReleaseNotes.addEventListener('click', () => {
        openModal('modal-release-notes');
        if (backend && backend.check_for_updates) {
          backend.check_for_updates();
        }
      });
    }

    const btnCheckUpdatesNow = document.getElementById('btn-check-updates-now');
    if (btnCheckUpdatesNow) {
      btnCheckUpdatesNow.addEventListener('click', () => {
        const title = document.getElementById('update-status-title');
        const sub = document.getElementById('update-status-sub');
        const icon = document.getElementById('update-status-icon');
        if (title) title.textContent = 'Checking GitHub...';
        if (sub) sub.textContent = 'Querying repository releases for updates...';
        if (icon) icon.textContent = '⏳';
        if (backend && backend.check_for_updates) {
          backend.check_for_updates();
        }
      });
    }

    const btnOpenGithubReleases = document.getElementById('btn-open-github-releases');
    if (btnOpenGithubReleases) {
      btnOpenGithubReleases.addEventListener('click', () => {
        if (backend && backend.open_external_url) {
          backend.open_external_url('https://github.com/Mr-Akito/GWReforgeTracker/releases');
        } else {
          window.open('https://github.com/Mr-Akito/GWReforgeTracker/releases', '_blank');
        }
      });
    }

    // Export & Import Progression Data Handlers
    const btnExportData = document.getElementById('btn-settings-export-data');
    if (btnExportData) {
      btnExportData.addEventListener('click', () => {
        if (backend && backend.export_progression) {
          backend.export_progression();
        }
      });
    }

    const btnImportData = document.getElementById('btn-settings-import-data');
    if (btnImportData) {
      btnImportData.addEventListener('click', () => {
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.json,application/json';
        fileInput.onchange = (e) => {
          const file = e.target.files[0];
          if (!file) return;
          const reader = new FileReader();
          reader.onload = (re) => {
            const jsonText = re.target.result;
            if (backend && backend.import_progression) {
              backend.import_progression(jsonText);
            }
          };
          reader.readAsText(file);
        };
        fileInput.click();
      });
    }

    // Setup Wizard Low GPU toggle live listener
    const setupGpuCheckbox = document.getElementById('setup-low-gpu');
    if (setupGpuCheckbox) {
      setupGpuCheckbox.addEventListener('change', () => {
        state.preferences.low_gpu_mode = setupGpuCheckbox.checked;
        applyPreferencesToDOM();
      });
    }

    // About Modal
    document.getElementById('btn-about').addEventListener('click', () => {
      openModal('modal-about');
    });

    // Modal Close Buttons
    document.querySelectorAll('.modal-close-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const modalId = btn.getAttribute('data-modal');
        closeModal(modalId);
      });
    });

    // Search Bar
    const searchInput = document.getElementById('search-input');
    const clearBtn = document.getElementById('btn-search-clear');
    let searchDebounceTimer = null;

    searchInput.addEventListener('input', e => {
      const val = e.target.value;
      clearBtn.style.display = val.length > 0 ? 'block' : 'none';
      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(() => {
        state.searchText = val;
        renderQuestList(false);
      }, 120);
    });

    clearBtn.addEventListener('click', () => {
      searchInput.value = '';
      state.searchText = '';
      clearBtn.style.display = 'none';
      renderQuestList(false);
    });

    // Status Filter Dropdown
    const statusBtn = document.getElementById('status-filter-btn');
    const statusMenu = document.getElementById('status-filter-menu');
    statusBtn.addEventListener('click', e => {
      e.stopPropagation();
      const isOpen = statusMenu.classList.contains('open');
      closeAllDropdowns();
      if (!isOpen) statusMenu.classList.add('open');
    });

    statusMenu.querySelectorAll('.select-item').forEach(item => {
      item.addEventListener('click', () => {
        const val = item.getAttribute('data-value');
        state.statusFilter = val;
        document.getElementById('status-filter-label').textContent = val;
        statusMenu.querySelectorAll('.select-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        statusMenu.classList.remove('open');
        renderQuestList(false);
        updateProgressDisplay();
      });
    });

    // Profession Filter Dropdown
    const profBtn = document.getElementById('prof-filter-btn');
    const profMenu = document.getElementById('prof-filter-menu');
    profBtn.addEventListener('click', e => {
      e.stopPropagation();
      const isOpen = profMenu.classList.contains('open');
      closeAllDropdowns();
      if (!isOpen) profMenu.classList.add('open');
    });

    // Profile Selector Dropdown
    const profileBtn = document.getElementById('profile-selector-btn');
    const profileMenu = document.getElementById('profile-dropdown-menu');
    profileBtn.addEventListener('click', e => {
      e.stopPropagation();
      const isOpen = profileMenu.classList.contains('open');
      closeAllDropdowns();
      if (!isOpen) profileMenu.classList.add('open');
    });

    document.addEventListener('click', closeAllDropdowns);

    // Edit / Rename Character Profile Button (Allows modifying 'Default' character name)
    document.getElementById('btn-edit-profile').addEventListener('click', openEditProfileModal);

    document.getElementById('btn-confirm-edit-profile').addEventListener('click', () => {
      const newName = document.getElementById('edit-profile-input').value.trim();
      const newProf = document.getElementById('edit-profile-prof-value').value || 'All Professions';
      if (!newName) return;

      const oldName = state.currentProfile;
      state.profFilter = newProf;

      if (backend && backend.rename_profile) {
        backend.rename_profile(oldName, newName, newProf);
      } else {
        const idx = state.profiles.indexOf(oldName);
        if (idx !== -1) state.profiles[idx] = newName;
        state.currentProfile = newName;
        state.currentProfession = newProf;
        renderProfileSection();
        renderProfessionFilterDropdown();
        renderQuestList(false);
        updateProgressDisplay();
      }
      closeModal('modal-edit-profile');
    });

    // Create New Character Profile Button
    document.getElementById('btn-new-profile').addEventListener('click', () => {
      document.getElementById('new-profile-input').value = '';
      setModalSelectValue('new-profile-prof-label', 'new-profile-prof-menu', 'new-profile-prof-value', 'All Professions');
      openModal('modal-new-profile');
    });

    document.getElementById('btn-confirm-create-profile').addEventListener('click', () => {
      const name = document.getElementById('new-profile-input').value.trim();
      const prof = document.getElementById('new-profile-prof-value').value || 'All Professions';
      if (name) {
        state.profFilter = prof;
        if (backend && backend.create_profile) {
          backend.create_profile(name, prof);
        } else {
          if (!state.profiles.includes(name)) state.profiles.push(name);
          state.currentProfile = name;
          state.currentProfession = prof;
          renderProfileSection();
          renderProfessionFilterDropdown();
          renderQuestList(false);
          updateProgressDisplay();
        }
        closeModal('modal-new-profile');
      }
    });

    // Delete Character Profile Button
    document.getElementById('btn-delete-profile').addEventListener('click', () => {
      if (state.profiles.length <= 1) {
        showConfirmModal(
          'Modify Default Character Instead',
          'You cannot delete the only remaining character profile. Use the Edit (✎) button next to the character name to rename it!',
          null
        );
        return;
      }
      showConfirmModal('Delete Character Profile', `Are you sure you want to delete '${state.currentProfile}'?`, () => {
        if (backend && backend.delete_profile) {
          backend.delete_profile(state.currentProfile);
        }
      });
    });

    // Reset Campaign Button
    document.getElementById('btn-reset-campaign').addEventListener('click', () => {
      const camp = state.currentCampaign;
      const targetText = (camp === 'All') ? 'ALL campaigns' : `the ${camp} campaign`;
      showConfirmModal('Reset Quest Progress', `Are you sure you want to reset all quest progress for ${targetText}?`, () => {
        if (backend && backend.reset_campaign) {
          backend.reset_campaign(camp);
        } else {
          state.questStatus = {};
          state.lockedQuests = [];
          syncQuestStatusAcrossUI('');
        }
      });
    });

    // Sync Database Button
    document.getElementById('btn-sync-db').addEventListener('click', () => {
      if (backend && backend.start_sync) {
        backend.start_sync();
      }
    });

    // Dossier Header Status Pill Buttons
    document.querySelectorAll('.status-pill-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        if (!state.selectedQuestName) return;
        const targetStatus = parseInt(btn.getAttribute('data-status'), 10);
        setQuestStatus(state.selectedQuestName, targetStatus);
      });
    });

    // Dossier Hide/Unhide Button
    document.getElementById('btn-dossier-hide').addEventListener('click', () => {
      if (!state.selectedQuestName) return;
      const q = state.selectedQuestName;
      const current = (state.questStatus[q] || {}).is_hidden || false;
      const nextHidden = !current;

      if (!state.questStatus[q]) {
        state.questStatus[q] = { status: 0, timestamp: null, is_hidden: nextHidden };
      } else {
        state.questStatus[q].is_hidden = nextHidden;
      }
      syncQuestStatusAcrossUI(q);

      if (backend && backend.set_quest_hidden) {
        backend.set_quest_hidden(q, nextHidden);
      }
    });

    // Dossier External Wiki Link Button (routes through in-app browser)
    document.getElementById('btn-dossier-external').addEventListener('click', () => {
      if (!state.selectedQuestName) return;
      const meta = state.questMeta[state.selectedQuestName] || {};
      const url = meta.url || `https://wiki.guildwars.com/wiki/${encodeURIComponent(state.selectedQuestName.replace(/ /g, '_'))}`;
      navigateToWiki(url, state.selectedQuestName, false);
    });
  }

  function initModalSelectDropdown(wrapperId, btnId, labelId, menuId, valueId, onSelect) {
    const wrapper = document.getElementById(wrapperId);
    const btn = document.getElementById(btnId);
    const label = document.getElementById(labelId);
    const menu = document.getElementById(menuId);
    const input = document.getElementById(valueId);
    if (!wrapper || !btn || !label || !menu || !input) return;

    menu.innerHTML = '';
    PROFESSIONS_LIST.forEach(p => {
      const item = document.createElement('div');
      item.className = 'select-item';
      item.setAttribute('data-value', p);
      item.textContent = p;
      item.addEventListener('click', (e) => {
        e.stopPropagation();
        input.value = p;
        label.textContent = p;
        menu.querySelectorAll('.select-item').forEach(el => el.classList.remove('active'));
        item.classList.add('active');
        menu.classList.remove('open');
        if (onSelect) onSelect(p);
      });
      menu.appendChild(item);
    });

    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = menu.classList.contains('open');
      closeAllDropdowns();
      if (!isOpen) {
        menu.classList.add('open');
      }
    });
  }

  function setModalSelectValue(labelId, menuId, valueId, value) {
    const label = document.getElementById(labelId);
    const menu = document.getElementById(menuId);
    const input = document.getElementById(valueId);
    const val = value || 'All Professions';
    if (label) label.textContent = val;
    if (input) input.value = val;
    if (menu) {
      menu.querySelectorAll('.select-item').forEach(el => {
        el.classList.toggle('active', el.getAttribute('data-value') === val);
      });
    }
  }

  function initGenericCustomDropdown(wrapperId, btnId, labelId, menuId, valueId, options, onSelect) {
    const wrapper = document.getElementById(wrapperId);
    const btn = document.getElementById(btnId);
    const label = document.getElementById(labelId);
    const menu = document.getElementById(menuId);
    const input = document.getElementById(valueId) || document.querySelector(`[name="${valueId}"]`);
    if (!wrapper || !btn || !label || !menu) return;

    menu.innerHTML = '';
    options.forEach(opt => {
      const val = typeof opt === 'object' ? opt.value : opt;
      const text = typeof opt === 'object' ? opt.label : opt;
      const item = document.createElement('div');
      item.className = 'select-item';
      item.setAttribute('data-value', String(val));
      item.textContent = text;
      item.addEventListener('click', (e) => {
        e.stopPropagation();
        if (input) input.value = String(val);
        label.textContent = text;
        menu.querySelectorAll('.select-item').forEach(el => el.classList.remove('active'));
        item.classList.add('active');
        menu.classList.remove('open');
        wrapper.classList.remove('is-open');
        const parentRow = wrapper.closest('.toggle-row');
        if (parentRow) parentRow.classList.remove('dropdown-active');
        if (onSelect) onSelect(val);
      });
      menu.appendChild(item);
    });

    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = menu.classList.contains('open');
      closeAllDropdowns();
      if (!isOpen) {
        menu.classList.add('open');
        wrapper.classList.add('is-open');
        const parentRow = wrapper.closest('.toggle-row');
        if (parentRow) parentRow.classList.add('dropdown-active');
      }
    });
  }

  // --- DYNAMIC MULTI-MONITOR RESOLUTION DETECTION (1080p, 1440p, 4K) ---
  window.onDisplayMetricsChanged = function(metrics) {
    if (!metrics) return;
    const b = document.body;
    b.classList.remove('display-1080p', 'display-1440p', 'display-4k');
    b.classList.add(`display-${metrics.category || '1080p'}`);
    b.style.setProperty('--screen-dpr', metrics.dpr || 1);
    b.style.setProperty('--screen-w', `${metrics.width || window.innerWidth}px`);
    b.style.setProperty('--screen-h', `${metrics.height || window.innerHeight}px`);
    console.log(`[Display Metrics Updated] Category: ${metrics.category}, DPR: ${metrics.dpr}`);
  };

  function detectClientDisplayProfile() {
    const dpr = window.devicePixelRatio || 1;
    const sw = window.screen.width * (dpr >= 1 ? dpr : 1);
    const sh = window.screen.height * (dpr >= 1 ? dpr : 1);
    let cat = '1080p';
    if (sw >= 3600 || sh >= 2000) cat = '4k';
    else if (sw >= 2400 || sh >= 1350) cat = '1440p';
    window.onDisplayMetricsChanged({ width: sw, height: sh, dpr: dpr, category: cat });
  }
  window.addEventListener('resize', detectClientDisplayProfile, { passive: true });

  function setGenericDropdownValue(labelId, menuId, valueId, val, defaultLabel) {
    const label = document.getElementById(labelId);
    const menu = document.getElementById(menuId);
    const input = document.getElementById(valueId);
    const stringVal = String(val);
    if (input) input.value = stringVal;
    if (menu) {
      let matchedLabel = defaultLabel || stringVal;
      menu.querySelectorAll('.select-item').forEach(el => {
        const isMatch = el.getAttribute('data-value') === stringVal;
        el.classList.toggle('active', isMatch);
        if (isMatch) matchedLabel = el.textContent;
      });
      if (label) label.textContent = matchedLabel;
    } else if (label) {
      label.textContent = defaultLabel || stringVal;
    }
  }

  function onUpdateCheckResult(jsonStr) {
    try {
      const res = JSON.parse(jsonStr);
      const title = document.getElementById('update-status-title');
      const sub = document.getElementById('update-status-sub');
      const icon = document.getElementById('update-status-icon');
      const banner = document.getElementById('update-check-banner');

      if (banner) {
        banner.classList.remove('update-available', 'update-error');
      }

      if (res.has_update) {
        if (title) title.textContent = `New Update Available: ${res.latest_version}`;
        if (sub) sub.textContent = `A newer release is available on GitHub. Click 'Open GitHub Releases' below to download.`;
        if (icon) icon.textContent = '★';
        if (banner) banner.classList.add('update-available');
      } else if (res.success) {
        if (title) title.textContent = 'Up to Date';
        if (sub) sub.textContent = `Guild Wars Reforge Tracker v${res.current_version} is currently the latest version.`;
        if (icon) icon.textContent = '✓';
      } else {
        if (title) title.textContent = `Current Version: v${res.current_version}`;
        if (sub) sub.textContent = `Displaying cached release history (offline / rate-limited).`;
        if (icon) icon.textContent = 'ℹ';
      }

      const container = document.getElementById('release-history-container');
      if (container && Array.isArray(res.releases)) {
        container.innerHTML = '';
        res.releases.forEach((rel, idx) => {
          const card = document.createElement('div');
          card.className = `release-card ${idx === 0 ? 'release-latest' : ''}`;

          const header = document.createElement('div');
          header.className = 'release-card-header';

          const tag = document.createElement('span');
          tag.className = 'release-tag';
          tag.textContent = rel.name || rel.tag;

          const date = document.createElement('span');
          date.className = 'release-date';
          date.textContent = rel.date ? rel.date.split('T')[0] : '';

          header.appendChild(tag);
          header.appendChild(date);

          const body = document.createElement('div');
          body.className = 'release-body';
          body.textContent = rel.body || 'No release notes provided.';

          card.appendChild(header);
          card.appendChild(body);
          container.appendChild(card);
        });
      }
    } catch (e) {
      console.error('Failed to parse update check result:', e);
    }
  }

  function onExportProgressionReady(jsonStr) {
    try {
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const dateStr = new Date().toISOString().slice(0, 10);
      a.download = `gw_reforge_backup_${dateStr}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Failed to download exported JSON:', e);
    }
  }

  function onImportProgressionFinished(success, message) {
    if (success) {
      alert(`Progression imported successfully!\n${message}`);
      if (backend && backend.request_initial_data) {
        backend.request_initial_data();
      }
    } else {
      alert(`Import failed:\n${message}`);
    }
  }

  function openFirstLaunchSetupModal() {
    const setupName = document.getElementById('setup-profile-name');
    if (setupName) {
      setupName.value = (state.currentProfile && state.currentProfile !== 'Default') ? state.currentProfile : 'Hero';
    }
    setModalSelectValue('setup-profile-prof-label', 'setup-profile-prof-menu', 'setup-profile-prof-value', state.currentProfession || 'All Professions');
    const classicRadio = document.getElementById('setup-scheme-classic');
    const altRadio = document.getElementById('setup-scheme-alternate');
    if (classicRadio) classicRadio.checked = (state.preferences.color_scheme !== 'alternate');
    if (altRadio) altRadio.checked = (state.preferences.color_scheme === 'alternate');
    document.querySelectorAll('#modal-initial-setup .scheme-option-card').forEach(card => {
      const r = card.querySelector('input[type="radio"]');
      card.classList.toggle('active', Boolean(r && r.checked));
    });
    const lowGpu = document.getElementById('setup-low-gpu');
    if (lowGpu) lowGpu.checked = Boolean(state.preferences.low_gpu_mode);
    openModal('modal-initial-setup');
  }

  function closeAllDropdowns() {
    document.querySelectorAll('.select-menu-animated.open').forEach(menu => {
      menu.classList.remove('open');
    });
    document.querySelectorAll('.settings-custom-select-wrapper.is-open').forEach(w => {
      w.classList.remove('is-open');
    });
    document.querySelectorAll('.toggle-row.dropdown-active').forEach(r => {
      r.classList.remove('dropdown-active');
    });
    const sMenu = document.getElementById('status-filter-menu');
    const pMenu = document.getElementById('prof-filter-menu');
    const profMenu = document.getElementById('profile-dropdown-menu');
    if (sMenu) sMenu.classList.remove('open');
    if (pMenu) pMenu.classList.remove('open');
    if (profMenu) profMenu.classList.remove('open');
  }

  function openEditProfileModal() {
    document.getElementById('edit-profile-input').value = state.currentProfile;
    setModalSelectValue('edit-profile-prof-label', 'edit-profile-prof-menu', 'edit-profile-prof-value', state.currentProfession || 'All Professions');
    openModal('modal-edit-profile');
  }

  let qrCodeInstance = null;

  function openQrSyncModal() {
    let pairingUrl = 'http://127.0.0.1:8848';
    let roomCode = 'GW-SYNC';

    if (backend && backend.get_companion_pairing_info) {
      try {
        const info = JSON.parse(backend.get_companion_pairing_info());
        if (info.pairing_url) pairingUrl = info.pairing_url;
        if (info.room_code) roomCode = info.room_code;
      } catch (e) {
        console.error('Error fetching companion pairing info:', e);
      }
    }

    const roomEl = document.getElementById('qr-room-code');
    if (roomEl) roomEl.textContent = roomCode;

    const urlInput = document.getElementById('qr-pairing-url');
    if (urlInput) urlInput.value = pairingUrl;

    const qrContainer = document.getElementById('qr-code-canvas');
    if (qrContainer) {
      qrContainer.innerHTML = '';
      if (typeof QRCode !== 'undefined') {
        qrCodeInstance = new QRCode(qrContainer, {
          text: pairingUrl,
          width: 180,
          height: 180,
          colorDark: '#0B0D13',
          colorLight: '#FFFFFF',
          correctLevel: QRCode.CorrectLevel.M
        });
      } else {
        qrContainer.textContent = pairingUrl;
      }
    }

    openModal('modal-qr-sync');
  }

  // --- Modal Controls ---
  function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    stopAuroraCanvas();
    modal.style.display = 'flex';
    requestAnimationFrame(() => modal.classList.add('open'));
  }

  function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.remove('open');
    setTimeout(() => {
      modal.style.display = 'none';
      if (!document.querySelector('.modal-backdrop.open')) {
        startAuroraCanvas();
      }
    }, 180);
  }

  function showConfirmModal(title, message, onConfirm) {
    document.getElementById('confirm-modal-title').textContent = title;
    document.getElementById('confirm-modal-message').textContent = message;
    openModal('modal-confirm');

    const okBtn = document.getElementById('btn-confirm-ok');
    const newOk = okBtn.cloneNode(true);
    okBtn.parentNode.replaceChild(newOk, okBtn);

    if (!onConfirm) {
      newOk.textContent = 'OK';
    } else {
      newOk.textContent = 'Yes, Confirm';
    }

    newOk.addEventListener('click', () => {
      closeModal('modal-confirm');
      if (onConfirm) onConfirm();
    });
  }

  // --- Dropdown Rendering ---
  function renderProfileSection() {
    const display = document.getElementById('profile-name-display');
    const menu = document.getElementById('profile-dropdown-menu');
    const profTag = state.currentProfession && state.currentProfession !== 'All Professions'
      ? ` (${state.currentProfession})`
      : '';
    display.textContent = `${state.currentProfile}${profTag}`;
    menu.innerHTML = '';

    state.profiles.forEach(p => {
      const item = document.createElement('div');
      item.className = `profile-dropdown-item ${p === state.currentProfile ? 'active' : ''}`;
      item.textContent = p;
      item.addEventListener('click', () => {
        if (backend && backend.switch_profile) {
          backend.switch_profile(p);
        } else {
          state.currentProfile = p;
          renderProfileSection();
        }
        menu.classList.remove('open');
      });
      menu.appendChild(item);
    });
  }

  function renderProfessionFilterDropdown() {
    const menu = document.getElementById('prof-filter-menu');
    menu.innerHTML = '';

    const labelEl = document.getElementById('prof-filter-label');
    if (labelEl) {
      labelEl.textContent = (state.profFilter === 'All Professions') ? 'Class: All' : state.profFilter;
    }

    PROFESSIONS_LIST.forEach(p => {
      const item = document.createElement('div');
      item.className = `select-item ${p === state.profFilter ? 'active' : ''}`;
      item.setAttribute('data-value', p);
      item.textContent = (p === 'All Professions') ? 'Class: All' : p;
      item.addEventListener('click', () => {
        state.profFilter = p;
        document.getElementById('prof-filter-label').textContent = (p === 'All Professions') ? 'Class: All' : p;
        menu.querySelectorAll('.select-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        menu.classList.remove('open');
        renderQuestList(false);
        updateProgressDisplay();
      });
      menu.appendChild(item);
    });
  }

  function onSyncProgress(percent, msg) {
    const btn = document.getElementById('btn-sync-db');
    const icon = btn.querySelector('.sync-icon');
    const label = document.getElementById('sync-btn-label');
    btn.disabled = true;
    icon.classList.add('spinning');
    label.textContent = `${msg} (${percent}%)`;
  }

  function onSyncFinished(success, message) {
    const btn = document.getElementById('btn-sync-db');
    const icon = btn.querySelector('.sync-icon');
    const label = document.getElementById('sync-btn-label');
    btn.disabled = false;
    icon.classList.remove('spinning');
    label.textContent = 'Sync Database from Wiki';
    showConfirmModal('Database Synchronization', message || 'Database synchronization complete.', null);
  }

  // Mock data for standalone browser testing
  function initMockData() {
    state.questDb = {
      'Prophecies': ['--- ASCALON ---', 'Ascalon Tutorials', 'The Great Northern Wall', 'Defend Droknar\'s Forge', 'The Hero\'s Challenge'],
      'Factions': ['--- SHING JEA ISLAND ---', 'A Belt Pouch', 'Minister Cho\'s Estate', 'Red Tape', 'Imperial Assistance'],
      'Nightfall': ['--- ISTAN ---', 'Chahbek Village', 'Isle of the Dead', 'Secrets in the Shadow', 'For a Price'],
      'Eye of the North': ['--- FAR SHIVERPEAKS ---', 'Boreal Station'],
      'Beyond': ['--- WAR IN KRYTA ---', 'The War in Kryta'],
      'LDoA': ['--- LEVELING ---', 'Reach Level 10 (Charr at the Gate)', 'Reach Level 20 (Legendary Defender)']
    };
    state.questMeta = {
      'Red Tape': { campaign: 'Factions', location: 'Wajjun Bazaar', profession: '' },
      'Imperial Assistance': { campaign: 'Factions', location: 'Wajjun Bazaar', profession: '' },
      'Isle of the Dead': { campaign: 'Nightfall', location: 'Istan', profession: '', url: 'https://wiki.guildwars.com/wiki/Isle_of_the_Dead_(quest)' }
    };
    applyPreferencesToDOM();
    renderProfileSection();
    renderProfessionFilterDropdown();
    renderQuestList(false);
    updateProgressDisplay();
  }

})();
