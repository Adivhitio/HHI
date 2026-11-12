"""Система метрик · прототип v1.0 по концепции (16).

Запуск: streamlit run app.py
Экспорт демоданных: python app.py --export-data synthetic_data.zip
Все расчёты и воспроизводимый генератор находятся в этом файле.
Доли внутри расчётов — 0..1; NPS — -100..100. Нули и пропуски различаются.
См. вкладку «Данные и правила» о явно принятых решениях реализации.
"""
from __future__ import annotations

import argparse
from datetime import date
from html import escape
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

AS_OF = pd.Timestamp("2026-11-12")
COLORS = {"green": "#157B62", "yellow": "#A66A09", "red": "#BD414B", "gray": "#748295"}
BG = {"green": "#E9F5EF", "yellow": "#FFF3DA", "red": "#FCEBEC", "gray": "#EDF0F4"}
ICONS = {"green": "🟢", "yellow": "🟡", "red": "🔴", "gray": "⚪"}
ZONES = {"green": "Целевая зона", "yellow": "Зона внимания", "red": "Зона риска", "gray": "Мало данных"}
QUESTIONS = {"q4": "В4 · Теория", "q5": "В5 · Актуальность", "q6": "В6 · Задания",
             "q7": "В7 · Эксперты", "q8": "В8 · Скорость", "q9": "В9 · Забота"}
MODULE_NAMES = ["Старт и инструменты", "Базовые приёмы", "Практика на кейсах",
                "Сложные задачи", "Сборка решения", "Финальный модуль"]
PROFILES = {
    "healthy": (.82, .88, .68, "Сбалансированный бенчмарк"),
    "illusion": (.82, .48, .46, "Иллюзия доходимости"),
    "emotional": (.85, .50, .78, "Эмоциональная ловушка"),
    "expectations": (.69, .47, .16, "Кризис результата и ожиданий"),
    "filter": (.42, .88, .42, "Синдром жёсткого фильтра"),
    "crisis": (.38, .43, .04, "Системный кризис"),
    "fallback": (.61, .68, .43, "Промежуточные показатели"),
    "low_nps": (.79, .83, .65, "Недостаточный охват NPS"),
    "small": (.50, .87, .65, "Малая база среза и модулей"),
    "local": (.83, .86, .62, "Локальная аномалия потока"),
    "service": (.80, .84, .43, "Сервисные проблемы"),
    "overload": (.78, .83, .55, "Скрытая перегрузка и усталость"),
    "low_mhi": (.30, .83, .55, "Низкий охват MHI"),
    "pending": (.81, .84, .62, "Открытые окна и незакрытая проверка"),
}
MACRO = {
    1: ("Сбалансированный бенчмарк", "green", "Планово", [
        "Зафиксировать версию программы как базовый эталон.",
        "Развивать факультативный трек сложных задач для сильных студентов."]),
    2: ("Иллюзия доходимости", "yellow", "Проверка результата", [
        "Сопоставить отказ от защиты и несдачу по рубрикатору: это разные причины потерь.",
        "Проверить избыточные подсказки в промежуточных ДЗ и скачок сложности диплома."]),
    3: ("Эмоциональная ловушка", "yellow", "Проверка результата", [
        "Проверить, не заменяет ли зачёт за старание независимую оценку навыка.",
        "Сопоставить критерии кураторов и независимых ревьюеров итогового проекта."]),
    4: ("Кризис результата и ожиданий", "red", "P1", [
        "Найти разрыв теории и практики через аудит модулей.",
        "Проверить ясность и адекватность требований проекта; подготовить поддерживающий практикум."]),
    5: ("Синдром жёсткого фильтра", "yellow", "Доступность обучения", [
        "Найти модуль с резким ростом отсева и спешки.",
        "Проверить входные требования, поддержку новичков и достаточность опорных примеров."]),
    6: ("Системный кризис программы", "red", "P0", [
        "Рассмотреть остановку масштабирования трафика до проверки причин.",
        "Проверить соответствие программы аудитории и пересобрать подтверждённые проблемные модули."]),
}


def ratio(a, b):
    return float(a) / float(b) if b else np.nan


def pct(x, digits=1):
    return "—" if pd.isna(x) else f"{x:.{digits}%}".replace(".", ",")


def high_zone(value, green, yellow, valid=True):
    if not valid or pd.isna(value):
        return "gray"
    return "green" if value >= green else "yellow" if value >= yellow else "red"


def low_zone(value, yellow, red=None, valid=True):
    if not valid or pd.isna(value):
        return "gray"
    if red is not None and value > red:
        return "red"
    return "yellow" if value > yellow else "green"


def csi_zone(top, bottom, question, valid):
    if not valid or pd.isna(top):
        return "gray"
    if bottom > .15:
        return "red"
    return high_zone(top, .85 if question in ("q4", "q5", "q6") else .88,
                     .75 if question in ("q4", "q5", "q6") else .80)


def _exact_flags(rng, size, rate):
    result = np.zeros(size, dtype=bool)
    result[rng.permutation(size)[:round(size * rate)]] = True
    return result


