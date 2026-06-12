import streamlit as st
import numpy as np
import requests
import pandas as pd
import urllib3
from datetime import datetime, timedelta

# 強制關閉跳過 SSL 檢查而產生的安全警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 1. 綁定實體 CWA API 授權碼與全域資料庫初始化
# ==========================================
CWA_API_KEY = "CWA-8794BCB2-04B5-4953-8EE1-CB3059C339D0"

# 智慧記憶體：若資料庫不存在則初始化，防止切換分頁時遺失數據
if 'weather_db' not in st.session_state:
    # 預載入 2026-06-01 至 06-12 您的現地精密流水帳作為基礎資料庫
    st.session_state.weather_db = {
        "2026-06-01": {"sl_pres": 1009.0, "sl_tx": 31.0, "sl_tn": 23.5, "sl_ws": 0.9, "sl_precp": 0.0, "sl_rs": 22.0, "sl_td": 21.0, "bq_pres": 1009.5, "bq_tx": 31.2, "bq_tn": 23.8, "bq_ws": 1.1, "bq_precp": 0.0, "bq_rs": 21.5, "bq_td": 21.2},
        "2026-06-02": {"sl_pres": 1008.5, "sl_tx": 31.5, "sl_tn": 24.0, "sl_ws": 1.1, "sl_precp": 0.0, "sl_rs": 23.0, "sl_td": 21.5, "bq_pres": 1008.9, "bq_tx": 31.8, "bq_tn": 24.1, "bq_ws": 1.3, "bq_precp": 0.0, "bq_rs": 22.0, "bq_td": 21.6},
        "2026-06-03": {"sl_pres": 1007.0, "sl_tx": 30.0, "sl_tn": 23.8, "sl_ws": 1.0, "sl_precp": 9.5, "sl_rs": 15.0, "sl_td": 22.0, "bq_pres": 1007.2, "bq_tx": 30.2, "bq_tn": 23.9, "bq_ws": 1.2, "bq_precp": 12.0, "bq_rs": 14.2, "bq_td": 22.1},
        "2026-06-04": {"sl_pres": 1006.5, "sl_tx": 29.0, "sl_tn": 23.0, "sl_ws": 0.9, "sl_precp": 75.0, "sl_rs": 10.0, "sl_td": 22.5, "bq_pres": 1006.8, "bq_tx": 29.1, "bq_tn": 23.2, "bq_ws": 1.0, "bq_precp": 82.0, "bq_rs": 9.5, "bq_td": 22.4},
        "2026-06-05": {"sl_pres": 1008.2, "sl_tx": 30.5, "sl_tn": 23.1, "sl_ws": 0.6, "sl_precp": 44.5, "sl_rs": 21.0, "sl_td": 21.5, "bq_pres": 1008.4, "bq_tx": 30.6, "bq_tn": 23.4, "bq_ws": 0.8, "bq_precp": 48.0, "bq_rs": 20.1, "bq_td": 21.7},
        "2026-06-06": {"sl_pres": 1007.9, "sl_tx": 32.1, "sl_tn": 24.2, "sl_ws": 0.9, "sl_precp": 0.0, "sl_rs": 23.4, "sl_td": 22.1, "bq_pres": 1008.1, "bq_tx": 32.3, "bq_tn": 24.4, "bq_ws": 1.0, "bq_precp": 0.0, "bq_rs": 22.8, "bq_td": 22.3},
        "2026-06-07": {"sl_pres": 1009.1, "sl_tx": 31.4, "sl_tn": 25.0, "sl_ws": 0.7, "sl_precp": 99.0, "sl_rs": 19.5, "sl_td": 23.0, "bq_pres": 1009.3, "bq_tx": 31.6, "bq_tn": 25.1, "bq_ws": 0.9, "bq_precp": 105.0, "bq_rs": 18.2, "bq_td": 23.2},
        "2026-06-08": {"sl_pres": 1008.5, "sl_tx": 29.8, "sl_tn": 23.8, "sl_ws": 0.6, "sl_precp": 18.0, "sl_rs": 17.1, "sl_td": 22.4, "bq_pres": 1008.7, "bq_tx": 29.9, "bq_tn": 24.0, "bq_ws": 0.7, "bq_precp": 20.0, "bq_rs": 16.5, "bq_td": 22.5},
        "2026-06-09": {"pres": 1005.1, "tmax": 33.2, "tmin": 22.9, "ws": 1.5, "precp": 23.5, "rad": 12.0, "tdew": 21.8, "sl_pres": 1005.1, "sl_tx": 33.2, "sl_tn": 22.9, "sl_ws": 1.5, "sl_precp": 23.5, "sl_rs": 12.0, "sl_td": 21.8, "bq_pres": 1005.4, "bq_tx": 33.4, "bq_tn": 23.0, "bq_ws": 1.7, "bq_precp": 25.0, "bq_rs": 11.2, "bq_td": 21.9},
        "2026-06-10": {"sl_pres": 1006.4, "sl_tx": 26.5, "sl_tn": 21.8, "sl_ws": 1.5, "sl_precp": 22.0, "sl_rs": 5.4, "sl_td": 20.9, "bq_pres": 1006.7, "bq_tx": 26.8, "bq_tn": 22.0, "bq_ws": 1.6, "bq_precp": 24.0, "bq_rs": 5.0, "bq_td": 21.0},
        "2026-06-11": {"sl_pres": 1007.8, "sl_tx": 31.0, "sl_tn": 24.0, "sl_ws": 2.1, "sl_precp": 6.0, "sl_rs": 22.1, "sl_td": 22.0, "bq_pres": 1008.0, "bq_tx": 31.2, "bq_tn": 24.2, "bq_ws": 2.3, "bq_precp": 7.2, "bq_rs": 21.4, "bq_td": 22.1},
        "2026-06-12": {"sl_pres": 1008.0, "sl_tx": 31.5, "sl_tn": 24.5, "sl_ws": 2.4, "sl_precp": 0.0, "sl_rs": 20.0, "sl_td": 21.8, "bq_pres": 1008.2, "bq_tx": 31.7, "bq_tn": 24.6, "bq_ws": 2.5, "bq_precp": 0.0, "bq_rs": 19.5, "bq_td": 21.9}
    }

