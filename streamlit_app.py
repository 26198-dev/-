import streamlit as st
import numpy as np
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="비타민 C 항산화 반응 시뮬레이션",
    page_icon="🍎",
    layout="wide"
)

st.title("🍎 비타민 C 항산화 효과 및 과일 갈변 억제 시뮬레이션")
st.markdown("비타민 C(아스코르브산)의 농도와 공기 노출 시간에 따른 갈변 방지 효과(산화-환원 반응)를 탐구합니다.")

# -----------------------------------------------------------------------------
# 2. 화학 반응 모델 상수 및 계산 함수
# -----------------------------------------------------------------------------
# 비타민 C 100 mg/dL당 약 10분의 갈변 지연 효과 (분당 10 mg/dL 소비)
CONSUMPTION_RATE = 10.0  # mg/dL/min
BROWNING_K = 0.08        # 비타민 C 소진 후 갈변 반응 속도 상수 (1차 반응)

def calculate_mechanics(init_c, t):
    """
    입력값 예외 처리 및 검증을 포함한 갈변 진행도 및 잔여 비타민 C 계산 함수
    """
    # [예외 처리] 입력값 검증 (음수 및 NaN 체크)
    if init_c is None or t is None or init_c < 0 or t < 0:
        st.error("⚠️ 입력값은 0 이상의 숫자여야 합니다.")
        return 0.0, 0.0, 0.0

    # 비타민 C 소진 시간 (갈변 지연 시간)
    delay_time = init_c / CONSUMPTION_RATE if CONSUMPTION_RATE > 0 else 0.0

    if t <= delay_time:
        # 비타민 C가 남아있는 동안: 갈변 억제 (0%), 비타민 C 선형 감소
        remaining_vit_c = init_c - (CONSUMPTION_RATE * t)
        browning_percent = 0.0
    else:
        # 비타민 C 소진 후: 갈변 진행 (1차 반응 모델)
        remaining_vit_c = 0.0
        active_time = t - delay_time
        browning_percent = (1 - np.exp(-BROWNING_K * active_time)) * 100.0

    # [이론적 범위 검증 (Validation)]
    remaining_vit_c = max(0.0, min(float(init_c), float(remaining_vit_c)))
    browning_percent = max(0.0, min(100.0, float(browning_percent)))

    return remaining_vit_c, browning_percent, delay_time

def get_apple_rgb(browning_percent):
    """
    갈변율(0~100%)에 따른 과육 RGB 색상 보정
    신선한 과육 (255, 238, 204) -> 갈변된 과육 (120, 66, 18)
    """
    factor = browning_percent / 100.0
    r = int(255 - (255 - 120) * factor)
    g = int(238 - (238 - 66) * factor)
    b = int(204 - (204 - 18) * factor)
    return r, g, b

# -----------------------------------------------------------------------------
# 3. 사이드바 (사용자 입력 컨트롤)
# -----------------------------------------------------------------------------
st.sidebar.header("🎛️ 변수 설정")

vit_c_init = st.sidebar.slider(
    "초기 비타민 C 농도 (mg/dL)",
    min_value=0,
    max_value=500,
    value=100,
    step=5,
    help="0 ~ 500 mg/dL 범위 설정"
)

time_current = st.sidebar.slider(
    "공기 노출 시간 (min)",
    min_value=0,
    max_value=60,
    value=0,
    step=1,
    help="0 ~ 60분 범위 설정"
)

# -----------------------------------------------------------------------------
# 4. 데이터 계산 및 메인 화면 레이아웃
# -----------------------------------------------------------------------------
rem_c, browning_pct, delay_t = calculate_mechanics(vit_c_init, time_current)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 현재 상태 수치")
    
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("현재 갈변율", f"{browning_pct:.1f} %")
    m_col2.metric("잔여 비타민 C", f"{rem_c:.1f} mg/dL")
    m_col3.metric("갈변 지연 시간", f"{delay_t:.1f} min")

    st.subheader("🍎 사과 표면 색상 변화")
    r, g, b = get_apple_rgb(browning_pct)
    
    # HTML/CSS를 이용한 사과 표면 색상 시각화
    apple_html = f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px;">
        <div style="
            width: 140px;
            height: 140px;
            border-radius: 50%;
            background-color: rgb({r}, {g}, {b});
            box-shadow: inset -10px -10px 20px rgba(0,0,0,0.2);
            position: relative;
            transition: background-color 0.3s ease;
        ">
            <div style="
                position: absolute;
                top: -8px;
                left: 50%;
                transform: translateX(-50%);
                width: 8px;
                height: 12px;
                background-color: #5c4033;
                border-radius: 3px;
            "></div>
        </div>
        <p style="margin-top: 10px; font-weight: bold; color: #555;">
            RGB Color: ({r}, {g}, {b})
        </p>
    </div>
    """
    st.markdown(apple_html, unsafe_allow_html=True)

with col2:
    st.subheader("📈 시간에 따른 반응 변화 그래프")

    # 0 ~ 60분 연속 데이터 생성
    t_range = np.linspace(0, 60, 61)
    results = [calculate_mechanics(vit_c_init, t) for t in t_range]
    
    vit_c_data = [res[0] for res in results]
    browning_data = [res[1] for res in results]

    # Plotly 2축 그래프 생성
    fig = go.Figure()

    # 갈변 진행도 Trace (왼쪽 Y축)
    fig.add_trace(
        go.Scatter(
            x=t_range,
            y=browning_data,
            name="갈변 진행도 (%)",
            line=dict(color="#8B4513", width=3),
            yaxis="y1"
        )
    )

    # 잔여 비타민 C Trace (오른쪽 Y축)
    fig.add_trace(
        go.Scatter(
            x=t_range,
            y=vit_c_data,
            name="잔여 비타민 C (mg/dL)",
            line=dict(color="#27ae60", width=2, dash="dash"),
            yaxis="y2"
        )
    )

    # 현재 설정 시간 수직선 표시
    fig.add_vline(
        x=time_current,
        line_width=1.5,
        line_dash="dot",
        line_color="red",
        annotation_text=f"현재: {time_current} min",
        annotation_position="top left"
    )

    # 레이아웃 및 축 단위 설정
    fig.update_layout(
        xaxis=dict(title="노출 시간 (min)"),
        yaxis=dict(
            title="갈변율 (%)",
            range=[0, 100],
            titlefont=dict(color="#8B4513"),
            tickfont=dict(color="#8B4513")
        ),
        yaxis2=dict(
            title="잔여 비타민 C (mg/dL)",
            range=[0, 500],
            overlaying="y",
            side="right",
            titlefont=dict(color="#27ae60"),
            tickfont=dict(color="#27ae60")
        ),
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=20, r=20, t=30, b=20),
        height=380
    )

    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# 5. 화학 반응식 안내 박스
# -----------------------------------------------------------------------------
st.info("""
### 🧪 화학 반응 원리 (산화-환원 반응)
1. **폴리페놀 산화 (갈변 원인):** $\\text{Polyphenol} + \\text{O}_2 \\xrightarrow{\\text{PPO}} \\text{Quinone}$ (갈색 색소)
2. **비타민 C의 항산화 작용:** $\\text{Quinone} + \\text{Ascorbic Acid (C}_6\\text{H}_8\\text{O}_6\\text{)} \\rightarrow \\text{Polyphenol} + \\text{Dehydroascorbic Acid (C}_6\\text{H}_6\\text{O}_6\\text{)}$

*비타민 C가 스스로 산화되면서 퀴논을 다시 폴리페놀로 환원시켜, 비타민 C가 완전히 소진될 때까지 갈변 반응을 억제합니다.*
""")