def generate_synthetic_data(seed=42, cohort_size=60):
    """Индивидуальные записи, а не заранее нарисованные значения KPI.

    14 срезов × 3 последовательных потока; в малом срезе 3 × 8 студентов.
    Статусы progress — снимки на cutoff (для незакрытых окон предварительные).
    Каждый продолжающий студент прошёл практику и обязательную анкету ранее.
    Точное квотирование держит основные демосценарии устойчивыми при смене seed.
    """
    rng = np.random.default_rng(int(seed))
    cohorts, modules, students, progress, pulse = [], [], [], [], []
    course_sequences = {}
    for index, (profile, (cr, a_task, nps_target, label)) in enumerate(PROFILES.items()):
        course = "Аналитик данных" if index < 10 else "Python-разработчик"
        version = "1.0" if index < 7 else "1.1" if index < 10 else "2.0"
        slice_id = f"S{index + 1:02d}"
        for c in range(3):
            seq_key = (course, version)
            course_sequences[seq_key] = course_sequences.get(seq_key, 0) + 1
            seq = course_sequences[seq_key]
            cid = f"{slice_id}-C{c + 1}"
            n = 8 if profile == "small" else int(cohort_size)
            start = AS_OF - pd.Timedelta(days=(len(PROFILES) - index) * 70 + 16 - c * 7)
            if profile == "pending":
                start = AS_OF - pd.Timedelta(days=[100, 80, 24][c])
            deadline = start + pd.Timedelta(days=63)
            reviews_closed = not (profile == "pending" and c in (1, 2))
            # В pending: C1 закрыт, C2 окончил, но работы на проверке, C3 ещё учится.
            cohorts.append(dict(cohort_id=cid, course=course, version=version, slice_id=slice_id,
                                slice_label=label, profile=profile, cohort_order=seq,
                                cohort_name=f"Поток {seq:02d}", start_date=start,
                                assessment_deadline=deadline, reviews_closed=reviews_closed))
            local_bad = profile == "local" and c == 2
            this_cr = .40 if local_bad else cr
            n_finished = round(n * this_cr)
            n_passed = round(n_finished * a_task)
            attempted_rate = min(.97, a_task + (.17 if profile in ("illusion", "emotional") else .24))
            n_attempted = max(n_passed, round(n_finished * attempted_rate))
            ids = [f"{cid}-U{i + 1:03d}" for i in range(n)]
            shuffled = list(rng.permutation(ids))
            final_ids = set(shuffled[:n_finished])
            attempt_ids = set(shuffled[:n_attempted])
            pass_ids = set(shuffled[:n_passed])
            response_count = round(n_finished * (.25 if profile == "low_nps" else .84))
            responder_ids = list(rng.permutation(list(sorted(final_ids))))[:response_count]
            detractors = round(response_count * .10)
            promoters = min(response_count - detractors, round(response_count * nps_target) + detractors)
            scores = list(rng.integers(9, 11, promoters)) + list(rng.integers(0, 7, detractors))
            scores += list(rng.integers(7, 9, response_count - len(scores)))
            rng.shuffle(scores)
            nps_by_id = dict(zip(responder_ids, scores))
            terminal = {}
            for sid in ids:
                if sid in final_ids:
                    terminal[sid] = 6
                elif profile in ("filter", "crisis", "low_mhi") or local_bad:
                    terminal[sid] = 3 if rng.random() < .85 else int(rng.choice([1, 2, 4, 5]))
                else:
                    terminal[sid] = int(rng.integers(1, 6))
                # Финальные результаты незрелого потока не существуют на дату снимка.
                ready_final = deadline <= AS_OF
                students.append(dict(student_id=sid, cohort_id=cid,
                                     final_attempted=bool(sid in attempt_ids and ready_final),
                                     final_passed=bool(sid in pass_ids and ready_final),
                                     nps=nps_by_id.get(sid, np.nan) if ready_final and reviews_closed else np.nan))
            for module_no, title in enumerate(MODULE_NAMES, 1):
                module_open = start + pd.Timedelta(days=(module_no - 1) * 7)
                module_deadline = start + pd.Timedelta(days=module_no * 7)
                cutoff = module_deadline + pd.Timedelta(days=14)
                modules.append(dict(cohort_id=cid, module_no=module_no, title=title,
                                    open_date=module_open, deadline=module_deadline, cutoff_date=cutoff,
                                    expert_id=f"EXP-{course[:1]}-{module_no}"))
                if module_open > AS_OF:
                    continue
                module_rows = []
                for sid in ids:
                    if terminal[sid] < module_no:
                        continue
                    continues = terminal[sid] > module_no
                    if continues or (module_no == 6 and sid in attempt_ids):
                        state = "passed"
                    elif module_no == 6:
                        state = str(rng.choice(["passed", "lagging", "dropped_inactive"], p=[.75, .18, .07]))
                    else:
                        choices = ["dropped_official", "dropped_inactive", "lagging", "paused", "passed"]
                        probs = [.20, .51, .12, .09, .08]
                        if profile == "low_mhi":
                            probs = [.15, .62, .13, .07, .03]
                        state = str(rng.choice(choices, p=probs))
                    module_rows.append(dict(student_id=sid, cohort_id=cid, module_no=module_no,
                                            state=state, loop_fail=False))
                    # Вход на следующий модуль требует заполненной анкеты.
                    answered = state == "passed" and (continues or sid in attempt_ids or rng.random() < .72)
                    if answered:
                        pulse.append(dict(student_id=sid, cohort_id=cid, module_no=module_no,
                                          pacing="normal", fragmented=False, depleted=False,
                                          **{q: 5 for q in QUESTIONS}, comment=""))
                active_indices = [i for i, row in enumerate(module_rows) if row["state"] != "paused"]
                loop_rate = .05
                if module_no == 3 and profile in ("illusion", "expectations", "crisis", "filter"):
                    loop_rate = .30
                if module_no == 3 and local_bad:
                    loop_rate = .42
                for idx in rng.permutation(active_indices)[:round(len(active_indices) * loop_rate)]:
                    module_rows[idx]["loop_fail"] = True
                progress.extend(module_rows)
    data = {"cohorts": pd.DataFrame(cohorts), "modules": pd.DataFrame(modules),
            "students": pd.DataFrame(students), "progress": pd.DataFrame(progress), "pulse": pd.DataFrame(pulse)}
    # Точное квотирование ответов внутри каждого потока и модуля.
    p = data["pulse"]
    for (cid, mod), group in p.groupby(["cohort_id", "module_no"], sort=False):
        cohort = data["cohorts"].set_index("cohort_id").loc[cid]
        profile = cohort["profile"]
        local_bad = profile == "local" and cid.endswith("C3")
        rushed, slow, fragmented, depleted = .12, .08, .06, .12
        if mod == 3 and profile in ("illusion", "expectations", "crisis", "filter"):
            fragmented, rushed = .30, .36
        if mod == 3 and local_bad:
            fragmented = .45
        if profile == "overload":
            if mod == 3:
                rushed = .42
            if mod in (4, 5):
                depleted = .38
            if mod == 2:
                slow = .30
        if profile == "low_mhi" and mod == 3:
            fragmented, depleted = .45, .48  # Серые значения не участвуют в гипотезах MHI.
        ix = group.index.to_numpy()
        perm = rng.permutation(ix)
        n_rushed, n_slow = round(len(ix) * rushed), round(len(ix) * slow)
        p.loc[perm[:n_rushed], "pacing"] = "rushed"
        p.loc[perm[n_rushed:n_rushed + n_slow], "pacing"] = "slow"
        p.loc[ix, "fragmented"] = _exact_flags(rng, len(ix), fragmented)
        p.loc[ix, "depleted"] = _exact_flags(rng, len(ix), depleted)
        for q in QUESTIONS:
            top, bottom = .94, .03
            if profile in ("illusion", "expectations", "crisis", "filter") and mod == 3 and q == "q6":
                top, bottom = .64, .21
            if local_bad and mod == 3 and q in ("q6", "q7"):
                top, bottom = .50, .30
            if profile == "service":
                if (mod == 2 and q == "q5") or (mod == 3 and q == "q7"):
                    top, bottom = .62, .22
                if mod == 4 and q in ("q8", "q9"):
                    top, bottom = .58, .27
            shuffled_ix = rng.permutation(ix)
            n_top, n_bottom = round(len(ix) * top), round(len(ix) * bottom)
            p.loc[ix, q] = 3
            p.loc[shuffled_ix[:n_top], q] = rng.integers(4, 6, n_top)
            p.loc[shuffled_ix[n_top:n_top + n_bottom], q] = rng.integers(1, 3, n_bottom)
        comments = ["Разобранный пример помог самостоятельно выполнить задание.",
                    "Хотелось бы больше задач повышенной сложности.", "Понятная последовательность и полезная обратная связь."]
        if fragmented > .20:
            comments = ["В задании используются термины, которых не было в теории.",
                        "Автотест выдаёт ошибку без пояснения. Нужен пример входных данных."]
        if profile == "service" and mod == 4:
            comments = ["Проверку ждал три дня; не понимал, когда получу ответ.",
                        "В отзыве перечислены ошибки, но неясно, как их исправить."]
        if profile == "service" and mod == 2:
            comments = ["Скриншоты относятся к старой версии инструмента."]
        if rushed > .30:
            comments += ["Содержание понятно, но на задание ушло гораздо больше времени, чем заявлено."]
        for idx in rng.permutation(ix)[:max(1, round(len(ix) * .12))]:
            p.loc[idx, "comment"] = str(rng.choice(comments))
    return data


@st.cache_data(show_spinner=False, max_entries=8)
def get_demo_data(seed, cohort_size):
    return generate_synthetic_data(seed, cohort_size)


def slice_cohorts(data, slice_id):
    result = data["cohorts"].loc[data["cohorts"]["slice_id"].eq(slice_id)].sort_values("cohort_order").copy()
    if result.empty:
        raise ValueError("Срез не найден")
    if len(result[["course", "version"]].drop_duplicates()) != 1:
        raise ValueError("Срез объединяет разные программы или версии")
    seq = result["cohort_order"].tolist()
    if seq != list(range(seq[0], seq[0] + len(seq))):
        raise ValueError("В срезе должны быть последовательные потоки одной версии")
    return result


def ready_cohorts(cohorts, as_of=AS_OF):
    """Только закрытый последовательный префикс: не перепрыгиваем через поток в проверке."""
    ready = cohorts["assessment_deadline"].le(as_of) & cohorts["reviews_closed"]
    return cohorts.loc[ready.cummin()].copy()


def course_metrics(data, cohort_ids):
    students = data["students"].loc[data["students"]["cohort_id"].isin(cohort_ids)]
    progress = data["progress"].loc[data["progress"]["cohort_id"].isin(cohort_ids)]
    finished_keys = set(zip(progress.loc[progress.module_no.eq(6), "cohort_id"],
                            progress.loc[progress.module_no.eq(6), "student_id"]))
    finished_mask = [(r.cohort_id, r.student_id) in finished_keys for r in students.itertuples()]
    finalists = students.loc[finished_mask]
    enrolled, finished = len(students), len(finalists)
    attempted, passed = int(finalists.final_attempted.sum()), int(finalists.final_passed.sum())
    nps_scores = finalists.nps.dropna()
    nps = 100 * ((nps_scores.ge(9).sum() - nps_scores.le(6).sum()) / len(nps_scores)) if len(nps_scores) else np.nan
    return dict(enrolled=enrolled, finished=finished, attempted=attempted, passed=passed,
                cr=ratio(finished, enrolled), a_task=ratio(passed, finished), hi=ratio(passed, enrolled),
                no_show=ratio(finished - attempted, finished), rubric_fail=ratio(attempted - passed, finished),
                task_fail=ratio(finished - passed, finished), unconfirmed=ratio(finished - passed, enrolled),
                nps=nps, nps_n=len(nps_scores), nps_rr=ratio(len(nps_scores), finished),
                nps_valid=len(nps_scores) >= 15 and ratio(len(nps_scores), finished) >= .5)


