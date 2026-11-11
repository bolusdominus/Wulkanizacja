require('dotenv').config();
const express = require('express');
const path = require('path');
const db = require('./db');
const nodemailer = require('nodemailer');

const app = express();
const PORT = process.env.PORT || 3000;

// Parsowanie JSON i urlencoded
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Obsługa ścieżki do folderu "public" (ustawialna i elastyczna pod pkg)
const isPackaged = process.pkg !== undefined;
const PUBLIC_DIR = isPackaged 
  ? path.join(path.dirname(process.execPath), 'public') 
  : path.join(__dirname, 'public');

console.log(`Ścieżka do zasobów statycznych (public): ${PUBLIC_DIR}`);

// Serwowanie plików statycznych z folderu public
app.use(express.static(PUBLIC_DIR));

// ==========================================
// 1. API: MAGAZYN OPON (DEPOZYTY I ARCHIWUM)
// ==========================================

// Pobieranie aktywnych depozytów
app.get('/api/deposits', (req, res) => {
  try {
    const deposits = db.getActiveDeposits();
    res.json(deposits);
  } catch (err) {
    res.status(500).json({ error: "Błąd podczas pobierania danych." });
  }
});

// Pobieranie archiwum (historii)
app.get('/api/archive', (req, res) => {
  try {
    const archive = db.getArchive();
    res.json(archive);
  } catch (err) {
    res.status(500).json({ error: "Błąd podczas pobierania archiwum." });
  }
});

// Dodawanie nowego depozytu
app.post('/api/deposits', (req, res) => {
  try {
    const { clientName, clientPhone, clientEmail, carLicensePlate, tireSize, tireBrand, tireSeason, tireRimType, notes, location, depositDate, price, quantity } = req.body;
    
    if (!clientName || !clientPhone || !carLicensePlate) {
      return res.status(400).json({ error: "Wymagane są dane klienta: imię, telefon oraz rejestracja." });
    }
    
    const newDeposit = db.addDeposit({
      clientName,
      clientPhone,
      clientEmail,
      carLicensePlate,
      tireSize,
      tireBrand,
      tireSeason,
      tireRimType,
      notes,
      location,
      depositDate,
      price,
      quantity
    });
    
    res.status(201).json(newDeposit);
  } catch (err) {
    res.status(500).json({ error: "Błąd podczas zapisywania depozytu." });
  }
});

// Wydanie opon (przeniesienie do archiwum)
app.post('/api/deposits/:id/release', (req, res) => {
  try {
    const { id } = req.params;
    const { releaseDate } = req.body;
    
    const released = db.releaseDeposit(id, releaseDate);
    if (!released) {
      return res.status(404).json({ error: "Nie znaleziono depozytu o podanym ID." });
    }
    
    res.json(released);
  } catch (err) {
    res.status(500).json({ error: "Błąd podczas operacji wydania." });
  }
});

// Przenoszenie opon (zmiana lokalizacji)
app.post('/api/deposits/:id/move', (req, res) => {
  try {
    const { id } = req.params;
    const { location } = req.body;
    
    if (!location) {
      return res.status(400).json({ error: "Lokalizacja docelowa jest wymagana." });
    }
    
    const updated = db.moveDeposit(id, location);
    if (!updated) {
      return res.status(404).json({ error: "Nie znaleziono depozytu o podanym ID." });
    }
    
    res.json(updated);
  } catch (err) {
    res.status(500).json({ error: "Błąd podczas operacji przenoszenia." });
  }
});

// ==========================================
// 2. API: KALENDARZ WIZYT (ADMIN)
// ==========================================

// Pobieranie konfiguracji kalendarza (słownik usług, godziny miesięcy, święta)
app.get('/api/calendar/config', (req, res) => {
  try {
    const config = db.getCalendarConfig();
    res.json(config);
  } catch (err) {
    res.status(500).json({ error: "Błąd podczas pobierania konfiguracji kalendarza." });
  }
});

