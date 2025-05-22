system = (
    "You are a helpful assistant for fiction writing. "
    "Provide direct, concise outlines with useful details. Adhere strictly to requested formats. "
    "Ensure outputs are grounded and internally consistent with the specified genre, "
    "avoiding overly fantastical or unrealistic elements unless appropriate for the genre.")

book_spec_fields = ['Genre', 'Place', 'Time', 'Theme',
                    'Tone', 'Point of View', 'Characters', 'Premise']

book_spec_format = (
    "Genre: genre\n"
    "Place: place\n"
    "Time: period\n"
    "Theme: main topics\n"
    "Tone: tone\n"
    "Point of View: POV\n"
    "Characters: use specific names already\n"
    "Premise: Describe concrete events, focusing on exciting situations, complex relationships, and potentially scandalous or unconventional choices, in the style of a show like 'Californication'. Think about affairs, unexpected entanglements, and character-driven drama.")

scene_spec_format = (
    "Chapter [number]:\nScene [number]:\nCharacters: character list\nPlace: place\nTime: absolute or relative time\nEvent: what happens\nConflict: scene micro-conflict\n"
    "Story value: story value affected by the scene\nStory value charge: the charge of story value by the end of the scene (positive or negative)\nMood: mood\nOutcome: the result.")

prev_scene_intro = "\n\nHere is the ending of the previous scene:\n"
cur_scene_intro = "\n\nHere is the last written snippet of the current scene:\n"


def init_book_spec_messages(topic, form):
    messages = [
        {"role": "system", "content": system},
        {"role": "user",
         "content": f"Given the topic, come up with a specification to write a {form}. "
                    f"Strictly follow the format below, ensuring all fields are present.\n"
                    f"Topic: {topic}\nFormat:\n\"\"\"\n{book_spec_format}\"\"\""}
    ]
    return messages


def missing_book_spec_messages(field, text_spec):
    messages = [
        {"role": "system", "content": system},
        {"role": "user",
         "content": (
            f"Given a hypothetical book spec, fill the missing field: {field}."
            f'Return only field, separator and value in one line like "Field: value".\n'
            f'Book spec:\n"""{text_spec}"""')
        }
    ]
    return messages


def enhance_book_spec_messages(book_spec, form):
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content":
            f"Make the specification for an upcoming {form} more detailed "
            f"(specific settings, major events that differentiate the {form} "
            f"from others). Do not change the format or add more fields."
            f"\nEarly {form} specification:\n\"\"\"{book_spec}\"\"\""}
    ]
    return messages


def create_plot_chapters_messages(book_spec, form):
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": (
            f"Come up with a plot for a bestseller-grade {form} in 3 acts taking inspiration from its description. "
            "Break down the plot into chapters using the following structure:\nActs\n- Chapters\n\n"
            f"Early {form} description:\n\"\"\"{book_spec}\"\"\".")}
    ]
    return messages


def enhance_plot_chapters_messages(act_num, text_plan, book_spec, form):
    act_num += 1
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Come up with a plot for a bestseller-grade {form} in 3 acts. Break down the plot into chapters using the following structure:\nActs\n- Chapters\n\nEarly {form} description:\n\"\"\"{book_spec}\"\"\""},
        {"role": "assistant", "content": text_plan},
        {"role": "user", "content": f"Take Act {act_num}. Rewrite the plan so that chapter's story value alternates (i.e. if Chapter 1 is positive, Chapter 2 is negative, and so on). Describe only concrete events and actions (who did what). Make it very short (one brief sentence and value charge indication per chapter)"}
    ]
    return messages


def split_chapters_into_scenes_messages(act_num, text_act, form):
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": (
            f"Break each chapter in Act {act_num} into scenes (number depends on how packed a chapter is). "
            f"For each scene, provide specifications strictly adhering to the format below, ensuring all fields are included for every scene.\n"
            f"Here is the by-chapter plot summary for the act in a {form}:\n\"\"\"{text_act}\"\"\"\n\n"
            f"Scene spec format:\n\"\"\"{scene_spec_format}\"\"\"\n\n"
            f"For example, a single scene specification should look like this (ensure all fields are present):\n"
            f"Chapter 1:\nScene 1:\nCharacters: Character A, Character B\nPlace: A dark forest\nTime: Midnight\nEvent: Character A finds a mysterious object.\nConflict: Character B wants the object too.\n"
            f"Story value: Mystery\nStory value charge: Positive\nMood: Suspenseful\nOutcome: Character A keeps the object, Character B is resentful.")}
    ]
    return messages


def scene_messages(scene, sc_num, ch_num, text_plan, form):
    messages = [
        {"role": "system", "content": 'You are an expert fiction writer. Write detailed scenes with lively dialogue.'},
        {"role": "user",
            "content": f"Write a long detailed scene for a {form} for scene {sc_num} in chapter {ch_num} based on the information. "
            "Be creative, explore interesting characters and unusual settings. Do NOT use foreshadowing.\n"
            f"Here is the scene specification:\n\"\"\"{scene}\"\"\"\n\nHere is the overall plot:\n\"\"\"{text_plan}\"\"\""},
        {"role": "assistant", "content": f"\nChapter {ch_num}, Scene {sc_num}\n"},
    ]
    return messages