def macro_scenario(m):
    if m["enrolled"] < 30:
        return None
    # При <20 финалистах концепция разрешает предварительную оценку A_task.
    if not m["nps_valid"]:
        return None
    cr, a, hi, nps = (m[k] for k in ("cr", "a_task", "hi", "nps"))
    if hi >= .50 and cr >= .65 and a >= .75 and nps >= 50:
        return 1
    if cr >= .65 and a < .60 and 35 <= nps <= 60:
        return 2
    if cr >= .65 and a < .60 and nps > 60:
        return 3
    if cr >= .55 and a < .60 and nps < 35:
        return 4
    if cr < .55 and a >= .75 and nps < 50:
        return 5
    if hi < .30 and cr < .55 and a < .60 and nps < 35:
        return 6
    return None


def cohort_comparison(data, cohorts):
    rows = []
    for r in cohorts.itertuples():
        m = course_metrics(data, [r.cohort_id])
        rows.append(dict(cohort_id=r.cohort_id, name=r.cohort_name, **m))
    return pd.DataFrame(rows)


def isolated_course_anomalies(table):
    """Для >=3 потоков: ровно один отстоит >20 п.п. от каждого из остальных.
    Остальные должны иметь размах <=20 п.п. Два потока не локализуют виновника.
    """
    flags = []
    if len(table) < 3:
        return flags
    for metric in ("cr", "a_task"):
        valid = table.dropna(subset=[metric])
        if len(valid) < 3:
            continue
        candidates = []
        for ix, r in valid.iterrows():
            others = valid.drop(ix)[metric]
            if (abs(others - r[metric]) > .20 + 1e-10).all() and others.max() - others.min() <= .20 + 1e-10:
                candidates.append((r["name"], metric))
        if len(candidates) == 1:
            flags.extend(candidates)
    return flags


def module_stats(progress, pulse):
    started = len(progress)
    paused = int(progress.state.eq("paused").sum())
    active = progress.loc[~progress.state.eq("paused")]
    n = len(active)
    passed = int(active.state.eq("passed").sum())
    lagging = int(active.state.eq("lagging").sum())
    official = int(active.state.eq("dropped_official").sum())
    inactive = int(active.state.eq("dropped_inactive").sum())
    m = len(pulse)
    result = dict(started=started, paused=paused, n=n, passed=passed, lagging=lagging,
                  dropped=official + inactive, official=official, inactive=inactive,
                  loop_n=int(active.loop_fail.sum()), drop=ratio(official + inactive, n),
                  lag=ratio(lagging, n), loop=ratio(active.loop_fail.sum(), n), m=m, rr=ratio(m, n),
                  rushed=ratio(pulse.pacing.eq("rushed").sum(), m),
                  slow=ratio(pulse.pacing.eq("slow").sum(), m),
                  fragmented=ratio(pulse.fragmented.sum(), m), depleted=ratio(pulse.depleted.sum(), m))
    result["lms_valid"] = n >= 15
    result["mhi_valid"] = m >= 15 and result["rr"] >= .5
    for q in QUESTIONS:
        result[f"{q}_top"] = ratio(pulse[q].ge(4).sum(), m)
        result[f"{q}_bottom"] = ratio(pulse[q].le(2).sum(), m)
    return result


def module_metrics(data, cohorts, as_of=AS_OF):
    cohort_ids = cohorts.cohort_id.tolist()
    enrolled = len(data["students"].loc[data["students"].cohort_id.isin(cohort_ids)])
    modules = data["modules"].loc[data["modules"].cohort_id.isin(cohort_ids)]
    completed = set(cohorts.loc[cohorts.assessment_deadline.le(as_of) & cohorts.reviews_closed, "cohort_id"])
    rows, details = [], []
    for mod, meta in modules.groupby("module_no", sort=True):
        eligible = meta.loc[meta.cutoff_date.le(as_of) | meta.cohort_id.isin(completed), "cohort_id"].tolist()
        prog_all = data["progress"].loc[data["progress"].cohort_id.isin(cohort_ids) & data["progress"].module_no.eq(mod)]
        prog = prog_all.loc[prog_all.cohort_id.isin(eligible)]
        p = data["pulse"].loc[data["pulse"].cohort_id.isin(eligible) & data["pulse"].module_no.eq(mod)]
        row = dict(module_no=int(mod), title=meta.iloc[0].title, closed_cohorts=len(eligible),
                   total_cohorts=len(cohort_ids), started_total=len(prog_all), enrolled=enrolled,
                   cor=ratio(len(prog_all), enrolled), **module_stats(prog, p))
        rows.append(row)
        for cid in eligible:
            details.append(dict(module_no=int(mod), cohort_id=cid,
                                **module_stats(prog.loc[prog.cohort_id.eq(cid)], p.loc[p.cohort_id.eq(cid)])))
    table = pd.DataFrame(rows)
    per_cohort = pd.DataFrame(details)
    baseline = ratio(table.loc[table.lms_valid, "dropped"].sum(), table.loc[table.lms_valid, "n"].sum())
    table["course_drop"] = baseline
    table["local_anomaly"] = ""
    if not per_cohort.empty:
        for mod, group in per_cohort.groupby("module_no"):
            valid = group.loc[group.lms_valid]
            if len(valid) >= 3:
                flags = valid.apply(lambda r: any(z in ("red", "yellow") for z in module_zones(r, np.nan).values()), axis=1)
                if int(flags.sum()) == 1:
                    culprit = valid.loc[flags, "cohort_id"].iloc[0]
                    name = cohorts.set_index("cohort_id").loc[culprit, "cohort_name"]
                    table.loc[table.module_no.eq(mod), "local_anomaly"] = str(name)
    return table, per_cohort


def module_zones(r, course_drop=np.nan):
    lms, mhi = bool(r["lms_valid"]), bool(r["mhi_valid"])
    drop = low_zone(r["drop"], .10, .15, lms)
    if lms and not pd.isna(course_drop) and r["drop"] - course_drop >= .10 - 1e-10:
        drop = "red"
    return dict(drop=drop, lag=low_zone(r["lag"], .20, valid=lms),
                loop=low_zone(r["loop"], .15, .20, lms),
                rushed=low_zone(r["rushed"], .25, .30, mhi),
                slow=low_zone(r["slow"], .20, valid=mhi),
                fragmented=low_zone(r["fragmented"], .15, .20, mhi),
                depleted=low_zone(r["depleted"], .25, .25, mhi))


def module_insights(r):
    """Возвращает все применимые гипотезы; несколько причин могут сосуществовать."""
    if not r["lms_valid"]:
        return [(0, "Предварительное наблюдение", [
            "Накопить не менее 15 активных участников с закрытым окном cutoff. Системный диагноз пока не формируется."])]
    insights = []
    acute = r["drop"] > .15 or r["lag"] > .20
    phase = "острая фаза" if acute else "скрытое напряжение"
    valid = bool(r["mhi_valid"])
    if r["loop"] > .15 or (valid and r["fragmented"] > .15):
        insights.append((2, f"Разрыв сценария или сбой проверки · {phase}", [
            "Проверить тренажёр и автотесты на корректность.",
            "Сверить термины лекции и задания; добавить разобранный пример и стартовый шаблон."]))
    if valid:
        if r["rushed"] > .25 and r["fragmented"] <= .15:
            insights.append((3, f"Перегрузка объёмом · {phase}", [
                "Сопоставить плановый хронометраж с реальным временем прохождения.",
                "Вынести второстепенную теорию в опциональный блок; сократить однотипную рутину ДЗ."]))
        if r["depleted"] > .25 and r["fragmented"] <= .15:
            insights.append((4, "Накопление усталости", [
                "Проверить, не стоят ли несколько тяжёлых модулей подряд.",
                "Оценить буферную неделю, консолидацию знаний или облегчение практики на экваторе."]))
        normal = r["rushed"] <= .25 and r["fragmented"] <= .15 and r["depleted"] <= .25 and r["slow"] <= .20
        if (r["drop"] > .10 or r["lag"] > .20) and normal and r["loop"] <= .15:
            insights.append((5, "Барьер у не дошедших до опроса", [
                "Найти шаг остановки: установка ПО, доступы, окружение или практическое задание.",
                "Проверить комментарии В10 и сравнить петли ошибок у сдавших и остановившихся."]))
        if r["slow"] > .20 and r["drop"] <= .15:
            insights.append((6, "Обращение экспертизы · заниженный темп", [
                "Предусмотреть досрочную сдачу базовых шагов и факультативные задачи со звёздочкой."]))
        if not insights and normal and r["drop"] <= .10 and r["lag"] <= .20 and r["loop"] <= .15:
            insights.append((1, "Штатный модуль", [
                "Зафиксировать рабочую структуру; планировать точечные улучшения по комментариям."]))
    else:
        insights.append((7, "Данных опроса недостаточно", [
            "Опираться на логи LMS. MHI отражает только студентов, завершивших практику и заполнивших анкету.",
            "Проверить остановки до опроса и между сдачей практики и анкетой; не трактовать оценки оставшихся как норму всей группы."]))
    if not insights:
        insights.append((0, "Смешанный профиль", [
            "Проверить отмеченные показатели и комментарии отдельно: сочетание не покрыто типовым сценарием."]))
    return insights


