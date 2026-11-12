import streamlit as st
import json
import os
import re
from datetime import datetime, date, timedelta
import pandas as pd
import io

# --- KONFIGURACJA STRONY STREAMLIT ---
st.set_page_config(
    page_title="4KołaMag - Terminarz i Magazyn Opon",
    page_icon="🛞",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Ścieżki do plików
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.json")
CONFIG_FILE = os.path.join(BASE_DIR, "calendar_config.json")
PUBLIC_CONFIG_FILE = os.path.join(BASE_DIR, "public", "calendar_config.json")

# --- WSTRZYKIWANIE STYLÓW DARK MODE (ZOPTYMALIZOWANYCH POD MOBILE I PC) ---
st.markdown("""
<style>
    /* Globalne tło aplikacji */
    .stApp {
        background-color: #0b0f19 !important;
        color: #f8fafc !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    }

    /* Dopasowanie marginesów kontenera głównego */
    .block-container {
        padding-top: 1.0rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 1.0rem !important;
        padding-right: 1.0rem !important;
        max-width: 1300px !important;
    }

    /* Pasek boczny (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #101726 !important;
        border-right: 1px solid #1e293b !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Przyciski standardowe */
    button[kind="primary"], button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #0284c7, #2563eb) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35) !important;
        min-height: 42px !important;
        transition: all 0.2s ease;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #0369a1, #1d4ed8) !important;
        transform: translateY(-1px);
    }
    
    button[kind="secondary"], button[data-testid="baseButton-secondary"] {
        background: #151d30 !important;
        color: #f8fafc !important;
        border: 1px solid #23314d !important;
        border-radius: 8px !important;
        min-height: 40px !important;
    }
    button[kind="secondary"]:hover {
        background: #1e293b !important;
        border-color: #38bdf8 !important;
    }

    /* Kafelki metryk */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #151d30, #131b2e) !important;
        border: 1px solid #23314d !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4) !important;
    }
    div[data-testid="stMetric"] label {
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-weight: 800 !important;
    }

    /* Pasek nagłówkowy aplikacji */
    .top-brand {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .top-brand-icon {
        font-size: 26px;
    }
    .top-brand-title {
        font-size: 18px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 0.3px;
        line-height: 1.2;
    }
    .top-brand-sub {
        font-size: 12px;
        color: #94a3b8;
    }

    /* Baner z telefonem - bezpośrednie wybieranie na smartfonie */
    .phone-hero-banner {
        background: linear-gradient(135deg, #0369a1, #0284c7);
        border: 1px solid #38bdf8;
        border-radius: 12px;
        padding: 12px 18px;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 12px;
        box-shadow: 0 6px 18px rgba(2, 132, 199, 0.3);
    }
    .phone-banner-text {
        font-size: 15px;
        font-weight: 700;
        color: #ffffff;
    }
    .phone-call-btn {
        background: #ffffff;
        color: #0369a1 !important;
        font-size: 15px;
        font-weight: 800;
        text-decoration: none !important;
        padding: 8px 18px;
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.25);
    }

    /* Pasek legendy */
    .legend-container {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        background: #131b2e;
        padding: 8px 14px;
        border-radius: 8px;
        border: 1px solid #23314d;
        margin-bottom: 14px;
        font-size: 12px;
    }
    .legend-title {
        font-weight: 700;
        color: #94a3b8;
        margin-right: 4px;
    }
    .legend-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: #e2e8f0;
        font-weight: 600;
        background: rgba(255, 255, 255, 0.04);
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid #1e293b;
    }
    .legend-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
    }

    /* Karta stanowiska */
    .station-column-header {
        background: #101726;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .station-title {
        font-size: 15px;
        font-weight: 800;
        color: #f8fafc;
    }
    .station-badge-count {
        font-size: 12px;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
    }
    .count-busy {
        background: rgba(244, 63, 94, 0.18);
        color: #fb7185;
        border: 1px solid rgba(244, 63, 94, 0.35);
    }
    .count-free {
        background: rgba(16, 185, 129, 0.18);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }

    /* Kafelki wizyt w kalendarzu (Publiczny) */
    .app-card-box {
        background: #151d30;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 10px;
        border: 1.5px solid #23314d;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .app-card-box.type-stal {
        border-color: #38bdf8;
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.22), rgba(15, 23, 42, 0.95));
    }
    .app-card-box.type-alu {
        border-color: #34d399;
        background: linear-gradient(135deg, rgba(5, 150, 105, 0.22), rgba(15, 23, 42, 0.95));
    }
    .app-card-box.type-alupremium {
        border-color: #c084fc;
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.22), rgba(15, 23, 42, 0.95));
    }
    .app-card-box.type-bus {
        border-color: #fcd34d;
        background: linear-gradient(135deg, rgba(217, 119, 6, 0.22), rgba(15, 23, 42, 0.95));
    }
    .app-card-box.type-szybki {
        border-color: #f472b6;
        background: linear-gradient(135deg, rgba(219, 39, 119, 0.22), rgba(15, 23, 42, 0.95));
    }

    .card-top-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 6px;
    }
    .time-badge {
        font-size: 13.5px;
        font-weight: 800;
        color: #ffffff;
        background: rgba(0, 0, 0, 0.45);
        padding: 2px 7px;
        border-radius: 5px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .duration-badge {
        font-size: 11px;
        font-weight: 700;
        color: #94a3b8;
    }
    .service-badge {
        font-size: 14px;
        font-weight: 800;
        color: #f8fafc;
    }

    /* Karta wyniku wyszukiwania terminu / Agenta AI */
    .slot-result-card {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(6, 78, 59, 0.2));
        border: 1.5px solid #10b981;
        border-radius: 12px;
        padding: 16px;
        margin-top: 10px;
        margin-bottom: 14px;
    }
    .slot-result-title {
        color: #34d399;
        font-size: 16px;
        font-weight: 800;
        margin-bottom: 8px;
    }

    /* Tabela cennika */
    .price-table-box {
        background: #131b2e;
        border: 1px solid #23314d;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 14px;
    }

    /* Responsywność dla telefonów (ekrany <= 768px) */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
            padding-top: 0.6rem !important;
        }
        .phone-hero-banner {
            flex-direction: column;
            align-items: stretch;
            text-align: center;
        }
        .phone-call-btn {
            justify-content: center;
            width: 100%;
        }
        .legend-container {
            font-size: 11px;
            gap: 6px;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- OBSŁUGA BAZY DANYCH I KONFIGURACJI ---
def load_db():
    default_db = {"deposits": [], "archive": [], "appointments": []}
    if not os.path.exists(DB_FILE):
        return default_db
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("deposits", [])
            data.setdefault("archive", [])
            data.setdefault("appointments", [])
            return data
    except Exception:
        return {"deposits": [], "archive": [], "appointments": []}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def load_config():
    target = CONFIG_FILE if os.path.exists(CONFIG_FILE) else PUBLIC_CONFIG_FILE
    default_services = [
        {"id": "steel_4", "shortLabel": "Stal", "name": "Stal - 4 koła stalowe (osobowe)", "durationMinutes": 45, "price": 120},
        {"id": "alu_small", "shortLabel": "Alu", "name": "Alu - koła aluminiowe <= 17 cali", "durationMinutes": 45, "price": 140},
        {"id": "alu_premium", "shortLabel": "AluPremium", "name": "AluPremium - koła aluminiowe > 17 cali", "durationMinutes": 60, "price": 180},
        {"id": "bus", "shortLabel": "Bus", "name": "Bus - samochód dostawczy", "durationMinutes": 60, "price": 200},
        {"id": "quick", "shortLabel": "Szybki", "name": "Szybki serwis / wyważenie / 2 koła", "durationMinutes": 30, "price": 60}
    ]
    if not os.path.exists(target):
        return {
            "adminPassword": "admin",
            "allowedEmails": ["michal@twoje4kola.pl", "alert@itover.pl"],
            "publicHeader": "Wulkanizacja Michał - rezerwacja terminu 600223669",
            "stationsCount": 2,
            "services": default_services
        }
    try:
        with open(target, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            if not cfg.get("services"):
                cfg["services"] = default_services
            return cfg
    except Exception:
        return {"services": default_services}

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        if os.path.exists(os.path.join(BASE_DIR, "public")):
            with open(PUBLIC_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def calculate_days(deposit_date_str):
    try:
        dep_date = datetime.strptime(deposit_date_str, "%Y-%m-%d").date()
        return (date.today() - dep_date).days
    except Exception:
        return 0

# --- ALGORYTM WYSZUKIWANIA NAJBLIŻSZEGO WOLNEGO TERMINU ---
def is_polish_holiday(d):
    fixed = [
        (1, 1), (1, 6), (5, 1), (5, 3), (8, 15),
        (11, 1), (11, 11), (12, 25), (12, 26)
    ]
    return (d.month, d.day) in fixed

def get_working_hours(d, cfg):
    if d.weekday() == 6:  # Niedziela
        return None
    if is_polish_holiday(d):
        return None
    month_key = str(d.month)
    monthly = cfg.get("monthlyWorkingHours", {})
    m_cfg = monthly.get(month_key, {
        "start": "08:00", "end": "18:00",
        "saturdayStart": "08:00", "saturdayEnd": "14:00", "workSaturday": True
    })

    if d.weekday() == 5:  # Sobota
        if not m_cfg.get("workSaturday", True):
            return None
        return {
            "start": m_cfg.get("saturdayStart", "08:00"),
            "end": m_cfg.get("saturdayEnd", "14:00")
        }
    return {
        "start": m_cfg.get("start", "08:00"),
        "end": m_cfg.get("end", "18:00")
    }

def find_first_free_slot(appointments, cfg, duration=45, start_from=None, station_pref=0):
    if not start_from:
        start_from = date.today()
    cur_d = start_from
    for _ in range(30):
        wh = get_working_hours(cur_d, cfg)
        if wh:
            d_str = cur_d.strftime("%Y-%m-%d")
            sh, sm = map(int, wh["start"].split(":"))
            eh, em = map(int, wh["end"].split(":"))
            start_m = sh * 60 + sm
            end_m = eh * 60 + em

            if cur_d == date.today():
                now_m = datetime.now().hour * 60 + datetime.now().minute
                if now_m > start_m:
                    start_m = ((now_m + 15) // 15) * 15

            day_apps = [a for a in appointments if a.get("date") == d_str]
            stations = [station_pref] if station_pref in [1, 2] else [1, 2]

            for s in range(start_m, end_m - duration + 1, 15):
                e = s + duration
                for st in stations:
                    collision = False
                    for a in day_apps:
                        if int(a.get("station", 1)) == st:
                            ash, asm = map(int, a.get("startTime", "00:00").split(":"))
                            aeh, aem = map(int, a.get("endTime", "00:00").split(":"))
                            astart = ash * 60 + asm
                            aend = aeh * 60 + aem
                            if astart < e and aend > s:
                                collision = True
                                break
                    if not collision:
                        return {
                            "date": d_str,
                            "startTime": f"{s // 60:02d}:{s % 60:02d}",
                            "endTime": f"{e // 60:02d}:{e % 60:02d}",
                            "durationMinutes": duration,
                            "station": st
                        }
        cur_d += timedelta(days=1)
    return None

# --- PARSER INTELIGENTNEGO ASYSTENTA AI ---
def parse_ai_prompt(prompt_text, appointments, cfg):
    p = prompt_text.lower().strip()
    services = cfg.get("services", [])
    
    # 1. Usługa
    target_srv = None
    if "premium" in p:
        target_srv = next((s for s in services if "premium" in s.get("id", "").lower()), None)
    elif "alu" in p:
        target_srv = next((s for s in services if "alu" in s.get("id", "").lower() and "premium" not in s.get("id", "").lower()), None)
    elif "bus" in p or "dostawcz" in p:
        target_srv = next((s for s in services if "bus" in s.get("id", "").lower()), None)
    elif "szybki" in p or "wyważ" in p:
        target_srv = next((s for s in services if "quick" in s.get("id", "").lower() or "szybki" in s.get("name", "").lower()), None)
    elif "stal" in p:
        target_srv = next((s for s in services if "steel" in s.get("id", "").lower() or "stal" in s.get("name", "").lower()), None)
    
    if not target_srv and services:
        target_srv = services[0]

    dur = target_srv.get("durationMinutes", 45) if target_srv else 45
    price = target_srv.get("price", 140) if target_srv else 140

    # 2. Stanowisko
    station = 0
    if "stanowisko 2" in p or "podnośnik b" in p or "st 2" in p:
        station = 2
    elif "stanowisko 1" in p or "podnośnik a" in p or "st 1" in p:
        station = 1

    # 3. Data
    target_d = date.today()
    if "jutro" in p:
        target_d = date.today() + timedelta(days=1)
    elif "pojutrze" in p:
        target_d = date.today() + timedelta(days=2)
    else:
        weekdays_map = {
            "poniedział": 0, "wtorek": 1, "wtork": 1, "środ": 2, "srod": 2,
            "czwartek": 3, "czwartk": 3, "piątek": 4, "piatk": 4, "sobot": 5
        }
        for k, v in weekdays_map.items():
            if k in p:
                diff = (v - date.today().weekday()) % 7
                if diff == 0 and "dziś" not in p and "dzisiaj" not in p:
                    diff = 7
                target_d = date.today() + timedelta(days=diff)
                break
        
        # Konkretny dzień np. 13-go, 13 listopada
        m_day = re.search(r'(\d{1,2})(?:-go|-ego|\.|\s)?\s*(listopad|grudzi|stycz|luty|marz|kwiet|maj|czerwc|lipc|sierp|wrzes|pa[źz]dzier)?', p)
        if m_day and m_day.group(1):
            try:
                target_d = target_d.replace(day=int(m_day.group(1)))
            except Exception:
                pass

    # 4. Numer rejestracyjny
    m_plate = re.search(r'\b([A-Z]{2,3}\s?[0-9A-Z]{4,5})\b', prompt_text.upper())
    plate = m_plate.group(1).replace(" ", "") if m_plate else ""

    # 5. Akronim / Klient
    client_name = "KLIENT"
    m_akr = re.search(r'(?:akronim|klient|dla|wpisz)\s+([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9]+)', prompt_text, re.IGNORECASE)
    if m_akr:
        val = m_akr.group(1).strip()
        if val.lower() not in ["na", "pierwszy", "wolny", "termin", "jutro", "piątek", "alu"]:
            client_name = val

    # 6. Wyszukanie slotu
    slot = find_first_free_slot(appointments, cfg, dur, target_d, station)
    if not slot and station != 0:
        slot = find_first_free_slot(appointments, cfg, dur, target_d, 0)

    return {
        "service": target_srv,
        "slot": slot,
        "plate": plate,
        "client": client_name,
        "price": price,
        "duration": dur
    }

# Wczytujemy dane
db_data = load_db()
app_config = load_config()

# --- STAN SESJI ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "logged_user" not in st.session_state:
    st.session_state["logged_user"] = ""
if "show_login_modal" not in st.session_state:
    st.session_state["show_login_modal"] = False
if "cal_date" not in st.session_state:
    st.session_state["cal_date"] = date.today()
if "ai_proposed_visit" not in st.session_state:
    st.session_state["ai_proposed_visit"] = None

# --- GÓRNY PASEK NAWIGACJI ---
header_col1, header_col2 = st.columns([3, 1])

with header_col1:
    st.markdown("""
    <div class="top-brand">
        <div class="top-brand-icon">🛞</div>
        <div>
            <div class="top-brand-title">4KołaMag – Terminarz Wulkanizacji</div>
            <div class="top-brand-sub">Podgląd dostępności stanowisk i wolnych terminów</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with header_col2:
    if not st.session_state["authenticated"]:
        if not st.session_state["show_login_modal"]:
            if st.button("🔐 Zaloguj", use_container_width=True, help="Dostęp do panelu warsztatu dla pracowników"):
                st.session_state["show_login_modal"] = True
                st.rerun()
        else:
            if st.button("✕ Zamknij logowanie", use_container_width=True):
                st.session_state["show_login_modal"] = False
                st.rerun()
    else:
        st.caption(f"👤 `{st.session_state['logged_user']}`")
        if st.button("🚪 Wyloguj", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["logged_user"] = ""
            st.session_state["show_login_modal"] = False
            st.rerun()

# --- OKIENKO LOGOWANIA ---
if not st.session_state["authenticated"] and st.session_state["show_login_modal"]:
    st.markdown("---")
    login_c1, login_c2, login_c3 = st.columns([1, 2, 1])
    with login_c2:
        st.markdown("### 🔐 Logowanie do Panelu Warsztatu")
        st.caption("Dostęp zastrzeżony dla pracowników. Wpisz uprawniony adres e-mail i hasło dostępowe.")
        login_email = st.text_input("Adres e-mail:", placeholder="Wpisz adres e-mail", key="input_login_email").strip().lower()
        login_password = st.text_input("Hasło dostępowe:", type="password", key="input_login_pass")
        
        b_log, b_close = st.columns(2)
        if b_log.button("Zaloguj się →", type="primary", use_container_width=True):
            allowed_list = app_config.get("allowedEmails", ["michal@twoje4kola.pl", "alert@itover.pl"])
            if isinstance(allowed_list, str):
                allowed_list = [x.strip().lower() for x in allowed_list.split(",") if x.strip()]
            else:
                allowed_list = [str(x).strip().lower() for x in allowed_list]

            is_email_valid = (
                "*" in allowed_list or 
                login_email in allowed_list or 
                login_email == "admin"
            )
            correct_password = str(app_config.get("adminPassword", "admin")).strip()

            if not is_email_valid:
                st.error("Brak uprawnień dla podanego adresu e-mail.")
            elif login_password != correct_password:
                st.error("Nieprawidłowe hasło.")
            else:
                st.session_state["authenticated"] = True
                st.session_state["logged_user"] = login_email
                st.session_state["show_login_modal"] = False
                st.success("Zalogowano pomyślnie!")
                st.rerun()

        if b_close.button("Anuluj", use_container_width=True):
            st.session_state["show_login_modal"] = False
            st.rerun()
    st.markdown("---")

# --- PASEK BOCZNY (SIDEBAR) – WIDOCZNY TYLKO DLA ZALOGOWANYCH ---
if st.session_state["authenticated"]:
    st.sidebar.markdown("## 🛞 Panel Warsztatu")
    st.sidebar.success(f"Zalogowano:\n`{st.session_state['logged_user']}`")
    
    menu_choice = st.sidebar.radio(
        "Nawigacja:",
        [
            "👁️ Podgląd Publiczny (dla Klientów)",
            "📅 Kalendarz Wizyt (Admin)",
            "📊 Dashboard & Magazyn Opon",
            "➕ Przyjmij Nowy Depozyt",
            "📜 Archiwum Wydanych Opon",
            "⚙️ Konfiguracja & Uprawnienia"
        ]
    )

    deposits = db_data.get("deposits", [])
    archive = db_data.get("archive", [])
    appointments = db_data.get("appointments", [])

    st.sidebar.markdown("---")
    st.sidebar.caption("📦 **Podsumowanie:**")
    st.sidebar.write(f"• Depozyty: `{len(deposits)}`")
    st.sidebar.write(f"• Archiwum: `{len(archive)}`")
    st.sidebar.write(f"• Wizyty: `{len(appointments)}`")

    if st.sidebar.button("🚪 Wyloguj się z panelu", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["logged_user"] = ""
        st.rerun()
else:
    menu_choice = "👁️ Podgląd Publiczny (dla Klientów)"


# ==========================================================
# 1. WIDOK TERMINARZA DLA KLIENTÓW (PUBLICZNY & RESPONSIVE)
# ==========================================================
if menu_choice == "👁️ Podgląd Publiczny (dla Klientów)":
    st.markdown("""
    <div class="phone-hero-banner">
        <div class="phone-banner-text">
            📢 Wulkanizacja Michał – rezerwacja dogodnego terminu:
        </div>
        <a href="tel:600223669" class="phone-call-btn">
            📞 600 223 669
        </a>
    </div>
    """, unsafe_allow_html=True)

    # Legenda usług
    st.markdown("""
    <div class="legend-container">
        <span class="legend-title">Usługi:</span>
        <span class="legend-chip"><span class="legend-dot" style="background: #0284c7;"></span> Stal (45m - 120 zł)</span>
        <span class="legend-chip"><span class="legend-dot" style="background: #10b981;"></span> Alu ≤ 17" (45m - 140 zł)</span>
        <span class="legend-chip"><span class="legend-dot" style="background: #8b5cf6;"></span> AluPremium > 17" (1h - 180 zł)</span>
        <span class="legend-chip"><span class="legend-dot" style="background: #f59e0b;"></span> Bus (1h - 200 zł)</span>
        <span class="legend-chip"><span class="legend-dot" style="background: #ec4899;"></span> Szybki (30m - 60 zł)</span>
        <span style="margin-left: auto; color: #38bdf8; font-weight: 700;">🕒 08:00 – 18:00</span>
    </div>
    """, unsafe_allow_html=True)

    # WYSZUKIWARKA WOLNEGO TERMINU DLA KLIENTA (EXPANDER)
    with st.expander("⚡ Sprawdź najbliższy wolny termin i koszt usługi", expanded=False):
        q_srv_col, q_date_col, q_btn_col = st.columns([2, 1, 1])
        services = app_config.get("services", [])
        srv_map = {f"{s.get('name')} ({s.get('price')} zł)": s for s in services}
        chosen_q_srv = q_srv_col.selectbox("Wybierz rodzaj usługi:", list(srv_map.keys()), key="pub_q_srv")
        chosen_srv_obj = srv_map[chosen_q_srv]
        q_start_d = q_date_col.date_input("Od kiedy szukać:", value=date.today(), key="pub_q_date")
        
        if q_btn_col.button("🔍 Znajdź termin", type="primary", use_container_width=True, key="pub_q_btn"):
            slot = find_first_free_slot(db_data.get("appointments", []), app_config, chosen_srv_obj.get("durationMinutes", 45), q_start_d)
            if slot:
                st.session_state["pub_found_slot"] = {
                    "slot": slot,
                    "service": chosen_srv_obj
                }
            else:
                st.session_state["pub_found_slot"] = None
                st.warning("Brak wolnych terminów w najbliższym czasie.")

        if st.session_state.get("pub_found_slot"):
            fs = st.session_state["pub_found_slot"]["slot"]
            srv_o = st.session_state["pub_found_slot"]["service"]
            st.markdown(f"""
            <div class="slot-result-card">
                <div class="slot-result-title">🎉 Znaleziono najbliższy wolny termin!</div>
                <div style="font-size: 15px; color: #f8fafc; line-height: 1.6;">
                    📅 <strong>Data:</strong> {fs['date']}<br>
                    ⏰ <strong>Godzina:</strong> {fs['startTime']} – {fs['endTime']} ({fs['durationMinutes']} min)<br>
                    🚗 <strong>Stanowisko:</strong> Stanowisko {fs['station']} (Podnośnik {'A' if fs['station']==1 else 'B'})<br>
                    🔧 <strong>Usługa:</strong> {srv_o.get('name')}<br>
                    💰 <strong>Cena usługi:</strong> <span style="font-size: 17px; color: #38bdf8; font-weight: 800;">{srv_o.get('price')} zł</span>
                </div>
                <div style="margin-top: 12px;">
                    <a href="tel:600223669" class="phone-call-btn">📞 Zadzwoń i zarezerwuj ten termin: 600 223 669</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Nawigacja dniami kalendarza
    nav_c1, nav_c2, nav_c3, nav_picker = st.columns([1, 1, 1, 2])

    if nav_c1.button("◀ Wczoraj", use_container_width=True):
        st.session_state["cal_date"] -= timedelta(days=1)
        st.rerun()
    if nav_c2.button("Dziś", use_container_width=True):
        st.session_state["cal_date"] = date.today()
        st.rerun()
    if nav_c3.button("Jutro ▶", use_container_width=True):
        st.session_state["cal_date"] += timedelta(days=1)
        st.rerun()

    chosen_d = nav_picker.date_input("Wybierz dzień:", value=st.session_state["cal_date"], label_visibility="collapsed")
    if chosen_d != st.session_state["cal_date"]:
        st.session_state["cal_date"] = chosen_d
        st.rerun()

    date_str = st.session_state["cal_date"].strftime("%Y-%m-%d")
    polish_weekdays = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
    polish_months = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca", "sierpnia", "września", "października", "listopada", "grudnia"]
    
    day_name = polish_weekdays[st.session_state["cal_date"].weekday()]
    month_name = polish_months[st.session_state["cal_date"].month - 1]
    formatted_date_title = f"{day_name}, {st.session_state['cal_date'].day} {month_name} {st.session_state['cal_date'].year}"

    st.markdown(f"### 📅 {formatted_date_title}")

    # Pobieramy wizyty
    appointments = db_data.get("appointments", [])
    day_apps = [a for a in appointments if a.get("date") == date_str]
    st1_apps = [a for a in day_apps if int(a.get("station", 1)) == 1]
    st2_apps = [a for a in day_apps if int(a.get("station", 1)) == 2]

    def get_service_info(service_name):
        s = str(service_name).lower()
        if "premium" in s:
            return "type-alupremium", "💎 AluPremium > 17 cali"
        elif "alu" in s:
            return "type-alu", "✨ Koła aluminiowe ≤ 17″"
        elif "bus" in s:
            return "type-bus", "🚐 Auto dostawcze (Bus)"
        elif "szybki" in s or "wyważ" in s:
            return "type-szybki", "⚡ Szybki serwis / wyważenie"
        return "type-stal", "🛞 Koła stalowe (osobowe)"

    def render_app_card(app):
        css_cls, pretty_name = get_service_info(app.get("serviceName", ""))
        start_t = app.get("startTime", "00:00")
        end_t = app.get("endTime", "00:00")
        dur = app.get("durationMinutes", 45)
        st.markdown(f"""
        <div class="app-card-box {css_cls}">
            <div class="card-top-row">
                <span class="time-badge">⏰ {start_t} – {end_t}</span>
                <span class="duration-badge">{dur} min</span>
            </div>
            <div class="service-badge">{pretty_name}</div>
        </div>
        """, unsafe_allow_html=True)

    tab_all, tab_st1, tab_st2, tab_prices = st.tabs([
        "🏢 Wszystkie stanowiska (Podgląd)",
        f"🚗 Stanowisko 1 ({len(st1_apps)} zajęte)",
        f"🚙 Stanowisko 2 ({len(st2_apps)} zajęte)",
        "💳 Cennik Usług"
    ])

    with tab_all:
        col_st1, col_st2 = st.columns(2)
        with col_st1:
            st.markdown(f"""
            <div class="station-column-header">
                <div class="station-title">🚗 Stanowisko 1 (Podnośnik A)</div>
                <div class="station-badge-count {'count-busy' if st1_apps else 'count-free'}">
                    {'● Zajęte: ' + str(len(st1_apps)) if st1_apps else '✓ Dostępne'}
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st1_apps:
                for app in sorted(st1_apps, key=lambda x: x.get("startTime", "")):
                    render_app_card(app)
            else:
                st.info("✓ Wszystkie godziny wolne na Stanowisku 1!")

        with col_st2:
            st.markdown(f"""
            <div class="station-column-header">
                <div class="station-title">🚙 Stanowisko 2 (Podnośnik B)</div>
                <div class="station-badge-count {'count-busy' if st2_apps else 'count-free'}">
                    {'● Zajęte: ' + str(len(st2_apps)) if st2_apps else '✓ Dostępne'}
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st2_apps:
                for app in sorted(st2_apps, key=lambda x: x.get("startTime", "")):
                    render_app_card(app)
            else:
                st.info("✓ Wszystkie godziny wolne na Stanowisku 2!")

    with tab_st1:
        st.markdown("#### 🚗 Stanowisko 1 (Podnośnik A)")
        if st1_apps:
            for app in sorted(st1_apps, key=lambda x: x.get("startTime", "")):
                render_app_card(app)
        else:
            st.success("✓ Stanowisko 1 jest wolne w wybranym dniu!")

    with tab_st2:
        st.markdown("#### 🚙 Stanowisko 2 (Podnośnik B)")
        if st2_apps:
            for app in sorted(st2_apps, key=lambda x: x.get("startTime", "")):
                render_app_card(app)
        else:
            st.success("✓ Stanowisko 2 jest wolne w wybranym dniu!")

    with tab_prices:
        st.markdown("#### 💳 Oficjalny Cennik Usług Wymiany i Serwisu Opon")
        df_p = pd.DataFrame(app_config.get("services", []))
        if not df_p.empty:
            st.dataframe(df_p[["name", "durationMinutes", "price"]].rename(columns={
                "name": "Nazwa Usługi",
                "durationMinutes": "Czas trwania (min)",
                "price": "Cena (PLN)"
            }), use_container_width=True)

    st.markdown("---")
    st.info("💡 **Chcesz zarezerwować termin?** Zadzwoń pod numer **600 223 669**.")


# ==========================================================
# 2. KALENDARZ WIZYT (ADMIN DLA ZALOGOWANYCH)
# ==========================================================
elif menu_choice == "📅 Kalendarz Wizyt (Admin)" and st.session_state["authenticated"]:
    st.header("📅 Zarządzanie Wizytami i Terminarzem")

    # --- MODUŁ 1: INTELIGENTNY ASYSTENT PLANOWANIA AI (GEMINI) ---
    with st.expander("🤖 Asystent Planowania AI (Google Gemini / Szybkie komendy)", expanded=True):
        st.markdown("""
        <p style="font-size: 13px; color: #94a3b8; margin-bottom: 8px;">
            Wpisz polecenie w języku naturalnym, np. <em>"wpisz na piątek 13-go listopada Alu premium pierwszy wolny termin Stanowisko 2 Akronim Wojtek, rejestracja PRA 999WX"</em>
        </p>
        """, unsafe_allow_html=True)

        chip_c1, chip_c2, chip_c3 = st.columns(3)
        if chip_c1.button("⚡ Wpisz Bolka na jutro na Alu Premium", use_container_width=True):
            st.session_state["ai_cmd_input"] = "wpisz Bolka na jutro na Alu Premium pierwszy wolny termin"
        if chip_c2.button("🔍 Wolny termin na koła stalowe", use_container_width=True):
            st.session_state["ai_cmd_input"] = "podaj najbliższy wolny termin na koła stalowe"
        if chip_c3.button("📅 Bolek na jutro na 14:00 (Alu)", use_container_width=True):
            st.session_state["ai_cmd_input"] = "wpisz Bolka na jutro na 14:00 koła aluminiowe"

        cmd_val = st.text_area(
            "Polecenie dla Asystenta:",
            value=st.session_state.get("ai_cmd_input", "wpisz na piątek 13-go listopada Alu premium pierwszy wolny termin Stanowisko 2 Akronim Wojtek, rejestracja PRA 999WX"),
            height=70
        )

        ac_c1, ac_c2 = st.columns([1, 2])
        if ac_c1.button("✨ Wykonaj polecenie z Gemini", type="primary", use_container_width=True):
            res = parse_ai_prompt(cmd_val, db_data.get("appointments", []), app_config)
            if res and res.get("slot"):
                st.session_state["ai_proposed_visit"] = res
            else:
                st.warning("Nie znaleziono pasującego wolnego terminu dla podanych kryteriów.")

        if st.session_state.get("ai_proposed_visit"):
            prop = st.session_state["ai_proposed_visit"]
            pslot = prop["slot"]
            psrv = prop["service"]
            st.markdown(f"""
            <div class="slot-result-card">
                <div class="slot-result-title">🤖 Agent znalazł termin i przygotował wizytę!</div>
                <div style="font-size: 14px; color: #e2e8f0; line-height: 1.6;">
                    Znalazłem wolny termin na <strong>{pslot['date']}</strong> w godzinach <strong>{pslot['startTime']} – {pslot['endTime']}</strong> ({pslot['durationMinutes']} min).<br>
                    Klient: <strong>{prop['client']}</strong> | Rejestracja: <strong>{prop['plate'] or 'Brak'}</strong> | Stanowisko: <strong>Stanowisko {pslot['station']} (Podnośnik {'A' if pslot['station']==1 else 'B'})</strong><br>
                    Usługa: <strong>{psrv.get('name')}</strong> | Cena usługi: <strong style="color: #38bdf8;">{prop['price']} zł</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

            prop_save_c1, prop_save_c2 = st.columns([1, 1])
            if prop_save_c1.button("✓ Zapisz i dodaj tę wizytę do kalendarza", type="primary", use_container_width=True):
                new_app = {
                    "id": f"app_{int(datetime.now().timestamp())}",
                    "date": pslot["date"],
                    "startTime": pslot["startTime"],
                    "endTime": pslot["endTime"],
                    "station": int(pslot["station"]),
                    "carLicensePlate": prop["plate"],
                    "clientAcronym": prop["client"],
                    "clientPhone": "",
                    "serviceId": psrv.get("id", "srv"),
                    "serviceName": psrv.get("name"),
                    "durationMinutes": int(pslot["durationMinutes"]),
                    "price": float(prop["price"]),
                    "status": "planned"
                }
                db_data["appointments"].append(new_app)
                save_db(db_data)
                st.session_state["ai_proposed_visit"] = None
                st.session_state["cal_date"] = datetime.strptime(pslot["date"], "%Y-%m-%d").date()
                st.success("Pomyślnie dodano wizytę!")
                st.rerun()

            if prop_save_c2.button("Anuluj", use_container_width=True):
                st.session_state["ai_proposed_visit"] = None
                st.rerun()

    # --- MODUŁ 2: SZYBKIE WYSZUKIWANIE WOLNEGO TERMINU ---
    with st.expander("⚡ Szybka Wyszukiwarka Pierwszego Wolnego Terminu", expanded=False):
        sf_c1, sf_c2, sf_c3, sf_c4 = st.columns([2, 1, 1, 1])
        services = app_config.get("services", [])
        srv_opts = {f"{s.get('name')} ({s.get('price')} zł, {s.get('durationMinutes')}m)": s for s in services}
        chosen_sf_srv = sf_c1.selectbox("Wybierz usługę:", list(srv_opts.keys()))
        target_sf_obj = srv_opts[chosen_sf_srv]
        sf_st = sf_c2.selectbox("Preferowane stanowisko:", [0, 1, 2], format_func=lambda x: "Dowolne" if x==0 else f"Stanowisko {x}")
        sf_d = sf_c3.date_input("Szukaj od dnia:", value=date.today())
        
        if sf_c4.button("🔍 Znajdź termin", type="primary", use_container_width=True):
            slot = find_first_free_slot(db_data.get("appointments", []), app_config, target_sf_obj.get("durationMinutes", 45), sf_d, sf_st)
            if slot:
                st.session_state["admin_found_slot"] = {
                    "slot": slot,
                    "service": target_sf_obj
                }
            else:
                st.session_state["admin_found_slot"] = None
                st.warning("Brak wolnych terminów.")

        if st.session_state.get("admin_found_slot"):
            fs = st.session_state["admin_found_slot"]["slot"]
            so = st.session_state["admin_found_slot"]["service"]
            st.success(f"Znaleziono wolny slot: {fs['date']} | Godz. {fs['startTime']} - {fs['endTime']} | Stanowisko {fs['station']} | Koszt: {so.get('price')} zł")
            if st.button("📅 Wstaw ten termin do poniższego formularza"):
                st.session_state["form_prefill"] = {
                    "date": datetime.strptime(fs["date"], "%Y-%m-%d").date(),
                    "start": fs["startTime"],
                    "station": fs["station"],
                    "service": so
                }
                st.rerun()

    st.markdown("---")

    # --- MODUŁ 3: LISTA WIZYT W WYBRANYM DNIU + PODSUMOWANIE FINANSOWE ---
    adm_date = st.date_input("Wybierz dzień kalendarza do edycji:", value=st.session_state.get("cal_date", date.today()))
    d_str = adm_date.strftime("%Y-%m-%d")

    apps = db_data.get("appointments", [])
    matching = [a for a in apps if a.get("date") == d_str]
    total_rev = sum(float(a.get("price", 0)) for a in matching)

    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Zapisanych aut w tym dniu", len(matching))
    m_col2.metric("Suma wartości usług", f"{total_rev:.0f} zł")
    m_col3.metric("Stanowisko 1 / Stanowisko 2", f"{sum(1 for a in matching if int(a.get('station',1))==1)} / {sum(1 for a in matching if int(a.get('station',1))==2)}")

    if matching:
        df_apps = pd.DataFrame(matching)
        cols_show = ["startTime", "endTime", "station", "carLicensePlate", "clientAcronym", "clientPhone", "serviceName", "price", "status"]
        valid_cols = [c for c in cols_show if c in df_apps.columns]
        st.dataframe(df_apps[valid_cols].rename(columns={
            "startTime": "Od",
            "endTime": "Do",
            "station": "Stanowisko",
            "carLicensePlate": "Rejestracja",
            "clientAcronym": "Akronim",
            "clientPhone": "Telefon",
            "serviceName": "Usługa",
            "price": "Cena",
            "status": "Status"
        }), use_container_width=True)

        st.subheader("Usuń wybraną wizytę")
        del_opts = {f"{a.get('startTime')}-{a.get('endTime')} | St.{a.get('station')} | {a.get('carLicensePlate')} ({a.get('clientAcronym')}) - {a.get('serviceName')}": a.get("id") for a in matching}
        chosen_del = st.selectbox("Wybierz wizytę do usunięcia:", list(del_opts.keys()))
        if st.button("🗑️ Usuń tę wizytę z kalendarza"):
            aid = del_opts[chosen_del]
            db_data["appointments"] = [a for a in apps if a.get("id") != aid]
            save_db(db_data)
            st.success("Usunięto wizytę.")
            st.rerun()
    else:
        st.info("Brak zarezerwowanych wizyt w tym dniu.")

    st.markdown("---")

    # --- MODUŁ 4: FORMULARZ DODAWANIA WIZYTY Z PODGLĄDEM CENY I CZASU ---
    st.subheader("➕ Dodaj nową wizytę ręcznie")
    
    prefill = st.session_state.get("form_prefill", {})

    with st.form("manual_appointment_form"):
        fa1, fa2, fa3 = st.columns(3)
        a_plate = fa1.text_input("Numer Rejestracyjny *", value=prefill.get("plate", "")).upper().strip()
        a_client = fa2.text_input("Akronim / Imię Klienta *", value=prefill.get("client", ""), placeholder="np. Nowak")
        a_phone = fa3.text_input("Telefon kontaktowy", placeholder="np. 600 123 456")

        fa4, fa5, fa6 = st.columns(3)
        services = app_config.get("services", [])
        srv_opts = {f"{s.get('name')} - {s.get('price')} zł ({s.get('durationMinutes')} min)": s for s in services}
        chosen_srv_key = fa4.selectbox("Wybierz usługę:", list(srv_opts.keys()))
        selected_srv = srv_opts[chosen_srv_key]

        a_station = fa5.selectbox(
            "Stanowisko:",
            [1, 2],
            index=1 if prefill.get("station") == 2 else 0,
            format_func=lambda x: f"Stanowisko {x} (Podnośnik {'A' if x==1 else 'B'})"
        )
        a_start = fa6.text_input("Godzina rozpoczęcia (HH:MM):", value=prefill.get("start", "09:00"))

        fa7, fa8 = st.columns(2)
        dur = selected_srv.get("durationMinutes", 45)
        default_p = selected_srv.get("price", 140)
        a_price = fa7.number_input("Cena usługi (PLN):", value=float(default_p), step=10.0)

        # Wyliczenie godziny zakończenia
        try:
            sh, sm = map(int, a_start.split(":"))
            end_m_calc = sh * 60 + sm + dur
            calc_end_str = f"{end_m_calc // 60:02d}:{end_m_calc % 60:02d}"
        except Exception:
            calc_end_str = "09:45"

        fa8.info(f"⏱️ **Czas trwania:** {dur} min | ⏰ **Koniec wizyty:** {calc_end_str}")

        if st.form_submit_button("💾 Dodaj wizytę do terminarza", type="primary"):
            if not a_plate or not a_client:
                st.error("Wpisz numer rejestracyjny i nazwisko/akronim klienta.")
            else:
                new_app = {
                    "id": f"app_{int(datetime.now().timestamp())}",
                    "date": d_str,
                    "startTime": a_start,
                    "endTime": calc_end_str,
                    "station": int(a_station),
                    "carLicensePlate": a_plate,
                    "clientAcronym": a_client,
                    "clientPhone": a_phone,
                    "serviceId": selected_srv.get("id", "srv"),
                    "serviceName": selected_srv.get("name"),
                    "durationMinutes": dur,
                    "price": float(a_price),
                    "status": "planned"
                }
                db_data["appointments"].append(new_app)
                save_db(db_data)
                st.session_state["form_prefill"] = {}
                st.success("Dodano wizytę do kalendarza!")
                st.rerun()


# ==========================================================
# 3. DASHBOARD & MAGAZYN OPON (DLA ZALOGOWANYCH)
# ==========================================================
elif menu_choice == "📊 Dashboard & Magazyn Opon" and st.session_state["authenticated"]:
    st.header("📊 Stan Magazynu Opon")

    deposits = db_data.get("deposits", [])
    count_wiata = sum(1 for d in deposits if str(d.get("location", "")).lower() == "wiata")
    count_tdol = sum(1 for d in deposits if str(d.get("location", "")).lower() in ["tdół", "tdol"])
    count_tgora = sum(1 for d in deposits if str(d.get("location", "")).lower() in ["tgóra", "tgora"])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 Łącznie Depozytów", len(deposits))
    m2.metric("Wiata", count_wiata)
    m3.metric("Tdół", count_tdol)
    m4.metric("Tgóra", count_tgora)

    # Opony zalegające > 180 dni
    aging = [d for d in deposits if calculate_days(d.get("depositDate", "")) >= 180]
    if aging:
        st.warning(f"⚠️ **Wykryto {len(aging)} depozytów zalegających powyżej 180 dni!**")
        df_ag = pd.DataFrame(aging)
        df_ag["Dni"] = df_ag["depositDate"].apply(calculate_days)
        st.dataframe(df_ag[["carLicensePlate", "clientName", "clientPhone", "tireBrand", "tireSize", "location", "depositDate", "Dni"]].rename(columns={
            "carLicensePlate": "Rejestracja",
            "clientName": "Klient",
            "clientPhone": "Telefon",
            "tireBrand": "Marka",
            "tireSize": "Rozmiar",
            "location": "Lokalizacja",
            "depositDate": "Przyjęto"
        }), use_container_width=True)

    st.subheader("Baza Wszystkich Depozytów")
    c_s, c_f = st.columns([3, 1])
    search_q = c_s.text_input("🔍 Wyszukaj (rejestracja, klient, telefon, opony):", "").lower().strip()
    loc_filter = c_f.selectbox("Filtruj lokalizację:", ["Wszystkie", "wiata", "Tdół", "Tgóra"])

    filtered = []
    for d in deposits:
        if loc_filter != "Wszystkie" and str(d.get("location", "")).lower() != loc_filter.lower():
            continue
        full_text = f"{d.get('carLicensePlate','')} {d.get('clientName','')} {d.get('clientPhone','')} {d.get('tireBrand','')} {d.get('tireSize','')}".lower()
        if search_q in full_text:
            filtered.append(d)

    if filtered:
        df_main = pd.DataFrame(filtered)
        col_names = {
            "carLicensePlate": "Nr Rejestracyjny",
            "clientName": "Klient",
            "clientPhone": "Telefon",
            "tireBrand": "Marka",
            "tireSize": "Rozmiar",
            "tireSeason": "Sezon",
            "quantity": "Sztuki",
            "location": "Lokalizacja",
            "depositDate": "Data Przyjęcia",
            "price": "Cena (PLN)",
            "notes": "Uwagi"
        }
        st.dataframe(df_main[[c for c in col_names.keys() if c in df_main.columns]].rename(columns=col_names), use_container_width=True)

        # Eksport Excel
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='openpyxl') as wr:
            df_main.to_excel(wr, index=False, sheet_name='Magazyn_Opon')
        st.download_button(
            "📥 Pobierz stan magazynu (.xlsx)",
            data=out.getvalue(),
            file_name=f"stan_magazynu_{date.today().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown("---")
        st.subheader("Wydanie depozytu klientowi")
        col_sel, col_btn = st.columns([3, 1])
        opts = {f"{d.get('carLicensePlate')} - {d.get('clientName')} ({d.get('tireSize')})": d.get("id") for d in deposits}
        chosen_dep = col_sel.selectbox("Wybierz opony do wydania:", options=list(opts.keys()))
        if col_btn.button("✓ Wydaj Opony", type="primary"):
            tid = opts[chosen_dep]
            target_dep = next((d for d in deposits if d.get("id") == tid), None)
            if target_dep:
                target_dep["status"] = "released"
                target_dep["releaseDate"] = date.today().strftime("%Y-%m-%d")
                db_data["deposits"] = [d for d in deposits if d.get("id") != tid]
                db_data["archive"].insert(0, target_dep)
                save_db(db_data)
                st.success(f"Wydano opony dla rejestracji {target_dep.get('carLicensePlate')}!")
                st.rerun()
    else:
        st.info("Brak depozytów spełniających kryteria.")


# ==========================================================
# 4. PRZYJMIJ NOWY DEPOZYT (DLA ZALOGOWANYCH)
# ==========================================================
elif menu_choice == "➕ Przyjmij Nowy Depozyt" and st.session_state["authenticated"]:
    st.header("➕ Przyjęcie Nowego Depozytu Opon")
    with st.form("new_deposit"):
        c1, c2 = st.columns(2)
        c_name = c1.text_input("Imię i Nazwisko / Nazwa Klienta *")
        c_phone = c2.text_input("Numer Telefonu *")
        c_email = c1.text_input("Adres E-mail (opcjonalnie)")
        c_plate = c2.text_input("Numer Rejestracyjny Pojazdu *").upper().strip()

        c3, c4, c5 = st.columns(3)
        t_size = c3.text_input("Rozmiar Opon *", placeholder="np. 205/55 R16")
        t_brand = c4.text_input("Marka Opon", placeholder="np. Michelin, Dębica")
        t_season = c5.selectbox("Sezon Opon", ["Zimowe", "Letnie", "Całoroczne"])

        c6, c7, c8 = st.columns(3)
        t_rim = c6.selectbox("Felgi", ["Brak (same opony)", "Aluminiowe", "Stalowe"])
        t_qty = c7.number_input("Liczba sztuk", min_value=1, max_value=8, value=4)
        t_loc = c8.selectbox("Lokalizacja w Magazynie *", ["wiata", "Tdół", "Tgóra"])

        c9, c10 = st.columns(2)
        t_date = c9.date_input("Data przyjęcia", value=date.today())
        t_price = c10.number_input("Cena przechowania (PLN)", value=140, step=10)
        t_notes = st.text_area("Uwagi do depozytu")

        if st.form_submit_button("💾 Zapisz Depozyt w Magazynie", type="primary"):
            if not c_name or not c_phone or not c_plate or not t_size:
                st.error("Wypełnij wymagane pola: Klient, Telefon, Rejestracja, Rozmiar.")
            else:
                new_item = {
                    "id": f"dep_{int(datetime.now().timestamp())}",
                    "clientName": c_name.strip(),
                    "clientPhone": c_phone.strip(),
                    "clientEmail": c_email.strip(),
                    "carLicensePlate": c_plate,
                    "tireSize": t_size.strip(),
                    "tireBrand": t_brand.strip(),
                    "tireSeason": t_season,
                    "tireRimType": t_rim,
                    "quantity": int(t_qty),
                    "location": t_loc,
                    "depositDate": t_date.strftime("%Y-%m-%d"),
                    "price": float(t_price),
                    "notes": t_notes.strip(),
                    "status": "active"
                }
                db_data["deposits"].insert(0, new_item)
                save_db(db_data)
                st.success(f"Przyjęto opony pojazdu {c_plate} do lokalizacji {t_loc}!")
                st.balloons()


# ==========================================================
# 5. ARCHIWUM WYDANYCH OPON (DLA ZALOGOWANYCH)
# ==========================================================
elif menu_choice == "📜 Archiwum Wydanych Opon" and st.session_state["authenticated"]:
    st.header("📜 Archiwum Wydanych Depozytów")
    archive = db_data.get("archive", [])
    if archive:
        df_arch = pd.DataFrame(archive)
        cols_arch = {
            "carLicensePlate": "Nr Rejestracyjny",
            "clientName": "Klient",
            "clientPhone": "Telefon",
            "tireBrand": "Marka",
            "tireSize": "Rozmiar",
            "location": "Była Lokalizacja",
            "depositDate": "Data Przyjęcia",
            "releaseDate": "Data Wydania"
        }
        st.dataframe(df_arch[[c for c in cols_arch.keys() if c in df_arch.columns]].rename(columns=cols_arch), use_container_width=True)
    else:
        st.info("Archiwum jest puste. Brak historii wydanych opon.")


# ==========================================================
# 6. KONFIGURACJA & UPRAWNIENIA (DLA ZALOGOWANYCH)
# ==========================================================
elif menu_choice == "⚙️ Konfiguracja & Uprawnienia" and st.session_state["authenticated"]:
    st.header("⚙️ Konfiguracja i Uprawnienia Pracowników")

    with st.form("cfg_form"):
        st.subheader("Dostęp i Bezpieczeństwo")
        curr_pwd = app_config.get("adminPassword", "admin")
        new_pwd = st.text_input("Hasło do Panelu Warsztatu:", value=curr_pwd, type="password")

        curr_emails = app_config.get("allowedEmails", ["michal@twoje4kola.pl", "alert@itover.pl"])
        emails_str = ", ".join(curr_emails) if isinstance(curr_emails, list) else str(curr_emails)
        new_emails = st.text_area("Uprawnione adresy e-mail pracowników (rozdzielone przecinkami):", value=emails_str)

        st.subheader("Ustawienia Terminarza Publicznego")
        curr_hdr = app_config.get("publicHeader", "Wulkanizacja Michał - rezerwacja terminu 600223669")
        new_hdr = st.text_input("Tekst w banerze kontaktowym:", value=curr_hdr)

        st.subheader("Słownik Usług i Domyślne Ceny")
        st.caption("Ceny i czasy trwania wykorzystywane przez Asystenta AI oraz formularz wizyt:")
        df_services = pd.DataFrame(app_config.get("services", []))
        st.dataframe(df_services, use_container_width=True)

        if st.form_submit_button("💾 Zapisz Konfigurację", type="primary"):
            app_config["adminPassword"] = new_pwd.strip()
            parsed_emails = [e.strip().lower() for e in new_emails.split(",") if e.strip()]
            app_config["allowedEmails"] = parsed_emails
            app_config["publicHeader"] = new_hdr.strip()
            save_config(app_config)
            st.success("Zapisano nową konfigurację!")
            st.rerun()