// Zapis nowej konfiguracji (godziny pracy, usługi) bez rekompilacji
app.post('/api/calendar/config', (req, res) => {
  try {
    const success = db.saveCalendarConfig(req.body);
    if (success) {
      res.json({ success: true, message: "Konfiguracja kalendarza została zaktualizowana." });
    } else {
      res.status(500).json({ error: "Nie udało się zapisać konfiguracji." });
    }
  } catch (err) {
    res.status(500).json({ error: "Błąd zapisu konfiguracji: " + err.message });
  }
});

// Pobieranie listy wizyt (pełne dane dla panelu admina)
app.get('/api/calendar/appointments', (req, res) => {
  try {
    const { date, dateFrom, dateTo } = req.query;
    const appointments = db.getAppointments({ date, dateFrom, dateTo });
    res.json(appointments);
  } catch (err) {
    res.status(500).json({ error: "Błąd pobierania wizyt z kalendarza." });
  }
});

// Dodawanie nowej wizyty
app.post('/api/calendar/appointments', (req, res) => {
  try {
    const { date, startTime, durationMinutes, clientName, clientPhone, carLicensePlate } = req.body;
    
    if (!date || !startTime) {
      return res.status(400).json({ error: "Data i godzina rozpoczęcia są wymagane." });
    }

    const newAppointment = db.addAppointment(req.body);
    res.status(201).json(newAppointment);
  } catch (err) {
    res.status(500).json({ error: "Błąd podczas dodawania wizyty: " + err.message });
  }
});

// Aktualizacja wizyty (zmiana godziny, stanowiska, statusu, edycja)
app.put('/api/calendar/appointments/:id', (req, res) => {
  try {
    const { id } = req.params;
    const updated = db.updateAppointment(id, req.body);
    if (!updated) {
      return res.status(404).json({ error: "Nie znaleziono wizyty o podanym ID." });
    }
    res.json(updated);
  } catch (err) {
    res.status(500).json({ error: "Błąd aktualizacji wizyty: " + err.message });
  }
});

// Usunięcie wizyty
app.delete('/api/calendar/appointments/:id', (req, res) => {
  try {
    const { id } = req.params;
    const ok = db.deleteAppointment(id);
    if (!ok) {
      return res.status(404).json({ error: "Nie znaleziono wizyty do usunięcia." });
    }
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: "Błąd usuwania wizyty: " + err.message });
  }
});

// Asystent: Wyszukiwanie pierwszego wolnego terminu
app.get('/api/calendar/first-available', (req, res) => {
  try {
    const duration = parseInt(req.query.duration, 10) || 45;
    const date = req.query.date || null;
    const slot = db.findFirstAvailableSlot(duration, date);
    
    if (!slot) {
      return res.status(404).json({ error: "Nie znaleziono wolnego terminu w najbliższych 45 dniach." });
    }
    res.json(slot);
  } catch (err) {
    res.status(500).json({ error: "Błąd podczas wyszukiwania terminu: " + err.message });
  }
});

// ==========================================
// 3. API: WIDOK PUBLICZNY (BEZ DANYCH WRAŻLIWYCH)
// ==========================================

// Pobieranie zajętości terminów dla klientów
// BEZWZGLĘDNIE BEZ DANYCH OSOBOWYCH (imię, telefon, rejestracja, uwagi zostają usunięte!)
app.get('/api/calendar/public', (req, res) => {
  try {
    const { date, dateFrom, dateTo } = req.query;
    const fullAppointments = db.getAppointments({ date, dateFrom, dateTo });
    
    // Filtrowanie wyłącznie do informacji o zajętości
    const sanitized = fullAppointments
      .filter(a => a.status !== "cancelled")
      .map(a => ({
        id: a.id,
        date: a.date,
        startTime: a.startTime,
        endTime: a.endTime,
        durationMinutes: a.durationMinutes,
        station: a.station,
        serviceName: a.serviceName || "Wymiana opon / Serwis",
        status: "busy" // Publicznie wyświetlane wyłącznie jako zajęte
      }));

    const config = db.getCalendarConfig();
    const targetDate = date || dateFrom || new Date().toISOString().split('T')[0];
    const workingHours = db.getWorkingHoursForDate(targetDate);
    const isHoliday = db.isPolishHoliday(targetDate);

    res.json({
      date: targetDate,
      workingHours: workingHours,
      isHoliday: isHoliday,
      stationsCount: config.stationsCount || 2,
      services: config.services || [],
      appointments: sanitized
    });
  } catch (err) {
    res.status(500).json({ error: "Błąd podczas pobierania grafiku publicznego." });
  }
});