def role_metrics(data, cohorts, module_table):
    ids = cohorts.cohort_id.tolist()
    eligible_pairs = set()
    completed = set(cohorts.loc[cohorts.assessment_deadline.le(AS_OF) & cohorts.reviews_closed, "cohort_id"])
    for m in data["modules"].loc[data["modules"].cohort_id.isin(ids)].itertuples():
        if m.cutoff_date <= AS_OF or m.cohort_id in completed:
            eligible_pairs.add((m.cohort_id, m.module_no))
    p = data["pulse"].loc[data["pulse"].cohort_id.isin(ids)].copy()
    p = p.loc[[(r.cohort_id, r.module_no) in eligible_pairs for r in p.itertuples()]]
    unique = p.student_id.nunique()
    enrolled = len(data["students"].loc[data["students"].cohort_id.isin(ids)])
    top_unique = p[list(QUESTIONS)].ge(4).groupby(p.student_id).mean().mean() if unique else pd.Series(dtype=float)
    return dict(content=top_unique.reindex(["q4", "q5", "q6"]).mean(), expert=top_unique.get("q7", np.nan),
                care=top_unique.reindex(["q8", "q9"]).mean(), unique=unique,
                coverage=ratio(unique, enrolled)), p


def friction_alerts(table):
    result = {}
    previous = None
    for _, r in table.sort_values("module_no").iterrows():
        if previous is not None and r["module_no"] == previous["module_no"] + 1 and r["mhi_valid"] and previous["mhi_valid"]:
            for q in QUESTIONS:
                delta = previous[f"{q}_top"] - r[f"{q}_top"]
                if delta >= .15 - 1e-10:
                    result[(int(r["module_no"]), q)] = delta
        previous = r
    return result


def service_insights(r):
    if not r["mhi_valid"]:
        return []
    zones = {q: csi_zone(r[f"{q}_top"], r[f"{q}_bottom"], q, True) for q in QUESTIONS}
    items = []
    if any(zones[q] == "red" for q in ("q4", "q5", "q6")):
        items.append(("Контент и практика", "Методист и автор", [
            "Сверить В10 с петлями ошибок и отсевом.",
            "При просадке В6 проверить формулировки ДЗ и автотесты; при В4/В5 обновить подачу и актуальность примеров."]))
    if zones["q7"] == "red":
        items.append(("Подача эксперта", "Отдел работы с экспертами", [
            "Сравнить разные потоки и записи занятий; проверить динамику и ответы на вопросы.",
            "Провести развивающий брифинг. Одного сигнала недостаточно для кадрового решения."]))
    if zones["q8"] == "red":
        items.append(("Восприятие скорости", "Руководитель сопровождения", [
            "Проверить фактическое время ответа и проверки в LMS: оценка В8 не измеряет SLA.",
            "При задержках перераспределить нагрузку; при соблюдении SLA уточнить ожидания и видимость регламента."]))
    if zones["q9"] == "red":
        items.append(("Эмпатия и тон общения", "Руководитель сопровождения", [
            "Изучить В10, тексты ревью и чаты; проверить ясность и тон обратной связи.",
            "Откалибровать обратную связь: признание усилий и конкретный следующий шаг."]))
    return items


def validate_data(data):
    """Проверки контрактов генератора и будущего адаптера LMS; возвращает ошибки."""
    errors = []
    c, m, s, p, q = (data[k] for k in ("cohorts", "modules", "students", "progress", "pulse"))
    for name, frame, keys in [("cohorts", c, ["cohort_id"]), ("modules", m, ["cohort_id", "module_no"]),
                              ("students", s, ["cohort_id", "student_id"]),
                              ("progress", p, ["cohort_id", "student_id", "module_no"]),
                              ("pulse", q, ["cohort_id", "student_id", "module_no"])]:
        if frame.duplicated(keys).any():
            errors.append(f"{name}: повторяются ключи {keys}")
    if (s.final_passed & ~s.final_attempted).any():
        errors.append("Passed_Task должен быть подмножеством Attempted_Task")
    if not s.nps.dropna().between(0, 10).all():
        errors.append("Оценка NPS должна быть от 0 до 10")
    if not q[list(QUESTIONS)].isin([1, 2, 3, 4, 5]).all().all():
        errors.append("В4–В9 должны содержать обязательные оценки 1–5")
    join = q.merge(p, on=["cohort_id", "student_id", "module_no"], how="left", validate="one_to_one")
    if not join.state.eq("passed").all():
        errors.append("Анкета допустима только после успешной практики")
    if not p.state.isin(["passed", "lagging", "paused", "dropped_official", "dropped_inactive"]).all():
        errors.append("Неизвестный статус модуля")
    known_students = set(zip(s.cohort_id, s.student_id))
    if any((r.cohort_id, r.student_id) not in known_students for r in p.itertuples()):
        errors.append("В progress есть неизвестные студенты")
    known_modules = set(zip(m.cohort_id, m.module_no))
    if any((r.cohort_id, r.module_no) not in known_modules for r in p.itertuples()):
        errors.append("В progress есть неизвестные модули")
    answered = set(zip(q.cohort_id, q.student_id, q.module_no))
    for r in p.loc[p.module_no.gt(1)].itertuples():
        if (r.cohort_id, r.student_id, r.module_no - 1) not in answered:
            errors.append("Переход на следующий модуль без обязательного опроса")
            break
    finalists = set(zip(p.loc[p.module_no.eq(6), "cohort_id"], p.loc[p.module_no.eq(6), "student_id"]))
    for r in s.loc[s.final_attempted | s.nps.notna()].itertuples():
        if (r.cohort_id, r.student_id) not in finalists:
            errors.append("Итоговая работа или NPS у нефиналиста")
            break
        if r.final_attempted and (r.cohort_id, r.student_id, 6) not in answered:
            errors.append("Итоговая аттестация без опроса последнего модуля")
            break
    for sid in c.slice_id.unique():
        try:
            slice_cohorts(data, sid)
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def dataset_zip(data, seed, cohort_size):
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as z:
        for name, frame in data.items():
            z.writestr(f"{name}.csv", frame.to_csv(index=False, date_format="%Y-%m-%d").encode("utf-8-sig"))
        z.writestr("metadata.json", json.dumps(dict(synthetic=True, seed=int(seed), cohort_size=int(cohort_size),
                                                     as_of=str(AS_OF.date()), schema_version="1.0",
                                                     note="progress.state: snapshot at cutoff; open windows are provisional"),
                                                ensure_ascii=False, indent=2))
    return buffer.getvalue()


