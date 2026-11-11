import streamlit as st
import json
import os
from datetime import datetime, date
import pandas as pd
import io

# Konfiguracja strony
st.set_page_config(
    page_title="4KołaMag - Magazyn Opon i Terminarz",
    page_icon="🛞",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.json")
CONFIG_FILE = os.path.join(BASE_DIR, "calendar_config.json")
PUBLIC_CONFIG_FILE = os.path.join(BASE_DIR, "public", "calendar_config.json")
PUBLIC_CAL_FILE = os.path.join(BASE_DIR, "public", "kalendarz.html")
PUBLIC_INDEX_FILE = os.path.join(BASE_DIR, "public", "index.html")

# --- POMOCNICZE: BAZA DANYCH JSON ---
def load_db():
    if not os.path.exists(DB_FILE):
        default_db = {"deposits": [], "archive": [], "appointments": []}
        save_db(default_db)
        return default_db
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("deposits", [])
            data.setdefault("archive", [])
            data.setdefault("appointments", [])
            return data
    except Exception as e:
        st.error(f"Błąd odczytu bazy danych: {e}")
        return {"deposits": [], "archive": [], "appointments": []}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Błąd zapisu bazy danych: {e}")
        return False

# --- POMOCNICZE: KONFIGURACJA ---
def load_config():
    target = CONFIG_FILE if os.path.exists(CONFIG_FILE) else PUBLIC_CONFIG_FILE
    if not os.path.exists(target):
        return {
            "adminPassword": "admin",
            "allowedEmails": ["michal@twoje4kola.pl", "alert@itover.pl"],
            "publicHeader": "Wulkanizacja Michał - rezerwacja terminu 600223669",
            "stationsCount": 2,
            "services": []
        }
    try:
        with open(target, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(cfg):
    try:
        # Zapisz w katalogu głównym oraz w public/
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        if os.path.exists(os.path.join(BASE_DIR, "public")):
            with open(PUBLIC_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Błąd zapisu konfiguracji: {e}")
        return False

def calculate_days(deposit_date_str):
    try:
        dep_date = datetime.strptime(deposit_date_str, "%Y-%m-%d").date()
        return (date.today() - dep_date).days
    except Exception:
        return 0

# --- INICJALIZACJA STANU ---
db_data = load_db()
app_config = load_config()

# --- SIDEBAR (NAWIGACJA) ---
st.sidebar.title("🛞 4KołaMag")
st.sidebar.caption("System Zarządzania Przechowalnią Opon i Terminarzem")

menu_choice = st.sidebar.radio(
    "Nawigacja:",
    [
        "📊 Dashboard Magazynu",
        "➕ Przyjmij Nowy Depozyt",
        "📅 Kalendarz Wizyt",
        "📜 Archiwum Wydanych Opon",
        "⚙️ Konfiguracja & E-mail",
        "🌐 Widok Aplikacji WWW"
    ]
)

# Szybkie statystyki w sidebarze
deposits = db_data.get("deposits", [])
archive = db_data.get("archive", [])
appointments = db_data.get("appointments", [])

st.sidebar.divider()
st.sidebar.markdown(f"**Aktywne depozyty:** `{len(deposits)}`")
st.sidebar.markdown(f"**Archiwum wydanych:** `{len(archive)}`")
st.sidebar.markdown(f"**Zapisane wizyty:** `{len(appointments)}`")

# ==========================================================
# 1. DASHBOARD MAGAZYNU
# ==========================================================
if menu_choice == "📊 Dashboard Magazynu":
    st.header("📊 Stan Magazynu i Depozytów")

    # Metryki lokalizacji
    count_wiata = sum(1 for d in deposits if str(d.get("location", "")).lower() == "wiata")
    count_tdol = sum(1 for d in deposits if str(d.get("location", "")).lower() in ["tdół", "tdol"])
    count_tgora = sum(1 for d in deposits if str(d.get("location", "")).lower() in ["tgóra", "tgora"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Łącznie opon w magazynie", len(deposits))
    c2.metric("Wiata", count_wiata)
    c3.metric("Tdół", count_tdol)
    c4.metric("Tgóra", count_tgora)

    # Opony zalegające > 180 dni
    aging_deposits = []
    for d in deposits:
        days = calculate_days(d.get("depositDate", ""))
        if days >= 180:
            aging_deposits.append({**d, "days": days})

    if aging_deposits:
        st.warning(f"⚠️ **Wykryto {len(aging_deposits)} depozytów zalegających powyżej 180 dni!**")
        df_aging = pd.DataFrame(aging_deposits)[[
            "clientName", "clientPhone", "carLicensePlate", "tireBrand", "tireSize", "location", "depositDate", "days"
        ]].rename(columns={
            "clientName": "Klient",
            "clientPhone": "Telefon",
            "carLicensePlate": "Rejestracja",
            "tireBrand": "Marka",
            "tireSize": "Rozmiar",
            "location": "Lokalizacja",
            "depositDate": "Data przyjęcia",
            "days": "Dni w magazynie"
        })
        st.dataframe(df_aging, use_container_width=True)

    st.subheader("Wszystkie Aktywne Depozyty")

    # Wyszukiwarka i filtry
    col_search, col_filter = st.columns([3, 1])
    search_q = col_search.text_input("🔍 Szukaj (rejestracja, nazwisko, telefon, opony):", "").lower().strip()
    loc_filter = col_filter.selectbox("Filtruj lokalizację:", ["Wszystkie", "Wiata", "Tdół", "Tgóra"])

    filtered_deposits = []
    for d in deposits:
        txt = f"{d.get('clientName','')} {d.get('carLicensePlate','')} {d.get('clientPhone','')} {d.get('tireBrand','')} {d.get('tireSize','')} {d.get('location','')}".lower()
        matches_search = search_q in txt if search_q else True
        matches_loc = True
        if loc_filter != "Wszystkie":
            matches_loc = str(d.get("location","")).lower() == loc_filter.lower()
        if matches_search and matches_loc:
            filtered_deposits.append({**d, "daysInStorage": calculate_days(d.get("depositDate", ""))})

    if filtered_deposits:
        df_dep = pd.DataFrame(filtered_deposits)
        cols_to_show = ["carLicensePlate", "clientName", "clientPhone", "tireBrand", "tireSize", "tireSeason", "quantity", "location", "depositDate", "price", "daysInStorage"]
        col_names = {
            "carLicensePlate": "Rejestracja",
            "clientName": "Klient",
            "clientPhone": "Telefon",
            "tireBrand": "Marka",
            "tireSize": "Rozmiar",
            "tireSeason": "Sezon",
            "quantity": "Sztuki",
            "location": "Lokalizacja",
            "depositDate": "Data przyjęcia",
            "price": "Cena (zł)",
            "daysInStorage": "Dni"
        }
        df_display = df_dep[[c for c in cols_to_show if c in df_dep.columns]].rename(columns=col_names)
        st.dataframe(df_display, use_container_width=True)

        # Eksport do Excela
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_display.to_excel(writer, index=False, sheet_name='Magazyn_Opon')
        excel_data = output.getvalue()

        st.download_button(
            label="📥 Pobierz stan magazynu jako Excel (.xlsx)",
            data=excel_data,
            file_name=f"stan_magazynu_{date.today().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.divider()
        st.subheader("Szybka Akcja: Wydanie opon klientowi (przeniesienie do archiwum)")
        release_col1, release_col2 = st.columns([3, 1])
        dep_options = {f"{d.get('carLicensePlate')} - {d.get('clientName')} ({d.get('tireSize')}) [ID: {d.get('id')}]": d.get('id') for d in deposits}
        selected_release = release_col1.selectbox("Wybierz depozyt do wydania:", options=list(dep_options.keys()))

        if release_col2.button("✓ Wydaj i przenieś do archiwum", type="primary"):
            target_id = dep_options[selected_release]
            dep_to_move = next((d for d in deposits if d.get("id") == target_id), None)
            if dep_to_move:
                dep_to_move["status"] = "released"
                dep_to_move["releaseDate"] = date.today().strftime("%Y-%m-%d")
                db_data["deposits"] = [d for d in deposits if d.get("id") != target_id]
                db_data["archive"].insert(0, dep_to_move)
                if save_db(db_data):
                    st.success(f"Pomyślnie wydano opony dla rejestracji {dep_to_move.get('carLicensePlate')}!")
                    st.rerun()
    else:
        st.info("Brak depozytów spełniających podane kryteria.")

# ==========================================================
# 2. PRZYJMIJ NOWY DEPOZYT
# ==========================================================
elif menu_choice == "➕ Przyjmij Nowy Depozyt":
    st.header("➕ Formularz Przyjęcia Opon do Magazynu")

    with st.form("new_deposit_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        client_name = col1.text_input("Imię i Nazwisko / Firma *", placeholder="np. Jan Kowalski")
        client_phone = col2.text_input("Numer Telefonu *", placeholder="np. 600 123 456")

        client_email = col1.text_input("Adres E-mail klienta (opcjonalnie do pokwitowań)", placeholder="klient@example.com")
        car_plate = col2.text_input("Numer Rejestracyjny Pojazdu *", placeholder="np. PRA 12345").upper().strip()

        col3, col4, col5 = st.columns(3)
        tire_size = col3.text_input("Rozmiar Opon *", placeholder="np. 205/55 R16")
        tire_brand = col4.text_input("Marka Opon", placeholder="np. Michelin, Dębica")
        tire_season = col5.selectbox("Sezon Opon", ["Zimowe", "Letnie", "Całoroczne"])

        col6, col7, col8 = st.columns(3)
        tire_rim = col6.selectbox("Rodzaj Felg", ["Brak (same opony)", "Aluminiowe", "Stalowe"])
        quantity = col7.number_input("Liczba sztuk", min_value=1, max_value=8, value=4)
        location = col8.selectbox("Lokalizacja w Magazynie *", ["wiata", "Tdół", "Tgóra"])

        col9, col10 = st.columns(2)
        deposit_date = col9.date_input("Data przyjęcia", value=date.today())
        price = col10.number_input("Opłata za przechowanie (PLN)", min_value=0, value=140, step=10)

        notes = st.text_area("Uwagi / Stan opon / Kołpaki", placeholder="np. Opony z czujnikami TPMS, stan bieżnika 6mm")

        submitted = st.form_submit_button("💾 Zapisz Depozyt w Magazynie", type="primary")
        if submitted:
            if not client_name or not client_phone or not car_plate or not tire_size:
                st.error("Proszę wypełnić wymagane pola: Imię/Firma, Telefon, Nr Rejestracyjny oraz Rozmiar Opon.")
            else:
                new_id = f"dep_{int(datetime.now().timestamp())}"
                new_dep = {
                    "id": new_id,
                    "clientName": client_name.strip(),
                    "clientPhone": client_phone.strip(),
                    "clientEmail": client_email.strip(),
                    "carLicensePlate": car_plate,
                    "tireSize": tire_size.strip(),
                    "tireBrand": tire_brand.strip(),
                    "tireSeason": tire_season,
                    "tireRimType": tire_rim,
                    "quantity": int(quantity),
                    "location": location,
                    "depositDate": deposit_date.strftime("%Y-%m-%d"),
                    "price": float(price),
                    "notes": notes.strip(),
                    "status": "active"
                }
                db_data["deposits"].insert(0, new_dep)
                if save_db(db_data):
                    st.success(f"Pomyślnie przyjęto opony pojazdu {car_plate} do lokalizacji {location}!")
                    st.balloons()

# ==========================================================
# 3. KALENDARZ WIZYT
# ==========================================================
elif menu_choice == "📅 Kalendarz Wizyt":
    st.header("📅 Kalendarz Wizyt Warsztatu")

    selected_date = st.date_input("Wybierz dzień do podglądu:", value=date.today())
    date_str = selected_date.strftime("%Y-%m-%d")

    day_appointments = [a for a in appointments if a.get("date") == date_str]
    st.subheader(f"Zaplanowane wizyty na dzień: **{selected_date.strftime('%d.%m.%Y')}** ({len(day_appointments)} aut)")

    st1_apps = [a for a in day_appointments if a.get("station") == 1]
    st2_apps = [a for a in day_appointments if a.get("station") == 2]

    col_st1, col_st2 = st.columns(2)
    with col_st1:
        st.markdown("#### 🚗 Stanowisko 1 (Podnośnik A)")
        if st1_apps:
            for app in sorted(st1_apps, key=lambda x: x.get("startTime", "")):
                st.info(f"**⏰ {app.get('startTime')} - {app.get('endTime')}** ({app.get('durationMinutes')} min)\n\n"
                        f"🚘 **{app.get('carLicensePlate', 'BRAK')}** | Akronim: **{app.get('clientAcronym', '-')}**\n\n"
                        f"🔧 {app.get('serviceName', 'Wymiana')} | Kwota: `{app.get('price', 0)} zł`")
        else:
            st.write("Brak wizyt na tym stanowisku.")

    with col_st2:
        st.markdown("#### 🚙 Stanowisko 2 (Podnośnik B)")
        if st2_apps:
            for app in sorted(st2_apps, key=lambda x: x.get("startTime", "")):
                st.success(f"**⏰ {app.get('startTime')} - {app.get('endTime')}** ({app.get('durationMinutes')} min)\n\n"
                           f"🚘 **{app.get('carLicensePlate', 'BRAK')}** | Akronim: **{app.get('clientAcronym', '-')}**\n\n"
                           f"🔧 {app.get('serviceName', 'Wymiana')} | Kwota: `{app.get('price', 0)} zł`")
        else:
            st.write("Brak wizyt na tym stanowisku.")

    st.divider()
    with st.expander("➕ Zaplanuj nową wizytę na ten dzień"):
        with st.form("new_app_form"):
            c_a, c_b, c_c = st.columns(3)
            app_start = c_a.time_input("Godzina rozpoczęcia", value=datetime.strptime("09:00", "%H:%M").time())
            app_dur = c_b.selectbox("Czas trwania", [30, 45, 60, 90], index=1)
            app_station = c_c.selectbox("Stanowisko", [1, 2], format_func=lambda x: f"Stanowisko {x} (Podnośnik {'A' if x==1 else 'B'})")

            c_d, c_e, c_f = st.columns(3)
            app_plate = c_d.text_input("Numer rejestracyjny *", placeholder="np. PRA 11111").upper().strip()
            app_acronym = c_e.text_input("Akronim klienta (widoczny na tablicy)", placeholder="np. BOLEK")
            app_service = c_f.selectbox("Usługa", [
                "Stal - 4 koła stalowe (osobowe)",
                "Alu - koła aluminiowe <= 17 cali",
                "AluPremium - koła aluminiowe > 17 cali",
                "Bus - samochód dostawczy",
                "Szybki serwis / wyważenie"
            ])

            app_sub = st.form_submit_button("Zapisz Wizytę w Terminarzu")
            if app_sub:
                if not app_plate:
                    st.error("Numer rejestracyjny jest wymagany.")
                else:
                    start_str = app_start.strftime("%H:%M")
                    start_dt = datetime.combine(date.today(), app_start)
                    end_dt = start_dt + pd.Timedelta(minutes=app_dur)
                    end_str = end_dt.strftime("%H:%M")

                    new_app = {
                        "id": f"app_{int(datetime.now().timestamp())}",
                        "date": date_str,
                        "startTime": start_str,
                        "endTime": end_str,
                        "durationMinutes": int(app_dur),
                        "station": int(app_station),
                        "carLicensePlate": app_plate,
                        "clientAcronym": app_acronym,
                        "serviceName": app_service,
                        "price": 140,
                        "status": "scheduled"
                    }
                    db_data["appointments"].append(new_app)
                    if save_db(db_data):
                        st.success(f"Zapisano wizytę dla {app_plate} na godz. {start_str}!")
                        st.rerun()

# ==========================================================
# 4. ARCHIWUM WYDANYCH OPON
# ==========================================================
elif menu_choice == "📜 Archiwum Wydanych Opon":
    st.header("📜 Archiwum Wydanych Opon (Historia)")

    if archive:
        df_arch = pd.DataFrame(archive)
        cols_to_show = ["carLicensePlate", "clientName", "clientPhone", "tireBrand", "tireSize", "tireSeason", "quantity", "location", "depositDate", "releaseDate"]
        col_names = {
            "carLicensePlate": "Rejestracja",
            "clientName": "Klient",
            "clientPhone": "Telefon",
            "tireBrand": "Marka",
            "tireSize": "Rozmiar",
            "tireSeason": "Sezon",
            "quantity": "Sztuki",
            "location": "Była Lokalizacja",
            "depositDate": "Przyjęto",
            "releaseDate": "Wydano"
        }
        df_arch_display = df_arch[[c for c in cols_to_show if c in df_arch.columns]].rename(columns=col_names)
        st.dataframe(df_arch_display, use_container_width=True)

        # Eksport do Excela
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_arch_display.to_excel(writer, index=False, sheet_name='Archiwum_Wydanych')
        excel_arch_data = output.getvalue()

        st.download_button(
            label="📥 Pobierz archiwum jako Excel (.xlsx)",
            data=excel_arch_data,
            file_name=f"archiwum_opon_{date.today().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Brak wpisów w archiwum.")

# ==========================================================
# 5. KONFIGURACJA SYSTEMU & E-MAIL
# ==========================================================
elif menu_choice == "⚙️ Konfiguracja & E-mail":
    st.header("⚙️ Konfiguracja Uprawnień i Paska Informacyjnego")

    with st.form("config_form"):
        st.subheader("📢 Pasek ogłoszeń kalendarza publicznego")
        header_text = st.text_input(
            "Nagłówek widoczny dla klientów w sieci:",
            value=app_config.get("publicHeader", "Wulkanizacja Michał - rezerwacja terminu 600223669")
        )

        st.subheader("🔐 Dostęp do Panelu Warsztatu")
        current_emails = app_config.get("allowedEmails", ["michal@twoje4kola.pl", "alert@itover.pl"])
        emails_str = ", ".join(current_emails) if isinstance(current_emails, list) else str(current_emails)
        
        emails_input = st.text_area(
            "Dozwolone adresy e-mail (oddzielone przecinkami):",
            value=emails_str,
            help="Tylko te adresy będą mogły logować się do panelu wewnętrznego."
        )

        admin_pwd = st.text_input(
            "Hasło dostępowe administratora:",
            value=app_config.get("adminPassword", "admin"),
            type="password"
        )

        save_cfg_btn = st.form_submit_button("💾 Zapisz Ustawienia", type="primary")
        if save_cfg_btn:
            parsed_emails = [e.strip().lower() for e in emails_input.replace("\n", ",").split(",") if e.strip() and "@" in e]
            if not parsed_emails:
                parsed_emails = ["michal@twoje4kola.pl", "alert@itover.pl"]

            app_config["publicHeader"] = header_text.strip()
            app_config["allowedEmails"] = parsed_emails
            app_config["adminPassword"] = admin_pwd.strip() or "admin"

            if save_config(app_config):
                st.success("Konfiguracja została pomyślnie zapisana!")
                st.rerun()

# ==========================================================
# 6. WIDOK APLIKACJI WWW (HTML EMBED)
# ==========================================================
elif menu_choice == "🌐 Widok Aplikacji WWW":
    st.header("🌐 Podgląd Aplikacji Webowej (HTML)")
    st.caption("Poniżej możesz wyświetlić natywny terminarz lub panel zoptymalizowany dla przeglądarek.")

    view_type = st.radio("Wybierz widok do osadzenia:", ["Kalendarz Publiczny (dla klientów)", "Panel Warsztatu (wewnętrzny)"], horizontal=True)

    if view_type == "Kalendarz Publiczny (dla klientów)":
        if os.path.exists(PUBLIC_CAL_FILE):
            with open(PUBLIC_CAL_FILE, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.components.v1.html(html_content, height=850, scrolling=True)
        else:
            st.warning("Plik public/kalendarz.html nie został odnaleziony.")
    else:
        if os.path.exists(PUBLIC_INDEX_FILE):
            with open(PUBLIC_INDEX_FILE, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.components.v1.html(html_content, height=850, scrolling=True)
        else:
            st.warning("Plik public/index.html nie został odnaleziony.")