if 'root_depth' not in st.session_state: st.session_state.root_depth = 300
if 'field_area' not in st.session_state: st.session_state.field_area = 100.0
if 'kc' not in st.session_state: st.session_state.kc = 0.75
if 'target_vwc' not in st.session_state: st.session_state.target_vwc = 0.24

# ==========================================
# 2. 核心科學公式定義
# ==========================================

def calculate_vwc(h):
    """依據 Van Genuchten 公式計算體積含水率 VWC (m3/m3)"""
    if h <= 0: return 0.381
    numerator = 0.381 - 0.1588
    denominator = (1 + (1.773 * h) ** 1.6282) ** 0.3858
    return 0.1588 + (numerator / denominator)

def calculate_et0(t_max, t_min, t_dew, u_z, r_s, z, latitude, day_of_year, z_wind=10):
    """FAO-56 Penman-Monteith 標準基準蒸發散量計算"""
    P = 101.3 * ((293 - 0.0065 * z) / 293) ** 5.26
    gamma = 0.665 * 10**-3 * P
    t_mean = (t_max + t_min) / 2
    delta = (4098 * (0.6108 * np.exp((17.27 * t_mean) / (t_mean + 237.3)))) / (t_mean + 237.3)**2
    
    e0_tmax = 0.6108 * np.exp((17.27 * t_max) / (t_max + 237.3))
    e0_tmin = 0.6108 * np.exp((17.27 * t_min) / (t_min + 237.3))
    e_s = (e0_tmax + e0_tmin) / 2
    e_a = 0.6108 * np.exp((17.27 * t_dew) / (t_dew + 237.3))
    
    phi = np.radians(latitude)
    dr = 1 + 0.033 * np.cos(2 * np.pi / 365 * day_of_year)
    solar_dec = 0.409 * np.sin(2 * np.pi / 365 * day_of_year - 1.39)
    
    arg = -np.tan(phi) * np.tan(solar_dec)
    arg = np.clip(arg, -1.0, 1.0)
    omega_s = np.arccos(arg)
    
    R_a = (24 * 60 / np.pi) * 0.082 * dr * (omega_s * np.sin(phi) * np.sin(solar_dec) + np.cos(phi) * np.cos(solar_dec) * np.sin(omega_s))
    R_ns = (1 - 0.23) * r_s
    R_so = (0.75 + 2 * 10**-5 * z) * R_a
    
    t_max_k, t_min_k = t_max + 273.16, t_min + 273.16
    sigma = 4.903 * 10**-9
    
    r_ratio = r_s / R_so if R_so > 0 else 1
    R_nl = sigma * ((t_max_k**4 + t_min_k**4) / 2) * (0.34 - 0.14 * np.sqrt(e_a)) * (1.35 * r_ratio - 0.35)
    R_n = R_ns - R_nl
    
    u2 = max(0.5, u_z * 4.87 / np.log(67.8 * z_wind - 5.42))
    num = 0.408 * delta * (R_n - 0) + gamma * (900 / (t_mean + 273)) * u2 * (e_s - e_a)
    den = delta + gamma * (1 + 0.34 * u2)
    return max(0.0, num / den)

