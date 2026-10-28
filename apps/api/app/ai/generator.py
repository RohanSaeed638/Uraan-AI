class DummyRoadmapGenerator:

    def generate(
        self,
        profile,
    ):

        return {
            "title": f"{profile.career_slug} Roadmap",
            "description": f"Personalized roadmap for {profile.full_name}",

            "phases":[

                {

                    "title":"Programming Basics",

                    "description":"Build strong fundamentals.",

                    "tasks":[

                        {

                            "title":"Learn Variables",

                            "description":"Study variables and data types.",

                            "estimated_hours":3

                        },

                        {

                            "title":"Practice Exercises",

                            "description":"Solve 20 beginner problems.",

                            "estimated_hours":4

                        }

                    ]

                },

                {

                    "title":"Functions",

                    "description":"Learn reusable code.",

                    "tasks":[

                        {

                            "title":"Functions",

                            "description":"Create reusable functions.",

                            "estimated_hours":4

                        }

                    ]

                }

            ]

        }