(() => {
  const { locale, currency, distanceUnit, email, finance } = window.DEALER;
  const cars = window.INVENTORY;
  const $ = (selector, root = document) => root.querySelector(selector);

  const money = new Intl.NumberFormat(locale, { style: 'currency', currency, maximumFractionDigits: 0 });
  const number = new Intl.NumberFormat(locale);
  const formatMoney = (amount) => money.format(Math.round(amount));
  const carTitle = (car) => `${car.year} ${car.make} ${car.model}`;
  const slug = (text) => text.toLowerCase().replace(/[^a-z0-9]+/g, '-');
  const icon = (id) => `<svg class="icon" aria-hidden="true"><use href="#${id}"/></svg>`;
  const esc = (value) =>
    String(value).replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch]);

  function monthlyPayment(principal, apr, months) {
    if (principal <= 0 || months <= 0) return 0;
    const rate = apr / 100 / 12;
    if (rate === 0) return principal / months;
    return (principal * rate) / (1 - Math.pow(1 + rate, -months));
  }

  const estimatedMonthly = (price) =>
    monthlyPayment(price * (1 - finance.downPaymentPct / 100), finance.apr, finance.termMonths);

  // ---------------------------------------------------------------------------
  // Saved cars (kept in this browser only)
  // ---------------------------------------------------------------------------

  const SAVED_KEY = 'saved-cars';
  let saved = new Set();
  try {
    saved = new Set(JSON.parse(localStorage.getItem(SAVED_KEY)) || []);
  } catch (e) {}

  const persistSaved = () => {
    try {
      localStorage.setItem(SAVED_KEY, JSON.stringify([...saved]));
    } catch (e) {}
  };

  // ---------------------------------------------------------------------------
  // Filters
  // ---------------------------------------------------------------------------

  const BODY_ORDER = ['SUV', 'Sedan', 'Truck', 'Coupe', 'Hatchback', 'Convertible', 'Wagon', 'Van'];
  const bodyRank = (body) => (BODY_ORDER.includes(body) ? BODY_ORDER.indexOf(body) : BODY_ORDER.length);
  const bodies = [...new Set(cars.map((car) => car.body))].sort((a, b) => bodyRank(a) - bodyRank(b));
  const makes = [...new Set(cars.map((car) => car.make))].sort();
  const PRICE_STEPS = [25000, 30000, 40000, 60000, 100000];

  const DEFAULT_STATE = { search: '', body: 'All', make: 'All', maxPrice: Infinity, sort: 'featured', savedOnly: false };
  const state = { ...DEFAULT_STATE };

  const els = {
    grid: $('#car-grid'),
    count: $('#result-count'),
    clear: $('#clear-filters'),
    empty: $('#empty-state'),
    chips: $('#f-body'),
    search: $('#f-search'),
    make: $('#f-make'),
    price: $('#f-price'),
    sort: $('#f-sort'),
    quick: $('#quick-search'),
    qBody: $('#q-body'),
    qMake: $('#q-make'),
    qPrice: $('#q-price'),
    qCount: $('#q-count'),
  };

  const addOptions = (select, options) => options.forEach(([value, label]) => select.add(new Option(label, value)));
  addOptions(els.qBody, bodies.map((body) => [body, body]));
  addOptions(els.qMake, makes.map((make) => [make, make]));
  addOptions(els.make, makes.map((make) => [make, make]));
  document.querySelectorAll('.price-select').forEach((select) => {
    addOptions(select, [['', 'Any price'], ...PRICE_STEPS.map((step) => [step, `Up to ${formatMoney(step)}`])]);
  });

  function filterCars(criteria) {
    const words = (criteria.search || '').toLowerCase().split(/\s+/).filter(Boolean);
    return cars.filter((car) => {
      if (criteria.body !== 'All' && car.body !== criteria.body) return false;
      if (criteria.make !== 'All' && car.make !== criteria.make) return false;
      if (car.price > criteria.maxPrice) return false;
      if (criteria.savedOnly && !saved.has(car.id)) return false;
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

  // Body-type chips, built once so focus survives re-filtering.
  const chipButtons = new Map();
  const addChip = (className, onClick) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = className;
    button.addEventListener('click', onClick);
    els.chips.append(button);
    return button;
  };

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

  const updateSavedChip = () => {
    savedChip.innerHTML = `${icon('i-heart')}Saved<span class="chip-count">${saved.size}</span>`;
    savedChip.setAttribute('aria-pressed', String(state.savedOnly));
  };

  function syncControls() {
    els.search.value = state.search;
    els.make.value = state.make;
    els.price.value = Number.isFinite(state.maxPrice) ? state.maxPrice : '';
    els.sort.value = state.sort;
  }

  function cardHTML(car, index) {
    const title = carTitle(car);
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
            <li>${icon('i-gauge')}${number.format(car.mileage)} ${distanceUnit}</li>
            <li>${icon('i-gears')}${esc(car.transmission)}</li>
            <li>${icon(car.fuel === 'Electric' ? 'i-bolt' : 'i-fuel')}${esc(car.fuel)}</li>
            <li>${icon('i-wheel')}${esc(car.drivetrain)}</li>
          </ul>
          <div class="car-foot">
            <div>
              <p class="price-line">
                <strong>${formatMoney(car.price)}</strong>
                ${car.wasPrice ? `<s><span class="sr-only">Was </span>${formatMoney(car.wasPrice)}</s>` : ''}
              </p>
              <span class="monthly">est. ${formatMoney(estimatedMonthly(car.price))}/mo</span>
            </div>
            <span class="car-cta" aria-hidden="true">Details ${icon('i-arrow')}</span>
          </div>
        </div>
      </article>`;
  }

  function render() {
    const list = filterCars(state).sort(sorters[state.sort]);
    els.grid.innerHTML = list.map(cardHTML).join('');
    els.empty.hidden = list.length > 0;
    els.count.textContent =
      list.length === cars.length ? `${cars.length} cars in stock` : `Showing ${list.length} of ${cars.length} cars`;
    els.clear.hidden = list.length === cars.length || list.length === 0;
    chipButtons.forEach((button, body) => button.setAttribute('aria-pressed', String(state.body === body)));
    updateSavedChip();
  }

  els.search.addEventListener('input', () => {
    state.search = els.search.value.trim();
    render();
  });
  els.make.addEventListener('change', () => {
    state.make = els.make.value;
    render();
  });
  els.price.addEventListener('change', () => {
    state.maxPrice = Number(els.price.value) || Infinity;
    render();
  });
  els.sort.addEventListener('change', () => {
    state.sort = els.sort.value;
    render();
  });
  const resetFilters = () => {
    Object.assign(state, DEFAULT_STATE);
    syncControls();
    render();
  };
  $('#reset-filters').addEventListener('click', resetFilters);
  els.clear.addEventListener('click', resetFilters);

  els.grid.addEventListener('click', (e) => {
    const saveButton = e.target.closest('[data-save]');
    if (saveButton) {
      const id = saveButton.dataset.save;
      saved.has(id) ? saved.delete(id) : saved.add(id);
      persistSaved();
      if (state.savedOnly) {
        render();
      } else {
        saveButton.setAttribute('aria-pressed', String(saved.has(id)));
        updateSavedChip();
      }
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
    maxPrice: Number(els.qPrice.value) || Infinity,
  });

  const updateQuickCount = () => {
    const n = filterCars(quickCriteria()).length;
    els.qCount.textContent = n === 0 ? 'No matches' : `Show ${n} ${n === 1 ? 'car' : 'cars'}`;
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
  // Vehicle details dialog
  // ---------------------------------------------------------------------------

  const dialog = $('#car-dialog');
  const spec = (label, value) => `<div><dt>${label}</dt><dd>${esc(value)}</dd></div>`;

  function openCar(id) {
    const car = cars.find((c) => c.id === id);
    if (!car) return;
    dialog.dataset.car = car.id;
    dialog.innerHTML = `
      <button class="dialog-close" type="button" aria-label="Close" data-close>${icon('i-close')}</button>
      <div class="dialog-media">
        <img src="${esc(car.image)}" alt="${esc(car.alt)}" width="1200" height="800">
        ${car.badge ? `<span class="badge badge-${slug(car.badge)}">${esc(car.badge)}</span>` : ''}
      </div>
      <div class="dialog-body">
        <p class="kicker">Stock #${esc(car.stock)}</p>
        <h2 id="dialog-title">${esc(carTitle(car))}</h2>
        <p class="car-trim">${esc(car.trim)}</p>
        <p class="dialog-price">
          <strong>${formatMoney(car.price)}</strong>
          ${car.wasPrice ? `<s><span class="sr-only">Was </span>${formatMoney(car.wasPrice)}</s>` : ''}
          <span>est. ${formatMoney(estimatedMonthly(car.price))}/mo with ${finance.downPaymentPct}% down over ${finance.termMonths} months</span>
        </p>
        <p class="dialog-desc">${esc(car.description)}</p>
        <dl class="spec-grid">
          ${spec('Mileage', `${number.format(car.mileage)} ${distanceUnit}`)}
          ${spec('Body', car.body)}
          ${spec('Engine', car.engine)}
          ${spec('Transmission', car.transmission)}
          ${spec('Drivetrain', car.drivetrain)}
          ${spec(car.fuel === 'Electric' ? 'Range' : 'Fuel economy', car.economy)}
          ${spec('Exterior', car.exterior)}
          ${spec('Interior', car.interior)}
        </dl>
        <h3 class="sub-label">Highlights</h3>
        <ul class="feature-list">
          ${car.features.map((feature) => `<li>${icon('i-check')}${esc(feature)}</li>`).join('')}
        </ul>
        <div class="dialog-actions">
          <button class="btn btn-accent" type="button" data-action="test-drive">Book a test drive</button>
          <button class="btn btn-ghost" type="button" data-action="calculate">Calculate payment</button>
        </div>
      </div>`;
    dialog.showModal();
  }

  dialog.addEventListener('click', (e) => {
    // A click on the backdrop lands on the dialog element itself.
    if (e.target === dialog || e.target.closest('[data-close]')) {
      dialog.close();
      return;
    }
    const action = e.target.closest('[data-action]')?.dataset.action;
    const car = cars.find((c) => c.id === dialog.dataset.car);
    if (!action || !car) return;
    dialog.close();
    if (action === 'test-drive') {
      prefillContact('Test drive', car.id);
    } else if (action === 'calculate') {
      setCalculatorPrice(car.price);
      $('#financing').scrollIntoView();
    }
  });

  // ---------------------------------------------------------------------------
  // Payment calculator
  // ---------------------------------------------------------------------------

  const calculator = $('#calculator');
  const calc = { price: $('#c-price'), down: $('#c-down'), trade: $('#c-trade'), apr: $('#c-apr') };
  const out = { monthly: $('#c-monthly'), financed: $('#c-financed'), interest: $('#c-interest'), total: $('#c-total') };
  const parseAmount = (input) => Number(input.value.replace(/[^\d.]/g, '')) || 0;

  function updateCalculator() {
    const price = parseAmount(calc.price);
    const down = parseAmount(calc.down);
    const trade = parseAmount(calc.trade);
    const apr = Math.min(parseAmount(calc.apr), 40);
    const term = Number(calculator.querySelector('[name="term"]:checked').value);
    const financed = Math.max(price - down - trade, 0);
    const monthly = monthlyPayment(financed, apr, term);
    const totalPaid = monthly * term;

    out.monthly.innerHTML = `${formatMoney(monthly)}<small>/mo</small>`;
    out.financed.textContent = formatMoney(financed);
    out.interest.textContent = formatMoney(totalPaid - financed);
    out.total.textContent = formatMoney(totalPaid + Math.min(down + trade, price));
  }

  function setCalculatorPrice(price) {
    calc.price.value = number.format(price);
    calc.down.value = number.format(Math.round((price * finance.downPaymentPct) / 100));
    updateCalculator();
  }

  // Add thousands separators once the visitor leaves a field (not while typing).
  [calc.price, calc.down, calc.trade].forEach((input) => {
    input.addEventListener('blur', () => {
      input.value = number.format(parseAmount(input));
    });
  });

  calc.apr.value = finance.apr;
  const defaultTerm = calculator.querySelector(`[name="term"][value="${finance.termMonths}"]`);
  if (defaultTerm) defaultTerm.checked = true;
  calculator.addEventListener('input', updateCalculator);
  calculator.addEventListener('submit', (e) => e.preventDefault());
  updateCalculator();

  // ---------------------------------------------------------------------------
  // Contact form
  // ---------------------------------------------------------------------------

  const form = $('#contact-form');
  const note = $('#form-note');
  const topicSelect = $('#topic');
  const vehicleSelect = $('#vehicle');
  const nameInput = $('#name');

  addOptions(vehicleSelect, cars.map((car) => [car.id, `${carTitle(car)} · ${formatMoney(car.price)}`]));

  const today = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  $('#date').min = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;

  function prefillContact(topic, carId) {
    topicSelect.value = topic;
    if (carId) vehicleSelect.value = carId;
    $('#contact').scrollIntoView();
    nameInput.focus({ preventScroll: true });
  }

  document.querySelectorAll('[data-topic]').forEach((link) => {
    link.addEventListener('click', () => {
      topicSelect.value = link.dataset.topic;
    });
  });

  const setNote = (message, type) => {
    note.textContent = message;
    note.className = `form-note${type ? ` is-${type}` : ''}`;
  };

  form.addEventListener('submit', (e) => {
    const required = [...form.querySelectorAll('[required]')];
    required.forEach((input) => input.setAttribute('aria-invalid', String(!input.checkValidity())));
    const firstInvalid = required.find((input) => !input.checkValidity());
    if (firstInvalid) {
      e.preventDefault();
      setNote('Please add your name and a valid email address.', 'error');
      firstInvalid.focus();
      return;
    }

    // A real form service is configured: let the browser submit normally.
    if (form.getAttribute('action')) return;

    // Otherwise hand the message to the visitor's email app.
    e.preventDefault();
    const data = new FormData(form);
    const car = cars.find((c) => c.id === data.get('vehicle'));
    const subject = `${data.get('topic')}${car ? `: ${carTitle(car)} (Stock #${car.stock})` : ''}`;
    const lines = [`Name: ${data.get('name')}`, `Email: ${data.get('email')}`];
    if (data.get('phone')) lines.push(`Phone: ${data.get('phone')}`);
    if (data.get('date')) lines.push(`Preferred date: ${data.get('date')}`);
    if (car) lines.push(`Vehicle: ${carTitle(car)} ${car.trim}, Stock #${car.stock}`);
    if (data.get('message')) lines.push('', data.get('message'));

    window.location.href = `mailto:${email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(lines.join('\n'))}`;
    setNote('Your email app should open with the message ready to send. Prefer to talk? Call (312) 555-0142.', 'success');
  });

  form.addEventListener('input', (e) => {
    if (e.target.getAttribute('aria-invalid') === 'true' && e.target.checkValidity()) {
      e.target.setAttribute('aria-invalid', 'false');
    }
  });

  // ---------------------------------------------------------------------------
  // Opening hours: highlight today and show "Open now" / "Closed now"
  // ---------------------------------------------------------------------------

  (function updateHours() {
    const now = new Date();
    const row = $(`#hours tr[data-day="${now.getDay()}"]`);
    if (!row) return;
    row.classList.add('is-today');

    const toMinutes = (time) => {
      const [h, m] = time.split(':').map(Number);
      return h * 60 + m;
    };
    const { open, close } = row.dataset;
    const minutes = now.getHours() * 60 + now.getMinutes();
    const isOpen = Boolean(open && close) && minutes >= toMinutes(open) && minutes < toMinutes(close);

    const status = $('#open-status');
    status.hidden = false;
    status.textContent = isOpen ? 'Open now' : 'Closed now';
    status.classList.toggle('is-closed', !isOpen);
    $('#today-hours').textContent = open ? `Open today ${row.querySelector('td').textContent}` : 'Closed today';
  })();

  // ---------------------------------------------------------------------------
  // Header: mobile menu and current-section highlight
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

  const links = [...navLinks.querySelectorAll('a[href^="#"]')];
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
  document.querySelectorAll('main section[id]').forEach((section) => sectionObserver.observe(section));

  $('#year').textContent = new Date().getFullYear();

  render();
  updateQuickCount();
})();