# ==========================================
# 3. 氣象署 API 自動串接調度器
# ==========================================

@st.cache_data(ttl=600)
def fetch_automated_cwa_data():
    """自動串接 72AI40 今日即時與板橋(466881)歷史、樹林預報"""
    today_data, future_list = None, []
    
    # A. 抓取樹林無人站 (72AI40) 的今日實時數據
    try:
        url_now = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization={CWA_API_KEY}&StationId=72AI40"
        res_now = requests.get(url_now, timeout=8, verify=False).json()
        if 'records' in res_now and res_now['records']['Station']:
            s_data = res_now['records']['Station'][0]['WeatherElement']
            t_now = float(s_data.get('AirTemperature', 28.0))
            u_z = float(s_data.get('WindSpeed', 1.2))
            rh = float(s_data.get('RelativeHumidity', 80.0)) / 100.0
            alpha = ((17.27 * t_now) / (237.7 + t_now)) + np.log(max(rh, 0.01))
            t_dew = (237.7 * alpha) / (17.27 - alpha)
            
            today_data = {"t_max": t_now + 2.0, "t_min": t_now - 2.0, "t_dew": round(t_dew, 1), "u_z": u_z, "r_s": 22.0}
    except:
        pass

    # B. 自動抓取板橋大站 (466881) 過去 7 天真實觀測並寫入記憶體
    try:
        url_hist = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={CWA_API_KEY}&StationId=466881"
        res_hist = requests.get(url_hist, timeout=8, verify=False).json()
        if 'records' in res_hist and res_hist['records']['Station']:
            hist_records = res_hist['records']['Station'][0]['WeatherElement']['DailyStat']
            for day in hist_records:
                d_str = day['Date']
                # 將板橋大站數據合併更新至全域記憶體中
                if d_str not in st.session_state.weather_db:
                    st.session_state.weather_db[d_str] = {"sl_pres": 1008.0, "sl_tx": 31.0, "sl_tn": 24.0, "sl_ws": 1.2, "sl_precp": 0.0, "sl_rs": 20.0, "sl_td": 22.0}
                
                st.session_state.weather_db[d_str].update({
                    "bq_pres": float(day['AirPressure']['Mean']),
                    "bq_tx": float(day['AirTemperature']['Maximum']),
                    "bq_tn": float(day['AirTemperature']['Minimum']),
                    "bq_ws": float(day['WindSpeed']['Mean']),
                    "bq_precp": float(day['Precipitation']['Accumulation']),
                    "bq_rs": float(day['GlobalSolarRadiation']['Accumulation']) if float(day['GlobalSolarRadiation']['Accumulation']) > 0 else 18.5,
                    "bq_td": round(float(day['AirTemperature']['Mean']) - ((100 - float(day['RelativeHumidity']['Mean'])) / 5), 1)
                })
    except:
        pass

    # C. 未來 7 天預報：完全對齊小寫 json 語法 (F-D0047-069)
    try:
        url_fore = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-069?Authorization={CWA_API_KEY}"
        res_fore = requests.get(url_fore, timeout=8, verify=False).json()
        rec_node = res_fore.get('records', {})
        locs_container = rec_node.get('locations', rec_node.get('Locations', []))[0]
        loc_list = locs_container.get('location', locs_container.get('Location', []))
        
        shulin_node = [loc for loc in loc_list if loc.get('locationName') == "樹林區"][0]
        w_elements = shulin_node.get('weatherElement', [])
        times_loop = w_elements[0].get('time', [])
        
        for i in range(0, len(times_loop), 2):
            if len(future_list) >= 7: break
            t_info = times_loop[i]
            
            def get_forecast_value(element_title):
                for el in w_elements:
                    if el.get('elementName') == element_title:
                        val_list = el.get('time', [])[i].get('elementValue', [])
                        return val_list[0].get('value', '0')
                return '0'
            
            future_list.append({
                "預報日期": t_info.get('startTime', '2026-06-12')[:10],
                "預估最高溫 (℃)": float(get_forecast_value("MaxT")),
                "預估最低溫 (℃)": float(get_forecast_value("MinT")),
                "預估風速 (m/s)": float(get_forecast_value("WS")),
                "白晝降雨機率 (%)": int(get_forecast_value("PoP12h") or 0),
                "天氣狀況": get_forecast_value("Wx"),
                "全天空日射量推估 (MJ/㎡)": 22.0 if "雨" not in get_forecast_value("Wx") else 11.0,
                "預估露點溫度 (℃)": float(get_forecast_value("Td"))
            })
    except:
        pass

    return today_data, future_list

