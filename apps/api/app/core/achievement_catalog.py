"""Every achievement, and the career titles.

`rule` names a measure in the learner stats (see AchievementService.stats) and
`threshold` is the amount that earns the badge. Changing a threshold here
updates existing rows on next use; a code must never be reused for a different
badge, because unlocks are stored by code."""

# (code, title, description, category, icon, xp, rule, threshold)
ACHIEVEMENTS: list[tuple] = [
    ("first_lesson", "First Step", "Finish your first lesson.", "learning", "Footprints", 10, "lessons", 1),
    ("lessons_25", "Getting Rolling", "Finish 25 lessons.", "learning", "BookOpen", 40, "lessons", 25),
    ("lessons_100", "Bookworm", "Finish 100 lessons.", "learning", "Library", 150, "lessons", 100),
    ("first_task", "Task Done", "Complete your first roadmap task.", "learning", "CheckCircle2", 15, "tasks", 1),
    ("tasks_10", "On a Mission", "Complete 10 roadmap tasks.", "learning", "Target", 60, "tasks", 10),
    ("roadmap_complete", "Roadmap Complete", "Finish every task in a roadmap.", "career", "Flag", 300, "roadmaps_completed", 1),
    ("hours_10", "Ten Hours In", "Study for 10 hours in total.", "learning", "Clock", 40, "hours", 10),
    ("hours_100", "100 Hours", "Study for 100 hours in total.", "learning", "Hourglass", 250, "hours", 100),
    ("streak_3", "Warming Up", "Study 3 days in a row.", "streak", "Flame", 20, "streak", 3),
    ("streak_7", "Week Warrior", "Study 7 days in a row.", "streak", "Flame", 50, "streak", 7),
    ("streak_30", "Unstoppable", "Study 30 days in a row.", "streak", "Flame", 200, "streak", 30),
    ("first_project", "Builder", "Finish your first project.", "projects", "Hammer", 40, "projects", 1),
    ("projects_5", "Portfolio Material", "Finish 5 projects.", "projects", "FolderKanban", 100, "projects", 5),
    ("boss_slayer", "Boss Slayer", "Defeat a monthly boss project.", "projects", "Swords", 100, "bosses", 1),
    ("first_quiz", "Quiz Passed", "Pass your first quiz.", "practice", "ClipboardCheck", 30, "quizzes_passed", 1),
    ("quizzes_5", "Quiz Master", "Pass 5 quizzes.", "practice", "Award", 80, "quizzes_passed", 5),
    ("first_interview", "Interview Ready", "Finish your first mock interview.", "practice", "Mic", 40, "interviews", 1),
    ("interviews_5", "Seasoned Candidate", "Finish 5 mock interviews.", "practice", "Mic", 120, "interviews", 5),
    ("curious_mind", "Curious Mind", "Ask the AI mentor a question.", "practice", "Bot", 10, "mentor_chats", 1),
    ("resume_ready", "Resume Ready", "Create your first career document.", "career", "FileText", 30, "documents", 1),
    ("portfolio_published", "Portfolio Published", "Make your portfolio public.", "career", "Briefcase", 60, "portfolio_public", 1),
    ("level_5", "Level 5", "Reach level 5.", "career", "Zap", 50, "level", 5),
    ("level_10", "Level 10", "Reach level 10.", "career", "Zap", 100, "level", 10),
]

# Career titles by total XP, lowest first.
TITLES: list[tuple[int, str]] = [
    (0, "Explorer"),
    (500, "Apprentice"),
    (1500, "Builder"),
    (4000, "Professional"),
    (10000, "Master"),
]

BOSS_BONUS_XP = 150


def career_title(xp: int) -> dict:
    """The learner's title for this much XP, the next one, and the XP still
    needed to reach it (None at the top)."""
    xp = max(xp, 0)
    index = 0

    for i, (needed, _) in enumerate(TITLES):
        if xp >= needed:
            index = i

    title = TITLES[index][1]

    if index + 1 < len(TITLES):
        needed, nxt = TITLES[index + 1]

        return {
            "title": title,
            "index": index,
            "next_title": nxt,
            "xp_to_next": needed - xp,
            "progress": (xp - TITLES[index][0]) / (needed - TITLES[index][0]),
        }

    return {"title": title, "index": index, "next_title": None, "xp_to_next": None, "progress": 1.0}