CSS = """
<style>
.stApp {background:#F5F7FA; color:#192E44;}
.block-container {max-width:1510px; padding-top:2rem; padding-bottom:3rem;}
h1,h2,h3 {letter-spacing:-.025em; color:#17324D;}
h1 {font-size:2.25rem !important; font-weight:750 !important;}
.eyebrow {font-size:.72rem; letter-spacing:.16em; color:#668093; font-weight:750; margin-bottom:.4rem;}
.subhead {color:#64768A; font-size:1rem; margin-top:-.4rem; margin-bottom:1.4rem;}
.kpi {background:white; border:1px solid #E1E7EF; border-radius:14px; padding:18px 18px 15px; min-height:182px; box-shadow:0 3px 12px #1A354405;}
.kpi-title {font-size:.82rem; color:#60748A; min-height:23px;}
.kpi-number {font-size:2.1rem; color:#19354F; letter-spacing:-.04em; font-weight:750; line-height:1.35;}
.kpi-detail {font-size:.76rem; color:#697B8F; min-height:34px; margin:3px 0 10px;}
.pill {display:inline-block; font-size:.70rem; font-weight:650; border-radius:20px; padding:4px 9px;}
.insight {border:1px solid #DDE7E4; background:white; border-left:4px solid #16816B; border-radius:12px; padding:18px 20px; margin:18px 0;}
.insight-title {font-size:1.12rem; font-weight:700; margin-bottom:6px;}
.insight-body {font-size:.9rem; color:#52697D; line-height:1.6;}
.matrix-wrap {overflow-x:auto; border:1px solid #DFE6EE; border-radius:12px; background:white; margin:12px 0;}
.matrix {width:100%; border-collapse:separate; border-spacing:0; font-size:.78rem;}
.matrix th {background:#EDF2F7; color:#496176; padding:12px 9px; text-align:left; font-size:.72rem; font-weight:700; white-space:nowrap;}
.matrix td {padding:11px 8px; border-top:1px solid #E9EDF3; vertical-align:middle;}
.matrix td:first-child {min-width:170px; max-width:220px; font-weight:650; color:#28475F;}
.matrix small {display:block; font-size:.67rem; font-weight:400; color:#6F8194; margin-top:4px;}
.cell {display:block; border-radius:6px; padding:7px 8px; white-space:nowrap; font-weight:650;}
.feedback {background:white; border:1px solid #E1E7EF; padding:13px 16px; border-radius:10px; margin:8px 0; color:#29445D; font-size:.9rem;}
.feedback small {color:#718498; display:block; margin-bottom:5px;}
div[data-testid="stMetric"] {background:white; border:1px solid #E1E7EF; border-radius:10px; padding:12px;}
div[data-testid="stExpander"] {background:white; border-radius:10px;}
button[data-baseweb="tab"] {font-size:.92rem;}
@media (max-width:700px) {.block-container {padding-left:1rem; padding-right:1rem;} .kpi {min-height:150px;} h1 {font-size:1.8rem !important;}}
</style>
"""


def html_cell(text, zone, tooltip=""):
    return (f'<span class="cell" style="background:{BG[zone]};color:{COLORS[zone]}" '
            f'title="{escape(tooltip, quote=True)}">{escape(str(text))}</span>')


def html_table(headers, rows):
    head = "".join(f"<th>{escape(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    st.markdown(f'<div class="matrix-wrap"><table class="matrix"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>', unsafe_allow_html=True)


def kpi(title, value, detail, zone, label=None):
    st.markdown(f'<div class="kpi"><div class="kpi-title">{escape(title)}</div>'
                f'<div class="kpi-number">{escape(value)}</div><div class="kpi-detail">{escape(detail)}</div>'
                f'<span class="pill" style="background:{BG[zone]};color:{COLORS[zone]}">{escape(label or ZONES[zone])}</span></div>',
                unsafe_allow_html=True)


def note(title, body, zone="green"):
    st.markdown(f'<div class="insight" style="border-left-color:{COLORS[zone]}">'
                f'<div class="insight-title">{escape(title)}</div><div class="insight-body">{escape(body)}</div></div>',
                unsafe_allow_html=True)


def chart_layout(fig, height=300):
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=20, r=20, t=25, b=30),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Arial, sans-serif", color="#486076", size=12),
                      legend=dict(orientation="h", y=1.15, x=0), hoverlabel=dict(bgcolor="white"))
    return fig


def fallback_actions(m):
    actions = []
    if m["cr"] < .65:
        actions.append("Проверить модули с потерями и задолженностью; сопоставить их со входными требованиями курса.")
    if m["a_task"] < .75:
        actions.append("Разделить неучастие в защите и несдачу по критериям; проверить переход от учебных ДЗ к итоговому кейсу.")
    if not m["nps_valid"]:
        actions.append("Накопить минимум 15 ответов NPS при охвате не ниже 50% финалистов.")
    elif m["nps"] < 50:
        actions.append("Проверить ожидания студентов, сервисные оценки и открытые комментарии.")
    if not actions:
        actions.append("Продолжить наблюдение за показателями; сочетание не соответствует ни одному из шести типовых сценариев.")
    return actions


def render_course(data, cohorts):
    eligible = ready_cohorts(cohorts)
    excluded = cohorts.loc[~cohorts.cohort_id.isin(eligible.cohort_id)]
    if not excluded.empty:
        st.info("В итоговом аудите участвуют только последовательные закрытые потоки: " +
                (", ".join(eligible.cohort_name) if len(eligible) else "пока нет") +
                ". Исключены: " + ", ".join(excluded.cohort_name) +
                ". Причина: срок аттестации / незакрытая проверка или разрыв последовательности.")
    m = course_metrics(data, eligible.cohort_id.tolist())
    if m["enrolled"] < 30:
        st.info(f"Идёт накопление выборки (собрано {m['enrolled']} из 30). Стратегическая аналитика курса защищена от шума малых групп.")
        st.caption("Аудит модулей и сервисные оценки используют собственные пороги достаточности данных.")
        return
    cols = st.columns(4)
    with cols[0]:
        kpi("Сквозной HI_core", f"{m['hi']:.3f}", f"{m['passed']} из {m['enrolled']} зачисленных подтвердили навык", high_zone(m["hi"], .50, .30))
    with cols[1]:
        kpi("Доходимость · CR", pct(m["cr"]), f"{m['finished']} из {m['enrolled']} дошли до финала", high_zone(m["cr"], .65, .55))
    with cols[2]:
        kpi("Самостоятельная сдача · A_task", pct(m["a_task"]),
            f"{m['passed']} из {m['finished']} финалистов · приступили {m['attempted']}",
            high_zone(m["a_task"], .75, .60), "Предварительно: <20 финалистов" if m["finished"] < 20 else None)
    with cols[3]:
        kpi("Лояльность · NPS", "—" if pd.isna(m["nps"]) else f"{m['nps']:+.0f}",
            f"Ответили {m['nps_n']} из {m['finished']} · охват {pct(m['nps_rr'], 0)}",
            high_zone(m["nps"], 50, 35, m["nps_valid"]))
    scenario = macro_scenario(m)
    if scenario:
        title, zone, priority, actions = MACRO[scenario]
        note(f"{priority} · {title}", "Предварительная диагностика по сочетанию метрик. Причины требуют проверки по модулям, логам и комментариям.", zone)
    else:
        actions = fallback_actions(m)
        note("Покомпонентная оценка", "Сочетание не входит в типовую матрицу или NPS пока недостаточно надёжен. Ниже — факты и проверки по доступным показателям.", "gray")
    if m["finished"] < 20:
        st.warning("Малая база финалистов: A_task и зависящие от него гипотезы предварительны, даже при достаточной базе зачисленных.")
    comp = cohort_comparison(data, eligible)
    flags = isolated_course_anomalies(comp)
    if flags:
        st.warning("⚡ Локальная аномалия: " + "; ".join(f"{name} · {metric.upper()}" for name, metric in flags) +
                   ". Сначала проверьте организацию этого потока и его состав.")
    elif len(comp) == 2 and (comp.cr.max() - comp.cr.min() > .20 or comp.a_task.max() - comp.a_task.min() > .20):
        st.warning("Между двумя потоками есть расхождение >20 п.п.; определить локальный выброс пока нельзя.")
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.subheader("Что показывают данные")
        st.write(f"Подтверждённый результат есть у **{pct(m['hi'])}** зачисленных. "
                 f"Среди финалистов без подтверждения — **{pct(m['task_fail'])}**: "
                 f"не представили проект {pct(m['no_show'])}, не прошли рубрикатор {pct(m['rubric_fail'])}.")
        st.write(f"Доля дошедших без подтверждённого навыка от всех зачисленных: **{pct(m['unconfirmed'])}**.")
        st.caption("NPS отражает ответы финалистов, а не мнение всех зачисленных. Достаточный охват не устраняет смещение отбора.")
    with right:
        st.subheader("Гипотезы и действия")
        for action in actions:
            st.markdown(f"- {action}")
    st.divider()
    st.subheader("Воронка подтверждения навыка")
    task_zone = high_zone(m["a_task"], .75, .60)
    fig = go.Figure(go.Bar(x=[m["cr"], m["hi"]], y=["Дошли до финала", "Подтвердили навык"], orientation="h",
                           marker_color=["#658FB7", COLORS[task_zone]], text=[pct(m["cr"]), pct(m["hi"])], textposition="auto",
                           hovertemplate="%{y}: %{x:.1%} от зачисленных<extra></extra>"))
    fig.update_xaxes(range=[0, 1], tickformat=".0%", gridcolor="#E3E9F0")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(chart_layout(fig, 220), width="stretch", key="course_funnel")
    if m["hi"] >= .50 and m["cr"] >= .65 and m["a_task"] >= .75:
        st.success("Образовательный выход сбалансирован: высокая доходимость подкреплена самостоятельной защитой проекта.")
    elif m["cr"] >= .65 and m["a_task"] < .60:
        st.warning(f"Разрыв подтверждения результата: дошли {pct(m['cr'])}, подтвердили навык {pct(m['hi'])} от поступивших. "
                   f"У {pct(m['task_fail'])} финалистов результат не подтверждён.")
    elif m["cr"] < .55 and m["a_task"] >= .75:
        st.info(f"Жёсткий фильтр: сдача {pct(m['a_task'])} среди финалистов при потере {pct(1 - m['cr'])} зачисленных до финала.")
    else:
        st.info(f"Удержание: {ZONES[high_zone(m['cr'], .65, .55)].lower()}. Подтверждение результата: "
                f"{ZONES[task_zone].lower()}. Не приступили {pct(m['no_show'])}; не прошли критерии {pct(m['rubric_fail'])} финалистов.")
    st.subheader("Динамика срезов одной версии")
    all_c = data["cohorts"]
    same = all_c.loc[all_c.course.eq(cohorts.iloc[0].course) & all_c.version.eq(cohorts.iloc[0].version)]
    history = []
    for sid in same.sort_values("start_date").slice_id.unique():
        e = ready_cohorts(slice_cohorts(data, sid))
        hm = course_metrics(data, e.cohort_id.tolist())
        if hm["enrolled"] >= 30:
            history.append(dict(slice_id=sid, **hm))
    hist = pd.DataFrame(history)
    if not hist.empty:
        trend = go.Figure()
        for key, label, color in [("cr", "Доходимость CR", "#7397BA"), ("a_task", "Сдача A_task", "#76BAB2")]:
            trend.add_bar(x=hist.slice_id, y=hist[key], name=label, marker_color=color,
                          hovertemplate="%{x}: %{y:.1%}<extra>" + label + "</extra>")
        trend.add_scatter(x=hist.slice_id, y=hist.hi, name="HI_core", mode="lines+markers",
                          line=dict(color="#253E66", width=3), hovertemplate="%{x}: %{y:.3f}<extra>HI_core</extra>")
        for value in [.30, .50]:
            trend.add_hline(y=value, line_dash="dot", line_color="#7C8DA0", annotation_text=f"HI {value:.2f}")
        trend.update_layout(barmode="group")
        trend.update_yaxes(range=[0, 1.04], tickformat=".0%")
        st.plotly_chart(chart_layout(trend), width="stretch", key="course_history")
        st.caption("Каждый столбец — отдельный непересекающийся срез одной версии. Линии 0,30 и 0,50 относятся только к HI_core. Это демосценарии, а не доказательство эффекта изменений.")
    with st.expander("Данные по потокам и формулы"):
        display = comp[["name", "enrolled", "finished", "attempted", "passed", "cr", "a_task", "hi", "nps_n", "nps_rr"]].copy()
        display.columns = ["Поток", "Зачислены", "Финалисты", "Приступили", "Сдали", "CR", "A_task", "HI_core", "Ответов NPS", "Охват NPS"]
        st.dataframe(display.style.format({k: "{:.1%}" for k in ["CR", "A_task", "HI_core", "Охват NPS"]}, na_rep="—"), hide_index=True, width="stretch")
        st.code("CR = Finished / Enrolled\nA_task = Passed_Task / Finished\nHI_core = Passed_Task / Enrolled = CR × A_task\nTask_Fail = No_Show + Rubric_Fail = 1 − A_task\nUnconfirmed_Share = (Finished − Passed_Task) / Enrolled", language="text")