cwa_now, cwa_future = fetch_automated_cwa_data()

# ==========================================
# 4. 網頁全新四大分頁佈局
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 土壤含水與灌溉決策", "📅 歷史氣象與 ET0 對照", "🔮 未來一週天氣預報", "⚙️ 幕後設定參數"])

today_dt = datetime.now()
current_doy = today_dt.timetuple().tm_yday

# ------------------------------------------
# 分頁一：土壤含水與灌溉決策
# ------------------------------------------
with tab1:
    st.header("💧 即時動態灌溉調度面板")
    t1_col1, t1_col2 = st.columns(2)
    with t1_col1:
        h_input = st.number_input("👉 請輸入當前田間張力計實測讀值 (kPa)", value=30.0, step=1.0)
    with t1_col2:
        default_rs = cwa_now["r_s"] if cwa_now else 22.0
        r_s_input = st.number_input("☀️ 今日累積日射量 (MJ/㎡·day)", value=default_rs, step=0.5)

    t_max = cwa_now["t_max"] if cwa_now else 31.5
    t_min = cwa_now["t_min"] if cwa_now else 24.2
    t_dew = cwa_now["t_dew"] if cwa_now else 22.1
    u_z = cwa_now["u_z"] if cwa_now else 1.5

    current_vwc = calculate_vwc(h_input)
    et0 = calculate_et0(t_max, t_min, t_dew, u_z, r_s_input, st.session_state.z if 'z' in st.session_state else 40.0, st.session_state.latitude, current_doy)
    etc = et0 * st.session_state.kc
    
    soil_water_deficit_mm = max(0.0, (st.session_state.target_vwc - current_vwc) * st.session_state.root_depth)
    total_water_volume_liters = (soil_water_deficit_mm + etc) * st.session_state.field_area

    st.markdown("---")
    res_col1, res_col2, res_col3 = st.columns(3)
    with res_col1: st.metric("推估當前土壤體積含水量 (VWC)", f"{current_vwc*100:.2f} %")
    with res_col2: st.metric("實時計算作物耗水 (ETc)", f"{etc:.2f} mm/day")
    with res_col3: st.metric("建議精確補水總體積", f"{total_water_volume_liters:.1f} 公升 (L)")

    st.markdown("### 🚨 系統自動調度狀態診斷")
    if h_input > 25.0:
        st.error(f"🔴 **【系統狀態：建議灌水】** 目前水分張力為 {h_input} kPa (已越過乾燥警戒值 > 25 kPa)。土壤缺水，請補水！")
    elif h_input < 15.0:
        st.success(f"🔵 **【系統狀態：全面停水】** 目前水分張力為 {h_input} kPa (已越過潮濕警戒值 < 15 kPa)。土壤水分飽和，停水！")
    else:
        st.warning(f"🟢 **【系統狀態：狀態良好】** 目前水分張力為 {h_input} kPa (維持在適宜區間 15 ~ 25 kPa)。")

