import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# =====================================================================
# КОНФИГУРАЦИЯ СТРАНИЦЫ И СТИЛИ
# =====================================================================
st.set_page_config(
    page_title="Система метрик v1.0 — Системный контур",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
    .kpi-card {
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 10px;
        border: 1px solid #e0e0e0;
        background-color: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .kpi-title { font-size: 0.9rem; color: #555; font-weight: 600; margin-bottom: 4px; }
    .kpi-value { font-size: 1.75rem; font-weight: 700; margin-bottom: 4px; color: #111; }
    .kpi-sub { font-size: 0.82rem; color: #666; margin-bottom: 6px; }
    .kpi-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .bg-green { background-color: #e6f4ea; color: #137333; border-left: 5px solid #34a853; }
    .bg-yellow { background-color: #fef7e0; color: #b06000; border-left: 5px solid #fbbc04; }
    .bg-red { background-color: #fce8e6; color: #c5221f; border-left: 5px solid #ea4335; }
    .bg-grey { background-color: #f1f3f4; color: #5f6368; border-left: 5px solid #9aa0a6; }
    .note-box {
        border-radius: 8px;
        padding: 16px;
        background-color: #f8f9fa;
        border: 1px solid #dadce0;
        height: 100%;
    }
    .comment-card {
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        background-color: #ffffff;
        border-left: 4px solid #4A90E2;
        border-top: 1px solid #eaeaea;
        border-right: 1px solid #eaeaea;
        border-bottom: 1px solid #eaeaea;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# ДАННЫЕ СРЕЗОВ (СИНТЕТИЧЕСКИЙ НАБОР ДЛЯ ПРОВЕРКИ ВСЕХ СЦЕНАРИЕВ ТЗ)
# =====================================================================
@st.cache_data
def get_slices_data():
    return {
        "Срез 1 [Потоки 1–3, v1.0]": {
            "id": "Срез 1 (v1.0)",
            "version": "v1.0",
            "enrolled": 45,
            "finished": 31,
            "attempted_task": 23,
            "passed_task": 16,
            "nps": 64,
            "nps_respondents": 22,
            "anomaly_cohort": None,
            "u_resp": 38,
            # Двухшаговые агрегаты Top2_Unique(q) по уникальным респондентам U_resp
            "top2_unique": {"q4": 81.5, "q5": 84.0, "q6": 71.0, "q7": 89.5, "q8": 78.0, "q9": 91.0},
            "modules": [
                {
                    "num": 1, "name": "М1: Введение и архитектура",
                    "started": 45, "paused": 1, "passed": 41, "lagging": 1,
                    "dropped_official": 1, "dropped_inactive": 1,
                    "mhi_resp": 40,
                    "rushed_cnt": 5, "slow_cnt": 9, "frag_cnt": 3, "depl_cnt": 2,
                    "loop_fail_users": 3, "cohort_outlier": False,
                    "csi_top2": {"q4": 90.0, "q5": 92.5, "q6": 87.5, "q7": 92.5, "q8": 90.0, "q9": 95.0},
                    "csi_bot2": {"q4": 2.5, "q5": 2.5, "q6": 5.0, "q7": 2.5, "q8": 5.0, "q9": 0.0},
                    "comments": [
                        "Для продолжающих специалистов первые уроки показались слишком простыми, хотелось бы сдать экстерном."
                    ]
                },
                {
                    "num": 2, "name": "М2: Проектирование БД и SQL",
                    "started": 42, "paused": 2, "passed": 31, "lagging": 2,
                    "dropped_official": 3, "dropped_inactive": 4,
                    "mhi_resp": 30,
                    "rushed_cnt": 7, "slow_cnt": 2, "frag_cnt": 8, "depl_cnt": 5,
                    "loop_fail_users": 10, "cohort_outlier": False,
                    "csi_top2": {"q4": 76.7, "q5": 83.3, "q6": 66.7, "q7": 90.0, "q8": 83.3, "q9": 90.0},
                    "csi_bot2": {"q4": 10.0, "q5": 6.7, "q6": 20.0, "q7": 3.3, "q8": 6.7, "q9": 3.3},
                    "comments": [
                        "В домашнем задании используются конструкции JOIN и оконные функции, которых не было в лекции!",
                        "Автотест в тренажере на 3-м шаге падает без понятного описания ошибки, просидел два вечера."
                    ]
                },
                {
                    "num": 3, "name": "М3: Асинхронность и интеграция API",
                    "started": 33, "paused": 0, "passed": 26, "lagging": 3,
                    "dropped_official": 1, "dropped_inactive": 3,
                    "mhi_resp": 25,
                    "rushed_cnt": 9, "slow_cnt": 1, "frag_cnt": 3, "depl_cnt": 6,
                    "loop_fail_users": 4, "cohort_outlier": True,
                    "csi_top2": {"q4": 80.0, "q5": 84.0, "q6": 76.0, "q7": 88.0, "q8": 72.0, "q9": 88.0},
                    "csi_bot2": {"q4": 8.0, "q5": 4.0, "q6": 12.0, "q7": 4.0, "q8": 16.0, "q9": 4.0},
                    "comments": [
                        "Очень большой объем видео (почти 5 часов) и рутинной верстки шаблонов, физически не успеваю после работы.",
                        "Проверку ДЗ ждал почти трое суток, хотя куратор ответил очень вежливо и подробно."
                    ]
                },
                {
                    "num": 4, "name": "М4: Деплой и подготовка к диплому",
                    "started": 31, "paused": 0, "passed": 28, "lagging": 1,
                    "dropped_official": 1, "dropped_inactive": 1,
                    "mhi_resp": 27,
                    "rushed_cnt": 6, "slow_cnt": 1, "frag_cnt": 3, "depl_cnt": 8,
                    "loop_fail_users": 3, "cohort_outlier": False,
                    "csi_top2": {"q4": 85.2, "q5": 88.9, "q6": 81.5, "q7": 88.9, "q8": 85.2, "q9": 92.6},
                    "csi_bot2": {"q4": 3.7, "q5": 3.7, "q6": 7.4, "q7": 3.7, "q8": 7.4, "q9": 3.7},
                    "comments": [
                        "К четвертому модулю накопилась сильная усталость, перед защитой диплома не хватает буферной недели."
                    ]
                },
            ]
        },
        "Срез 2 [Потоки 4–6, v1.1]": {
            "id": "Срез 2 (v1.1)",
            "version": "v1.1",
            "enrolled": 48,
            "finished": 33,
            "attempted_task": 29,
            "passed_task": 23,
            "nps": 48,
            "nps_respondents": 24,
            "anomaly_cohort": "Потока #5",
            "u_resp": 42,
            "top2_unique": {"q4": 86.0, "q5": 88.0, "q6": 82.0, "q7": 84.5, "q8": 88.5, "q9": 90.0},
            "modules": [
                {
                    "num": 1, "name": "М1: Введение и архитектура",
                    "started": 48, "paused": 1, "passed": 44, "lagging": 1,
                    "dropped_official": 1, "dropped_inactive": 1,
                    "mhi_resp": 43,
                    "rushed_cnt": 5, "slow_cnt": 5, "frag_cnt": 3, "depl_cnt": 3,
                    "loop_fail_users": 3, "cohort_outlier": False,
                    "csi_top2": {"q4": 90.7, "q5": 93.0, "q6": 88.4, "q7": 93.0, "q8": 90.7, "q9": 93.0},
                    "csi_bot2": {"q4": 2.3, "q5": 2.3, "q6": 4.7, "q7": 2.3, "q8": 4.7, "q9": 2.3},
                    "comments": []
                },
                {
                    "num": 2, "name": "М2: Проектирование БД и SQL",
                    "started": 45, "paused": 1, "passed": 38, "lagging": 2,
                    "dropped_official": 2, "dropped_inactive": 2,
                    "mhi_resp": 37,
                    "rushed_cnt": 6, "slow_cnt": 2, "frag_cnt": 4, "depl_cnt": 4,
                    "loop_fail_users": 5, "cohort_outlier": False,
                    "csi_top2": {"q4": 86.5, "q5": 89.2, "q6": 83.8, "q7": 75.7, "q8": 89.2, "q9": 89.2},
                    "csi_bot2": {"q4": 5.4, "q5": 2.7, "q6": 8.1, "q7": 16.2, "q8": 5.4, "q9": 5.4},
                    "comments": [
                        "Новый шаблон к ДЗ по SQL сильно помог, но приглашенный спикер на вебинаре в Потоке 5 путался в примерах."
                    ]
                },
                {
                    "num": 3, "name": "М3: Асинхронность и интеграция API",
                    "started": 40, "paused": 1, "passed": 33, "lagging": 2,
                    "dropped_official": 2, "dropped_inactive": 2,
                    "mhi_resp": 32,
                    "rushed_cnt": 9, "slow_cnt": 1, "frag_cnt": 3, "depl_cnt": 5,
                    "loop_fail_users": 4, "cohort_outlier": False,
                    "csi_top2": {"q4": 84.4, "q5": 87.5, "q6": 81.3, "q7": 87.5, "q8": 87.5, "q9": 90.6},
                    "csi_bot2": {"q4": 6.3, "q5": 3.1, "q6": 9.4, "q7": 6.3, "q8": 6.3, "q9": 3.1},
                    "comments": [
                        "Материала всё ещё многовато для одной недели, приходилось сидеть в выходные."
                    ]
                },
                {
                    "num": 4, "name": "М4: Деплой и подготовка к диплому",
                    "started": 35, "paused": 0, "passed": 29, "lagging": 1,
                    "dropped_official": 2, "dropped_inactive": 3,
                    "mhi_resp": 14,  # Демонстрация m < 15 (Серая зона MHI/CSI)
                    "rushed_cnt": 3, "slow_cnt": 1, "frag_cnt": 2, "depl_cnt": 3,
                    "loop_fail_users": 3, "cohort_outlier": False,
                    "csi_top2": {"q4": 85.7, "q5": 85.7, "q6": 78.6, "q7": 85.7, "q8": 85.7, "q9": 92.9},
                    "csi_bot2": {"q4": 7.1, "q5": 7.1, "q6": 7.1, "q7": 7.1, "q8": 7.1, "q9": 0.0},
                    "comments": []
                },
            ]
        },
        "Срез 3 [Потоки 7–9, v1.2]": {
            "id": "Срез 3 (v1.2)",
            "version": "v1.2",
            "enrolled": 52,
            "finished": 38,
            "attempted_task": 35,
            "passed_task": 31,
            "nps": 58,
            "nps_respondents": 28,
            "anomaly_cohort": None,
            "u_resp": 46,
            "top2_unique": {"q4": 89.2, "q5": 91.0, "q6": 87.5, "q7": 91.5, "q8": 92.0, "q9": 94.0},
            "modules": [
                {
                    "num": 1, "name": "М1: Введение и архитектура",
                    "started": 52, "paused": 1, "passed": 48, "lagging": 1,
                    "dropped_official": 1, "dropped_inactive": 1,
                    "mhi_resp": 47,
                    "rushed_cnt": 5, "slow_cnt": 4, "frag_cnt": 3, "depl_cnt": 3,
                    "loop_fail_users": 3, "cohort_outlier": False,
                    "csi_top2": {"q4": 91.5, "q5": 93.6, "q6": 89.4, "q7": 93.6, "q8": 91.5, "q9": 95.7},
                    "csi_bot2": {"q4": 2.1, "q5": 2.1, "q6": 4.3, "q7": 2.1, "q8": 4.3, "q9": 0.0},
                    "comments": ["Отличный старт, трек экстерната для опытных сэкономил кучу времени!"]
                },
                {
                    "num": 2, "name": "М2: Проектирование БД и SQL",
                    "started": 49, "paused": 1, "passed": 43, "lagging": 2,
                    "dropped_official": 1, "dropped_inactive": 2,
                    "mhi_resp": 42,
                    "rushed_cnt": 7, "slow_cnt": 3, "frag_cnt": 4, "depl_cnt": 4,
                    "loop_fail_users": 4, "cohort_outlier": False,
                    "csi_top2": {"q4": 88.1, "q5": 90.5, "q6": 88.1, "q7": 90.5, "q8": 92.9, "q9": 92.9},
                    "csi_bot2": {"q4": 4.8, "q5": 2.4, "q6": 4.8, "q7": 4.8, "q8": 2.4, "q9": 2.4},
                    "comments": ["Разбор типового кейса перед ДЗ снял все вопросы по сложным запросам."]
                },
                {
                    "num": 3, "name": "М3: Асинхронность и интеграция API",
                    "started": 45, "paused": 1, "passed": 40, "lagging": 1,
                    "dropped_official": 1, "dropped_inactive": 2,
                    "mhi_resp": 39,
                    "rushed_cnt": 7, "slow_cnt": 2, "frag_cnt": 3, "depl_cnt": 5,
                    "loop_fail_users": 4, "cohort_outlier": False,
                    "csi_top2": {"q4": 89.7, "q5": 89.7, "q6": 87.2, "q7": 89.7, "q8": 92.3, "q9": 94.9},
                    "csi_bot2": {"q4": 2.6, "q5": 2.6, "q6": 5.1, "q7": 5.1, "q8": 2.6, "q9": 2.6},
                    "comments": []
                },
                {
                    "num": 4, "name": "М4: Деплой и подготовка к диплому",
                    "started": 40, "paused": 0, "passed": 38, "lagging": 0,
                    "dropped_official": 1, "dropped_inactive": 1,
                    "mhi_resp": 37,
                    "rushed_cnt": 6, "slow_cnt": 2, "frag_cnt": 3, "depl_cnt": 5,
                    "loop_fail_users": 3, "cohort_outlier": False,
                    "csi_top2": {"q4": 89.2, "q5": 91.9, "q6": 86.5, "q7": 91.9, "q8": 91.9, "q9": 94.6},
                    "csi_bot2": {"q4": 2.7, "q5": 2.7, "q6": 5.4, "q7": 2.7, "q8": 2.7, "q9": 0.0},
                    "comments": ["Все структурно и прозрачно, рубрикатор дипломного проекта понятен заранее."]
                },
            ]
        },
        "Срез 4 [Поток 10, v1.2 — в наборе]": {
            "id": "Срез 4 (набор)",
            "version": "v1.2",
            "enrolled": 18,  # Демонстрация правила Data Gating (Enrolled < 30)
            "finished": 14,
            "attempted_task": 12,
            "passed_task": 11,
            "nps": 60,
            "nps_respondents": 10,
            "anomaly_cohort": None,
            "u_resp": 15,
            "top2_unique": {"q4": 88.0, "q5": 90.0, "q6": 86.0, "q7": 90.0, "q8": 90.0, "q9": 92.0},
            "modules": []
        }
    }


slices_data = get_slices_data()


# =====================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ РАСЧЕТА И ДИАГНОСТИКИ (СТРОГО ПО ТЗ v16)
# =====================================================================
def render_kpi_card(title, value_str, subtitle, status_label, color_class, extra_badge=""):
    badge_html = f'<div style="margin-top:4px;"><span class="kpi-badge">{extra_badge}</span></div>' if extra_badge else ""
    st.markdown(f"""
    <div class="kpi-card {color_class}">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value_str}</div>
        <div class="kpi-sub">{subtitle}</div>
        <span class="kpi-badge">{status_label}</span>
        {badge_html}
    </div>
    """, unsafe_allow_html=True)


def evaluate_macro_scenario(hi_core, cr_pct, a_task_pct, nps_val, nps_valid, no_show_pct, rubric_fail_pct, unconfirmed_pct):
    """Формирование автоматической исследовательской записки (Блок Г, п. 1.4 и 2.2 Части 1)"""
    task_fail_pct = 100.0 - a_task_pct

    # Фактическое описание для Колонки 1
    nps_fact = (
        f"Индекс лояльности выпускников NPS = **{nps_val}**."
        if nps_valid else
        "Индекс лояльности NPS: **⚪ Данных недостаточно** (менее 15 ответов или охват < 50%)."
    )
    facts_base = (
        f"- **Сквозной выход навыка ($HI_{{\\text{{core}}}}$):** `{hi_core:.3f}` ({hi_core*100:.1f}% от поступивших).\n"
        f"- **Доходимость до финала ($CR$):** `{cr_pct:.1f}%`.\n"
        f"- **Сдача боевой задачи ($A_{{\\text{{task}}}}$):** `{a_task_pct:.1f}%`.\n"
        f"- **Потери на финише (`Task_Fail_Rate`):** `{task_fail_pct:.1f}%` финалистов без подтвержденного результата "
        f"(не приступили к проекту `No_Show_Rate`: `{no_show_pct:.1f}%` | не прошли по рубрикатору `Rubric_Fail_Rate`: `{rubric_fail_pct:.1f}%`).\n"
        f"- **Доля «холостого выпуска» (`Unconfirmed_Share`):** `{unconfirmed_pct:.1f}%` от всех зачисленных.\n"
        f"- {nps_fact}"
    )

    if nps_valid:
        # Сценарий 1: Сбалансированный бенчмарк
        if hi_core >= 0.500 and cr_pct >= 65.0 and a_task_pct >= 75.0 and nps_val >= 50:
            col1 = (
                "**Сценарий 1. Сбалансированный бенчмарк**\n\n"
                "🟢 **Здоровый продукт:** высокий сквозной выход подтвержденных специалистов, "
                "удержание и удовлетворенность в целевой зоне.\n\n" + facts_base
            )
            col2 = (
                "**Действия:**\n"
                "1. Зафиксировать текущую версию программы как базовый эталон.\n"
                "2. Развивать трек задач повышенной сложности для сильных студентов."
            )
            return col1, col2

        # Сценарий 2: «Иллюзия доходимости» (при умеренной лояльности)
        if cr_pct >= 65.0 and a_task_pct < 60.0 and (35 <= nps_val <= 60):
            col1 = (
                "**Сценарий 2. «Иллюзия доходимости» (при умеренной лояльности)**\n\n"
                "🟡 **Разрыв подтверждения навыка:** студенты успешно проходят модули, но более 40% финалистов "
                "не имеют подтвержденного результата по итоговому кейсу (требуется разделить неучастие в защите и несдачу по критериям).\n\n"
                + facts_base
            )
            col2 = (
                "**Что проверить:**\n"
                "1. Соотношение `No_Show_Rate` и `Rubric_Fail_Rate`: люди не приступают к диплому из-за усталости или не проходят по баллам.\n"
                "2. Нет ли избыточных подсказок кураторов в промежуточных ДЗ («ведение за руку»).\n"
                "3. Соответствует ли сложность диплома предыдущим модулям."
            )
            return col1, col2

        # Сценарий 3: «Эмоциональная ловушка» (Забота вместо навыка)
        if cr_pct >= 65.0 and a_task_pct < 60.0 and nps_val > 60:
            col1 = (
                "**Сценарий 3. «Эмоциональная ловушка» (Забота вместо навыка)**\n\n"
                "🟡 **Атмосфера без подтверждения результата:** студенты восторженно оценивают спикеров и комьюнити, "
                "но более 40% финалистов выпускаются без защищенного проекта (проверить соотношение не приступивших к диплому и не прошедших рубрикатор).\n\n"
                + facts_base
            )
            col2 = (
                "**Что проверить:**\n"
                "1. Не носит ли приемка промежуточных заданий завышенно-лояльный характер («зачет за старание»).\n"
                "2. Калибровку критериев проверки между текущими кураторами и независимыми ревьюерами диплома."
            )
            return col1, col2

        # Сценарий 4: «Кризис результата и ожиданий»
        if cr_pct >= 55.0 and a_task_pct < 60.0 and nps_val < 35:
            col1 = (
                "**Сценарий 4. «Кризис результата и ожиданий»**\n\n"
                "🔴 **Критический дефицит результата на финише:** студенты дошли до конца курса, но не подтвердили "
                "квалификацию на боевой задаче (из-за провала по критериям или отказа от сдачи диплома) и разочарованы обучением.\n\n"
                + facts_base
            )
            col2 = (
                "**Что проверить (Приоритет P1):**\n"
                "1. На каком модуле возник разрыв между теорией и практикой (сверить с вкладкой «Аудит модулей»).\n"
                "2. Прозрачность и адекватность требований итогового проекта.\n"
                "3. Организовать поддерживающий практикум для финалистов текущего среза."
            )
            return col1, col2

        # Сценарий 5: «Синдром жесткого фильтра» (Буткемп)
        if cr_pct < 55.0 and a_task_pct >= 75.0 and nps_val < 50:
            col1 = (
                "**Сценарий 5. «Синдром жесткого фильтра» (Буткемп)**\n\n"
                "🟡 **Барьер доступности среды:** выжившие финалисты показывают высокий результат, но курс теряет "
                "почти половину потока по дороге.\n\n" + facts_base
            )
            col2 = (
                "**Что проверить:**\n"
                "1. Наличие «модуля-убийцы» с резким скачком `Drop_rate` и `% Rushed` на вкладке «Аудит модулей»."
            )
            return col1, col2

        # Сценарий 6: Системный кризис программы
        if hi_core < 0.300 and cr_pct < 55.0 and a_task_pct < 60.0 and nps_val < 35:
            col1 = (
                "**Сценарий 6. Системный кризис программы**\n\n"
                "🔴 **Критический сбой курса:** высокие потери контингента на дистанции в сочетании с низкой сдачей проекта и негативом.\n\n"
                + facts_base
            )
            col2 = (
                "**Действия (Приоритет P0):**\n"
                "1. Остановить масштабирование трафика на программу.\n"
                "2. Провести сквозную ревизию соответствия программы профилю аудитории и пересобрать проблемные модули."
            )
            return col1, col2

    # Покомпонентный режим (Fallback) — если комбинация в промежуточной зоне ИЛИ невалидный NPS
    cr_zone = "🟢 Высокий" if cr_pct >= 65.0 else ("🟡 Умеренный" if cr_pct >= 55.0 else "🔴 Низкий")
    at_zone = "🟢 Высокий" if a_task_pct >= 75.0 else ("🟡 Умеренный" if a_task_pct >= 60.0 else "🔴 Низкий")
    nps_zone = (
        ("🟢 Высокий" if nps_val >= 50 else ("🟡 Умеренный" if nps_val >= 35 else "🔴 Низкий"))
        if nps_valid else "⚪ Данных недостаточно"
    )

    col1 = (
        "**Покомпонентный режим диагностики (Fallback)**\n\n"
        f"Сочетание показателей находится в промежуточной зоне (или данных NPS недостаточно). "
        f"Раздельная оценка векторов: Удержание — **{cr_zone}**, Результат — **{at_zone}**, Лояльность — **{nps_zone}**.\n\n"
        + facts_base
    )

    checks = []
    if cr_pct < 65.0:
        checks.append(
            "- **По вектору удержания (`CR` в желтой/красной зоне):** проверить модули с повышенным `Drop_rate` и `Lagging_rate` на вкладке «Аудит модулей»."
        )
    if a_task_pct < 75.0:
        checks.append(
            f"- **По вектору результата (`A_task` в желтой/красной зоне):** проанализировать структуру `Task_Fail_Rate` ({task_fail_pct:.1f}%): "
            f"долю не приступивших к проекту (`{no_show_pct:.1f}%`) и не преодолевших рубрикатор (`{rubric_fail_pct:.1f}%`). "
            "Проверить плавность нарастания сложности практики к финалу."
        )
    if nps_valid and nps_val < 50:
        checks.append(
            "- **По вектору лояльности (`NPS` в желтой/красной зоне):** сверить динамику удовлетворенности контентом, спикерами и заботой на вкладке «Сервис и среда (CSI)»."
        )
    if not nps_valid:
        checks.append(
            "- **По охвату финального опроса (`NPS`):** повысить конверсию заполнения выпускной анкеты финалистами (требуется >= 15 ответов и охват >= 50%)."
        )
    if not checks:
        checks.append("- Все ключевые показатели находятся в целевом коридоре.")

    col2 = "**Чек-лист проверки по зонам внимания:**\n" + "\n".join(checks)
    return col1, col2


def diagnose_module_lxd(mod_metrics, avg_course_drop):
    """
    Диагностика сценариев модуля (Матрица 1.4 и Блок В п. 2.2 Части 2).
    Возвращает: (expanded_by_default, badge_icon, status_title, hypotheses_list)
    """
    drop = mod_metrics["drop_rate"]
    lag = mod_metrics["lagging_rate"]
    loop = mod_metrics["loop_fail"]
    mhi_valid = mod_metrics["mhi_valid"]
    rushed = mod_metrics["rushed"]
    slow = mod_metrics["slow"]
    frag = mod_metrics["frag"]
    depl = mod_metrics["depl"]

    # Поведенческие триггеры LMS (действуют независимо от охвата опроса MHI)
    lms_red = (drop > 15.0) or (drop - avg_course_drop > 10.0) or (loop > 20.0)
    lms_yellow = (10.0 < drop <= 15.0) or (lag > 20.0) or (15.0 < loop <= 20.0)

    # Опросные триггеры MHI (действуют только при валидном MHI: >= 15 ответов и охват >= 50%)
    mhi_red = mhi_valid and ((rushed > 30.0) or (frag > 20.0) or (depl > 25.0))
    mhi_yellow = mhi_valid and ((25.0 < rushed <= 30.0) or (15.0 < frag <= 20.0) or (slow > 20.0))

    is_red = lms_red or mhi_red
    is_yellow = (not is_red) and (lms_yellow or mhi_yellow)
    expanded = is_red or is_yellow

    scenarios = []

    # Проверка Сценария 7 (недостаточно данных опроса)
    if not mhi_valid:
        scenarios.append({
            "title": "Сценарий №7. ⚪ Данных опроса недостаточно",
            "hypothesis": "Высокий риск смещения оценок из-за малой выборки (m < 15) или остановки более половины группы до опроса (Response Rate < 50%).",
            "checklist": [
                "Опираться только на объективные логи LMS (`Drop_rate`, `Lagging_rate`, `% Loop Fail`) по алгоритму Сценария №5.",
                "Проверить конверсию доходимости до финального опроса модуля."
            ]
        })

    # Сценарий 2: Разрыв сценария или сбой проверки
    if (mhi_valid and frag > 15.0) or (loop > 15.0):
        phase = "Острая фаза (с ростом отсева/отставания)" if (drop > 15.0 or lag > 20.0) else "Скрытая фаза (преодоление тупика ценой сверхусилий)"
        sev = "🔴" if ((mhi_valid and frag > 20.0) or loop > 20.0) else "🟡"
        scenarios.append({
            "title": f"Сценарий №2. {sev} Гипотеза разрыва сценария или сбоя проверки ({phase})",
            "hypothesis": "Вероятен отрыв практики от лекции, нехватка опорных примеров либо ошибка в автотестах.",
            "checklist": [
                "1. Проверить корректность работы тренажера и автотестов на задании.",
                "2. Сверить терминологию лекции с формулировкой ТЗ домашнего задания.",
                "3. Проверить наличие разобранного примера (worked example) и стартового шаблона (scaffolding)."
            ]
        })

    # Сценарий 3: Перегруз объемом (CLT)
    if mhi_valid and rushed > 25.0 and frag <= 15.0:
        phase = "Острая фаза" if (drop > 15.0 or lag > 20.0) else "Скрытая фаза (группа укладывается на пределе ресурса)"
        sev = "🔴" if rushed > 30.0 else "🟡"
        scenarios.append({
            "title": f"Сценарий №3. {sev} Гипотеза перегруза объемом — CLT ({phase})",
            "hypothesis": "Материал понятен, но суммарный хронометраж или объем рутины превышает недельный бюджет времени студента.",
            "checklist": [
                "1. Сопоставить расчетное время изучения видео/текстов и ДЗ с реальным временем прохождения в LMS.",
                "2. Проверить, можно ли вынести второстепенную теорию в опциональные материалы.",
                "3. Сократить однотипные механические операции в ДЗ."
            ]
        })

    # Сценарий 4: Аккумуляция усталости
    if mhi_valid and depl > 25.0 and frag <= 15.0:
        scenarios.append({
            "title": "Сценарий №4. 🔴 Гипотеза аккумуляции усталости",
            "hypothesis": "Длительная высокая плотность сложных тем без передышки истощает ресурс учащихся.",
            "checklist": [
                "1. Проанализировать кривую плотности тем по всей программе: идут ли подряд несколько тяжелых модулей.",
                "2. Оценить целесообразность буферной недели / модуля консолидации знаний или облегчения практики на экваторе."
            ]
        })

    # Сценарий 5: Барьер у не дошедших до опроса
    if (drop > 10.0 or lag > 20.0) and loop <= 15.0 and (not mhi_valid or (rushed <= 25.0 and frag <= 15.0 and depl <= 25.0)):
        sev = "🔴" if drop > 15.0 else "🟡"
        scenarios.append({
            "title": f"Сценарий №5. {sev} Гипотеза барьера у не дошедших до финального опроса модуля",
            "hypothesis": "Инфраструктурное трение ИЛИ скрытый методический стоппер: поскольку MHI отражает только опыт сдавших практику, нормальные оценки выживших не исключают барьера у остановившихся.",
            "checklist": [
                "1. По логам LMS локализовать шаг остановки неответивших в MHI: отвал произошел на входе в модуль (установка ПО, доступы, окружение) или на попытках выполнения практического задания.",
                "2. Проверить текстовые комментарии В10 на жалобы по настройке софта и тренажера.",
                "3. Сопоставить `% Loop Fail` между завершившими модуль и остановившимися студентами."
            ]
        })

    # Сценарий 6: Обращение экспертизы (Скука)
    if mhi_valid and slow > 20.0:
        scenarios.append({
            "title": "Сценарий №6. 🟡 Гипотеза обращения экспертизы (Скука)",
            "hypothesis": "Базовый темп слишком прост для части аудитории с опытом.",
            "checklist": [
                "1. Добавить возможность досрочной сдачи базовых шагов (экстернат) и факультативные задачи «со звездочкой»."
            ]
        })

    # Сценарий 1: Штатный модуль (если нет ни одного отклонения и MHI валиден)
    if not expanded and mhi_valid:
        scenarios.append({
            "title": "Сценарий №1. 🟢 Штатный модуль",
            "hypothesis": "Признаков системного перегруза или когнитивных тупиков не выявлено.",
            "checklist": [
                "• Зафиксировать структуру урока как рабочую.",
                "• Плановые точечные улучшения по открытым комментариям."
            ]
        })

    if is_red:
        badge = "🔴 Проблемный модуль (Красная зона)"
    elif is_yellow:
        badge = "🟡 Зона внимания (Желтая зона)"
    else:
        badge = "🟢 Штатный модуль" if mhi_valid else "⚪ Мало данных опроса (поведение в LMS в норме)"

    return expanded, badge, scenarios


# =====================================================================
# САЙДБАР И УПРАВЛЕНИЕ СРЕЗОМ
# =====================================================================
st.sidebar.title("🧭 Управление аудитом")
selected_slice_name = st.sidebar.selectbox(
    "Выберите активный срез (Audit Slice):",
    options=list(slices_data.keys()),
    index=0
)

current_slice = slices_data[selected_slice_name]
enrolled_n = current_slice["enrolled"]

st.sidebar.markdown("---")
st.sidebar.subheader("📏 Индикатор выборки")
if enrolled_n >= 30:
    st.sidebar.success(f"✅ Выборка валидна: **N = {enrolled_n}** чел. (порог ≥ 30 выполнен)")
else:
    st.sidebar.warning(f"⏳ Накопление выборки: **N = {enrolled_n} из 30** чел.")
    st.sidebar.progress(enrolled_n / 30.0)

st.sidebar.markdown(f"**Версия программы:** `{current_slice['version']}`")
if current_slice["anomaly_cohort"]:
    st.sidebar.info(f"⚡ Зафиксирована локальная аномалия {current_slice['anomaly_cohort']} (отклонение > 20 п.п. от соседних когорт среза).")

# Заголовок страницы
st.title("📊 Система диагностики качества образовательного продукта (v1.0)")
st.caption(f"Активный срез: **{selected_slice_name}** | Интеграция логов LMS и анкеты «Пульс модуля»")

# =====================================================================
# ПРАВИЛО DATA GATING НА УРОВНЕ СРЕЗА (Enrolled < 30)
# =====================================================================
if enrolled_n < 30:
    st.warning(
        f"🔒 **Идет накопление выборки (собрано {enrolled_n} из 30). "
        "Стратегическая аналитика курса защищена от шума малых групп.**"
    )
    st.stop()


# =====================================================================
# ТРИ ВКЛАДКИ СИСТЕМНОГО КОНТУРА
# =====================================================================
tab1, tab2, tab3 = st.tabs([
    "🌐 Часть №1. Аудит курса",
    "🔬 Часть №2. Аудит модулей",
    "🤝 Часть №3. Сервис и среда (CSI)"
])


# ---------------------------------------------------------------------
# ВКЛАДКА 1: АУДИТ КУРСА (МАКРО-УРОВЕНЬ)
# ---------------------------------------------------------------------
with tab1:
    finished = current_slice["finished"]
    attempted = current_slice["attempted_task"]
    passed = current_slice["passed_task"]
    nps = current_slice["nps"]
    nps_resp = current_slice["nps_respondents"]
    anomaly_flag = f" ⚡ Локальная аномалия {current_slice['anomaly_cohort']}" if current_slice["anomaly_cohort"] else ""

    # Расчеты производных метрик (п. 1.2)
    cr = finished / enrolled_n
    a_task = passed / finished if finished > 0 else 0.0
    hi_core = passed / enrolled_n  # CR * A_task

    task_fail_rate = (finished - passed) / finished if finished > 0 else 0.0
    no_show_rate = (finished - attempted) / finished if finished > 0 else 0.0
    rubric_fail_rate = (attempted - passed) / finished if finished > 0 else 0.0
    unconfirmed_share = (finished - passed) / enrolled_n  # CR - HI_core

    nps_coverage = (nps_resp / finished * 100.0) if finished > 0 else 0.0
    nps_valid = (nps_resp >= 15) and (nps_coverage >= 50.0)

    # --- БЛОК А. Верхний ряд ключевых показателей (KPI Cards) ---
    st.subheader("Блок А. Ключевые показатели стратегического здоровья курса")
    c1, c2, c3, c4 = st.columns(4)

    # 1. Сквозной HI_core
    with c1:
        if hi_core >= 0.500:
            hi_cls, hi_lbl = "bg-green", "🟢 Целевая зона (≥ 0.500)"
        elif hi_core >= 0.300:
            hi_cls, hi_lbl = "bg-yellow", "🟡 Умеренная зона (0.300–0.499)"
        else:
            hi_cls, hi_lbl = "bg-red", "🔴 Критическая зона (< 0.300)"
        render_kpi_card(
            "Сквозной HI_core",
            f"{hi_core:.3f} ({hi_core*100:.1f}%)",
            f"{passed} из {enrolled_n} зачисленных",
            hi_lbl, hi_cls, anomaly_flag
        )

    # 2. Доходимость (CR)
    with c2:
        cr_pct = cr * 100.0
        if cr_pct >= 65.0:
            cr_cls, cr_lbl = "bg-green", "🟢 Высокий (≥ 65.0%)"
        elif cr_pct >= 55.0:
            cr_cls, cr_lbl = "bg-yellow", "🟡 Умеренный (55.0–64.9%)"
        else:
            cr_cls, cr_lbl = "bg-red", "🔴 Низкий (< 55.0%)"
        render_kpi_card(
            "Доходимость (CR)",
            f"{cr_pct:.1f}%",
            f"{finished} из {enrolled_n} чел.",
            cr_lbl, cr_cls, anomaly_flag
        )

    # 3. Сдача боевой задачи (A_task)
    with c3:
        at_pct = a_task * 100.0
        if at_pct >= 75.0:
            at_cls, at_lbl = "bg-green", "🟢 Высокий (≥ 75.0%)"
        elif at_pct >= 60.0:
            at_cls, at_lbl = "bg-yellow", "🟡 Умеренный (60.0–74.9%)"
        else:
            at_cls, at_lbl = "bg-red", "🔴 Низкий (< 60.0%)"
        small_fin_badge = "⚠️ Малая база финалистов, оценка предварительная" if finished < 20 else anomaly_flag
        render_kpi_card(
            "Сдача боевой задачи (A_task)",
            f"{at_pct:.1f}%",
            f"{passed} из {finished} финалистов (Приступили: {attempted})",
            at_lbl, at_cls, small_fin_badge
        )

    # 4. Итоговый NPS курса
    with c4:
        if not nps_valid:
            nps_cls, nps_lbl = "bg-grey", "⚪ Мало ответов (< 15 или охват < 50%)"
        elif nps >= 50:
            nps_cls, nps_lbl = "bg-green", "🟢 Высокий (≥ 50)" + (" [Сверхвысокий > 60]" if nps > 60 else "")
        elif nps >= 35:
            nps_cls, nps_lbl = "bg-yellow", "🟡 Умеренный (35–49)"
        else:
            nps_cls, nps_lbl = "bg-red", "🔴 Низкий (< 35)"
        render_kpi_card(
            "Итоговый NPS курса",
            f"{nps:+d}" if nps_valid else f"{nps:+d} (⚪)",
            f"Ответили: {nps_resp} из {finished} финалистов ({nps_coverage:.0f}%)",
            nps_lbl, nps_cls
        )

    st.markdown("---")

    # --- БЛОК Б и БЛОК В в две колонки ---
    col_b, col_v = st.columns([1.15, 1.0])

    with col_b:
        st.subheader("Блок Б. Динамика валидных срезов во времени")
        valid_slices = [s for s in slices_data.values() if s["enrolled"] >= 30]
        x_labels = [s["id"] for s in valid_slices]
        cr_series = [s["finished"] / s["enrolled"] for s in valid_slices]
        at_series = [s["passed_task"] / s["finished"] for s in valid_slices]
        hi_series = [s["passed_task"] / s["enrolled"] for s in valid_slices]

        fig_dyn = go.Figure()
        fig_dyn.add_trace(go.Bar(
            x=x_labels, y=cr_series, name="Доходимость (CR)",
            marker_color="#5B9BD5", text=[f"{v*100:.1f}%" for v in cr_series], textposition="auto"
        ))
        fig_dyn.add_trace(go.Bar(
            x=x_labels, y=at_series, name="Сдача задачи (A_task)",
            marker_color="#4ECDC4", text=[f"{v*100:.1f}%" for v in at_series], textposition="auto"
        ))
        fig_dyn.add_trace(go.Scatter(
            x=x_labels, y=hi_series, name="Сквозной HI_core",
            mode="lines+markers+text",
            text=[f"{v:.3f}" for v in hi_series], textposition="top center",
            line=dict(color="#1F2937", width=3.5),
            marker=dict(size=9, color="#1F2937")
        ))
        # Горизонтальные пунктирные ориентиры специально для HI_core (0.50 и 0.30)
        fig_dyn.add_hline(
            y=0.50, line_dash="dash", line_color="#2E7D32",
            annotation_text="Целевой HI_core ≥ 0.50", annotation_position="top left"
        )
        fig_dyn.add_hline(
            y=0.30, line_dash="dash", line_color="#C62828",
            annotation_text="Критическая граница HI_core = 0.30", annotation_position="bottom left"
        )
        fig_dyn.update_layout(
            barmode="group",
            yaxis=dict(title="Доля / Индекс (0.0 – 1.0)", range=[0, 1.05], tickformat=".0%"),
            xaxis=dict(title="Валидные срезы"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=380,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor="white"
        )
        st.plotly_chart(fig_dyn, use_container_width=True)

    with col_v:
        st.subheader("Блок В. Воронка подтверждения навыка (от базы Enrolled)")
        hi_bar_color = "#34A853" if at_pct >= 75.0 else ("#FBBC04" if at_pct >= 60.0 else "#EA4335")

        fig_funnel = go.Figure()
        fig_funnel.add_trace(go.Bar(
            y=["Дошли и подтвердили навык (HI_core)", "Дошли до финала (CR)"],
            x=[hi_core * 100.0, cr * 100.0],
            orientation="h",
            marker_color=[hi_bar_color, "#4A90E2"],
            text=[
                f"{hi_core*100:.1f}% ({passed} из {enrolled_n} чел.)",
                f"{cr*100:.1f}% ({finished} из {enrolled_n} чел.)"
            ],
            textposition="auto"
        ))
        fig_funnel.update_layout(
            xaxis=dict(title="% от числа зачисленных (Enrolled)", range=[0, 100]),
            height=210,
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor="white"
        )
        st.plotly_chart(fig_funnel, use_container_width=True)

        # Расчетные показатели под графиком
        st.markdown(
            f"- **Доля финалистов без подтверждения навыка (`Task_Fail_Rate = 1 - A_task`):** `{task_fail_rate*100:.1f}%` "
            f"*(в т.ч. Не приступили к проекту: `{no_show_rate*100:.1f}%` | Не прошли по рубрикатору: `{rubric_fail_rate*100:.1f}%`)*\n"
            f"- **Доля «холостого выпуска» от всех зачисленных (`Unconfirmed_Share = CR - HI_core`):** `{unconfirmed_share*100:.1f}%`"
        )

        # Алгоритм вывода текстового статуса под графиком (4 ветки по п. 2.2 Блок В)
        if hi_core >= 0.500 and cr_pct >= 65.0 and at_pct >= 75.0:
            st.success("🟢 Образовательный выход сбалансирован: высокая доходимость подкреплена успешной защитой независимого проекта.")
        elif cr_pct >= 65.0 and at_pct < 60.0:
            st.warning(
                f"⚠️ Внимание: разрыв подтверждения результата! До финала дошли {cr_pct:.1f}%, но подтвердили квалификацию "
                f"только {hi_core*100:.1f}% от поступивших ({task_fail_rate*100:.1f}% финалистов остались без подтвержденного результата: "
                f"{no_show_rate*100:.1f}% не представили работу, {rubric_fail_rate*100:.1f}% не прошли по рубрикатору)."
            )
        elif cr_pct < 55.0 and at_pct >= 75.0:
            st.info(
                f"ℹ️ Синдром жесткого фильтра: высокая сдача итогового проекта ({at_pct:.1f}% финалистов) "
                f"достигается ценой потери {100.0 - cr_pct:.1f}% студентов на дистанции курса."
            )
        else:
            cr_state = "целевой норме" if cr_pct >= 65.0 else ("умеренной зоне" if cr_pct >= 55.0 else "зоне риска")
            at_state = "целевой норме" if at_pct >= 75.0 else ("умеренной зоне" if at_pct >= 60.0 else "зоне риска")
            st.info(
                f"ℹ️ Комбинированный статус: удержание (CR = {cr_pct:.1f}%) находится в {cr_state}, "
                f"подтверждение результата (A_task = {at_pct:.1f}%) — в {at_state} "
                f"(не приступили к диплому: {no_show_rate*100:.1f}%, не прошли по критериям: {rubric_fail_rate*100:.1f}%)."
            )

    st.markdown("---")

    # --- БЛОК Г. Автоматическая исследовательская записка ---
    st.subheader("Блок Г. Автоматическая исследовательская записка")
    note_col1_text, note_col2_text = evaluate_macro_scenario(
        hi_core, cr_pct, at_pct, nps, nps_valid,
        no_show_rate * 100.0, rubric_fail_rate * 100.0, unconfirmed_share * 100.0
    )
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("#### 📌 Колонка 1: «Что показывают данные»")
        st.markdown(f'<div class="note-box">{note_col1_text}</div>', unsafe_allow_html=True)
    with g2:
        st.markdown("#### 🛠️ Колонка 2: «Гипотезы и вектор действий»")
        st.markdown(f'<div class="note-box">{note_col2_text}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------
# ВКЛАДКА 2: АУДИТ МОДУЛЕЙ (МЕЗО-УРОВЕНЬ)
# ---------------------------------------------------------------------
with tab2:
    modules_raw = current_slice["modules"]
    processed_modules = []

    for m in modules_raw:
        s_started = m["started"]
        p_paused = m["paused"]
        n_active = s_started - p_paused  # Students_in_module = S - P
        dropped_total = m["dropped_official"] + m["dropped_inactive"]
        m_resp = m["mhi_resp"]

        cor_mod = (s_started / enrolled_n * 100.0) if enrolled_n > 0 else 0.0
        drop_rate = (dropped_total / n_active * 100.0) if n_active > 0 else 0.0
        lagging_rate = (m["lagging"] / n_active * 100.0) if n_active > 0 else 0.0
        mhi_resp_rate = (m_resp / n_active * 100.0) if n_active > 0 else 0.0
        mhi_valid = (m_resp >= 15) and (mhi_resp_rate >= 50.0)

        rushed_pct = (m["rushed_cnt"] / m_resp * 100.0) if m_resp > 0 else 0.0
        slow_pct = (m["slow_cnt"] / m_resp * 100.0) if m_resp > 0 else 0.0
        frag_pct = (m["frag_cnt"] / m_resp * 100.0) if m_resp > 0 else 0.0
        depl_pct = (m["depl_cnt"] / m_resp * 100.0) if m_resp > 0 else 0.0
        loop_fail_pct = (m["loop_fail_users"] / n_active * 100.0) if n_active > 0 else 0.0

        title_display = m["name"]
        if m["cohort_outlier"]:
            title_display += " ⚡"
        if n_active < 15:
            title_display += " ⚠️ Малая база модуля (n < 15), оценка предварительная"

        processed_modules.append({
            "num": m["num"],
            "title_display": title_display,
            "s_started": s_started,
            "p_paused": p_paused,
            "n_active": n_active,
            "m_resp": m_resp,
            "cor_mod": cor_mod,
            "drop_rate": drop_rate,
            "lagging_rate": lagging_rate,
            "dropped_official": m["dropped_official"],
            "dropped_inactive": m["dropped_inactive"],
            "mhi_resp_rate": mhi_resp_rate,
            "mhi_valid": mhi_valid,
            "rushed": rushed_pct,
            "slow": slow_pct,
            "frag": frag_pct,
            "depl": depl_pct,
            "loop_fail": loop_fail_pct,
            "cohort_outlier": m["cohort_outlier"]
        })

    avg_course_drop = sum(x["drop_rate"] for x in processed_modules) / len(processed_modules) if processed_modules else 0.0

    # --- БЛОК А. Сводная матрица учебной среды (Module Overview Matrix) ---
    st.subheader("Блок А. Сводная матрица учебной среды (Module Overview Matrix)")
    st.caption(
        "Оценка проводится по закрытым модулям после окна Cutoff (Дедлайн + 14 дней). "
        "При ответивших m < 15 чел. или охвате MHI < 50% опросные колонки (5–8) переводятся в серый статус «⚪ Мало данных»."
    )

    # Построение HTML-таблицы с точным условным форматированием и тултипами разбивки отсева
    html_rows = []
    for pm in processed_modules:
        # 3. Колонка Drop_rate | Lagging_rate
        if pm["drop_rate"] > 15.0 or (pm["drop_rate"] - avg_course_drop > 10.0):
            drop_bg = "#fce8e6; color:#c5221f; font-weight:600;"
        elif pm["drop_rate"] > 10.0 or pm["lagging_rate"] > 20.0:
            drop_bg = "#fef7e0; color:#b06000; font-weight:600;"
        else:
            drop_bg = "#ffffff;"

        drop_tooltip = (
            f"Активная база n = {pm['n_active']} чел. | "
            f"Официальные отчисления: {pm['dropped_official']} чел. ({pm['dropped_official']/pm['n_active']*100:.1f}%) | "
            f"Неактивность > 14 дн.: {pm['dropped_inactive']} чел. ({pm['dropped_inactive']/pm['n_active']*100:.1f}%)"
        )

        # Колонки 5–8 (MHI) с приоритетом полноты данных
        if not pm["mhi_valid"]:
            grey_style = "#f1f3f4; color:#5f6368;"
            rushed_cell = f'<td style="background:{grey_style}">⚪ Мало данных ({pm["rushed"]:.1f}%)</td>'
            slow_cell = f'<td style="background:{grey_style}">⚪ Мало данных ({pm["slow"]:.1f}%)</td>'
            frag_cell = f'<td style="background:{grey_style}">⚪ Мало данных ({pm["frag"]:.1f}%)</td>'
            depl_cell = f'<td style="background:{grey_style}">⚪ Мало данных ({pm["depl"]:.1f}%)</td>'
        else:
            r_bg = "#fce8e6; color:#c5221f; font-weight:600;" if pm["rushed"] > 30.0 else ("#fef7e0; color:#b06000; font-weight:600;" if pm["rushed"] > 25.0 else "#ffffff;")
            s_bg = "#fef7e0; color:#b06000; font-weight:600;" if pm["slow"] > 20.0 else "#ffffff;"
            f_bg = "#fce8e6; color:#c5221f; font-weight:600;" if pm["frag"] > 20.0 else ("#fef7e0; color:#b06000; font-weight:600;" if pm["frag"] > 15.0 else "#ffffff;")
            d_bg = "#fce8e6; color:#c5221f; font-weight:600;" if pm["depl"] > 25.0 else "#ffffff;"

            rushed_cell = f'<td style="background:{r_bg}">{pm["rushed"]:.1f}%</td>'
            slow_cell = f'<td style="background:{s_bg}">{pm["slow"]:.1f}%</td>'
            frag_cell = f'<td style="background:{f_bg}">{pm["frag"]:.1f}%</td>'
            depl_cell = f'<td style="background:{d_bg}">{pm["depl"]:.1f}%</td>'

        # 9. Колонка % Loop Fail (независимо от охвата MHI)
        l_bg = "#fce8e6; color:#c5221f; font-weight:600;" if pm["loop_fail"] > 20.0 else ("#fef7e0; color:#b06000; font-weight:600;" if pm["loop_fail"] > 15.0 else "#ffffff;")

        html_rows.append(f"""
        <tr>
            <td style="font-weight:600;">{pm['title_display']}</td>
            <td>{pm['cor_mod']:.1f}% <span style="color:#666; font-size:0.82rem;">(приступили: {pm['s_started']} из {enrolled_n} чел., на паузе: {pm['p_paused']} чел.)</span></td>
            <td style="background:{drop_bg}" title="{drop_tooltip}">Отсев: {pm['drop_rate']:.1f}% | В досдаче: {pm['lagging_rate']:.1f}% ℹ️</td>
            <td>{pm['mhi_resp_rate']:.0f}% ({pm['m_resp']}/{pm['n_active']} чел.)</td>
            {rushed_cell}
            {slow_cell}
            {frag_cell}
            {depl_cell}
            <td style="background:{l_bg}">{pm['loop_fail']:.1f}%</td>
        </tr>
        """)

    table_html = f"""
    <div style="overflow-x:auto;">
    <table style="width:100%; border-collapse:collapse; font-size:0.9rem; border:1px solid #ddd;">
        <thead>
            <tr style="background-color:#f8f9fa; text-align:left; border-bottom:2px solid #ccc;">
                <th style="padding:10px;">1. Модуль курса</th>
                <th style="padding:10px;">2. Кумулятивное удержание (COR_mod)</th>
                <th style="padding:10px;">3. Отсев и отставание (Drop | Lagging)</th>
                <th style="padding:10px;">4. Охват MHI</th>
                <th style="padding:10px;">5. Спешат (% Rushed)</th>
                <th style="padding:10px;">6. Заниженный темп (% Slow)</th>
                <th style="padding:10px;">7. Хаос (% Fragmented)</th>
                <th style="padding:10px;">8. Истощены (% Depleted)</th>
                <th style="padding:10px;">9. Петли ошибок (% Loop Fail)</th>
            </tr>
        </thead>
        <tbody>
            {''.join(html_rows)}
        </tbody>
    </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("---")

    # --- БЛОК Б. Воронка модульного удержания (Drop-off Map) ---
    st.subheader("Блок Б. Воронка модульного удержания (Drop-off Map)")
    fig_dropoff = go.Figure()
    fig_dropoff.add_trace(go.Bar(
        x=[pm["title_display"] for pm in processed_modules],
        y=[pm["cor_mod"] for pm in processed_modules],
        text=[f"COR: {pm['cor_mod']:.1f}% (Отсев шага: {pm['drop_rate']:.1f}%)" for pm in processed_modules],
        textposition="auto",
        marker=dict(
            color=[pm["drop_rate"] for pm in processed_modules],
            colorscale=[[0.0, "#4A90E2"], [0.5, "#F5A623"], [1.0, "#D0021B"]],
            cmin=0, cmax=25,
            colorbar=dict(title="Drop_rate (%)")
        )
    ))
    fig_dropoff.add_hline(
        y=65.0, line_dash="dash", line_color="#137333",
        annotation_text="Ориентир нормативного выпуска курса (65%)", annotation_position="top right"
    )
    fig_dropoff.update_layout(
        yaxis=dict(title="Кумулятивная доля удержания COR_mod (%)", range=[0, 108]),
        xaxis=dict(title="Последовательность модулей программы"),
        height=350,
        margin=dict(l=20, r=20, t=30, b=20),
        plot_bgcolor="white"
    )
    st.plotly_chart(fig_dropoff, use_container_width=True)

    st.markdown("---")

    # --- БЛОК В. Исследовательские карточки модулей (LXD Insight Cards) ---
    st.subheader("Блок В. Исследовательские карточки модулей (LXD Insight Cards)")
    for pm in processed_modules:
        expanded_flag, badge_str, mod_scenarios = diagnose_module_lxd(pm, avg_course_drop)
        with st.expander(f"{pm['title_display']} — {badge_str}", expanded=expanded_flag):
            left_c, right_c = st.columns([1.0, 1.4])
            with left_c:
                st.markdown("**Ключевые метрики модуля и нормативные границы:**")
                st.markdown(
                    f"- **Активная база модуля (`Students_in_module`):** `{pm['n_active']}` чел. (приступили `{pm['s_started']}`, на паузе `{pm['p_paused']}`)\n"
                    f"- **Локальный отсев (`Drop_rate`):** `{pm['drop_rate']:.1f}%` *(норма ≤ 10.0%, риск > 15.0%)* — "
                    f"офиц. отчисления: `{pm['dropped_official']}`, неактивность > 14 дн.: `{pm['dropped_inactive']}`\n"
                    f"- **В досдаче (`Lagging_rate`):** `{pm['lagging_rate']:.1f}%` *(норма ≤ 20.0%)*\n"
                    f"- **Петли 3+ ошибок (`% Loop Fail`):** `{pm['loop_fail']:.1f}%` *(норма ≤ 15.0%, красная > 20.0%)*\n"
                    f"- **Охват опроса MHI:** `{pm['mhi_resp_rate']:.0f}%` (`{pm['m_resp']}/{pm['n_active']}` чел. — "
                    f"{'валиден' if pm['mhi_valid'] else '⚪ мало данных'})\n"
                    f"- **Спешат (`% Rushed`):** `{pm['rushed']:.1f}%` *(норма ≤ 25.0%, красная > 30.0%)*\n"
                    f"- **Заниженный темп (`% Slow`):** `{pm['slow']:.1f}%` *(ориентир ≤ 20.0%)*\n"
                    f"- **Хаос (`% Fragmented`):** `{pm['frag']:.1f}%` *(норма ≤ 15.0%, красная > 20.0%)*\n"
                    f"- **Истощены (`% Depleted`):** `{pm['depl']:.1f}%` *(норма ≤ 25.0%)*"
                )
            with right_c:
                st.markdown("**Диагностическое заключение (модель LXD) и чек-лист верификации:**")
                if pm["cohort_outlier"]:
                    st.info("⚡ **Выброс в 1 потоке:** аномалия зафиксирована только в одной когорте среза. Проверьте локальный сбой расписания или замену куратора перед правкой контента.")
                for sc in mod_scenarios:
                    st.markdown(f"**{sc['title']}**")
                    st.caption(f"Вероятное состояние среды: {sc['hypothesis']}")
                    for item in sc["checklist"]:
                        st.markdown(item)


# ---------------------------------------------------------------------
# ВКЛАДКА 3: СЕРВИС И СРЕДА (CSI)
# ---------------------------------------------------------------------
with tab3:
    u_resp = current_slice["u_resp"]
    u_coverage = (u_resp / enrolled_n * 100.0) if enrolled_n > 0 else 0.0
    t2_u = current_slice["top2_unique"]

    csi_content = (t2_u["q4"] + t2_u["q5"] + t2_u["q6"]) / 3.0
    csi_expert = t2_u["q7"]
    csi_care = (t2_u["q8"] + t2_u["q9"]) / 2.0

    # --- БЛОК А. Верхний ряд ролевых KPI (Service Health Summary) ---
    st.subheader("Блок А. Сводные ролевые субиндексы по уникальным респондентам среза")
    sc1, sc2, sc3 = st.columns(3)

    cov_sub = f"Охват среза: {u_coverage:.1f}%, {u_resp} уникальных студентов"

    # 1. Контент и задания (В4–6)
    with sc1:
        if u_resp < 15:
            c_cls, c_lbl = "bg-grey", "⚪ Мало данных (U_resp < 15)"
        elif csi_content >= 85.0:
            c_cls, c_lbl = "bg-green", "🟢 Целевая зона (≥ 85.0%)"
        elif csi_content >= 75.0:
            c_cls, c_lbl = "bg-yellow", "🟡 Зона калибровки (75.0–84.9%)"
        else:
            c_cls, c_lbl = "bg-red", "🔴 Выраженное трение (< 75.0%)"
        render_kpi_card(
            "Контент и задания (В4–6)",
            f"{csi_content:.1f}%",
            f"Зона ответственности методистов и авторов | {cov_sub}",
            c_lbl, c_cls
        )

    # 2. Эксперты и спикеры (В7)
    with sc2:
        if u_resp < 15:
            e_cls, e_lbl = "bg-grey", "⚪ Мало данных (U_resp < 15)"
        elif csi_expert >= 88.0:
            e_cls, e_lbl = "bg-green", "🟢 Целевая зона (≥ 88.0%)"
        elif csi_expert >= 80.0:
            e_cls, e_lbl = "bg-yellow", "🟡 Зона калибровки (80.0–87.9%)"
        else:
            e_cls, e_lbl = "bg-red", "🔴 Выраженное трение (< 80.0%)"
        render_kpi_card(
            "Эксперты и спикеры (В7)",
            f"{csi_expert:.1f}%",
            f"Отдел работы с экспертами (ОРЭ) | {cov_sub}",
            e_lbl, e_cls
        )

    # 3. Команда сопровождения (В8–9)
    with sc3:
        if u_resp < 15:
            k_cls, k_lbl = "bg-grey", "⚪ Мало данных (U_resp < 15)"
        elif csi_care >= 88.0:
            k_cls, k_lbl = "bg-green", "🟢 Целевая зона (≥ 88.0%)"
        elif csi_care >= 80.0:
            k_cls, k_lbl = "bg-yellow", "🟡 Зона калибровки (80.0–87.9%)"
        else:
            k_cls, k_lbl = "bg-red", "🔴 Выраженное трение (< 80.0%)"
        render_kpi_card(
            "Команда сопровождения (В8–9)",
            f"{csi_care:.1f}%",
            f"Служба заботы и кураторы | {cov_sub}",
            k_lbl, k_cls
        )

    st.markdown("---")

    # --- БЛОК Б. Детальная матрица рейтингов модулей (CSI Matrix) ---
    st.subheader("Блок Б. Детальная матрица рейтингов модулей (CSI Matrix, Top-2 Box)")
    st.caption(
        "Наведите курсор на ячейку для просмотра доли критического негатива (Bottom-2 Box, оценки 1–2). "
        "Индикатор 📉 фиксирует резкий перепад восприятия (падение Top-2 Box на ≥ 15.0 п.п. к предыдущему модулю)."
    )

    csi_rows_html = []
    prev_mod_valid = False
    prev_top2 = {}

    for idx, m in enumerate(modules_raw):
        n_active = m["started"] - m["paused"]
        m_resp = m["mhi_resp"]
        resp_rate = (m_resp / n_active * 100.0) if n_active > 0 else 0.0
        cell_valid = (m_resp >= 15) and (resp_rate >= 50.0)

        cells_html = []
        q_keys = ["q4", "q5", "q6", "q7", "q8", "q9"]

        for qk in q_keys:
            t2 = m["csi_top2"][qk]
            b2 = m["csi_bot2"][qk]
            is_content = qk in ("q4", "q5", "q6")

            if not cell_valid:
                style = "background:#f1f3f4; color:#5f6368;"
                val_str = f"⚪ Мало данных ({t2:.1f}%)"
            else:
                # Проверка резкого перепада (Friction Alert: падение >= 15.0 п.п.)
                drop_alert = ""
                if prev_mod_valid and (prev_top2.get(qk, t2) - t2 >= 15.0):
                    diff = prev_top2[qk] - t2
                    drop_alert = f" <span style='color:#c5221f; font-weight:700;'>📉 -{diff:.1f} п.п.</span>"

                # Пороги для Контента (В4-В6: 85% / 75%) vs Экспертов и Заботы (В7-В9: 88% / 80%) + Bottom-2 > 15%
                green_thr = 85.0 if is_content else 88.0
                yellow_thr = 75.0 if is_content else 80.0

                if t2 < yellow_thr or b2 > 15.0:
                    style = "background:#fce8e6; color:#c5221f; font-weight:600;"
                elif t2 < green_thr:
                    style = "background:#fef7e0; color:#b06000; font-weight:600;"
                else:
                    style = "background:#e6f4ea; color:#137333;"

                val_str = f"{t2:.1f}%{drop_alert}"

            tooltip = f"Top-2 Box (оценки 4-5): {t2:.1f}% | Bottom-2 Box (оценки 1-2): {b2:.1f}%"
            cells_html.append(f'<td style="padding:10px; {style}" title="{tooltip}">{val_str}</td>')

        csi_rows_html.append(f"""
        <tr style="border-bottom:1px solid #eee;">
            <td style="padding:10px; font-weight:600;">{m['name']}</td>
            {''.join(cells_html)}
            <td style="padding:10px;">{resp_rate:.0f}% ({m_resp}/{n_active} чел.)</td>
        </tr>
        """)

        prev_mod_valid = cell_valid
        prev_top2 = m["csi_top2"]

    csi_table_html = f"""
    <div style="overflow-x:auto;">
    <table style="width:100%; border-collapse:collapse; font-size:0.9rem; border:1px solid #ddd;">
        <thead>
            <tr style="background-color:#f8f9fa; text-align:left; border-bottom:2px solid #ccc;">
                <th style="padding:10px;">Модуль программы</th>
                <th style="padding:10px;">В4: Теория (%)</th>
                <th style="padding:10px;">В5: Актуальность (%)</th>
                <th style="padding:10px;">В6: Задания (%)</th>
                <th style="padding:10px;">В7: Спикеры (%)</th>
                <th style="padding:10px;">В8: Скорость / SLA (%)</th>
                <th style="padding:10px;">В9: Эмпатия (%)</th>
                <th style="padding:10px;">Охват CSI</th>
            </tr>
        </thead>
        <tbody>
            {''.join(csi_rows_html)}
        </tbody>
    </table>
    </div>
    """
    st.markdown(csi_table_html, unsafe_allow_html=True)

    # Вывод диагностических чек-листов для профильных отделов при срабатывании сервисных сценариев (п. 1.4 Части 3)
    with st.expander("📋 Чек-листы верификации сервисных сбоев для профильных отделов (по матрице п. 1.4)", expanded=False):
        st.markdown("""
        - **Контент и практика (В4–В6 < 75.0% или Bottom-2 > 15.0%):** изучить комментарии В10 и сверить с `% Loop Fail`; провести ревизию формулировок ДЗ, автотестов и опубликовать чек-лист самопроверки; обновить проблемные фрагменты теории.
        - **Эксперты курса (В7 < 80.0% или Bottom-2 > 15.0%):** проверить однородность оценки между потоками среза; отсмотреть запись вебинара по чек-листу динамики; провести развивающий брифинг со спикером.
        - **Команда заботы — Восприятие скорости (В8 < 80.0% или Bottom-2 > 15.0%):** выгрузить из тикет-системы/LMS фактическое время первого ответа и проверки ДЗ (проверить реальное нарушение SLA > 24–48 ч); перераспределить нагрузку в пиковые дни или подсветить регламентные сроки студентам.
        - **Команда заботы — Эмпатия и ToV (В9 < 80.0% или Bottom-2 > 15.0%):** провести выборочный аудит текста комментариев ревьюеров и чатов на проблемном модуле; откалибровать кураторов по стандарту развивающей обратной связи.
        """)

    st.markdown("---")

    # --- БЛОК В. Реестр качественного фидбека (Qualitative Feedback Feed) ---
    st.subheader("Блок В. Реестр качественного фидбека (Вопрос В10: «Что стоит улучшить в модуле?»)")
    module_filter_options = ["Все модули"] + [m["name"] for m in modules_raw]
    selected_mod_filter = st.selectbox("Фильтр по модулю программы:", options=module_filter_options)

    filtered_comments = []
    for m in modules_raw:
        if selected_mod_filter in ("Все модули", m["name"]):
            for txt in m["comments"]:
                filtered_comments.append((m["name"], txt))

    if not filtered_comments:
        st.info("По данному срезу/модулю нет текстовых комментариев в открытом вопросе В10")
    else:
        for mod_title, comment_text in filtered_comments:
            st.markdown(f"""
            <div class="comment-card">
                <div style="font-weight:700; color:#2c3e50; margin-bottom:4px;">{mod_title}</div>
                <div style="color:#333;">{comment_text}</div>
            </div>
            """, unsafe_allow_html=True)