def render_modules(data, cohorts, table, per_cohort):
    st.subheader("Где возникают затруднения")
    st.caption("Все модули выбранного среза на одном экране. MHI описывает опыт завершивших практику; серые значения не участвуют в содержательной интерпретации.")
    if (table.closed_cohorts < table.total_cohorts).any():
        st.info("Часть окон ещё открыта. COR показывает фактически приступивших во всех потоках среза; отсев, задолженность и опросы рассчитаны только по закрытым окнам. Число закрытых потоков указано в каждой строке.")
    cells = []
    for _, r in table.iterrows():
        zones = module_zones(r, r.course_drop)
        title = f"М{int(r.module_no)} · {escape(r.title)}"
        if r.local_anomaly:
            title += f"<small>⚡ {escape(r.local_anomaly)} — один поток</small>"
        if r.n < 15:
            title += "<small>⚠ Малая база модуля</small>"
        title += f"<small>Закрыто окон: {int(r.closed_cohorts)}/{int(r.total_cohorts)}</small>"
        cor = f"{pct(r.cor)}<small>Начали {int(r.started_total)}/{int(r.enrolled)}<br>Паузы в закрытых окнах: {int(r.paused)}</small>"
        drop_text = html_cell(pct(r["drop"]), zones["drop"], f"Официально: {int(r.official)}; неактивность: {int(r.inactive)}; база: {int(r.n)}")
        lag_text = html_cell(pct(r.lag), zones["lag"], f"Задолжников: {int(r.lagging)} из {int(r.n)}")
        coverage = f"{pct(r.rr, 0)}<small>{int(r.m)}/{int(r.n)} чел.</small>"
        cells.append([title, cor, drop_text, lag_text, coverage] +
                     [html_cell(pct(r[key]), zones[key], "От ответивших на опрос" if key != "loop" else "От активной базы модуля; независимо от MHI")
                      for key in ("rushed", "slow", "fragmented", "depleted", "loop")])
    html_table(["Модуль", "COR", "Отсев", "В досдаче", "Охват MHI", "Спешат", "Медленно", "Несвязно", "Истощены", "Петли"], cells)
    st.caption("Наведите курсор на значение для базы расчёта. Пороги: отсев >10% / >15%; досдача >20%; спешка >25% / >30%; несвязность и петли >15% / >20%; истощение >25%; медленно >20%.")
    st.subheader("Карта удержания")
    valid_drop = table["drop"].where(table.lms_valid)
    bar_colors = ["#CCD4DF" if pd.isna(x) else f"rgb({int(111 + min(x / .4, 1) * 80)}, {int(156 - min(x / .4, 1) * 90)}, {int(181 - min(x / .4, 1) * 100)})" for x in valid_drop]
    fig = go.Figure(go.Bar(x=[f"М{n}" for n in table.module_no], y=table.cor,
                           marker_color=bar_colors, text=[pct(x, 0) for x in table.cor], textposition="outside",
                           customdata=np.array([[r.title, pct(r["drop"]), pct(r.lag), int(r.n)] for _, r in table.iterrows()], dtype=object),
                           hovertemplate="%{customdata[0]}<br>COR %{y:.1%}<br>Отсев %{customdata[1]} · досдача %{customdata[2]}<br>Активная база закрытых окон: %{customdata[3]}<extra></extra>"))
    fig.add_hline(y=.65, line_dash="dot", line_color="#8B9DB1", annotation_text="Ориентир выпуска 65%")
    fig.update_yaxes(range=[0, 1.12], tickformat=".0%")
    st.plotly_chart(chart_layout(fig, 285), width="stretch", key="module_funnel")
    st.caption("Высота — факт достижения модуля, включая паузы; цвет — локальный отсев по закрытым окнам. Это разные базы. Ориентир 65% относится к выпуску курса.")
    st.subheader("Гипотезы для проверки")
    for _, r in table.iterrows():
        zones = module_zones(r, r.course_drop)
        severity = "red" if "red" in zones.values() else "yellow" if "yellow" in zones.values() else "green" if r.mhi_valid else "gray"
        insights = module_insights(r)
        title = f"{ICONS[severity]} М{int(r.module_no)} · {r.title} — {insights[0][1]}"
        with st.expander(title, expanded=severity in ("red", "yellow")):
            left, right = st.columns([1, 1.7], gap="large")
            with left:
                st.markdown(f"**Активная база:** {int(r.n)} · **Ответили:** {int(r.m)} ({pct(r.rr)})")
                st.write(f"Отсев {pct(r['drop'])} · в досдаче {pct(r.lag)} · петли ошибок {pct(r.loop)}")
                st.caption(f"Сдали {int(r.passed)} + задолжники {int(r.lagging)} + отсев {int(r.dropped)} = {int(r.n)}. Паузы {int(r.paused)} исключены из активной базы.")
                if r.local_anomaly:
                    st.warning(f"⚡ Только {r.local_anomaly} имеет диагностические сигналы. Сначала проверьте локальный сбой.")
                if r.n < 15:
                    st.warning("Оценка предварительная: активная база <15.")
            with right:
                for scenario_id, hypothesis, checklist in insights:
                    st.markdown(f"**{('Сценарий ' + str(scenario_id) + ' · ') if scenario_id else ''}{hypothesis}**")
                    for item in checklist:
                        st.markdown(f"- {item}")
            if not per_cohort.empty:
                detail = per_cohort.loc[per_cohort.module_no.eq(r.module_no), ["cohort_id", "n", "m", "drop", "lag", "loop", "rr"]].copy()
                names = cohorts.set_index("cohort_id").cohort_name.to_dict()
                detail["cohort_id"] = detail.cohort_id.map(names)
                detail.columns = ["Поток", "Активная база", "Ответили", "Отсев", "Досдача", "Петли", "Охват"]
                st.dataframe(detail.style.format({k: "{:.1%}" for k in ["Отсев", "Досдача", "Петли", "Охват"]}, na_rep="—"), hide_index=True, width="stretch")


