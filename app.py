import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- Конфигурация страницы ---
st.set_page_config(
    page_title="Системный аудит курса (Post-Flight)",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 1. МОДЕЛЬ ДАННЫХ: ВАЛИДНЫЕ СРЕЗЫ, МОДУЛИ И CSI
# ==============================================================================
@st.cache_data
def load_audit_slices_data():
    # 1.1. Макро-показатели валидных срезов (N >= 30, пул из 3 потоков в каждом)
    slices_summary = [
        {
            "slice_id": "slice_1",
            "slice_name": "Срез #1 [Потоки 1–3, Версия 1.0]",
            "cohorts_range": "Потоки 1–3",
            "enrolled": 39,
            "finished": 30,
            "passed_atask": 16,
            "cr": 30 / 39,          # 76.9%
            "a_task": 16 / 30,      # 53.3% — Разрыв подтверждения навыка!
            "hi_core": (30 / 39) * (16 / 30),  # 0.410 (Желтая зона)
            "nps": 48,              # Лояльность умеренная
            "status": "🟡 Зона риска"
        },
        {
            "slice_id": "slice_2",
            "slice_name": "Срез #2 [Потоки 4–6, Версия 1.1 — Редизайн M2]",
            "cohorts_range": "Потоки 4–6",
            "enrolled": 42,
            "finished": 32,
            "passed_atask": 24,
            "cr": 32 / 42,          # 76.2%
            "a_task": 24 / 32,      # 75.0% — Сокращение разрыва
            "hi_core": (32 / 42) * (24 / 32),  # 0.571 (Зеленая зона)
            "nps": 58,
            "status": "🟢 Здоровый"
        },
        {
            "slice_id": "slice_3",
            "slice_name": "Срез #3 [Потоки 7–9, Версия 1.2 — Стабилизация]",
            "cohorts_range": "Потоки 7–9",
            "enrolled": 44,
            "finished": 35,
            "passed_atask": 29,
            "cr": 35 / 44,          # 79.5%
            "a_task": 29 / 35,      # 82.9% — Высокая автономность
            "hi_core": (35 / 44) * (29 / 35),  # 0.659 (Зеленая зона)
            "nps": 66,
            "status": "🟢 Здоровый"
        }
    ]
    df_slices = pd.DataFrame(slices_summary)

    # 1.2. Помодульные данные MHI и образовательной среды (Мезо-уровень)
    modules_data = [
        # Срез #1 (Версия 1.0)
        {"slice_id": "slice_1", "mod_num": 1, "mod_name": "M1: Введение и архитектура", "cum_cor": 0.95, "drop_rate": 0.05, "p_rushed": 12.0, "p_frag": 6.0, "p_depl": 8.0, "p_loop_fail": 5.0, "csi_tasks": 88.0},
        {"slice_id": "slice_1", "mod_num": 2, "mod_name": "M2: Базы данных и ORM", "cum_cor": 0.72, "drop_rate": 0.23, "p_rushed": 24.0, "p_frag": 28.0, "p_depl": 16.0, "p_loop_fail": 31.0, "csi_tasks": 66.0}, # Очаг разрыва!
        {"slice_id": "slice_1", "mod_num": 3, "mod_name": "M3: Интеграция API и Сервисы", "cum_cor": 0.64, "drop_rate": 0.08, "p_rushed": 34.0, "p_frag": 12.0, "p_depl": 22.0, "p_loop_fail": 15.0, "csi_tasks": 78.0}, # Перегруз объема
        {"slice_id": "slice_1", "mod_num": 4, "mod_name": "M4: Боевой выпускной проект", "cum_cor": 0.58, "drop_rate": 0.06, "p_rushed": 18.0, "p_frag": 15.0, "p_depl": 32.0, "p_loop_fail": 12.0, "csi_tasks": 74.0},

        # Срез #2 (Версия 1.1)
        {"slice_id": "slice_2", "mod_num": 1, "mod_name": "M1: Введение и архитектура", "cum_cor": 0.97, "drop_rate": 0.03, "p_rushed": 10.0, "p_frag": 5.0, "p_depl": 6.0, "p_loop_fail": 4.0, "csi_tasks": 90.0},
        {"slice_id": "slice_2", "mod_num": 2, "mod_name": "M2: Базы данных и ORM", "cum_cor": 0.88, "drop_rate": 0.09, "p_rushed": 16.0, "p_frag": 9.0, "p_depl": 11.0, "p_loop_fail": 9.0, "csi_tasks": 86.0}, # Исправлено!
        {"slice_id": "slice_2", "mod_num": 3, "mod_name": "M3: Интеграция API и Сервисы", "cum_cor": 0.81, "drop_rate": 0.07, "p_rushed": 20.0, "p_frag": 8.0, "p_depl": 15.0, "p_loop_fail": 8.0, "csi_tasks": 84.0},
        {"slice_id": "slice_2", "mod_num": 4, "mod_name": "M4: Боевой выпускной проект", "cum_cor": 0.76, "drop_rate": 0.05, "p_rushed": 14.0, "p_frag": 10.0, "p_depl": 21.0, "p_loop_fail": 7.0, "csi_tasks": 85.0},

        # Срез #3 (Версия 1.2)
        {"slice_id": "slice_3", "mod_num": 1, "mod_name": "M1: Введение и архитектура", "cum_cor": 0.98, "drop_rate": 0.02, "p_rushed": 8.0, "p_frag": 4.0, "p_depl": 5.0, "p_loop_fail": 3.0, "csi_tasks": 92.0},
        {"slice_id": "slice_3", "mod_num": 2, "mod_name": "M2: Базы данных и ORM", "cum_cor": 0.90, "drop_rate": 0.08, "p_rushed": 14.0, "p_frag": 7.0, "p_depl": 9.0, "p_loop_fail": 7.0, "csi_tasks": 89.0},
        {"slice_id": "slice_3", "mod_num": 3, "mod_name": "M3: Интеграция API и Сервисы", "cum_cor": 0.84, "drop_rate": 0.06, "p_rushed": 15.0, "p_frag": 6.0, "p_depl": 12.0, "p_loop_fail": 6.0, "csi_tasks": 88.0},
        {"slice_id": "slice_3", "mod_num": 4, "mod_name": "M4: Боевой выпускной проект", "cum_cor": 0.80, "drop_rate": 0.04, "p_rushed": 12.0, "p_frag": 7.0, "p_depl": 16.0, "p_loop_fail": 5.0, "csi_tasks": 90.0}
    ]
    df_modules = pd.DataFrame(modules_data)

    # 1.3. Сервисные метрики CSI (Вопросы 4–9, Top-2 Box %)
    csi_service_data = [
        # Срез 1
        {"slice_id": "slice_1", "mod_name": "M1: Введение", "v4_theory": 89, "v5_actual": 92, "v6_tasks": 88, "v7_expert": 94, "v8_sla": 91, "v9_care": 92},
        {"slice_id": "slice_1", "mod_name": "M2: Базы данных", "v4_theory": 73, "v5_actual": 88, "v6_tasks": 66, "v7_expert": 79, "v8_sla": 72, "v9_care": 83}, # Просадка заданий, лектора и SLA
        {"slice_id": "slice_1", "mod_name": "M3: API и Сервисы", "v4_theory": 76, "v5_actual": 85, "v6_tasks": 78, "v7_expert": 88, "v8_sla": 80, "v9_care": 85},
        {"slice_id": "slice_1", "mod_name": "M4: Боевой проект", "v4_theory": 82, "v5_actual": 90, "v6_tasks": 74, "v7_expert": 86, "v8_sla": 78, "v9_care": 88},

        # Срез 2
        {"slice_id": "slice_2", "mod_name": "M1: Введение", "v4_theory": 91, "v5_actual": 94, "v6_tasks": 90, "v7_expert": 95, "v8_sla": 92, "v9_care": 94},
        {"slice_id": "slice_2", "mod_name": "M2: Базы данных", "v4_theory": 86, "v5_actual": 91, "v6_tasks": 86, "v7_expert": 90, "v8_sla": 89, "v9_care": 91},
        {"slice_id": "slice_2", "mod_name": "M3: API и Сервисы", "v4_theory": 85, "v5_actual": 89, "v6_tasks": 84, "v7_expert": 91, "v8_sla": 88, "v9_care": 90},
        {"slice_id": "slice_2", "mod_name": "M4: Боевой проект", "v4_theory": 88, "v5_actual": 92, "v6_tasks": 85, "v7_expert": 92, "v8_sla": 86, "v9_care": 92},

        # Срез 3
        {"slice_id": "slice_3", "mod_name": "M1: Введение", "v4_theory": 93, "v5_actual": 95, "v6_tasks": 92, "v7_expert": 96, "v8_sla": 94, "v9_care": 95},
        {"slice_id": "slice_3", "mod_name": "M2: Базы данных", "v4_theory": 89, "v5_actual": 93, "v6_tasks": 89, "v7_expert": 92, "v8_sla": 91, "v9_care": 93},
        {"slice_id": "slice_3", "mod_name": "M3: API и Сервисы", "v4_theory": 88, "v5_actual": 91, "v6_tasks": 88, "v7_expert": 93, "v8_sla": 90, "v9_care": 92},
        {"slice_id": "slice_3", "mod_name": "M4: Боевой проект", "v4_theory": 90, "v5_actual": 94, "v6_tasks": 90, "v7_expert": 94, "v8_sla": 89, "v9_care": 94}
    ]
    df_csi = pd.DataFrame(csi_service_data)

    # 1.4. Качественный фидбек Вопроса №10 (с ролевыми LXD-тегами)
    feedbacks = [
        {"slice_id": "slice_1", "mod": "M2: Базы данных", "role": "Методисты", "tag": "lxd_no_control", "text": "В лекции разбирали простые SELECT, а в домашке потребовали сложный JOIN с агрегацией. Непонятно, за что браться."},
        {"slice_id": "slice_1", "mod": "M2: Базы данных", "role": "ОРЭ (Спикеры)", "tag": "lxd_friction", "text": "Приглашенный эксперт на вебинаре очень быстро пролистал слайды и почти не отвечал на вопросы из чата."},
        {"slice_id": "slice_1", "mod": "M2: Базы данных", "role": "Служба заботы", "tag": "lxd_friction", "text": "Ждал проверки первого задания почти двое суток. В итоге застрял и не мог приступить ко второй части."},
        {"slice_id": "slice_1", "mod": "M3: API и Сервисы", "role": "Методисты", "tag": "lxd_overload", "text": "Огромный лонгрид по REST API, физически не успевал прочитать за вечер после работы, приходилось пропускать."},
        {"slice_id": "slice_2", "mod": "M2: Базы данных", "role": "Методисты", "tag": "lxd_scaffolding", "text": "Новый стартовый шаблон и подсказки в тренажере очень помогли, разобрался со сложным запросом сам!"}
    ]
    df_fb = pd.DataFrame(feedbacks)

    return df_slices, df_modules, df_csi, df_fb

df_slices, df_modules, df_csi, df_fb = load_audit_slices_data()

# ==============================================================================
# 2. САЙДБАР: НАВИГАЦИЯ И DATA GATING
# ==============================================================================
st.sidebar.title("🏛️ Системный аудит")
st.sidebar.caption("Контур Post-Flight: оценка качества программы")

slice_names = df_slices["slice_name"].tolist()
selected_slice_name = st.sidebar.selectbox("Активный валидный срез:", slice_names, index=0)
curr_slice = df_slices[df_slices["slice_name"] == selected_slice_name].iloc[0]

# Блок Data Gating
st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ Статус репрезентативности")
n_enrolled = curr_slice["enrolled"]

if n_enrolled >= 30:
    st.sidebar.success(f"**Выборка валидна: N = {n_enrolled} (≥ 30)**\n\nСрез объединяет {curr_slice['cohorts_range']}. Стратегическая аналитика разблокирована.")
else:
    st.sidebar.warning(f"**Накопление данных: N = {n_enrolled} < 30**\n\nМалая когорта. Выводы защищены от случайного шума.")

with st.sidebar.expander("📖 Справочник стандартов здоровья"):
    st.markdown("""
    **Ядро здоровья курса ($HI_{\\text{core}} = CR \\times A_{\\text{task}}$):**
    * 🟢 **$\\ge 0.500$** — Здоровый продукт.
    * 🟡 **$0.300 - 0.499$** — Зона риска / доработка.
    * 🔴 **$< 0.300$** — Критическое состояние.

    **Мезо-нормативы модулей (MHI):**
    * Отсев модуля: норма $\\le 10\\%$ (внимание $> 15\\%$).
    * % Rushed (Спешка): норма $\\le 25\\%$.
    * % Fragmented (Хаос): норма $\\le 15\\%$.
    * % Loop Fail (3+ ошибок): норма $\\le 15\\%$.

    **Бенчмарки сервиса CSI (Top-2 Box):**
    * 🟢 **$\\ge 85-88\\%$** — стабильная среда.
    * 🟡 **$75-85\\%$** — зона точечных правок.
    * 🔴 **$< 75\\%$** — очаг острого трения.
    """)

# ==============================================================================
# 3. ОСНОВНОЙ ЭКРАН: 3 ВЫДЕЛЕННЫЕ ВКЛАДКИ
# ==============================================================================
st.title("🎯 Системный аудит образовательного продукта")
st.caption(f"Программа: **Fullstack Разработчик (Рескилл)** | Анализируется: **{curr_slice['slice_name']}** (N = {n_enrolled} зачисленных)")

tab1, tab2, tab3 = st.tabs([
    "🌐 Аудит курса (Макро-уровень)",
    "🔬 Аудит модулей (Мезо-уровень)",
    "🤝 Сервис и среда (CSI)"
])

# ==============================================================================
# ВКЛАДКА 1: АУДИТ КУРСА (МАКРО-УРОВЕНЬ)
# ==============================================================================
with tab1:
    st.subheader("1. Сквозные показатели здоровья программы")
    st.caption("Формула сквозного выхода подтвержденного навыка: $HI_{\\text{core}} = CR \\times A_{\\text{task}}$ (без субъективных экспертных оценок)")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Сквозной HI_core", f"{curr_slice['hi_core']:.3f}", f"Статус: {curr_slice['status']}", delta_color="normal" if curr_slice["hi_core"] >= 0.5 else "inverse")
    k2.metric("Доходимость (CR)", f"{curr_slice['cr']:.1%}", f"{curr_slice['finished']} из {curr_slice['enrolled']} чел.")
    k3.metric("Сдача боевой задачи (A_task)", f"{curr_slice['a_task']:.1%}", f"{curr_slice['passed_atask']} из {curr_slice['finished']} финалистов", help="Доля защитивших боевой кейс без подсказок")
    k4.metric("Итоговый NPS курса", f"{curr_slice['nps']}", f"Лояльность финалистов", help="Замеряется в итоговой анкете выпускников")

    st.markdown("---")

    # 1.1. Динамика срезов во времени
    st.markdown("#### 📈 Динамика показателей по валидным срезам во времени")
    col_t1, col_t2 = st.columns([3, 2])

    with col_t1:
        fig_trend = go.Figure()
        # Зоны здоровья фона
        fig_trend.add_hrect(y0=0.50, y1=1.00, fillcolor="rgba(46, 204, 113, 0.10)", line_width=0, annotation_text="Зеленая зона (≥ 0.50)", annotation_position="top left")
        fig_trend.add_hrect(y0=0.30, y1=0.50, fillcolor="rgba(241, 196, 15, 0.10)", line_width=0, annotation_text="Желтая зона (0.30–0.50)", annotation_position="top left")
        fig_trend.add_hrect(y0=0.00, y1=0.30, fillcolor="rgba(231, 76, 60, 0.10)", line_width=0, annotation_text="Красная зона (< 0.30)", annotation_position="top left")

        # Тренды компонентов
        fig_trend.add_trace(go.Scatter(x=df_slices["slice_name"], y=df_slices["hi_core"], name="Итоговый HI_core", mode="lines+markers+text", text=[f"{v:.3f}" for v in df_slices["hi_core"]], textposition="top center", line=dict(color="#2C3E50", width=4), marker=dict(size=10)))
        fig_trend.add_trace(go.Bar(x=df_slices["slice_name"], y=df_slices["cr"], name="CR (Доходимость)", marker_color="rgba(52, 152, 219, 0.65)"))
        fig_trend.add_trace(go.Bar(x=df_slices["slice_name"], y=df_slices["a_task"], name="A_task (Боевой кейс)", marker_color="rgba(46, 204, 113, 0.65)"))

        fig_trend.update_layout(
            barmode="group",
            yaxis=dict(title="Значение индекса / доли", range=[0, 1.05]),
            xaxis=dict(title="Валидный срез курса"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
            height=380,
            margin=dict(t=30, b=30, l=30, r=30)
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_t2:
        st.markdown("##### 🔍 Сопоставление: Доходимость vs Навык")
        gap = curr_slice["cr"] - curr_slice["a_task"]
        
        fig_gap = go.Figure()
        fig_gap.add_trace(go.Bar(
            y=["Метрики среза"],
            x=[curr_slice["cr"]],
            name="CR (Дошли до финала)",
            orientation="h",
            marker_color="#3498DB",
            text=[f"{curr_slice['cr']:.1%}"],
            textposition="auto"
        ))
        fig_gap.add_trace(go.Bar(
            y=["Метрики среза"],
            x=[curr_slice["a_task"]],
            name="A_task (Сдали задачу сами)",
            orientation="h",
            marker_color="#2ECC71" if gap <= 0.15 else "#E74C3C",
            text=[f"{curr_slice['a_task']:.1%}"],
            textposition="auto"
        ))
        fig_gap.update_layout(
            barmode="group",
            xaxis=dict(range=[0, 1.0], tickformat=".0%"),
            height=200,
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_gap, use_container_width=True)

        with st.container(border=True):
            if gap > 0.15:
                st.warning(f"⚠️ **Разрыв подтверждения навыка: Δ = {gap*100:.1f}%**")
                st.caption(f"До финала доходит {curr_slice['cr']:.0%}, но самостоятельно защитить задачу без помощи могут только {curr_slice['a_task']:.0%}. Есть вероятность накопления подсказок по ходу трека.")
            else:
                st.success(f"✅ **Сбалансированный навык: Δ = {gap*100:.1f}%**")
                st.caption("Доходимость и сдача боевого проекта синхронизированы. Те, кто доходит до финала, подтверждают автономный навык.")

    st.markdown("---")

    # 1.2. Мягкая исследовательская записка
    st.subheader("📋 Исследовательская записка для продуктовой команды")
    
    col_inf1, col_inf2 = st.columns(2)
    with col_inf1:
        with st.container(border=True):
            st.markdown("#### 🎯 Зоны внимания и сигналы в данных")
            if curr_slice["cr"] >= 0.70 and curr_slice["a_task"] < 0.60:
                st.markdown("""
                * **Зафиксирован разрыв самостоятельности:** Высокая доходимость (**76.9%**) сочетается с заметной просадкой сдачи итоговой задачи (**53.3%**).
                * **Контраст с NPS ({curr_slice['nps']} п.):** Студенты в целом довольны процессом обучения, однако на открытом кейсе испытывают трудности без прямого ведения за руку.
                * **Вектор:** Требуется проверить степень автономности студентов в промежуточной практике.
                """)
            elif curr_slice["hi_core"] >= 0.50:
                st.markdown(f"""
                * **Стабильный образовательный выход:** Продукт находится в зеленой зоне ($HI = {curr_slice['hi_core']:.3f}$).
                * **Баланс лояльности и практики:** Доходимость **{curr_slice['cr']:.1%}**, сдача боевой задачи **{curr_slice['a_task']:.1%}**, NPS **{curr_slice['nps']} п.**
                * **Вектор:** Программа готова к плановому масштабированию трафика.
                """)
            else:
                st.markdown("* Данные среза показывают локальные расхождения, требующие плановой калибровки нагрузки.")

    with col_inf2:
        with st.container(border=True):
            st.markdown("#### 💡 Гипотезы для проверки методистами и продюсером")
            if curr_slice["a_task"] < 0.65:
                st.markdown("""
                1. **Гипотеза о подсказках:** Промежуточные задания могли содержать избыточный объем прямых инструкций, из-за чего студент не тренировал поиск решения в условиях неопределенности.
                2. **Гипотеза о скачке сложности:** Требования финального кейса могли оказаться существенно выше типичных домашних заданий модулей.
                3. **Возможное направление работы:** Протестировать внедрение независимого контрольного мини-кейса без подсказок на экваторе курса.
                """)
            else:
                st.markdown("""
                1. **Поддержание планки:** Текущий баланс теории, промежуточных тестов и самостоятельной практики подтвердил свою устойчивость.
                2. **Дифференциация:** Можно рассмотреть добавление факультативных усложненных треков для опытных студентов.
                """)

# ==============================================================================
# ВКЛАДКА 2: АУДИТ МОДУЛЕЙ (МЕЗО-УРОВЕНЬ)
# ==============================================================================
with tab2:
    st.subheader(f"2. Панорама учебной среды по модулям программы ({curr_slice['slice_name']})")
    st.caption("Сквозной срез по всем модулям: локализация точек отсева и диагностических симптомов среды (MHI)")

    curr_mods = df_modules[df_modules["slice_id"] == curr_slice["slice_id"]].sort_values("mod_num")

    # 2.1. Единая тепловая таблица всех модулей сразу
    st.markdown("#### 📊 Сводный профиль сценария программы")
    
    table_view = curr_mods[["mod_name", "cum_cor", "drop_rate", "p_rushed", "p_frag", "p_depl", "p_loop_fail", "csi_tasks"]].copy()
    table_view.columns = [
        "Модуль курса", "Удержание (COR)", "Отсев шага", 
        "% Спешат (Pacing)", "% Хаос (Cohesion)", "% Истощены (Energy)", 
        "% Петли (3+ ошибок)", "CSI заданий (Top-2)"
    ]

    # Стилизация таблицы с защитой от различий в версиях Pandas
    styler = table_view.set_index("Модуль курса").style.format({
        "Удержание (COR)": "{:.1%}",
        "Отсев шага": "{:.1%}",
        "% Спешат (Pacing)": "{:.1f}%",
        "% Хаос (Cohesion)": "{:.1f}%",
        "% Истощены (Energy)": "{:.1f}%",
        "% Петли (3+ ошибок)": "{:.1f}%",
        "CSI заданий (Top-2)": "{:.0f}%"
    })

    def highlight_anomalies(val):
        if isinstance(val, (int, float)):
            if val > 20.0 and val <= 100.0:
                return "background-color: #FADBD8; color: #78281F; font-weight: bold;"
        return ""

    if hasattr(styler, "map"):
        styler = styler.map(highlight_anomalies, subset=["% Спешат (Pacing)", "% Хаос (Cohesion)", "% Истощены (Energy)", "% Петли (3+ ошибок)"])
    else:
        styler = styler.applymap(highlight_anomalies, subset=["% Спешат (Pacing)", "% Хаос (Cohesion)", "% Истощены (Energy)", "% Петли (3+ ошибок)"])

    st.dataframe(styler, use_container_width=True)
    st.caption("Красной заливкой выделены значения метрик среды, превышающие критический порог ( > 20% ).")

    st.markdown("---")

    # 2.2. Воронка отсева Drop-off Map
    col_d1, col_d2 = st.columns([1, 1])
    with col_d1:
        st.markdown("#### 📉 Карта удержания по воронке (Drop-off Map)")
        fig_drop = px.bar(
            curr_mods,
            x="mod_name",
            y="cum_cor",
            text=[f"{v:.0%}" for v in curr_mods["cum_cor"]],
            color="drop_rate",
            color_continuous_scale="Reds",
            labels={"cum_cor": "Кумулятивное удержание", "mod_name": "Модуль", "drop_rate": "Отсев на шаге"}
        )
        fig_drop.add_hline(y=0.70, line_dash="dot", line_color="gray", annotation_text="Нормативный коридор выпуска (70%)")
        fig_drop.update_layout(yaxis=dict(range=[0, 1.15], tickformat=".0%"), height=320, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_drop, use_container_width=True)

    with col_d2:
        st.markdown("#### 🚨 Психометрические очаги напряжения")
        fig_radar = go.Figure()
        for _, r in curr_mods.iterrows():
            fig_radar.add_trace(go.Bar(
                name=r["mod_name"],
                x=["Спешка (% Rushed)", "Хаос (% Frag)", "Истощение (% Depl)", "Петли ошибок (% Loop)"],
                y=[r["p_rushed"], r["p_frag"], r["p_depl"], r["p_loop_fail"]]
            ))
        fig_radar.update_layout(barmode="group", yaxis=dict(title="% студентов", range=[0, 40]), height=320, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("---")

    # 2.3. Аккордеон по проблемным модулям программы
    st.markdown("#### 🔍 Исследовательские карточки модулей (Симптомы и гипотезы LXD)")

    for _, mod_row in curr_mods.iterrows():
        is_troubled = (mod_row["drop_rate"] > 0.15) or (mod_row["p_frag"] > 20) or (mod_row["p_rushed"] > 25)
        icon = "🔴" if is_troubled else "🟢"
        
        with st.expander(f"{icon} **{mod_row['mod_name']}** (Отсев: {mod_row['drop_rate']:.1%}, Хаос: {mod_row['p_frag']:.0f}%, Петли: {mod_row['p_loop_fail']:.0f}%)", expanded=is_troubled):
            ec1, ec2 = st.columns([1, 2])
            with ec1:
                st.metric("Отсев на модуле", f"{mod_row['drop_rate']:.1%}", help="Норма: <= 10%")
                st.metric("Разрыв связности (Cohesion)", f"{mod_row['p_frag']:.1f}%", help="Норма: <= 15%")
                st.metric("Студенты в тупике (3+ ошибок)", f"{mod_row['p_loop_fail']:.1f}%", help="Норма: <= 15%")
            with ec2:
                if mod_row["p_frag"] > 20 and mod_row["p_loop_fail"] > 20:
                    st.error("⚠️ **Зона внимания: Признаки разрыва сценария и потери контроля**")
                    st.markdown("""
                    * **Что показывают метрики:** Высокая доля дезориентации сочетается с частыми сериями $\ge 3$ ошибок в практических шагах.
                    * **Вероятные факторы среды (LXD):**
                        1. Терминология в теории может отличаться от формулировок задания.
                        2. Отсутствие разобранного примера перед самостоятельной практикой (недостаток scaffolding).
                    * **Чек-лист для методиста и автора:**
                        - [ ] Проверить формулировку ТЗ на соответствие материалу лекции.
                        - [ ] Рассмотреть внедрение стартового шаблона проекта или адаптивной подсказки при второй ошибке.
                    """)
                elif mod_row["p_rushed"] > 25:
                    st.warning("⏱️ **Зона внимания: Признаки высокой плотности объема (CLT Overload)**")
                    st.markdown("""
                    * **Что показывают метрики:** Связность сохранена, но треть группы отмечает дефицит времени на освоение.
                    * **Вероятные факторы среды:** Избыточный хронометраж видео или рутинные технические действия в задании.
                    * **Чек-лист:**
                        - [ ] Оценить возможность выноса второстепенной теории в факультативные шпаргалки.
                        - [ ] Проверить хронометраж записей относительно запланированного бюджета времени.
                    """)
                else:
                    st.success("Параметры модуля находятся в пределах нормативных коридоров. Сценарий стабилен.")

# ==============================================================================
# ВКЛАДКА 3: СЕРВИС И СРЕДА (CSI)
# ==============================================================================
with tab3:
    st.subheader(f"3. Сервисный срез и качество среды: CSI ({curr_slice['slice_name']})")
    st.caption("Данные опроса «Пульс модуля» (Вопросы 4–10, методология Top-2 Box). Инструмент для ОРЭ, Службы заботы, Платформы и Методистов.")

    curr_csi = df_csi[df_csi["slice_id"] == curr_slice["slice_id"]]

    # 3.1. Верхние KPI карточки для смежных служб
    avg_content = (curr_csi["v4_theory"].mean() + curr_csi["v5_actual"].mean() + curr_csi["v6_tasks"].mean()) / 3
    avg_expert = curr_csi["v7_expert"].mean()
    avg_care = (curr_csi["v8_sla"].mean() + curr_csi["v9_care"].mean()) / 2

    c_col1, c_col2, c_col3 = st.columns(3)
    c_col1.metric("Контент и задания (В4–6)", f"{avg_content:.1f}%", "Методисты и авторы", help="Средний Top-2 Box по теории, актуальности и ДЗ")
    c_col2.metric("Эксперты и спикеры (В7)", f"{avg_expert:.1f}%", "Отдел работы с экспертами", help="Средний Top-2 Box по преподавателям модуля")
    c_col3.metric("Команда заботы (В8–9)", f"{avg_care:.1f}%", "Служба заботы / Сопровождение", help="Средний Top-2 Box по скорости (SLA) и эмпатии кураторов")

    st.markdown("---")

    # 3.2. Детальная матрица CSI по вопросам 4–9
    st.markdown("#### 📋 Детальные рейтинги среды по модулям (Top-2 Box %)")
    
    display_csi = curr_csi.copy()
    display_csi.columns = ["slice_id", "Модуль", "В4: Теория", "В5: Свежесть", "В6: Задания", "В7: Спикеры (ОРЭ)", "В8: SLA (Забота)", "В9: Эмпатия"]
    
    csi_styler = display_csi.drop(columns=["slice_id"]).set_index("Модуль").style.format("{:.0f}%")

    def highlight_csi(val):
        if isinstance(val, (int, float)):
            if val < 75.0:
                return "background-color: #FADBD8; color: #78281F; font-weight: bold;" # Критический очаг
            elif val < 85.0:
                return "background-color: #FCF3CF; color: #7D6608;" # Зона внимания
        return ""

    if hasattr(csi_styler, "map"):
        csi_styler = csi_styler.map(highlight_csi)
    else:
        csi_styler = csi_styler.applymap(highlight_csi)

    st.dataframe(csi_styler, use_container_width=True)
    st.caption("Цветовые маркеры: 🔴 красный — Top-2 Box < 75% (острый очаг трения); 🟡 желтый — 75–84% (зона точечной калибровки).")

    st.markdown("---")

    # 3.3. Качественный фидбек Вопроса №10 (с ролевыми тегами)
    st.markdown("#### 💬 Качественная обратная связь (Вопрос №10: «Что стоит улучшить?»)")
    st.caption("Цитаты студентов с автоматической разметкой по модели LXD для профильных отделов")

    curr_fb = df_fb[df_fb["slice_id"] == curr_slice["slice_id"]]
    
    if not curr_fb.empty:
        col_fil1, col_fil2 = st.columns([1, 2])
        with col_fil1:
            sel_role = st.selectbox("Фильтр по получателю:", ["Все отделы"] + curr_fb["role"].unique().tolist())
        
        filtered_fb = curr_fb if sel_role == "Все отделы" else curr_fb[curr_fb["role"] == sel_role]
        
        for _, fb in filtered_fb.iterrows():
            with st.container(border=True):
                h1, h2, h3 = st.columns([2, 1, 1])
                h1.markdown(f"**{fb['mod']}**")
                h2.caption(f"Адресат: `{fb['role']}`")
                h3.caption(f"Тег: `#{fb['tag']}`")
                st.markdown(f"> *«{fb['text']}»*")
    else:
        st.info("По данному срезу нет зафиксированных критических замечаний в открытом фидбеке.")
