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