// Dedykowany adres strony publicznej dla klientów (Google Calendar style)
app.get('/kalendarz', (req, res) => {
  res.sendFile(path.join(PUBLIC_DIR, 'kalendarz.html'));
});
app.get('/kalendarz.html', (req, res) => {
  res.sendFile(path.join(PUBLIC_DIR, 'kalendarz.html'));
});

// ==========================================
// 4. E-MAIL, BACKUP I SERWOWANIE SPA
// ==========================================

// Funkcja pomocnicza do wysyłania e-maila za pomocą Nodemailer
async function sendReceiptEmail(deposit) {
  const smtpHost = process.env.SMTP_HOST;
  const smtpPort = parseInt(process.env.SMTP_PORT) || 587;
  const smtpUser = process.env.SMTP_USER;
  const smtpPass = process.env.SMTP_PASS;

  if (!smtpUser || !smtpPass) {
    console.log("Dane SMTP nie zostały skonfigurowane w pliku .env. Pomijam wysyłkę e-mail.");
    throw new Error("Brak konfiguracji SMTP w pliku .env serwera.");
  }

  const transporter = nodemailer.createTransport({
    host: smtpHost,
    port: smtpPort,
    secure: smtpPort === 465,
    auth: {
      user: smtpUser,
      pass: smtpPass
    }
  });

  const fromHeader = `Przechowalnia Opon 4KołaMag <${smtpUser.trim()}>`;

  const mailOptions = {
    from: fromHeader,
    to: deposit.clientEmail,
    subject: `Pokwitowanie depozytu opon - Rejestracja: ${deposit.carLicensePlate}`,
    html: `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background: #fdfdfd;">
        <h2 style="color: #2c3e50; border-bottom: 2px solid #2ecc71; padding-bottom: 10px; margin-top: 0;">4KołaMag - Pokwitowanie Przyjęcia Opon</h2>
        <p>Dzień dobry,</p>
        <p>Potwierdzamy przyjęcie opon do naszej przechowalni. Poniżej znajdują się szczegóły zarejestrowanego depozytu:</p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
          <tr style="background: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #eee; font-weight: bold; width: 40%;">ID Depozytu:</td>
            <td style="padding: 10px; border: 1px solid #eee; font-family: monospace;">${deposit.id}</td>
          </tr>
          <tr>
            <td style="padding: 10px; border: 1px solid #eee; font-weight: bold;">Imię i Nazwisko:</td>
            <td style="padding: 10px; border: 1px solid #eee;">${deposit.clientName}</td>
          </tr>
          <tr style="background: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #eee; font-weight: bold;">Numer Telefonu:</td>
            <td style="padding: 10px; border: 1px solid #eee;">${deposit.clientPhone}</td>
          </tr>
          <tr>
            <td style="padding: 10px; border: 1px solid #eee; font-weight: bold;">Numer Rejestracyjny:</td>
            <td style="padding: 10px; border: 1px solid #eee; font-weight: bold; color: #2c3e50;">${deposit.carLicensePlate}</td>
          </tr>
          <tr style="background: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #eee; font-weight: bold;">Opony:</td>
            <td style="padding: 10px; border: 1px solid #eee;">${deposit.tireBrand || "Nieokreślono"} ${deposit.tireSize || ""} (Sezon: ${deposit.tireSeason})</td>
          </tr>
          <tr>
            <td style="padding: 10px; border: 1px solid #eee; font-weight: bold;">Felgi:</td>
            <td style="padding: 10px; border: 1px solid #eee;">${deposit.tireRimType}</td>
          </tr>
          <tr style="background: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #eee; font-weight: bold;">Liczba sztuk:</td>
            <td style="padding: 10px; border: 1px solid #eee; font-weight: bold;">${deposit.quantity || 4} szt.</td>
          </tr>
          <tr>
            <td style="padding: 10px; border: 1px solid #eee; font-weight: bold;">Lokalizacja:</td>
            <td style="padding: 10px; border: 1px solid #eee;"><span style="background: #e8f8f5; color: #1abc9c; padding: 4px 8px; border-radius: 4px; font-weight: bold;">${deposit.location}</span></td>
          </tr>
          <tr style="background: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #eee; font-weight: bold;">Data przyjęcia:</td>
            <td style="padding: 10px; border: 1px solid #eee;">${deposit.depositDate}</td>
          </tr>
          <tr>
            <td style="padding: 10px; border: 1px solid #eee; font-weight: bold;">Opłata:</td>
            <td style="padding: 10px; border: 1px solid #eee; font-weight: bold; color: #27ae60;">${deposit.price} PLN</td>
          </tr>
          ${deposit.notes ? `
          <tr style="background: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #eee; font-weight: bold;">Stan opon / uwagi:</td>
            <td style="padding: 10px; border: 1px solid #eee; font-style: italic;">${deposit.notes}</td>
          </tr>` : ''}
        </table>
        
        <p style="margin-top: 25px; border-top: 1px solid #eee; padding-top: 15px; font-size: 13px; color: #7f8c8d; text-align: center;">
          Niniejsza wiadomość została wygenerowana automatycznie przez system magazynowy <strong>4KołaMag</strong>. Prosimy na nią nie odpowiadać.
        </p>
      </div>
    `
  };

  await transporter.sendMail(mailOptions);
}

