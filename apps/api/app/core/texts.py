"""Messages the server itself writes for a learner (notifications, the
dashboard fallback line), in each language they can pick.

`text(key, language, **values)` fills the placeholders. English is the source;
an unknown language or key falls back to English so a message is never blank.
The Urdu and Roman Urdu wording is an AI draft for a native speaker to review
(see README, Languages)."""

_TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "email_open": "Open Uraan AI",
        "email_reason": "You get this email because email notifications are on for your account.",
        "email_unsubscribe": "Unsubscribe",
        "email_settings": "Change what you get in Settings",
        "streak_title": "{days}-day streak! 🔥",
        "streak_body": "You have studied {days} days in a row. Keep it going.",
        "daily_streak_title": "Keep your {days}-day streak alive",
        "daily_streak_body": "One lesson today keeps it going. Finish today's quest.",
        "daily_start_title": "Time to study",
        "daily_start_body": "Start a lesson today and begin a new streak.",
        "weekly_title": "Your weekly summary",
        "weekly_xp": "You earned {xp} XP last week. Let's beat it.",
        "weekly_fresh": "A fresh week starts now. Pick up where you left off.",
        "achievement_title": "Achievement unlocked: {title}",
        "achievement_body": "{description} +{xp} XP",
        "boss_title": "Boss project defeated!",
        "boss_body": "You finished this month's boss project. +{xp} XP",
        "plan_updated": "Your study plan was updated",
        "moved_one": "We moved {count} lesson to keep you on track",
        "moved_other": "We moved {count} lessons to keep you on track",
        "moved_missed": "You did not get to everything planned yesterday.",
        "moved_until": "You did not get to everything planned yesterday. Your plan now finishes on {date}.",
        "fallback_streak": "{days} days in a row: that is real momentum.",
        "fallback_today": "You have already studied today. Well done.",
        "fallback_start": "Every expert started with one lesson.",
        "fallback_next": "{base} Next up: {lesson}.",
        "fallback_pick": "{base} Pick a lesson and begin.",
    },
    "ur": {
        "email_open": "Uraan AI کھولیں",
        "email_reason": "آپ کو یہ ای میل اس لیے مل رہی ہے کہ آپ کے اکاؤنٹ پر ای میل اطلاعات آن ہیں۔",
        "email_unsubscribe": "ان سبسکرائب کریں",
        "email_settings": "ترتیبات میں اپنی پسند تبدیل کریں",
        "streak_title": "{days} دن کی مسلسل محنت! 🔥",
        "streak_body": "آپ مسلسل {days} دن سے پڑھ رہے ہیں۔ اسے جاری رکھیں۔",
        "daily_streak_title": "اپنی {days} دن کی مسلسل محنت جاری رکھیں",
        "daily_streak_body": "آج ایک سبق اسے جاری رکھے گا۔ آج کا مشن مکمل کریں۔",
        "daily_start_title": "پڑھنے کا وقت ہو گیا",
        "daily_start_body": "آج ایک سبق شروع کریں اور نئی مسلسل محنت کا آغاز کریں۔",
        "weekly_title": "آپ کا ہفتہ وار خلاصہ",
        "weekly_xp": "آپ نے پچھلے ہفتے {xp} XP کمائے۔ آئیے اسے بہتر بنائیں۔",
        "weekly_fresh": "نیا ہفتہ شروع ہو گیا ہے۔ جہاں چھوڑا تھا وہیں سے جاری رکھیں۔",
        "achievement_title": "کامیابی حاصل ہوئی: {title}",
        "achievement_body": "{description} +{xp} XP",
        "boss_title": "بڑا پروجیکٹ مکمل!",
        "boss_body": "آپ نے اس مہینے کا بڑا پروجیکٹ مکمل کر لیا۔ +{xp} XP",
        "plan_updated": "آپ کا مطالعے کا منصوبہ اپ ڈیٹ ہو گیا",
        "moved_one": "ہم نے آپ کو ٹریک پر رکھنے کے لیے {count} سبق منتقل کیا",
        "moved_other": "ہم نے آپ کو ٹریک پر رکھنے کے لیے {count} سبق منتقل کیے",
        "moved_missed": "کل جو کچھ طے تھا وہ سب مکمل نہیں ہو سکا۔",
        "moved_until": "کل جو کچھ طے تھا وہ سب مکمل نہیں ہو سکا۔ آپ کا منصوبہ اب {date} کو مکمل ہو گا۔",
        "fallback_streak": "{days} دن مسلسل: یہی اصل رفتار ہے۔",
        "fallback_today": "آپ آج پڑھ چکے ہیں۔ شاباش۔",
        "fallback_start": "ہر ماہر نے ایک سبق سے آغاز کیا تھا۔",
        "fallback_next": "{base} اگلا: {lesson}۔",
        "fallback_pick": "{base} ایک سبق چنیں اور شروع کریں۔",
    },
    "ur-Latn": {
        "email_open": "Uraan AI kholein",
        "email_reason": "Aap ko yeh email is liye mil rahi hai ke aap ke account par email notifications on hain.",
        "email_unsubscribe": "Unsubscribe karein",
        "email_settings": "Settings mein apni pasand tabdeel karein",
        "streak_title": "{days} din ki streak! 🔥",
        "streak_body": "Aap musalsal {days} din se parh rahe hain. Isay jari rakhein.",
        "daily_streak_title": "Apni {days} din ki streak barqarar rakhein",
        "daily_streak_body": "Aaj aik sabaq isay jari rakhega. Aaj ka mission mukammal karein.",
        "daily_start_title": "Parhne ka waqt ho gaya",
        "daily_start_body": "Aaj aik sabaq shuru karein aur nayi streak ka aghaz karein.",
        "weekly_title": "Aap ka haftawar khulasa",
        "weekly_xp": "Aap ne pichle hafte {xp} XP kamaye. Aayiye isay behtar banayein.",
        "weekly_fresh": "Naya hafta shuru ho gaya hai. Jahan chhora tha wahin se jari rakhein.",
        "achievement_title": "Kamyabi hasil hui: {title}",
        "achievement_body": "{description} +{xp} XP",
        "boss_title": "Bara project mukammal!",
        "boss_body": "Aap ne is mahine ka bara project mukammal kar liya. +{xp} XP",
        "plan_updated": "Aap ka parhai ka mansooba update ho gaya",
        "moved_one": "Humne aap ko track par rakhne ke liye {count} sabaq muntaqil kiya",
        "moved_other": "Humne aap ko track par rakhne ke liye {count} sabaq muntaqil kiye",
        "moved_missed": "Kal jo kuch tay tha woh sab mukammal nahin ho saka.",
        "moved_until": "Kal jo kuch tay tha woh sab mukammal nahin ho saka. Aap ka mansooba ab {date} ko mukammal hoga.",
        "fallback_streak": "{days} din musalsal: yehi asal raftaar hai.",
        "fallback_today": "Aap aaj parh chuke hain. Shabash.",
        "fallback_start": "Har mahir ne aik sabaq se aghaz kiya tha.",
        "fallback_next": "{base} Agla: {lesson}.",
        "fallback_pick": "{base} Aik sabaq chunein aur shuru karein.",
    },
}

_MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "ur": ["جنوری", "فروری", "مارچ", "اپریل", "مئی", "جون", "جولائی", "اگست", "ستمبر", "اکتوبر", "نومبر", "دسمبر"],
}
_MONTHS["ur-Latn"] = _MONTHS["en"]


def text(key: str, language: str | None = None, **values) -> str:
    table = _TEXTS.get(language or "en", _TEXTS["en"])
    template = table.get(key) or _TEXTS["en"][key]

    return template.format(**values)


def short_date(value, language: str | None = None) -> str:
    """"Nov 3" (or the month in Urdu): a date as written inside a message."""
    months = _MONTHS.get(language or "en", _MONTHS["en"])

    return f"{months[value.month - 1]} {value.day}" if language != "ur" else f"{value.day} {months[value.month - 1]}"