# ------------------------------------------
# 分頁二：歷史氣象與 ET0 對照 (雙站記憶 + 日期回溯器)
# ------------------------------------------
with tab2:
    st.header("📅 雙站氣象歷史記憶資料庫")
    
    # A. 樹林手動上傳區
    st.markdown("### 📂 樹林分場 - 手動流水帳上傳同步")
    uploaded_file = st.file_uploader("拖曳上傳樹林分場 Excel 紀錄檔，系統會將其合併寫入永久記憶體", type=["xlsx", "csv"])
    if uploaded_file is not None:
        try:
            df_user = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
            df_user.columns = df_user.columns.str.strip()
            for _, row in df_user.iterrows():
                d_str = str(row.get("ObsTime", row.iloc[0]))[:10]
                if d_str not in st.session_state.weather_db:
                    st.session_state.weather_db[d_str] = {"bq_pres": 1008.0, "bq_tx": 31.0, "bq_tn": 24.0, "bq_ws": 1.2, "bq_precp": 0.0, "bq_rs": 20.0, "bq_td": 22.0}
                st.session_state.weather_db[d_str].update({
                    "sl_pres": float(row.get("Pres", 1008.0)),
                    "sl_tx": float(row.get("Tx", 31.0)),
                    "sl_tn": float(row.get("Tn", 24.0)),
                    "sl_ws": float(row.get("WS", 1.0)),
                    "sl_precp": float(row.get("Precp", 0.0)),
                    "sl_rs": float(row.get("St", 20.0)),
                    "sl_td": float(row.get("Td", 22.0))
                })
            st.success("🎉 樹林分場歷史流水帳已成功記憶合併！")
        except:
            st.error("上傳格式解析失敗。")

    st.markdown("---")
    
    # B. 呈現近七天雙站對照表
    st.subheader("📋 近 7 日雙站觀測與各自 ET0 預估報表")
    sorted_dates = sorted(list(st.session_state.weather_db.keys()))[-7:]
    
    display_rows = []
    for d in sorted_dates:
        node = st.session_state.weather_db[d]
        d_dt = datetime.strptime(d, "%Y-%m-%d")
        doy = d_dt.timetuple().tm_yday
        
        # 各自帶入公式算當天 ET0
        sl_et0 = calculate_et0(node.get("sl_tx",31.0), node.get("sl_tn",24.0), node.get("sl_td",22.0), node.get("sl_ws",1.0), node.get("sl_rs",20.0), 40.0, 24.9445, doy)
        bq_et0 = calculate_et0(node.get("bq_tx",31.0), node.get("bq_tn",24.0), node.get("bq_td",22.0), node.get("bq_ws",1.0), node.get("bq_rs",20.0), 24.5, 24.9592, doy)
        
        display_rows.append({
            "日期": d,
            "樹林降雨(mm)": node.get("sl_precp", 0.0),
            "樹林風速(m/s)": node.get("sl_ws", 1.0),
            "樹林預估ET0": round(sl_et0, 2),
            "板橋(466881)降雨": node.get("bq_precp", 0.0),
            "板橋風速": node.get("bq_ws", 1.0),
            "板橋預估ET0": round(bq_et0, 2)
        })
    st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    
    # 🌟 核心：任意日期回溯查詢器
    st.subheader("🔍 歷史日期任意觀測回溯 lookup")
    search_date = st.date_input("📅 請選擇欲回溯查詢的歷史日期", value=datetime.strptime(sorted_dates[-1], "%Y-%m-%d"))
    search_str = search_date.strftime("%Y-%m-%d")
    
    if search_str in st.session_state.weather_db:
        s_node = st.session_state.weather_db[search_str]
        s_doy = search_date.timetuple().tm_yday
        s_sl_et0 = calculate_et0(s_node.get("sl_tx",31.0), s_node.get("sl_tn",24.0), s_node.get("sl_td",22.0), s_node.get("sl_ws",1.0), s_node.get("sl_rs",20.0), 40.0, 24.9445, s_doy)
        s_bq_et0 = calculate_et0(s_node.get("bq_tx",31.0), s_node.get("bq_tn",24.0), s_node.get("bq_td",22.0), s_node.get("bq_ws",1.0), s_node.get("bq_rs",20.0), 24.5, 24.9592, s_doy)
        
        st.markdown(f"#### 📊 {search_str} 當日物理因子對照清單")
        lookup_col1, lookup_col2 = st.columns(2)
        with lookup_col1:
            st.info(f"""
            **🏡 樹林分場 (手動站)**
            *   測站氣壓: `{s_node.get('sl_pres')} hPa`
            *   最高 / 最低溫: `{s_node.get('sl_tx')}°C / {s_node.get('sl_tn')}°C`
            *   實測風速 / 降雨: `{s_node.get('sl_ws')} m/s / {s_node.get('sl_precp')} mm`
            *   全天空日射量: `{s_node.get('sl_rs')} MJ/㎡`
            *   👉 **當日推估基準 ET0: {s_sl_et0:.2f} mm/day**
            """)
        with lookup_col2:
            st.warning(f"""
            **🏢 板橋大站 (站號: 466881)**
            *   測站氣壓: `{s_node.get('bq_pres')} hPa`
            *   最高 / 最低溫: `{s_node.get('bq_tx')}°C / {s_node.get('bq_tn')}°C`
            *   實測風速 / 降雨: `{s_node.get('bq_ws')} m/s / {s_node.get('bq_precp')} mm`
            *   全天空日射量: `{s_node.get('bq_rs')} MJ/㎡`
            *   👉 **當日推估基準 ET0: {s_bq_et0:.2f} mm/day**
            """)
    else:
        st.error(f"抱歉，記憶體資料庫中目前尚無 {search_str} 的觀測數據，請先於上方上傳對應時間之 Excel 帳本。")

