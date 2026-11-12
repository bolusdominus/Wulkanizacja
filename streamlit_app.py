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
    initial_sidebar_state="expanded"
)

# Ścieżki do plików
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.json")
CONFIG_FILE = os.path.join(BASE_DIR, "calendar_config.json")
PUBLIC_CONFIG_FILE = os.path.join(BASE_DIR, "public", "calendar_config.json")

# --- WSTRZYKIWANIE STYLÓW DARK MODE (MOBILE & PC) ---
st.markdown("""
<style>
    /* Globalne tło aplikacji */
    .stApp {
        background-color: #0b0f19 !important;
        color: #f8fafc !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    }

    /* Marginesy kontenera głównego */
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

    /* Etykiety grup w pasku bocznym */
    .nav-group-title {
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-top: 14px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .group-cal {
        color: #38bdf8;
    }
    .group-mag {
        color: #34d399;
    }
    .group-sys {
        color: #94a3b8;
    }

    /* Przyciski nawigacyjne w panelu bocznym */
    [data-testid="stSidebar"] button {
        margin-bottom: 4px !important;
        text-align: center !important;
        justify-content: center !important;
        font-size: 13.5px !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        min-height: 42px !important;
        padding: 4px 8px !important;
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
        min-height: 40px !important;
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

    /* Baner z telefonem */
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

    /* Kafelki wizyt w kalendarzu (kompaktowe, aby zmieścić cały dzień) */
    .app-card-box {
        background: #151d30;
        border-radius: 8px;
        padding: 6px 9px;
        margin-bottom: 5px;
        border: 1px solid #23314d;
        box-shadow: 0 2px 6px rgba(0,0,0,0.25);
    }
    .app-card-box.type-stal {
        border-color: #38bdf8;
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.18), rgba(15, 23, 42, 0.95));
    }
    .app-card-box.type-alu {
        border-color: #34d399;
        background: linear-gradient(135deg, rgba(5, 150, 105, 0.18), rgba(15, 23, 42, 0.95));
    }
    .app-card-box.type-alupremium {
        border-color: #c084fc;
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.18), rgba(15, 23, 42, 0.95));
    }
    .app-card-box.type-bus {
        border-color: #fcd34d;
        background: linear-gradient(135deg, rgba(217, 119, 6, 0.18), rgba(15, 23, 42, 0.95));
    }
    .app-card-box.type-szybki {
        border-color: #f472b6;
        background: linear-gradient(135deg, rgba(219, 39, 119, 0.18), rgba(15, 23, 42, 0.95));
    }

    .card-top-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 3px;
    }
    .time-badge {
        font-size: 12px;
        font-weight: 800;
        color: #ffffff;
        background: rgba(0, 0, 0, 0.45);
        padding: 1px 6px;
        border-radius: 4px;
        border: 1px solid rgba(255, 255, 255, 0.12);
    }
    .duration-badge {
        font-size: 10.5px;
        font-weight: 700;
        color: #94a3b8;
    }
    .service-badge {
        font-size: 12px;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.25;
    }

    /* Pasek szczegółów w karcie wizyty (Admin) */
    .admin-app-details {
        margin-top: 4px;
        padding-top: 3px;
        border-top: 1px dashed rgba(255, 255, 255, 0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 4px;
    }
    .admin-plate-pill {
        background: rgba(255, 255, 255, 0.12);
        color: #ffffff;
        padding: 1px 6px;
        border-radius: 4px;
        font-weight: 800;
        font-size: 11.5px;
        letter-spacing: 0.3px;
    }
    .admin-client-pill {
        background: rgba(56, 189, 248, 0.18);
        color: #38bdf8;
        padding: 1px 6px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 11.5px;
    }
    .admin-price-pill {
        background: rgba(16, 185, 129, 0.18);
        color: #34d399;
        padding: 1px 6px;
        border-radius: 4px;
        font-weight: 800;
        font-size: 11.5px;
    }

    /* Wolne okna czasowe w kalendarzu */
    .free-slot-card {
        background: rgba(16, 185, 129, 0.05);
        border: 1px dashed rgba(16, 185, 129, 0.32);
        border-radius: 6px;
        padding: 4px 8px;
        margin-bottom: 5px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #34d399;
        font-size: 11px;
        font-weight: 600;
        transition: all 0.15s ease;
    }
    .free-slot-card:hover {
        background: rgba(16, 185, 129, 0.12);
        border-color: #34d399;
    }

    /* Kafelki w widoku tygodnia */
    .week-col-box {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 8px 6px;
        margin-bottom: 8px;
    }
    .week-col-box.is-today {
        border-color: #38bdf8;
        background: linear-gradient(180deg, rgba(56, 189, 248, 0.1), #111827);
    }
    .week-col-box.is-selected {
        border: 1.5px solid #a855f7;
    }
    .week-header-title {
        font-size: 12.5px;
        font-weight: 800;
        color: #f8fafc;
        text-align: center;
    }
    .week-header-sub {
        font-size: 10px;
        color: #94a3b8;
        text-align: center;
        margin-bottom: 4px;
    }
    .week-badge-free {
        font-size: 9.5px;
        font-weight: 700;
        padding: 1px 5px;
        border-radius: 4px;
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        display: block;
        text-align: center;
        margin-bottom: 6px;
    }
    .week-mini-app {
        background: #1e293b;
        border-left: 3px solid #38bdf8;
        border-radius: 4px;
        padding: 3px 5px;
        margin-bottom: 4px;
        font-size: 10px;
        line-height: 1.3;
    }
    .week-mini-app.st2 {
        border-left-color: #c084fc;
    }

    /* Kompaktowe wskaźniki metryk (dashboard i kalendarz) */
    .compact-metric-card {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 6px 12px;
        margin-bottom: 8px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.25);
    }
    .metric-card-label {
        font-size: 11px;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-bottom: 2px;
    }
    .metric-card-value {
        font-size: 18px;
        font-weight: 800;
        color: #38bdf8;
        line-height: 1.2;
    }

    /* Pomniejszenie standardowych metryk st.metric */
    [data-testid="stMetric"] {
        background: #111827 !important;
        border: 1px solid #1e293b !important;
        border-radius: 8px !important;
        padding: 6px 12px !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.2) !important;
    }
    [data-testid="stMetricLabel"] p, [data-testid="stMetricLabel"] label {
        font-size: 11px !important;
        font-weight: 700 !important;
        color: #94a3b8 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.3px !important;
        margin: 0 !important;
    }
    [data-testid="stMetricValue"] div, [data-testid="stMetricValue"] {
        font-size: 18px !important;
        font-weight: 800 !important;
        color: #38bdf8 !important;
        line-height: 1.2 !important;
    }

    /* Karta wyniku wyszukiwania terminu */
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

# --- ALGORYTM WYSZUKIWANIA NAJBLIŻSZEGO WOLNEGO TERMINU Z OGRANICZENIAMI CZASOWYMI ---
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

def find_first_free_slot(appointments, cfg, duration=45, start_from=None, station_pref=0, min_time_m=None, max_time_m=None, exact_time_m=None, exact_day_only=False):
    if not start_from:
        start_from = date.today()
    cur_d = start_from
    max_days = 1 if exact_day_only else 30

    for _ in range(max_days):
        wh = get_working_hours(cur_d, cfg)
        if wh:
            d_str = cur_d.strftime("%Y-%m-%d")
            sh, sm = map(int, wh["start"].split(":"))
            eh, em = map(int, wh["end"].split(":"))
            day_start_m = sh * 60 + sm
            day_end_m = eh * 60 + em

            # Jeśli szukamy w dzisiejszym dniu, nie proponuj przeszłych godzin
            if cur_d == date.today():
                now_m = datetime.now().hour * 60 + datetime.now().minute
                if now_m > day_start_m:
                    day_start_m = ((now_m + 15) // 15) * 15

            # Ograniczenie min_time_m (np. "po 12-tej", "po południu")
            if min_time_m is not None and min_time_m > day_start_m:
                day_start_m = min_time_m

            # Ograniczenie max_time_m (np. "rano", "przed 12:00")
            search_end_m = day_end_m
            if max_time_m is not None and max_time_m < search_end_m:
                search_end_m = max_time_m

            day_apps = [a for a in appointments if a.get("date") == d_str]
            stations = [station_pref] if station_pref in [1, 2] else [1, 2]

            # Jeśli podano konkretną godzinę (np. "na 14:00")
            if exact_time_m is not None:
                s = exact_time_m
                e = s + duration
                if s >= day_start_m and e <= day_end_m:
                    for st in stations:
                        collision = False
                        for a in day_apps:
                            if int(a.get("station", 1)) == st:
                                ash, asm = map(int, a.get("startTime", "00:00").split(":"))
                                aeh, aem = map(int, a.get("endTime", "00:00").split(":"))
                                if (ash * 60 + asm) < e and (aeh * 60 + aem) > s:
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

            # Wyszukiwanie pierwszego pasującego slotu co 15 minut
            for s in range(day_start_m, search_end_m - duration + 1, 15):
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

# --- PARSER INTELIGENTNEGO ASYSTENTA AI Z OBSŁUGĄ PÓR DNIA I GODZIN ---
def parse_ai_prompt(prompt_text, appointments, cfg):
    p = prompt_text.lower().strip()
    services = cfg.get("services", [])
    
    # 1. Wykrycie usługi
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
    if "stanowisko 2" in p or "podnośnik b" in p or "st 2" in p or "st. 2" in p:
        station = 2
    elif "stanowisko 1" in p or "podnośnik a" in p or "st 1" in p or "st. 1" in p:
        station = 1

    # 3. Preferencje godzinowe (po 12-tej, po południu, rano, o 14:00)
    min_time_m = None
    max_time_m = None
    exact_time_m = None

    # Po godzinie X / po X
    m_po = re.search(r'po\s+(?:godz(?:inie|\.)?\s*)?(\d{1,2})(?::(\d{2}))?', p)
    if m_po:
        h = int(m_po.group(1))
        m = int(m_po.group(2)) if m_po.group(2) else 0
        min_time_m = h * 60 + m
    elif "po południu" in p or "popołudniu" in p or "po poludniu" in p:
        min_time_m = 12 * 60  # Po 12:00

    # Przed godziną X / rano
    m_przed = re.search(r'przed\s+(?:godz(?:iną|\.)?\s*)?(\d{1,2})(?::(\d{2}))?', p)
    if m_przed:
        h = int(m_przed.group(1))
        m = int(m_przed.group(2)) if m_przed.group(2) else 0
        max_time_m = h * 60 + m
    elif "rano" in p or "z rana" in p or "przed południem" in p or "przed poludniem" in p:
        max_time_m = 12 * 60  # Przed 12:00

    # Dokładna godzina (np. na 14:00, o 10:30)
    m_exact = re.search(r'(?:na|o|godz(?:ina|\.)?)\s+(\d{1,2}):(\d{2})', p)
    if not m_exact:
        m_exact = re.search(r'(?:o|na)\s+(\d{1,2})\s*(?:-ej|-tej|\.|\b)', p)
    if m_exact:
        eh = int(m_exact.group(1))
        em = int(m_exact.group(2)) if m_exact.lastindex >= 2 and m_exact.group(2) else 0
        if 7 <= eh <= 20:
            exact_time_m = eh * 60 + em

    # 4. Wykrycie daty i dnia tygodnia
    target_d = date.today()
    exact_day_only = False

    if "jutro" in p:
        target_d = date.today() + timedelta(days=1)
        exact_day_only = True
    elif "pojutrze" in p:
        target_d = date.today() + timedelta(days=2)
        exact_day_only = True
    else:
        weekdays_map = {
            "poniedział": 0, "wtorek": 1, "wtork": 1, "środ": 2, "srod": 2,
            "czwartek": 3, "czwartk": 3, "piątek": 4, "piatk": 4, "sobot": 5
        }
        for k, v in weekdays_map.items():
            if k in p:
                diff = (v - date.today().weekday()) % 7
                if diff == 0 and ("dziś" not in p and "dzisiaj" not in p):
                    diff = 7
                target_d = date.today() + timedelta(days=diff)
                exact_day_only = True
                break
        
        # Konkretna data z nazwą miesiąca (np. "15 listopada") - nie mylić z godziną "12-tej"!
        m_date_cal = re.search(r'(?:dnia\s+)?(\d{1,2})(?:-go|-ego)?\s+(stycz|lut|mar|kwie|maj|czerw|lip|sierp|wrze|pa[źz]dz|listopad|grud)', p)
        if m_date_cal and m_date_cal.group(1):
            try:
                target_d = target_d.replace(day=int(m_date_cal.group(1)))
                exact_day_only = True
            except Exception:
                pass

    # 5. Numer rejestracyjny (odrzucamy słowa bez cyfr typu 'NA JUTRO')
    plate = ""
    # Szukamy wyraźnego znacznika "nr rej. PRA1234", "rej: PRA 1234", "rejestracja WI12345"
    m_rej_direct = re.search(r'(?:nr\s*rej(?:\.|\:)?|rejestracja|nr|rej(?:\.|\:)?)\s*[:=]?\s*([A-Za-z]{1,3}\s*[0-9A-Za-z]{4,5})\b', prompt_text, re.IGNORECASE)
    if m_rej_direct:
        cand = m_rej_direct.group(1).strip().upper().replace(" ", "")
        if any(c.isdigit() for c in cand) and any(c.isalpha() for c in cand):
            if not any(w in cand for w in ["ALU", "BUS", "STAL", "PREMIUM", "KLIENT"]):
                plate = cand

    if not plate:
        plate_candidates = re.findall(r'\b([A-Z]{2,3})\s*([0-9][0-9A-Z]{3,4}|[0-9A-Z]{1,2}[0-9][0-9A-Z]{1,2})\b', prompt_text.upper())
        for p_pre, p_suf in plate_candidates:
            cand = f"{p_pre}{p_suf}".replace(" ", "")
            if cand not in ["ALU17", "ALU18", "BUS1", "STAL1"]:
                plate = cand
                break

    # 6. Akronim / Klient
    client_name = "KLIENT"
    # Sprawdzamy "Klient Olek", "Akronim: Olek", "dla Olka"
    m_client_direct = re.search(r'(?:klient|akronim|dla)\s*[:=-]?\s*([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9]+)', prompt_text, re.IGNORECASE)
    if m_client_direct:
        cand = m_client_direct.group(1).strip().capitalize()
        if cand.upper() not in ["KLIENT", "AKRONIM"]:
            client_name = cand
    else:
        # Sprawdzamy "wpisz Bolka..."
        m_wpisz = re.search(r'wpisz\s+([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]+)', prompt_text, re.IGNORECASE)
        if m_wpisz:
            cand = m_wpisz.group(1).strip().capitalize()
            stopwords = ["Na", "W", "Do", "Jutro", "Pojutrze", "Pierwszy", "Wolny", "Termin", "Piątek", "Sobota", "Poniedziałek", "Wtorek", "Środa", "Czwartek", "Alu", "Stal", "Premium", "Bus", "Szybki", "Stanowisko", "Podnośnik"]
            if cand not in stopwords:
                client_name = cand

    # 7. Wyszukanie slotu z uwzględnieniem pory dnia i stanowiska
    slot = find_first_free_slot(
        appointments, cfg, dur,
        start_from=target_d,
        station_pref=station,
        min_time_m=min_time_m,
        max_time_m=max_time_m,
        exact_time_m=exact_time_m,
        exact_day_only=exact_day_only
    )

    # Jeśli wybrane stanowisko było zajęte, a użytkownik nie wymusił go twardo, sprawdź drugie stanowisko
    if not slot and station != 0 and not exact_day_only:
        slot = find_first_free_slot(
            appointments, cfg, dur,
            start_from=target_d,
            station_pref=0,
            min_time_m=min_time_m,
            max_time_m=max_time_m,
            exact_time_m=exact_time_m,
            exact_day_only=exact_day_only
        )

    return {
        "service": target_srv,
        "slot": slot,
        "plate": plate,
        "client": client_name,
        "price": price,
        "duration": dur,
        "requested_date": target_d
    }

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
if "current_nav_page" not in st.session_state:
    st.session_state["current_nav_page"] = "admin_cal" if st.session_state.get("authenticated") else "public_cal"

# --- GÓRNY PASEK NAWIGACJI ---
header_col1, header_col2 = st.columns([3, 1])

with header_col1:
    st.markdown("""
    <div class="top-brand">
        <div class="top-brand-icon">🛞</div>
        <div>
            <div class="top-brand-title">4KołaMag – Terminarz Wulkanizacji i Magazyn Opon</div>
            <div class="top-brand-sub">Zintegrowany system obsługi stanowisk warsztatowych i depozytów</div>
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
            st.session_state["current_nav_page"] = "public_cal"
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
                st.session_state["current_nav_page"] = "admin_cal"
                st.success("Zalogowano pomyślnie!")
                st.rerun()

        if b_close.button("Anuluj", use_container_width=True):
            st.session_state["show_login_modal"] = False
            st.rerun()
    st.markdown("---")

# --- PASEK BOCZNY (PRZYCISKI POGRUPOWANE I LEŻĄCE OBOK SIEBIE) ---
if st.session_state["authenticated"]:
    st.sidebar.markdown("## 🛞 Panel Warsztatu")
    st.sidebar.success(f"Zalogowano jako:\n`{st.session_state['logged_user']}`")

    # GRUPA 1: TERMINARZ I KALENDARZ (BŁĘKITNY AKCENT)
    st.sidebar.markdown('<div class="nav-group-title group-cal">📅 TERMINARZ I WIZYTY</div>', unsafe_allow_html=True)
    c_cal1, c_cal2 = st.sidebar.columns(2)
    is_admin_cal = (st.session_state.get("current_nav_page") == "admin_cal")
    is_pub_cal = (st.session_state.get("current_nav_page") == "public_cal")

    if c_cal1.button("📅 Admin", key="nav_btn_admin_cal", use_container_width=True, type="primary" if is_admin_cal else "secondary"):
        st.session_state["current_nav_page"] = "admin_cal"
        st.rerun()

    if c_cal2.button("👁️ Klient", key="nav_btn_public_cal", use_container_width=True, type="primary" if is_pub_cal else "secondary"):
        st.session_state["current_nav_page"] = "public_cal"
        st.rerun()

    # GRUPA 2: MAGAZYN OPON I DEPOZYTY (SZMARAGDOWY AKCENT)
    st.sidebar.markdown('<div class="nav-group-title group-mag">📦 MAGAZYN OPON</div>', unsafe_allow_html=True)
    c_mag1, c_mag2 = st.sidebar.columns(2)
    is_dash = (st.session_state.get("current_nav_page") == "dashboard")
    is_intake = (st.session_state.get("current_nav_page") == "intake")

    if c_mag1.button("📊 Magazyn", key="nav_btn_dashboard", use_container_width=True, type="primary" if is_dash else "secondary"):
        st.session_state["current_nav_page"] = "dashboard"
        st.rerun()

    if c_mag2.button("➕ Nowy", key="nav_btn_intake", use_container_width=True, type="primary" if is_intake else "secondary"):
        st.session_state["current_nav_page"] = "intake"
        st.rerun()

    is_arch = (st.session_state.get("current_nav_page") == "archive")
    if st.sidebar.button("📜 Archiwum Wydanych Opon", key="nav_btn_archive", use_container_width=True, type="primary" if is_arch else "secondary"):
        st.session_state["current_nav_page"] = "archive"
        st.rerun()

    # GRUPA 3: SYSTEM I USTAWIENIA (SZARY AKCENT)
    st.sidebar.markdown('<div class="nav-group-title group-sys">⚙️ USTAWIENIA</div>', unsafe_allow_html=True)
    is_cfg = (st.session_state.get("current_nav_page") == "config")
    if st.sidebar.button("⚙️ Konfiguracja & Słowniki", key="nav_btn_config", use_container_width=True, type="primary" if is_cfg else "secondary"):
        st.session_state["current_nav_page"] = "config"
        st.rerun()

    deposits = db_data.get("deposits", [])
    archive = db_data.get("archive", [])
    appointments = db_data.get("appointments", [])

    st.sidebar.markdown("---")
    st.sidebar.caption("📦 **Podsumowanie bazy:**")
    st.sidebar.write(f"• Depozyty w magazynie: `{len(deposits)}`")
    st.sidebar.write(f"• Archiwum wydanych: `{len(archive)}`")
    st.sidebar.write(f"• Wizyty w terminarzu: `{len(appointments)}`")

    if st.sidebar.button("🚪 Wyloguj się", key="btn_side_logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["logged_user"] = ""
        st.session_state["current_nav_page"] = "public_cal"
        st.rerun()

active_page = st.session_state.get("current_nav_page", "public_cal") if st.session_state["authenticated"] else "public_cal"


# ==========================================================
# KOMPONENTY I WIDOKI KALENDARZA (KOMPAKTOWE KARTY + TYDZIEŃ)
# ==========================================================
def render_admin_app_card(app):
    css_cls, pretty_name = get_service_info(app.get("serviceName", ""))
    start_t = app.get("startTime", "00:00")
    end_t = app.get("endTime", "00:00")
    dur = app.get("durationMinutes", 45)
    plate = app.get("carLicensePlate", "Brak rej.")
    client = app.get("clientAcronym", "KLIENT")
    phone = app.get("clientPhone", "")
    price = app.get("price", 0)
    
    phone_txt = f"| 📞 {phone}" if phone else ""
    st.markdown(f"""
    <div class="app-card-box {css_cls}">
        <div class="card-top-row">
            <span class="time-badge">⏰ {start_t} – {end_t}</span>
            <span class="duration-badge">{dur} min</span>
        </div>
        <div class="service-badge">{pretty_name}</div>
        <div class="admin-app-details">
            <div>
                <span class="admin-plate-pill">🚗 {plate}</span>
                <span class="admin-client-pill">👤 {client}</span>
                <span style="font-size: 11px; color: #94a3b8;">{phone_txt}</span>
            </div>
            <span class="admin-price-pill">💰 {price:.0f} zł</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_public_app_card(app):
    css_cls, pretty_name = get_service_info(app.get("serviceName", ""))
    start_t = app.get("startTime", "00:00")
    end_t = app.get("endTime", "00:00")
    dur = app.get("durationMinutes", 45)
    st.markdown(f"""
    <div class="app-card-box {css_cls}">
        <div class="card-top-row">
            <span class="time-badge">⏰ {start_t} – {end_t}</span>
            <span class="duration-badge">ok. {dur} min</span>
        </div>
        <div class="service-badge">{pretty_name}</div>
    </div>
    """, unsafe_allow_html=True)

def render_station_timeline(st_apps, station_num, station_label, wh, is_admin=True):
    if not wh:
        st.markdown(f"""
        <div class="station-column-header">
            <div class="station-title">{station_label}</div>
            <div class="station-badge-count count-busy">Zamknięte</div>
        </div>
        """, unsafe_allow_html=True)
        st.info("Warsztat jest nieczynny w wybranym dniu.")
        return

    sh, sm = map(int, wh.get("start", "08:00").split(":"))
    eh, em = map(int, wh.get("end", "18:00").split(":"))
    day_s = sh * 60 + sm
    day_e = eh * 60 + em
    total_m = max(1, day_e - day_s)

    sorted_apps = sorted(st_apps, key=lambda x: x.get("startTime", "00:00"))

    busy_m = 0
    for a in sorted_apps:
        try:
            ash, asm = map(int, a.get("startTime", "08:00").split(":"))
            aeh, aem = map(int, a.get("endTime", "09:00").split(":"))
            busy_m += max(0, (aeh * 60 + aem) - (ash * 60 + asm))
        except Exception:
            busy_m += int(a.get("durationMinutes", 45))

    busy_m = min(total_m, busy_m)
    free_m = max(0, total_m - busy_m)
    pct_free = int((free_m / total_m) * 100)
    pct_busy = 100 - pct_free

    badge_txt = f"🟢 Wolne: {free_m // 60}h {free_m % 60:02d}m ({pct_free}%)"
    bar_grad = "linear-gradient(90deg, #38bdf8, #818cf8)" if station_num == 1 else "linear-gradient(90deg, #c084fc, #f472b6)"

    st.markdown(f"""
    <div class="station-column-header">
        <div class="station-title">{station_label}</div>
        <div class="station-badge-count {'count-busy' if busy_m > 0 else 'count-free'}">
            {badge_txt}
        </div>
    </div>
    <div style="width: 100%; height: 5px; background: rgba(255,255,255,0.08); border-radius: 3px; margin: 2px 0 8px 0; overflow: hidden;" title="Zajęte: {pct_busy}%, Wolne: {pct_free}%">
        <div style="width: {pct_busy}%; height: 100%; background: {bar_grad}; border-radius: 3px;"></div>
    </div>
    """, unsafe_allow_html=True)

    cur_t = day_s
    for app in sorted_apps:
        try:
            ash, asm = map(int, app.get("startTime", "08:00").split(":"))
            aeh, aem = map(int, app.get("endTime", "09:00").split(":"))
            app_s = ash * 60 + asm
            app_e = aeh * 60 + aem
        except Exception:
            app_s = cur_t
            app_e = cur_t + int(app.get("durationMinutes", 45))

        if app_s > cur_t:
            gap = app_s - cur_t
            if gap >= 15:
                gap_txt = f"{gap // 60}h {gap % 60:02d}m" if gap >= 60 else f"{gap} min"
                st.markdown(f"""
                <div class="free-slot-card">
                    <span>🟢 <strong>{cur_t // 60:02d}:{cur_t % 60:02d} – {app_s // 60:02d}:{app_s % 60:02d}</strong></span>
                    <span>✓ Wolne {gap_txt}</span>
                </div>
                """, unsafe_allow_html=True)

        if is_admin:
            render_admin_app_card(app)
        else:
            render_public_app_card(app)

        cur_t = max(cur_t, app_e)

    if cur_t < day_e:
        gap = day_e - cur_t
        if gap >= 15:
            gap_txt = f"{gap // 60}h {gap % 60:02d}m" if gap >= 60 else f"{gap} min"
            st.markdown(f"""
            <div class="free-slot-card">
                <span>🟢 <strong>{cur_t // 60:02d}:{cur_t % 60:02d} – {day_e // 60:02d}:{day_e % 60:02d}</strong></span>
                <span>✓ Wolne {gap_txt}</span>
            </div>
            """, unsafe_allow_html=True)

def render_week_view(current_date, appointments, cfg, is_admin=True):
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=5)

    wn1, wn2, wn3, wn_title = st.columns([1.2, 1.2, 1.2, 2.4])
    if wn1.button("◀ Poprz. tydzień", key=f"wk_prev_{'adm' if is_admin else 'pub'}", use_container_width=True):
        st.session_state["cal_date"] -= timedelta(days=7)
        st.rerun()
    if wn2.button("Bieżący tydzień", key=f"wk_curr_{'adm' if is_admin else 'pub'}", use_container_width=True):
        st.session_state["cal_date"] = date.today()
        st.rerun()
    if wn3.button("Nast. tydzień ▶", key=f"wk_next_{'adm' if is_admin else 'pub'}", use_container_width=True):
        st.session_state["cal_date"] += timedelta(days=7)
        st.rerun()

    week_num = start_of_week.isocalendar()[1]
    wn_title.markdown(f"""
    <div style="padding-top: 6px; font-size: 14.5px; font-weight: 800; color: #38bdf8;">
        🗓️ Tydzień {week_num}: {start_of_week.strftime('%d.%m')} – {end_of_week.strftime('%d.%m.%Y')}
    </div>
    """, unsafe_allow_html=True)

    week_apps = []
    for day_offset in range(6):
        d_check = (start_of_week + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        week_apps.extend([a for a in appointments if a.get("date") == d_check])

    tot_week_rev = sum(float(a.get("price", 0)) for a in week_apps)
    
    if is_admin:
        wm1, wm2, wm3 = st.columns(3)
        wm1.markdown(f"""
        <div class="compact-metric-card">
            <div class="metric-card-label">Wizyty w tym tygodniu</div>
            <div class="metric-card-value">{len(week_apps)} aut</div>
        </div>
        """, unsafe_allow_html=True)
        wm2.markdown(f"""
        <div class="compact-metric-card">
            <div class="metric-card-label">Wartość usług tygodnia</div>
            <div class="metric-card-value" style="color: #34d399;">{tot_week_rev:.0f} zł</div>
        </div>
        """, unsafe_allow_html=True)
        wm3.markdown(f"""
        <div class="compact-metric-card">
            <div class="metric-card-label">Średnio na dzień roboczy</div>
            <div class="metric-card-value">{len(week_apps)/6:.1f} aut</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    w_cols = st.columns(6)
    short_days = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota"]

    for idx in range(6):
        d = start_of_week + timedelta(days=idx)
        d_str = d.strftime("%Y-%m-%d")
        d_apps = [a for a in appointments if a.get("date") == d_str]
        wh = get_working_hours(d, cfg)

        is_today = (d == date.today())
        is_selected = (d == current_date)
        col_cls = "week-col-box"
        if is_today:
            col_cls += " is-today"
        if is_selected:
            col_cls += " is-selected"

        with w_cols[idx]:
            free_txt = "Nieczynne"
            hours_txt = "Zamknięte"
            if wh:
                sh, sm = map(int, wh.get("start", "08:00").split(":"))
                eh, em = map(int, wh.get("end", "18:00").split(":"))
                day_cap_m = ((eh * 60 + em) - (sh * 60 + sm)) * 2
                busy_m = sum(int(a.get("durationMinutes", 45)) for a in d_apps)
                free_m = max(0, day_cap_m - busy_m)
                free_txt = f"🟢 Wolne: {free_m // 60}h {free_m % 60:02d}m"
                hours_txt = f"⏰ {wh.get('start')} – {wh.get('end')}"

            today_badge = " <span style='color: #38bdf8; font-weight:800;'>(DZIŚ)</span>" if is_today else ""
            st.markdown(f"""
            <div class="{col_cls}">
                <div class="week-header-title">{short_days[idx]}{today_badge}</div>
                <div class="week-header-sub">{d.strftime('%d.%m.%Y')} | {hours_txt}</div>
                <div class="week-badge-free">{free_txt} | 🚗 {len(d_apps)} aut</div>
            </div>
            """, unsafe_allow_html=True)

            if d_apps:
                for app in sorted(d_apps, key=lambda x: x.get("startTime", "")):
                    st_num = int(app.get("station", 1))
                    cls_s = "st2" if st_num == 2 else "st1"
                    if is_admin:
                        st.markdown(f"""
                        <div class="week-mini-app {cls_s}">
                            <strong>⏰ {app.get('startTime')}</strong> [St.{st_num}]<br>
                            🚗 {app.get('carLicensePlate', 'Brak')} ({app.get('clientAcronym', 'Klient')})<br>
                            <span style="color: #94a3b8; font-size: 9.5px;">{app.get('serviceName', '')[:20]}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="week-mini-app {cls_s}">
                            <strong>⏰ {app.get('startTime')} – {app.get('endTime')}</strong> [St.{st_num}]<br>
                            <span style="color: #cbd5e1; font-size: 9.5px;">{app.get('serviceName', '')[:22]}</span>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                if wh:
                    st.caption("✓ Dzień wolny")
                else:
                    st.caption("Nieczynne")

            if st.button("Dzień 🔍", key=f"wk_jump_{'adm' if is_admin else 'pub'}_{d_str}", use_container_width=True):
                st.session_state["cal_date"] = d
                if is_admin:
                    st.session_state["adm_view_mode_toggle"] = "📆 Widok Dnia"
                else:
                    st.session_state["pub_view_mode_toggle"] = "📆 Widok Dnia"
                st.rerun()


# ==========================================================
# 1. WIDOK TERMINARZA DLA KLIENTÓW (PUBLICZNY - BEZ CEN)
# ==========================================================
if active_page == "public_cal":
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

    st.markdown("""
    <div class="legend-container">
        <span class="legend-title">Usługi (szacowany czas):</span>
        <span class="legend-chip"><span class="legend-dot" style="background: #0284c7;"></span> Stal (ok. 45 min)</span>
        <span class="legend-chip"><span class="legend-dot" style="background: #10b981;"></span> Alu ≤ 17" (ok. 45 min)</span>
        <span class="legend-chip"><span class="legend-dot" style="background: #8b5cf6;"></span> AluPremium > 17" (ok. 60 min)</span>
        <span class="legend-chip"><span class="legend-dot" style="background: #f59e0b;"></span> Bus (ok. 60 min)</span>
        <span class="legend-chip"><span class="legend-dot" style="background: #ec4899;"></span> Szybki serwis (ok. 30 min)</span>
        <span style="margin-left: auto; color: #38bdf8; font-weight: 700;">🕒 08:00 – 18:00</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("⚡ Sprawdź najbliższy wolny termin", expanded=False):
        q_srv_col, q_date_col, q_btn_col = st.columns([2, 1, 1])
        services = app_config.get("services", [])
        srv_map = {f"{s.get('name')} (czas: ok. {s.get('durationMinutes')} min)": s for s in services}
        chosen_q_srv = q_srv_col.selectbox("Wybierz rodzaj kół / usługę:", list(srv_map.keys()), key="pub_q_srv")
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
                    ⏰ <strong>Godzina:</strong> {fs['startTime']} – {fs['endTime']} (szacunkowy czas: {fs['durationMinutes']} min)<br>
                    🚗 <strong>Stanowisko:</strong> Stanowisko {fs['station']} (Podnośnik {'A' if fs['station']==1 else 'B'})<br>
                    🔧 <strong>Usługa:</strong> {srv_o.get('name')}
                </div>
                <div style="margin-top: 12px;">
                    <a href="tel:600223669" class="phone-call-btn">📞 Zadzwoń i zarezerwuj ten termin: 600 223 669</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

    pub_v_col1, pub_v_col2 = st.columns([1, 2])
    with pub_v_col1:
        pub_view_mode = st.radio("Widok terminarza:", ["📆 Widok Dnia", "🗓️ Widok Tygodnia"], horizontal=True, key="pub_view_mode_toggle")

    if pub_view_mode == "🗓️ Widok Tygodnia":
        render_week_view(st.session_state["cal_date"], db_data.get("appointments", []), app_config, is_admin=False)
    else:
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

        appointments = db_data.get("appointments", [])
        day_apps = [a for a in appointments if a.get("date") == date_str]
        st1_apps = [a for a in day_apps if int(a.get("station", 1)) == 1]
        st2_apps = [a for a in day_apps if int(a.get("station", 1)) == 2]
        wh = get_working_hours(st.session_state["cal_date"], app_config)

        tab_all, tab_st1, tab_st2 = st.tabs([
            "🏢 Wszystkie stanowiska (Podgląd)",
            f"🚗 Stanowisko 1 ({len(st1_apps)} zajęte)",
            f"🚙 Stanowisko 2 ({len(st2_apps)} zajęte)"
        ])

        with tab_all:
            col_st1, col_st2 = st.columns(2)
            with col_st1:
                render_station_timeline(st1_apps, 1, "🚗 Stanowisko 1 (Podnośnik A)", wh, is_admin=False)

            with col_st2:
                render_station_timeline(st2_apps, 2, "🚙 Stanowisko 2 (Podnośnik B)", wh, is_admin=False)

        with tab_st1:
            st.markdown("#### 🚗 Stanowisko 1 (Podnośnik A)")
            render_station_timeline(st1_apps, 1, "Stanowisko 1 (Podnośnik A)", wh, is_admin=False)

        with tab_st2:
            st.markdown("#### 🚙 Stanowisko 2 (Podnośnik B)")
            render_station_timeline(st2_apps, 2, "Stanowisko 2 (Podnośnik B)", wh, is_admin=False)

    st.markdown("---")
    st.info("💡 **Chcesz zarezerwować termin?** Zadzwoń pod numer **600 223 669**.")


# ==========================================================
# 2. KALENDARZ WIZYT (ADMIN DLA ZALOGOWANYCH)
# ==========================================================
elif active_page == "admin_cal" and st.session_state["authenticated"]:
    st.markdown('<div style="font-size: 21px; font-weight: 800; color: #f8fafc; margin-bottom: 8px;">📅 Kalendarz Wizyt i Stanowisk Warsztatowych</div>', unsafe_allow_html=True)

    apps = db_data.get("appointments", [])
    d_str = st.session_state["cal_date"].strftime("%Y-%m-%d")
    matching = [a for a in apps if a.get("date") == d_str]
    total_rev = sum(float(a.get("price", 0)) for a in matching)
    st1_apps = [a for a in matching if int(a.get("station", 1)) == 1]
    st2_apps = [a for a in matching if int(a.get("station", 1)) == 2]

    adm_v_col1, adm_v_col2 = st.columns([1, 2])
    with adm_v_col1:
        admin_view_mode = st.radio("Widok kalendarza:", ["📆 Widok Dnia", "🗓️ Widok Tygodnia"], horizontal=True, key="adm_view_mode_toggle")

    if admin_view_mode == "🗓️ Widok Tygodnia":
        render_week_view(st.session_state["cal_date"], apps, app_config, is_admin=True)
    else:
        # Nawigacja dniami kalendarza dla Admina
        nav_adm1, nav_adm2, nav_adm3, nav_adm_p = st.columns([1, 1, 1, 2])
        if nav_adm1.button("◀ Wczoraj", key="adm_prev_d", use_container_width=True):
            st.session_state["cal_date"] -= timedelta(days=1)
            st.rerun()
        if nav_adm2.button("Dziś", key="adm_today_d", use_container_width=True):
            st.session_state["cal_date"] = date.today()
            st.rerun()
        if nav_adm3.button("Jutro ▶", key="adm_next_d", use_container_width=True):
            st.session_state["cal_date"] += timedelta(days=1)
            st.rerun()

        chosen_adm_d = nav_adm_p.date_input("Dzień kalendarza:", value=st.session_state["cal_date"], key="adm_date_picker", label_visibility="collapsed")
        if chosen_adm_d != st.session_state["cal_date"]:
            st.session_state["cal_date"] = chosen_adm_d
            st.rerun()

        polish_weekdays = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
        polish_months = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca", "sierpnia", "września", "października", "listopada", "grudnia"]
        
        day_name = polish_weekdays[st.session_state["cal_date"].weekday()]
        month_name = polish_months[st.session_state["cal_date"].month - 1]
        formatted_adm_title = f"{day_name}, {st.session_state['cal_date'].day} {month_name} {st.session_state['cal_date'].year}"

        wh = get_working_hours(st.session_state["cal_date"], app_config)

        # Metryki dnia (kompaktowe)
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.markdown(f"""
        <div class="compact-metric-card">
            <div class="metric-card-label">📅 {day_name}, {st.session_state['cal_date'].strftime('%d.%m.%Y')}</div>
            <div class="metric-card-value">{len(matching)} aut</div>
        </div>
        """, unsafe_allow_html=True)
        m_col2.markdown(f"""
        <div class="compact-metric-card">
            <div class="metric-card-label">Suma wartości usług</div>
            <div class="metric-card-value" style="color: #34d399;">{total_rev:.0f} zł</div>
        </div>
        """, unsafe_allow_html=True)
        m_col3.markdown(f"""
        <div class="compact-metric-card">
            <div class="metric-card-label">Obłożenie stanowisk</div>
            <div class="metric-card-value" style="font-size: 15px;">St.1: {len(st1_apps)} | St.2: {len(st2_apps)}</div>
        </div>
        """, unsafe_allow_html=True)

        # --- WIZUALNY PODGLĄD 2 STANOWISK BEZPOŚREDNIO W PANELU ADMINA ---
        st.markdown("#### 🚗 Wizualny Podgląd Obłożenia Stanowisk w tym dniu")

        col_adm_st1, col_adm_st2 = st.columns(2)
        with col_adm_st1:
            render_station_timeline(st1_apps, 1, "🚗 Stanowisko 1 (Podnośnik A)", wh, is_admin=True)

        with col_adm_st2:
            render_station_timeline(st2_apps, 2, "🚙 Stanowisko 2 (Podnośnik B)", wh, is_admin=True)

    st.markdown("---")

    # --- ZAKŁADKI OPERACYJNE: REJESTRACJA, POPRAWA ORAZ ASYSTENT AI ---
    tab_new, tab_edit, tab_ai, tab_quick, tab_table = st.tabs([
        "➕ Rejestracja Nowej Wizyty",
        f"✏️ Popraw / Usuń Wizytę ({len(matching)})",
        "🤖 Asystent Planowania AI",
        "⚡ Szukaj Wolnego Terminu",
        "📋 Tabela Szczegółowa Dnia"
    ])

    # ZAKŁADKA A: REJESTRACJA NOWEJ WIZYTY RĘCZNIE
    with tab_new:
        prefill = st.session_state.get("form_prefill", {})
        if prefill:
            pref_d = prefill.get("date")
            pref_d_txt = pref_d.strftime("%Y-%m-%d") if isinstance(pref_d, (date, datetime)) else str(pref_d or "")
            st.info(f"📋 **Wypełniono danymi terminu:** Data: **{pref_d_txt}**, Godz: **{prefill.get('start')}**, Stanowisko: **{prefill.get('station')}**, Usługa: **{prefill.get('service', {}).get('name', 'Wybrana')}**")

        with st.form("manual_appointment_form"):
            fa0, fa1, fa2 = st.columns([1, 1, 1])
            init_date = prefill.get("date") if prefill.get("date") else st.session_state["cal_date"]
            if not isinstance(init_date, date):
                init_date = date.today()
            a_date = fa0.date_input("Data wizyty *:", value=init_date)
            a_plate = fa1.text_input("Numer Rejestracyjny *", value=prefill.get("plate", "")).upper().strip()
            a_client = fa2.text_input("Akronim / Imię Klienta *", value=prefill.get("client", ""), placeholder="np. Nowak")

            fa3, fa4, fa5 = st.columns(3)
            a_phone = fa3.text_input("Telefon kontaktowy", placeholder="np. 600 123 456")

            services = app_config.get("services", [])
            srv_opts = {f"{s.get('name')} - {s.get('price')} zł ({s.get('durationMinutes')} min)": s for s in services}
            srv_keys = list(srv_opts.keys())
            pref_srv_id = prefill.get("service", {}).get("id")
            def_srv_idx = 0
            if pref_srv_id:
                for idx_s, sk in enumerate(srv_keys):
                    if srv_opts[sk].get("id") == pref_srv_id:
                        def_srv_idx = idx_s
                        break
            chosen_srv_key = fa4.selectbox("Wybierz usługę:", srv_keys, index=def_srv_idx)
            selected_srv = srv_opts[chosen_srv_key]

            a_station = fa5.selectbox(
                "Stanowisko:",
                [1, 2],
                index=1 if prefill.get("station") == 2 else 0,
                format_func=lambda x: f"Stanowisko {x} (Podnośnik {'A' if x==1 else 'B'})"
            )

            fa6, fa7, fa8 = st.columns(3)
            a_start = fa6.text_input("Godzina rozpoczęcia (HH:MM):", value=prefill.get("start", "09:00"))
            dur = selected_srv.get("durationMinutes", 45)
            default_p = prefill.get("service", {}).get("price", selected_srv.get("price", 140))
            a_price = fa7.number_input("Cena usługi (PLN):", value=float(default_p), step=10.0)

            try:
                sh, sm = map(int, a_start.split(":"))
                end_m_calc = sh * 60 + sm + dur
                calc_end_str = f"{end_m_calc // 60:02d}:{end_m_calc % 60:02d}"
            except Exception:
                calc_end_str = "09:45"

            fa8.info(f"⏱️ **Czas trwania:** {dur} min | ⏰ **Koniec:** {calc_end_str}")

            if st.form_submit_button("💾 Dodaj wizytę do kalendarza", type="primary", use_container_width=True):
                if not a_plate or not a_client:
                    st.error("Wpisz numer rejestracyjny i nazwisko/akronim klienta.")
                else:
                    saved_date_str = a_date.strftime("%Y-%m-%d")
                    new_app = {
                        "id": f"app_{int(datetime.now().timestamp())}",
                        "date": saved_date_str,
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
                    st.session_state["cal_date"] = a_date
                    st.session_state["form_prefill"] = {}
                    st.success(f"Dodano wizytę dla {a_plate} na dzień {saved_date_str}!")
                    st.rerun()

    # ZAKŁADKA B: POPRAW / USUŃ WIZYTĘ
    with tab_edit:
        if matching:
            del_opts = {f"{a.get('startTime')}-{a.get('endTime')} | St.{a.get('station')} | {a.get('carLicensePlate') or 'Brak rej.'} ({a.get('clientAcronym')}) - {a.get('serviceName')}": a.get("id") for a in matching}
            chosen_app_label = st.selectbox("Wybierz wizytę do poprawy:", list(del_opts.keys()), key="chosen_edit_app")
            chosen_app_id = del_opts[chosen_app_label]
            target_app = next((a for a in apps if a.get("id") == chosen_app_id), None)

            if target_app:
                with st.form("edit_appointment_form"):
                    ec1, ec2, ec3 = st.columns(3)
                    new_plate = ec1.text_input("Numer Rejestracyjny:", value=target_app.get("carLicensePlate", "")).upper().strip()
                    new_client = ec2.text_input("Akronim / Imię Klienta:", value=target_app.get("clientAcronym", "")).strip()
                    new_phone = ec3.text_input("Telefon kontaktowy:", value=target_app.get("clientPhone", "")).strip()

                    ec4, ec5, ec6 = st.columns(3)
                    services = app_config.get("services", [])
                    srv_opts_edit = {s.get("name", s.get("id")): s for s in services}
                    curr_srv_name = target_app.get("serviceName", "")
                    srv_index = 0
                    for idx, sname in enumerate(srv_opts_edit.keys()):
                        if sname == curr_srv_name:
                            srv_index = idx
                            break
                    selected_edit_srv_name = ec4.selectbox("Usługa:", list(srv_opts_edit.keys()), index=srv_index)
                    selected_edit_srv = srv_opts_edit[selected_edit_srv_name]

                    curr_station = int(target_app.get("station", 1))
                    new_station = ec5.selectbox("Stanowisko:", [1, 2], index=0 if curr_station == 1 else 1, format_func=lambda x: f"Stanowisko {x} (Podnośnik {'A' if x==1 else 'B'})"
                    )
                    
                    status_list = ["planned", "completed", "cancelled"]
                    curr_st_val = target_app.get("status", "planned")
                    st_idx = status_list.index(curr_st_val) if curr_st_val in status_list else 0
                    new_status = ec6.selectbox("Status wizyty:", status_list, index=st_idx, format_func=lambda x: "Zaplanowana" if x=="planned" else ("Zrealizowana" if x=="completed" else "Odwołana"))

                    ec7, ec8, ec9 = st.columns(3)
                    new_start = ec7.text_input("Godzina rozpoczęcia (HH:MM):", value=target_app.get("startTime", "08:00"))
                    new_end = ec8.text_input("Godzina zakończenia (HH:MM):", value=target_app.get("endTime", "09:00"))
                    new_price = ec9.number_input("Cena usługi (PLN):", value=float(target_app.get("price", 140)), step=10.0)

                    b_save_edit, b_del_edit = st.columns(2)
                    save_clicked = b_save_edit.form_submit_button("💾 Zapisz poprawki wizyty", type="primary", use_container_width=True)
                    if save_clicked:
                        target_app["carLicensePlate"] = new_plate
                        target_app["clientAcronym"] = new_client
                        target_app["clientPhone"] = new_phone
                        target_app["serviceName"] = selected_edit_srv.get("name")
                        target_app["serviceId"] = selected_edit_srv.get("id")
                        target_app["station"] = int(new_station)
                        target_app["status"] = new_status
                        target_app["startTime"] = new_start
                        target_app["endTime"] = new_end
                        target_app["price"] = float(new_price)
                        save_db(db_data)
                        st.success("✅ Pomyślnie zaktualizowano dane wizyty!")
                        st.rerun()

                if st.button("🗑️ Usuń tę wizytę z kalendarza", type="secondary", use_container_width=True):
                    db_data["appointments"] = [a for a in apps if a.get("id") != chosen_app_id]
                    save_db(db_data)
                    st.success("Usunięto wizytę.")
                    st.rerun()
        else:
            st.info("Brak zapisanych wizyt w tym dniu do edycji.")

    # ZAKŁADKA C: ASYSTENT AI
    with tab_ai:
        st.markdown("""
        <p style="font-size: 13px; color: #94a3b8; margin-bottom: 8px;">
            Wpisz polecenie w języku naturalnym, np. <em>"sobota po południu nr rej. PRA1234 Klient Olek"</em> lub <em>"wpisz Bolka na najbliższy poniedziałek na Alu Premium pierwszy wolny termin, ale po godzinie 12-tej"</em>
        </p>
        """, unsafe_allow_html=True)

        chip_c1, chip_c2, chip_c3 = st.columns(3)
        if chip_c1.button("⚡ Sobota po południu PRA1234 Olek", use_container_width=True):
            st.session_state["ai_cmd_input"] = "sobota po południu nr rej. PRA1234 Klient Olek"
        if chip_c2.button("🔍 Poniedziałek po 12:00 (Alu)", use_container_width=True):
            st.session_state["ai_cmd_input"] = "wpisz Bolka na najbliższy poniedziałek na Alu Premium pierwszy wolny termin, ale po godzinie 12-tej"
        if chip_c3.button("📅 Jutro 14:00 Koła stalowe", use_container_width=True):
            st.session_state["ai_cmd_input"] = "jutro na 14:00 koła stalowe Klient Nowak PRA9999"

        cmd_val = st.text_area(
            "Polecenie dla Asystenta:",
            value=st.session_state.get("ai_cmd_input", "sobota po południu nr rej. PRA1234 Klient Olek"),
            height=70
        )

        ac_c1, ac_c2 = st.columns([1, 2])
        if ac_c1.button("✨ Wykonaj polecenie dla Agenta", type="primary", use_container_width=True):
            res = parse_ai_prompt(cmd_val, db_data.get("appointments", []), app_config)
            if res and res.get("slot"):
                st.session_state["ai_proposed_visit"] = res
            else:
                req_d = res.get("requested_date", date.today()).strftime("%Y-%m-%d") if res else ""
                st.warning(f"Brak wolnego terminu w wybranym dniu ({req_d}) z uwzględnieniem wskazanej pory (np. po 12:00).")

        if st.session_state.get("ai_proposed_visit"):
            prop = st.session_state["ai_proposed_visit"]
            pslot = prop["slot"]
            psrv = prop["service"]
            st.markdown(f"""
            <div class="slot-result-card">
                <div class="slot-result-title">🤖 Agent znalazł termin i przygotował wizytę!</div>
                <div style="font-size: 14px; color: #e2e8f0; line-height: 1.6;">
                    Znalazłem wolny termin na <strong>{pslot['date']}</strong> w godzinach <strong>{pslot['startTime']} – {pslot['endTime']}</strong> ({pslot['durationMinutes']} min).<br>
                    Stanowisko: <strong>Stanowisko {pslot['station']} (Podnośnik {'A' if pslot['station']==1 else 'B'})</strong> | Usługa: <strong>{psrv.get('name')}</strong> | Cena: <strong style="color: #38bdf8;">{prop['price']} zł</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

            prop_c1, prop_c2, prop_c3 = st.columns(3)
            final_plate = prop_c1.text_input("Numer rejestracyjny:", value=prop.get("plate", ""), key="ai_final_plate").upper().strip()
            final_client = prop_c2.text_input("Akronim / Klient:", value=prop.get("client", "KLIENT"), key="ai_final_client").strip()
            final_phone = prop_c3.text_input("Telefon (opcjonalnie):", value="", key="ai_final_phone").strip()

            prop_save_c1, prop_save_c2 = st.columns([1, 1])
            if prop_save_c1.button("✓ Zapisz i dodaj tę wizytę do kalendarza", type="primary", use_container_width=True):
                new_app = {
                    "id": f"app_{int(datetime.now().timestamp())}",
                    "date": pslot["date"],
                    "startTime": pslot["startTime"],
                    "endTime": pslot["endTime"],
                    "station": int(pslot["station"]),
                    "carLicensePlate": final_plate,
                    "clientAcronym": final_client,
                    "clientPhone": final_phone,
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

    # ZAKŁADKA D: SZUKAJ WOLNEGO TERMINU
    with tab_quick:
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
            st.markdown(f"""
            <div class="slot-result-card" style="margin-top: 8px; margin-bottom: 12px;">
                <div class="slot-result-title">🎉 Znaleziono wolny termin!</div>
                <div style="font-size: 14px; color: #f8fafc; line-height: 1.6;">
                    📅 <strong>Data:</strong> {fs['date']}<br>
                    ⏰ <strong>Godziny:</strong> {fs['startTime']} – {fs['endTime']} ({fs['durationMinutes']} min)<br>
                    🚗 <strong>Stanowisko:</strong> Stanowisko {fs['station']} (Podnośnik {'A' if fs['station']==1 else 'B'})<br>
                    🔧 <strong>Usługa:</strong> {so.get('name')} | 💰 <strong>Cena:</strong> {so.get('price')} zł
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("##### ✍️ Szybka rejestracja na znaleziony termin:")
            rq1, rq2, rq3 = st.columns(3)
            quick_plate = rq1.text_input("Numer Rejestracyjny *:", key="quick_reg_plate_val").upper().strip()
            quick_client = rq2.text_input("Akronim / Klient *:", key="quick_reg_client_val", placeholder="np. Nowak").strip()
            quick_phone = rq3.text_input("Telefon (opcjonalnie):", key="quick_reg_phone_val").strip()

            bq1, bq2 = st.columns([1, 1])
            if bq1.button("💾 Zapisz wizytę na ten termin teraz", type="primary", use_container_width=True, key="btn_save_quick_direct"):
                if not quick_plate or not quick_client:
                    st.error("Wpisz numer rejestracyjny i nazwisko/akronim klienta.")
                else:
                    new_app = {
                        "id": f"app_{int(datetime.now().timestamp())}",
                        "date": fs["date"],
                        "startTime": fs["startTime"],
                        "endTime": fs["endTime"],
                        "station": int(fs["station"]),
                        "carLicensePlate": quick_plate,
                        "clientAcronym": quick_client,
                        "clientPhone": quick_phone,
                        "serviceId": so.get("id", "srv"),
                        "serviceName": so.get("name"),
                        "durationMinutes": int(fs["durationMinutes"]),
                        "price": float(so.get("price", 140)),
                        "status": "planned"
                    }
                    db_data["appointments"].append(new_app)
                    save_db(db_data)
                    st.session_state["cal_date"] = datetime.strptime(fs["date"], "%Y-%m-%d").date()
                    st.session_state["admin_found_slot"] = None
                    st.session_state["form_prefill"] = {}
                    st.success(f"✅ Zapisano wizytę {quick_plate} ({quick_client}) na {fs['date']} godz. {fs['startTime']}!")
                    st.rerun()

            if bq2.button("📋 Przejdź do formularza ręcznego z tym terminem", use_container_width=True, key="btn_fill_form_manual"):
                st.session_state["form_prefill"] = {
                    "date": datetime.strptime(fs["date"], "%Y-%m-%d").date(),
                    "start": fs["startTime"],
                    "station": fs["station"],
                    "service": so
                }
                st.session_state["cal_date"] = datetime.strptime(fs["date"], "%Y-%m-%d").date()
                st.success(f"✅ Wypełniono formularz danymi na {fs['date']} godz. {fs['startTime']}. Przejdź do pierwszej zakładki '➕ Rejestracja Nowej Wizyty'.")

    # ZAKŁADKA E: PEŁNA TABELA DLA DNIA
    with tab_table:
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
        else:
            st.info("Brak zapisanych wizyt w tym dniu.")


# ==========================================================
# 3. DASHBOARD & MAGAZYN OPON (DLA ZALOGOWANYCH)
# ==========================================================
elif active_page == "dashboard" and st.session_state["authenticated"]:
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
elif active_page == "intake" and st.session_state["authenticated"]:
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
elif active_page == "archive" and st.session_state["authenticated"]:
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
# 6. KONFIGURACJA & SŁOWNIKI (DLA ZALOGOWANYCH)
# ==========================================================
elif active_page == "config" and st.session_state["authenticated"]:
    st.header("⚙️ Konfiguracja, Słowniki i Harmonogram Pracy")
    st.caption("Wszystkie poniższe tabele są w pełni edytowalne. Możesz zmieniać nazwy, czasy trwania, ceny i godziny pracy.")

    # --- SEKCJA A: SŁOWNIK USŁUG ---
    st.subheader("🔧 Słownik Usług, Czasów Trwania i Cen")
    st.info("💡 Kliknij w dowolną komórkę tabeli, aby zmienić nazwę usługi, czas w minutach lub domyślną cenę. Możesz też dopisywać nowe usługi.")

    srv_list = app_config.get("services", [])
    services_edit_data = []
    for s in srv_list:
        services_edit_data.append({
            "Identyfikator": s.get("id", "usluga"),
            "Etykieta skrócona": s.get("shortLabel", s.get("id", "")),
            "Pełna nazwa usługi": s.get("name", ""),
            "Czas trwania (min)": int(s.get("durationMinutes", 45)),
            "Domyślna cena (PLN)": float(s.get("price", 100))
        })

    df_srv_input = pd.DataFrame(services_edit_data)
    edited_srv_df = st.data_editor(
        df_srv_input,
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor_services",
        column_config={
            "Identyfikator": st.column_config.TextColumn("Klucz ID (unikalny)", required=True),
            "Etykieta skrócona": st.column_config.TextColumn("Etykieta (np. Stal, Alu)", width="small", required=True),
            "Pełna nazwa usługi": st.column_config.TextColumn("Pełna nazwa wyświetlana", width="large", required=True),
            "Czas trwania (min)": st.column_config.NumberColumn("Czas trwania (min)", min_value=10, max_value=240, step=5, required=True),
            "Domyślna cena (PLN)": st.column_config.NumberColumn("Cena domyślna (PLN)", min_value=0.0, step=10.0, required=True)
        }
    )

    st.markdown("---")

    # --- SEKCJA B: GODZINY PRACY W MIESIĄCACH ---
    st.subheader("🕒 Harmonogram Godzin Pracy (Wszystkie 12 Miesięcy)")
    months_names = [
        "1. Styczeń", "2. Luty", "3. Marzec", "4. Kwiecień", "5. Maj", "6. Czerwiec",
        "7. Lipiec", "8. Sierpień", "9. Wrzesień", "10. Październik", "11. Listopad", "12. Grudzień"
    ]
    monthly_dict = app_config.get("monthlyWorkingHours", {})
    m_rows = []
    for i in range(1, 13):
        m_k = str(i)
        mc = monthly_dict.get(m_k, {"start": "08:00", "end": "18:00", "saturdayStart": "08:00", "saturdayEnd": "14:00", "workSaturday": True, "note": ""})
        m_rows.append({
            "Miesiąc": months_names[i - 1],
            "Pon - Pt (Od)": mc.get("start", "08:00"),
            "Pon - Pt (Do)": mc.get("end", "18:00"),
            "Sobota (Od)": mc.get("saturdayStart", "08:00"),
            "Sobota (Do)": mc.get("saturdayEnd", "14:00"),
            "Czynne w soboty": bool(mc.get("workSaturday", True)),
            "Uwagi / Sezon": mc.get("note", "")
        })

    df_m_input = pd.DataFrame(m_rows)
    edited_months_df = st.data_editor(
        df_m_input,
        use_container_width=True,
        key="data_editor_months",
        column_config={
            "Miesiąc": st.column_config.TextColumn("Miesiąc", disabled=True),
            "Pon - Pt (Od)": st.column_config.TextColumn("Pon - Pt (Od)", width="small"),
            "Pon - Pt (Do)": st.column_config.TextColumn("Pon - Pt (Do)", width="small"),
            "Sobota (Od)": st.column_config.TextColumn("Sobota (Od)", width="small"),
            "Sobota (Do)": st.column_config.TextColumn("Sobota (Do)", width="small"),
            "Czynne w soboty": st.column_config.CheckboxColumn("Sobota czynna?"),
            "Uwagi / Sezon": st.column_config.TextColumn("Uwagi (np. Sezon zimowy)")
        }
    )

    st.markdown("---")

    # --- SEKCJA C: HASŁO, E-MAILE I NAGŁÓWEK ---
    st.subheader("🔐 Dostęp Pracowników i Nagłówek Kalendarza")
    c_p1, c_p2 = st.columns(2)
    cfg_pwd = c_p1.text_input("Hasło dostępu do Panelu Warsztatu:", value=app_config.get("adminPassword", "admin"), type="password")
    cfg_hdr = c_p2.text_input("Nagłówek kalendarza publicznego (telefon i nazwa):", value=app_config.get("publicHeader", "Wulkanizacja Michał - rezerwacja terminu 600223669"))

    curr_emails_val = app_config.get("allowedEmails", ["michal@twoje4kola.pl", "alert@itover.pl"])
    emails_txt = ", ".join(curr_emails_val) if isinstance(curr_emails_val, list) else str(curr_emails_val)
    cfg_emails = st.text_area("Uprawnione adresy e-mail pracowników (rozdzielone przecinkami):", value=emails_txt)

    if st.button("💾 Zapisz Całą Konfigurację i Słowniki", type="primary", use_container_width=True):
        new_services_list = []
        for _, r in edited_srv_df.iterrows():
            if str(r["Pełna nazwa usługi"]).strip():
                new_services_list.append({
                    "id": str(r["Identyfikator"]).strip(),
                    "shortLabel": str(r["Etykieta skrócona"]).strip(),
                    "name": str(r["Pełna nazwa usługi"]).strip(),
                    "durationMinutes": int(r["Czas trwania (min)"]),
                    "price": float(r["Domyślna cena (PLN)"])
                })
        app_config["services"] = new_services_list

        new_m_dict = {}
        for idx, r in edited_months_df.iterrows():
            m_idx_str = str(idx + 1)
            new_m_dict[m_idx_str] = {
                "start": str(r["Pon - Pt (Od)"]).strip(),
                "end": str(r["Pon - Pt (Do)"]).strip(),
                "saturdayStart": str(r["Sobota (Od)"]).strip(),
                "saturdayEnd": str(r["Sobota (Do)"]).strip(),
                "workSaturday": bool(r["Czynne w soboty"]),
                "note": str(r["Uwagi / Sezon"]).strip()
            }
        app_config["monthlyWorkingHours"] = new_m_dict

        app_config["adminPassword"] = cfg_pwd.strip()
        app_config["publicHeader"] = cfg_hdr.strip()
        parsed_e = [x.strip().lower() for x in cfg_emails.split(",") if x.strip()]
        app_config["allowedEmails"] = parsed_e

        if save_config(app_config):
            st.success("✅ Pomyślnie zapisano wszystkie zmiany w konfiguracji, słowniku usług i godzinach pracy!")
            st.rerun()
        else:
            st.error("Błąd podczas zapisywania konfiguracji do pliku.")