def render_service(data, cohorts, table, per_cohort):
    roles, pulse = role_metrics(data, cohorts, table)
    columns = st.columns(3)
    specs = [("content", "Контент и задания", "Методисты и авторы", .85, .75),
             ("expert", "Эксперты и спикеры", "Отдел работы с экспертами", .88, .80),
             ("care", "Команда сопровождения", "Служба заботы и кураторы", .88, .80)]
    for col, (key, title, owner, green, yellow) in zip(columns, specs):
        with col:
            kpi(title, pct(roles[key]), f"{owner} · {roles['unique']} уникальных · охват {pct(roles['coverage'], 0)}",
                high_zone(roles[key], green, yellow, roles["unique"] >= 15))
    st.caption("У каждого студента одинаковый вес: сначала его доля оценок 4–5 по вопросу, затем среднее по уникальным студентам. Карточки — по закрытым окнам; критический негатив проверяется отдельно в матрице.")
    st.subheader("Качество среды по модулям")
    alerts = friction_alerts(table)
    cells = []
    for _, r in table.iterrows():
        row = [f"М{int(r.module_no)} · {escape(r.title)}"]
        for q in QUESTIONS:
            top, bottom = r[f"{q}_top"], r[f"{q}_bottom"]
            zone = csi_zone(top, bottom, q, r.mhi_valid)
            text_value = pct(top)
            delta = alerts.get((int(r.module_no), q))
            if delta is not None:
                text_value += f" ↓{delta * 100:.1f} п.п."
            row.append(html_cell(text_value, zone, f"Top-2 (4–5): {pct(top)}; Bottom-2 (1–2): {pct(bottom)}. Ответили {int(r.m)} из {int(r.n)}."))
        row.append(f"{pct(r.rr, 0)}<small>{int(r.m)}/{int(r.n)} чел.</small>")
        cells.append(row)
    html_table(["Модуль", *QUESTIONS.values(), "Охват CSI"], cells)
    st.caption("Top-2 — оценки 4–5. Bottom-2 — оценки 1–2, доступен при наведении. Красный при Bottom-2 >15% независимо от Top-2. ↓ — падение ≥15 п.п. между соседними модулями с достаточными данными.")
    st.subheader("Кому и что проверить")
    any_issues = False
    for _, r in table.iterrows():
        items = service_insights(r)
        for title, owner, checklist in items:
            any_issues = True
            with st.expander(f"🔴 М{int(r.module_no)} · {title} — {owner}", expanded=True):
                for item in checklist:
                    st.markdown(f"- {item}")
                if title == "Подача эксперта":
                    mod_p = pulse.loc[pulse.module_no.eq(r.module_no)]
                    unique = mod_p.student_id.nunique()
                    st.caption(f"Оценок от уникальных студентов: {unique}. Для кадровых выводов нужны 15–20 и проверка однородности между потоками.")
                    if not per_cohort.empty:
                        cmp = per_cohort.loc[per_cohort.module_no.eq(r.module_no), ["cohort_id", "m", "q7_top", "q7_bottom", "mhi_valid"]].copy()
                        cmp["cohort_id"] = cmp.cohort_id.map(cohorts.set_index("cohort_id").cohort_name)
                        cmp.columns = ["Поток", "Оценок", "Top-2 В7", "Bottom-2 В7", "Достаточность"]
                        st.dataframe(cmp.style.format({"Top-2 В7": "{:.1%}", "Bottom-2 В7": "{:.1%}"}, na_rep="—"), hide_index=True, width="stretch")
    yellow_cells = sum(csi_zone(r[f"{q}_top"], r[f"{q}_bottom"], q, r.mhi_valid) == "yellow" for _, r in table.iterrows() for q in QUESTIONS)
    if not any_issues:
        if table.mhi_valid.any():
            st.info("Красных сервисных сигналов на достаточных данных нет. " +
                    (f"В жёлтой зоне {yellow_cells} оценок: запланируйте проверку комментариев и калибровку." if yellow_cells else "Продолжайте плановое наблюдение."))
        else:
            st.info("Для сервисной диагностики пока недостаточно ответов на модулях.")
    elif yellow_cells:
        st.caption(f"Дополнительно {yellow_cells} оценок в жёлтой зоне — плановая проверка комментариев и калибровка профильной службы.")
    st.subheader("Голос студентов")
    options = [0] + table.module_no.astype(int).tolist()
    labels = {int(r.module_no): f"М{int(r.module_no)} · {r.title}" for _, r in table.iterrows()}
    chosen = st.selectbox("Комментарии по модулю", options, format_func=lambda x: "Все модули" if x == 0 else labels[x], key="comments_module")
    comments = pulse.loc[pulse.comment.fillna("").str.strip().ne("")].copy()
    if chosen:
        comments = comments.loc[comments.module_no.eq(chosen)]
    if comments.empty:
        st.info("По данному срезу/модулю нет текстовых комментариев в открытом вопросе В10.")
    else:
        page_size = 8
        pages = max(1, (len(comments) + page_size - 1) // page_size)
        page = st.selectbox("Страница комментариев", range(1, pages + 1), key=f"comments_page_{cohorts.iloc[0].slice_id}_{chosen}")
        st.caption(f"{len(comments)} комментариев · все тексты синтетические")
        names = cohorts.set_index("cohort_id").cohort_name.to_dict()
        for r in comments.sort_values(["module_no", "cohort_id", "student_id"]).iloc[(page - 1) * page_size:page * page_size].itertuples():
            st.markdown(f'<div class="feedback"><small>{escape(labels[r.module_no])} · {escape(names[r.cohort_id])} · {escape(r.student_id)}</small>{escape(r.comment)}</div>', unsafe_allow_html=True)


RULES = """
**Область реализации.** Системный контур v1.0 по документу «Концепция: Система метрик (16)»:
аудит курса, модулей, сервиса. Оперативный контур отнесён в концепции к v2.0 и здесь не реализован.

**Достаточность данных.** Курс: минимум 30 зачисленных в закрытых последовательных потоках.
При <20 финалистах A_task предварителен. NPS: минимум 15 ответов и 50% финалистов.
Модуль: cutoff = дедлайн + 14 дней (или полностью завершённый поток); активная база минимум 15.
MHI и модульный CSI: минимум 15 ответов и охват не ниже 50% активной базы.
Ролевой CSI: минимум 15 уникальных респондентов. Эти пороги не означают статистической доказанности причин.

**Состояния.** Сдавшие, задолжники и выбывшие — непересекающиеся состояния активной базы;
официальная пауза до завершения исключается. Если практика была сдана, позднейший уход не меняет
статус этого модуля. Генератор хранит уже классифицированный снимок `state` на cutoff; для настоящей
LMS его нужно построить из событий с приоритетом «сдано → пауза до сдачи → активный задолжник → отсев».
`loop_fail` — факт серии ≥3 неудачных попыток до cutoff, даже если позже практика сдана.

**Базы.** COR = фактически начавшие модуль / все зачисленные выбранного среза.
Локальные метрики и анкеты считаются по закрытым окнам. При частично открытом срезе их база
может отличаться от базы COR; число закрытых потоков всегда показано. MHI может иметь охват ниже
доли сдавших практику: некоторые останавливаются между сдачей и анкетой. Опрос обязателен перед
следующим модулем и итоговой аттестацией.

**Границы.** Все сравнения используют исходные значения до округления. Доли хранятся в диапазоне
0–1, NPS в диапазоне −100…100. Показатель без знаменателя — «—», а не 0. Границы Baseline v1.0
являются стартовыми ориентирами для последующей калибровки.

**Решения реализации там, где документ не задаёт точный алгоритм:**

- Для курса принят минимальный порог 30 (из диапазона 30–40). Аномалия потока при ≥3 потоках:
  один отличается от каждого из остальных более чем на 20 п.п., а размах остальных ≤20 п.п.
  При двух потоках показывается расхождение без назначения «виновного».
- Для модулей локальная аномалия — только один поток с диагностическими сигналами среди
  минимум трёх потоков с активной базой ≥15. Для опросных сигналов дополнительно проверяется охват.
- Средний отсев курса для относительного порога +10 п.п. — сумма выбывших / сумма активных
  баз модулей с n≥15. Это среднее по наблюдениям «студент × модуль», не сквозной отсев курса.
- При n<15 поведенческие числа показаны серым как предварительные; системные гипотезы подавлены.
- Модуль может иметь несколько одновременно применимых гипотез. Сценарий 7 запрещает выводы
  по MHI, но не отменяет сигнал петель ошибок из LMS. Не покрытое матрицей сочетание описывается отдельно.
- Если поток в середине среза не закрыт, итоговый аудит использует только закрытый последовательный
  префикс. Более поздние потоки через этот разрыв не объединяются.
- Ролевые карточки CSI используют анкеты закрытых окон и порог U≥15, как в технической части
  концепции. Bottom-2 не меняет цвет ролевой карточки; он отдельно управляет цветом каждой ячейки
  модульной матрицы и сервисными рекомендациями. В8 и В9 запускают оба чек-листа при общей просадке.

**Подключение настоящих данных.** Замените `get_demo_data()` адаптером, возвращающим те же пять
таблиц, и обновите `AS_OF`. До адаптера необходимо удалить технические дубли и отмены до старта,
разметить версии и последовательность потоков, зафиксировать временные снимки и критерии
самостоятельной сдачи. `student_id` должен устойчиво обозначать человека, а не ответ на анкету.
Флаги закрытия и ответы не следует восстанавливать из отсутствия записей. Эта версия не подключена к LMS.
"""


def render_data(data, cohorts, table, seed, cohort_size):
    st.subheader("Синтетический набор для проверки")
    counts = st.columns(4)
    for col, title, value in zip(counts, ["Демосрезов", "Потоков", "Студентов", "Анкет модулей"],
                                 [data["cohorts"].slice_id.nunique(), len(data["cohorts"]), len(data["students"]), len(data["pulse"])]):
        col.metric(title, f"{value:,}".replace(",", " "))
    st.write(f"Снимок: **{AS_OF:%d.%m.%Y}**. Seed: **{seed}**. Размер обычного потока: **{cohort_size}**. "
             "Каждый срез содержит три потока одной версии. В малом срезе всегда 3 × 8 студентов.")
    errors = validate_data(data)
    if errors:
        for error in errors:
            st.error(error)
    else:
        st.success("Контроль целостности пройден: ключи, допустимые оценки, последовательность модулей, анкеты после практики и вложенность итоговых результатов.")
    st.download_button("Скачать все исходные данные · ZIP / CSV", dataset_zip(data, seed, cohort_size),
                       file_name=f"synthetic_data_seed_{seed}.zip", mime="application/zip", key="download_raw")
    st.download_button("Скачать расчёты выбранного среза · CSV", table.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"module_audit_{cohorts.iloc[0].slice_id}.csv", mime="text/csv", key="download_metrics")
    st.subheader("Путеводитель по демосценариям")
    rows = data["cohorts"][["course", "version", "slice_id", "slice_label"]].drop_duplicates()
    rows.columns = ["Курс", "Версия", "Срез", "Что проверять"]
    st.dataframe(rows, hide_index=True, width="stretch")
    st.subheader("Состав таблиц")
    st.dataframe(pd.DataFrame([
        ("cohorts", "Поток", "Курс, версия, срез, порядок, сроки аттестации, закрытие проверки"),
        ("modules", "Поток × модуль", "Дедлайн, cutoff, преподаватель"),
        ("students", "Поток × студент", "Итоговая попытка, независимая сдача, оценка NPS"),
        ("progress", "Поток × студент × модуль", "Состояние на cutoff и серия ≥3 ошибок"),
        ("pulse", "Поток × студент × модуль", "Ритм, связность, ресурс, В4–В9 и комментарий В10"),
    ], columns=["Таблица", "Единица записи", "Содержание"]), hide_index=True, width="stretch")
    chosen = st.selectbox("Предпросмотр исходной таблицы", list(data), key="source_table")
    filtered = data[chosen].loc[data[chosen].cohort_id.isin(cohorts.cohort_id)]
    st.caption(f"Выбранный срез: {len(filtered)} записей. Показаны первые 100.")
    st.dataframe(filtered.head(100), hide_index=True, width="stretch")
    st.subheader("Формулы, ограничения и решения реализации")
    st.markdown(RULES)


def main():
    st.set_page_config(page_title="Система метрик · Аудит программ", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
    st.markdown(CSS, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### ◈ Система метрик")
        st.caption("Системный аудит · v1.0")
        with st.expander("Генератор демоданных", expanded=False):
            seed = int(st.number_input("Seed", min_value=0, max_value=999999, value=42, step=1, key="seed"))
            cohort_size = int(st.slider("Студентов в потоке", min_value=30, max_value=120, value=60, step=10, key="cohort_size"))
            st.caption("Одинаковый seed и размер дают одинаковый набор. Срез малой базы фиксирован: 24 человека.")
        data = get_demo_data(seed, cohort_size)
        course = st.selectbox("Образовательный продукт", data["cohorts"].course.unique(), key="course")
        versions = data["cohorts"].loc[data["cohorts"].course.eq(course), "version"].unique()
        version = st.selectbox("Версия программы", versions, key="version")
        available = data["cohorts"].loc[data["cohorts"].course.eq(course) & data["cohorts"].version.eq(version)]
        labels = available.drop_duplicates("slice_id").set_index("slice_id").slice_label.to_dict()
        slice_id = st.selectbox("Аудиторский срез", list(labels), format_func=lambda x: f"{x} · {labels[x]}", key="slice")
        cohorts = slice_cohorts(data, slice_id)
        enrolled = int(data["students"].cohort_id.isin(cohorts.cohort_id).sum())
        st.divider()
        st.metric("Зачислено в срез", enrolled)
        st.caption(f"{len(cohorts)} последовательных потока · версия {version}")
        st.caption(" · ".join(cohorts.cohort_name))
        st.info("ДЕМО · Синтетические данные\n\nРекомендации — гипотезы для проверки.")
        st.caption(f"Снимок на {AS_OF:%d.%m.%Y}\n\nBaseline v1.0 · пороги требуют калибровки")
    st.markdown('<div class="eyebrow">КАЧЕСТВО ОБРАЗОВАТЕЛЬНОГО ПРОДУКТА</div>', unsafe_allow_html=True)
    st.title("От показателей к решениям")
    st.markdown(f'<div class="subhead">{escape(course)} · версия {escape(version)} · {escape(slice_id)} · {escape(labels[slice_id])}</div>', unsafe_allow_html=True)
    table, per_cohort = module_metrics(data, cohorts)
    course_tab, module_tab, service_tab, data_tab = st.tabs(["Аудит курса", "Аудит модулей", "Сервис и среда", "Данные и правила"])
    with course_tab:
        render_course(data, cohorts)
    with module_tab:
        render_modules(data, cohorts, table, per_cohort)
    with service_tab:
        render_service(data, cohorts, table, per_cohort)
    with data_tab:
        render_data(data, cohorts, table, seed, cohort_size)


if __name__ == "__main__":
    import sys
    if "--export-data" in sys.argv:
        parser = argparse.ArgumentParser(description="Экспорт воспроизводимого набора синтетических данных")
        parser.add_argument("--export-data", type=Path, required=True)
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--cohort-size", type=int, choices=range(30, 121, 10), default=60)
        args = parser.parse_args()
        data = generate_synthetic_data(args.seed, args.cohort_size)
        errors = validate_data(data)
        if errors:
            raise ValueError("; ".join(errors))
        args.export_data.write_bytes(dataset_zip(data, args.seed, args.cohort_size))
        print(f"Сохранено: {args.export_data}")
    else:
        main()
