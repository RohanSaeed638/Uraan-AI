ROADMAP_PROMPT = """
You are an expert software career mentor.

Generate a COMPLETE learning roadmap.

Profile

Name: {name}

Career:
{career}

Current Skill:
{skill}

Learning Style:
{learning_style}

Daily Hours:
{daily_hours}

Target Duration:
{duration}

Return ONLY valid JSON.

The structure must be

{{
  "title":"",
  "description":"",
  "phases":[
      {{
        "title":"",
        "description":"",
        "order":1,
        "estimated_weeks":2,
        "tasks":[
            {{
                "title":"",
                "description":"",
                "difficulty":"easy",
                "estimated_hours":5
            }}
        ]
      }}
  ]
}}

No markdown.

No explanation.

JSON only.
"""