# ------------------------------------------
# 分頁三：未來一週天氣預報 (內嵌 CWA 智慧圖標)
# ------------------------------------------
with tab3:
    st.header("🔮 樹林區未來 7 天官方天氣與降雨預報")
    
    if cwa_future:
        # 圖標對應轉換字典
        def get_weather_icon(wx_text):
            if "雷" in wx_text: return "⛈️"
            elif "雨" in wx_text: return "🌧️"
            elif "陰" in wx_text: return "🌥️"
            elif "多雲" in wx_text: return "☁️"
            else: return "☀️"
            
        st.markdown("### 📡 氣象署官方動態天氣因子圖表")
        
        # 建立美觀的圖卡排版
        cols = st.columns(7)
        for idx, day in enumerate(cwa_future):
            with cols[idx]:
                icon = get_weather_icon(day["天氣狀況"])
                st.markdown(f"""
                <div style="background-color:#1E1E1E; padding:10px; border-radius:8px; text-align:center; border:1px solid #333;">
                    <span style="font-size:14px; color:#aaa;">{day["預報日期"][5:]}</span><br>
                    <span style="font-size:32px;">{icon}</span><br>
                    <span style="font-size:12px; font-weight:bold; color:#fff;">{day["天氣狀況"]}</span><br>
                    <span style="font-size:14px; color:#ff4b4b; font-weight:bold;">{day["預估最高溫 (℃)"]}°</span> 
                    <span style="font-size:14px; color:#4b9eff;">{day["預估最低溫 (℃)"]}°</span><br>
                    <span style="font-size:12px; color:#666;">💧 降雨: {day["白晝降雨機率 (%)"]}%</span>
                </div>
                """, unsafe_allow_html=True)
                
        st.markdown("---")
        st.subheader("📑 預報要素詳細數據清單")
        st.dataframe(pd.DataFrame(cwa_future), use_container_width=True, hide_index=True)
    else:
        st.warning("預報 API 連線中，請稍候...")

# ------------------------------------------
# 分頁四：幕後設定參數
# ------------------------------------------
with tab4:
    st.header("⚙️ 系統底層物理參數維護 (固定大站參數)")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.session_state.z = st.number_input("📍 樹林分場海拔高度 (m)", value=40.0, disabled=True)
        st.session_state.latitude = st.number_input("📐 樹林分場北緯緯度 (度)", value=24.9445, format="%.4f", disabled=True)
    with col_p2:
        st.number_input("🏢 板橋主站(466881)海拔高度 (m)", value=24.5, disabled=True)
        st.number_input("📐 板橋主站(466881)北緯緯度 (度)", value=24.9592, format="%.4f", disabled=True)
        
    st.markdown("---")
    st.markdown("### 🌾 田區操作基本設定")
    t4_col1, t4_col2 = st.columns(2)
    with t4_col1:
        st.session_state.root_depth = st.number_input("📏 有效根系深度 D (mm)", value=st.session_state.root_depth, step=50)
        st.session_state.field_area = st.number_input("📐 實際灌溉面積 (㎡)", value=st.session_state.field_area, step=10.0)
    with t4_col2:
        st.session_state.kc = st.number_input("🌿 作物係數 (Kc)", value=st.session_state.kc, step=0.05)
        st.session_state.target_vwc = st.number_input("🎯 目標含水量 (田間容水量) (m3/m3)", value=st.session_state.target_vwc, step=0.01)
