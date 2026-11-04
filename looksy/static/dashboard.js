(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const {session, next} = window.looksyBootstrap;
  const providers = {anthropic: 'Claude (Anthropic)', openrouter: 'OpenRouter', openai: 'OpenAI', gemini: 'Gemini'};
  let settings, editor = null, saving = false, historyRequest = 0;

  async function api(path, body) {
    const options = {headers: {'X-Looksy-Key': session}, credentials: 'same-origin', cache: 'no-store', redirect: 'error'};
    if (body !== undefined) {
      options.method = 'POST';
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }
    const response = await fetch(path, options);
    if (!response.ok) {
      const error = new Error('Request failed');
      error.status = response.status;
      throw error;
    }
    return response.json();
  }

  function updateSettings(data) {
    if (!data || !['apify_verified', 'apify_configured', 'onboarded'].every(key => typeof data[key] === 'boolean')
        || (data.ai_provider !== null && !Object.hasOwn(providers, data.ai_provider))) {
      throw new Error('Unexpected settings');
    }
    settings = data;
  }

  function feedback(id, message = '') {
    $(id).textContent = message;
    $(id).hidden = !message;
  }

  function clearSecrets() {
    $('apify-key').value = '';
    $('ai-key').value = '';
  }
  window.addEventListener('pagehide', clearSecrets);

  function currentPage() {
    return ['#settings', '#history'].includes(location.hash) ? location.hash.slice(1) : 'home';
  }

  function configureStep(apify, editing) {
    $('steps').hidden = editing;
    Array.from($('steps').children).forEach((item, index) => {
      if (index === (apify ? 0 : 1)) item.setAttribute('aria-current', 'step');
      else item.removeAttribute('aria-current');
    });
    $('setup-label').textContent = editing ? 'Workspace settings' : (apify ? 'Setup · Step 1 of 2' : 'Setup · Step 2 of 2 · Optional');
    const external = settings.apify_external === true;
    $('setup-title').textContent = apify ? (editing && external ? 'Verify your configured key' : editing ? 'Replace your Apify key' : 'Connect your Apify account') :
      (editing ? 'Set your AI provider' : 'Choose how to use AI');
    $('setup-description').textContent = apify ?
      'Looksy checks your key with a read-only account request. You’ll review costs before starting any collection.' :
      'Your current assistant handles everyday research. Add a provider key only if you want to request a direct AI call.';
    $('apify-form').hidden = !apify;
    $('ai-step').hidden = apify;
    $('apify-key').required = !external && (editing || !settings.apify_configured);
    $('apify-key').hidden = external;
    document.querySelector('label[for="apify-key"]').hidden = external;
    $('apify-hint').textContent = external ?
      'Your environment supplies the Apify key. Restart Looksy without the environment override to change it here.' : !editing && settings.apify_configured ?
      'A key is already configured. Leave this field empty to verify it, or enter a replacement.' :
      'Paste the API token from your Apify Console. Looksy saves it on this device.';
    $('verify').textContent = external ? 'Verify configured key' : editing ? 'Verify and replace key' : 'Verify key';
    $('assistant-choice').hidden = editing;
    $('ai-form').hidden = !editing;
    $('toggle-provider').textContent = 'Add a provider key';
    $('toggle-provider').setAttribute('aria-expanded', 'false');
    $('provider').value = settings.ai_provider || 'anthropic';
    document.querySelectorAll('.cancel').forEach(button => { button.hidden = !editing; });
  }

  function render(focus = true) {
    clearSecrets();
    for (const id of ['apify-error', 'ai-error', 'settings-error']) feedback(id);
    for (const id of ['apify-key', 'ai-key']) $(id).removeAttribute('aria-invalid');
    $('manual-copy').hidden = true;
    $('copy-text').value = '';
    $('notice').textContent = '';
    const ready = settings.apify_verified && settings.onboarded;
    const page = currentPage();
    if (page !== 'settings') editor = null;
    const view = ready && !editor ? page : 'setup';
    for (const id of ['setup', 'home', 'history', 'settings']) $(id).hidden = id !== view;
    $('loading').hidden = true;
    $('layout').hidden = false;
    $('field-notes').hidden = !(view === 'home' || (view === 'setup' && !ready));
    $('nav').hidden = !ready;
    for (const link of $('nav').querySelectorAll('a')) {
      if (link.hash === '#' + page) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    }
    if (view === 'setup') configureStep(ready ? editor === 'apify' : !settings.apify_verified, ready);
    if (view === 'settings') {
      $('apify-state').textContent = settings.apify_external ? 'Using the verified key supplied by your environment.' : 'Account key verified.';
      $('edit-apify').textContent = settings.apify_external ? 'Verify configured key' : 'Replace key';
      $('ai-state').textContent = settings.ai_provider ? providers[settings.ai_provider] + ' key saved.' : 'Using your current assistant.';
      $('edit-ai').textContent = settings.ai_provider ? 'Change provider' : 'Add provider';
      $('remove-ai').hidden = !settings.ai_provider;
    }
    if (view === 'history') loadHistory();
    if (focus) $(view + '-title').focus();
    document.title = $(view + '-title').textContent + ' · Looksy Agent';
  }

  async function openWorkspace() {
    $('reload').hidden = true;
    feedback('load-error');
    $('loading-title').textContent = 'Opening your workspace…';
    $('loading').querySelector('.loading-lines').hidden = false;
    try {
      updateSettings(await api('/api/settings'));
      if (settings.onboarded && settings.apify_verified && next === '/leads') return location.replace('/leads');
      render(false);
    } catch {
      $('loading-title').textContent = 'Workspace unavailable';
      $('loading').querySelector('.loading-lines').hidden = true;
      feedback('load-error', 'Reopen the private launcher from your assistant, or try again if it is still running.');
      $('reload').hidden = false;
      $('loading-title').focus();
    }
  }

  function busy(value) {
    saving = value;
    document.querySelectorAll('#setup button, #setup select, #setup input, #settings button').forEach(control => { control.disabled = value; });
    $('setup').setAttribute('aria-busy', String(value));
    $('settings').setAttribute('aria-busy', String(value));
  }

  async function save(kind, payload, trigger, errorId) {
    if (saving) return;
    const onboarding = !settings.onboarded || !settings.apify_verified;
    const apify = kind === 'apify';
    const field = apify ? $('apify-key') : $('ai-key');
    const oldLabel = trigger.textContent;
    feedback(errorId);
    field.removeAttribute('aria-invalid');
    busy(true);
    trigger.textContent = apify ? 'Verifying…' : 'Saving…';
    clearSecrets();
    let success = false;
    try {
      updateSettings(await api('/api/settings/' + kind, payload));
      if (apify && !settings.apify_verified) throw new Error('Verification incomplete');
      success = true;
    } catch (error) {
      let message = apify ? 'Couldn’t verify the Apify key. Check the token, its account-read permission and your connection, then try again.' :
        'Couldn’t save this choice. Check your local connection and try again.';
      if (error.status === 403) message = 'Your local session could not authorize this change. Reopen the private launcher and try again.';
      feedback(errorId, message);
      if (!payload.skip && !field.hidden) field.setAttribute('aria-invalid', 'true');
    } finally {
      busy(false);
      trigger.textContent = oldLabel;
    }
    if (!success) {
      (payload.skip || field.hidden ? trigger : field).focus();
      return;
    }
    editor = null;
    if (onboarding && settings.apify_verified && settings.onboarded) {
      if (next === '/leads') return location.replace('/leads');
      if (currentPage() !== 'home') window.history.replaceState(null, '', '#home');
    }
    render();
    $('notice').textContent = apify ? 'Apify key verified.' :
      payload.skip ? 'Using your current assistant.' : 'Provider key saved.';
  }

  $('apify-form').addEventListener('submit', event => {
    event.preventDefault();
    const key = settings.apify_external ? '' : $('apify-key').value.trim();
    if (!key && $('apify-key').required) {
      feedback('apify-error', 'Enter your Apify key to verify the account.');
      $('apify-key').focus();
      return;
    }
    save('apify', key ? {key} : {}, $('verify'), 'apify-error');
  });
  $('ai-form').addEventListener('submit', event => {
    event.preventDefault();
    const key = $('ai-key').value.trim();
    if (!key) {
      feedback('ai-error', 'Enter a key for the selected provider.');
      $('ai-key').focus();
      return;
    }
    save('ai', {provider: $('provider').value, key}, $('save-ai'), 'ai-error');
  });
  $('skip-ai').addEventListener('click', () => save('ai', {skip: true}, $('skip-ai'), 'ai-error'));
  $('remove-ai').addEventListener('click', () => save('ai', {skip: true}, $('remove-ai'), 'settings-error'));
  $('toggle-provider').addEventListener('click', () => {
    const show = $('ai-form').hidden;
    $('ai-form').hidden = !show;
    $('ai-key').value = '';
    feedback('ai-error');
    $('toggle-provider').textContent = show ? 'Hide provider form' : 'Add a provider key';
    $('toggle-provider').setAttribute('aria-expanded', String(show));
    if (show) $('provider').focus();
  });
  $('provider').addEventListener('change', () => { $('ai-key').value = ''; feedback('ai-error'); });
  for (const kind of ['apify', 'ai']) $('edit-' + kind).addEventListener('click', () => { editor = kind; render(); });
  document.querySelectorAll('.cancel').forEach(button => button.addEventListener('click', () => { editor = null; render(); }));
  window.addEventListener('hashchange', () => { editor = null; if (settings) render(); });
  document.querySelector('.skip').addEventListener('click', event => { event.preventDefault(); $('main').focus(); });
  $('reload').addEventListener('click', openWorkspace);

  async function copyRequest(request, button) {
    try {
      await navigator.clipboard.writeText(request);
      $('manual-copy').hidden = true;
      const label = button.textContent;
      if (label !== 'Copied') {
        button.textContent = 'Copied';
        setTimeout(() => { button.textContent = label; }, 1800);
      }
      $('notice').textContent = 'Request copied. Paste it into your assistant.';
    } catch {
      $('notice').textContent = 'Copy the selected request and paste it into your assistant.';
      $('manual-copy').hidden = false;
      $('copy-text').value = request;
      $('copy-text').focus();
      $('copy-text').select();
    }
  }
  $('copy-example').addEventListener('click', () => copyRequest($('example').textContent, $('copy-example')));

  function node(tag, content, className) {
    const element = document.createElement(tag);
    if (content) element.textContent = content;
    if (className) element.className = className;
    return element;
  }

  function historyRow(item, isBrief) {
    const row = node('li');
    const title = isBrief ? item.goal : item.request?.niche;
    row.append(node('h3', title || (isBrief ? 'Research brief' : 'Local Leads campaign')));
    const stamp = new Date(isBrief ? item.created : item.created_at);
    const date = Number.isNaN(stamp.getTime()) ? '' : stamp.toLocaleDateString(undefined, {dateStyle: 'medium'});
    const meta = [date, isBrief ? item.deliverable : item.status].filter(Boolean);
    if (meta.length) row.append(node('p', meta.join(' · ')));
    if (isBrief && item.next_step) row.append(node('p', 'Next step · ' + item.next_step));
    if (!isBrief && Array.isArray(item.request?.locations)) row.append(node('p', item.request.locations.join(', ')));
    if (isBrief) {
      const button = node('button', 'Copy reopen request', 'row-action');
      button.type = 'button';
      button.addEventListener('click', () => copyRequest('Use Looksy Agent to reopen saved brief ' + item.id + ' and show its results and next step.', button));
      row.append(button);
    } else {
      const link = node('a', 'Open campaign →', 'row-action');
      link.href = '/leads#' + encodeURIComponent(item.id);
      row.append(link);
    }
    return row;
  }

  async function loadHistory() {
    const request = ++historyRequest;
    $('history-status').hidden = false;
    $('history-error').hidden = true;
    $('history-lists').hidden = true;
    try {
      const {briefs, campaigns} = await api('/api/history');
      if (request !== historyRequest) return;
      if (!Array.isArray(briefs) || !Array.isArray(campaigns)) throw new Error('Unexpected history');
      for (const [kind, items] of [['brief', briefs], ['campaign', campaigns]]) {
        $(kind + '-list').replaceChildren(...items.map(item => historyRow(item, kind === 'brief')));
        $(kind + '-empty').hidden = items.length !== 0;
      }
      $('history-lists').hidden = false;
    } catch {
      if (request === historyRequest) $('history-error').hidden = false;
    } finally {
      if (request === historyRequest) $('history-status').hidden = true;
    }
  }
  $('retry-history').addEventListener('click', loadHistory);
  openWorkspace();
})();
