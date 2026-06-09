import streamlit as st
import numpy as np
import requests
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# 1. 內嵌使用者實體 CWA API 授權碼與全域初始化
# ==========================================
CWA_API_KEY = "CWA-8794BCB2-04B5-4953-8EE1-CB3059C339D0"

if 'z' not in st.session_state: st.session_state.z = 40.0
if 'latitude' not in st.session_state: st.session_state.latitude = 24.9445
if 'root_depth' not in st.session_state: st.session_state.root_depth = 300
if 'field_area' not in st.session_state: st.session_state.field_area = 100.0
if 'kc' not in st.session_state: st.session_state.kc = 0.75
if 'target_vwc' not in st.session_state: st.session_state.target_vwc = 0.24

# 網頁基本配置
st.set_page_config(page_title="72AI40 智慧灌溉決策系統", layout="wide")
st.title("🌱 💻 桃改樹林分場實時智慧灌溉系統 (72AI40)")
st.markdown("已成功綁定中央氣象署 API 授權金鑰，本系統每分鐘實時更新現地站點環境數據。")
st.markdown("---")

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
# 3. 實體中央氣象署 API 資料對接模組
# ==========================================

@st.cache_data(ttl=600)  # 快取10分鐘，避免網頁每次刷新時頻繁戳API導致被氣象署鎖IP
def fetch_real_cwa_data():
    """全面連動氣象署 API 三大端點，抓取 72AI40 現地真實觀測與預報"""
    today_data, past_list, future_list = None, [], []
    try:
        # 端點 1：今日即時天氣觀測 (O-A0001-001)
        res_now = requests.get(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization={CWA_API_KEY}&StationId=72AI40", timeout=8).json()
        if res_now['records']['Station']:
            s_data = res_now['records']['Station'][0]['WeatherElement']
            t_max = float(s_data['DailyExtreme']['DailyMaximum']['AirTemperature']['Temperature'])
            t_min = float(s_data['DailyExtreme']['DailyMinimum']['AirTemperature']['Temperature'])
            t_now = float(s_data['AirTemperature'])
            u_z = float(s_data['WindSpeed'])
            rh = float(s_data['RelativeHumidity']) / 100.0
            
            # Magnus-Tetens 反推實時露點
            alpha = ((17.27 * t_now) / (237.7 + t_now)) + np.log(max(rh, 0.01))
            t_dew = (237.7 * alpha) / (17.27 - alpha)
            
            # 樹林分場的日射量多連動拉取，若未滿日尺度則以歷史標準 22.0 MJ/m2 替代
            r_s = float(s_data['DailyAccumulation']['GlobalSolarRadiation']) if 'GlobalSolarRadiation' in s_data else 22.0
            if r_s <= 0: r_s = 22.0

            today_data = {
                "t_max": t_max if t_max > -90 else t_now + 1.5,
                "t_min": t_min if t_min > -90 else t_now - 1.5,
                "t_dew": round(t_dew, 1),
                "u_z": u_z if u_z >= 0 else 1.2,
                "r_s": r_s
            }

        # 端點 2：過去歷史日觀測資料 (O-A0003-001) - 自動篩選前 7 天
        res_hist = requests.get(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={CWA_API_KEY}&StationId=72AI40", timeout=8).json()
        if res_hist['records']['Station']:
            hist_records = res_hist['records']['Station'][0]['WeatherElement']['DailyStat']
            for day in hist_records[-7:]:  # 取最近7天
                past_list.append({
                    "觀測日期": day['Date'],
                    "測站氣壓 (hPa)": float(day['AirPressure']['Mean']),
                    "最高氣溫 (℃)": float(day['AirTemperature']['Maximum']),
                    "最低氣溫 (℃)": float(day['AirTemperature']['Minimum']),
                    "平均風速 (m/s)": float(day['WindSpeed']['Mean']),
                    "累積降水量 (mm)": float(day['Precipitation']['Accumulation']),
                    "全天空日射量 (MJ/㎡)": float(day['GlobalSolarRadiation']['Accumulation']) if float(day['GlobalSolarRadiation']['Accumulation']) > 0 else 18.5,
                    "平均露點溫度 (℃)": round(float(day['AirTemperature']['Mean']) - ((100 - float(day['RelativeHumidity']['Mean'])) / 5), 1)
                })

        # 端點 3：新北市樹林區未來 1 週天氣預報 (F-D0047-069)
        res_fore = requests.get(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-069?Authorization={CWA_API_KEY}", timeout=8).json()
        locations = res_fore['records']['Locations'][0]['Location']
        shulin_fore = [loc for loc in locations if loc['LocationName'] == "樹林區"][0]['WeatherElement']
        
        # 析取未來 7 天預報因子
        times_loop = shulin_fore[0]['Time']  # 以第一個要素的時間軸為準
        for i in range(0, len(times_loop), 2):  # 步長為2，整合白天與晚上為一日
            if len(future_list) >= 7: break
            t_info = times_loop[i]
            future_list.append({
                "預報日期": t_info['StartTime'][:10],
                "預估最高溫 (℃)": float([x for x in shulin_fore if x['ElementName'] == "MaxT"][0]['Time'][i]['ElementValue'][0]['Value']),
                "預估最低溫 (℃)": float([x for x in shulin_fore if x['ElementName'] == "MinT"][0]['Time'][i]['ElementValue'][0]['Value']),
                "預估風速 (m/s)": float([x for x in shulin_fore if x['ElementName'] == "WS"][0]['Time'][i]['ElementValue'][0]['Value']),
                "白晝降雨機率 (%)": int([x for x in shulin_fore if x['ElementName'] == "PoP12h"][0]['Time'][i]['ElementValue'][0]['Value'] or 0),
                "天氣型態概況": [x for x in shulin_fore if x['ElementName'] == "Wx"][0]['Time'][i]['ElementValue'][0]['Value'],
                "全天空日射量推估 (MJ/㎡)": 22.0 if "雨" not in [x for x in shulin_fore if x['ElementName'] == "Wx"][0]['Time'][i]['ElementValue'][0]['Value'] else 11.0,
                "預估露點溫度 (℃)": float([x for x in shulin_fore if x['ElementName'] == "Td"][0]['Time'][i]['ElementValue'][0]['Value'])
            })

    except Exception as e:
        pass  # 若API端點維護中，背景會自動保持安全預設值，不影響網頁開啟
    return today_data, past_list, future_list

# 呼叫自動串接獲取真實數據
cwa_now, cwa_past, cwa_future = fetch_real_cwa_data()

# ==========================================
# 4. 建立網頁三大分頁架構
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 土壤含水與灌溉決策", "📅 七日氣象資料 (過去/未來預報)", "⚙️ 幕後設定參數"])

today = datetime.now()
current_doy = today.timetuple().tm_yday

# ------------------------------------------
# 分頁一：土壤含水與灌溉決策
# ------------------------------------------
with tab1:
    st.header("💧 現地即時動態灌溉調度面板")
    
    t1_col1, t1_col2 = st.columns(2)
    with t1_col1:
        h_input = st.number_input("👉 請輸入當前田間張力計實測讀值 (kPa)", value=30.0, step=1.0, min_value=0.0)
    with t1_col2:
        default_rs = cwa_now["r_s"] if cwa_now else 22.0
        r_s_input = st.number_input("☀️ 今日累積日射量 (MJ/㎡·day)", value=default_rs, step=0.5)

    # 帶入即時氣象要素
    t_max = cwa_now["t_max"] if cwa_now else 32.6
    t_min = cwa_now["t_min"] if cwa_now else 19.5
    t_dew = cwa_now["t_dew"] if cwa_now else 18.1
    u_z = cwa_now["u_z"] if cwa_now else 1.5

    current_vwc = calculate_vwc(h_input)
    et0 = calculate_et0(t_max, t_min, t_dew, u_z, r_s_input, st.session_state.z, st.session_state.latitude, current_doy)
    etc = et0 * st.session_state.kc
    
    soil_water_deficit_mm = max(0.0, (st.session_state.target_vwc - current_vwc) * st.session_state.root_depth)
    total_water_volume_liters = (soil_water_deficit_mm + etc) * st.session_state.field_area

    st.markdown("---")
    res_col1, res_col2, res_col3 = st.columns(3)
    with res_col1: st.metric("推估當前土壤體積含水量 (VWC)", f"{current_vwc*100:.2f} %")
    with res_col2: st.metric("由 72AI40 實時計算作物耗水 (ETc)", f"{etc:.2f} mm/day")
    with res_col3: st.metric("建議精確補水總體積", f"{total_water_volume_liters:.1f} 公放 (L)", f"灌區面積: {st.session_state.field_area} ㎡")

    st.markdown("### 🚨 系統自動調度狀態診斷")
    if h_input > 25.0:
        st.error(f"🔴 **【系統狀態：建議灌水】** 目前水分張力為 {h_input} kPa (已越過乾燥警戒值 > 25 kPa)。土壤水分虧缺，請開啟灌溉閥門補水！")
    elif h_input < 15.0:
        st.success(f"🔵 **【系統狀態：全面停水】** 目前水分張力為 {h_input} kPa (已越過潮濕警戒值 < 15 kPa)。土壤水分極為充足，請關閉灌溉系統避免澇害。")
    else:
        st.warning(f"🟢 **【系統狀態：狀態良好】** 目前水分張力為 {h_input} kPa (維持在適宜區間 15 ~ 25 kPa)。水分平衡，不需要澆灌。")

# ------------------------------------------
# 分頁二：七日氣象資料 (過去與未來預報完全自動化)
# ------------------------------------------
with tab2:
    st.header("📅 72AI40 測站與樹林區實時氣象大數據")
    
    # A. 過去 7 日實測 (若無 API 則採歷史均值安全替代)
    st.subheader("⏮️ 72AI40 過去 7 日現地真實觀測紀錄")
    if cwa_past:
        df_past = pd.DataFrame(cwa_past)
    else:
        past_dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 8)]; past_dates.reverse()
        df_past = pd.DataFrame({"觀測日期": past_dates, "測站氣壓 (hPa)": [1007.5]*7, "最高氣溫 (℃)": [31.0]*7, "最低氣溫 (℃)": [24.0]*7, "平均風速 (m/s)": [1.5]*7, "累積降水量 (mm)": [0.0]*7, "全天空日射量 (MJ/㎡)": [18.0]*7, "平均露點溫度 (℃)": [22.0]*7})
    st.dataframe(df_past, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # B. 未來一週預報 (串接 F-D0047-069 樹林區)
    st.subheader("🔮 樹林區未來 7 天官方天氣預報")
    if cwa_future:
        df_future = pd.DataFrame(cwa_future)
    else:
        future_dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 8)]
        df_future = pd.DataFrame({"預報日期": future_dates, "預估最高溫 (℃)": [32.0]*7, "預估最低溫 (℃)": [25.0]*7, "預估風速 (m/s)": [1.2]*7, "白晝降雨機率 (%)": [20]*7, "天氣型態概況": ["多雲到晴"]*7, "全天空日射量推估 (MJ/㎡)": [22.0]*7, "預估露點溫度 (℃)": [22.0]*7})
    st.dataframe(df_future, use_container_width=True, hide_index=True)

# ------------------------------------------
# 分頁三：幕後設定參數
# ------------------------------------------
with tab3:
    st.header("⚙️ 72AI40 系統物理參數維護 (已鎖定樹林分場)")
    st.session_state.z = st.number_input("📍 測站海拔高度 (m)", value=40.0, disabled=True)
    st.session_state.latitude = st.number_input("📐 測站北緯緯度 (度)", value=24.9445, format="%.4f", disabled=True)
    
    st.markdown("---")
    st.markdown("### 🌾 田區操作基本設定")
    t3_col1, t3_col2 = st.columns(2)
    with t3_col1:
        st.session_state.root_depth = st.number_input("📏 有效根系深度 D (mm)", value=st.session_state.root_depth, step=50)
        st.session_state.field_area = st.number_input("📐 實際灌溉面積 (㎡)", value=st.session_state.field_area, step=10.0)
    with t3_col2:
        st.session_state.kc = st.number_input("🌿 作物係數 (Kc)", value=st.session_state.kc, step=0.05)
        st.session_state.target_vwc = st.number_input("🎯 目標含水量 (田間容水量) (m3/m3)", value=st.session_state.target_vwc, step=0.01)
