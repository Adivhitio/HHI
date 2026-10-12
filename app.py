import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- Конфигурация страницы ---
st.set_page_config(
    page_title="Системный аудит курса (Post-Flight Engine)",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 1. МОДЕЛЬ ДАННЫХ ВАЛИДНЫХ СРЕЗОВ (Синтетические срезы N >= 30)
# ==============================================================================
@st.cache_data
def load_systemic_data():
    # 1.1. Макро-показатели валидных срезов курса
    # Срез #1: Версия 1.0 (проблема "иллюзии доходимости" и разрыва на Модуле 2)
    # Срез #2: Версия 1.1 (после внедрения P0/P1 интервенций)
    slices_summary = [
        {
            "slice_id": "slice_1",
            "slice_name": "Срез #1 [Потоки 1–3, Версия 1.0]",
            "cohorts_range": "Потоки 1–3",
            "enrolled": 39,
            "finished": 30,
            "passed_atask": 17,
            "cr": 30 / 39,          # 76.9%
            "a_task": 17 / 30,      # 56.7% (Разрыв: высокий CR, но низкий A_task!)
            "r_market": 0.85,
            "hi_core": (30 / 39) * (17 / 30) * 0.85,  # 0.370 (Желтая зона)
            "status": "🟡 Зона риска"
        },
        {
            "slice_id": "slice_2",
            "slice_name": "Срез #2 [Потоки 4–6, Версия 1.1 — После правок]",
            "cohorts_range": "Потоки 4–6",
            "enrolled": 42,
            "finished": 33,
            "passed_atask": 27,
            "cr": 33 / 42,          # 78.6%
            "a_task": 27 / 33,      # 81.8% (Навык сформирован)
            "r_market": 0.90,
            "hi_core": (33 / 42) * (27 / 33) * 0.90,  # 0.579 (Зеленая зона)
            "status": "🟢 Здоровый"
        }
    ]
    df_slices = pd.DataFrame(slices_summary)

    # 1.2. Помодульные кумулятивные данные по срезам (Мезо-уровень)
    modules_slice_data = [
        # Модули Среза #1 (Версия 1.0)
        {"slice_id": "slice_1", "module_num": 1, "module_name": "M1: Архитектура и основы", "cum_cor": 0.95, "drop_rate": 0.05, "pct_rushed": 12.0, "pct_frag": 5.0, "pct_depleted": 8.0, "pct_loop_fail": 6.0},
        {"slice_id": "slice_1", "module_num": 2, "module_name": "M2: Базы данных и ORM", "cum_cor": 0.72, "drop_rate": 0.23, "pct_rushed": 22.0, "pct_frag": 28.0, "pct_depleted": 15.0, "pct_loop_fail": 31.0}, # Разрыв сценария!
        {"slice_id": "slice_1", "module_num": 3, "module_name": "M3: Интеграция API и Сервисы", "cum_cor": 0.62, "drop_rate": 0.10, "pct_rushed": 36.0, "pct_frag": 12.0, "pct_depleted": 22.0, "pct_loop_fail": 14.0}, # CLT перегруз!
        {"slice_id": "slice_1", "module_num": 4, "module_name": "M4: Боевой выпускной проект", "cum_cor": 0.56, "drop_rate": 0.06, "pct_rushed": 18.0, "pct_frag": 14.0, "pct_depleted": 32.0, "pct_loop_fail": 11.0},

        # Модули Среза #2 (Версия 1.1 — после методических интервенций)
        {"slice_id": "slice_2", "module_num": 1, "module_name": "M1: Архитектура и основы", "cum_cor": 0.97, "drop_rate": 0.03, "pct_rushed": 10.0, "pct_frag": 4.0, "pct_depleted": 6.0, "pct_loop_fail": 4.0},
        {"slice_id": "slice_2", "module_num": 2, "module_name": "M2: Базы данных и ORM", "cum_cor": 0.88, "drop_rate": 0.09, "pct_rushed": 16.0, "pct_frag": 7.0, "pct_depleted": 10.0, "pct_loop_fail": 8.0}, # Вылечено!
        {"slice_id": "slice_2", "module_num": 3, "module_name": "M3: Интеграция API и Сервисы", "cum_cor": 0.81, "drop_rate": 0.07, "pct_rushed": 18.0, "pct_frag": 8.0, "pct_depleted": 14.0, "pct_loop_fail": 9.0}, # Вылечено!
        {"slice_id": "slice_2", "module_num": 4, "module_name": "M4: Боевой выпускной проект", "cum_cor": 0.76, "drop_rate": 0.05, "pct_rushed": 15.0, "pct_frag": 9.0, "pct_depleted": 18.0, "pct_loop_fail": 8.0}
    ]
    df_modules = pd.DataFrame(modules_slice_data)
    return df_slices, df_modules

df_slices, df_modules = load_systemic_data()

# ==============================================================================
# 2. БОКОВАЯ ПАНЕЛЬ И УПРАВЛЕНИЕ СРЕЗАМИ
# ==============================================================================
st.sidebar.title("🏛️ Системный аудит")
st.sidebar.caption("Контур Post-Flight: оценка качества программы")

slice_options = df_slices["slice_name"].tolist()
selected_slice_name = st.sidebar.selectbox("Выберите анализируемый срез:", slice_options, index=0)
curr_slice = df_slices[df_slices["slice_name"] == selected_slice_name].iloc[0]

# Блок Data Gating
st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ Статус валидности (Data Gating)")
sample_size = curr_slice["enrolled"]

if sample_size >= 30:
    st.sidebar.success(f"**Выборка репрезентативна: N = {sample_size}**\n\nСрез объединяет {curr_slice['cohorts_range']}. Стратегическая аналитика разблокирована.")
else:
    st.sidebar.error(f"**Недостаточно данных: N = {sample_size} < 30**\n\nАналитика заблокирована для защиты от случайного шума.")

with st.sidebar.expander("📖 Легенда и стандарты здоровья"):
    st.markdown("""
    **Макро-стандарты курса ($HI_{\\text{core}}$):**
    * 🟢 $\\ge 0.500$ — Здоровый продукт.
    * 🟡 $0.250 - 0.499$ — Зона риска / доработка.
    * 🔴 $< 0.250$ — Кризис продукта.
    
    **Мезо-нормативы модуля:**
    * Отсев модуля: норма $\\le 10\\%$ (аномалия $> 15\\%$).
    * % Rushed: порог перегруза $> 25-30\\%$.
    * % Fragmented: порог хаоса $> 15-20\\%$.
    * % Loop Fail (3+ ошибок): порог $> 20\\%$.
    """)

# ==============================================================================
# 3. ОСНОВНОЙ ЭКРАН СИСТЕМНОГО ДАШБОРДА
# ==============================================================================
st.title("🎯 Системный аудит образовательной программы")
st.caption(f"Программа: **Fullstack Разработчик (Рескилл)** | Активный срез: **{curr_slice['slice_name']}** (N = {sample_size} зачисленных)")

tab1, tab2, tab3, tab4 = st.tabs([
    "🌐 Макро-аудит (Курс)",
    "🔬 Мезо-аудит (Модули)",
    "📋 Бэклог интервенций (P0–P3)",
    "⚖️ Валидация «До и После»"
])

# ==============================================================================
# ВКЛАДКА 1: МАКРО-АУДИТ КУРСА
# ==============================================================================
with tab1:
    st.subheader("1. Детекция здоровья программы (Макро-уровень)")
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Сквозной HI_core", f"{curr_slice['hi_core']:.3f}", delta=f"Статус: {curr_slice['status']}", delta_color="normal" if curr_slice['hi_core'] >= 0.5 else "inverse")
    m_col2.metric("Сквозной CR (Доходимость)", f"{curr_slice['cr']:.1%}", f"{curr_slice['finished']} из {curr_slice['enrolled']} чел.")
    m_col3.metric("A_task (Боевая задача)", f"{curr_slice['a_task']:.1%}", f"{curr_slice['passed_atask']} из {curr_slice['finished']} финалистов", help="Доля сдавших итоговый кейс без подсказок")
    m_col4.metric("R_market (Актуальность)", f"{curr_slice['r_market']:.2f}", "Ревизия рынка труда")

    st.markdown("---")
    
    col_g1, col_g2 = st.columns([1, 1])
    
    with col_g1:
        st.markdown("#### 🔍 Квадрант самостоятельности: CR vs A_task")
        fig_quad = go.Figure()
        
        # Отрисовка зон квадранта
        fig_quad.add_hrect(y0=0.6, y1=1.0, x0=0.6, x1=1.0, fillcolor="rgba(46, 204, 113, 0.15)", line_width=0, annotation_text="Здоровая зона выпуска")
        fig_quad.add_hrect(y0=0.0, y1=0.6, x0=0.6, x1=1.0, fillcolor="rgba(231, 76, 60, 0.15)", line_width=0, annotation_text="«ИЛЛЮЗИЯ ДОХОДИМОСТИ»")
        fig_quad.add_hrect(y0=0.0, y1=0.6, x0=0.0, x1=0.6, fillcolor="rgba(149, 165, 166, 0.15)", line_width=0, annotation_text="Системный кризис")
        
        fig_quad.add_trace(go.Scatter(
            x=[curr_slice["cr"]],
            y=[curr_slice["a_task"]],
            mode="markers+text",
            marker=dict(size=18, color="#2980B9" if curr_slice["hi_core"] >= 0.5 else "#E74C3C"),
            text=[f"{curr_slice['cohorts_range']}"],
            textposition="top center"
        ))
        
        fig_quad.update_layout(
            xaxis=dict(title="Доходимость (CR)", range=[0.3, 1.0], tickformat=".0%"),
            yaxis=dict(title="Сдача аутентичной задачи (A_task)", range=[0.3, 1.0], tickformat=".0%"),
            height=340,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_quad, use_container_width=True)

    with col_g2:
        st.markdown("#### 🩺 Диагностическое заключение по курсу")
        with st.container(border=True):
            if curr_slice["cr"] >= 0.70 and curr_slice["a_task"] < 0.60:
                st.error("🚨 **ПОДТВЕРЖДЕН СИСТЕМНЫЙ ДИАГНОЗ: «ИЛЛЮЗИЯ ДОХОДИМОСТИ»**")
                st.markdown("""
                * **В чем сбой:** Студенты успешно доходят до финала (доходимость **76.9%**), но срезаются на итоговом кейсе без помощи кураторов (**всего 56.7% сдачи**).
                * **Методическая первопричина:** На протяжении курса менторы давали прямые подсказки, а тесты проверяли память. Навык самостоятельного переноса не выработан.
                * **Управленческое решение:** Приоритет **P1** — реструктуризация промежуточной практики.
                """)
            elif curr_slice["hi_core"] >= 0.50:
                st.success("🟢 **ПРОГРАММА ЗДОРОВА И ЭФФЕКТИВНА**")
                st.markdown("""
                * Сквозной выход специалистов стабилен (**CR 78.6%**, **A_task 81.8%**).
                * Продукт подтверждает образовательное обещание и готов к расширению маркетингового набора.
                """)
            else:
                st.warning("🟡 **ТРЕБУЕТСЯ ПЛАНОВАЯ КОРРЕКЦИЯ**")

# ==============================================================================
# ВКЛАДКА 2: МЕЗО-АУДИТ МОДУЛЕЙ
# ==============================================================================
with tab2:
    st.subheader(f"2. Локализация поломок по сценарию программы ({curr_slice['slice_name']})")
    
    slice_mods = df_modules[df_modules["slice_id"] == curr_slice["slice_id"]].sort_values("module_num")
    
    col_d1, col_d2 = st.columns([1, 1])
    
    with col_d1:
        st.markdown("#### 📉 Карта отсева по воронке (Drop-off Map среза)")
        fig_drop = px.bar(
            slice_mods,
            x="module_name",
            y="cum_cor",
            text=[f"{v:.0%}" for v in slice_mods["cum_cor"]],
            color="drop_rate",
            color_continuous_scale="Reds",
            labels={"cum_cor": "Кумулятивное удержание", "module_name": "Модуль", "drop_rate": "Отвал на шаге"}
        )
        fig_drop.add_hline(y=0.70, line_dash="dot", line_color="gray", annotation_text="Нормативный коридор выпуска")
        fig_drop.update_layout(yaxis=dict(range=[0, 1.15], tickformat=".0%"), height=320, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_drop, use_container_width=True)

    with col_d2:
        st.markdown("#### 🚨 Сводный профиль среды модулей (Кумулятивный срез)")
        display_m = slice_mods[["module_name", "drop_rate", "pct_rushed", "pct_frag", "pct_loop_fail"]].copy()
        display_m.columns = ["Модуль", "Отвал шага", "% Спешат (Pacing)", "% Хаос (Cohesion)", "% Петли (3+ ошибок)"]
        
        st.dataframe(
            display_m.set_index("Модуль").style.format({
                "Отвал шага": "{:.1%}",
                "% Спешат (Pacing)": "{:.1f}%",
                "% Хаос (Cohesion)": "{:.1f}%",
                "% Петли (3+ ошибок)": "{:.1f}%"
            }).applymap(lambda v: "background-color: #FADBD8" if isinstance(v, (int, float)) and v > 20 else ""),
            use_container_width=True
        )
        st.caption("Красным подсвечены значения, превышающие нормативные пороги LXD-модели (отвал > 15%, метрики > 20%).")

    st.markdown("---")
    
    # LXD-рентген конкретного модуля
    st.markdown("#### 🔬 LXD-Рентген выбранного модуля")
    sel_mod_name = st.selectbox("Выберите модуль для глубокого анализа:", slice_mods["module_name"].tolist(), index=1)
    sel_mod_row = slice_mods[slice_mods["module_name"] == sel_mod_name].iloc[0]
    
    rx_col1, rx_col2 = st.columns([1, 2])
    
    with rx_col1:
        with st.container(border=True):
            st.metric("Отсев на модуле", f"{sel_mod_row['drop_rate']:.1%}", help="Норма: <= 10%")
            st.metric("Разрыв связности (% Frag)", f"{sel_mod_row['pct_frag']:.1f}%", help="Порог: > 15-20%")
            st.metric("Студенты в тупике (3+ ошибок)", f"{sel_mod_row['pct_loop_fail']:.1f}%", help="Порог: > 20%")
    
    with rx_col2:
        with st.container(border=True):
            if sel_mod_row["pct_frag"] >= 20.0 and sel_mod_row["pct_loop_fail"] >= 20.0:
                st.error(f"🚨 **ДИАГНОЗ ПО {sel_mod_name}: РАЗРЫВ СЦЕНАРИЯ И ПОТЕРЯ КОНТРОЛЯ**")
                st.markdown("""
                * **Методический сбой:** Теория оторвана от ТЗ практики. Студенты не понимают логику решения и массово впадают в ступор (31% студентов уперлись в $\ge 3$ ошибок подряд).
                * **Психологический эффект:** Срабатывает порог смены атрибуции («я не технарь»), что вызвало системный отвал 23% потока.
                * **Интервенция (P1):** Требуется синхронизация лекции и практики, внедрение стартового шаблона и ступенчатых подсказок (scaffolding).
                """)
            elif sel_mod_row["pct_rushed"] >= 30.0:
                st.warning(f"⚠️ **ДИАГНОЗ ПО {sel_mod_name}: ХРОНИЧЕСКАЯ ПОСТОРОННЯЯ НАГРУЗКА (CLT OVERLOAD)**")
                st.markdown("""
                * **Методический сбой:** Связность в норме, но объем лонгридов и рутинного кода превышает лимит времени взрослого учащегося.
                * **Интервенция (P2):** Декомпозиция практики на кванты по 15–20 мин, вынос второстепенной теории в факультатив.
                """)
            else:
                st.success(f"🟢 **{sel_mod_name}: Параметры среды в пределах нормы.**")

# ==============================================================================
# ВКЛАДКА 3: БЭКЛОГ АРХИТЕКТУРНЫХ ИНТЕРВЕНЦИЙ (P0–P3)
# ==============================================================================
with tab3:
    st.subheader("3. Доказательный бэклог доработок программы (Приоритеты P0–P3)")
    st.markdown("Задачи генерируются автоматически на основе выявленных на срезе системных дефектов:")
    
    # Логика формирования задач по активному срезу
    if curr_slice["slice_id"] == "slice_1":
        with st.container(border=True):
            st.error("### 🔴 ПРИОРИТЕТ P1: Реструктуризация промежуточной практики")
            st.markdown("""
            * **Объект:** Курс в целом (сквозная система аттестации).
            * **Обоснование:** Системный диагноз «Иллюзия доходимости» ($A_{\\text{task}} = 56.7\\%$ при $CR = 76.9\\%$).
            * **Архитектурная интервенция:**
                1. Внедрить на 5-й неделе независимый контрольный мини-кейс без подсказок кураторов.
                2. Запретить кураторам давать готовые куски кода в тикетах; перевести помощь на формат сократических наводящих вопросов.
            * **Ответственные:** Главный методист курса, Лид-эксперт направления.
            """)
            
        with st.container(border=True):
            st.error("### 🔴 ПРИОРИТЕТ P1: Устранение разрыва сценария на Модуле 2")
            st.markdown("""
            * **Объект:** Модуль 2 (Базы данных и ORM).
            * **Обоснование:** Системный отвал $23\\%$, % Fragmented = $28\\%$, петли 3+ ошибок у $31\\%$ студентов.
            * **Архитектурная интервенция:**
                1. Синхронизировать терминологию между лекцией по SQL и ТЗ домашнего задания.
                2. Разработать стартовый шаблон проекта для снятия барьера «чистого листа».
                3. Встроить адаптивную подсказку (scaffolding) на 2-й неудачной попытке отправки задания.
            * **Ответственные:** Методист модуля, Автор практических заданий.
            """)

        with st.container(border=True):
            st.warning("### 🟡 ПРИОРИТЕТ P2: Балансировка объема Модуля 3")
            st.markdown("""
            * **Объект:** Модуль 3 (Интеграция API и Сервисы).
            * **Обоснование:** Хронический перегруз хронометража (% Rushed = $36\\%$).
            * **Архитектурная интервенция:**
                1. Сократить хронометраж обзорных видео с 45 до 15 минут.
                2. Вынести справочные материалы по сторонним библиотекам в опциональные шпаргалки.
            * **Ответственные:** Контент-продюсер, Редактор.
            """)
    else:
        st.success("🎉 На активном срезе нет критических дефектов категории P0 и P1! Программа находится в зеленой зоне здоровья.")
        with st.container(border=True):
            st.info("### 🟢 ПРИОРИТЕТ P3: Плановая полировка и дифференциация (UX / Задачи со звездочкой)")
            st.markdown("""
            * **Объект:** Модули 1–4.
            * **Действие:** Добавить факультативные усложненные задачи для сильных студентов (профилактика скуки); точечные косметические правки формулировок.
            * **Ответственный:** Методист курса.
            """)

# ==============================================================================
# ВКЛАДКА 4: ВАЛИДАЦИЯ «ДО И ПОСЛЕ»
# ==============================================================================
with tab4:
    st.subheader("4. Доказательная валидация эффективности: Срез #1 vs Срез #2")
    st.markdown("""
    Здесь проверяется продуктовая гипотеза: **вылечили ли интервенции P1/P2 системные проблемы курса?**
    Сравниваются два полноценных валидных среза по 3 последовательных набора в каждом ($N_1 = 39$, $N_2 = 42$).
    """)
    
    s1 = df_slices[df_slices["slice_id"] == "slice_1"].iloc[0]
    s2 = df_slices[df_slices["slice_id"] == "slice_2"].iloc[0]
    
    comp_c1, comp_c2, comp_c3 = st.columns(3)
    comp_c1.metric("Сквозной HI_core", f"{s2['hi_core']:.3f}", delta=f"{s2['hi_core'] - s1['hi_core']:+.3f} (Выход в зеленую зону)")
    comp_c2.metric("Сдача боевой задачи (A_task)", f"{s2['a_task']:.1%}", delta=f"{(s2['a_task'] - s1['a_task'])*100:+.1f}% (Ликвидация разрыва)")
    comp_c3.metric("Доходимость (CR)", f"{s2['cr']:.1%}", delta=f"{(s2['cr'] - s1['cr'])*100:+.1f}%")
    
    st.markdown("---")
    
    # Помодульное сравнение До и После
    st.markdown("#### 🔬 Динамика дефектных модулей «До и После» интервенций")
    
    m_comp = df_modules.pivot(index="module_name", columns="slice_id", values=["drop_rate", "pct_frag", "pct_loop_fail"])
    
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        st.markdown("##### Отсев на проблемном Модуле 2 (Базы данных)")
        fig_bar_comp = go.Figure()
        fig_bar_comp.add_trace(go.Bar(name="Срез #1 (До правок, v1.0)", x=["M2: Базы данных"], y=[0.23], marker_color="#E74C3C", text=["23%"]))
        fig_bar_comp.add_trace(go.Bar(name="Срез #2 (После правок, v1.1)", x=["M2: Базы данных"], y=[0.09], marker_color="#2ECC71", text=["9%"]))
        fig_bar_comp.update_layout(yaxis=dict(tickformat=".0%", range=[0, 0.3]), height=280, barmode="group")
        st.plotly_chart(fig_bar_comp, use_container_width=True)
        st.caption("✅ Отсев на Модуле 2 сократился с 23% до 9% (в пределах здоровой нормы).")

    with col_v2:
        st.markdown("##### Доля студентов в тупике (3+ ошибок подряд)")
        fig_bar_err = go.Figure()
        fig_bar_err.add_trace(go.Bar(name="Срез #1 (До правок)", x=["M2: Базы данных"], y=[0.31], marker_color="#E74C3C", text=["31%"]))
        fig_bar_err.add_trace(go.Bar(name="Срез #2 (После правок)", x=["M2: Базы данных"], y=[0.08], marker_color="#2ECC71", text=["8%"]))
        fig_bar_err.update_layout(yaxis=dict(tickformat=".0%", range=[0, 0.35]), height=280, barmode="group")
        st.plotly_chart(fig_bar_err, use_container_width=True)
        st.caption("✅ Scaffolding и стартовый шаблон снизили долю тупиков с 31% до 8%.")

    with st.container(border=True):
        st.markdown("### 🎯 Итоговый вердикт по продуктовому релизу Версии 1.1")
        st.success("""
        **Гипотеза подтверждена:** Реструктуризация промежуточных мини-кейсов и устранение разрыва на Модуле 2 полностью ликвидировали «иллюзию доходимости».
        Показатель самостоятельной сдачи финального кейса ($A_{\\text{task}}$) вырос с **56.7% до 81.8%**, вернув продукт в зеленую зону ($HI_{\\text{core}} = 0.579$).
        """)
