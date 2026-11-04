(() => {
  'use strict';

  const session = window.looksyBootstrap.session;
  const $ = id => document.getElementById(id);
  const form = $('campaign-form');
  const tabs = [...document.querySelectorAll('[data-kind]')];
  const presets = [...document.querySelectorAll('[data-target]')];
  const steps = ['Business and location', 'Research options', 'Review sources and costs', 'Your results'];
  const pageSize = 50;
  const currency = new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD'});
  const readable = value => String(value ?? '').replaceAll('_', ' ');
  let step = 1;
  let job = null;
  let kind = 'businesses';
  let offset = 0;
  let rowIndex = 0;
  let query = '';
  let requestVersion = 0;
  let workspaceVersion = 0;
  let exportPreviewVersion = 0;
  let searchTimer;
  let loading = false;
  let working = false;

  function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text != null) element.textContent = text;
    return element;
  }

  function sourceUrl(value) {
    try {
      const url = new URL(value);
      return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url : null;
    } catch {
      return null;
    }
  }

  function sourceLink(value, label) {
    const url = sourceUrl(value);
    if (!url) return node('span', 'hint', 'Not available');
    const anchor = node('a', '', (label || url.hostname.replace(/^www\./, '')) + ' ↗');
    anchor.href = url.href;
    anchor.target = '_blank';
    anchor.rel = 'noopener noreferrer';
    return anchor;
  }

  function message(text = '') {
    $('message').textContent = text;
    $('message').hidden = !text;
    if (text) $('message').scrollIntoView({block: 'nearest'});
  }

  async function api(path, body) {
    const options = {headers: {'X-Looksy-Key': session}};
    if (body !== undefined) {
      options.method = 'POST';
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }
    const response = await fetch(path, options);
    const result = await response.json();
    if (!response.ok) throw Error(result.error || 'The action could not complete.');
    return result;
  }

  function show(view, nextStep) {
    step = nextStep;
    for (const name of ['create', 'plan', 'result']) $(name + '-view').hidden = view !== name;
    [...$('chapters').children].forEach((chapter, i) => {
      if (i + 1 === step) chapter.setAttribute('aria-current', 'step');
      else chapter.removeAttribute('aria-current');
      chapter.classList.toggle('complete', i + 1 < step);
    });
    $('campaign-step-label').textContent = 'Step ' + step + ' of 4 · ' + steps[step - 1];
  }

  function syncOptions() {
    presets.forEach(button => {
      button.setAttribute('aria-pressed', String(Number(button.dataset.target) === Number($('target').value)));
    });
    $('offer-fields').hidden = !$('analysis-toggle').checked;
  }

  function setCampaignStep(nextStep) {
    const territory = nextStep === 1;
    show('create', nextStep);
    $('create-title').textContent = territory ? 'Find local businesses.' : 'Set your research options.';
    $('create-description').textContent = territory
      ? 'Start with the businesses you want to find and where to look.'
      : 'Choose how many businesses to find and the most to spend on Actor events.';
    $('target-fields').hidden = !territory;
    $('options-fields').hidden = territory;
    $('target-next').hidden = !territory;
    $('target-back').hidden = territory;
    $('plan-button').hidden = territory;
    syncOptions();
  }

  function advanceTarget() {
    if (!$('niche').reportValidity() || !$('locations').reportValidity()) return;
    setCampaignStep(2);
    $('target').focus();
  }

  function fillRequest(request) {
    form.elements.niche.value = request.niche;
    form.elements.locations.value = request.locations.join('\n');
    form.elements.target.value = request.target;
    form.elements.budget_usd.value = request.budget_usd;
    form.elements.include_contacts.checked = request.include_contacts;
    form.elements.analysis.checked = request.analysis;
    form.elements.offer.value = request.offer || '';
    syncOptions();
  }

  async function listJobs() {
    const data = await api('/api/jobs');
    $('connection').textContent = data.configured ? 'Apify key available' : 'Connect Apify to preview sources';
    const select = $('saved-jobs');
    select.replaceChildren(new Option('Recent campaigns', ''));
    for (const saved of data.jobs) {
      select.add(new Option(saved.request.niche + ' · ' + saved.request.locations.join(', '), saved.id));
    }
    select.value = job?.id || '';
    return data.jobs;
  }

  async function loadJob(id, {reset = false, table = kind, start = offset, search = query} = {}) {
    const version = ++requestVersion;
    if (reset) {
      clearTimeout(searchTimer);
      table = 'businesses';
      start = 0;
      search = '';
    }
    const params = new URLSearchParams({id, kind: table, offset: start, q: search});
    loading = true;
    try {
      const nextJob = await api('/api/job?' + params);
      if (version !== requestVersion) return;
      const changedRecord = id !== job?.id;
      if (reset || table !== kind || start !== offset || search !== query) rowIndex = 0;
      job = nextJob;
      kind = table;
      offset = start;
      query = search;
      if (reset) $('search').value = '';
      if (changedRecord) $('review-offer').value = job.request.offer || '';
      if (window.location.hash.slice(1) !== id) window.location.hash = id;
      $('saved-jobs').value = id;
      const previousStep = step;
      if (job.status === 'PLANNED') renderPlan();
      else renderResults();
      if (step !== previousStep || changedRecord) {
        const title = $(step === 3 ? 'plan-title' : 'result-title');
        title.focus({preventScroll: true});
        window.scrollTo(0, 0);
      }
    } catch (error) {
      if (version === requestVersion) {
        $('saved-jobs').value = job?.id || '';
        message(error.message);
      }
    } finally {
      if (version === requestVersion) loading = false;
    }
  }

  function stat(value, label) {
    const item = node('div', 'stat');
    item.append(node('b', '', value), node('span', '', label));
    return item;
  }

  function sourceDetails(actor) {
    const section = node('section', 'source');
    const name = (actor.slug || '').split('/').pop().replaceAll('-', ' ');
    section.append(node('h3', '', name || 'Research source'), node('p', 'hint', 'Build ' + (actor.build_number ?? 'unavailable')),
      sourceLink(actor.store_url, 'Actor details'));
    for (const [event, price] of Object.entries(actor.pricing?.events || {})) {
      const row = node('div', 'price-row');
      const value = typeof price.price_usd === 'number' ? '$' + price.price_usd : 'See account pricing';
      row.append(node('span', '', price.title || event), node('b', '', value));
      section.append(row);
    }
    return section;
  }

  function renderPlan() {
    const {request, plan} = job;
    show('plan', 3);
    $('plan-title').textContent = request.niche;
    $('plan-locations').textContent = request.locations.join(' · ');
    $('plan-summary').replaceChildren(
      stat(request.target.toLocaleString(), 'Business target'),
      stat(request.locations.length, 'Territories'),
      stat(currency.format(request.budget_usd), 'Actor event limit'),
      stat(request.include_contacts ? 'Included' : 'Off', 'Contact research')
    );
    $('plan-copy').replaceChildren(
      node('p', '', 'Approval starts paid research with a ' + currency.format(request.budget_usd) + ' Actor event limit. Apify platform usage is billed separately.'),
      node('p', 'hint', plan.cost_note),
      node('p', 'hint', 'Source coverage can limit how many businesses and contacts you receive.')
    );
    $('approve-button').textContent = 'Approve and start · ' + currency.format(request.budget_usd) + ' event limit';
    const sources = plan.actors.map(sourceDetails);
    $('source-details').replaceChildren(...(sources.length ? sources : [node('p', 'hint', 'No Actor prices are listed in this plan.')]));
  }

  function coverage(summary) {
    if (summary.partial) return 'Partial';
    if (summary.businesses === 0) return 'Empty';
    if (summary.businesses == null) return 'Pending';
    return summary.businesses < job.request.target ? 'Below target' : 'Target met';
  }

  function renderResults() {
    const summary = job.summary || {};
    show('result', 4);
    $('result-eyebrow').textContent = job.imported ? 'Imported research' : 'Campaign results';
    $('result-title').textContent = job.request.niche;
    $('result-locations').textContent = job.request.locations.join(' · ');
    $('result-status').textContent = readable(job.status);
    $('result-status').className = 'chip' + (['PARTIAL', 'ATTENTION', 'WAITING'].includes(job.status) ? ' amber' : '');
    $('run-message').textContent = job.progress?.message || 'Review your campaign.';
    $('run-message').classList.toggle('attention', job.status === 'ATTENTION');
    $('result-stats').replaceChildren(
      stat(summary.businesses ?? '—', 'Businesses found'),
      stat(summary.unique_emails ?? '—', 'Unique addresses'),
      stat(job.request.target, 'Business target'),
      stat(coverage(summary), 'Coverage')
    );
    tabs.forEach(button => {
      const current = button.dataset.kind === kind;
      button.setAttribute('aria-selected', String(current));
      button.tabIndex = current ? 0 : -1;
    });
    $('results-panel').setAttribute('aria-labelledby', 'tab-' + kind);
    $('analysis-controls').hidden = kind !== 'analysis';
    const ready = ['COMPLETE', 'PARTIAL', 'IMPORTED'].includes(job.status);
    $('request-analysis').disabled = !ready || job.analysis_status === 'AWAITING_ASSISTANT';
    if (!ready) $('analysis-status').textContent = 'AI review is available after research results are ready.';
    else if (job.analysis_status === 'AWAITING_ASSISTANT') $('analysis-status').textContent = 'Waiting for your active assistant.';
    else if (['COMPLETE', 'PARTIAL'].includes(job.analysis_status)) $('analysis-status').textContent = (summary.ai_reviewed ?? job.total) + ' businesses reviewed.';
    else $('analysis-status').textContent = '';
    $('resume-button').hidden = !['WAITING', 'ATTENTION'].includes(job.status) || job.imported;
    $('export-button').disabled = !job.total;
    const destination = $('export-destination');
    if (kind !== 'contacts') destination.value = 'research';
    for (const option of destination.options) option.disabled = kind !== 'contacts' && option.value !== 'research';
    if (destination.value === 'research') {
      $('export-status').textContent = kind === 'contacts'
        ? 'Research CSV includes all recorded contacts. Choose an import format to preview eligible rows.'
        : 'The Contacts tab also offers Instantly, Smartlead and HubSpot import formats.';
    }
    renderRows();
  }

  function field(label, value) {
    const detail = node('div', 'field');
    detail.append(node('span', '', label), value instanceof Node ? value : node('b', '', value || 'Not available'));
    return detail;
  }

  function renderDetail() {
    const detail = $('detail');
    const row = job.rows?.[rowIndex];
    if (!row) {
      detail.replaceChildren(node('p', 'eyebrow', 'Record details'), node('h2', '', 'Source evidence'),
        node('p', 'hint', 'Select a result to see its source details here.'));
      return;
    }
    if (kind === 'businesses') {
      detail.replaceChildren(node('p', 'eyebrow', 'Selected business'), node('h2', '', row.business_name),
        field('Location', row.address), field('Phone', row.phone), field('Website', sourceLink(row.website)),
        field('Contact result', (row.email_count ?? 0) + ' addresses · ' + readable(row.coverage)),
        field('Maps source', sourceLink(row.maps_source, 'Open the listing')));
    } else if (kind === 'contacts') {
      detail.replaceChildren(node('p', 'eyebrow', 'Contact to review'), node('h2', '', row.email || 'Address unavailable'),
        node('span', 'chip amber', readable(row.validation_status) || 'Unchecked'),
        field('Business', row.business_name), field('Source website', sourceLink(row.source_website)),
        field('Check reasons', readable(row.validation_reason)), field('Extraction review', readable(row.extraction_review)),
        node('p', 'hint', 'Website evidence may identify only the domain. Individual mailbox delivery is unconfirmed.'));
    } else {
      const sources = node('div', 'field');
      sources.append(node('span', '', 'Sources'));
      const links = (row.sources || []).map(url => sourceLink(url));
      sources.append(...(links.length ? links : [node('b', '', 'Not available')]));
      detail.replaceChildren(node('p', 'eyebrow', 'Assistant research note'), node('h2', '', row.business_name || 'Research note'),
        field('Note', row.note), field('Confidence', row.confidence), field('Next step', row.next_step), sources,
        node('p', 'hint', 'Review the cited evidence before drawing conclusions about buying intent.'));
    }
  }

  function emptyState() {
    const panel = node('div', 'empty');
    let heading, description;
    if (query) {
      heading = 'No matching records';
      description = 'Try a different search or clear the search field to see all rows.';
    } else if (kind === 'analysis') {
      heading = 'No AI research notes yet';
      description = job.analysis_status === 'AWAITING_ASSISTANT'
        ? 'Your active assistant has a review request.'
        : 'Describe your offer above to request a review when results are ready.';
    } else if (['RUNNING', 'QUEUED', 'WAITING'].includes(job.status)) {
      heading = 'Research is in progress';
      description = 'Available rows will appear as results are saved.';
    } else {
      heading = kind === 'contacts' ? 'No public contacts recorded' : 'No business listings recorded';
      description = kind === 'contacts' && !job.request.include_contacts
        ? 'Contact research was off for this campaign.'
        : 'Check the campaign status and territory above for context.';
    }
    panel.append(node('h3', '', heading), node('p', '', description));
    return panel;
  }

  function renderRows() {
    const rows = job.rows || [];
    rowIndex = Math.min(rowIndex, Math.max(0, rows.length - 1));
    const records = rows.map((row, index) => {
      const record = node('button', 'row');
      record.dataset.row = index;
      record.setAttribute('aria-pressed', String(index === rowIndex));
      record.classList.toggle('active', index === rowIndex);
      const position = node('span', 'row-icon', String(offset + index + 1).padStart(2, '0'));
      position.setAttribute('aria-hidden', 'true');
      const body = node('span');
      const title = row.business_name || (kind === 'analysis' && row.note?.slice(0, 100)) || 'Unnamed business';
      const subtitle = kind === 'contacts' ? row.email : kind === 'analysis' ? row.confidence : sourceUrl(row.website)?.hostname.replace(/^www\./, '');
      body.append(node('strong', '', title), node('small', '', subtitle));
      record.append(position, body);
      const status = kind === 'contacts' ? row.validation_status : kind === 'analysis' ? 'AI note' : row.coverage;
      if (status) record.append(node('span', 'chip ' + (kind === 'contacts' ? 'amber' : 'muted'), readable(status)));
      return record;
    });
    $('rows').replaceChildren(...(records.length ? records : [emptyState()]));
    $('page-info').textContent = rows.length ? (offset + 1) + '–' + (offset + rows.length) + ' of ' + job.total : '0 rows';
    $('previous').disabled = offset === 0;
    $('next').disabled = offset + rows.length >= job.total;
    renderDetail();
  }

  async function action(button, task) {
    if (working) return;
    const version = workspaceVersion;
    working = true;
    if (button) button.disabled = true;
    message();
    try {
      await task();
    } catch (error) {
      if (version === workspaceVersion) message(error.message);
    } finally {
      working = false;
      if (button) button.disabled = false;
      if (step === 4 && job) {
        $('export-button').disabled = !job.total;
        $('request-analysis').disabled = !['COMPLETE', 'PARTIAL', 'IMPORTED'].includes(job.status) || job.analysis_status === 'AWAITING_ASSISTANT';
      }
    }
  }

  function startWorkspace() {
    workspaceVersion++;
    requestVersion++;
    exportPreviewVersion++;
    clearTimeout(searchTimer);
    loading = false;
    message();
  }

  function newCampaign() {
    startWorkspace();
    job = null;
    kind = 'businesses';
    offset = rowIndex = 0;
    query = '';
    form.reset();
    form.querySelector('details').open = false;
    $('search').value = '';
    $('review-offer').value = '';
    $('export-destination').value = 'research';
    window.location.hash = '';
    $('saved-jobs').value = '';
    setCampaignStep(1);
    $('niche').focus();
  }

  $('target-next').addEventListener('click', advanceTarget);
  $('target-back').addEventListener('click', () => { setCampaignStep(1); $('niche').focus(); });
  presets.forEach(button => button.addEventListener('click', () => {
    $('target').value = button.dataset.target;
    syncOptions();
  }));
  $('target').addEventListener('input', syncOptions);
  $('analysis-toggle').addEventListener('change', syncOptions);

  // Validate the current chapter. An invalid field in a hidden chapter can't receive browser focus.
  form.noValidate = true;
  form.addEventListener('submit', event => {
    event.preventDefault();
    if (step === 1) { advanceTarget(); return; }
    if (!$('target').reportValidity() || !$('budget').reportValidity()) return;
    if ($('analysis-toggle').checked && $('offer').value.trim().length < 3) {
      form.querySelector('details').open = true;
      $('offer').focus();
      message('Add a short description of your offer for the AI review.');
      return;
    }
    const version = workspaceVersion;
    action($('plan-button'), async () => {
      $('plan-button').textContent = 'Checking current sources…';
      const values = new FormData(form);
      try {
        const result = await api('/api/plan', {
          niche: values.get('niche'), locations: values.get('locations'), target: Number(values.get('target')),
          budget_usd: Number(values.get('budget_usd')), include_contacts: values.has('include_contacts'),
          analysis: values.has('analysis'), offer: values.get('offer')
        });
        await listJobs();
        if (version === workspaceVersion) await loadJob(result.id, {reset: true});
      } finally {
        $('plan-button').textContent = 'Preview sources and costs';
      }
    });
  });

  $('new-button').addEventListener('click', newCampaign);
  $('edit-button').addEventListener('click', () => {
    startWorkspace();
    fillRequest(job.request);
    setCampaignStep(1);
    $('niche').focus();
  });
  $('saved-jobs').addEventListener('change', () => {
    if (!$('saved-jobs').value) return;
    startWorkspace();
    $('export-destination').value = 'research';
    loadJob($('saved-jobs').value, {reset: true});
  });

  function runSavedAction(buttonId, path, payload) {
    const id = job.id;
    const version = workspaceVersion;
    return action($(buttonId), async () => {
      await api(path, {id, ...payload});
      if (version === workspaceVersion) await loadJob(id);
    });
  }

  $('approve-button').addEventListener('click', () => runSavedAction('approve-button', '/api/approve', {hash: job.plan.hash}));
  $('resume-button').addEventListener('click', () => runSavedAction('resume-button', '/api/resume', {}));
  $('request-analysis').addEventListener('click', () => runSavedAction('request-analysis', '/api/analysis-request', {offer: $('review-offer').value}));
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => {
      clearTimeout(searchTimer);
      loadJob(job.id, {table: tab.dataset.kind, start: 0, search: $('search').value});
    });
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      else if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = tabs.length - 1;
      else return;
      event.preventDefault();
      tabs[next].focus();
      tabs[next].click();
    });
  });
  $('search').addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => loadJob(job.id, {start: 0, search: $('search').value}), 250);
  });
  $('previous').addEventListener('click', () => loadJob(job.id, {start: Math.max(0, offset - pageSize)}));
  $('next').addEventListener('click', () => loadJob(job.id, {start: offset + pageSize}));
  $('rows').addEventListener('click', event => {
    const record = event.target.closest('[data-row]');
    if (!record) return;
    rowIndex = Number(record.dataset.row);
    for (const button of $('rows').querySelectorAll('[data-row]')) {
      button.classList.toggle('active', button === record);
      button.setAttribute('aria-pressed', String(button === record));
    }
    renderDetail();
    if (window.matchMedia('(max-width: 730px)').matches) $('detail').scrollIntoView({block: 'start'});
  });

  $('export-button').addEventListener('click', () => action($('export-button'), async () => {
    const destination = $('export-destination').value;
    const table = kind;
    const params = new URLSearchParams({id: job.id, kind: table, destination});
    const response = await fetch('/api/export?' + params, {headers: {'X-Looksy-Key': session}});
    if (!response.ok) throw Error('The export could not be read.');
    const url = URL.createObjectURL(await response.blob());
    try {
      const anchor = node('a');
      anchor.href = url;
      anchor.download = 'looksy-' + (destination === 'research' ? table : destination) + '.csv';
      anchor.click();
    } finally {
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
  }));
  $('export-destination').addEventListener('change', async () => {
    const version = ++exportPreviewVersion;
    const destination = $('export-destination').value;
    const id = job.id;
    if (destination === 'research') {
      $('export-status').textContent = 'Research CSV includes all recorded rows in this table.';
      return;
    }
    $('export-status').textContent = 'Checking eligible rows…';
    try {
      const params = new URLSearchParams({id, kind, destination});
      const result = await api('/api/export-preview?' + params);
      if (version !== exportPreviewVersion || kind !== 'contacts' || job?.id !== id || $('export-destination').value !== destination) return;
      $('export-status').textContent = result.exported + ' of ' + result.input_rows + ' rows included · ' + result.duplicates
        + ' duplicates · ' + result.missing_or_invalid_email + ' missing or invalid addresses. Check column mapping on import. Mailbox delivery is unconfirmed.';
    } catch (error) {
      if (version === exportPreviewVersion && kind === 'contacts' && job?.id === id) $('export-status').textContent = error.message;
    }
  });

  setInterval(() => {
    if (!working && !loading && step === 4 && job && (['RUNNING', 'QUEUED', 'WAITING'].includes(job.status) || job.analysis_status === 'AWAITING_ASSISTANT')) loadJob(job.id);
  }, 3500);

  const initialWorkspace = workspaceVersion;
  action(null, async () => {
    const jobs = await listJobs();
    if (initialWorkspace !== workspaceVersion) return;
    const hash = window.location.hash.slice(1);
    const requested = jobs.find(entry => entry.id === hash);
    if (requested) {
      await loadJob(requested.id, {reset: true});
      return;
    }
    if (window.looksyBootstrap.draft) {
      fillRequest(window.looksyBootstrap.draft);
      setCampaignStep(1);
      return;
    }
    const saved = jobs[0];
    if (saved) await loadJob(saved.id, {reset: true});
    else setCampaignStep(1);
  });
})();
