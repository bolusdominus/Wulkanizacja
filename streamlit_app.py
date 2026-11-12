import streamlit as st
import json
import os
from datetime import datetime, date, timedelta
import pandas as pd
import io

# --- KONFIGURACJA STRONY STREAMLIT ---
st.set_page_config(
    page_title="4KołaMag - Magazyn Opon i Terminarz",
    page_icon="🛞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ścieżki do plików
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.json")
CONFIG_FILE = os.path.join(BASE_DIR, "calendar_config.json")
PUBLIC_CONFIG_FILE = os.path.join(BASE_DIR, "public", "calendar_config.json")
PUBLIC_CAL_FILE = os.path.join(BASE_DIR, "public", "kalendarz.html")

# --- WSTRZYKIWANIE STYLÓW DARK MODE (ELEGANT SAAS THEME) ---
st.markdown("""
<style>
    /* Tło aplikacji i główny kontrast */
    .stApp {
        background-color: #0b0f19;
        color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Panel boczny (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #101726;
        border-right: 1px solid #1e293b;
    }
    
    /* Karty statystyk (Metrics) */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #151d30, #131b2e);
        border: 1px solid #23314d;
        border-radius: 12px;
        padding: 14px 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
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
    
    /* Przyciski podstawowe i formularze */
    button[kind="primary"] {
        background: linear-gradient(135deg, #0284c7, #2563eb) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
        transition: all 0.2s ease;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #0369a1, #1d4ed8) !important;
        transform: translateY(-1px);
    }
    
    button[kind="secondary"] {
        background: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    
    /* Pasek ogłoszeniowy (Header Banner) */
    .cal-public-banner {
        background: linear-gradient(90deg, #0369a1, #0284c7);
        color: #ffffff;
        padding: 12px 20px;
        font-weight: 800;
        font-size: 16px;
        text-align: center;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.25);
        letter-spacing: 0.5px;
    }
    
    /* Pasek legendy */
    .legend-container {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
        background: #131b2e;
        padding: 10px 18px;
        border-radius: 8px;
        border: 1px solid #23314d;
        margin-bottom: 20px;
        font-size: 12px;
    }
    .legend-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: #cbd5e1;
        font-weight: 600;
    }
    .legend-dot {
        width: 10px;
        height: 10px;
        border-radius: 3px;
    }

    /* Kafelki wizyt na stanowiskach */
    .app-card-box {
        background: #151d30;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 12px;
        border: 1.5px solid #23314d;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .app-card-box.type-stal {
        border-color: #38bdf8;
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.25), rgba(7, 89, 133, 0.2));
    }
    .app-card-box.type-alu {
        border-color: #34d399;
        background: linear-gradient(135deg, rgba(5, 150, 105, 0.25), rgba(6, 95, 70, 0.2));
    }
    .app-card-box.type-alupremium {
        border-color: #c084fc;
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.25), rgba(91, 33, 182, 0.2));
    }
    .app-card-box.type-bus {
        border-color: #fcd34d;
        background: linear-gradient(135deg, rgba(217, 119, 6, 0.25), rgba(146, 64, 14, 0.2));
    }
    .app-card-box.type-szybki {
        border-color: #f472b6;
        background: linear-gradient(135deg, rgba(219, 39, 119, 0.25), rgba(157, 23, 77, 0.2));
    }
    
    .time-badge {
        display: inline-block;
        background: rgba(0, 0, 0, 0.4);
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 700;
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 6px;
    }
    .service-badge {
        font-size: 14px;
        font-weight: 800;
        color: #ffffff;
    }

    /* Tabele Dataframe */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        border: 1px solid #23314d;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# --- OBSŁUGA BAZY DANYCH I KONFIGURACJI ---
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

# Ładujemy dane
db_data = load_db()
app_config = load_config()

# --- STAN SESJI LOGOWANIA ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "logged_user" not in st.session_state:
    st.session_state["logged_user"] = ""

# --- PANEL BOCZNY (SIDEBAR) Z OBSŁUGĄ LOGOWANIA ---
st.sidebar.markdown("## 🛞 4KołaMag")

if st.session_state["authenticated"]:
    # UŻYTKOWNIK ZALOGOWANY
    st.sidebar.success(f"👤 **Zalogowano jako:**\n`{st.session_state['logged_user']}`")
    
    if st.sidebar.button("🚪 Wyloguj się", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["logged_user"] = ""
        st.rerun()

    st.sidebar.markdown("---")
    menu_choice = st.sidebar.radio(
        "Nawigacja po panelu warsztatu:",
        [
            "📊 Dashboard & Magazyn Opon",
            "➕ Przyjmij Nowy Depozyt",
            "📅 Kalendarz Wizyt (Admin)",
            "📜 Archiwum Wydanych Opon",
            "⚙️ Konfiguracja & Uprawnienia",
            "👁️ Podgląd Publiczny (dla Klientów)"
        ]
    )

    deposits = db_data.get("deposits", [])
    archive = db_data.get("archive", [])
    appointments = db_data.get("appointments", [])

    st.sidebar.markdown("---")
    st.sidebar.caption("📦 **Podsumowanie magazynu:**")
    st.sidebar.write(f"• Aktywne depozyty: `{len(deposits)}`")
    st.sidebar.write(f"• Archiwum wydanych: `{len(archive)}`")
    st.sidebar.write(f"• Zapisane wizyty: `{len(appointments)}`")

else:
    # UŻYTKOWNIK NIEZALOGOWANY (WIDOK PUBLICZNY)
    menu_choice = "👁️ Podgląd Publiczny (dla Klientów)"
    
    st.sidebar.info("🔒 **Jesteś w widoku publicznym dla klientów.**\n\nPanel magazynu i dane klientów są zablokowane.")
    
    with st.sidebar.expander("🔐 Logowanie do Panelu Warsztatu", expanded=True):
        login_email = st.text_input("Adres E-mail pracownika:", placeholder="np. michal@twoje4kola.pl").strip().lower()
        login_password = st.text_input("Hasło dostępowe:", type="password")
        
        if st.button("Zaloguj się →", type="primary", use_container_width=True):
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

            if not login_email:
                st.error("Wpisz swój adres e-mail.")
            elif not is_email_valid:
                st.error(f"⚠️ Adres '{login_email}' nie znajduje się na liście pracowników warsztatu.")
            elif login_password != correct_password:
                st.error("⚠️ Nieprawidłowe hasło dostępowe.")
            else:
                st.session_state["authenticated"] = True
                st.session_state["logged_user"] = login_email
                st.success("Zalogowano pomyślnie!")
                st.rerun()

# ==========================================================
# 1. WIDOK DLA KLIENTÓW: TERMINARZ PUBLICZNY (BEZ DANYCH OSOBOWYCH)
# ==========================================================
if menu_choice == "👁️ Podgląd Publiczny (dla Klientów)":
    banner_text = app_config.get("publicHeader", "Wulkanizacja Michał - rezerwacja terminu 600223669")
    st.markdown(f'<div class="cal-public-banner">📢 {banner_text}</div>', unsafe_allow_html=True)

    # Pasek legendy
    st.markdown("""
    <div class="legend-container">
        <span style="font-weight: 700; color: #fff;">Etykiety usług:</span>
        <span class="legend-chip"><span class="legend-dot" style="background: #0284c7;"></span> Stal (45m)</span>
        <span class="legend-chip"><span class="legend-dot" style="background: #10b981;"></span> Alu ≤ 17" (45m)</span>
        <span class="legend-chip"><span class="legend-dot" style="background: #8b5cf6;"></span> AluPremium > 17" (1h)</span>
        <span class="legend-chip"><span class="legend-dot" style="background: #f59e0b;"></span> Bus (1h)</span>
        <span class="legend-chip"><span class="legend-dot" style="background: #ec4899;"></span> Szybki (30m)</span>
        <span style="margin-left: auto; color: #38bdf8; font-weight: 600;">🕒 Godziny: 08:00 – 18:00 (Stanowiska 1 i 2)</span>
    </div>
    """, unsafe_allow_html=True)

    # Wybór daty
    c_nav1, c_nav2, c_nav3, c_date = st.columns([1, 1, 1, 2])
    if "cal_date" not in st.session_state:
        st.session_state["cal_date"] = date.today()

    if c_nav1.button("← Poprzedni dzień"):
        st.session_state["cal_date"] -= timedelta(days=1)
        st.rerun()
    if c_nav2.button("Dziś"):
        st.session_state["cal_date"] = date.today()
        st.rerun()
    if c_nav3.button("Następny dzień →"):
        st.session_state["cal_date"] += timedelta(days=1)
        st.rerun()

    chosen_date = c_date.date_input("Wybierz dzień kalendarza:", value=st.session_state["cal_date"], key="cal_picker")
    if chosen_date != st.session_state["cal_date"]:
        st.session_state["cal_date"] = chosen_date
        st.rerun()

    date_str = st.session_state["cal_date"].strftime("%Y-%m-%d")
    polish_weekdays = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
    day_name = polish_weekdays[st.session_state["cal_date"].weekday()]
    
    st.markdown(f"### 📅 {day_name}, {st.session_state['cal_date'].strftime('%d.%m.%Y')}")

    # Pobieramy wizyty na wybrany dzień
    appointments = db_data.get("appointments", [])
    day_apps = [a for a in appointments if a.get("date") == date_str]
    st1_apps = [a for a in day_apps if int(a.get("station", 1)) == 1]
    st2_apps = [a for a in day_apps if int(a.get("station", 1)) == 2]

    col_st1, col_st2 = st.columns(2)

    def get_service_type_class(sname):
        s = str(sname).lower()
        if "premium" in s: return "type-alupremium"
        if "alu" in s: return "type-alu"
        if "bus" in s: return "type-bus"
        if "szybki" in s or "wyważ" in s: return "type-szybki"
        return "type-stal"

    with col_st1:
        st.markdown(f"#### 🚗 Stanowisko 1 (Podnośnik A)")
        if st1_apps:
            st.caption(f"Zajęte terminy: {len(st1_apps)}")
            for app in sorted(st1_apps, key=lambda x: x.get("startTime", "")):
                t_cls = get_service_type_class(app.get("serviceName", ""))
                srv_title = app.get("serviceName", "Wymiana opon")
                st.markdown(f"""
                <div class="app-card-box {t_cls}">
                    <span class="time-badge">⏰ {app.get('startTime')} – {app.get('endTime')} ({app.get('durationMinutes', 45)} min)</span>
                    <div class="service-badge">🔧 {srv_title}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✓ Brak zarezerwowanych wizyt. Wszystkie godziny wolne!")

    with col_st2:
        st.markdown(f"#### 🚙 Stanowisko 2 (Podnośnik B)")
        if st2_apps:
            st.caption(f"Zajęte terminy: {len(st2_apps)}")
            for app in sorted(st2_apps, key=lambda x: x.get("startTime", "")):
                t_cls = get_service_type_class(app.get("serviceName", ""))
                srv_title = app.get("serviceName", "Wymiana opon")
                st.markdown(f"""
                <div class="app-card-box {t_cls}">
                    <span class="time-badge">⏰ {app.get('startTime')} – {app.get('endTime')} ({app.get('durationMinutes', 45)} min)</span>
                    <div class="service-badge">🔧 {srv_title}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✓ Brak zarezerwowanych wizyt. Wszystkie godziny wolne!")

    st.markdown("---")
    st.info("💡 **Chcesz umówić dogodny termin wymiany opon?** Zadzwoń do warsztatu pod numer podany w nagłówku!")

# ==========================================================
# 2. DASHBOARD & MAGAZYN OPON (TYLKO DLA ZALOGOWANYCH)
# ==========================================================
elif menu_choice == "📊 Dashboard & Magazyn Opon" and st.session_state["authenticated"]:
    st.header("📊 Stan Magazynu i Aktywne Depozyty")

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
        txt = f"{d.get('carLicensePlate','')} {d.get('clientName','')} {d.get('clientPhone','')} {d.get('tireBrand','')} {d.get('tireSize','')} {d.get('location','')}".lower()
        if (not search_q or search_q in txt) and (loc_filter == "Wszystkie" or str(d.get("location","")).lower() == loc_filter.lower()):
            filtered.append({**d, "dni": calculate_days(d.get("depositDate", ""))})

    if filtered:
        df_main = pd.DataFrame(filtered)
        col_names = {
            "carLicensePlate": "Rejestracja",
            "clientName": "Klient",
            "clientPhone": "Telefon",
            "tireBrand": "Marka",
            "tireSize": "Rozmiar",
            "tireSeason": "Sezon",
            "quantity": "Sztuk",
            "location": "Lokalizacja",
            "depositDate": "Data przyjęcia",
            "price": "Cena (PLN)",
            "dni": "Dni w magazynie"
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
        st.subheader("Wydanie depozytu (przeniesienie do archiwum)")
        col_sel, col_btn = st.columns([3, 1])
        opts = {f"{d.get('carLicensePlate')} - {d.get('clientName')} ({d.get('tireSize')})": d.get("id") for d in deposits}
        chosen_dep = col_sel.selectbox("Wybierz opony do wydania klientowi:", options=list(opts.keys()))
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
# 3. PRZYJMIJ NOWY DEPOZYT (TYLKO DLA ZALOGOWANYCH)
# ==========================================================
elif menu_choice == "➕ Przyjmij Nowy Depozyt" and st.session_state["authenticated"]:
    st.header("➕ Nowy Depozyt Opon")
    with st.form("new_deposit"):
        c1, c2 = st.columns(2)
        c_name = c1.text_input("Imię i Nazwisko / Firma *", placeholder="np. Jan Kowalski")
        c_phone = c2.text_input("Numer Telefonu *", placeholder="np. 600 123 456")
        c_email = c1.text_input("Adres E-mail klienta (opcjonalnie)", placeholder="klient@gmail.com")
        c_plate = c2.text_input("Numer Rejestracyjny *", placeholder="np. PRA 11111").upper().strip()

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

        if st.form_submit_button("💾 Zapisz Depozyt", type="primary"):
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
# 4. KALENDARZ WIZYT (ADMIN)
# ==========================================================
elif menu_choice == "📅 Kalendarz Wizyt (Admin)" and st.session_state["authenticated"]:
    st.header("📅 Zarządzanie Wizytami i Rezerwacjami")

    adm_date = st.date_input("Dzień do edycji:", value=date.today())
    d_str = adm_date.strftime("%Y-%m-%d")

    apps = db_data.get("appointments", [])
    matching = [a for a in apps if a.get("date") == d_str]

    st.subheader(f"Wizyty na dzień {d_str} ({len(matching)} aut)")
    if matching:
        df_apps = pd.DataFrame(matching)
        st.dataframe(df_apps[["startTime", "endTime", "station", "carLicensePlate", "clientAcronym", "serviceName", "price", "status"]].rename(columns={
            "startTime": "Od",
            "endTime": "Do",
            "station": "Stanowisko",
            "carLicensePlate": "Rejestracja",
            "clientAcronym": "Akronim",
            "serviceName": "Usługa",
            "price": "Cena",
            "status": "Status"
        }), use_container_width=True)
    else:
        st.info("Brak zaplanowanych wizyt na ten dzień.")

    with st.expander("➕ Dodaj nową wizytę", expanded=True):
        with st.form("admin_new_app"):
            c_a, c_b, c_c = st.columns(3)
            app_start = c_a.time_input("Godzina rozpoczęcia", value=datetime.strptime("09:00", "%H:%M").time())
            app_dur = c_b.selectbox("Czas trwania", [30, 45, 60, 90], index=1)
            app_st = c_c.selectbox("Stanowisko", [1, 2], format_func=lambda x: f"Stanowisko {x} (Podnośnik {'A' if x==1 else 'B'})")

            c_d, c_e, c_f = st.columns(3)
            app_plate = c_d.text_input("Numer rejestracyjny *", placeholder="np. PRA 11111").upper().strip()
            app_acro = c_e.text_input("Akronim klienta", placeholder="np. BOLEK")
            app_srv = c_f.selectbox("Usługa", [
                "Stal - 4 koła stalowe (osobowe)",
                "Alu - koła aluminiowe <= 17 cali",
                "AluPremium - koła aluminiowe > 17 cali",
                "Bus - samochód dostawczy",
                "Szybki serwis / wyważenie"
            ])

            if st.form_submit_button("Zapisz Wizytę", type="primary"):
                if not app_plate:
                    st.error("Podaj numer rejestracyjny.")
                else:
                    start_str = app_start.strftime("%H:%M")
                    start_dt = datetime.combine(date.today(), app_start)
                    end_dt = start_dt + timedelta(minutes=app_dur)
                    end_str = end_dt.strftime("%H:%M")

                    new_app = {
                        "id": f"app_{int(datetime.now().timestamp())}",
                        "date": d_str,
                        "startTime": start_str,
                        "endTime": end_str,
                        "durationMinutes": int(app_dur),
                        "station": int(app_st),
                        "carLicensePlate": app_plate,
                        "clientAcronym": app_acro,
                        "serviceName": app_srv,
                        "price": 140,
                        "status": "scheduled"
                    }
                    db_data["appointments"].append(new_app)
                    save_db(db_data)
                    st.success(f"Zapisano wizytę dla {app_plate}!")
                    st.rerun()

# ==========================================================
# 5. ARCHIWUM WYDANYCH OPON (TYLKO DLA ZALOGOWANYCH)
# ==========================================================
elif menu_choice == "📜 Archiwum Wydanych Opon" and st.session_state["authenticated"]:
    st.header("📜 Archiwum Wydanych Opon")
    archive = db_data.get("archive", [])
    if archive:
        df_arch = pd.DataFrame(archive)
        st.dataframe(df_arch[["carLicensePlate", "clientName", "clientPhone", "tireBrand", "tireSize", "location", "depositDate", "releaseDate"]].rename(columns={
            "carLicensePlate": "Rejestracja",
            "clientName": "Klient",
            "clientPhone": "Telefon",
            "tireBrand": "Marka",
            "tireSize": "Rozmiar",
            "location": "Była Lokalizacja",
            "depositDate": "Przyjęto",
            "releaseDate": "Wydano"
        }), use_container_width=True)
    else:
        st.info("Brak wpisów w archiwum.")

# ==========================================================
# 6. KONFIGURACJA & UPRAWNIENIA (TYLKO DLA ZALOGOWANYCH)
# ==========================================================
elif menu_choice == "⚙️ Konfiguracja & Uprawnienia" and st.session_state["authenticated"]:
    st.header("⚙️ Konfiguracja Systemu")
    with st.form("cfg_form"):
        hdr = st.text_input("Nagłówek kalendarza publicznego (rezerwacje telefoniczne):", value=app_config.get("publicHeader", ""))
        
        cur_emails = app_config.get("allowedEmails", ["michal@twoje4kola.pl", "alert@itover.pl"])
        emails_val = ", ".join(cur_emails) if isinstance(cur_emails, list) else str(cur_emails)
        emails_in = st.text_area("Dozwolone adresy e-mail (oddzielone przecinkami):", value=emails_val)
        
        pwd_in = st.text_input("Hasło dostępu do panelu:", value=app_config.get("adminPassword", "admin"), type="password")

        if st.form_submit_button("Zapisz Konfigurację", type="primary"):
            parsed_e = [e.strip().lower() for e in emails_in.replace("\n", ",").split(",") if e.strip() and "@" in e]
            app_config["publicHeader"] = hdr.strip()
            app_config["allowedEmails"] = parsed_e if parsed_e else ["michal@twoje4kola.pl", "alert@itover.pl"]
            app_config["adminPassword"] = pwd_in.strip() or "admin"
            save_config(app_config)
            st.success("Zapisano konfigurację!")
            st.rerun()
