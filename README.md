# 🛞 4KołaMag — System Magazynu Opon i Terminarz Wulkanizacji

Nowoczesny, kompleksowy system zarządzania przechowalnią opon oraz terminarzem wizyt warsztatu wulkanizacyjnego. Aplikacja oferuje zarówno interfejs webowy (Node.js/HTML5), wersję standalone (.exe), jak i pełne wdrożenie w środowisku **Streamlit (Python)**.

---

## 🌟 Kluczowe Możliwości

1. **Magazyn Depozytów Opon**:
   - Rejestracja depozytów: dane klienta, numer rejestracyjny, parametry opon (rozmiar, marka, sezon, felgi), lokalizacja (*Wiata*, *Tdół*, *Tgóra*), kwota i data.
   - Monitorowanie czasu magazynowania z automatycznym ostrzeżeniem o depozytach zalegających **powyżej 180 dni**.
   - Wydawanie opon i automatyczne przenoszenie do archiwum historii.
   - Generowanie i drukowanie eleganckich pokwitowań depozytu dla klienta.
   - Szybki eksport stanu magazynu i archiwum do plików **Excel (.xlsx)**.

2. **Terminarz Wizyt Warsztatu (Google Calendar style)**:
   - Obsługa 2 niezależnych stanowisk warsztatowych: *Stanowisko 1 (Podnośnik A)* oraz *Stanowisko 2 (Podnośnik B)*.
   - Płynny widok tygodniowy oraz powiększony widok pojedynczego dnia (fokus na 1 dzień).
   - Kolorystyczne rozróżnienie usług: *Stal*, *Alu ≤ 17"*, *AluPremium > 17"*, *Bus*, *Szybki serwis*.

3. **Publiczny Serwis WWW dla Klientów (`/kalendarz.html`)**:
   - Wystawiony w sieci podgląd wolnych i zajętych terminów bez ujawniania danych osobowych klientów (brak nazwisk, telefonów, numerów rejestracyjnych).
   - Konfigurowalny nagłówek z numerem telefonu do rezerwacji.

4. **Bezpieczne Logowanie Pracowników**:
   - Dostęp do panelu warsztatu chroniony autoryzacją e-mail i hasłem.
   - Lista dozwolonych adresów e-mail zarządzana bezpośrednio w konfiguracji `calendar_config.json`.

5. **Asystent Głosowy AI (Google Gemini Studio)**:
   - Obsługa poleceń głosowych i tekstowych w języku naturalnym (np. *"wpisz Bolka na jutro na 14:00 na AluPremium"*).

---

## 📁 Struktura Projektu

```text
tire-storage/
├── public/                     # Zasoby interfejsu przeglądarkowego
│   ├── index.html              # Pełny panel roboczy warsztatu (Dashboard, Magazyn, AI)
│   ├── kalendarz.html          # Publiczny terminarz wizyt dla klientów + okno logowania
│   ├── app.js                  # Logika frontendu i komunikacja API
│   ├── style.css               # Nowoczesna stylistyka Dark Mode
│   └── calendar_config.json    # Konfiguracja godzin, usług i uprawnień
├── database.json               # Baza danych w formacie JSON (depozyty, archiwum, wizyty)
├── database.example.json       # Przykładowa struktura bazy danych
├── calendar_config.json        # Główny plik konfiguracyjny (hasło, e-maile, usługi)
├── server.js                   # Serwer backendowy Express.js
├── db.js                       # Warstwa obsługi plików bazy danych
├── package.json                # Zależności środowiska Node.js
├── streamlit_app.py            # Pełna aplikacja Python przygotowana pod Streamlit
├── requirements.txt            # Zależności środowiska Python (Streamlit)
└── .gitignore                  # Pliki wykluczone z repozytorium Git
```

---

## 🚀 Eksport i Publikacja na GitHub

Aby umieścić projekt w nowym repozytorium na **GitHubie**, wykonaj następujące kroki w terminalu w folderze projektu:

### 1. Inicjalizacja repozytorium Git (jeśli jeszcze nie zainicjalizowano):
```bash
git init
```

### 2. Dodanie plików do repozytorium:
```bash
git add .
git commit -m "Wersja produkcyjna 4KolaMag - Magazyn Opon, Terminarz i Streamlit"
```

### 3. Połączenie ze swoim repozytorium na GitHubie:
Utwórz nowe, puste repozytorium na [github.com/new](https://github.com/new) (np. o nazwie `4kola-magazyn`), a następnie podepnij je:
```bash
git branch -M main
git remote add origin https://github.com/TWOJA_NAZWA_UZYTKOWNIKA/4kola-magazyn.git
git push -u origin main
```

---

## ☁️ Wdrożenie pod Streamlit (Streamlit Community Cloud)

Aplikacja posiada gotowy plik **`streamlit_app.py`** oraz **`requirements.txt`**, dzięki czemu możesz uruchomić ją lokalnie w Pythonie lub wystawić całkowicie **za darmo** w chmurze Streamlit.

### Opcja A: Lokalne uruchomienie w Pythonie:
1. Zainstaluj wymagane pakiety:
   ```bash
   pip install -r requirements.txt
   ```
2. Uruchom aplikację:
   ```bash
   streamlit run streamlit_app.py
   ```
3. Aplikacja otworzy się automatycznie w przeglądarce pod adresem: `http://localhost:8501`.

### Opcja B: Darmowe wdrożenie w Streamlit Community Cloud:
1. Wejdź na [share.streamlit.io](https://share.streamlit.io/) i zaloguj się swoim kontem GitHub.
2. Kliknij **"New app"**.
3. Wybierz swoje repozytorium (`TWOJA_NAZWA_UZYTKOWNIKA/4kola-magazyn`).
4. Ustaw:
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
5. Kliknij **"Deploy!"**.
6. W ciągu 1-2 minut aplikacja zostanie skompilowana i otrzyma publiczny adres WWW dostępny z dowolnego urządzenia (telefon, tablet, komputer).

---

## 💻 Uruchomienie wersji Node.js

Jeśli chcesz uruchomić oryginalny serwer Node.js:
```bash
npm install
npm start
```
Aplikacja uruchomi się na porcie `3000`:
- **Panel warsztatu:** `http://localhost:3000/`
- **Kalendarz publiczny:** `http://localhost:3000/kalendarz.html`

---

## 🔐 Domyślne Dane Dostępu do Panelu

- **Dozwolone adresy e-mail (skonfigurowane w `calendar_config.json`):**
  - `michal@twoje4kola.pl`
  - `alert@itover.pl`
  - Login awaryjny: `admin`
- **Hasło dostępowe:** `admin` *(możliwe do zmiany w zakładce Konfiguracja)*