// API: Wysyłanie pokwitowania na e-mail
app.post('/api/deposits/:id/send-email', async (req, res) => {
  try {
    const { id } = req.params;
    const deposits = db.getActiveDeposits();
    const deposit = deposits.find(d => d.id === id);
    
    if (!deposit) {
      return res.status(404).json({ error: "Nie znaleziono depozytu o podanym ID." });
    }
    
    if (!deposit.clientEmail || deposit.clientEmail.trim() === "") {
      return res.status(400).json({ error: "Ten klient nie ma przypisanego adresu e-mail." });
    }
    
    await sendReceiptEmail(deposit);
    res.json({ success: true, message: "E-mail z pokwitowaniem został wysłany!" });
  } catch (err) {
    console.error("Błąd wysyłki e-mail:", err);
    res.status(500).json({ error: "Błąd serwera przy wysyłce poczty: " + err.message });
  }
});

// API: Pobieranie kopii zapasowej (backup database.json)
app.get('/api/backup', (req, res) => {
  const dbPath = path.join(__dirname, 'database.json');
  res.download(dbPath, `kopia_przechowalni_${new Date().toISOString().split('T')[0]}.json`, (err) => {
    if (err) {
      console.error("Błąd podczas pobierania backupu:", err);
      if (!res.headersSent) {
        res.status(500).json({ error: "Nie udało się wygenerować pliku kopii zapasowej." });
      }
    }
  });
});

// Serwowanie index.html dla wszystkich innych zapytań (SPA router fallback)
app.get('*', (req, res) => {
  res.sendFile(path.join(PUBLIC_DIR, 'index.html'));
});

// Uruchomienie serwera na 0.0.0.0 w celu umożliwienia połączeń w sieci lokalnej
app.listen(PORT, '0.0.0.0', () => {
  console.log(`==================================================`);
  console.log(` Serwer 4KołaMag został uruchomiony!`);
  console.log(` Dostęp lokalny (Admin): http://localhost:${PORT}`);
  console.log(` Kalendarz publiczny:   http://localhost:${PORT}/kalendarz`);
  console.log(` Dostęp w sieci LAN:    http://[IP_KOMPUTERA]:${PORT}`);
  console.log(`==================================================`);
});
