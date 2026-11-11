const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

// Wykrywanie czy uruchomiono jako plik .exe skompilowany przez pkg
const isPackaged = process.pkg !== undefined;
const DB_FILE = isPackaged 
  ? path.join(path.dirname(process.execPath), 'database.json') 
  : path.join(__dirname, 'database.json');

const CONFIG_FILE = isPackaged 
  ? path.join(path.dirname(process.execPath), 'calendar_config.json') 
  : path.join(__dirname, 'calendar_config.json');

// Inicjalizacja bazy danych, jeśli plik nie istnieje
function initDB() {
  if (!fs.existsSync(DB_FILE)) {
    const defaultData = {
      deposits: [],     // Aktywne depozyty
      archive: [],      // Wydane opony (historia)
      appointments: []  // Kalendarz wizyt
    };
    fs.writeFileSync(DB_FILE, JSON.stringify(defaultData, null, 2), 'utf8');
  }
}

// Odczyt pełnej bazy danych
function readDB() {
  initDB();
  try {
    const data = fs.readFileSync(DB_FILE, 'utf8');
    const parsed = JSON.parse(data);
    if (!parsed.deposits) parsed.deposits = [];
    if (!parsed.archive) parsed.archive = [];
    if (!parsed.appointments) parsed.appointments = [];
    return parsed;
  } catch (err) {
    console.error("Błąd podczas odczytu bazy danych. Tworzenie nowej struktury.", err);
    return { deposits: [], archive: [], appointments: [] };
  }
}

// Zapis pełnej bazy danych
function writeDB(data) {
  try {
    fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2), 'utf8');
    return true;
  } catch (err) {
    console.error("Błąd zapisu do bazy danych:", err);
    return false;
  }
}

// Domyślna konfiguracja kalendarza
const DEFAULT_CALENDAR_CONFIG = {
  publicHeader: "Wulkanizacja Michał - rezerwacja terminu 600223669",
  stationsCount: 2,
  slotDurationMinutes: 15,
  services: [
    {
      id: "steel_4",
      name: "Przekładka 4 kół stalowych (osobowe)",
      durationMinutes: 45,
      price: 120
    },
    {
      id: "alu_small",
      name: "Koła aluminiowe <= 17 cali",
      durationMinutes: 45,
      price: 140
    },
    {
      id: "alu_premium",
      name: "Koła aluminiowe premium (> 17 cali)",
      durationMinutes: 60,
      price: 180
    },
    {
      id: "bus",
      name: "Bus / Dostawczy",
      durationMinutes: 60,
      price: 200
    },
    {
      id: "quick",
      name: "Szybki serwis / wyważenie / 2 koła",
      durationMinutes: 30,
      price: 60
    }
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

// Odczyt konfiguracji kalendarza
function getCalendarConfig() {
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      const data = fs.readFileSync(CONFIG_FILE, 'utf8');
      return JSON.parse(data);
    }
  } catch (err) {
    console.error("Błąd podczas odczytu calendar_config.json:", err);
  }
  // Jeśli brak, utwórz z wartości domyślnych
  saveCalendarConfig(DEFAULT_CALENDAR_CONFIG);
  return DEFAULT_CALENDAR_CONFIG;
}

// Zapis konfiguracji kalendarza (edycja bez konieczności restartu/rekompilacji)
function saveCalendarConfig(cfg) {
  try {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(cfg, null, 2), 'utf8');
    return true;
  } catch (err) {
    console.error("Błąd zapisu calendar_config.json:", err);
    return false;
  }
}

// Obliczenie daty Wielkanocy (algorytm Meeusa/Gaussa dla kalendarza gregoriańskiego)
function getEasterSunday(year) {
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31); // 3 = Marzec, 4 = Kwiecień
  const day = ((h + l - 7 * m + 114) % 31) + 1;
  return new Date(Date.UTC(year, month - 1, day));
}

