document.addEventListener('DOMContentLoaded', () => {
  /* Script originally embedded in dashboard.html. */

  const toggle = document.querySelector('.kitlast-dashboard-sidebar__toggle');
  const subnav = document.getElementById('services-subnav');
  const sectionContainer = document.querySelector('.kitlast-dashboard-content');
  const sections = document.querySelectorAll('.kitlast-content-section');
  const navLinks = document.querySelectorAll('[data-section-target]');
  const categoryModal = document.querySelector('[data-category-modal]');
  const serviceModal = document.querySelector('[data-service-modal]');
  const eventModal = document.querySelector('[data-event-modal]');
  const newEventModal = document.querySelector('[data-new-event-modal]');
  const categoryFormField = categoryModal ? categoryModal.querySelector('input[type="text"]') : null;
  const serviceNameField = serviceModal ? serviceModal.querySelector('input[name="name"]') : null;
  const eventFieldMap = eventModal
    ? {
      date: eventModal.querySelector('[data-event-field="date"]'),
      time: eventModal.querySelector('[data-event-field="time"]'),
      title: eventModal.querySelector('[data-event-field="title"]'),
      service: eventModal.querySelector('[data-event-field="service"]'),
      category: eventModal.querySelector('[data-event-field="category"]'),
      status: eventModal.querySelector('[data-event-field="status"]'),
      created_by: eventModal.querySelector('[data-event-field="created_by"]'),
      description: eventModal.querySelector('[data-event-field="description"]'),
      deleteButton: eventModal.querySelector('[data-event-delete]'),
    }
    : null;
  const newEventFieldMap = newEventModal
    ? {
      date: newEventModal.querySelector('[data-new-event-field="date"]'),
      time: newEventModal.querySelector('[data-new-event-field="time"]'),
      message: newEventModal.querySelector('[data-new-event-field="message"]'),
      confirm: newEventModal.querySelector('[data-new-event-confirm]'),
      service: newEventModal.querySelector('[data-new-event-field="service"]'),
    }
    : null;
  const plannerColumnsContainer = document.querySelector('.kitlast-planner__columns');
  const plannerColumns = plannerColumnsContainer ? Array.from(plannerColumnsContainer.querySelectorAll('[data-planner-column]')) : [];
  const plannerButtons = document.querySelectorAll('[data-planner-action]');
  const todayButton = document.querySelector('[data-planner-action="today"]');
  const dayButton = document.querySelector('[data-planner-action="day"]');
  const weekButton = document.querySelector('[data-planner-action="week"]');
  const prevButton = document.querySelector('[data-planner-nav="prev"]');
  const nextButton = document.querySelector('[data-planner-nav="next"]');
  const plannerRangeLabel = document.querySelector('[data-planner-range]');

  let currentSection = sectionContainer ? sectionContainer.dataset.activeSection || 'overview' : 'overview';
  let currentSingleColumn = null;
  let currentViewMode = 'week';

  const readWeekOffset = () => {
    if (!sectionContainer) return 0;
    const value = sectionContainer.dataset.weekOffset;
    const parsed = Number.parseInt(value || '0', 10);
    return Number.isNaN(parsed) ? 0 : parsed;
  };

  const navigateWeek = (delta) => {
    const url = new URL(window.location);
    const existing = url.searchParams.get('week_offset');
    const parsedExisting = existing !== null ? Number.parseInt(existing, 10) : NaN;
    const baseOffset = Number.isNaN(parsedExisting) ? readWeekOffset() : parsedExisting;
    url.searchParams.set('section', 'planning');
    url.searchParams.set('week_offset', (baseOffset + delta).toString());
    window.location.href = url.toString();
  };

  const syncUrl = () => {
    try {
      const url = new URL(window.location);
      url.searchParams.set('section', currentSection);
      if (currentSection === 'services') {
        if (categoryModal && !categoryModal.hasAttribute('hidden')) {
          url.searchParams.set('show', 'category-form');
        } else if (serviceModal && !serviceModal.hasAttribute('hidden')) {
          url.searchParams.set('show', 'service-form');
        } else {
          url.searchParams.delete('show');
        }
      } else {
        url.searchParams.delete('show');
      }
      window.history.replaceState(null, '', url);
    } catch (err) {
      /* noop */
    }
  };

  const openModal = (modal, focusElement) => {
    if (!modal) return;
    modal.removeAttribute('hidden');
    if (focusElement) {
      window.requestAnimationFrame(() => focusElement.focus());
    }
    syncUrl();
  };

  const closeModal = (modal) => {
    if (!modal) return;
    modal.setAttribute('hidden', '');
    syncUrl();
  };

  const attachModalHandlers = (modal, focusElement) => {
    if (!modal) return null;
    modal.querySelectorAll('[data-modal-close]').forEach((btn) => {
      btn.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopPropagation();
        closeModal(modal);
      });
    });
    modal.addEventListener('click', (event) => {
      const target = event.target;
      const elementTarget =
        target && target.nodeType === Node.ELEMENT_NODE
          ? target
          : target?.parentElement;
      const closer = elementTarget?.closest('[data-modal-close]');
      const isBackdropClick = target === modal;
      if (closer || isBackdropClick) {
        event.stopPropagation();
        closeModal(modal);
      }
    });
    return {
      open: () => openModal(modal, focusElement),
      close: () => closeModal(modal),
    };
  };

  const categoryModalHandlers = attachModalHandlers(categoryModal, categoryFormField);
  const serviceModalHandlers = attachModalHandlers(serviceModal, serviceNameField);
  const eventModalHandlers = attachModalHandlers(eventModal);
  const newEventModalHandlers = attachModalHandlers(newEventModal);

  const setActiveSection = (sectionName) => {
    if (!sectionContainer) return;
    currentSection = sectionName;
    sectionContainer.setAttribute('data-active-section', sectionName);
    sections.forEach((section) => {
      section.classList.toggle('is-active', section.dataset.section === sectionName);
    });
    if (sectionName === 'services' && toggle && subnav) {
      toggle.setAttribute('aria-expanded', 'true');
      subnav.hidden = false;
    } else if (sectionName !== 'services') {
      closeModal(categoryModal);
      closeModal(serviceModal);
      closeModal(eventModal);
      closeModal(newEventModal);
    }
    syncUrl();
  };

  if (toggle && subnav) {
    toggle.addEventListener('click', () => {
      const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!isExpanded));
      subnav.hidden = isExpanded;
      setActiveSection('services');
    });
  }

  navLinks.forEach((link) => {
    link.addEventListener('click', (event) => {
      const targetSection = link.dataset.sectionTarget;
      if (!targetSection) return;
      setActiveSection(targetSection);
      event.preventDefault();
    });
  });

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') {
      return;
    }
    if (categoryModal && !categoryModal.hasAttribute('hidden')) {
      closeModal(categoryModal);
    }
    if (serviceModal && !serviceModal.hasAttribute('hidden')) {
      closeModal(serviceModal);
    }
    if (eventModal && !eventModal.hasAttribute('hidden')) {
      closeModal(eventModal);
    }
    if (newEventModal && !newEventModal.hasAttribute('hidden')) {
      closeModal(newEventModal);
    }
  });

  document.addEventListener(
    'click',
    (event) => {
      const target = event.target;
      if (!(target instanceof Element)) {
        return;
      }
      const modalContainer = target.closest('.kitlast-modal');
      const explicitCloser = target.closest('[data-modal-close]');

      if (explicitCloser && modalContainer) {
        event.preventDefault();
        event.stopPropagation();
        closeModal(modalContainer);
        return;
      }

      if (modalContainer && target === modalContainer) {
        console.log('backdrop close');
        event.preventDefault();
        event.stopPropagation();
      }
    },
    true
  );

  const minutesToTime = (totalMinutes) => {
    const hours = String(Math.floor(totalMinutes / 60)).padStart(2, '0');
    const minutes = String(totalMinutes % 60).padStart(2, '0');
    return `${hours}:${minutes}`;
  };

  const parseColumnDate = (value) => {
    const [day, month] = (value || '').split('/').map(Number);
    const year = new Date().getFullYear();
    return new Date(year, (month || 1) - 1, day || 1, 0, 0, 0, 0);
  };

  const fillEventModal = (data) => {
    if (!eventFieldMap) return;
    const fallback = '—';
    eventFieldMap.date.textContent = data.date || fallback;
    eventFieldMap.time.textContent = data.time || fallback;
    eventFieldMap.title.textContent = data.title || fallback;
    eventFieldMap.service.textContent = data.service || fallback;
    eventFieldMap.category.textContent = data.category || fallback;
    eventFieldMap.status.textContent = data.status || fallback;
    eventFieldMap.created_by.textContent = data.created_by || fallback;
    eventFieldMap.description.textContent = data.description || fallback;
    if (eventFieldMap.deleteButton) {
      const start = data.start || '';
      const end = data.end || '';
      eventFieldMap.deleteButton.dataset.eventStart = start;
      eventFieldMap.deleteButton.dataset.eventEnd = end;
      const ariaLabel = data.title ? `Supprimer ${data.title}` : 'Supprimer le rendez-vous';
      eventFieldMap.deleteButton.setAttribute('aria-label', ariaLabel);
    }
  };

  const fillNewEventModal = (data) => {
    if (!newEventFieldMap) return;
    newEventFieldMap.date.textContent = data.dateDisplay;
    newEventFieldMap.time.textContent = data.timeDisplay;
    if (newEventFieldMap.message) {
      newEventFieldMap.message.textContent = `Créneau sélectionné pour le ${data.dateDisplay} à ${data.timeDisplay}.`;
    }
    if (newEventFieldMap.confirm) {
      newEventFieldMap.confirm.dataset.newEventDate = data.dateIso;
      newEventFieldMap.confirm.dataset.newEventTime = data.timeIso;
    }
    if (newEventFieldMap.service) {
      newEventFieldMap.service.selectedIndex = 0;
    }
  };

  const updatePlannerButtons = (view) => {
    plannerButtons.forEach((button) => {
      button.classList.toggle('kitlast-planner__button--active', button.dataset.plannerAction === view);
    });
    if (plannerRangeLabel) {
      plannerRangeLabel.textContent = view === 'week' ? 'Vue semaine' : 'Vue jour';
    }
  };

  const showWeekView = () => {
    if (!plannerColumnsContainer) return;
    plannerColumnsContainer.classList.remove('kitlast-planner__columns--single');
    plannerColumns.forEach((column) => column.classList.remove('is-hidden'));
    updatePlannerButtons('week');
    currentSingleColumn = null;
    currentViewMode = 'week';
  };

  const showSingleDay = (column, viewName) => {
    if (!plannerColumnsContainer || plannerColumns.length === 0) return;
    const targetColumn = column || plannerColumns[0];
    plannerColumns.forEach((col) => {
      col.classList.toggle('is-hidden', col !== targetColumn);
    });
    plannerColumnsContainer.classList.add('kitlast-planner__columns--single');
    updatePlannerButtons(viewName);
    currentSingleColumn = targetColumn;
    currentViewMode = viewName;
  };

  const showTodayView = () => {
    if (!plannerColumnsContainer || plannerColumns.length === 0) return;
    const today = new Date();
    const formatted = today.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
    const matchingColumn = plannerColumns.find((column) => column.dataset.plannerDate === formatted);
    showSingleDay(matchingColumn, 'day');
  };

  todayButton?.addEventListener('click', () => {
    showTodayView();
  });

  dayButton?.addEventListener('click', () => {
    showTodayView();
  });

  weekButton?.addEventListener('click', () => {
    showWeekView();
  });

  const navigateDayView = (direction) => {
    if (!plannerColumns.length) return;
    if (!currentSingleColumn) {
      showTodayView();
      return;
    }
    const currentIndex = plannerColumns.indexOf(currentSingleColumn);
    const targetColumn =
      direction === 'previous'
        ? plannerColumns[currentIndex - 1] || plannerColumns[plannerColumns.length - 1]
        : plannerColumns[currentIndex + 1] || plannerColumns[0];
    showSingleDay(targetColumn, 'day');
  };

  prevButton?.addEventListener('click', () => {
    if (currentViewMode === 'week') {
      navigateWeek(-1);
      return;
    }
    navigateDayView('previous');
  });

  nextButton?.addEventListener('click', () => {
    if (currentViewMode === 'week') {
      navigateWeek(1);
      return;
    }
    navigateDayView('next');
  });

  showWeekView();

  if (plannerColumnsContainer) {
    plannerColumnsContainer.addEventListener('click', (evt) => {
      const card = evt.target.closest('[data-planner-event]');
      if (card && eventModalHandlers) {
        fillEventModal({
          label: card.dataset.eventLabel,
          date: card.dataset.eventDate,
          time: card.dataset.eventTime,
          title: card.dataset.eventTitle,
          service: card.dataset.eventService,
          category: card.dataset.eventCategory,
          description: card.dataset.eventDescription,
          status: card.dataset.eventStatus,
          created_by: card.dataset.eventCreatedBy,
          start: card.dataset.eventStart,
          end: card.dataset.eventEnd,
        });
        eventModalHandlers.open();
        return;
      }

      const timeline = evt.target.closest('.kitlast-planner__timeline');
      const column = evt.target.closest('[data-planner-column]');
      if (!timeline || !column || !newEventModalHandlers || !newEventFieldMap) {
        return;
      }

      const rect = timeline.getBoundingClientRect();
      const clampedY = Math.min(Math.max(evt.clientY, rect.top), rect.bottom);
      const ratio = rect.height ? (clampedY - rect.top) / rect.height : 0;
      const totalMinutes = 12 * 60;
      const minutesFromStart = Math.round((ratio * totalMinutes) / 15) * 15;
      const absoluteMinutes = 8 * 60 + minutesFromStart;
      const timeDisplay = minutesToTime(absoluteMinutes);

      const rawDate = column.dataset.plannerDate || column.querySelector('.kitlast-planner__column-date')?.textContent?.trim() || '';
      const baseDate = parseColumnDate(rawDate);
      const startDate = new Date(baseDate.getTime());
      startDate.setHours(Math.floor(absoluteMinutes / 60), absoluteMinutes % 60, 0, 0);

      fillNewEventModal({
        dateDisplay: rawDate,
        timeDisplay,
        dateIso: startDate.toISOString(),
        timeIso: timeDisplay,
      });
      newEventModalHandlers.open();
    });
  }

  if (newEventFieldMap?.confirm && newEventModalHandlers) {
    newEventFieldMap.confirm.addEventListener('click', () => {
      newEventModalHandlers.close();
      const url = new URL(window.location);
      url.searchParams.set('section', 'planning');
      url.searchParams.set(
        'new_event_start',
        newEventFieldMap.confirm.dataset.newEventDate || ''
      );
      if (newEventFieldMap.service && newEventFieldMap.service.value) {
        url.searchParams.set('service_id', newEventFieldMap.service.value);
      } else {
        url.searchParams.delete('service_id');
      }
      window.location.href = url.toString();
    });
  }

  if (sectionContainer) {
    const active = sectionContainer.dataset.activeSection;
    const shouldShowCategory =
      (sectionContainer.dataset.showCategory || '').toLowerCase() === 'true';
    const shouldShowService =
      (sectionContainer.dataset.showService || '').toLowerCase() === 'true';
    setActiveSection(active || 'overview');
    if (active === 'services') {
      if (shouldShowCategory && categoryModalHandlers) {
        categoryModalHandlers.open();
      }
      if (shouldShowService && serviceModalHandlers) {
        serviceModalHandlers.open();
      }
    }
  }
});
