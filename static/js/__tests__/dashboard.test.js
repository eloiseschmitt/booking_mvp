const { initializeDashboard } = require('../dashboard.js');

const buildDom = () => {
  document.body.innerHTML = `
    <div class="kitlast-dashboard-sidebar">
      <button class="kitlast-dashboard-sidebar__toggle" data-section-target="services" aria-expanded="false"></button>
      <nav>
        <a href="#" data-section-target="services">Services</a>
        <a href="#" data-section-target="planning">Planning</a>
      </nav>
      <ul id="services-subnav"></ul>
    </div>
    <div class="kitlast-dashboard-content"
      data-active-section="services"
      data-show-category="false"
      data-show-service="false"
      data-week-offset="0"></div>

    <div class="kitlast-modal" data-category-modal hidden>
      <div class="kitlast-modal__overlay" data-modal-close></div>
      <div class="kitlast-modal__content">
        <input type="text" />
        <button type="button" data-modal-close>close</button>
      </div>
    </div>

    <div class="kitlast-modal" data-service-modal>
      <div class="kitlast-modal__overlay" data-modal-close data-testid="service-overlay"></div>
      <div class="kitlast-modal__content">
        <button type="button" data-modal-close data-testid="service-close">×</button>
        <form>
          <input name="name" />
        </form>
      </div>
    </div>

    <div class="kitlast-modal" data-event-modal hidden>
      <div class="kitlast-modal__overlay" data-modal-close></div>
      <div class="kitlast-modal__content">
        <div data-event-field="date"></div>
        <div data-event-field="time"></div>
        <div data-event-field="title"></div>
        <div data-event-field="service"></div>
        <div data-event-field="category"></div>
        <div data-event-field="status"></div>
        <div data-event-field="created_by"></div>
        <div data-event-field="description"></div>
        <button type="button" data-event-delete></button>
      </div>
    </div>

    <div class="kitlast-modal" data-new-event-modal hidden>
      <div class="kitlast-modal__overlay" data-modal-close></div>
      <div class="kitlast-modal__content">
        <form data-new-event-form>
          <input type="hidden" data-new-event-field="start-input" />
          <div data-new-event-field="date"></div>
          <div data-new-event-field="time"></div>
          <div data-new-event-field="message"></div>
          <select data-new-event-field="service">
            <option value="">Sélectionnez</option>
            <option value="1">Retouche</option>
          </select>
          <select data-new-event-field="client">
            <option value="">Sélectionnez</option>
            <option value="42">Client 1</option>
          </select>
          <button type="submit" data-new-event-submit disabled>Ajouter</button>
        </form>
      </div>
    </div>

    <div class="kitlast-modal" data-client-modal hidden data-testid="client-modal">
      <div class="kitlast-modal__overlay" data-modal-close></div>
      <div class="kitlast-modal__content">
        <form>
          <input type="text" />
          <button type="button" data-modal-close>×</button>
        </form>
      </div>
    </div>

    <button data-open-client-modal data-testid="open-client-modal">Ajouter un client</button>

    <div class="kitlast-planner__columns">
      <div class="kitlast-planner__column" data-planner-column data-planner-date="01/04">
        <div class="kitlast-planner__column-date">01/04</div>
        <div class="kitlast-planner__timeline">
          <div class="kitlast-planner__event"
            data-planner-event
            data-event-label="Lun."
            data-event-date="01/04"
            data-event-time="10:00 – 11:00"
            data-event-title="Marie · Retouche"
            data-event-service="Retouche"
            data-event-category="Couture"
            data-event-description="Desc"
            data-event-status="Confirmé"
            data-event-created-by="Marie"
            data-event-start="2024-04-01T08:00:00.000Z"
            data-event-end="2024-04-01T09:00:00.000Z">
            <span>10:00 – 11:00</span>
          </div>
        </div>
      </div>
      <div class="kitlast-planner__column" data-planner-column data-planner-date="02/04">
        <div class="kitlast-planner__column-date">02/04</div>
        <div class="kitlast-planner__timeline"></div>
      </div>
    </div>
    <button data-planner-action="today"></button>
    <button data-planner-action="day"></button>
    <button data-planner-action="week"></button>
    <button data-planner-nav="prev"></button>
    <button data-planner-nav="next"></button>
    <span data-planner-range></span>
  `;
};

beforeEach(() => {
  document.head.innerHTML = '';
  document.body.innerHTML = '';
  window.requestAnimationFrame = (cb) => cb();
  buildDom();
  initializeDashboard();
});

describe('dashboard.js modals', () => {
  test('close button hides the service modal on first click', () => {
    const serviceModal = document.querySelector('[data-service-modal]');
    const closeButton = document.querySelector('[data-testid="service-close"]');

    expect(serviceModal.hasAttribute('hidden')).toBe(false);
    closeButton.click();
    expect(serviceModal.hasAttribute('hidden')).toBe(true);
  });

  test('clicking overlay hides the service modal', () => {
    const serviceModal = document.querySelector('[data-service-modal]');
    const overlay = document.querySelector('[data-testid="service-overlay"]');

    overlay.click();
    expect(serviceModal.hasAttribute('hidden')).toBe(true);
  });

  test('client modal opens from button click', () => {
    const clientModal = document.querySelector('[data-testid="client-modal"]');
    const openButton = document.querySelector('[data-open-client-modal]');

    expect(clientModal.hasAttribute('hidden')).toBe(true);
    openButton.click();
    expect(clientModal.hasAttribute('hidden')).toBe(false);
  });
});

describe('dashboard.js planner interactions', () => {
  test('clicking an event fills and opens the detail modal', () => {
    const eventModal = document.querySelector('[data-event-modal]');
    const plannerEvent = document.querySelector('[data-planner-event]');
    expect(eventModal.hasAttribute('hidden')).toBe(true);

    plannerEvent.click();

    expect(eventModal.hasAttribute('hidden')).toBe(false);
    expect(document.querySelector('[data-event-field="service"]').textContent).toBe('Retouche');
    expect(document.querySelector('[data-event-field="title"]').textContent).toContain('Marie');
    const deleteButton = document.querySelector('[data-event-delete]');
    expect(deleteButton.dataset.eventStart).toBe('2024-04-01T08:00:00.000Z');
  });

  test('clicking the timeline prepares the new-event modal and enables submit after selections', () => {
    const newEventModal = document.querySelector('[data-new-event-modal]');
    const timeline = document.querySelector('.kitlast-planner__timeline');
    const serviceSelect = document.querySelector('[data-new-event-field="service"]');
    const clientSelect = document.querySelector('[data-new-event-field="client"]');
    const submitButton = document.querySelector('[data-new-event-submit]');
    const startInput = document.querySelector('[data-new-event-field="start-input"]');

    expect(newEventModal.hasAttribute('hidden')).toBe(true);
    timeline.getBoundingClientRect = () => ({ top: 0, bottom: 600, height: 600, left: 0, right: 0, width: 0 });

    timeline.dispatchEvent(new MouseEvent('click', { bubbles: true, clientY: 300 }));

    expect(newEventModal.hasAttribute('hidden')).toBe(false);
    expect(startInput.value).not.toBe('');
    expect(document.querySelector('[data-new-event-field="time"]').textContent).not.toBe('');
    expect(submitButton.disabled).toBe(true);

    serviceSelect.value = '1';
    serviceSelect.dispatchEvent(new Event('change', { bubbles: true }));
    expect(submitButton.disabled).toBe(true);

    clientSelect.value = '42';
    clientSelect.dispatchEvent(new Event('change', { bubbles: true }));

    expect(submitButton.disabled).toBe(false);
  });
});
