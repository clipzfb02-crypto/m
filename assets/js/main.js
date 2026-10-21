(() => {
  const D = window.DEALER;
  const { locale, currency, distanceUnit, email, phone, finance } = D;
  const cars = window.INVENTORY;
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  const money = new Intl.NumberFormat(locale, { style: 'currency', currency, maximumFractionDigits: 0 });
  const number = new Intl.NumberFormat(locale);
  const formatMoney = (amount) => money.format(Math.round(amount));
  const formatMiles = (miles) => `${number.format(miles)} ${distanceUnit}`;
  const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
  const carTitle = (car) => `${car.year} ${car.make} ${car.model}`;
  const byId = (id) => cars.find((car) => car.id === id);
  const slug = (text) => text.toLowerCase().replace(/[^a-z0-9]+/g, '-');
  const icon = (id) => `<svg class="icon" aria-hidden="true"><use href="#${id}"/></svg>`;
  const esc = (value) =>
    String(value).replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch]);
  const economyText = (car) =>
    car.range ? `${number.format(car.range)} ${distanceUnit} range` : `${car.mpg.city} city / ${car.mpg.highway} hwy mpg`;

  // ---------------------------------------------------------------------------
  // Money maths
  // ---------------------------------------------------------------------------

  function monthlyPayment(principal, apr, months) {
    if (principal <= 0 || months <= 0) return 0;
    const rate = apr / 100 / 12;
    if (rate === 0) return principal / months;
    return (principal * rate) / (1 - Math.pow(1 + rate, -months));
  }

  // The loan a monthly payment can cover: the inverse of monthlyPayment.
  function principalFor(monthly, apr, months) {
    if (monthly <= 0 || months <= 0) return 0;
    const rate = apr / 100 / 12;
    if (rate === 0) return monthly * months;
    return (monthly * (1 - Math.pow(1 + rate, -months))) / rate;
  }

  const estimatedMonthly = (price) =>
    monthlyPayment(price * (1 - finance.downPaymentPct / 100), finance.apr, finance.termMonths);

  // ---------------------------------------------------------------------------
  // Small helpers: storage, toast, odometer digits
  // ---------------------------------------------------------------------------

  const store = {
    get(key, fallback) {
      try {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : fallback;
      } catch (e) {
        return fallback;
      }
    },
    set(key, value) {
      try {
        localStorage.setItem(key, JSON.stringify(value));
      } catch (e) {}
    },
  };

  const toastEl = $('#toast');
  let toastTimer;
  function toast(message) {
    toastEl.textContent = message;
    toastEl.classList.add('is-visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove('is-visible'), 2800);
  }

  const DIGITS = [...'0123456789'].map((d) => `<span>${d}</span>`).join('');
  const odoCells = (text, setDigits) =>
    [...text]
      .map((ch) =>
        /\d/.test(ch)
          ? `<span class="odo-cell"><span class="odo-strip"${setDigits ? ` style="--d: ${ch}"` : ''}>${DIGITS}</span></span>`
          : `<span class="odo-sep">${esc(ch)}</span>`
      )
      .join('');

  const odometerHTML = (text) =>
    `<span class="odo"><span class="sr-only">${esc(text)}</span><span class="odo-cells" aria-hidden="true">${odoCells(text, true)}</span></span>`;

  // Updates an odometer in place so the digits roll to their new values.
  function setOdometer(el, text) {
    const shape = text.replace(/\d/g, '0');
    if (el.dataset.shape !== shape) {
      el.dataset.shape = shape;
      el.innerHTML = `<span class="sr-only"></span><span class="odo-cells" aria-hidden="true">${odoCells(text, false)}</span>`;
      el.getBoundingClientRect(); // commit the zero position so the digits roll in
    }
    el.firstElementChild.textContent = text;
    const digits = text.replace(/\D/g, '');
    $$('.odo-strip', el).forEach((strip, i) => strip.style.setProperty('--d', digits[i]));
  }

  // ---------------------------------------------------------------------------
  // Saved cars and compare list (kept in this browser only)
  // ---------------------------------------------------------------------------

  const saved = new Set(store.get('saved-cars', []));
  let compare = store.get('compare-cars', []).filter(byId).slice(0, 3);
  const MAX_COMPARE = 3;

  // ---------------------------------------------------------------------------
  // Filters
  // ---------------------------------------------------------------------------

  const BODY_ORDER = ['SUV', 'Sedan', 'Truck', 'Coupe', 'Hatchback', 'Convertible', 'Wagon', 'Van'];
  const bodyRank = (body) => (BODY_ORDER.includes(body) ? BODY_ORDER.indexOf(body) : BODY_ORDER.length);
  const bodies = [...new Set(cars.map((car) => car.body))].sort((a, b) => bodyRank(a) - bodyRank(b));
  const makes = [...new Set(cars.map((car) => car.make))].sort();
  const collectionById = new Map(D.collections.map((c) => [c.id, c]));

  const DEFAULT_STATE = {
    search: '',
    body: 'All',
    make: 'All',
    budget: null,
    collection: null,
    sort: 'featured',
    savedOnly: false,
  };
  const state = { ...DEFAULT_STATE };
  let currentList = cars.slice();

  const els = {
    grid: $('#car-grid'),
    count: $('#result-count'),
    clear: $('#clear-filters'),
    empty: $('#empty-state'),
    chips: $('#f-body'),
    search: $('#f-search'),
    make: $('#f-make'),
    budget: $('#f-budget'),
    sort: $('#f-sort'),
    quick: $('#quick-search'),
    qBody: $('#q-body'),
    qMake: $('#q-make'),
    qBudget: $('#q-budget'),
    qCount: $('#q-count'),
  };

  // Budgets are stored as "price:30000" or "monthly:450" in the selects.
  const budgetValue = (budget) => (budget ? `${budget.kind}:${budget.max}` : '');
  const parseBudget = (value) => {
    if (!value) return null;
    const [kind, max] = value.split(':');
    return { kind, max: Number(max) };
  };
  const budgetLabel = (budget) =>
    budget.kind === 'monthly' ? `Up to ${formatMoney(budget.max)}/mo` : `Up to ${formatMoney(budget.max)}`;

  function fillBudgetSelect(select) {
    select.add(new Option('Any budget', ''));
    [
      ['price', 'Total price'],
      ['monthly', 'Monthly payment'],
    ].forEach(([kind, label]) => {
      const group = document.createElement('optgroup');
      group.label = label;
      group.dataset.kind = kind;
      D.budgets[kind].forEach((max) => group.append(new Option(budgetLabel({ kind, max }), budgetValue({ kind, max }))));
      select.append(group);
    });
  }

  // Adds a budget that isn't one of the presets (for example, from the calculator).
  function ensureBudgetOption(select, budget) {
    if (!budget || [...select.options].some((option) => option.value === budgetValue(budget))) return;
    const group = select.querySelector(`optgroup[data-kind="${budget.kind}"]`);
    const next = [...group.children].find((option) => parseBudget(option.value).max > budget.max);
    group.insertBefore(new Option(budgetLabel(budget), budgetValue(budget)), next || null);
  }

  const addOptions = (select, options) => options.forEach(([value, label]) => select.add(new Option(label, value)));
  addOptions(els.qBody, bodies.map((body) => [body, body]));
  addOptions(els.qMake, makes.map((make) => [make, make]));
  addOptions(els.make, makes.map((make) => [make, make]));
  fillBudgetSelect(els.qBudget);
  fillBudgetSelect(els.budget);

  function filterCars(criteria) {
    const words = (criteria.search || '').toLowerCase().split(/\s+/).filter(Boolean);
    return cars.filter((car) => {
      if (criteria.body !== 'All' && car.body !== criteria.body) return false;
      if (criteria.make !== 'All' && car.make !== criteria.make) return false;
      if (criteria.collection && !(car.tags || []).includes(criteria.collection)) return false;
      if (criteria.savedOnly && !saved.has(car.id)) return false;
      if (criteria.budget) {
        const cost = criteria.budget.kind === 'monthly' ? estimatedMonthly(car.price) : car.price;
        if (cost > criteria.budget.max) return false;
      }
      if (!words.length) return true;
      const haystack = [car.year, car.make, car.model, car.trim, car.body, car.fuel, car.drivetrain, car.exterior, ...car.features]
        .join(' ')
        .toLowerCase();
      return words.every((word) => haystack.includes(word));
    });
  }

  const sorters = {
    featured: () => 0,
    'price-asc': (a, b) => a.price - b.price,
    'price-desc': (a, b) => b.price - a.price,
    mileage: (a, b) => a.mileage - b.mileage,
    year: (a, b) => b.year - a.year,
  };

  const isFiltered = () =>
    Object.keys(DEFAULT_STATE).some((key) => key !== 'sort' && state[key] !== DEFAULT_STATE[key]);

  // Chips: an optional collection chip, body types, then saved cars.
  const addChip = (className, onClick) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = className;
    button.addEventListener('click', onClick);
    els.chips.append(button);
    return button;
  };

  const collectionChip = addChip('chip chip-collection', () => {
    state.collection = null;
    render();
  });

  const chipButtons = new Map();
  ['All', ...bodies].forEach((body) => {
    const count = body === 'All' ? cars.length : cars.filter((car) => car.body === body).length;
    const button = addChip('chip', () => {
      state.body = body;
      render();
    });
    button.innerHTML = `${body === 'All' ? 'All cars' : esc(body)}<span class="chip-count">${count}</span>`;
    chipButtons.set(body, button);
  });

  const savedChip = addChip('chip chip-saved', () => {
    state.savedOnly = !state.savedOnly;
    render();
  });

  function updateChips() {
    chipButtons.forEach((button, body) => button.setAttribute('aria-pressed', String(state.body === body)));
    savedChip.innerHTML = `${icon('i-heart')}Saved<span class="chip-count">${saved.size}</span>`;
    savedChip.setAttribute('aria-pressed', String(state.savedOnly));
    const collection = state.collection && collectionById.get(state.collection);
    collectionChip.hidden = !collection;
    if (collection) {
      collectionChip.innerHTML = `${esc(collection.name)}${icon('i-close')}`;
      collectionChip.setAttribute('aria-label', `Remove filter: ${collection.name}`);
    }
    $$('[data-collection]').forEach((tile) =>
      tile.setAttribute('aria-pressed', String(tile.dataset.collection === state.collection))
    );
  }

  function syncControls() {
    els.search.value = state.search;
    els.make.value = state.make;
    ensureBudgetOption(els.budget, state.budget);
    els.budget.value = budgetValue(state.budget);
    els.sort.value = state.sort;
  }

  function cardHTML(car, index) {
    const title = carTitle(car);
    const monthlyMode = state.budget?.kind === 'monthly';
    const est = estimatedMonthly(car.price);
    const headline = monthlyMode
      ? `<strong>${formatMoney(est)}<small>/mo</small></strong>`
      : `<strong>${formatMoney(car.price)}</strong>${
          car.wasPrice ? `<s><span class="sr-only">Was </span>${formatMoney(car.wasPrice)}</s>` : ''
        }`;
    const subline = monthlyMode
      ? `${formatMoney(car.price)} · ${finance.downPaymentPct}% down, ${finance.termMonths} mo`
      : `est. ${formatMoney(est)}/mo`;

    return `
      <article class="car-card" style="--i: ${index}">
        <div class="car-media">
          <img src="${esc(car.image)}" alt="${esc(car.alt)}" width="1200" height="800" loading="lazy" decoding="async">
          ${car.badge ? `<span class="badge badge-${slug(car.badge)}">${esc(car.badge)}</span>` : ''}
          <button class="save-btn" type="button" data-save="${esc(car.id)}" aria-pressed="${saved.has(car.id)}" aria-label="Save ${esc(title)}">${icon('i-heart')}</button>
        </div>
        <div class="car-body">
          <h3 class="car-title"><button class="car-open" type="button" data-open="${esc(car.id)}">${esc(title)}</button></h3>
          <p class="car-trim">${esc(car.trim)}</p>
          <ul class="car-specs" aria-label="Key specs">
            <li>${icon('i-gauge')}${formatMiles(car.mileage)}</li>
            <li>${icon('i-gears')}${esc(car.transmission)}</li>
            <li>${icon(car.fuel === 'Electric' ? 'i-bolt' : 'i-fuel')}${esc(car.fuel)}</li>
            <li>${icon('i-wheel')}${esc(car.drivetrain)}</li>
          </ul>
          <div class="car-foot">
            <div>
              <p class="price-line">${headline}</p>
              <span class="monthly">${subline}</span>
            </div>
            <button class="compare-toggle" type="button" data-compare="${esc(car.id)}" aria-pressed="${compare.includes(car.id)}" aria-label="Compare ${esc(title)}"><span class="box" aria-hidden="true"></span>Compare</button>
          </div>
        </div>
      </article>`;
  }

  function render() {
    currentList = filterCars(state).sort(sorters[state.sort]);
    els.grid.innerHTML = currentList.map(cardHTML).join('');
    els.empty.hidden = currentList.length > 0;
    els.count.textContent = isFiltered()
      ? `Showing ${currentList.length} of ${plural(cars.length, 'car')}`
      : `${plural(cars.length, 'car')} in stock`;
    els.clear.hidden = !isFiltered() || currentList.length === 0;
    updateChips();
  }

  const resetFilters = () => {
    Object.assign(state, DEFAULT_STATE);
    syncControls();
    render();
  };

  els.search.addEventListener('input', () => {
    state.search = els.search.value.trim();
    render();
  });
  els.make.addEventListener('change', () => {
    state.make = els.make.value;
    render();
  });
  els.budget.addEventListener('change', () => {
    state.budget = parseBudget(els.budget.value);
    render();
  });
  els.sort.addEventListener('change', () => {
    state.sort = els.sort.value;
    render();
  });
  $('#reset-filters').addEventListener('click', resetFilters);
  els.clear.addEventListener('click', resetFilters);

  function describeFilters() {
    const words = [];
    if (state.make !== 'All') words.push(state.make);
    words.push(state.body === 'All' ? 'car' : state.body === 'SUV' ? 'SUV' : state.body.toLowerCase());
    let text = words.join(' ');
    if (state.collection) text += ` for ${collectionById.get(state.collection).name.toLowerCase()}`;
    if (state.budget) text += `, ${budgetLabel(state.budget).toLowerCase()}`;
    if (state.search) text += `, with "${state.search}"`;
    return `${/^(SUV|[aeiou])/i.test(text) ? 'an' : 'a'} ${text}`;
  }

  $('#find-for-me').addEventListener('click', () => {
    prefillContact({
      topic: 'General question',
      message: `I'm looking for ${describeFilters()}. Please let me know if one comes in.`,
    });
  });

  els.grid.addEventListener('click', (e) => {
    const saveButton = e.target.closest('[data-save]');
    if (saveButton) {
      const id = saveButton.dataset.save;
      saved.has(id) ? saved.delete(id) : saved.add(id);
      store.set('saved-cars', [...saved]);
      if (state.savedOnly) {
        render();
      } else {
        saveButton.setAttribute('aria-pressed', String(saved.has(id)));
        updateChips();
      }
      return;
    }
    const compareButton = e.target.closest('[data-compare]');
    if (compareButton) {
      toggleCompare(compareButton.dataset.compare);
      return;
    }
    const openButton = e.target.closest('[data-open]');
    if (openButton) openCar(openButton.dataset.open);
  });

  // Quick search in the hero: preview the match count, then apply it to the inventory.
  const quickCriteria = () => ({
    ...DEFAULT_STATE,
    body: els.qBody.value,
    make: els.qMake.value,
    budget: parseBudget(els.qBudget.value),
  });

  const updateQuickCount = () => {
    const n = filterCars(quickCriteria()).length;
    els.qCount.textContent = n === 0 ? 'No matches yet' : `Show ${plural(n, 'car')}`;
  };

  els.quick.addEventListener('change', updateQuickCount);
  els.quick.addEventListener('submit', (e) => {
    e.preventDefault();
    Object.assign(state, quickCriteria());
    syncControls();
    render();
    $('#inventory').scrollIntoView();
  });

  // ---------------------------------------------------------------------------
  // Shop by lifestyle
  // ---------------------------------------------------------------------------

  const collectionGrid = $('#collection-grid');
  collectionGrid.innerHTML = D.collections
    .map((collection) => {
      const members = cars.filter((car) => (car.tags || []).includes(collection.id));
      if (!members.length) return '';
      const from = Math.min(...members.map((car) => car.price));
      return `
        <button class="collection" type="button" data-collection="${esc(collection.id)}" aria-pressed="false">
          <img src="${esc(collection.image)}" alt="" loading="lazy" decoding="async" style="object-position: ${esc(collection.focus || 'center')}">
          <strong>${esc(collection.name)}</strong>
          <span class="collection-blurb">${esc(collection.blurb)}</span>
          <span class="collection-meta"><span>${plural(members.length, 'car')} · from ${formatMoney(from)}</span>${icon('i-arrow')}</span>
        </button>`;
    })
    .join('');

  collectionGrid.addEventListener('click', (e) => {
    const tile = e.target.closest('[data-collection]');
    if (!tile) return;
    state.collection = state.collection === tile.dataset.collection ? null : tile.dataset.collection;
    render();
    if (state.collection) $('#inventory').scrollIntoView();
  });

  // ---------------------------------------------------------------------------
  // Compare
  // ---------------------------------------------------------------------------

  const tray = $('#compare-tray');
  const trayItems = $('#tray-items');
  const trayCompare = $('#tray-compare');
  const trayLabel = $('#tray-label');

  function toggleCompare(id) {
    if (compare.includes(id)) {
      compare = compare.filter((x) => x !== id);
    } else if (compare.length >= MAX_COMPARE) {
      toast(`You can compare up to ${MAX_COMPARE} cars. Remove one first.`);
      return false;
    } else {
      compare.push(id);
    }
    store.set('compare-cars', compare);
    updateCompareUI();
    return true;
  }

  function updateCompareUI() {
    $$('[data-compare]').forEach((button) =>
      button.setAttribute('aria-pressed', String(compare.includes(button.dataset.compare)))
    );
    tray.hidden = compare.length === 0;
    trayItems.innerHTML = compare
      .map((id) => {
        const car = byId(id);
        return `
          <li class="tray-item">
            <img src="${esc(car.image)}" alt="">
            <span>${esc(`${car.make} ${car.model}`)}</span>
            <button class="tray-remove" type="button" data-remove="${esc(car.id)}" aria-label="Remove ${esc(carTitle(car))} from compare">${icon('i-close')}</button>
          </li>`;
      })
      .join('');
    trayCompare.disabled = compare.length < 2;
    trayLabel.textContent = compare.length < 2 ? 'Add one more' : `Compare ${compare.length}`;
    syncStickerCompare();
    updateActionBar();
  }

  trayItems.addEventListener('click', (e) => {
    const remove = e.target.closest('[data-remove]');
    if (remove) toggleCompare(remove.dataset.remove);
  });
  $('#tray-clear').addEventListener('click', () => {
    compare = [];
    store.set('compare-cars', compare);
    updateCompareUI();
  });
  trayCompare.addEventListener('click', openCompare);

  const compareDialog = $('#compare-dialog');

  // Marks the best value in a row, unless every car ties.
  function bestFlags(values, better) {
    const target = better === 'low' ? Math.min(...values) : Math.max(...values);
    const winners = values.filter((v) => v === target).length;
    return values.map((v) => v === target && winners < values.length);
  }

  function openCompare() {
    const list = compare.map(byId);
    if (list.length < 2) return;
    const allGas = list.every((car) => car.mpg);
    const allElectric = list.every((car) => car.range);
    const pick = (fn) => list.map(fn);

    const rows = [
      ['Price', pick((c) => formatMoney(c.price)), bestFlags(pick((c) => c.price), 'low')],
      ['Est. payment', pick((c) => `${formatMoney(estimatedMonthly(c.price))}/mo`), bestFlags(pick((c) => c.price), 'low')],
      ['Mileage', pick((c) => formatMiles(c.mileage)), bestFlags(pick((c) => c.mileage), 'low')],
      ['Year', pick((c) => c.year), bestFlags(pick((c) => c.year), 'high')],
      ['Body', pick((c) => c.body)],
      ['Engine', pick((c) => c.engine)],
      ['Drivetrain', pick((c) => c.drivetrain)],
      [
        'Fuel economy',
        pick(economyText),
        allGas ? bestFlags(pick((c) => c.mpg.highway), 'high') : allElectric ? bestFlags(pick((c) => c.range), 'high') : null,
      ],
      ['Owners', pick((c) => c.owners), bestFlags(pick((c) => c.owners), 'low')],
      [
        'Highlights',
        pick((c) => `<ul class="check-list">${c.features.map((f) => `<li>${icon('i-check')}${esc(f)}</li>`).join('')}</ul>`),
        null,
        true,
      ],
    ];

    compareDialog.innerHTML = `
      <button class="dialog-close" type="button" aria-label="Close" data-close>${icon('i-close')}</button>
      <div class="compare-inner">
        <p class="kicker">Compare</p>
        <h2 id="compare-title">Side by side</h2>
        <div class="table-scroll">
          <table class="compare-table">
            <thead>
              <tr>
                <th scope="col"><span class="sr-only">Spec</span></th>
                ${list
                  .map(
                    (car) => `
                  <th scope="col">
                    <div class="compare-car">
                      <img src="${esc(car.image)}" alt="${esc(car.alt)}" loading="lazy">
                      <strong>${esc(carTitle(car))}</strong>
                      <span>${esc(car.trim)}</span>
                      <button class="link-btn" type="button" data-open="${esc(car.id)}">View window sticker</button>
                    </div>
                  </th>`
                  )
                  .join('')}
              </tr>
            </thead>
            <tbody>
              ${rows
                .map(
                  ([label, values, best, isHTML]) => `
                <tr>
                  <th scope="row" class="label">${label}</th>
                  ${values
                    .map(
                      (value, i) =>
                        `<td${best?.[i] ? ' class="is-best"' : ''}>${isHTML ? value : esc(value)}${
                          best?.[i] ? '<span class="best">Best</span>' : ''
                        }</td>`
                    )
                    .join('')}
                </tr>`
                )
                .join('')}
            </tbody>
          </table>
        </div>
      </div>`;
    compareDialog.showModal();
  }

  compareDialog.addEventListener('click', (e) => {
    if (e.target === compareDialog || e.target.closest('[data-close]')) {
      compareDialog.close();
      return;
    }
    const open = e.target.closest('[data-open]');
    if (open) {
      compareDialog.close();
      openCar(open.dataset.open, { list: compare.map(byId) });
    }
  });

  // ---------------------------------------------------------------------------
  // Window sticker (vehicle details)
  // ---------------------------------------------------------------------------

  const sticker = $('#car-dialog');
  let navList = [];

  const setHash = (id) => {
    try {
      history.replaceState(null, '', `#${id}`);
    } catch (e) {}
  };
  const clearHash = () => {
    try {
      history.replaceState(null, '', location.pathname + location.search);
    } catch (e) {}
  };

  // Clears the link at once; the dialog's own close event follows a moment later.
  const closeSticker = () => {
    sticker.close();
    clearHash();
  };

  function openCar(id, { list } = {}) {
    const car = byId(id);
    if (!car) return;
    const source = list || (currentList.some((c) => c.id === id) ? currentList : cars);
    navList = source.map((c) => c.id);
    renderSticker(car);
    if (!sticker.open) sticker.showModal();
    setHash(car.id);
  }

  function renderSticker(car) {
    const index = navList.indexOf(car.id);
    const est = estimatedMonthly(car.price);
    const spec = (label, value) => `<div><dt>${label}</dt><dd>${esc(value)}</dd></div>`;
    const economy = car.range
      ? `<div class="economy"><div class="economy-num"><strong>${number.format(car.range)}</strong><span>${distanceUnit} range (EPA)</span></div></div>`
      : `<div class="economy">
           <div class="economy-num"><strong>${car.mpg.city}</strong><span>City mpg</span></div>
           <span class="economy-divider" aria-hidden="true"></span>
           <div class="economy-num"><strong>${car.mpg.highway}</strong><span>Highway mpg</span></div>
         </div>`;
    const odometer = String(car.mileage).padStart(6, '0');

    sticker.dataset.car = car.id;
    sticker.innerHTML = `
      <button class="dialog-close" type="button" aria-label="Close" data-close>${icon('i-close')}</button>
      <div class="sticker-photo">
        <img src="${esc(car.image)}" alt="${esc(car.alt)}" width="1200" height="800">
        ${car.badge ? `<span class="badge badge-${slug(car.badge)}">${esc(car.badge)}</span>` : ''}
      </div>
      <div class="sticker">
        <p class="sticker-band"><span><span class="band-name">${esc(D.name)} · </span>Vehicle information</span></p>
        <div class="sticker-head">
          <div>
            <h2 id="dialog-title">${esc(carTitle(car))}</h2>
            <p class="car-trim">${esc(car.trim)} · ${esc(car.exterior)}</p>
          </div>
          <span class="stock-tag">Stock ${esc(car.stock)}</span>
        </div>
        <div class="sticker-grid">
          <div class="sticker-cell">
            <span class="label">Price</span>
            <p class="sticker-figure">${formatMoney(car.price)}${
              car.wasPrice ? `<s><span class="sr-only">Was </span>${formatMoney(car.wasPrice)}</s>` : ''
            }</p>
            <p class="sticker-sub">Plus tax, title and registration</p>
          </div>
          <div class="sticker-cell">
            <span class="label">Est. payment</span>
            <p class="sticker-figure">${formatMoney(est)}<small>/mo</small></p>
            <p class="sticker-sub">${finance.downPaymentPct}% down · ${finance.termMonths} months · ${finance.apr}% APR</p>
          </div>
          <div class="sticker-cell">
            <span class="label">${car.range ? 'Range' : 'Fuel economy'}</span>
            ${economy}
          </div>
          <div class="sticker-cell">
            <span class="label">Odometer</span>
            <p class="odometer">${odometerHTML(odometer)}<span class="odometer-unit">${distanceUnit}</span></p>
          </div>
        </div>
        <div class="sticker-section">
          <p class="sticker-desc">${esc(car.description)}</p>
        </div>
        <div class="sticker-section sticker-cols">
          <div>
            <h3 class="label">Specifications</h3>
            <dl class="spec-list">
              ${spec('Engine', car.engine)}
              ${spec('Transmission', car.transmission)}
              ${spec('Drivetrain', car.drivetrain)}
              ${spec('Body', car.body)}
              ${spec('Exterior', car.exterior)}
              ${spec('Interior', car.interior)}
            </dl>
          </div>
          <div>
            <h3 class="label">Highlights</h3>
            <ul class="check-list">${car.features.map((f) => `<li>${icon('i-check')}${esc(f)}</li>`).join('')}</ul>
          </div>
        </div>
        <div class="sticker-section">
          <h3 class="label">History report</h3>
          <ul class="history-list">
            <li>${icon('i-check')}${plural(car.owners, 'owner')}</li>
            ${(car.history || []).map((item) => `<li>${icon('i-check')}${esc(item)}</li>`).join('')}
          </ul>
        </div>
        <div class="sticker-actions">
          <button class="btn btn-lane" type="button" data-action="test-drive">${icon('i-calendar')} Book a test drive</button>
          <button class="btn btn-ghost" type="button" data-action="calculate">Calculate payment</button>
          <button class="btn btn-ghost" type="button" data-action="compare" aria-pressed="false">${icon('i-compare')} <span>Compare</span></button>
          <button class="btn btn-ghost" type="button" data-action="share">${icon('i-link')} Copy link</button>
        </div>
        <input class="share-field" type="text" readonly hidden aria-label="Link to this car">
        <div class="sticker-nav">
          <button class="btn btn-ghost btn-small" type="button" data-action="prev" aria-label="Previous car">${icon('i-left')} Prev</button>
          <span class="label">${index + 1} of ${navList.length}</span>
          <button class="btn btn-ghost btn-small" type="button" data-action="next" aria-label="Next car">Next ${icon('i-right')}</button>
        </div>
      </div>`;
    syncStickerCompare();
  }

  function syncStickerCompare() {
    const button = sticker.open && sticker.querySelector('[data-action="compare"]');
    if (!button) return;
    const inList = compare.includes(sticker.dataset.car);
    button.setAttribute('aria-pressed', String(inList));
    button.querySelector('span').textContent = inList ? 'Added to compare' : 'Compare';
  }

  function stepSticker(delta) {
    if (navList.length < 2) return;
    const i = navList.indexOf(sticker.dataset.car);
    const id = navList[(i + delta + navList.length) % navList.length];
    renderSticker(byId(id));
    setHash(id);
    sticker.scrollTop = 0;
    sticker.querySelector(`[data-action="${delta < 0 ? 'prev' : 'next'}"]`).focus();
  }

  function shareCar(car) {
    const url = `${(D.siteUrl || location.href).split('#')[0]}#${car.id}`;
    const field = sticker.querySelector('.share-field');
    const fallback = () => {
      field.hidden = false;
      field.value = url;
      field.focus();
      field.select();
      toast('Copy the link from the box below the buttons');
    };
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(url).then(() => toast('Link copied'), fallback);
    } else {
      fallback();
    }
  }

  sticker.addEventListener('click', (e) => {
    // A click on the backdrop lands on the dialog element itself.
    if (e.target === sticker || e.target.closest('[data-close]')) {
      closeSticker();
      return;
    }
    const action = e.target.closest('[data-action]')?.dataset.action;
    const car = byId(sticker.dataset.car);
    if (!action || !car) return;
    if (action === 'test-drive') {
      closeSticker();
      prefillContact({ topic: 'Test drive', carId: car.id });
    } else if (action === 'calculate') {
      closeSticker();
      setMode('payment');
      setCalculatorPrice(car.price);
      $('#financing').scrollIntoView();
    } else if (action === 'compare') {
      toggleCompare(car.id);
    } else if (action === 'share') {
      shareCar(car);
    } else if (action === 'prev' || action === 'next') {
      stepSticker(action === 'prev' ? -1 : 1);
    }
  });

  sticker.addEventListener('keydown', (e) => {
    if (e.target.matches('input, textarea, select')) return;
    if (e.key === 'ArrowLeft') stepSticker(-1);
    if (e.key === 'ArrowRight') stepSticker(1);
  });

  sticker.addEventListener('close', clearHash);

  // A link ending in #<car id> opens that car's window sticker.
  const openFromHash = () => {
    const id = decodeURIComponent(location.hash.slice(1));
    if (byId(id)) openCar(id);
  };
  window.addEventListener('hashchange', openFromHash);

  // ---------------------------------------------------------------------------
  // Payment calculator
  // ---------------------------------------------------------------------------

  const calculator = $('#calculator');
  const calc = {
    price: $('#c-price'),
    budget: $('#c-budget'),
    down: $('#c-down'),
    trade: $('#c-trade'),
    apr: $('#c-apr'),
  };
  const out = {
    label: $('#c-label'),
    figure: $('#c-figure'),
    suffix: $('#c-suffix'),
    principal: $('#c-split-principal'),
    interest: $('#c-split-interest'),
    financed: $('#c-financed'),
    totalInterest: $('#c-interest'),
    total: $('#c-total'),
    shop: $('#c-shop'),
  };
  const parseAmount = (input) => Number(input.value.replace(/[^\d.]/g, '')) || 0;
  let mode = 'payment';
  let affordable = 0;

  function updateCalculator() {
    const down = parseAmount(calc.down);
    const trade = parseAmount(calc.trade);
    const apr = Math.min(parseAmount(calc.apr), 40);
    const term = Number(calculator.querySelector('[name="term"]:checked').value);
    let financed;
    let monthly;
    let price;

    if (mode === 'payment') {
      price = parseAmount(calc.price);
      financed = Math.max(price - down - trade, 0);
      monthly = monthlyPayment(financed, apr, term);
    } else {
      monthly = parseAmount(calc.budget);
      financed = principalFor(monthly, apr, term);
      price = financed + down + trade;
    }

    const totalPaid = monthly * term;
    const interest = Math.max(totalPaid - financed, 0);
    const principalShare = totalPaid > 0 ? (financed / totalPaid) * 100 : 100;

    if (mode === 'payment') {
      out.label.textContent = 'Estimated monthly payment';
      setOdometer(out.figure, formatMoney(monthly));
      out.suffix.hidden = false;
      out.shop.hidden = true;
    } else {
      affordable = Math.floor(price / 100) * 100;
      out.label.textContent = 'You could afford up to';
      setOdometer(out.figure, formatMoney(affordable));
      out.suffix.hidden = true;
      out.shop.hidden = affordable <= 0;
      out.shop.firstChild.textContent = `Show cars up to ${formatMoney(affordable)} `;
    }

    out.principal.style.flexBasis = `${principalShare}%`;
    out.interest.style.flexBasis = `${100 - principalShare}%`;
    out.financed.textContent = formatMoney(financed);
    out.totalInterest.textContent = formatMoney(interest);
    out.total.textContent = formatMoney(totalPaid + Math.min(down + trade, price));
  }

  function setMode(next) {
    mode = next;
    $(`#mode-${next}`).checked = true;
    $$('[data-mode]', calculator).forEach((field) => {
      field.hidden = field.dataset.mode !== next;
    });
    updateCalculator();
  }

  function setCalculatorPrice(price) {
    calc.price.value = number.format(price);
    calc.down.value = number.format(Math.round((price * finance.downPaymentPct) / 100));
    updateCalculator();
  }

  // Add thousands separators once the visitor leaves a field (not while typing).
  [calc.price, calc.budget, calc.down, calc.trade].forEach((input) => {
    input.addEventListener('blur', () => {
      input.value = number.format(parseAmount(input));
    });
  });

  calculator.addEventListener('input', (e) => {
    if (e.target.name === 'mode') setMode(e.target.value);
    else updateCalculator();
  });
  calculator.addEventListener('submit', (e) => e.preventDefault());

  out.shop.addEventListener('click', () => {
    state.budget = { kind: 'price', max: affordable };
    state.collection = null;
    syncControls();
    render();
    $('#inventory').scrollIntoView();
  });

  calc.apr.value = finance.apr;
  const defaultTerm = calculator.querySelector(`[name="term"][value="${finance.termMonths}"]`);
  if (defaultTerm) defaultTerm.checked = true;

  // ---------------------------------------------------------------------------
  // Opening hours (shared by "Open now" and the test-drive time picker)
  // ---------------------------------------------------------------------------

  const toMinutes = (time) => {
    const [h, m] = time.split(':').map(Number);
    return h * 60 + m;
  };
  const hours = new Map(
    $$('#hours tr').map((row) => [
      Number(row.dataset.day),
      row.dataset.open && row.dataset.close ? { open: toMinutes(row.dataset.open), close: toMinutes(row.dataset.close) } : null,
    ])
  );

  (function updateOpenStatus() {
    const now = new Date();
    const row = $(`#hours tr[data-day="${now.getDay()}"]`);
    if (!row) return;
    row.classList.add('is-today');
    const today = hours.get(now.getDay());
    const minutes = now.getHours() * 60 + now.getMinutes();
    const isOpen = Boolean(today) && minutes >= today.open && minutes < today.close;
    const status = $('#open-status');
    status.hidden = false;
    status.textContent = isOpen ? 'Open now' : 'Closed now';
    status.classList.toggle('is-closed', !isOpen);
    $('#today-hours').textContent = today ? `Open today ${row.querySelector('td').textContent}` : 'Closed today';
  })();

  // ---------------------------------------------------------------------------
  // Contact form, test-drive times and trade-in details
  // ---------------------------------------------------------------------------

  const form = $('#contact-form');
  const note = $('#form-note');
  const topicSelect = $('#topic');
  const vehicleSelect = $('#vehicle');
  const nameInput = $('#name');
  const messageInput = $('#message');
  const slotPicker = $('#slot-picker');
  const slotDaysRow = $('#slot-days');
  const slotTimesRow = $('#slot-times');

  addOptions(vehicleSelect, cars.map((car) => [car.id, `${carTitle(car)} · ${formatMoney(car.price)}`]));

  const weekdayFormat = new Intl.DateTimeFormat(locale, { weekday: 'short' });
  const longDateFormat = new Intl.DateTimeFormat(locale, { weekday: 'long', month: 'long', day: 'numeric' });
  const timeFormat = new Intl.DateTimeFormat(locale, { hour: 'numeric', minute: '2-digit' });
  const atMinutes = (date, m) => new Date(date.getFullYear(), date.getMonth(), date.getDate(), Math.floor(m / 60), m % 60);

  // Upcoming open days with bookable start times, skipping times that have passed today.
  const slotDays = (() => {
    const now = new Date();
    const nowMinutes = now.getHours() * 60 + now.getMinutes();
    const { slotMinutes, daysAhead } = D.testDrive;
    const days = [];
    for (let offset = 0; days.length < daysAhead && offset < 21; offset++) {
      const date = new Date(now.getFullYear(), now.getMonth(), now.getDate() + offset);
      const open = hours.get(date.getDay());
      if (!open) continue;
      const times = [];
      for (let m = open.open; m + slotMinutes <= open.close; m += slotMinutes) {
        if (offset === 0 && m < nowMinutes + 60) continue;
        times.push(m);
      }
      if (times.length) days.push({ date, offset, times });
    }
    return days;
  })();

  slotDaysRow.innerHTML = slotDays
    .map((day, i) => {
      const name = day.offset === 0 ? 'Today' : day.offset === 1 ? 'Tomorrow' : weekdayFormat.format(day.date);
      return `<label class="slot"><input type="radio" name="slot-day" id="slot-day-${i}" value="${i}"><span><small>${name}</small>${day.date.getDate()}</span></label>`;
    })
    .join('');
  slotTimesRow.hidden = true;

  slotDaysRow.addEventListener('change', (e) => {
    const day = slotDays[Number(e.target.value)];
    slotTimesRow.innerHTML = day.times
      .map(
        (m, j) =>
          `<label class="slot"><input type="radio" name="slot-time" id="slot-time-${j}" value="${m}"><span>${timeFormat.format(atMinutes(day.date, m))}</span></label>`
      )
      .join('');
    slotTimesRow.hidden = false;
  });

  function selectedSlot() {
    const dayInput = slotDaysRow.querySelector('input:checked');
    if (!dayInput) return '';
    const day = slotDays[Number(dayInput.value)];
    const timeInput = slotTimesRow.querySelector('input:checked');
    const date = longDateFormat.format(day.date);
    return timeInput ? `${date} at ${timeFormat.format(atMinutes(day.date, Number(timeInput.value)))}` : `${date}, any time`;
  }

  const updateSlotPicker = () => {
    slotPicker.hidden = topicSelect.value !== 'Test drive' || slotDays.length === 0;
  };
  topicSelect.addEventListener('change', updateSlotPicker);
  updateSlotPicker();

  function prefillContact({ topic, carId, message }) {
    if (topic) {
      topicSelect.value = topic;
      updateSlotPicker();
    }
    if (carId !== undefined) vehicleSelect.value = carId || '';
    if (message) messageInput.value = message;
    $('#contact').scrollIntoView();
    nameInput.focus({ preventScroll: true });
  }

  document.querySelectorAll('[data-topic]').forEach((link) => {
    link.addEventListener('click', () => {
      topicSelect.value = link.dataset.topic;
      updateSlotPicker();
    });
  });

  const setNote = (el, message, type) => {
    el.textContent = message;
    el.className = `form-note${type ? ` is-${type}` : ''}`;
  };

  // Marks empty or invalid required fields and returns the first one, if any.
  function firstInvalid(scope) {
    const required = $$('[required]', scope);
    required.forEach((input) => input.setAttribute('aria-invalid', String(!input.checkValidity() || !input.value.trim())));
    return required.find((input) => input.getAttribute('aria-invalid') === 'true');
  }

  form.addEventListener('submit', (e) => {
    const invalid = firstInvalid(form);
    if (invalid) {
      e.preventDefault();
      setNote(note, 'Please add your name and a valid email address.', 'error');
      invalid.focus();
      return;
    }

    // A real form service is configured: let the browser submit normally.
    if (form.getAttribute('action')) return;

    // Otherwise hand the message to the visitor's email app.
    e.preventDefault();
    const data = new FormData(form);
    const car = byId(data.get('vehicle'));
    const slot = data.get('topic') === 'Test drive' ? selectedSlot() : '';
    const subject = `${data.get('topic')}${car ? `: ${carTitle(car)} (Stock #${car.stock})` : ''}`;
    const lines = [`Name: ${data.get('name')}`, `Email: ${data.get('email')}`];
    if (data.get('phone')) lines.push(`Phone: ${data.get('phone')}`);
    if (car) lines.push(`Vehicle: ${carTitle(car)} ${car.trim}, Stock #${car.stock}`);
    if (slot) lines.push(`Requested time: ${slot}`);
    if (data.get('message')) lines.push('', data.get('message'));

    window.location.href = `mailto:${email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(lines.join('\n'))}`;
    setNote(note, `Your email app should open with the message ready to send. Prefer to talk? Call ${phone}.`, 'success');
  });

  [form, $('#trade-form')].forEach((scope) =>
    scope.addEventListener('input', (e) => {
      if (e.target.getAttribute('aria-invalid') === 'true' && e.target.checkValidity() && e.target.value.trim()) {
        e.target.setAttribute('aria-invalid', 'false');
      }
    })
  );

  // Trade-in: collect the car's details, then carry them into the contact form.
  const tradeForm = $('#trade-form');
  const tradeNote = $('#trade-note');
  const yearSelect = $('#t-year');
  const thisYear = new Date().getFullYear();
  for (let y = thisYear + 1; y >= thisYear - 25; y--) yearSelect.add(new Option(y, y));
  yearSelect.add(new Option('Older', 'Older'));
  yearSelect.value = String(thisYear - 5);

  tradeForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const mileage = $('#t-mileage');
    if (!/\d/.test(mileage.value)) mileage.value = '';
    const invalid = firstInvalid(tradeForm);
    if (invalid) {
      setNote(tradeNote, 'Add the make, model and mileage so we can price your car.', 'error');
      invalid.focus();
      return;
    }
    setNote(tradeNote, '');
    const data = new FormData(tradeForm);
    const miles = Number(String(data.get('mileage')).replace(/\D/g, ''));
    const year = data.get('year') === 'Older' ? 'older' : data.get('year');
    prefillContact({
      topic: 'Trade-in',
      message: `I'd like an offer for my ${year} ${data.get('make').trim()} ${data.get('model').trim()} with ${formatMiles(miles)}, in ${data.get('condition').toLowerCase()} condition.`,
    });
  });

  // ---------------------------------------------------------------------------
  // Header, phone action bar and hero stats
  // ---------------------------------------------------------------------------

  const navToggle = $('.nav-toggle');
  const navLinks = $('#nav-links');
  const setNavOpen = (open) => {
    navToggle.setAttribute('aria-expanded', String(open));
    navLinks.classList.toggle('open', open);
  };

  navToggle.addEventListener('click', () => setNavOpen(navToggle.getAttribute('aria-expanded') !== 'true'));
  navLinks.addEventListener('click', (e) => {
    if (e.target.closest('a')) setNavOpen(false);
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') setNavOpen(false);
  });

  const links = $$('a[href^="#"]', navLinks);
  const sectionObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        links.forEach((link) => {
          if (link.getAttribute('href') === `#${entry.target.id}`) {
            link.setAttribute('aria-current', 'true');
          } else {
            link.removeAttribute('aria-current');
          }
        });
      });
    },
    { rootMargin: '-45% 0px -50% 0px' }
  );
  $$('main section[id]').forEach((section) => sectionObserver.observe(section));

  // The phone action bar steps aside for the contact form and the compare tray.
  const actionBar = $('#action-bar');
  let contactInView = false;
  function updateActionBar() {
    actionBar.classList.toggle('is-hidden', contactInView || compare.length > 0);
  }
  new IntersectionObserver(
    ([entry]) => {
      contactInView = entry.isIntersecting;
      updateActionBar();
    },
    { threshold: 0.1 }
  ).observe($('#contact'));

  const averageMiles = Math.round(cars.reduce((sum, car) => sum + car.mileage, 0) / cars.length / 100) * 100;
  $('#stat-count').textContent = plural(cars.length, 'car');
  $('#stat-from').textContent = formatMoney(Math.min(...cars.map((car) => car.price)));
  $('#stat-miles').textContent = formatMiles(averageMiles);
  $('#year').textContent = new Date().getFullYear();

  render();
  updateQuickCount();
  updateCompareUI();
  setMode('payment');
  openFromHash();
})();