// Sprawdzenie czy dany dzień (format "YYYY-MM-DD") to polskie święto ustawowo wolne od pracy
function isPolishHoliday(dateStr) {
  const [yStr, mStr, dStr] = dateStr.split('-');
  const year = parseInt(yStr, 10);
  const month = parseInt(mStr, 10);
  const day = parseInt(dStr, 10);

  // Święta stałe w Polsce
  const fixed = [
    "01-01", // Nowy Rok
    "01-06", // Trzech Króli
    "05-01", // Święto Pracy
    "05-03", // Święto Konstytucji 3 Maja
    "08-15", // Wniebowzięcie NMP / Wojska Polskiego
    "11-01", // Wszystkich Świętych
    "11-11", // Święto Niepodległości
    "12-25", // Boże Narodzenie (dzień 1)
    "12-26"  // Boże Narodzenie (dzień 2)
  ];

  const md = `${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  if (fixed.includes(md)) {
    return true;
  }

  // Święta ruchome na bazie Wielkanocy
  const easter = getEasterSunday(year);
  const addDays = (base, days) => {
    const res = new Date(base.getTime());
    res.setUTCDate(res.getUTCDate() + days);
    return `${String(res.getUTCMonth() + 1).padStart(2, '0')}-${String(res.getUTCDate()).padStart(2, '0')}`;
  };

  const easterMonday = addDays(easter, 1);  // Poniedziałek Wielkanocny
  const corpusChristi = addDays(easter, 60); // Boże Ciało (czwartek)
  const pentecost = addDays(easter, 49);     // Zielone Świątki (niedziela)

  if (md === easterMonday || md === corpusChristi || md === pentecost) {
    return true;
  }

  // Własne zdefiniowane dni wolne w konfiguracji
  const config = getCalendarConfig();
  if (config.customHolidays && config.customHolidays.includes(dateStr)) {
    return true;
  }

  return false;
}

// Pobieranie godzin pracy dla danej daty ("YYYY-MM-DD")
function getWorkingHoursForDate(dateStr) {
  const [yStr, mStr, dStr] = dateStr.split('-');
  const year = parseInt(yStr, 10);
  const month = parseInt(mStr, 10);
  const day = parseInt(dStr, 10);
  const dateObj = new Date(year, month - 1, day);
  const dayOfWeek = dateObj.getDay(); // 0 = Niedziela, 6 = Sobota

  if (dayOfWeek === 0) {
    return null; // Niedziela nieczynne
  }

  if (isPolishHoliday(dateStr)) {
    return null; // Święto państwowe - nieczynne
  }

  const config = getCalendarConfig();
  const monthConfig = (config.monthlyWorkingHours && config.monthlyWorkingHours[String(month)]) 
    ? config.monthlyWorkingHours[String(month)]
    : { start: "08:00", end: "18:00", saturdayStart: "08:00", saturdayEnd: "14:00", workSaturday: true };

  if (dayOfWeek === 6) {
    if (!monthConfig.workSaturday) return null;
    return {
      start: monthConfig.saturdayStart || "08:00",
      end: monthConfig.saturdayEnd || "14:00"
    };
  }

  return {
    start: monthConfig.start || "08:00",
    end: monthConfig.end || "18:00"
  };
}

// Konwersja czasu "HH:mm" na minuty od północy
function timeToMinutes(tStr) {
  if (!tStr) return 0;
  const [h, m] = tStr.split(':').map(Number);
  return (h || 0) * 60 + (m || 0);
}

// Konwersja minut od północy na "HH:mm"
function minutesToTime(mins) {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

// ==========================================
// FUNKCJE OBSŁUGI KALENDARZA WIZYT
// ==========================================

// Pobranie listy wizyt (z opcjonalnym filtrowaniem po dacie lub zakresie)
function getAppointments(filter = {}) {
  const db = readDB();
  let list = db.appointments || [];

  if (filter.date) {
    list = list.filter(a => a.date === filter.date);
  }
  if (filter.dateFrom) {
    list = list.filter(a => a.date >= filter.dateFrom);
  }
  if (filter.dateTo) {
    list = list.filter(a => a.date <= filter.dateTo);
  }

  // Sortowanie chronologiczne: data, potem godzina
  list.sort((a, b) => {
    if (a.date !== b.date) return a.date.localeCompare(b.date);
    return a.startTime.localeCompare(b.startTime);
  });

  return list;
}

// Dodanie nowej wizyty
function addAppointment(data) {
  const db = readDB();
  const config = getCalendarConfig();

  const duration = parseInt(data.durationMinutes, 10) || 45;
  const startMins = timeToMinutes(data.startTime);
  const calculatedEndTime = data.endTime || minutesToTime(startMins + duration);

  const newApp = {
    id: uuidv4(),
    date: data.date,                          // "YYYY-MM-DD"
    startTime: data.startTime,                // "HH:mm"
    endTime: calculatedEndTime,               // "HH:mm"
    durationMinutes: duration,
    station: parseInt(data.station, 10) || 1, // 1 lub 2
    serviceId: data.serviceId || "custom",
    serviceName: data.serviceName || "Wymiana opon",
    clientName: data.clientName ? data.clientName.trim() : "",
    clientAcronym: data.clientAcronym ? data.clientAcronym.trim().toUpperCase() : "",
    clientPhone: data.clientPhone ? data.clientPhone.trim() : "",
    clientEmail: data.clientEmail ? data.clientEmail.trim() : "",
    carLicensePlate: data.carLicensePlate ? data.carLicensePlate.trim().toUpperCase() : "",
    carModel: data.carModel ? data.carModel.trim() : "",
    notes: data.notes ? data.notes.trim() : "",
    depositId: data.depositId || null,
    price: parseFloat(data.price) || 0,
    status: data.status || "scheduled",       // scheduled / completed / cancelled
    createdAt: new Date().toISOString()
  };

  db.appointments.push(newApp);
  writeDB(db);
  return newApp;
}

// Aktualizacja wizyty
function updateAppointment(id, updateData) {
  const db = readDB();
  const index = db.appointments.findIndex(a => a.id === id);
  if (index === -1) return null;

  const current = db.appointments[index];
  
  let duration = updateData.durationMinutes !== undefined 
    ? parseInt(updateData.durationMinutes, 10) 
    : current.durationMinutes;

  let startTime = updateData.startTime || current.startTime;
  let endTime = updateData.endTime;

  if (!endTime && (updateData.startTime || updateData.durationMinutes)) {
    endTime = minutesToTime(timeToMinutes(startTime) + duration);
  }

  const updated = {
    ...current,
    ...updateData,
    id: current.id,
    durationMinutes: duration,
    startTime: startTime,
    endTime: endTime || current.endTime,
    station: updateData.station !== undefined ? parseInt(updateData.station, 10) : current.station,
    carLicensePlate: updateData.carLicensePlate ? updateData.carLicensePlate.trim().toUpperCase() : current.carLicensePlate,
    clientAcronym: updateData.clientAcronym !== undefined ? updateData.clientAcronym.trim().toUpperCase() : (current.clientAcronym || ""),
    updatedAt: new Date().toISOString()
  };

  db.appointments[index] = updated;
  writeDB(db);
  return updated;
}

// Usunięcie wizyty
function deleteAppointment(id) {
  const db = readDB();
  const index = db.appointments.findIndex(a => a.id === id);
  if (index === -1) return false;

  db.appointments.splice(index, 1);
  writeDB(db);
  return true;
}

// Algorytm: Znajdź pierwszy wolny termin
// durationMinutes: czas usługi (np. 30, 45, 60)
// startDateStr: preferowana data startowa ("YYYY-MM-DD", domyślnie dzisiaj)
function findFirstAvailableSlot(durationMinutes = 45, startDateStr = null) {
  const config = getCalendarConfig();
  const stepMinutes = config.slotDurationMinutes || 15;
  const duration = parseInt(durationMinutes, 10) || 45;
  const stationsCount = config.stationsCount || 2;

  const now = new Date();
  const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  
  let checkDateStr = startDateStr && startDateStr >= todayStr ? startDateStr : todayStr;

  // Przeszukujemy do 45 dni naprzód
  for (let dayOffset = 0; dayOffset < 45; dayOffset++) {
    const curDate = new Date(checkDateStr + "T00:00:00");
    curDate.setDate(curDate.getDate() + dayOffset);
    const dateStr = `${curDate.getFullYear()}-${String(curDate.getMonth() + 1).padStart(2, '0')}-${String(curDate.getDate()).padStart(2, '0')}`;

    const workHours = getWorkingHoursForDate(dateStr);
    if (!workHours) {
      continue; // Dzień wolny / święto / niedziela
    }

    const dayStartMins = timeToMinutes(workHours.start);
    const dayEndMins = timeToMinutes(workHours.end);

    // Jeśli sprawdzamy dzień dzisiejszy, nie proponujemy terminów z przeszłości
    let startCheckingFromMins = dayStartMins;
    if (dateStr === todayStr) {
      const currentMins = now.getHours() * 60 + now.getMinutes();
      // Dajemy min. 15 minut buforu od teraz, zaokrąglone do najbliższego slotu
      const earliestMins = Math.ceil((currentMins + 15) / stepMinutes) * stepMinutes;
      startCheckingFromMins = Math.max(dayStartMins, earliestMins);
    }

    // Pobieramy istniejące wizyty na ten dzień (z pominięciem anulowanych)
    const dayApps = getAppointments({ date: dateStr }).filter(a => a.status !== "cancelled");

    // Przeszukujemy sloty w krokach co stepMinutes
    for (let slotStart = startCheckingFromMins; slotStart + duration <= dayEndMins; slotStart += stepMinutes) {
      const slotEnd = slotStart + duration;

      // Sprawdzamy dostępność stanowisk (Stanowisko 1..stationsCount)
      for (let st = 1; st <= stationsCount; st++) {
        // Czy na tym stanowisku występuje kolizja?
        const hasCollision = dayApps.some(app => {
          if (app.station !== st) return false;
          const aStart = timeToMinutes(app.startTime);
          const aEnd = timeToMinutes(app.endTime);
          // Kolizja: appStart < slotEnd && appEnd > slotStart
          return aStart < slotEnd && aEnd > slotStart;
        });

        if (!hasCollision) {
          // Znaleziono pierwszy wolny termin!
          return {
            date: dateStr,
            startTime: minutesToTime(slotStart),
            endTime: minutesToTime(slotEnd),
            durationMinutes: duration,
            station: st,
            workHours: workHours
          };
        }
      }
    }
  }

  return null; // Brak wolnych terminów w zasięgu 45 dni
}

// ==========================================
// FUNKCJE ISTNIEJĄCEGO MAGAZYNU OPON
// ==========================================

function getActiveDeposits() {
  const db = readDB();
  return db.deposits;
}

function getArchive() {
  const db = readDB();
  return db.archive;
}

function addDeposit(deposit) {
  const db = readDB();
  
  let maxIdNum = 0;
  const parseId = (idStr) => {
    if (!idStr) return 0;
    if (!/^\d+$/.test(idStr)) return 0;
    const num = parseInt(idStr, 10);
    return isNaN(num) ? 0 : num;
  };
  
  db.deposits.forEach(d => {
    const num = parseId(d.id);
    if (num > maxIdNum) maxIdNum = num;
  });
  db.archive.forEach(d => {
    const num = parseId(d.id);
    if (num > maxIdNum) maxIdNum = num;
  });
  
  const nextId = String(maxIdNum + 1).padStart(7, '0');
  
  const newDeposit = {
    id: nextId,
    clientName: deposit.clientName ? deposit.clientName.trim() : "",
    clientPhone: deposit.clientPhone ? deposit.clientPhone.trim() : "",
    clientEmail: deposit.clientEmail ? deposit.clientEmail.trim() : "",
    carLicensePlate: deposit.carLicensePlate ? deposit.carLicensePlate.trim().toUpperCase() : "",
    tireSize: deposit.tireSize ? deposit.tireSize.trim() : "",
    tireBrand: deposit.tireBrand ? deposit.tireBrand.trim() : "",
    tireSeason: deposit.tireSeason || "Zimowe",
    tireRimType: deposit.tireRimType || "Brak",
    notes: deposit.notes ? deposit.notes.trim() : "",
    location: deposit.location || "wiata",
    depositDate: deposit.depositDate || new Date().toISOString().split('T')[0],
    quantity: parseInt(deposit.quantity) || 4,
    price: parseFloat(deposit.price) || 0,
    status: "active"
  };

  db.deposits.push(newDeposit);
  writeDB(db);
  return newDeposit;
}

function releaseDeposit(id, releaseDateStr) {
  const db = readDB();
  const index = db.deposits.findIndex(d => d.id === id);
  
  if (index === -1) {
    return null;
  }
  
  const deposit = db.deposits.splice(index, 1)[0];
  const releaseDate = releaseDateStr || new Date().toISOString().split('T')[0];
  
  const dateDep = new Date(deposit.depositDate);
  const dateRel = new Date(releaseDate);
  const diffTime = Math.abs(dateRel - dateDep);
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  const archivedDeposit = {
    ...deposit,
    status: "released",
    releaseDate: releaseDate,
    daysStored: diffDays
  };
  
  db.archive.push(archivedDeposit);
  writeDB(db);
  return archivedDeposit;
}

function moveDeposit(id, newLocation) {
  const db = readDB();
  const deposit = db.deposits.find(d => d.id === id);
  if (!deposit) return null;
  deposit.location = newLocation;
  writeDB(db);
  return deposit;
}

module.exports = {
  // Magazyn
  getActiveDeposits,
  getArchive,
  addDeposit,
  releaseDeposit,
  moveDeposit,
  getRawData: readDB,
  
  // Kalendarz
  getAppointments,
  addAppointment,
  updateAppointment,
  deleteAppointment,
  getCalendarConfig,
  saveCalendarConfig,
  isPolishHoliday,
  getWorkingHoursForDate,
  findFirstAvailableSlot
};
