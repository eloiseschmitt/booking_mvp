const { initializeDashboard } = require('../dashboard.js');

const formatDateLabel = (date) =>
  date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });

const buildDom = () => {
  const today = new Date();
  const todayLabel = formatDateLabel(today);
  const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000);
  const tomorrowLabel = formatDateLabel(tomorrow);
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
        <form>
          <input type="hidden" data-event-field="event-id" />
          <button type="button" data-event-delete></button>
        </form>
      </div>
    </div>

    <div class="kitlast-modal" data-new-event-modal hidden>
      <div class="kitlast-modal__overlay" data-modal-close></div>
      <div class="kitlast-modal__content">
        <form data-new-event-form>
          <input type="hidden" data-new-event-field="start-input" />
          <input type="hidden" data-new-event-field="end-input" />
          <div data-new-event-field="date"></div>
          <div data-new-event-field="time"></div>
          <div data-new-event-field="message"></div>
          <select data-new-event-field="start-select"></select>
          <select data-new-event-field="end-select"></select>
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
        <header class="kitlast-modal__header">
          <h2 id="client-modal-title">Ajouter un client</h2>
          <button type="button" data-modal-close>×</button>
        </header>
        <form data-client-form>
          <input type="hidden" name="action" value="add_client" data-client-form-action>
          <input type="hidden" name="client_id" value="" data-client-form-id>
          <input name="first_name" />
          <input name="last_name" />
          <input name="email" />
          <input name="phone_number" />
          <button type="submit">Enregistrer</button>
        </form>
      </div>
    </div>

    <button data-open-client-modal data-testid="open-client-modal">Ajouter un client</button>

    <table>
      <tr>
        <td>Elisa Toto</td>
        <td>
          <button data-open-client-detail data-client-id="7" data-client-full-name="Elisa Toto" data-client-email="toto@email.com" data-client-phone="">Modifier</button>
          <button data-client-delete data-client-id="7" data-client-full-name="Elisa Toto">Supprimer</button>
        </td>
      </tr>
    </table>

    <div class="kitlast-modal" data-client-detail-modal hidden data-client-id="7">
      <div class="kitlast-modal__overlay" data-modal-close></div>
      <div class="kitlast-modal__content">
        <div data-client-field="full_name">Elisa Toto</div>
        <div data-client-field="phone">0600000000</div>
        <div data-client-field="email">toto@email.com</div>
        <button type="button" data-client-detail-edit>Modifier</button>
      </div>
    </div>

    <div class="kitlast-modal" data-client-delete-modal hidden>
      <div class="kitlast-modal__overlay" data-modal-close></div>
      <div class="kitlast-modal__content">
        <p>Souhaitez-vous supprimer <span data-client-delete-name></span> ?</p>
        <form>
          <input type="hidden" name="client_id" data-client-delete-id value="">
          <button type="submit" data-client-delete-confirm>Confirmer</button>
          <button type="button" data-modal-close>Annuler</button>
        </form>
      </div>
    </div>

    <div class="kitlast-planner__columns">
      <div class="kitlast-planner__column" data-planner-column data-planner-date="${todayLabel}">
        <div class="kitlast-planner__column-date">${todayLabel}</div>
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
      <div class="kitlast-planner__column" data-planner-column data-planner-date="${tomorrowLabel}">
        <div class="kitlast-planner__column-date">${tomorrowLabel}</div>
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
    // title should be 'Ajouter un client' when opened from add button
    expect(document.getElementById('client-modal-title').textContent).toBe('Ajouter un client');
  });

  test('clicking modify pre-fills client modal and sets update action', () => {
    const clientModal = document.querySelector('[data-testid="client-modal"]');
    const modifyButton = document.querySelector('[data-open-client-detail]');

    expect(clientModal.hasAttribute('hidden')).toBe(true);
    modifyButton.click();

    expect(clientModal.hasAttribute('hidden')).toBe(false);
    // modal title should switch to edit mode
    expect(document.getElementById('client-modal-title').textContent).toBe('Modifier un client');
    // fields prefilled
    expect(document.querySelector('input[name="first_name"]').value).toBe('Elisa');
    expect(document.querySelector('input[name="last_name"]').value).toBe('Toto');
    expect(document.querySelector('input[name="email"]').value).toBe('toto@email.com');
    // hidden inputs
    expect(document.querySelector('[data-client-form-action]').value).toBe('update_client');
    expect(document.querySelector('[data-client-form-id]').value).toBe('7');
  });

  test('clicking delete opens confirmation modal and fills name and id', () => {
    const deleteModal = document.querySelector('[data-client-delete-modal]');
    const deleteButton = document.querySelector('[data-client-delete]');

    expect(deleteModal.hasAttribute('hidden')).toBe(true);
    deleteButton.click();

    expect(deleteModal.hasAttribute('hidden')).toBe(false);
    expect(document.querySelector('[data-client-delete-name]').textContent).toBe('Elisa Toto');
    expect(document.querySelector('[data-client-delete-id]').value).toBe('7');
  });

  test('escape closes open modals', () => {
    const serviceModal = document.querySelector('[data-service-modal]');
    const categoryModal = document.querySelector('[data-category-modal]');
    categoryModal.removeAttribute('hidden');

    expect(serviceModal.hasAttribute('hidden')).toBe(false);
    expect(categoryModal.hasAttribute('hidden')).toBe(false);

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));

    expect(serviceModal.hasAttribute('hidden')).toBe(true);
    expect(categoryModal.hasAttribute('hidden')).toBe(true);
  });

  test('client detail edit button populates the client modal', () => {
    const clientDetailModal = document.querySelector('[data-client-detail-modal]');
    const editButton = clientDetailModal.querySelector('[data-client-detail-edit]');
    const clientModal = document.querySelector('[data-testid="client-modal"]');

    expect(clientDetailModal.hasAttribute('hidden')).toBe(true);
    clientDetailModal.removeAttribute('hidden');
    editButton.click();

    expect(clientDetailModal.hasAttribute('hidden')).toBe(true);
    expect(clientModal.hasAttribute('hidden')).toBe(false);
    expect(document.getElementById('client-modal-title').textContent).toBe('Modifier un client');
    expect(document.querySelector('input[name="first_name"]').value).toBe('Elisa');
    expect(document.querySelector('input[name="last_name"]').value).toBe('Toto');
    expect(document.querySelector('input[name="email"]').value).toBe('toto@email.com');
    expect(document.querySelector('input[name="phone_number"]').value).toBe('0600000000');
    expect(document.querySelector('[data-client-form-action]').value).toBe('update_client');
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

  test('changing end time before start time clamps the end selection', () => {
    const timeline = document.querySelector('.kitlast-planner__timeline');
    timeline.getBoundingClientRect = () => ({ top: 0, bottom: 600, height: 600, left: 0, right: 0, width: 0 });
    timeline.dispatchEvent(new MouseEvent('click', { bubbles: true, clientY: 100 }));

    const startSelect = document.querySelector('[data-new-event-field="start-select"]');
    const endSelect = document.querySelector('[data-new-event-field="end-select"]');

    startSelect.value = '10:00';
    startSelect.dispatchEvent(new Event('change', { bubbles: true }));
    endSelect.value = '09:00';
    endSelect.dispatchEvent(new Event('change', { bubbles: true }));

    expect(endSelect.value).toBe('10:15');
    expect(document.querySelector('[data-new-event-field="end-input"]').value).not.toBe('');
  });

  test('day/week buttons toggle the planner layout', () => {
    const columnsContainer = document.querySelector('.kitlast-planner__columns');
    const dayButton = document.querySelector('[data-planner-action="day"]');
    const weekButton = document.querySelector('[data-planner-action="week"]');
    const columns = Array.from(document.querySelectorAll('[data-planner-column]'));

    dayButton.click();
    expect(columnsContainer.classList.contains('kitlast-planner__columns--single')).toBe(true);
    expect(columns.filter((col) => !col.classList.contains('is-hidden')).length).toBe(1);

    weekButton.click();
    expect(columnsContainer.classList.contains('kitlast-planner__columns--single')).toBe(false);
    expect(columns.filter((col) => !col.classList.contains('is-hidden')).length).toBe(2);
  });

  test('event delete button submits the form when event id is present', () => {
    const plannerEvent = document.querySelector('[data-planner-event]');
    plannerEvent.click();

    const form = document.querySelector('[data-event-modal] form');
    const submitSpy = jest.spyOn(form, 'submit').mockImplementation(() => {});
    const deleteButton = document.querySelector('[data-event-delete]');

    deleteButton.click();

    expect(submitSpy).toHaveBeenCalled();
    submitSpy.mockRestore();
  });
});
