document.addEventListener('DOMContentLoaded', () => {
  // Stan aplikacji
  let depositsState = [];
  let archiveState = [];
  let currentInventoryFilter = 'all';
  let showAgingOnly = false;
  let activeReleaseId = null;
  let activeMoveId = null;

  // Domyślna konfiguracja kalendarza na wypadek braku połączenia lub uruchomienia ze starszego .exe
  const DEFAULT_CALENDAR_CONFIG = {
    adminPassword: "admin",
    allowedEmails: [
      "michal@twoje4kola.pl",
      "alert@itover.pl"
    ],
    publicHeader: "Wulkanizacja Michał - rezerwacja terminu 600223669",
    stationsCount: 2,
    slotDurationMinutes: 15,
    services: [
      { id: "steel_4", name: "Przekładka 4 kół stalowych (osobowe)", durationMinutes: 45, price: 120 },
      { id: "alu_small", name: "Koła aluminiowe <= 17 cali", durationMinutes: 45, price: 140 },
      { id: "alu_premium", name: "Koła aluminiowe premium (> 17 cali)", durationMinutes: 60, price: 180 },
      { id: "bus", name: "Bus / Samochód dostawczy", durationMinutes: 60, price: 200 },
      { id: "quick", name: "Szybki serwis / wyważenie / 2 koła", durationMinutes: 30, price: 60 }
    ],
    monthlyWorkingHours: {
      "1": { start: "08:00", end: "18:00", saturdayStart: "08:00", saturdayEnd: "14:00", workSaturday: true },
      "2": { start: "08:00", end: "18:00", saturdayStart: "08:00", saturdayEnd: "14:00", workSaturday: true },
      "3": { start: "08:00", end: "18:00", saturdayStart: "08:00", saturdayEnd: "14:00", workSaturday: true },
      "4": { start: "08:00", end: "20:00", saturdayStart: "08:00", saturdayEnd: "16:00", workSaturday: true, note: "Sezon wiosenny (kwiecień)" },
      "5": { start: "08:00", end: "18:00", saturdayStart: "08:00", saturdayEnd: "14:00", workSaturday: true },
      "6": { start: "08:00", end: "18:00", saturdayStart: "08:00", saturdayEnd: "14:00", workSaturday: true },
      "7": { start: "08:00", end: "18:00", saturdayStart: "08:00", saturdayEnd: "14:00", workSaturday: true },
      "8": { start: "08:00", end: "18:00", saturdayStart: "08:00", saturdayEnd: "14:00", workSaturday: true },
      "9": { start: "08:00", end: "18:00", saturdayStart: "08:00", saturdayEnd: "14:00", workSaturday: true },
      "10": { start: "08:00", end: "18:00", saturdayStart: "08:00", saturdayEnd: "14:00", workSaturday: true },
      "11": { start: "08:00", end: "20:00", saturdayStart: "08:00", saturdayEnd: "16:00", workSaturday: true, note: "Sezon zimowy (listopad)" },
      "12": { start: "08:00", end: "18:00", saturdayStart: "08:00", saturdayEnd: "14:00", workSaturday: true }
    },
    customHolidays: []
  };

  // Stan modułu kalendarza
  let calendarSelectedDate = new Date().toISOString().split('T')[0];
  let calendarAppointmentsState = [];
  let calendarConfigState = JSON.parse(JSON.stringify(DEFAULT_CALENDAR_CONFIG));
  try {
    const savedLocalCfg = localStorage.getItem('tire_calendar_config');
    if (savedLocalCfg) calendarConfigState = JSON.parse(savedLocalCfg);
  } catch(e) {}
  let foundQuickSlot = null;

  // Pobranie elementów DOM
  const menuItems = document.querySelectorAll('.menu-item');
  const tabContents = document.querySelectorAll('.tab-content');
  const sectionTitle = document.getElementById('section-title');
  const liveTimeEl = document.getElementById('live-time');
  
  // Daty domyślne w formularzach
  const depositDateInput = document.getElementById('depositDate');
  const releaseDateInput = document.getElementById('release-date-input');
  const today = new Date().toISOString().split('T')[0];
  if (depositDateInput) depositDateInput.value = today;
  if (releaseDateInput) releaseDateInput.value = today;

  // Ustawienie zegara w nagłówku
  function updateTime() {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    liveTimeEl.textContent = new Date().toLocaleDateString('pl-PL', options);
  }
  updateTime();
  setInterval(updateTime, 60000);

  // --- 1. OBSŁUGA NAWIGACJI (TABY) ---
  menuItems.forEach(item => {
    item.addEventListener('click', () => {
      const target = item.getAttribute('data-target');
      
      // Przełączenie menu
      menuItems.forEach(mi => mi.classList.remove('active'));
      item.classList.add('active');
      
      // Przełączenie sekcji
      tabContents.forEach(content => content.classList.remove('active'));
      const activeSection = document.getElementById(target);
      activeSection.classList.add('active');
      
      // Nagłówek sekcji
      sectionTitle.textContent = item.querySelector('span').textContent;
      
      // Odświeżenie danych przy wejściu do sekcji
      if (target === 'dashboard-section' || target === 'inventory-section') {
        fetchDeposits();
      } else if (target === 'archive-section') {
        fetchArchive();
      } else if (target === 'calendar-section') {
        loadCalendarDay(calendarSelectedDate);
      }
    });
  });

  // --- 2. OPERACJE NA DANYCH (API API) ---
  
  // Pobieranie aktywnych depozytów
  async function fetchDeposits() {
    try {
      const response = await fetch('/api/deposits');
      depositsState = await response.json();
      updateDashboardStats();
      renderInventoryTable();
      renderAgingReport();
    } catch (err) {
      console.error("Błąd pobierania opon:", err);
    }
  }

  // Pobieranie archiwum
  async function fetchArchive() {
    try {
      const response = await fetch('/api/archive');
      archiveState = await response.json();
      renderArchiveTable();
    } catch (err) {
      console.error("Błąd pobierania archiwum:", err);
    }
  }

  // Obliczanie różnicy dni
  function calculateDays(dateStr) {
    const dateDep = new Date(dateStr);
    const todayDate = new Date();
    // Zerowanie czasu do porównania samych dat
    dateDep.setHours(0,0,0,0);
    todayDate.setHours(0,0,0,0);
    const diffTime = todayDate - dateDep;
    return Math.max(0, Math.floor(diffTime / (1000 * 60 * 60 * 24)));
  }

  // Formatowanie daty
  function formatDate(dateStr) {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleDateString('pl-PL');
  }

  // Helper dla odznak sezonu
  function getSeasonBadge(season) {
    const s = season.toLowerCase();
    if (s === 'zimowe') return `<span class="badge badge-season-zimowe">❄️ Zimowe</span>`;
    if (s === 'letnie') return `<span class="badge badge-season-letnie">☀️ Letnie</span>`;
    return `<span class="badge badge-season-caloroczne">🌦️ Całoroczne</span>`;
  }

  // Helper dla felg
  function getRimBadge(rim) {
    if (rim === 'Aluminiowe') return `<span class="badge badge-location">Alu</span>`;
    if (rim === 'Stalowe') return `<span class="badge badge-location">Stal</span>`;
    return `<span class="badge text-muted">Brak</span>`;
  }

  // --- 3. RENDERING DASHBOARDU ---
  function updateDashboardStats() {
    const total = depositsState.length;
    const wiata = depositsState.filter(d => d.location === 'wiata').length;
    const tdol = depositsState.filter(d => d.location === 'Tdół').length;
    const tgora = depositsState.filter(d => d.location === 'Tgóra').length;

    document.getElementById('stats-total').textContent = total;
    document.getElementById('stats-wiata').textContent = wiata;
    document.getElementById('stats-tdol').textContent = tdol;
    document.getElementById('stats-tgora').textContent = tgora;
  }

  function renderAgingReport() {
    const tbody = document.getElementById('aging-report-table-body');
    
    // Sortuj opony od najstarszych
    const sorted = [...depositsState]
      .map(d => ({ ...d, days: calculateDays(d.depositDate) }))
      .filter(d => d.days >= 180) // Raportuj te leżące ponad pół roku
      .sort((a, b) => b.days - a.days);

    if (sorted.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted" style="padding: 30px 10px;">Brak depozytów zalegających powyżej 180 dni. Świetna rotacja!</td></tr>`;
      return;
    }

    tbody.innerHTML = sorted.map(d => {
      const daysColorClass = d.days >= 360 ? 'text-danger-custom' : 'text-warning-custom';
      return `
        <tr class="${d.days >= 360 ? 'row-danger' : 'row-warning'}">
          <td data-label="Klient"><strong>${d.clientName}</strong><br><small class="text-muted">${d.clientPhone}</small></td>
          <td data-label="Rejestracja"><span class="badge badge-location">${d.carLicensePlate}</span></td>
          <td data-label="Opony">${d.tireBrand ? d.tireBrand + ' ' : ''}${d.tireSize} <strong>(${d.quantity || 4} szt.)</strong><br>${getSeasonBadge(d.tireSeason)}</td>
          <td data-label="Lokalizacja"><span class="badge badge-success">${d.location}</span></td>
          <td data-label="Data przyjęcia">${formatDate(d.depositDate)}</td>
          <td data-label="Dni w magazynie" class="${daysColorClass}">${d.days} dni</td>
        </tr>
      `;
    }).join('');
  }

  // --- 4. RENDERING I WYSZUKIWANIE MAGAZYNU ---
  const inventorySearchInput = document.getElementById('inventory-search');
  const filterBtns = document.querySelectorAll('.filter-btn:not(.btn-toggle-aging)');
  const filterAgingBtn = document.getElementById('filter-aging-only');

  inventorySearchInput.addEventListener('input', renderInventoryTable);
  
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentInventoryFilter = btn.getAttribute('data-filter');
      renderInventoryTable();
    });
  });

  filterAgingBtn.addEventListener('click', () => {
    showAgingOnly = !showAgingOnly;
    filterAgingBtn.classList.toggle('active', showAgingOnly);
    renderInventoryTable();
  });

  function renderInventoryTable() {
    const tbody = document.getElementById('inventory-table-body');
    const query = inventorySearchInput.value.toLowerCase().trim();

    // Filtrowanie stanu magazynu
    const filtered = depositsState.filter(d => {
      // 1. Filtr wyszukiwania tekstowego
      const matchesSearch = 
        d.id.toLowerCase().includes(query) ||
        d.clientName.toLowerCase().includes(query) ||
        d.clientPhone.replace(/\s+/g, '').includes(query.replace(/\s+/g, '')) ||
        d.carLicensePlate.toLowerCase().includes(query) ||
        d.location.toLowerCase().includes(query);
      
      // 2. Filtr lokalizacji
      const matchesLocation = currentInventoryFilter === 'all' || d.location === currentInventoryFilter;
      
      // 3. Filtr zalegania (>180 dni)
      const days = calculateDays(d.depositDate);
      const matchesAging = !showAgingOnly || days >= 180;

      return matchesSearch && matchesLocation && matchesAging;
    });

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted" style="padding: 40px 10px;">Brak aktywnych opon spełniających kryteria wyszukiwania.</td></tr>`;
      return;
    }

    tbody.innerHTML = filtered.map(d => {
      const days = calculateDays(d.depositDate);
      let daysHtml = `${days} dni`;
      let rowClass = 'row-normal';

      if (days >= 360) {
        daysHtml = `<span class="text-danger-custom">⚠️ ${days} dni</span>`;
        rowClass = 'row-danger';
      } else if (days >= 180) {
        daysHtml = `<span class="text-warning-custom">⚠️ ${days} dni</span>`;
        rowClass = 'row-warning';
      }

      const emailBtnDisabled = !d.clientEmail ? 'disabled title="Brak e-maila klienta"' : '';

      return `
        <tr class="${rowClass}">
          <td data-label="ID"><strong>${d.id}</strong></td>
          <td data-label="Klient i Telefon"><strong>${d.clientName}</strong><br><small class="text-muted">${d.clientPhone}</small>${d.clientEmail ? `<br><small class="text-muted">${d.clientEmail}</small>` : ''}</td>
          <td data-label="Nr Rejestracyjny"><span class="badge badge-location">${d.carLicensePlate}</span></td>
          <td data-label="Opony">${d.tireBrand ? d.tireBrand : ''} ${d.tireSize} <strong>(${d.quantity || 4} szt.)</strong><br>${getSeasonBadge(d.tireSeason)}</td>
          <td data-label="Felgi">${getRimBadge(d.tireRimType)}</td>
          <td data-label="Lokalizacja"><span class="badge badge-success">${d.location}</span></td>
          <td data-label="Data przyjęcia">${formatDate(d.depositDate)}</td>
          <td data-label="Dni">${daysHtml}</td>
          <td data-label="Akcja" class="text-right">
            <button class="btn btn-secondary btn-sm btn-print-action" data-id="${d.id}" title="Drukuj pokwitowanie">🖨️ Drukuj</button>
            <button class="btn btn-primary btn-sm btn-email-action" data-id="${d.id}" ${emailBtnDisabled} title="Wyślij pokwitowanie na e-mail">✉️ E-mail</button>
            <button class="btn btn-secondary btn-sm btn-move-action" data-id="${d.id}">Przenieś</button>
            <button class="btn btn-success btn-sm btn-release-action" data-id="${d.id}">Wydaj</button>
          </td>
        </tr>
      `;
    }).join('');

    // Dodanie nasłuchu na przyciski wydania
    document.querySelectorAll('.btn-release-action').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.target.getAttribute('data-id');
        openReleaseModal(id);
      });
    });

    // Dodanie nasłuchu na przyciski przeniesienia
    document.querySelectorAll('.btn-move-action').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.target.getAttribute('data-id');
        openMoveModal(id);
      });
    });

    // Dodanie nasłuchu na przycisk drukowania
    document.querySelectorAll('.btn-print-action').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.target.getAttribute('data-id');
        printReceipt(id);
      });
    });

    // Dodanie nasłuchu na przycisk e-mail
    document.querySelectorAll('.btn-email-action').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const id = e.currentTarget.getAttribute('data-id');
        e.currentTarget.disabled = true;
        const originalText = e.currentTarget.textContent;
        e.currentTarget.textContent = "...";
        
        try {
          const response = await fetch(`/api/deposits/${id}/send-email`, { method: 'POST' });
          if (response.ok) {
            alert("E-mail z potwierdzeniem został pomyślnie wysłany!");
          } else {
            const errData = await response.json();
            alert(`Błąd wysyłki e-mail: ${errData.error}\nSkonfiguruj plik .env serwera.`);
          }
        } catch (err) {
          console.error(err);
          alert("Błąd połączenia z serwerem podczas wysyłki maila.");
        } finally {
          e.currentTarget.disabled = false;
          e.currentTarget.textContent = originalText;
        }
      });
    });
  }

  // --- 5. OBSŁUGA FORMULARZA PRZYJĘCIA ---
  const addForm = document.getElementById('add-deposit-form');
  addForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(addForm);
    const data = {};
    formData.forEach((value, key) => {
      data[key] = value;
    });

    try {
      const response = await fetch('/api/deposits', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        addForm.reset();
        if (depositDateInput) depositDateInput.value = today; // reset date to today
        const quantityInput = document.getElementById('quantity');
        if (quantityInput) quantityInput.value = 4; // reset quantity to default
        
        // Automatyczne przejście do zakładki Stan Magazynu
        const inventoryMenuBtn = document.querySelector('.menu-item[data-target="inventory-section"]');
        inventoryMenuBtn.click();
      } else {
        const errData = await response.json();
        alert(`Błąd: ${errData.error}`);
      }
    } catch (err) {
      console.error("Błąd wysyłania depozytu:", err);
      alert("Wystąpił błąd sieciowy podczas dodawania opon.");
    }
  });

  // --- 6. MODAL I OBSŁUGA WYDANIA OPON ---
  const releaseModal = document.getElementById('release-modal');
  const btnCloseModal = document.getElementById('btn-close-modal');
  const btnCancelRelease = document.getElementById('btn-cancel-release');
  const btnConfirmRelease = document.getElementById('btn-confirm-release');

  function openReleaseModal(id) {
    activeReleaseId = id;
    const deposit = depositsState.find(d => d.id === id);
    if (!deposit) return;

    document.getElementById('modal-client-name').textContent = deposit.clientName;
    document.getElementById('modal-car-plate').textContent = deposit.carLicensePlate;
    document.getElementById('modal-location').textContent = deposit.location;
    
    // Ustawienie dzisiejszej daty jako domyślnej daty wydania
    releaseDateInput.value = new Date().toISOString().split('T')[0];
    
    releaseModal.classList.add('active');
  }

  function closeReleaseModal() {
    releaseModal.classList.remove('active');
    activeReleaseId = null;
  }

  [btnCloseModal, btnCancelRelease].forEach(btn => {
    btn.addEventListener('click', closeReleaseModal);
  });

  // Potwierdzenie wydania
  btnConfirmRelease.addEventListener('click', async () => {
    if (!activeReleaseId) return;

    const releaseDate = releaseDateInput.value;

    try {
      const response = await fetch(`/api/deposits/${activeReleaseId}/release`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ releaseDate })
      });

      if (response.ok) {
        closeReleaseModal();
        fetchDeposits(); // odśwież magazyn i statystyki
      } else {
        const errData = await response.json();
        alert(`Błąd podczas wydawania: ${errData.error}`);
      }
    } catch (err) {
      console.error("Błąd podczas wydawania:", err);
      alert("Błąd połączenia z serwerem.");
    }
  });

  // --- 6a. OBSŁUGA PRZENOSZENIA MIĘDZY LOKALIZACJAMI ---
  const moveModal = document.getElementById('move-modal');
  const btnCloseMoveModal = document.getElementById('btn-close-move-modal');
  const btnCancelMove = document.getElementById('btn-cancel-move');
  const btnConfirmMove = document.getElementById('btn-confirm-move');
  const moveLocationSelect = document.getElementById('move-location-select');

  function openMoveModal(id) {
    activeMoveId = id;
    const deposit = depositsState.find(d => d.id === id);
    if (!deposit) return;

    document.getElementById('move-modal-client-name').textContent = deposit.clientName;
    document.getElementById('move-modal-car-plate').textContent = deposit.carLicensePlate;
    document.getElementById('move-modal-current-location').textContent = deposit.location;
    
    // Ustawienie domyślnie wybranej obecnej lokalizacji
    moveLocationSelect.value = deposit.location;
    
    moveModal.classList.add('active');
  }

  function closeMoveModal() {
    moveModal.classList.remove('active');
    activeMoveId = null;
  }

  [btnCloseMoveModal, btnCancelMove].forEach(btn => {
    btn.addEventListener('click', closeMoveModal);
  });

  btnConfirmMove.addEventListener('click', async () => {
    if (!activeMoveId) return;

    const newLocation = moveLocationSelect.value;

    try {
      const response = await fetch(`/api/deposits/${activeMoveId}/move`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ location: newLocation })
      });

      if (response.ok) {
        closeMoveModal();
        fetchDeposits(); // odśwież dane
      } else {
        const errData = await response.json();
        alert(`Błąd podczas przenoszenia: ${errData.error}`);
      }
    } catch (err) {
      console.error("Błąd podczas przenoszenia:", err);
      alert("Błąd połączenia z serwerem.");
    }
  });

  // --- 7. RENDERING ARCHIWUM ---
  const archiveSearchInput = document.getElementById('archive-search');
  archiveSearchInput.addEventListener('input', renderArchiveTable);

  function renderArchiveTable() {
    const tbody = document.getElementById('archive-table-body');
    const query = archiveSearchInput.value.toLowerCase().trim();

    // Filtrowanie archiwum
    const filtered = archiveState.filter(d => {
      return (
        d.id.toLowerCase().includes(query) ||
        d.clientName.toLowerCase().includes(query) ||
        d.clientPhone.replace(/\s+/g, '').includes(query.replace(/\s+/g, '')) ||
        d.carLicensePlate.toLowerCase().includes(query)
      );
    });

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted" style="padding: 40px 10px;">Brak danych w archiwum lub brak dopasowania do wyszukiwania.</td></tr>`;
      return;
    }

    // Sortowanie archiwum: od najnowszych wydań
    const sorted = [...filtered].sort((a, b) => new Date(b.releaseDate) - new Date(a.releaseDate));

    tbody.innerHTML = sorted.map(d => {
      return `
        <tr>
          <td data-label="ID"><strong>${d.id}</strong></td>
          <td data-label="Klient / Telefon"><strong>${d.clientName}</strong><br><small class="text-muted">${d.clientPhone}</small></td>
          <td data-label="Nr Rejestracyjny"><span class="badge badge-location">${d.carLicensePlate}</span></td>
          <td data-label="Opony">${d.tireBrand ? d.tireBrand : ''} ${d.tireSize} <strong>(${d.quantity || 4} szt.)</strong><br>${getSeasonBadge(d.tireSeason)}</td>
          <td data-label="Lokalizacja"><span class="badge badge-location">${d.location}</span></td>
          <td data-label="Przyjęto">${formatDate(d.depositDate)}</td>
          <td data-label="Wydano">${formatDate(d.releaseDate)}</td>
          <td data-label="Czas przechowywania" class="text-danger-custom" style="color: var(--color-success); font-weight: 600;">${d.daysStored} dni</td>
        </tr>
      `;
    }).join('');
  }

  // --- 7.5. DRUKOWANIE POKWITOWANIA ---
  function printReceipt(id) {
    const deposit = depositsState.find(d => d.id === id);
    if (!deposit) return;

    const printWindow = window.open('', '_blank', 'width=800,height=600');
    
    const receiptHtml = `
      <!DOCTYPE html>
      <html lang="pl">
      <head>
        <meta charset="UTF-8">
        <title>Pokwitowanie depozytu - ${deposit.carLicensePlate}</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            color: #333;
            line-height: 1.5;
            padding: 40px;
            max-width: 700px;
            margin: 0 auto;
          }
          .header {
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 20px;
            margin-bottom: 30px;
          }
          .header h1 {
            margin: 0 0 10px 0;
            font-size: 28px;
            text-transform: uppercase;
            letter-spacing: 1px;
          }
          .header p {
            margin: 0;
            color: #666;
            font-size: 14px;
          }
          .details-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
          }
          .details-table th, .details-table td {
            padding: 12px 15px;
            border: 1px solid #ddd;
            text-align: left;
          }
          .details-table th {
            background-color: #f8f9fa;
            width: 35%;
            font-weight: bold;
          }
          .details-table td {
            font-size: 16px;
          }
          .notes-box {
            border: 1px solid #ddd;
            background-color: #fafafa;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 40px;
          }
          .notes-box h4 {
            margin: 0 0 10px 0;
            text-transform: uppercase;
            font-size: 12px;
            color: #666;
          }
          .notes-box p {
            margin: 0;
            font-style: italic;
          }
          .signatures {
            display: flex;
            justify-content: space-between;
            margin-top: 60px;
            padding-top: 20px;
          }
          .signature-line {
            width: 45%;
            border-top: 1px dashed #333;
            text-align: center;
            padding-top: 10px;
            font-size: 14px;
            color: #666;
          }
          .footer {
            text-align: center;
            margin-top: 80px;
            font-size: 12px;
            color: #999;
            border-top: 1px solid #eee;
            padding-top: 20px;
          }
          @media print {
            body {
              padding: 0;
            }
            .no-print {
              display: none;
            }
          }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>POKWITOWANIE DEPOZYTU OPON</h1>
          <p>System Magazynowy 4KołaMag | Data wydruku: ${new Date().toLocaleDateString('pl-PL')}</p>
        </div>

        <table class="details-table">
          <tr>
            <th>Numer Depozytu (ID):</th>
            <td style="font-family: monospace; font-size: 13px;">${deposit.id}</td>
          </tr>
          <tr>
            <th>Imię i Nazwisko klienta:</th>
            <td><strong>${deposit.clientName}</strong></td>
          </tr>
          <tr>
            <th>Numer Telefonu:</th>
            <td>${deposit.clientPhone}</td>
          </tr>
          ${deposit.clientEmail ? `
          <tr>
            <th>Adres E-mail:</th>
            <td>${deposit.clientEmail}</td>
          </tr>` : ''}
          <tr>
            <th>Rejestracja pojazdu:</th>
            <td><strong>${deposit.carLicensePlate}</strong></td>
          </tr>
          <tr>
            <th>Opony (Rozmiar/Marka):</th>
            <td>${deposit.tireBrand || "Nieokreślono"} ${deposit.tireSize || ""}</td>
          </tr>
          <tr>
            <th>Sezon:</th>
            <td>${deposit.tireSeason}</td>
          </tr>
          <tr>
            <th>Felgi:</th>
            <td>${deposit.tireRimType}</td>
          </tr>
          <tr>
            <th>Liczba sztuk w depozycie:</th>
            <td><strong>${deposit.quantity || 4} szt.</strong></td>
          </tr>
          <tr>
            <th>Lokalizacja w magazynie:</th>
            <td>${deposit.location}</td>
          </tr>
          <tr>
            <th>Data przyjęcia opon:</th>
            <td>${formatDate(deposit.depositDate)}</td>
          </tr>
          <tr>
            <th>Opłata za depozyt:</th>
            <td><strong>${deposit.price} PLN</strong></td>
          </tr>
        </table>

        ${deposit.notes ? `
        <div class="notes-box">
          <h4>Uwagi i opis stanu opon/felg:</h4>
          <p>${deposit.notes}</p>
        </div>` : ''}

        <div class="signatures">
          <div class="signature-line">Podpis pracownika przyjmującego</div>
          <div class="signature-line">Podpis klienta / deponenta</div>
        </div>

        <div class="footer">
          Dziękujemy za skorzystanie z naszych usług. Prosimy o zachowanie niniejszego pokwitowania w celu odbioru opon.
        </div>

        <script>
          window.onload = function() {
            window.print();
          };
        </script>
      </body>
      </html>
    `;

    printWindow.document.write(receiptHtml);
    printWindow.document.close();
  }

  // --- 7.7. EKSPORT DO EXCELA (.XLSX) ---
  function exportTableToExcel(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;

    // Klonujemy tabelę, aby usunąć kolumnę "Akcja" z eksportu (kolumny z klasą .no-export)
    const clonedTable = table.cloneNode(true);
    clonedTable.querySelectorAll('.no-export').forEach(el => el.remove());
    clonedTable.querySelectorAll('tr').forEach(tr => {
      tr.querySelectorAll('.no-export').forEach(el => el.remove());
    });

    // Konwersja tabeli do arkusza SheetJS
    const wb = XLSX.utils.table_to_book(clonedTable, { sheet: "Raport" });
    
    // Zapis pliku
    XLSX.writeFile(wb, filename);
  }

  const btnExportInventory = document.getElementById('btn-export-inventory');
  if (btnExportInventory) {
    btnExportInventory.addEventListener('click', () => {
      const activeFilter = currentInventoryFilter === 'all' ? 'wszystko' : currentInventoryFilter;
      exportTableToExcel('inventory-data-table', `stan_magazynu_${activeFilter}_${new Date().toISOString().split('T')[0]}.xlsx`);
    });
  }

  const btnExportArchive = document.getElementById('btn-export-archive');
  if (btnExportArchive) {
    btnExportArchive.addEventListener('click', () => {
      exportTableToExcel('archive-data-table', `archiwum_wydanych_${new Date().toISOString().split('T')[0]}.xlsx`);
    });
  }

  // ==========================================================
  // --- 8. MODUŁ KALENDARZA WIZYT (TERMINARZ WULKANIZACJI) ---
  // ==========================================================

  const calPrevDay = document.getElementById('cal-prev-day');
  const calToday = document.getElementById('cal-today');
  const calNextDay = document.getElementById('cal-next-day');
  const calDatePicker = document.getElementById('cal-date-picker');
  const calSelectedDateLabel = document.getElementById('cal-selected-date-label');
  const calDayStatusPill = document.getElementById('cal-day-status-pill');
  const calHoursInfo = document.getElementById('cal-hours-info');
  const calAppointmentsCount = document.getElementById('cal-appointments-count');
  const calClosedAlert = document.getElementById('cal-closed-alert');
  const timelineSt1 = document.getElementById('timeline-st1');
  const timelineSt2 = document.getElementById('timeline-st2');
  const countSt1 = document.getElementById('count-st1');
  const countSt2 = document.getElementById('count-st2');

  const btnAddAppointment = document.getElementById('btn-add-appointment');
  const btnQuickFindSlot = document.getElementById('btn-quick-find-slot');
  const btnOpenConfigModal = document.getElementById('btn-open-config-modal');

  // Elementy modala wizyty
  const appointmentModal = document.getElementById('appointment-modal');
  const appModalTitle = document.getElementById('app-modal-title');
  const appForm = document.getElementById('appointment-form');
  const appIdInput = document.getElementById('app-id');
  const appDateInput = document.getElementById('app-date');
  const appStartTimeInput = document.getElementById('app-start-time');
  const appServiceSelect = document.getElementById('app-service-select');
  const appDurationInput = document.getElementById('app-duration');
  const appStationSelect = document.getElementById('app-station');
  const appCarPlateInput = document.getElementById('app-car-plate');
  const appClientAcronymInput = document.getElementById('app-client-acronym');
  const appAdvancedDetails = document.getElementById('app-advanced-details');
  const appClientNameInput = document.getElementById('app-client-name');
  const appClientPhoneInput = document.getElementById('app-client-phone');
  const appCarModelInput = document.getElementById('app-car-model');
  const appPriceInput = document.getElementById('app-price');
  const appStatusSelect = document.getElementById('app-status');
  const appNotesInput = document.getElementById('app-notes');
  const btnDeleteApp = document.getElementById('btn-delete-app');
  const btnSaveApp = document.getElementById('btn-save-app');
  const btnCancelApp = document.getElementById('btn-cancel-app');
  const btnCloseAppModal = document.getElementById('btn-close-app-modal');
  const btnFillNextSlot = document.getElementById('btn-fill-next-slot');

  // Elementy modala wyszukiwarki slotów
  const quickSlotModal = document.getElementById('quick-slot-modal');
  const quickServiceSelect = document.getElementById('quick-service-select');
  const quickStartDate = document.getElementById('quick-start-date');
  const quickResultBox = document.getElementById('quick-result-box');
  const quickResultText = document.getElementById('quick-result-text');
  const btnFindSlotAction = document.getElementById('btn-find-slot-action');
  const btnUseFoundSlot = document.getElementById('btn-use-found-slot');
  const btnCancelQuickSlot = document.getElementById('btn-cancel-quick-slot');
  const btnCloseQuickSlotModal = document.getElementById('btn-close-quick-slot-modal');

  // Elementy modala konfiguracji
  const calendarConfigModal = document.getElementById('calendar-config-modal');
  const monthsConfigTbody = document.getElementById('months-config-tbody');
  const servicesConfigTbody = document.getElementById('services-config-tbody');
  const btnCloseConfigModal = document.getElementById('btn-close-config-modal');
  const btnCancelConfig = document.getElementById('btn-cancel-config');
  const btnSaveConfig = document.getElementById('btn-save-config');

  // Formatowanie daty po polsku
  function formatPolishDateLong(dateStr) {
    if (!dateStr) return "";
    const [y, m, d] = dateStr.split('-').map(Number);
    const dateObj = new Date(y, m - 1, d);
    return dateObj.toLocaleDateString('pl-PL', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  // Sprawdzenie polskich świąt po stronie klienta (niezawodne nawet offline / bez node)
  function isPolishHolidayClient(dateStr) {
    const [yStr, mStr, dStr] = dateStr.split('-');
    const year = parseInt(yStr, 10);
    const month = parseInt(mStr, 10);
    const day = parseInt(dStr, 10);
    const md = `${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const fixed = ["01-01", "01-06", "05-01", "05-03", "08-15", "11-01", "11-11", "12-25", "12-26"];
    if (fixed.includes(md)) return true;

    // Wielkanoc (algorytm Meeusa/Gaussa dla kalendarza gregoriańskiego)
    const a = year % 19, b = Math.floor(year / 100), c = year % 100;
    const d = Math.floor(b / 4), e = b % 4, f = Math.floor((b + 8) / 25);
    const g = Math.floor((b - f + 1) / 3);
    const h = (19 * a + b - d - g + 15) % 30;
    const i = Math.floor(c / 4), k = c % 4;
    const l = (32 + 2 * e + 2 * i - h - k) % 7;
    const m = Math.floor((a + 11 * h + 22 * l) / 451);
    const eMonth = Math.floor((h + l - 7 * m + 114) / 31);
    const eDay = ((h + l - 7 * m + 114) % 31) + 1;
    const easter = new Date(Date.UTC(year, eMonth - 1, eDay));

    const addDays = (base, days) => {
      const res = new Date(base.getTime());
      res.setUTCDate(res.getUTCDate() + days);
      return `${String(res.getUTCMonth() + 1).padStart(2, '0')}-${String(res.getUTCDate()).padStart(2, '0')}`;
    };

    if (md === addDays(easter, 1) || md === addDays(easter, 60) || md === addDays(easter, 49)) {
      return true;
    }
    if (calendarConfigState.customHolidays && calendarConfigState.customHolidays.includes(dateStr)) {
      return true;
    }
    return false;
  }

  // Obliczenie godzin pracy po stronie klienta
  function getWorkingHoursClient(dateStr) {
    const [y, m, d] = dateStr.split('-').map(Number);
    const dObj = new Date(y, m - 1, d);
    const dow = dObj.getDay();
    if (dow === 0) return null; // Niedziela
    if (isPolishHolidayClient(dateStr)) return null; // Święto państwowe

    const mKey = String(m);
    const mCfg = (calendarConfigState.monthlyWorkingHours && calendarConfigState.monthlyWorkingHours[mKey])
      ? calendarConfigState.monthlyWorkingHours[mKey]
      : { start: "08:00", end: "18:00", saturdayStart: "08:00", saturdayEnd: "14:00", workSaturday: true };

    if (dow === 6) {
      if (!mCfg.workSaturday) return null;
      return { start: mCfg.saturdayStart || "08:00", end: mCfg.saturdayEnd || "14:00" };
    }
    return { start: mCfg.start || "08:00", end: mCfg.end || "18:00" };
  }

  // Pobranie konfiguracji kalendarza (z backendu lub statycznego pliku JSON)
  async function fetchCalendarConfig() {
    try {
      const res = await fetch('/api/calendar/config?t=' + Date.now());
      const ct = res.headers.get('content-type') || '';
      if (res.ok && ct.includes('application/json')) {
        const data = await res.json();
        if (data && data.services) {
          calendarConfigState = data;
        }
      } else {
        // Fallback do pliku public/calendar_config.json
        const sRes = await fetch('/calendar_config.json?t=' + Date.now());
        if (sRes.ok) {
          const sData = await sRes.json();
          if (sData && sData.services) {
            calendarConfigState = sData;
          }
        }
      }
    } catch (err) {
      console.warn("Użyto konfiguracji lokalnej:", err);
    }
    populateServicesDropdown();
  }

  // Wypełnienie listy usług w formularzu
  function populateServicesDropdown() {
    if (!calendarConfigState || !calendarConfigState.services) return;
    
    let html = '';
    calendarConfigState.services.forEach(srv => {
      html += `<option value="${srv.id}" data-dur="${srv.durationMinutes}" data-price="${srv.price}">
        ${srv.name} (~${srv.durationMinutes} min, ${srv.price} zł)
      </option>`;
    });

    if (appServiceSelect) appServiceSelect.innerHTML = html;
    if (quickServiceSelect) quickServiceSelect.innerHTML = html;
  }

  // Pobieranie wizyt dla danego dnia (API lub localStorage)
  async function fetchAppointmentsForDay(dateStr) {
    try {
      const res = await fetch(`/api/calendar/appointments?date=${dateStr}`);
      const ct = res.headers.get('content-type') || '';
      if (res.ok && ct.includes('application/json')) {
        const data = await res.json();
        if (Array.isArray(data)) {
          return data.sort((a, b) => (a.startTime || '').localeCompare(b.startTime || ''));
        }
      }
    } catch (err) {}

    // Fallback: localStorage
    try {
      const local = localStorage.getItem('tire_calendar_appointments');
      if (local) {
        const all = JSON.parse(local);
        return all
          .filter(a => a.date === dateStr)
          .sort((a, b) => (a.startTime || '').localeCompare(b.startTime || ''));
      }
    } catch (e) {}

    return [];
  }

  // Załadowanie danego dnia w kalendarzu
  async function loadCalendarDay(dateStr) {
    calendarSelectedDate = dateStr;
    if (calDatePicker) calDatePicker.value = dateStr;
    if (calSelectedDateLabel) calSelectedDateLabel.textContent = formatPolishDateLong(dateStr);

    // Sprawdzenie godzin pracy i świąt
    const workHours = getWorkingHoursClient(dateStr);
    const isHoliday = isPolishHolidayClient(dateStr);
    const [y, m, d] = dateStr.split('-').map(Number);
    const isSunday = new Date(y, m - 1, d).getDay() === 0;

    if (!workHours) {
      if (calClosedAlert) {
        calClosedAlert.style.display = 'block';
        if (isHoliday) {
          calClosedAlert.innerHTML = `⚠️ <strong>Święto państwowe w Polsce</strong> - w tym dniu zakład jest nieczynny. Możesz jednak ręcznie zapisać wizytę w razie wyjątku.`;
        } else if (isSunday) {
          calClosedAlert.innerHTML = `⚠️ <strong>Niedziela</strong> - zakład jest nieczynny. Możesz jednak ręcznie zapisać wizytę w razie wyjątku.`;
        } else {
          calClosedAlert.innerHTML = `⚠️ Zakład jest w tym dniu nieczynny.`;
        }
      }
      if (calDayStatusPill) {
        calDayStatusPill.textContent = "Dzień wolny";
        calDayStatusPill.style.color = "#f87171";
        calDayStatusPill.style.background = "rgba(239, 68, 68, 0.15)";
      }
      if (calHoursInfo) calHoursInfo.textContent = "🕒 Dziś nieczynne";
    } else {
      if (calClosedAlert) calClosedAlert.style.display = 'none';
      if (calDayStatusPill) {
        calDayStatusPill.textContent = "Dzień roboczy";
        calDayStatusPill.style.color = "#10b981";
        calDayStatusPill.style.background = "rgba(16, 185, 129, 0.15)";
      }
      const seasonNote = (calendarConfigState.monthlyWorkingHours && calendarConfigState.monthlyWorkingHours[String(m)] && calendarConfigState.monthlyWorkingHours[String(m)].note)
        ? ` (${calendarConfigState.monthlyWorkingHours[String(m)].note})` : '';
      if (calHoursInfo) calHoursInfo.textContent = `🕒 Godziny pracy: ${workHours.start} - ${workHours.end}${seasonNote}`;
    }

    // Pobieramy wizyty
    calendarAppointmentsState = await fetchAppointmentsForDay(dateStr);

    if (calAppointmentsCount) {
      calAppointmentsCount.textContent = `Zaplanowanych aut: ${calendarAppointmentsState.length}`;
    }

    renderTimelineForStation(1, timelineSt1, countSt1);
    renderTimelineForStation(2, timelineSt2, countSt2);
  }

  // Renderowanie osi czasu dla danego stanowiska (1 lub 2)
  function renderTimelineForStation(stationNum, containerEl, countEl) {
    if (!containerEl) return;
    const stationApps = calendarAppointmentsState
      .filter(a => a.station === stationNum)
      .sort((a, b) => (a.startTime || '').localeCompare(b.startTime || ''));
    if (countEl) countEl.textContent = `${stationApps.length} aut`;

    if (stationApps.length === 0) {
      containerEl.innerHTML = `
        <div class="empty-station-notice">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          <p>Brak zaplanowanych wizyt na tym stanowisku.</p>
          <button class="btn btn-secondary btn-sm" onclick="window.calendarModule.newAppForStation(${stationNum})">+ Zaplanuj tutaj</button>
        </div>
      `;
      return;
    }

    let html = '';
    stationApps.forEach(app => {
      const isCompleted = app.status === 'completed';
      const isCancelled = app.status === 'cancelled';
      const statusClass = isCompleted ? 'status-completed' : (isCancelled ? 'status-cancelled' : '');
      const stationClass = stationNum === 2 ? 'station-2-card' : '';

      let statusBadge = '<span class="app-status-badge badge-scheduled">Zaplanowana</span>';
      if (isCompleted) statusBadge = '<span class="app-status-badge badge-completed">✓ Zrealizowana</span>';
      if (isCancelled) statusBadge = '<span class="app-status-badge badge-cancelled">Odwołana</span>';

      html += `
        <div class="app-card ${stationClass} ${statusClass}" data-id="${app.id}" onclick="window.calendarModule.editApp('${app.id}')" style="cursor: pointer;" title="Kliknij wizytę, aby edytować">
          <div class="app-card-top">
            <div>
              <span class="app-time-badge">${app.startTime} - ${app.endTime}</span>
              <span class="app-duration-pill">(${app.durationMinutes} min)</span>
            </div>
            <div>${statusBadge}</div>
          </div>

          <div class="app-card-main">
            <div style="display: flex; align-items: center; gap: 6px;">
              <span class="app-plate">${app.carLicensePlate || 'BRAK NR'}</span>
              ${app.clientAcronym ? `<span style="background: rgba(56, 189, 248, 0.2); color: var(--color-primary); padding: 2px 7px; border-radius: 4px; font-weight: 700; font-size: 13px; letter-spacing: 0.5px;">${app.clientAcronym}</span>` : ''}
            </div>
            <div style="text-align: right;">
              <span class="app-client">${app.clientName || ''}</span>
              ${app.clientPhone ? `<span class="app-phone"> | 📞 ${app.clientPhone}</span>` : ''}
            </div>
          </div>

          <div class="app-service-info">
            <span>🔧 ${app.serviceName || 'Wymiana opon'}</span>
            ${app.carModel ? `<span style="color: var(--text-secondary);">(${app.carModel})</span>` : ''}
            ${app.price ? `<strong style="margin-left: auto; color: var(--color-success);">${app.price} zł</strong>` : ''}
          </div>

          ${app.notes ? `<div class="app-notes">💬 ${app.notes}</div>` : ''}

          <div class="app-card-actions">
            <button class="app-btn-icon" title="Oznacz jako wykonana/zaplanowana" onclick="event.stopPropagation(); window.calendarModule.toggleStatus('${app.id}')">
              ${isCompleted ? '↩ Przywróć' : '✓ Gotowe'}
            </button>
            <button class="app-btn-icon app-btn-copy" title="Skopiuj to zlecenie na inny termin lub stanowisko" onclick="event.stopPropagation(); window.calendarModule.copyApp('${app.id}')">
              📋 Kopiuj
            </button>
            <button class="app-btn-icon" title="Edytuj dane wizyty" onclick="event.stopPropagation(); window.calendarModule.editApp('${app.id}')">
              ✏️ Edytuj
            </button>
            <button class="app-btn-icon app-btn-delete" title="Usuń wizytę z kalendarza" onclick="event.stopPropagation(); window.calendarModule.deleteApp('${app.id}')">
              🗑️
            </button>
          </div>
        </div>
      `;
    });

    containerEl.innerHTML = html;
  }

  // Otwarcie modala dodawania/edycji wizyty
  function openAppointmentModal(appData = null, isCopy = false) {
    if (!appForm) return;
    appForm.reset();

    // Domyślny czas i data
    appDateInput.value = calendarSelectedDate;
    const now = new Date();
    const defaultTime = `${String(now.getHours()).padStart(2, '0')}:00`;
    appStartTimeInput.value = defaultTime;
    appDurationInput.value = 45;
    appStationSelect.value = "1";
    appStatusSelect.value = "scheduled";

    // Szczegóły zaawansowane zwijamy domyślnie pod telefon
    if (appAdvancedDetails) appAdvancedDetails.open = false;

    if (btnDeleteApp) btnDeleteApp.style.display = 'none';

    // Upewnijmy się, że opcje usług są zawsze dostępne
    if (appServiceSelect.options.length === 0) {
      populateServicesDropdown();
    }

    if (appData) {
      if (isCopy) {
        appIdInput.value = "";
        if (appModalTitle) appModalTitle.textContent = "📋 Skopiuj Wizytę (Nowy Termin)";
        appDateInput.value = calendarSelectedDate;
        appStartTimeInput.value = appData.startTime || defaultTime;
        appDurationInput.value = appData.durationMinutes || 45;
        appStationSelect.value = appData.station === 1 ? "2" : "1";
        appCarPlateInput.value = appData.carLicensePlate || "";
        if (appClientAcronymInput) appClientAcronymInput.value = appData.clientAcronym || "";
        appClientNameInput.value = appData.clientName || "";
        appClientPhoneInput.value = appData.clientPhone || "";
        appCarModelInput.value = appData.carModel || "";
        appServiceSelect.value = appData.serviceId || (appServiceSelect.options[0] ? appServiceSelect.options[0].value : "");
        appPriceInput.value = appData.price || 140;
        appNotesInput.value = appData.notes || "";
      } else {
        appIdInput.value = appData.id;
        if (appModalTitle) appModalTitle.textContent = "✏️ Edycja Wizyty";
        if (btnDeleteApp) btnDeleteApp.style.display = 'inline-block';
        
        appDateInput.value = appData.date;
        appStartTimeInput.value = appData.startTime;
        appDurationInput.value = appData.durationMinutes;
        appStationSelect.value = String(appData.station);
        appCarPlateInput.value = appData.carLicensePlate || "";
        if (appClientAcronymInput) appClientAcronymInput.value = appData.clientAcronym || "";
        appClientNameInput.value = appData.clientName || "";
        appClientPhoneInput.value = appData.clientPhone || "";
        appCarModelInput.value = appData.carModel || "";
        appServiceSelect.value = appData.serviceId || "";
        appPriceInput.value = appData.price || 0;
        appStatusSelect.value = appData.status || "scheduled";
        appNotesInput.value = appData.notes || "";

        // Jeśli są notatki lub telefon, rozwiń sekcję dla wygody
        if (appData.notes || appData.clientPhone) {
          if (appAdvancedDetails) appAdvancedDetails.open = true;
        }
      }
    } else {
      appIdInput.value = "";
      if (appClientAcronymInput) appClientAcronymInput.value = "";
      if (appModalTitle) appModalTitle.textContent = "Zaplanuj Nową Wizytę";
      if (appServiceSelect && appServiceSelect.options.length > 0) {
        appServiceSelect.selectedIndex = 0;
        const opt = appServiceSelect.options[0];
        appDurationInput.value = opt.getAttribute('data-dur') || 45;
        appPriceInput.value = opt.getAttribute('data-price') || 120;
      }
    }

    if (appointmentModal) appointmentModal.classList.add('active');
  }

  function closeAppointmentModal() {
    if (appointmentModal) appointmentModal.classList.remove('active');
  }

  // Zapisanie wizyty (API + localStorage fallback)
  async function saveAppointment() {
    const id = appIdInput.value;
    const date = appDateInput.value;
    const startTime = appStartTimeInput.value;
    const durationMinutes = parseInt(appDurationInput.value, 10) || 45;
    const station = parseInt(appStationSelect.value, 10) || 1;
    const carLicensePlate = appCarPlateInput.value.trim().toUpperCase();
    const clientAcronym = appClientAcronymInput ? appClientAcronymInput.value.trim().toUpperCase() : "";
    const clientName = appClientNameInput.value.trim();
    const clientPhone = appClientPhoneInput.value.trim();
    const carModel = appCarModelInput.value.trim();
    const price = parseFloat(appPriceInput.value) || 0;
    const status = appStatusSelect.value;
    const notes = appNotesInput.value.trim();

    const selectedOpt = appServiceSelect.options[appServiceSelect.selectedIndex];
    const serviceId = selectedOpt ? selectedOpt.value : "custom";
    const serviceName = selectedOpt ? selectedOpt.text.split('(~')[0].trim() : "Wymiana opon";

    // Obliczenie endTime
    const [sh, sm] = startTime.split(':').map(Number);
    const endMins = (sh * 60 + sm) + durationMinutes;
    const endTime = `${String(Math.floor(endMins / 60)).padStart(2, '0')}:${String(endMins % 60).padStart(2, '0')}`;

    if (!date || !startTime) {
      alert("Proszę podać datę oraz godzinę rozpoczęcia wizyty.");
      return;
    }
    if (!carLicensePlate) {
      alert("Proszę podać numer rejestracyjny pojazdu.");
      return;
    }

    const payload = {
      date,
      startTime,
      endTime,
      durationMinutes,
      station,
      serviceId,
      serviceName,
      carLicensePlate,
      clientAcronym,
      clientName,
      clientPhone,
      carModel,
      price,
      status,
      notes
    };

    // 1. Spróbuj wysłać do backendu
    try {
      const url = id ? `/api/calendar/appointments/${id}` : '/api/calendar/appointments';
      const method = id ? 'PUT' : 'POST';
      await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch (err) {}

    // 2. Zapisz w localStorage (zapewnia działanie nawet pod starym .exe)
    try {
      const local = localStorage.getItem('tire_calendar_appointments');
      let all = local ? JSON.parse(local) : [];
      if (id) {
        const idx = all.findIndex(a => a.id === id);
        if (idx !== -1) all[idx] = { ...all[idx], ...payload, id };
        else all.push({ ...payload, id });
      } else {
        const newId = 'app_' + Date.now();
        all.push({ ...payload, id: newId });
      }
      localStorage.setItem('tire_calendar_appointments', JSON.stringify(all));
    } catch(e) {}

    closeAppointmentModal();
    loadCalendarDay(date);
  }

  // Zmiana statusu na wykonana / zaplanowana
  async function toggleStatus(appId) {
    const app = calendarAppointmentsState.find(a => a.id === appId);
    if (!app) return;
    const newStatus = app.status === 'completed' ? 'scheduled' : 'completed';
    
    try {
      await fetch(`/api/calendar/appointments/${appId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
    } catch (err) {}

    try {
      const local = localStorage.getItem('tire_calendar_appointments');
      if (local) {
        let all = JSON.parse(local);
        const a = all.find(x => x.id === appId);
        if (a) a.status = newStatus;
        localStorage.setItem('tire_calendar_appointments', JSON.stringify(all));
      }
    } catch(e) {}

    loadCalendarDay(calendarSelectedDate);
  }

  // Usunięcie wizyty
  async function deleteApp(appId) {
    if (!confirm("Czy na pewno chcesz usunąć tę wizytę z kalendarza?")) return;
    try {
      await fetch(`/api/calendar/appointments/${appId}`, { method: 'DELETE' });
    } catch (err) {}

    try {
      const local = localStorage.getItem('tire_calendar_appointments');
      if (local) {
        let all = JSON.parse(local);
        all = all.filter(a => a.id !== appId);
        localStorage.setItem('tire_calendar_appointments', JSON.stringify(all));
      }
    } catch(e) {}

    closeAppointmentModal();
    loadCalendarDay(calendarSelectedDate);
  }

  // Algorytm znajdowania pierwszego wolnego slotu po stronie klienta
  function findFirstAvailableSlotClient(durationMinutes, startDateStr, preferredStation = null) {
    const step = calendarConfigState.slotDurationMinutes || 15;
    const dur = parseInt(durationMinutes, 10) || 45;
    const stations = calendarConfigState.stationsCount || 2;
    const now = new Date();
    const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    let checkDateStr = startDateStr && startDateStr >= todayStr ? startDateStr : todayStr;

    let allApps = [];
    try {
      const local = localStorage.getItem('tire_calendar_appointments');
      if (local) allApps = JSON.parse(local);
    } catch(e) {}

    for (let dayOffset = 0; dayOffset < 45; dayOffset++) {
      const cur = new Date(checkDateStr + "T00:00:00");
      cur.setDate(cur.getDate() + dayOffset);
      const dStr = `${cur.getFullYear()}-${String(cur.getMonth() + 1).padStart(2, '0')}-${String(cur.getDate()).padStart(2, '0')}`;

      const workH = getWorkingHoursClient(dStr);
      if (!workH) continue;

      const [sh, sm] = workH.start.split(':').map(Number);
      const [eh, em] = workH.end.split(':').map(Number);
      const dayStart = sh * 60 + sm;
      const dayEnd = eh * 60 + em;

      let startFrom = dayStart;
      if (dStr === todayStr) {
        const curMins = now.getHours() * 60 + now.getMinutes();
        startFrom = Math.max(dayStart, Math.ceil((curMins + 15) / step) * step);
      }

      const dayApps = allApps.filter(a => a.date === dStr && a.status !== 'cancelled');

      // Jeśli podano preferowane stanowisko (np. 1 lub 2), sprawdzamy tylko to stanowisko
      const stationsToCheck = preferredStation ? [parseInt(preferredStation, 10)] : [1, 2];

      for (let s = startFrom; s + dur <= dayEnd; s += step) {
        const e = s + dur;
        for (let st of stationsToCheck) {
          const coll = dayApps.some(a => {
            if (a.station !== st) return false;
            const [ash, asm] = a.startTime.split(':').map(Number);
            const [aeh, aem] = a.endTime.split(':').map(Number);
            return (ash * 60 + asm) < e && (aeh * 60 + aem) > s;
          });
          if (!coll) {
            const formatT = (m) => `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`;
            return {
              date: dStr,
              startTime: formatT(s),
              endTime: formatT(e),
              durationMinutes: dur,
              station: st
            };
          }
        }
      }
    }
    return null;
  }

  // Wypełnienie najbliższym wolnym terminem bezpośrednio w formularzu
  async function fillNextAvailableSlotInForm() {
    const dur = parseInt(appDurationInput.value, 10) || 45;
    const startDate = appDateInput.value || calendarSelectedDate;
    
    let slot = null;
    try {
      const res = await fetch(`/api/calendar/first-available?duration=${dur}&date=${startDate}`);
      const ct = res.headers.get('content-type') || '';
      if (res.ok && ct.includes('application/json')) {
        slot = await res.json();
      }
    } catch (err) {}

    if (!slot) {
      slot = findFirstAvailableSlotClient(dur, startDate);
    }

    if (!slot) {
      alert("Nie znaleziono wolnego terminu w najbliższym czasie.");
      return;
    }

    appDateInput.value = slot.date;
    appStartTimeInput.value = slot.startTime;
    appStationSelect.value = String(slot.station);
    alert(`Znaleziono i ustawiono wolny termin:\nData: ${slot.date}\nGodzina: ${slot.startTime} - ${slot.endTime}\nStanowisko: ${slot.station}`);
  }

  // Obsługa asystenta szybkiego wolnego terminu (Quick Slot Modal)
  function openQuickSlotModal() {
    if (quickStartDate) quickStartDate.value = calendarSelectedDate;
    if (quickResultBox) quickResultBox.style.display = 'none';
    if (btnUseFoundSlot) btnUseFoundSlot.style.display = 'none';
    foundQuickSlot = null;
    if (quickServiceSelect.options.length === 0) populateServicesDropdown();
    if (quickSlotModal) quickSlotModal.classList.add('active');
  }

  function closeQuickSlotModal() {
    if (quickSlotModal) quickSlotModal.classList.remove('active');
  }

  async function executeQuickFindSlot() {
    const durRadio = document.querySelector('input[name="quick-dur"]:checked');
    const duration = durRadio ? parseInt(durRadio.value, 10) : 45;
    const startD = quickStartDate ? quickStartDate.value : calendarSelectedDate;

    let slot = null;
    try {
      const res = await fetch(`/api/calendar/first-available?duration=${duration}&date=${startD}`);
      const ct = res.headers.get('content-type') || '';
      if (res.ok && ct.includes('application/json')) {
        slot = await res.json();
      }
    } catch (err) {}

    if (!slot) {
      slot = findFirstAvailableSlotClient(duration, startD);
    }

    if (!slot) {
      alert("Brak wolnych terminów w najbliższym okresie.");
      return;
    }

    foundQuickSlot = slot;

    if (quickResultBox && quickResultText) {
      quickResultBox.style.display = 'block';
      quickResultText.innerHTML = `
        📅 <strong>${formatPolishDateLong(foundQuickSlot.date)}</strong><br>
        ⏰ Godziny: <strong>${foundQuickSlot.startTime} - ${foundQuickSlot.endTime}</strong> (${foundQuickSlot.durationMinutes} min)<br>
        🚗 Stanowisko: <strong>Stanowisko ${foundQuickSlot.station}</strong> (Podnośnik ${foundQuickSlot.station === 1 ? 'A' : 'B'})
      `;
    }
    if (btnUseFoundSlot) btnUseFoundSlot.style.display = 'inline-block';
  }

  function useFoundQuickSlotAction() {
    if (!foundQuickSlot) return;
    closeQuickSlotModal();
    openAppointmentModal();
    appDateInput.value = foundQuickSlot.date;
    appStartTimeInput.value = foundQuickSlot.startTime;
    appDurationInput.value = foundQuickSlot.durationMinutes;
    appStationSelect.value = String(foundQuickSlot.station);
  }

  // Obsługa modala konfiguracji godzin pracy i usług
  async function openConfigModal() {
    renderConfigModalData();
    if (calendarConfigModal) calendarConfigModal.classList.add('active');
  }

  function closeConfigModal() {
    if (calendarConfigModal) calendarConfigModal.classList.remove('active');
  }

  const MONTH_NAMES = [
    "1. Styczeń", "2. Luty", "3. Marzec", "4. Kwiecień", "5. Maj", "6. Czerwiec",
    "7. Lipiec", "8. Sierpień", "9. Wrzesień", "10. Październik", "11. Listopad", "12. Grudzień"
  ];

  function renderConfigModalData() {
    if (!calendarConfigState) {
      calendarConfigState = JSON.parse(JSON.stringify(DEFAULT_CALENDAR_CONFIG));
    }

    // Nagłówek publiczny
    const cfgPublicHeader = document.getElementById('cfg-public-header');
    if (cfgPublicHeader) {
      cfgPublicHeader.value = calendarConfigState.publicHeader || "Wulkanizacja Michał - rezerwacja terminu 600223669";
    }

    // Dozwolone emaile
    const cfgAllowedEmails = document.getElementById('cfg-allowed-emails');
    if (cfgAllowedEmails) {
      const emails = calendarConfigState.allowedEmails || ["michal@wulkanizacja.pl", "biuro@4kola.pl", "admin@warsztat.pl"];
      cfgAllowedEmails.value = Array.isArray(emails) ? emails.join(', ') : emails;
    }

    // Hasło do panelu warsztatu
    const cfgAdminPassword = document.getElementById('cfg-admin-password');
    if (cfgAdminPassword) {
      cfgAdminPassword.value = calendarConfigState.adminPassword || "admin";
    }

    // Tabela miesięcy
    if (monthsConfigTbody) {
      let mHtml = '';
      for (let m = 1; m <= 12; m++) {
        const mKey = String(m);
        const mCfg = (calendarConfigState.monthlyWorkingHours && calendarConfigState.monthlyWorkingHours[mKey]) 
          ? calendarConfigState.monthlyWorkingHours[mKey] 
          : { start: "08:00", end: "18:00", saturdayStart: "08:00", saturdayEnd: "14:00", note: "" };

        mHtml += `
          <tr data-month="${m}">
            <td><strong>${MONTH_NAMES[m - 1]}</strong></td>
            <td><input type="time" class="cfg-m-start" value="${mCfg.start || '08:00'}" style="padding: 4px; font-size: 12px; background: var(--bg-primary); color: #fff; border: 1px solid var(--border-color); border-radius: 4px;"></td>
            <td><input type="time" class="cfg-m-end" value="${mCfg.end || '18:00'}" style="padding: 4px; font-size: 12px; background: var(--bg-primary); color: #fff; border: 1px solid var(--border-color); border-radius: 4px;"></td>
            <td><input type="time" class="cfg-m-sat-start" value="${mCfg.saturdayStart || '08:00'}" style="padding: 4px; font-size: 12px; background: var(--bg-primary); color: #fff; border: 1px solid var(--border-color); border-radius: 4px;"></td>
            <td><input type="time" class="cfg-m-sat-end" value="${mCfg.saturdayEnd || '14:00'}" style="padding: 4px; font-size: 12px; background: var(--bg-primary); color: #fff; border: 1px solid var(--border-color); border-radius: 4px;"></td>
            <td><input type="text" class="cfg-m-note" value="${mCfg.note || ''}" placeholder="np. Sezon" style="padding: 4px; font-size: 12px; width: 100%; background: var(--bg-primary); color: #fff; border: 1px solid var(--border-color); border-radius: 4px;"></td>
          </tr>
        `;
      }
      monthsConfigTbody.innerHTML = mHtml;
    }

    // Tabela usług
    if (servicesConfigTbody && calendarConfigState.services) {
      let sHtml = '';
      calendarConfigState.services.forEach(srv => {
        sHtml += `
          <tr data-srv-id="${srv.id}">
            <td><input type="text" class="cfg-srv-name" value="${srv.name}" style="padding: 4px; font-size: 12px; width: 100%; background: var(--bg-primary); color: #fff; border: 1px solid var(--border-color); border-radius: 4px;"></td>
            <td><input type="number" class="cfg-srv-dur" value="${srv.durationMinutes}" min="15" max="180" step="5" style="padding: 4px; font-size: 12px; width: 80px; background: var(--bg-primary); color: #fff; border: 1px solid var(--border-color); border-radius: 4px;"> min</td>
            <td><input type="number" class="cfg-srv-price" value="${srv.price}" min="0" step="5" style="padding: 4px; font-size: 12px; width: 80px; background: var(--bg-primary); color: #fff; border: 1px solid var(--border-color); border-radius: 4px;"> zł</td>
          </tr>
        `;
      });
      servicesConfigTbody.innerHTML = sHtml;
    }
  }

  async function saveConfigData() {
    if (!calendarConfigState) calendarConfigState = JSON.parse(JSON.stringify(DEFAULT_CALENDAR_CONFIG));

    // Zbieramy miesiące
    const newMonthly = {};
    if (monthsConfigTbody) {
      monthsConfigTbody.querySelectorAll('tr').forEach(tr => {
        const m = tr.getAttribute('data-month');
        newMonthly[m] = {
          start: tr.querySelector('.cfg-m-start').value || "08:00",
          end: tr.querySelector('.cfg-m-end').value || "18:00",
          saturdayStart: tr.querySelector('.cfg-m-sat-start').value || "08:00",
          saturdayEnd: tr.querySelector('.cfg-m-sat-end').value || "14:00",
          workSaturday: true,
          note: tr.querySelector('.cfg-m-note').value || ""
        };
      });
    }

    // Zbieramy usługi
    const newServices = [];
    if (servicesConfigTbody) {
      servicesConfigTbody.querySelectorAll('tr').forEach(tr => {
        const id = tr.getAttribute('data-srv-id');
        newServices.push({
          id: id,
          name: tr.querySelector('.cfg-srv-name').value,
          durationMinutes: parseInt(tr.querySelector('.cfg-srv-dur').value, 10) || 45,
          price: parseFloat(tr.querySelector('.cfg-srv-price').value) || 0
        });
      });
    }

    // Pobieramy nagłówek
    const cfgPublicHeader = document.getElementById('cfg-public-header');
    if (cfgPublicHeader) {
      calendarConfigState.publicHeader = cfgPublicHeader.value.trim() || "Wulkanizacja Michał - rezerwacja terminu 600223669";
    }

    // Pobieramy dozwolone emaile
    const cfgAllowedEmails = document.getElementById('cfg-allowed-emails');
    if (cfgAllowedEmails) {
      const raw = cfgAllowedEmails.value;
      const parsedEmails = raw
        .split(/[\n,;]+/)
        .map(e => e.trim().toLowerCase())
        .filter(e => e.length > 0 && e.includes('@'));
      calendarConfigState.allowedEmails = parsedEmails.length > 0 ? parsedEmails : ["michal@wulkanizacja.pl", "admin@warsztat.pl"];
    }

    // Pobieramy hasło do panelu warsztatu
    const cfgAdminPassword = document.getElementById('cfg-admin-password');
    if (cfgAdminPassword) {
      calendarConfigState.adminPassword = cfgAdminPassword.value.trim() || "admin";
    }

    calendarConfigState.monthlyWorkingHours = newMonthly;
    calendarConfigState.services = newServices;

    // Zapis do localStorage
    localStorage.setItem('tire_calendar_config', JSON.stringify(calendarConfigState));

    // Zapis do backendu (jeśli dostępny)
    try {
      await fetch('/api/calendar/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(calendarConfigState)
      });
    } catch (err) {}

    alert("Konfiguracja kalendarza została pomyślnie zapisana!");
    closeConfigModal();
    populateServicesDropdown();
    loadCalendarDay(calendarSelectedDate);
  }

  // Rejestracja globalnego modułu dla wywołań inline onclick
  window.calendarModule = {
    newAppForStation: (st) => {
      openAppointmentModal();
      if (appStationSelect) appStationSelect.value = String(st);
    },
    editApp: (id) => {
      const app = calendarAppointmentsState.find(a => a.id === id);
      if (app) openAppointmentModal(app, false);
    },
    copyApp: (id) => {
      const app = calendarAppointmentsState.find(a => a.id === id);
      if (app) openAppointmentModal(app, true);
    },
    deleteApp: (id) => {
      deleteApp(id);
    },
    toggleStatus: (id) => {
      toggleStatus(id);
    }
  };

  // Rejestracja zdarzeń interfejsu kalendarza
  if (calPrevDay) {
    calPrevDay.addEventListener('click', () => {
      const d = new Date(calendarSelectedDate);
      d.setDate(d.getDate() - 1);
      loadCalendarDay(d.toISOString().split('T')[0]);
    });
  }

  if (calNextDay) {
    calNextDay.addEventListener('click', () => {
      const d = new Date(calendarSelectedDate);
      d.setDate(d.getDate() + 1);
      loadCalendarDay(d.toISOString().split('T')[0]);
    });
  }

  if (calToday) {
    calToday.addEventListener('click', () => {
      loadCalendarDay(new Date().toISOString().split('T')[0]);
    });
  }

  if (calDatePicker) {
    calDatePicker.addEventListener('change', (e) => {
      if (e.target.value) loadCalendarDay(e.target.value);
    });
  }

  if (btnAddAppointment) {
    btnAddAppointment.addEventListener('click', () => openAppointmentModal());
  }

  if (btnCancelApp) btnCancelApp.addEventListener('click', closeAppointmentModal);
  if (btnCloseAppModal) btnCloseAppModal.addEventListener('click', closeAppointmentModal);
  if (btnSaveApp) btnSaveApp.addEventListener('click', saveAppointment);
  if (btnDeleteApp) {
    btnDeleteApp.addEventListener('click', () => {
      const id = appIdInput.value;
      if (id) deleteApp(id);
    });
  }
  if (btnFillNextSlot) btnFillNextSlot.addEventListener('click', fillNextAvailableSlotInForm);

  // Przyciski szybkiego czasu w formularzu (30m, 45m, 60m)
  document.querySelectorAll('.btn-set-dur').forEach(b => {
    b.addEventListener('click', () => {
      const dur = b.getAttribute('data-dur');
      if (appDurationInput) appDurationInput.value = dur;
    });
  });

  // Zmiana usługi automatycznie ustawia czas i cenę
  if (appServiceSelect) {
    appServiceSelect.addEventListener('change', () => {
      const opt = appServiceSelect.options[appServiceSelect.selectedIndex];
      if (opt) {
        const d = opt.getAttribute('data-dur');
        const p = opt.getAttribute('data-price');
        if (d && appDurationInput) appDurationInput.value = d;
        if (p && appPriceInput) appPriceInput.value = p;
      }
    });
  }

  // Wyszukiwarka slotów
  if (btnQuickFindSlot) btnQuickFindSlot.addEventListener('click', openQuickSlotModal);
  if (btnCancelQuickSlot) btnCancelQuickSlot.addEventListener('click', closeQuickSlotModal);
  if (btnCloseQuickSlotModal) btnCloseQuickSlotModal.addEventListener('click', closeQuickSlotModal);
  if (btnFindSlotAction) btnFindSlotAction.addEventListener('click', executeQuickFindSlot);
  if (btnUseFoundSlot) btnUseFoundSlot.addEventListener('click', useFoundQuickSlotAction);

  // Synchronizacja usługi w Quick Slot Modal z radio buttonami czasu
  if (quickServiceSelect) {
    quickServiceSelect.addEventListener('change', () => {
      const opt = quickServiceSelect.options[quickServiceSelect.selectedIndex];
      if (opt) {
        const d = opt.getAttribute('data-dur');
        const radio = document.querySelector(`input[name="quick-dur"][value="${d}"]`);
        if (radio) radio.checked = true;
      }
    });
  }

  // Modal konfiguracji
  if (btnOpenConfigModal) btnOpenConfigModal.addEventListener('click', openConfigModal);
  if (btnCloseConfigModal) btnCloseConfigModal.addEventListener('click', closeConfigModal);
  if (btnCancelConfig) btnCancelConfig.addEventListener('click', closeConfigModal);
  if (btnSaveConfig) btnSaveConfig.addEventListener('click', saveConfigData);

  // Wylogowanie administratora do widoku publicznego kalendarza
  const btnAdminLogout = document.getElementById('btn-admin-logout');
  if (btnAdminLogout) {
    btnAdminLogout.addEventListener('click', () => {
      if (confirm("Czy na pewno chcesz się wylogować i powrócić do widoku publicznego kalendarza?")) {
        sessionStorage.removeItem('tire_admin_logged');
        localStorage.removeItem('tire_admin_logged');
        window.location.replace('/kalendarz.html');
      }
    });
  }

  // =========================================================================
  // 8B. MODUŁ ASYSTENTA AI (GOOGLE GEMINI STUDIO + STEROWANIE GŁOSOWE)
  // =========================================================================
  const btnOpenAiModal = document.getElementById('btn-open-ai-modal');
  const aiAgentModal = document.getElementById('ai-agent-modal');
  const btnCloseAiModal = document.getElementById('btn-close-ai-modal');
  const btnToggleKeyInput = document.getElementById('btn-toggle-key-input');
  const aiKeyInputRow = document.getElementById('ai-key-input-row');
  const aiGeminiKeyInput = document.getElementById('ai-gemini-key-input');
  const btnSaveAiKey = document.getElementById('btn-save-ai-key');
  const aiKeyStatus = document.getElementById('ai-key-status');
  const btnAiMic = document.getElementById('btn-ai-mic');
  const aiMicLabel = document.getElementById('ai-mic-label');
  const aiPromptInput = document.getElementById('ai-prompt-input');
  const btnExecuteAiPlan = document.getElementById('btn-execute-ai-plan');
  const btnClearAiPrompt = document.getElementById('btn-clear-ai-prompt');
  const aiLoadingBox = document.getElementById('ai-loading-box');
  const aiLoadingText = document.getElementById('ai-loading-text');
  const aiResultBox = document.getElementById('ai-result-box');
  const aiResultTitle = document.getElementById('ai-result-title');
  const aiResultMessage = document.getElementById('ai-result-message');
  const aiResultDetails = document.getElementById('ai-result-details');
  const btnAiConfirmSave = document.getElementById('btn-ai-confirm-save');
  const btnAiCancelRes = document.getElementById('btn-ai-cancel-res');

  let proposedAiAppointment = null;
  let isSpeechListening = false;
  let speechRecognition = null;

  // Inicjalizacja Web Speech API
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRec) {
    speechRecognition = new SpeechRec();
    speechRecognition.lang = 'pl-PL';
    speechRecognition.interimResults = true;
    speechRecognition.continuous = false;

    speechRecognition.onstart = () => {
      isSpeechListening = true;
      if (btnAiMic) btnAiMic.classList.add('listening');
      if (aiMicLabel) {
        aiMicLabel.textContent = "🎙️ Słucham... Mów teraz swoje polecenie";
        aiMicLabel.style.color = "#ef4444";
      }
    };

    speechRecognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      if (aiPromptInput) aiPromptInput.value = transcript;
    };

    speechRecognition.onerror = (event) => {
      console.warn("Błąd mikrofonu:", event.error);
      isSpeechListening = false;
      if (btnAiMic) btnAiMic.classList.remove('listening');
      if (aiMicLabel) {
        aiMicLabel.textContent = `Błąd mikrofonu (${event.error}). Możesz wpisać tekst poniżej.`;
        aiMicLabel.style.color = "#f59e0b";
      }
    };

    speechRecognition.onend = () => {
      isSpeechListening = false;
      if (btnAiMic) btnAiMic.classList.remove('listening');
      if (aiMicLabel) {
        aiMicLabel.textContent = "Zakończono nagrywanie. Kliknij 'Wykonaj polecenie z Gemini'";
        aiMicLabel.style.color = "var(--color-primary)";
      }
    };
  }

  function updateAiKeyStatus() {
    const key = localStorage.getItem('gemini_api_key') || "";
    if (aiKeyStatus) {
      if (key && key.trim().length > 10) {
        aiKeyStatus.textContent = "Zapisany ✓";
        aiKeyStatus.style.background = "#10b981";
      } else {
        aiKeyStatus.textContent = "Nieskonfigurowany";
        aiKeyStatus.style.background = "#ef4444";
      }
    }
  }

  function openAiModal() {
    updateAiKeyStatus();
    if (aiResultBox) aiResultBox.style.display = 'none';
    if (aiLoadingBox) aiLoadingBox.style.display = 'none';
    proposedAiAppointment = null;
    const key = localStorage.getItem('gemini_api_key') || "";
    if (!key && aiKeyInputRow) {
      aiKeyInputRow.style.display = 'flex';
    }
    if (aiAgentModal) aiAgentModal.classList.add('active');
  }

  function closeAiModal() {
    if (speechRecognition && isSpeechListening) {
      speechRecognition.stop();
    }
    if (aiAgentModal) aiAgentModal.classList.remove('active');
  }

  // Kliknięcie mikrofonu
  if (btnAiMic) {
    btnAiMic.addEventListener('click', () => {
      if (!SpeechRec) {
        alert("Twoja przeglądarka nie wspiera bezpośredniego rozpoznawania mowy. Możesz wpisać polecenie w polu tekstowym poniżej.");
        return;
      }
      if (isSpeechListening) {
        speechRecognition.stop();
      } else {
        try {
          speechRecognition.start();
        } catch (e) {
          console.warn(e);
        }
      }
    });
  }

  // Zapisywanie klucza API
  if (btnToggleKeyInput) {
    btnToggleKeyInput.addEventListener('click', () => {
      if (aiKeyInputRow) {
        aiKeyInputRow.style.display = (aiKeyInputRow.style.display === 'none' || !aiKeyInputRow.style.display) ? 'flex' : 'none';
      }
    });
  }

  if (btnSaveAiKey) {
    btnSaveAiKey.addEventListener('click', () => {
      const key = aiGeminiKeyInput ? aiGeminiKeyInput.value.trim() : "";
      if (!key) {
        alert("Proszę wkleić poprawny klucz API z Google AI Studio.");
        return;
      }
      localStorage.setItem('gemini_api_key', key);
      updateAiKeyStatus();
      if (aiKeyInputRow) aiKeyInputRow.style.display = 'none';
      alert("Klucz Google AI Studio został pomyślnie zapisany!");
    });
  }

  // Klikanie chipów z przykładami
  document.querySelectorAll('.ai-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const p = chip.getAttribute('data-prompt');
      if (aiPromptInput) aiPromptInput.value = p;
    });
  });

  if (btnClearAiPrompt) {
    btnClearAiPrompt.addEventListener('click', () => {
      if (aiPromptInput) aiPromptInput.value = "";
      if (aiResultBox) aiResultBox.style.display = 'none';
    });
  }

  // Inteligentny lokalny parser NLP (fallback i natychmiastowe precyzyjne reguły)
  function parseLocallyNLP(prompt) {
    const text = prompt.toLowerCase();
    const now = new Date();
    let targetDate = new Date(now);

    // 1. Rozpoznawanie dni tygodnia i dat
    // Dzisiejszy dzień tygodnia: 0=niedziela, 1=poniedziałek, 2=wtorek, 3=środa, 4=czwartek, 5=piątek, 6=sobota
    const curDow = now.getDay();
    const dowMap = [
      { key: 'poniedział', dow: 1 },
      { key: 'wtork', dow: 2 },
      { key: 'środ', dow: 3 },
      { key: 'czwart', dow: 4 },
      { key: 'piąt', dow: 5 },
      { key: 'piatek', dow: 5 },
      { key: 'sobot', dow: 6 }
    ];

    let dowFound = false;
    for (const item of dowMap) {
      if (text.includes(item.key)) {
        let diff = item.dow - curDow;
        if (diff <= 0) diff += 7; // najbliższy kolejny dzień tygodnia
        targetDate = new Date(now);
        targetDate.setDate(now.getDate() + diff);
        dowFound = true;
        break;
      }
    }

    if (!dowFound) {
      if (text.includes('pojutrze')) {
        targetDate = new Date(now);
        targetDate.setDate(now.getDate() + 2);
      } else if (text.includes('jutro') || text.includes('jutrzejszy')) {
        targetDate = new Date(now);
        targetDate.setDate(now.getDate() + 1);
      }
    }

    // Rozpoznawanie konkretnych dat, np. "13-go listopada", "13 listopada", "14.11"
    const monthPrefixes = {
      'stycz': 1, 'lut': 2, 'mar': 3, 'kwie': 4, 'maj': 5, 'czer': 6,
      'lip': 7, 'sierp': 8, 'wrzes': 9, 'paźdz': 10, 'list': 11, 'grud': 12
    };
    const dateWordMatch = text.match(/(\d{1,2})(?:-?go|-?ego)?\s+([a-ząćęłńóśźż]+)/i);
    if (dateWordMatch) {
      const dayNum = parseInt(dateWordMatch[1], 10);
      const mWord = dateWordMatch[2].toLowerCase();
      for (const [mPrefix, mNum] of Object.entries(monthPrefixes)) {
        if (mWord.startsWith(mPrefix)) {
          targetDate = new Date(now.getFullYear(), mNum - 1, dayNum);
          break;
        }
      }
    }

    const pad = (n) => String(n).padStart(2, '0');
    const targetDateStr = `${targetDate.getFullYear()}-${pad(targetDate.getMonth() + 1)}-${pad(targetDate.getDate())}`;

    // 2. Typ usługi
    let serviceId = "steel_4";
    let duration = 45;
    if (text.includes('premium')) {
      serviceId = "alu_premium";
      duration = 60;
    } else if (text.includes('alu')) {
      serviceId = "alu_small";
      duration = 45;
    } else if (text.includes('bus') || text.includes('dostawcz')) {
      serviceId = "bus";
      duration = 60;
    } else if (text.includes('szybki') || text.includes('wyważenie')) {
      serviceId = "quick";
      duration = 30;
    } else if (text.includes('stal')) {
      serviceId = "steel_4";
      duration = 45;
    }

    // 3. Stanowisko (Podnośnik A / 1 vs Podnośnik B / 2)
    let preferredStation = null;
    const stMatch = text.match(/(?:stanowisk[oaue]|podnośnik[a]?)\s*([12ab])/i);
    if (stMatch) {
      const stVal = stMatch[1].toUpperCase();
      if (stVal === '1' || stVal === 'A') preferredStation = 1;
      if (stVal === '2' || stVal === 'B') preferredStation = 2;
    } else if (text.includes('na dwójce') || text.includes('drugim stanowisku')) {
      preferredStation = 2;
    } else if (text.includes('na jedynce') || text.includes('pierwszym stanowisku')) {
      preferredStation = 1;
    }

    // 4. Numer rejestracyjny pojazdu
    let carLicensePlate = "";
    const regWordMatch = prompt.match(/rejestracj[aei]?\s*:?\s*([A-Za-z0-9\s-]+?)(?=[,\.]|$|\s+(?:akronim|na|usługa|stanowisko))/i);
    if (regWordMatch) {
      carLicensePlate = regWordMatch[1].trim().toUpperCase();
    } else {
      const plateRegexMatch = prompt.match(/\b([A-Z]{2,3}\s?[A-Z0-9]{4,5})\b/i);
      if (plateRegexMatch) {
        carLicensePlate = plateRegexMatch[1].trim().toUpperCase();
      }
    }

    // 5. Akronim i Klient
    let clientName = "";
    let acronym = "";
    const akrMatch = prompt.match(/akronim\s*:?\s*([A-Za-z0-9ąćęłńóśźż]+)/i);
    if (akrMatch) {
      clientName = akrMatch[1].trim();
      acronym = clientName.toUpperCase();
    } else {
      const dlaMatch = prompt.match(/dla\s+([A-Za-z0-9ąćęłńóśźż]+)/i);
      if (dlaMatch && !['kół', 'opon', 'jutra', 'piątku', 'soboty', 'aut', 'auta'].includes(dlaMatch[1].toLowerCase())) {
        clientName = dlaMatch[1].trim();
        acronym = clientName.toUpperCase();
      } else {
        const quotesMatch = prompt.match(/["'„”]([^"'„”]+)["'„”]/);
        if (quotesMatch) {
          clientName = quotesMatch[1].trim();
          acronym = clientName.toUpperCase();
        } else {
          const wpiszMatch = prompt.match(/wpisz\s+([A-Za-ząćęłńóśźż]+)/i);
          if (wpiszMatch) {
            const w = wpiszMatch[1].toLowerCase();
            const stopWords = ['na', 'do', 'w', 'jutro', 'dzisiaj', 'pierwszy', 'wolny', 'termin', 'stanowisko', 'piątek', 'sobotę'];
            if (!stopWords.includes(w)) {
              clientName = wpiszMatch[1].charAt(0).toUpperCase() + wpiszMatch[1].slice(1);
              acronym = clientName.toUpperCase();
            }
          }
        }
      }
    }

    if (!acronym && carLicensePlate) {
      acronym = carLicensePlate;
      clientName = carLicensePlate;
    } else if (!acronym) {
      acronym = "KLIENT";
      clientName = "Klient";
    }

    if (!carLicensePlate) {
      carLicensePlate = acronym;
    }

    return {
      targetDate: targetDateStr,
      serviceId,
      duration,
      preferredStation,
      clientName,
      acronym,
      carLicensePlate
    };
  }

  // Wywołanie Gemini API w Google AI Studio
  async function callGeminiAIStudio(apiKey, promptText) {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const todayStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

    const getShiftDate = (days) => {
      const d = new Date(now);
      d.setDate(d.getDate() + days);
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    };

    // Wyznaczamy daty kolejnych dni tygodnia na potrzeby Gemini
    const curDow = now.getDay();
    const nextDaysContext = [];
    const dowNames = ["Niedziela", "Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota"];
    for (let offset = 0; offset <= 7; offset++) {
      const d = new Date(now);
      d.setDate(d.getDate() + offset);
      const iso = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
      const name = dowNames[d.getDay()];
      const desc = offset === 0 ? "dzisiaj" : (offset === 1 ? "jutro" : (offset === 2 ? "pojutrze" : name.toLowerCase()));
      nextDaysContext.push(`- ${desc} (${name}): ${iso}`);
    }

    const systemPrompt = `Jesteś inteligentnym agentem-dyspozytorem w warsztacie wulkanizacyjnym (4KołaMag).
Kontekst kalendarza (bieżące daty):
${nextDaysContext.join('\n')}

Dostępne usługi w słowniku:
${JSON.stringify(calendarConfigState.services || [])}

Twoim zadaniem jest przeanalizować polecenie użytkownika w języku polskim i zwrócić wyłącznie poprawny obiekt JSON (bez znaczników markdown \`\`\`json):
{
  "intent": "book",
  "targetDate": "YYYY-MM-DD",
  "serviceId": "steel_4 | alu_small | alu_premium | bus | quick",
  "durationMinutes": 45,
  "station": 1 lub 2 lub null (jeśli podano np. Stanowisko 2),
  "clientName": "Imię lub firma (np. Wojtek, Bolek)",
  "clientAcronym": "AKRONIM (np. WOJTEK, BOLEK)",
  "carLicensePlate": "Numer rejestracyjny (np. PRA 999WX) lub jeśli brak, to akronim",
  "preferredTime": "HH:mm" lub "find_first",
  "explanation": "Krótkie podsumowanie po polsku"
}

Zasady:
1. Rozpoznawaj dni tygodnia (np. "piątek", "sobota", "jutro") i dopasuj właściwą datę z powyższej listy dat.
2. Rozpoznawaj numer rejestracyjny pojazdu (np. PRA 999WX, PRA 12345).
3. Rozpoznawaj akronim i imię klienta (np. "Akronim Wojtek" -> clientAcronym: "WOJTEK", clientName: "Wojtek").
4. Rozpoznawaj stanowisko jeśli użytkownik je wymienił (np. "Stanowisko 2" -> station: 2).
5. "Alu Premium" to serviceId: "alu_premium", durationMinutes: 60.
6. "Stal" to serviceId: "steel_4", durationMinutes: 45.`;

    const modelName = "gemini-1.5-flash";
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${apiKey}`;

    const bodyPayload = {
      contents: [
        {
          role: "user",
          parts: [{ text: `${systemPrompt}\n\nPolecenie użytkownika: "${promptText}"` }]
        }
      ],
      generationConfig: {
        responseMimeType: "application/json",
        temperature: 0.1
      }
    };

    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyPayload)
    });

    if (!res.ok) {
      let errMsg = `Błąd API ${res.status}`;
      try {
        const err = await res.json();
        if (err.error && err.error.message) errMsg = err.error.message;
      } catch(e) {}
      throw new Error(errMsg);
    }

    const data = await res.json();
    const textOut = data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts[0].text;
    if (!textOut) throw new Error("Pusta odpowiedź z Gemini");

    return JSON.parse(textOut);
  }

  // Funkcja syntezy mowy po polsku (stabilna i bezpieczna)
  function speakVoiceAnswer(text) {
    if (!('speechSynthesis' in window)) return;
    try {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = 'pl-PL';
      utter.rate = 1.05;

      const voices = window.speechSynthesis.getVoices();
      const plVoice = voices.find(v => v.lang === 'pl-PL' || v.lang.startsWith('pl'));
      if (plVoice) utter.voice = plVoice;

      window.speechSynthesis.speak(utter);
    } catch (e) {
      console.warn("Speech error:", e);
    }
  }

  let lastSpokenText = "";

  // Główna funkcja wykonania polecenia Agenta AI
  async function executeAiPlan() {
    const prompt = (aiPromptInput ? aiPromptInput.value : "").trim();
    if (!prompt) {
      alert("Proszę wpisać lub podyktować polecenie głosowo.");
      return;
    }

    if (aiResultBox) aiResultBox.style.display = 'none';
    if (aiLoadingBox) aiLoadingBox.style.display = 'block';
    if (aiLoadingText) aiLoadingText.textContent = "Agent analizuje wolne sloty i konfigurację warsztatu...";

    // Automatycznie pobieramy klucz jeśli użytkownik wpisał go w input, ale nie kliknął Zapisz
    let apiKey = localStorage.getItem('gemini_api_key') || "";
    if (!apiKey && aiGeminiKeyInput && aiGeminiKeyInput.value.trim()) {
      apiKey = aiGeminiKeyInput.value.trim();
      localStorage.setItem('gemini_api_key', apiKey);
      updateAiKeyStatus();
    }

    let aiPlan = null;
    let geminiError = null;

    if (apiKey) {
      try {
        aiPlan = await callGeminiAIStudio(apiKey, prompt);
      } catch (err) {
        geminiError = err.message;
        console.warn("Gemini API error:", err);
      }
    }

    // Jeśli brak klucza lub Gemini rzuciło błąd, używamy ulepszonego parsera regułowego
    if (!aiPlan) {
      const loc = parseLocallyNLP(prompt);
      aiPlan = {
        intent: "book",
        targetDate: loc.targetDate,
        serviceId: loc.serviceId,
        durationMinutes: loc.duration,
        station: loc.preferredStation,
        clientName: loc.clientName,
        clientAcronym: loc.acronym,
        carLicensePlate: loc.carLicensePlate,
        preferredTime: "find_first",
        explanation: `Zaplanowano wizytę dla klienta ${loc.clientName} (${loc.acronym}) na dzień ${loc.targetDate}.`
      };
    }

    // Dobieramy pełną nazwę i cenę usługi
    const services = calendarConfigState.services || DEFAULT_CALENDAR_CONFIG.services;
    const srv = services.find(s => s.id === aiPlan.serviceId) || services[0];
    const duration = aiPlan.durationMinutes || srv.durationMinutes || 45;
    const price = srv.price || 140;

    // Preferowane stanowisko (1 lub 2)
    const prefStation = (aiPlan.station === 1 || aiPlan.station === 2) ? aiPlan.station : null;
    const targetDate = aiPlan.targetDate || calendarSelectedDate;

    // Znajdujemy wolny termin w warsztacie z uwzględnieniem wybranego stanowiska
    let slot = null;
    if (aiPlan.preferredTime && aiPlan.preferredTime !== 'find_first' && aiPlan.preferredTime.includes(':')) {
      const [sh, sm] = aiPlan.preferredTime.split(':').map(Number);
      const endMins = (sh * 60 + sm) + duration;
      const pad = (n) => String(n).padStart(2, '0');
      const endTime = `${pad(Math.floor(endMins / 60))}:${pad(endMins % 60)}`;

      slot = {
        date: targetDate,
        startTime: aiPlan.preferredTime,
        endTime: endTime,
        durationMinutes: duration,
        station: prefStation || 1
      };
    } else {
      slot = findFirstAvailableSlotClient(duration, targetDate, prefStation);
    }

    if (!slot) {
      if (aiLoadingBox) aiLoadingBox.style.display = 'none';
      alert(`Nie znaleziono wolnego slotu na ${duration} minut od dnia ${targetDate} ${prefStation ? `na Stanowisku ${prefStation}` : ''}. Sprawdź grafik warsztatu.`);
      return;
    }

    const finalAcronym = (aiPlan.clientAcronym || aiPlan.clientName || "KLIENT").toUpperCase();
    const finalPlate = (aiPlan.carLicensePlate || finalAcronym).toUpperCase();
    const finalName = aiPlan.clientName || "Klient";

    // Przygotowujemy gotowy rekord wizyty
    proposedAiAppointment = {
      date: slot.date,
      startTime: slot.startTime,
      endTime: slot.endTime,
      durationMinutes: duration,
      station: slot.station,
      serviceId: srv.id,
      serviceName: srv.name,
      carLicensePlate: finalPlate,
      clientAcronym: finalAcronym,
      clientName: finalName,
      price: price,
      status: "scheduled",
      notes: `Zlecenie utworzone przez Agenta AI (${prompt})`
    };

    if (aiLoadingBox) aiLoadingBox.style.display = 'none';
    if (aiResultBox) aiResultBox.style.display = 'block';

    const niceDate = formatPolishDateLong(slot.date);
    const stationName = slot.station === 1 ? "Stanowisko 1 (Podnośnik A)" : "Stanowisko 2 (Podnośnik B)";

    if (aiResultTitle) {
      aiResultTitle.innerHTML = `🤖 Agent przygotował wizytę! ${geminiError ? `<span style="font-size: 11px; background: rgba(245, 158, 11, 0.2); color: #f59e0b; padding: 2px 6px; border-radius: 4px; font-weight: normal;">(Silnik regułowy - ${geminiError})</span>` : ''}`;
    }

    if (aiResultMessage) {
      aiResultMessage.innerHTML = `
        Znalazłem wolny termin na <strong>${niceDate}</strong> w godzinach <strong>${slot.startTime} – ${slot.endTime}</strong> na <strong>${stationName}</strong>.<br>
        Klient: <strong>${finalAcronym}</strong> | Nr rej: <strong>${finalPlate}</strong> | Usługa: <strong>${srv.name}</strong> (${duration} min).
      `;
    }

    if (aiResultDetails) {
      aiResultDetails.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px;">
          <div>📅 Data: <strong>${slot.date}</strong></div>
          <div>⏰ Godziny: <strong>${slot.startTime} - ${slot.endTime}</strong> (${duration}m)</div>
          <div>🚗 Stanowisko: <strong>${stationName}</strong></div>
          <div>👤 Akronim klienta: <span style="background: rgba(56, 189, 248, 0.2); color: var(--color-primary); padding: 2px 6px; border-radius: 4px; font-weight: 700;">${finalAcronym}</span></div>
          <div>🚙 Rejestracja: <span style="background: rgba(255, 255, 255, 0.1); color: #fff; padding: 2px 6px; border-radius: 4px; font-weight: 700;">${finalPlate}</span></div>
          <div>🔧 Usługa: <strong>${srv.name}</strong></div>
          <div>💰 Cena: <strong>${price} zł</strong></div>
        </div>
      `;
    }

    // Przygotowanie i odtworzenie odpowiedzi głosowej
    const spokenDate = slot.date === targetDate ? niceDate : `dniu ${slot.date}`;
    lastSpokenText = `Znalazłem wolny termin na ${spokenDate} od godziny ${slot.startTime} do ${slot.endTime} na stanowisku ${slot.station} dla klienta ${finalName}.`;
    speakVoiceAnswer(lastSpokenText);
  }

  // Zatwierdzenie i zapisanie wizyty z poziomu Agenta
  async function confirmSaveAiAppointment() {
    if (!proposedAiAppointment) return;

    const payload = proposedAiAppointment;
    const newId = 'app_' + Date.now();

    // 1. Backend (jeśli dostępny)
    try {
      await fetch('/api/calendar/appointments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch (err) {}

    // 2. localStorage
    try {
      const local = localStorage.getItem('tire_calendar_appointments');
      let all = local ? JSON.parse(local) : [];
      all.push({ ...payload, id: newId });
      localStorage.setItem('tire_calendar_appointments', JSON.stringify(all));
    } catch(e) {}

    alert(`Pomyślnie zapisano wizytę dla klienta ${payload.clientAcronym} (${payload.carLicensePlate}) na dzień ${payload.date} o godz. ${payload.startTime}!`);

    closeAiModal();

    // Przełączamy kalendarz na ten zaplanowany dzień
    calendarSelectedDate = payload.date;
    loadCalendarDay(payload.date);
  }

  // Zdarzenia Asystenta AI
  if (btnOpenAiModal) btnOpenAiModal.addEventListener('click', openAiModal);
  if (btnCloseAiModal) btnCloseAiModal.addEventListener('click', closeAiModal);
  if (btnExecuteAiPlan) btnExecuteAiPlan.addEventListener('click', executeAiPlan);
  if (btnAiConfirmSave) btnAiConfirmSave.addEventListener('click', confirmSaveAiAppointment);
  if (btnAiCancelRes) btnAiCancelRes.addEventListener('click', () => {
    if (aiResultBox) aiResultBox.style.display = 'none';
  });

  // Dodatkowy przycisk odsłuchania głosu
  const btnReplayVoice = document.getElementById('btn-ai-replay-voice');
  if (btnReplayVoice) {
    btnReplayVoice.addEventListener('click', () => {
      if (lastSpokenText) speakVoiceAnswer(lastSpokenText);
    });
  }

  // Ustawienie wyświetlanego adresu e-mail zalogowanego pracownika
  const userEmail = sessionStorage.getItem('tire_admin_email') || localStorage.getItem('tire_admin_email') || 'warsztat';
  const emailEl = document.getElementById('admin-user-email');
  if (emailEl) emailEl.textContent = userEmail;

  // Inicjalne natychmiastowe wypełnienie opcji i pobranie konfiguracji kalendarza
  populateServicesDropdown();
  fetchCalendarConfig();

  // --- 9. INICJALNE POBRANIE DANYCH ---
  fetchDeposits();
});
