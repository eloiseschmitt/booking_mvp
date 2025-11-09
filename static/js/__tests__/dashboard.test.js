const { initializeDashboard } = require('../dashboard.js');

const buildDom = () => {
  document.body.innerHTML = `
    <div class="kitlast-dashboard-sidebar">
      <button class="kitlast-dashboard-sidebar__toggle" data-section-target="services" aria-expanded="false"></button>
      <nav>
        <a href="#" data-section-target="services">Services</a>
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
        <div data-new-event-field="date"></div>
        <div data-new-event-field="time"></div>
        <div data-new-event-field="message"></div>
        <select data-new-event-field="service">
          <option value="">Sélectionnez</option>
        </select>
        <button type="button" data-new-event-confirm></button>
      </div>
    </div>

    <div class="kitlast-planner__columns"></div>
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
});
