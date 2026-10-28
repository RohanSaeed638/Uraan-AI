from app.ai.roadmap_schedule import assign_weeks, clean_milestones, normalize


def phase(weeks, tasks):
    return {
        "estimated_weeks": weeks,
        "tasks": [{"estimated_hours": h, **({"week": w} if w else {})} for h, w in tasks],
    }


def weeks_of(phases):
    return [[t["week"] for t in (p["tasks"] or [])] for p in phases]


def test_valid_ai_weeks_are_kept():
    phases = [phase(3, [(4, 1), (4, 2), (4, 3)])]

    assign_weeks(phases)

    assert weeks_of(phases) == [[1, 2, 3]]


def test_missing_weeks_are_spread_by_hours():
    phases = [phase(4, [(10, None), (10, None), (10, None), (10, None)])]

    assign_weeks(phases)

    assert weeks_of(phases) == [[1, 2, 3, 4]]


def test_a_long_task_takes_more_of_the_phase():
    phases = [phase(4, [(30, None), (5, None), (5, None)])]

    assign_weeks(phases)

    weeks = weeks_of(phases)[0]
    assert weeks[0] == 1
    assert weeks == sorted(weeks)
    assert weeks[1] >= 3


def test_phases_follow_each_other():
    phases = [phase(2, [(5, None), (5, None)]), phase(3, [(5, None), (5, None), (5, None)])]

    nxt = assign_weeks(phases)

    assert weeks_of(phases) == [[1, 2], [3, 4, 5]]
    assert phases[1]["start_week"] == 3
    assert nxt == 6


def test_weeks_outside_the_phase_are_replaced():
    phases = [phase(2, [(5, 1), (5, 1)]), phase(2, [(5, 99), (5, 1)])]

    assign_weeks(phases)

    second = weeks_of(phases)[1]
    assert all(3 <= w <= 4 for w in second)


def test_weeks_never_go_backwards():
    phases = [phase(4, [(5, 3), (5, 1), (5, 2), (5, 4)])]

    assign_weeks(phases)

    weeks = weeks_of(phases)[0]
    assert weeks == sorted(weeks)


def test_junk_values_do_not_crash():
    phases = [
        {
            "estimated_weeks": "abc",
            "tasks": [{"estimated_hours": None, "week": "x"}, {"week": -4}],
        },
        {"estimated_weeks": 0, "tasks": []},
        {"tasks": None},
    ]

    assign_weeks(phases)

    assert weeks_of(phases)[0] == [1, 1]


def test_first_week_offset_for_an_adapted_plan():
    phases = [phase(2, [(5, 1), (5, 2)])]

    assign_weeks(phases, first_week=7)

    assert weeks_of(phases) == [[7, 8]]


def test_milestones_are_trimmed_deduped_and_capped():
    raw = ["  Build an API ", "Build an API", "", None, "x" * 500, "a", "b", "c", "d"]

    cleaned = clean_milestones(raw)

    assert cleaned[0] == "Build an API"
    assert len(cleaned) == 4
    assert all(len(m) <= 160 for m in cleaned)
    assert clean_milestones("nope") == []
    assert clean_milestones(None) == []


def test_normalize_does_both():
    data = {"phases": [{"estimated_weeks": 2, "milestones": ["Ship it"], "tasks": [{"estimated_hours": 3}]}]}

    normalize(data)

    assert data["phases"][0]["milestones"] == ["Ship it"]
    assert data["phases"][0]["tasks"][0]["week"] == 1
