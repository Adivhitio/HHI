import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# =====================================================================
# КОНФИГУРАЦИЯ СТРАНИЦЫ И СТИЛИ
# =====================================================================
st.set_page_config(
    page_title="Диагностика качества курса",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
.kpi-card {
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 12px;
    border: 1px solid #e0e0e0;
    background-color: #ffffff;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.kpi-title { font-size: 0.9rem; color: #374151 !important; font-weight: 600; margin-bottom: 4px; }
.kpi-value { font-size: 1.75rem; font-weight: 700; margin-bottom: 4px; color: #111827 !important; }
.kpi-sub { font-size: 0.82rem; color: #4b5563 !important; margin-bottom: 8px; }
.kpi-badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 600;
    background-color: rgba(255,255,255,0.75);
    color: inherit !important;
}
.bg-green { background-color: #e6f4ea !important; color: #137333 !important; border-left: 5px solid #34a853 !important; }
.bg-yellow { background-color: #fef7e0 !important; color: #b06000 !important; border-left: 5px solid #fbbc04 !important; }
.bg-red { background-color: #fce8e6 !important; color: #c5221f !important; border-left: 5px solid #ea4335 !important; }
.bg-grey { background-color: #f1f3f4 !important; color: #5f6368 !important; border-left: 5px solid #9aa0a6 !important; }

.custom-table-wrap { overflow-x: auto; margin-bottom: 1rem; }
table.custom-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.88rem;
    background-color: #ffffff !important;
    color: #1f2937 !important;
    border: 1px solid #d1d5db;
}
table.custom-table th {
    background-color: #f3f4f6 !important;
    color: #111827 !important;
    font-weight: 600;
    text-align: left;
    padding: 10px 12px;
    border-bottom: 2px solid #d1d5db;
    border-right: 1px solid #e5e7eb;
}
table.custom-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #e5e7eb;
    border-right: 1px solid #e5e7eb;
    color: #1f2937;
    vertical-align: middle;
}
.cell-red { background-color: #fce8e6 !important; color: #c5221f !important; font-weight: 600; }
.cell-yellow { background-color: #fef7e0 !important; color: #b06000 !important; font-weight: 600; }
.cell-green { background-color: #e6f4ea !important; color: #137333 !important; }
.cell-grey { background-color: #f1f3f4 !important; color: #5f6368 !important; }
.cell-norm { background-color: #ffffff !important; color: #1f2937 !important; }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# ДАННЫЕ СРЕЗОВ
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
                    "mhi_resp": 14,
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
            "enrolled": 18,
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
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =====================================================================
def render_kpi_card(title, value_str, subtitle, status_label, color_class, extra_badge=""):
    badge_html = f'<div style="margin-top:6px;"><span class="kpi-badge">{extra_badge}</span></div>' if extra_badge else ""
    card_html = (
        f'<div class="kpi-card {color_class}">'
        f'<div class="kpi-title">{title}</div>'
        f'<div class="kpi-value">{value_str}</div>'
        f'<div class="kpi-sub">{subtitle}</div>'
        f'<span class="kpi-badge">{status_label}</span>'
        f'{badge_html}'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)


def evaluate_macro_scenario(hi_core, cr_pct, a_task_pct, nps_val, nps_valid, no_show_pct, rubric_fail_pct, unconfirmed_pct, no_show_cnt, rubric_fail_cnt):
    task_fail_pct = 100.0 - a_task_pct

    if nps_valid:
        if hi_core >= 0.500 and cr_pct >= 65.0 and a_task_pct >= 75.0 and nps_val >= 50:
            return (
                "success",
                "🟢 Сбалансированный курс: студенты доходят до конца и успешно подтверждают навык на практике",
                (
                    f"Большинство зачисленных (**{hi_core*100:.1f}%**) не просто получают сертификат, а самостоятельно справляются с финальным проектом. "
                    f"Удержание (**{cr_pct:.1f}%**) и лояльность выпускников (**NPS {nps_val:+d}**) находятся в целевой зеленой зоне."
                ),
                (
                    "1. **Зафиксировать текущую версию программы** как рабочий эталон.\n"
                    "2. **Развивать трек задач со звездочкой** для наиболее сильных студентов."
                )
            )

        if cr_pct >= 65.0 and a_task_pct < 60.0 and (35 <= nps_val <= 60):
            return (
                "warning",
                "🟡 «Иллюзия доходимости»: студенты доходят до конца курса, но заваливают итоговый проект",
                (
                    f"Модули успешно проходят **{cr_pct:.1f}%** студентов, однако **{task_fail_pct:.1f}%** финалистов остаются без подтвержденного навыка:\n"
                    f"* **{no_show_cnt} чел. ({no_show_pct:.1f}%)** — дошли до финала, но даже не приступили к диплому.\n"
                    f"* **{rubric_fail_cnt} чел. ({rubric_fail_pct:.1f}%)** — сдали работу, но не прошли по критериям самостоятельности."
                ),
                (
                    "1. **Проверить причину потерь на дипломе:** усталость перед финалом (если не приступают) или резкий скачок сложности (если не проходят по баллам).\n"
                    "2. **Убрать «ведение за руку»:** проверить, не дают ли кураторы готовые решения в промежуточных ДЗ.\n"
                    "3. **Выровнять сложность** финального проекта относительно модульных практик."
                )
            )

        if cr_pct >= 65.0 and a_task_pct < 60.0 and nps_val > 60:
            return (
                "warning",
                "🟡 «Эмоциональная ловушка»: студенты в восторге от атмосферы, но почти половина не сдает итоговый проект",
                (
                    f"Выпускники ставят сверхвысокие оценки спикерам и заботе (**NPS {nps_val:+d}**), до финала доходят **{cr_pct:.1f}%**. "
                    f"Но реальный навык не сформирован у **{task_fail_pct:.1f}%** финалистов (**{unconfirmed_pct:.1f}%** от всех поступивших выпустились «вхолостую»):\n"
                    f"* **{no_show_cnt} чел. ({no_show_pct:.1f}%)** — не открыли дипломный проект.\n"
                    f"* **{rubric_fail_cnt} чел. ({rubric_fail_pct:.1f}%)** — не преодолели порог рубрикатора без подсказок."
                ),
                (
                    "1. **Исключить «зачеты за старание»** на промежуточных модулях — повысить строгость приемки ключевых ДЗ.\n"
                    "2. **Синхронизировать требования** между кураторами на курсе и независимыми ревьюерами диплома."
                )
            )

        if cr_pct >= 55.0 and a_task_pct < 60.0 and nps_val < 35:
            return (
                "error",
                "🔴 Кризис результата и ожиданий: финалисты не справляются с проектом и разочарованы обучением",
                (
                    f"Студенты доходят до конца программы (**{cr_pct:.1f}%**), но **{task_fail_pct:.1f}%** из них не могут защитить итоговую работу "
                    f"(не приступили: **{no_show_pct:.1f}%**, не прошли рубрикатор: **{rubric_fail_pct:.1f}%**), что обрушило лояльность (**NPS {nps_val:+d}**)."
                ),
                (
                    "1. **Приоритет P1:** На вкладке «Разбор по модулям» найти модуль, где возник разрыв между теорией и практикой.\n"
                    "2. **Проверить прозрачность и посильность** требований дипломного проекта.\n"
                    "3. **Провести поддерживающий практикум** для выпускников текущего среза."
                )
            )

        if cr_pct < 55.0 and a_task_pct >= 75.0 and nps_val < 50:
            return (
                "warning",
                "🟡 «Синдром жесткого фильтра»: выжившие сдают проект отлично, но курс теряет почти половину людей по дороге",
                (
                    f"Те, кто дошел до финала, успешно защищают диплом (**{a_task_pct:.1f}%**), однако по ходу обучения отсеивается **{100.0 - cr_pct:.1f}%** потока, "
                    f"что негативно сказывается на оценке курса (**NPS {nps_val:+d}**)."
                ),
                (
                    "1. **Найти «модуль-убийцу»** с резким скачком отсева и спешки на вкладке «Разбор по модулям».\n"
                    "2. **Разгрузить пиковые недели** или добавить адаптивную поддержку на сложном переходе."
                )
            )

        if hi_core < 0.300 and cr_pct < 55.0 and a_task_pct < 60.0 and nps_val < 35:
            return (
                "error",
                "🔴 Системный кризис программы: высокий отсев по ходу курса и провал на финальной защите",
                (
                    f"До финала доходит менее половины потока (**{cr_pct:.1f}%**), а итоговый навык подтверждают лишь **{hi_core*100:.1f}%** от поступивших "
                    f"при критически низком **NPS ({nps_val:+d})**."
                ),
                (
                    "1. **Приоритет P0:** Приостановить масштабирование трафика на программу.\n"
                    "2. **Пересобрать проблемные модули** и сверить входные требования с реальным профилем новичков."
                )
            )

    issues = []
    actions = []
    if cr_pct < 65.0:
        issues.append(f"* **Удержание требует внимания ({cr_pct:.1f}%):** до финала не доходят {100.0 - cr_pct:.1f}% студентов.")
        actions.append("1. **По удержанию:** проверить модули с повышенным отсевом и числом должников на вкладке «Разбор по модулям».")
    if a_task_pct < 75.0:
        issues.append(
            f"* **Просадка на итоговом проекте (сдали {a_task_pct:.1f}% финалистов):** "
            f"{no_show_cnt} чел. ({no_show_pct:.1f}%) не приступили к диплому, {rubric_fail_cnt} чел. ({rubric_fail_pct:.1f}%) не прошли по критериям."
        )
        actions.append("2. **По итоговому проекту:** проверить плавность перехода от модульных задач к диплому и критерии рубрикатора.")
    if nps_valid and nps_val < 50:
        issues.append(f"* **Умеренная или сниженная лояльность (NPS {nps_val:+d}):** есть точечное недовольство опытом обучения.")
        actions.append("3. **По лояльности:** посмотреть, на каком модуле просели оценки контента, спикеров или скорости проверки (вкладка 3).")
    if not nps_valid:
        issues.append("* **Мало данных по лояльности (NPS):** недостаточно ответов выпускников для оценки (нужно ≥ 15 ответов и охват ≥ 50%).")
        actions.append("3. **По опросу выпускников:** повысить долю заполнения финальной анкеты.")

    if not issues:
        issues.append("* Все показатели находятся вблизи целевых ориентиров.")
        actions.append("1. Продолжать плановый мониторинг следующих потоков.")

    return (
        "info",
        "ℹ️ Показатели курса в переходной зоне: требуется точечная доработка отдельных этапов",
        "\n".join(issues),
        "\n".join(actions)
    )


def diagnose_module_human(pm, avg_course_drop):
    drop = pm["drop_rate"]
    lag = pm["lagging_rate"]
    loop = pm["loop_fail"]
    mhi_valid = pm["mhi_valid"]
    rushed = pm["rushed"]
    slow = pm["slow"]
    frag = pm["frag"]
    depl = pm["depl"]

    lms_red = (drop > 15.0) or (drop - avg_course_drop > 10.0) or (loop > 20.0)
    lms_yellow = (10.0 < drop <= 15.0) or (lag > 20.0) or (15.0 < loop <= 20.0)

    mhi_red = mhi_valid and ((rushed > 30.0) or (frag > 20.0) or (depl > 25.0))
    mhi_yellow = mhi_valid and ((25.0 < rushed <= 30.0) or (15.0 < frag <= 20.0) or (slow > 20.0))

    is_red = lms_red or mhi_red
    is_yellow = (not is_red) and (lms_yellow or mhi_yellow)
    is_problem = is_red or is_yellow

    triggered_signals = []
    if drop > 15.0 or (drop - avg_course_drop > 10.0):
        triggered_signals.append(
            f"🔴 **Высокий отсев на модуле: {drop:.1f}%** (ушли {pm['dropped_official']} чел. официально + {pm['dropped_inactive']} чел. перестали заходить > 14 дней)."
        )
    elif drop > 10.0:
        triggered_signals.append(f"🟡 **Повышенный отсев: {drop:.1f}%** (норма ≤ 10%).")

    if lag > 20.0:
        triggered_signals.append(f"🟡 **Много задолжников в досдаче: {lag:.1f}%** группы еще не закрыли практику (норма ≤ 20%).")

    if loop > 20.0:
        triggered_signals.append(f"🔴 **Массовые тупики на практике: {loop:.1f}%** студентов совершили 3+ неудачных попыток подряд (норма ≤ 15%).")
    elif loop > 15.0:
        triggered_signals.append(f"🟡 **Затруднения в практике: {loop:.1f}%** студентов сделали 3+ ошибки подряд (норма ≤ 15%).")

    if not mhi_valid:
        triggered_signals.append(
            f"⚪ **Мало ответов в опросе модуля:** ответили {pm['m_resp']} из {pm['n_active']} чел. ({pm['mhi_resp_rate']:.0f}%). Выводы строятся только по логам LMS."
        )
    else:
        if frag > 20.0:
            triggered_signals.append(f"🔴 **Разрыв теории и практики (Хаос): {frag:.1f}%** студентов не понимают, как применить лекцию к ДЗ (норма ≤ 15%).")
        elif frag > 15.0:
            triggered_signals.append(f"🟡 **Теряется связь урока и практики: {frag:.1f}%** жалоб на несвязность (норма ≤ 15%).")

        if rushed > 30.0:
            triggered_signals.append(f"🔴 **Острая нехватка времени (Спешка): {rushed:.1f}%** группы не укладываются в ритм недели (норма ≤ 25%).")
        elif rushed > 25.0:
            triggered_signals.append(f"🟡 **Плотный темп (Спешка): {rushed:.1f}%** студентов отмечают нехватку времени (норма ≤ 25%).")

        if depl > 25.0:
            triggered_signals.append(f"🔴 **Накопленное истощение: {depl:.1f}%** студентов заканчивают модуль без сил (норма ≤ 25%).")

        if slow > 20.0:
            triggered_signals.append(f"🟡 **Слишком простой темп (Скука): {slow:.1f}%** студентов считают материал слишком медленным (норма ≤ 20%).")

    diagnoses = []
    actions = []

    if (mhi_valid and frag > 15.0) or (loop > 15.0):
        diagnoses.append("**Отрыв домашнего задания от лекции или сбой проверки**")
        actions.extend([
            "Проверить корректность автотестов и тренажера на задании.",
            "Сверить терминологию лекции с условиями ДЗ.",
            "Добавить перед заданием разбор типового примера (worked example) и стартовый шаблон."
        ])

    if mhi_valid and rushed > 25.0 and frag <= 15.0:
        diagnoses.append("**Перегруз объемом материала и рутиной**")
        actions.extend([
            "Сопоставить расчетное время уроков и ДЗ с реальным временем прохождения в LMS.",
            "Вынести второстепенную теорию в необязательные (дополнительные) материалы.",
            "Сократить однотипные механические операции в домашнем задании."
        ])

    if mhi_valid and depl > 25.0 and frag <= 15.0:
        diagnoses.append("**Накопленная усталость от нескольких сложных тем подряд**")
        actions.extend([
            "Проверить плотность соседних модулей: идут ли подряд несколько тяжелых тем без передышки.",
            "Добавить буферную неделю или облегчить практику перед финальным рывком."
        ])

    if (drop > 10.0 or lag > 20.0) and loop <= 15.0 and (not mhi_valid or (rushed <= 25.0 and frag <= 15.0 and depl <= 25.0)):
        diagnoses.append("**Скрытый барьер внутри модуля (у тех, кто остановился до опроса)**")
        actions.extend([
            "Посмотреть по логам LMS, на каком именно шаге остановились ушедшие студенты (на установке ПО/окружения или на задании).",
            "Проверить комментарии к модулю на жалобы по настройке софта и доступов."
        ])

    if mhi_valid and slow > 20.0:
        diagnoses.append("**Материал слишком прост для части аудитории с опытом**")
        actions.append("Добавить возможность досрочной сдачи базовых шагов (экстернат) и задачи «со звездочкой».")

    if not mhi_valid and not actions:
        diagnoses.append("**Недостаточно ответов в опросе для оценки состояния группы**")
        actions.append("Опираться на объективные показатели сдачи ДЗ и проверить доходимость до конца модуля.")

    unique_actions = list(dict.fromkeys(actions))
    summary_label = " + ".join([d.replace("**", "") for d in diagnoses]) if diagnoses else "Штатный модуль без отклонений"
    if is_red:
        header_icon = "🔴"
    elif is_yellow:
        header_icon = "🟡"
    else:
        header_icon = "🟢" if mhi_valid else "⚪"

    return is_problem, header_icon, summary_label, triggered_signals, unique_actions


# =====================================================================
# САЙДБАР И УПРАВЛЕНИЕ СРЕЗОМ
# =====================================================================
st.sidebar.title("🧭 Выбор среза данных")
selected_slice_name = st.sidebar.selectbox(
    "Анализируемый срез потоков:",
    options=list(slices_data.keys()),
    index=0
)

current_slice = slices_data[selected_slice_name]
enrolled_n = current_slice["enrolled"]

st.sidebar.markdown("---")
st.sidebar.subheader("📏 Достаточность данных")
if enrolled_n >= 30:
    st.sidebar.success(f"✅ Данных достаточно: **{enrolled_n} чел.** (минимум 30)")
else:
    st.sidebar.warning(f"⏳ Идет набор данных: **{enrolled_n} из 30 чел.**")
    st.sidebar.progress(enrolled_n / 30.0)

st.sidebar.markdown(f"**Версия программы:** `{current_slice['version']}`")
if current_slice["anomaly_cohort"]:
    st.sidebar.info(f"⚡ Зафиксирован локальный сбой {current_slice['anomaly_cohort']} (отклонение > 20 п.п. от соседних потоков).")

st.title("📊 Диагностика качества образовательного курса")
st.caption(f"Выбранный срез: **{selected_slice_name}**")

# =====================================================================
# ЗАЩИТА ОТ МАЛЫХ ВЫБОРОК (Enrolled < 30)
# =====================================================================
if enrolled_n < 30:
    st.warning(
        f"🔒 **Идет накопление выборки (собрано {enrolled_n} из 30). "
        "Стратегическая аналитика курса защищена от шума малых групп.**"
    )
    st.stop()


# =====================================================================
# ВКЛАДКИ
# =====================================================================
tab1, tab2, tab3 = st.tabs([
    "🌐 1. Итоги курса",
    "🔬 2. Разбор по модулям",
    "🤝 3. Сервис и спикеры"
])


# ---------------------------------------------------------------------
# ВКЛАДКА 1: ИТОГИ КУРСА
# Порядок: 1. Главные показатели -> 2. Диагноз -> 3. Динамика и воронка
# ---------------------------------------------------------------------
with tab1:
    finished = current_slice["finished"]
    attempted = current_slice["attempted_task"]
    passed = current_slice["passed_task"]
    nps = current_slice["nps"]
    nps_resp = current_slice["nps_respondents"]
    anomaly_flag = f"⚡ Локальная аномалия {current_slice['anomaly_cohort']}" if current_slice["anomaly_cohort"] else ""

    cr = finished / enrolled_n
    a_task = passed / finished if finished > 0 else 0.0
    hi_core = passed / enrolled_n

    no_show_cnt = finished - attempted
    rubric_fail_cnt = attempted - passed
    task_fail_rate = (finished - passed) / finished if finished > 0 else 0.0
    no_show_rate = no_show_cnt / finished if finished > 0 else 0.0
    rubric_fail_rate = rubric_fail_cnt / finished if finished > 0 else 0.0
    unconfirmed_share = (finished - passed) / enrolled_n

    nps_coverage = (nps_resp / finished * 100.0) if finished > 0 else 0.0
    nps_valid = (nps_resp >= 15) and (nps_coverage >= 50.0)

    cr_pct = cr * 100.0
    at_pct = a_task * 100.0

    # --- 1. ГЛАВНЫЕ ПОКАЗАТЕЛИ КУРСА ---
    st.subheader("Главные показатели курса")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if hi_core >= 0.500:
            hi_cls, hi_lbl = "bg-green", "🟢 В норме (≥ 50%)"
        elif hi_core >= 0.300:
            hi_cls, hi_lbl = "bg-yellow", "🟡 Зона внимания (30–49.9%)"
        else:
            hi_cls, hi_lbl = "bg-red", "🔴 Критично (< 30%)"
        render_kpi_card(
            "Выпуск с навыком (HI_core)",
            f"{hi_core*100:.1f}% ({hi_core:.3f})",
            f"Сдали проект: {passed} из {enrolled_n} поступивших",
            hi_lbl, hi_cls, anomaly_flag
        )

    with c2:
        if cr_pct >= 65.0:
            cr_cls, cr_lbl = "bg-green", "🟢 В норме (≥ 65%)"
        elif cr_pct >= 55.0:
            cr_cls, cr_lbl = "bg-yellow", "🟡 Умеренная (55–64.9%)"
        else:
            cr_cls, cr_lbl = "bg-red", "🔴 Низкая (< 55%)"
        render_kpi_card(
            "Доходимость до финала (CR)",
            f"{cr_pct:.1f}%",
            f"Дошли до конца: {finished} из {enrolled_n} чел.",
            cr_lbl, cr_cls, anomaly_flag
        )

    with c3:
        if at_pct >= 75.0:
            at_cls, at_lbl = "bg-green", "🟢 В норме (≥ 75%)"
        elif at_pct >= 60.0:
            at_cls, at_lbl = "bg-yellow", "🟡 Умеренная (60–74.9%)"
        else:
            at_cls, at_lbl = "bg-red", "🔴 Низкая (< 60%)"
        small_fin_badge = "⚠️ Малая база финалистов (< 20)" if finished < 20 else anomaly_flag
        render_kpi_card(
            "Сдача итогового проекта (A_task)",
            f"{at_pct:.1f}%",
            f"Защитили: {passed} из {finished} финалистов (отправили: {attempted})",
            at_lbl, at_cls, small_fin_badge
        )

    with c4:
        if not nps_valid:
            nps_cls, nps_lbl = "bg-grey", "⚪ Мало ответов (< 15 или охват < 50%)"
        elif nps >= 50:
            nps_cls, nps_lbl = "bg-green", "🟢 Высокая лояльность (≥ 50)"
        elif nps >= 35:
            nps_cls, nps_lbl = "bg-yellow", "🟡 Умеренная (35–49)"
        else:
            nps_cls, nps_lbl = "bg-red", "🔴 Низкая (< 35)"
        render_kpi_card(
            "Лояльность выпускников (NPS)",
            f"{nps:+d}" if nps_valid else f"{nps:+d} (⚪)",
            f"Ответили: {nps_resp} из {finished} финалистов ({nps_coverage:.0f}%)",
            nps_lbl, nps_cls
        )

    st.markdown("---")

    # --- 2. ДИАГНОЗ И ПЛАН ДЕЙСТВИЙ ПО КУРСУ ---
    alert_type, headline_verdict, essence_text, actions_text = evaluate_macro_scenario(
        hi_core, cr_pct, at_pct, nps, nps_valid,
        no_show_rate * 100.0, rubric_fail_rate * 100.0, unconfirmed_share * 100.0,
        no_show_cnt, rubric_fail_cnt
    )

    st.subheader("Диагноз и план действий по курсу")
    if alert_type == "success":
        st.success(f"**{headline_verdict}**")
    elif alert_type == "warning":
        st.warning(f"**{headline_verdict}**")
    elif alert_type == "error":
        st.error(f"**{headline_verdict}**")
    else:
        st.info(f"**{headline_verdict}**")

    g1, g2 = st.columns(2)
    with g1:
        with st.container(border=True):
            st.markdown("##### 📍 В чем суть ситуации")
            st.markdown(essence_text)
    with g2:
        with st.container(border=True):
            st.markdown("##### 🛠️ Что сделать команде курса")
            st.markdown(actions_text)

    st.markdown("---")

    # --- 3. ДИНАМИКА И ВОРОНКА НАВЫКА ---
    col_b, col_v = st.columns([1.15, 1.0])

    with col_b:
        st.subheader("Динамика результатов от среза к срезу")
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
            x=x_labels, y=at_series, name="Сдача проекта (A_task)",
            marker_color="#4ECDC4", text=[f"{v*100:.1f}%" for v in at_series], textposition="auto"
        ))
        fig_dyn.add_trace(go.Scatter(
            x=x_labels, y=hi_series, name="Выпуск с навыком (HI_core)",
            mode="lines+markers+text",
            text=[f"{v*100:.1f}%" for v in hi_series], textposition="top center",
            line=dict(color="#1F2937", width=3.5),
            marker=dict(size=9, color="#1F2937")
        ))
        fig_dyn.add_hline(
            y=0.50, line_dash="dash", line_color="#2E7D32",
            annotation_text="Целевой выпуск ≥ 50%", annotation_position="top left"
        )
        fig_dyn.add_hline(
            y=0.30, line_dash="dash", line_color="#C62828",
            annotation_text="Критическая граница = 30%", annotation_position="bottom left"
        )
        fig_dyn.update_layout(
            barmode="group",
            yaxis=dict(title="Доля студентов", range=[0, 1.05], tickformat=".0%"),
            xaxis=dict(title="Последовательные срезы потоков"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=360,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor="white"
        )
        st.plotly_chart(fig_dyn, use_container_width=True)

    with col_v:
        st.subheader("Воронка навыка: дошли до конца vs защитили проект")
        hi_bar_color = "#34A853" if at_pct >= 75.0 else ("#FBBC04" if at_pct >= 60.0 else "#EA4335")

        fig_funnel = go.Figure()
        fig_funnel.add_trace(go.Bar(
            y=["Дошли и защитили проект", "Просто дошли до финала"],
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
            xaxis=dict(title="% от всех поступивших на курс", range=[0, 100]),
            height=210,
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor="white"
        )
        st.plotly_chart(fig_funnel, use_container_width=True)

        st.markdown(
            f"* **Не защитили диплом среди финалистов:** `{task_fail_rate*100:.1f}%` ({finished - passed} чел.) — "
            f"из них **{no_show_cnt} чел. ({no_show_rate*100:.1f}%)** не приступили к работе, "
            f"а **{rubric_fail_cnt} чел. ({rubric_fail_rate*100:.1f}%)** не прошли по критериям.\n"
            f"* **Доля «холостого выпуска» от поступивших:** `{unconfirmed_share*100:.1f}%` (дошли до конца без подтверждения навыка)."
        )


# ---------------------------------------------------------------------
# ВКЛАДКА 2: РАЗБОР ПО МОДУЛЯМ
# Порядок: 1. Сводная карта -> 2. Воронка -> 3. Обзор модулей
# ---------------------------------------------------------------------
with tab2:
    modules_raw = current_slice["modules"]
    processed_modules = []

    for m in modules_raw:
        s_started = m["started"]
        p_paused = m["paused"]
        n_active = s_started - p_paused
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
            title_display += " ⚠️ Малая база (n < 15)"

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

    # --- 1. СВОДНАЯ КАРТА ПРОХОЖДЕНИЯ МОДУЛЕЙ ---
    st.subheader("Сводная карта прохождения модулей")
    st.caption(
        "Цветом подсвечены только те ячейки, где показатель вышел за пределы нормы. "
        "Наведите курсор на ячейку «Отсев и досдача», чтобы увидеть число официальных отчислений и ушедших по неактивности."
    )

    html_rows = []
    for pm in processed_modules:
        if pm["drop_rate"] > 15.0 or (pm["drop_rate"] - avg_course_drop > 10.0):
            drop_cls = "cell-red"
        elif pm["drop_rate"] > 10.0 or pm["lagging_rate"] > 20.0:
            drop_cls = "cell-yellow"
        else:
            drop_cls = "cell-norm"

        drop_tooltip = (
            f"Активная база n = {pm['n_active']} чел. | "
            f"Официальные отчисления: {pm['dropped_official']} чел. | "
            f"Неактивность > 14 дн.: {pm['dropped_inactive']} чел."
        )

        if not pm["mhi_valid"]:
            rushed_cell = f'<td class="cell-grey">⚪ Мало данных ({pm["rushed"]:.1f}%)</td>'
            slow_cell = f'<td class="cell-grey">⚪ Мало данных ({pm["slow"]:.1f}%)</td>'
            frag_cell = f'<td class="cell-grey">⚪ Мало данных ({pm["frag"]:.1f}%)</td>'
            depl_cell = f'<td class="cell-grey">⚪ Мало данных ({pm["depl"]:.1f}%)</td>'
        else:
            r_cls = "cell-red" if pm["rushed"] > 30.0 else ("cell-yellow" if pm["rushed"] > 25.0 else "cell-norm")
            s_cls = "cell-yellow" if pm["slow"] > 20.0 else "cell-norm"
            f_cls = "cell-red" if pm["frag"] > 20.0 else ("cell-yellow" if pm["frag"] > 15.0 else "cell-norm")
            d_cls = "cell-red" if pm["depl"] > 25.0 else "cell-norm"

            rushed_cell = f'<td class="{r_cls}">{pm["rushed"]:.1f}%</td>'
            slow_cell = f'<td class="{s_cls}">{pm["slow"]:.1f}%</td>'
            frag_cell = f'<td class="{f_cls}">{pm["frag"]:.1f}%</td>'
            depl_cell = f'<td class="{d_cls}">{pm["depl"]:.1f}%</td>'

        l_cls = "cell-red" if pm["loop_fail"] > 20.0 else ("cell-yellow" if pm["loop_fail"] > 15.0 else "cell-norm")

        row_str = (
            f'<tr>'
            f'<td class="cell-norm" style="font-weight:600;">{pm["title_display"]}</td>'
            f'<td class="cell-norm"><b>{pm["cor_mod"]:.1f}%</b> <span style="color:#4b5563; font-size:0.8rem;">(дошли: {pm["s_started"]} из {enrolled_n}, пауза: {pm["p_paused"]})</span></td>'
            f'<td class="{drop_cls}" title="{drop_tooltip}">Отсев: {pm["drop_rate"]:.1f}% | В досдаче: {pm["lagging_rate"]:.1f}% ℹ️</td>'
            f'<td class="cell-norm">{pm["mhi_resp_rate"]:.0f}% ({pm["m_resp"]}/{pm["n_active"]})</td>'
            f'{rushed_cell}{slow_cell}{frag_cell}{depl_cell}'
            f'<td class="{l_cls}">{pm["loop_fail"]:.1f}%</td>'
            f'</tr>'
        )
        html_rows.append(row_str)

    table_html = (
        '<div class="custom-table-wrap"><table class="custom-table">'
        '<thead><tr>'
        '<th>Модуль курса</th>'
        '<th>Дошли до модуля</th>'
        '<th>Отсев и досдача на шаге</th>'
        '<th>Охват опроса</th>'
        '<th>Спешат (норма ≤25%)</th>'
        '<th>Скучают (норма ≤20%)</th>'
        '<th>Не видят связи (норма ≤15%)</th>'
        '<th>Истощены (норма ≤25%)</th>'
        '<th>3+ ошибки подряд (норма ≤15%)</th>'
        '</tr></thead>'
        f'<tbody>{"".join(html_rows)}</tbody>'
        '</table></div>'
    )
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("---")

    # --- 2. ВОРОНКА УДЕРЖАНИЯ ---
    st.subheader("Воронка удержания студентов от модуля к модулю")
    fig_dropoff = go.Figure()
    fig_dropoff.add_trace(go.Bar(
        x=[pm["title_display"] for pm in processed_modules],
        y=[pm["cor_mod"] for pm in processed_modules],
        text=[f"Дошли: {pm['cor_mod']:.1f}% (Отсев шага: {pm['drop_rate']:.1f}%)" for pm in processed_modules],
        textposition="auto",
        marker=dict(
            color=[pm["drop_rate"] for pm in processed_modules],
            colorscale=[[0.0, "#4A90E2"], [0.5, "#F5A623"], [1.0, "#D0021B"]],
            cmin=0, cmax=25,
            colorbar=dict(title="Отсев шага (%)")
        )
    ))
    fig_dropoff.add_hline(
        y=65.0, line_dash="dash", line_color="#137333",
        annotation_text="Целевое удержание к финалу (65%)", annotation_position="top right"
    )
    fig_dropoff.update_layout(
        yaxis=dict(title="% студентов от старта курса", range=[0, 108]),
        xaxis=dict(title="Модули программы"),
        height=330,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor="white"
    )
    st.plotly_chart(fig_dropoff, use_container_width=True)

    st.markdown("---")

    # --- 3. ОБЗОР МОДУЛЕЙ (ДИАГНОЗЫ И ДЕЙСТВИЯ ПО ПРОБЛЕМНЫМ МОДУЛЯМ) ---
    st.subheader("Обзор модулей: где сбоит программа и что нужно исправить")

    problem_cards = []
    normal_cards = []

    for pm in processed_modules:
        is_prob, icon, summary_lbl, trig_list, act_list = diagnose_module_human(pm, avg_course_drop)
        item_tuple = (pm, icon, summary_lbl, trig_list, act_list)
        if is_prob:
            problem_cards.append(item_tuple)
        else:
            normal_cards.append(item_tuple)

    if not problem_cards:
        st.success("🟢 **Все модули курса проходят штатно!** Критических скачков отсева, перегруза или тупиков в практике не обнаружено.")
    else:
        st.caption(f"Обнаружены отклонения в **{len(problem_cards)} из {len(processed_modules)}** модулей курса (раскрыты ниже):")
        for pm, icon, summary_lbl, trig_list, act_list in problem_cards:
            with st.expander(f"{icon} {pm['title_display']} — {summary_lbl}", expanded=True):
                if pm["cohort_outlier"]:
                    st.info("⚡ **Локальный выброс в 1 потоке:** проблема проявилась только в одной группе среза. Сначала проверьте расписание и работу куратора в этом потоке, прежде чем переписывать контент.")
                col_sig, col_act = st.columns([1.0, 1.2])
                with col_sig:
                    st.markdown("**🚩 Что пошло не так (сработавшие сигналы):**")
                    for sig in trig_list:
                        st.markdown(f"* {sig}")
                with col_act:
                    st.markdown("**🛠️ Что проверить и сделать:**")
                    for idx_a, act in enumerate(act_list, 1):
                        st.markdown(f"{idx_a}. {act}")

    if normal_cards:
        with st.expander(f"🟢 Показать модули без отклонений ({len(normal_cards)} шт.)", expanded=False):
            for pm, icon, summary_lbl, trig_list, _ in normal_cards:
                extra_note = f" — *{trig_list[0]}*" if trig_list else " — *все показатели отсева и самочувствия в норме.*"
                st.markdown(f"* **{icon} {pm['title_display']}** (удержание `{pm['cor_mod']:.1f}%`, отсев шага `{pm['drop_rate']:.1f}%`){extra_note}")


# ---------------------------------------------------------------------
# ВКЛАДКА 3: СЕРВИС И СПИКЕРЫ (CSI)
# ---------------------------------------------------------------------
with tab3:
    u_resp = current_slice["u_resp"]
    u_coverage = (u_resp / enrolled_n * 100.0) if enrolled_n > 0 else 0.0
    t2_u = current_slice["top2_unique"]

    csi_content = (t2_u["q4"] + t2_u["q5"] + t2_u["q6"]) / 3.0
    csi_expert = t2_u["q7"]
    csi_care = (t2_u["q8"] + t2_u["q9"]) / 2.0

    st.subheader("Оценка работы команд по курсу в целом (доля оценок 4 и 5)")
    sc1, sc2, sc3 = st.columns(3)

    cov_sub = f"Охват опроса: {u_coverage:.1f}% ({u_resp} уникальных студентов)"

    with sc1:
        if u_resp < 15:
            c_cls, c_lbl = "bg-grey", "⚪ Мало данных (< 15 отв.)"
        elif csi_content >= 85.0:
            c_cls, c_lbl = "bg-green", "🟢 В норме (≥ 85%)"
        elif csi_content >= 75.0:
            c_cls, c_lbl = "bg-yellow", "🟡 Зона внимания (75–84.9%)"
        else:
            c_cls, c_lbl = "bg-red", "🔴 Нужна доработка (< 75%)"
        render_kpi_card(
            "Контент и задания (Методисты и авторы)",
            f"{csi_content:.1f}%",
            cov_sub,
            c_lbl, c_cls
        )

    with sc2:
        if u_resp < 15:
            e_cls, e_lbl = "bg-grey", "⚪ Мало данных (< 15 отв.)"
        elif csi_expert >= 88.0:
            e_cls, e_lbl = "bg-green", "🟢 В норме (≥ 88%)"
        elif csi_expert >= 80.0:
            e_cls, e_lbl = "bg-yellow", "🟡 Зона внимания (80–87.9%)"
        else:
            e_cls, e_lbl = "bg-red", "🔴 Нужна проверка (< 80%)"
        render_kpi_card(
            "Преподаватели и вебинары (ОРЭ)",
            f"{csi_expert:.1f}%",
            cov_sub,
            e_lbl, e_cls
        )

    with sc3:
        if u_resp < 15:
            k_cls, k_lbl = "bg-grey", "⚪ Мало данных (< 15 отв.)"
        elif csi_care >= 88.0:
            k_cls, k_lbl = "bg-green", "🟢 В норме (≥ 88%)"
        elif csi_care >= 80.0:
            k_cls, k_lbl = "bg-yellow", "🟡 Зона внимания (80–87.9%)"
        else:
            k_cls, k_lbl = "bg-red", "🔴 Нужна проверка (< 80%)"
        render_kpi_card(
            "Кураторы и поддержка (Служба заботы)",
            f"{csi_care:.1f}%",
            cov_sub,
            k_lbl, k_cls
        )

    st.markdown("---")

    st.subheader("Рейтинг удовлетворенности по каждому модулю")
    st.caption(
        "Показана доля довольных студентов (оценки 4 и 5 из 5). "
        "Значок 📉 отмечает резкое падение оценки (на ≥ 15 п.п. к прошлому модулю). Наведите курсор на ячейку, чтобы увидеть долю негатива (оценки 1–2)."
    )

    csi_rows_html = []
    prev_mod_valid = False
    prev_top2 = {}

    for m in modules_raw:
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
                c_cls = "cell-grey"
                val_str = f"⚪ Мало данных ({t2:.1f}%)"
            else:
                drop_alert = ""
                if prev_mod_valid and (prev_top2.get(qk, t2) - t2 >= 15.0):
                    diff = prev_top2[qk] - t2
                    drop_alert = f' <span style="color:#c5221f; font-weight:700;">📉 -{diff:.1f} п.п.</span>'

                green_thr = 85.0 if is_content else 88.0
                yellow_thr = 75.0 if is_content else 80.0

                if t2 < yellow_thr or b2 > 15.0:
                    c_cls = "cell-red"
                elif t2 < green_thr:
                    c_cls = "cell-yellow"
                else:
                    c_cls = "cell-green"

                val_str = f"{t2:.1f}%{drop_alert}"

            tooltip = f"Довольны (4-5): {t2:.1f}% | Недовольны (1-2): {b2:.1f}%"
            cells_html.append(f'<td class="{c_cls}" title="{tooltip}">{val_str}</td>')

        row_str = (
            f'<tr>'
            f'<td class="cell-norm" style="font-weight:600;">{m["name"]}</td>'
            f'{"".join(cells_html)}'
            f'<td class="cell-norm">{resp_rate:.0f}% ({m_resp}/{n_active})</td>'
            f'</tr>'
        )
        csi_rows_html.append(row_str)

        prev_mod_valid = cell_valid
        prev_top2 = m["csi_top2"]

    csi_table_html = (
        '<div class="custom-table-wrap"><table class="custom-table">'
        '<thead><tr>'
        '<th>Модуль программы</th>'
        '<th>Подача теории (норма ≥85%)</th>'
        '<th>Актуальность (норма ≥85%)</th>'
        '<th>Понятность ДЗ (норма ≥85%)</th>'
        '<th>Спикеры (норма ≥88%)</th>'
        '<th>Скорость ответов (норма ≥88%)</th>'
        '<th>Забота и эмпатия (норма ≥88%)</th>'
        '<th>Охват опроса</th>'
        '</tr></thead>'
        f'<tbody>{"".join(csi_rows_html)}</tbody>'
        '</table></div>'
    )
    st.markdown(csi_table_html, unsafe_allow_html=True)

    st.markdown("---")

    st.subheader("Открытые комментарии студентов: «Что стоит улучшить в модуле?»")
    module_filter_options = ["Все модули"] + [m["name"] for m in modules_raw]
    selected_mod_filter = st.selectbox("Показать комментарии по модулю:", options=module_filter_options)

    filtered_comments = []
    for m in modules_raw:
        if selected_mod_filter in ("Все модули", m["name"]):
            for txt in m["comments"]:
                filtered_comments.append((m["name"], txt))

    if not filtered_comments:
        st.info("По выбранному модулю/срезу нет текстовых комментариев.")
    else:
        for mod_title, comment_text in filtered_comments:
            with st.container(border=True):
                st.markdown(f"**{mod_title}**")
                st.write(comment_text)
