# GOAT-Storytelling-Agent: Agent for writing consistent and interesting long stories for any fiction form
![Goat Agent](./images/GOAT-story.png)
## Description
GOAT-Storytelling-Agent writes consistent and  interesting stories over long context requiring only a standard LLM for text generation. By default it takes our open-source model, [GOAT-70B-Storytelling](https://huggingface.co/GOAT-AI/GOAT-70B-Storytelling), specifically tuned for the task.
The agent consists of several stages of planning and writing to build a story from top to down. A user can control the story creation at any preferred scale - starting from a basic novel description to the text of a specific scene. More details can be found in the [release blogpost](https://www.blog.goat.ai/goat-st/).

## Novella dataset
To demonstrate the capabilities of the agent, we release 20 novellas generated without human supervision requiring only single initial topic for input. The dataset is hosted as an HF dataset - [generated-novels](https://huggingface.co/datasets/GOAT-AI/generated-novels/tree/main/generated-books).

## Setup
1. Provide configuration details in `goat_storytelling_agent/config.py` with a text generation endpoint and huggingface access token for tokenizer initialization.

2. You can install the dependencies only

    ```pip install -r requirements.txt```

    or install as a package

    ```pip install -e .```

## Usage
### Generate a complete story from a topic (complete pipeline)
The whole pipeline consists of an interplay between different story elements. A whole story can be generated from scratch using the general pipeline. Currently, `HF(TGI)` and `Llama.cpp` text generation backends are supported, but can be extended to any engine.

```python
from goat_storytelling_agent.storytelling_agent import StoryAgent

backend_uri = # Text generation endpoint
writer = StoryAgent(backend_uri, form='novel')
novel_scenes = writer.generate_story('treasure hunt in a jungle')
```

Under the hood, `generate_story` performs following operations:
```python
msgs, book_spec = self.init_book_spec(topic)
msgs, book_spec = self.enhance_book_spec(book_spec)
msgs, plan = self.create_plot_chapters(book_spec)
msgs, plan = self.enhance_plot_chapters(book_spec, plan)
msgs, plan = self.split_chapters_into_scenes(plan)

form_text = []
for act in plan:
    for ch_num, chapter in act['chapter_scenes'].items():
        sc_num = 1
        for scene in chapter:
            previous_scene = form_text[-1] if form_text else None
            _, generated_scene = self.write_a_scene(
                scene, sc_num, ch_num, plan,
                previous_scene=previous_scene)
            form_text.append(generated_scene)
            sc_num += 1
```

Some of the steps will be reviewed in the examples below.
### Create novel ideas from a seed topic
It is possible to break down the generation process and have a more granular control over the story. `init_book_spec` command takes a topic and comes up with a book description consisting of predefined fields - Genre, Place, Time, Theme, Tone, Point of View, Characters, Premise. It is possible to add your own fields and then pass the spec in subsequent stages.

```python
message, book_spec = writer.init_book_spec(topic='treasure hunt in a jungle')
print(book_spec)
```
```output
Genre: Adventure Thriller
Place: Amazon Jungle, South America
Time: Present Day
Theme: Persistence, Survival, Discovery of ancient culture
Tone: Suspenseful, Tense
Point of View: Third person limited
Characters: Dr. Helen Carr, an archaeology professor; Ignacio, an experienced local guide; Bruno Hafner, a greedy treasure collector; Ana Maria, an idealistic student and local tribe leader, Kaya.
Premise: Dr. Helen Carr uncovers a map to an ancient artifact believed to be deep inside the Amazon Jungle. Teaming up with local guide, Ignacio, she embarks on a tense journey to locate the artifact before the ruthless treasure collector, Bruno Hafner, gets there first. Along the way, their path crosses with the idealistic student Ana Maria who is fascinated by the legend of the artifact. The plot thickens as Helen and her team rediscover a lost civilization and have to navigate through both physical dangers of the jungle and complex local politics represented by the tribe leader Kaya. In this race against time, they will also have to fight against the elements of jungle and not to fall into the trap set by Hafner while handling Kaya's tribe with respect and care.
```
### Create a by-chapter outline of the story
```python
from goat_storytelling_agent.plan import Plan

messages, plan = writer.create_plot_chapters(book_spec)
print(Plan.plan_2_str(plan))
```
```output
Act 1: Setting Up The Expedition
- Chapter 1: Dr. Helen Carr's discovery of an ancient map suggesting the location of a valuable artifact deep inside the Amazon Jungle.
- Chapter 2: rugged guide Ignacio and passionate anthropology student, Ana Maria.
- Chapter 3: The expedition's unexpected adversary - Bruno Hafner, a ruthless treasure collector with his technologically advanced team and similar intentions.

Act 2: Journey Through the Jungle and Revelations
- Chapter 4: The expedition commences - navigating treacherous terrain, confronting dangerous wildlife, and surviving on limited resources.
- Chapter 5: Tensions rise within the group due to the intense conditions. A riveting rescue from a piranha-infested river crossing builds trust.
- Chapter 6: The team discovers Kaya and her tribe, decedents of the tribe that created the artifact.
- Chapter 7: Ana Maria's revelation about her connection to Kaya's tribe creates new alliances and emotions.
- Chapter 8: Bruno Hafner's team attacks the village, attempting to steal the artifact's location. A brief skirmish reveals Ignacio's skilled combat past.
- Chapter 9: The staggering scale and sophistication of the underground cave are discovered. The booby-trapped chamber designed to protect the artifact provides a challenging hurdle.

Act 3: Showdown and Epilogue
- Chapter 10: An intense showdown between Helen's group and Bruno in the underground cave, culminating in thwarting Bruno's plans.
- Chapter 11: The true significance of the artifact unraveled, not just a historical treasure but a record of sustainable agricultural practices of the lost tribe.
- Chapter 12: The struggle to return the artifact from the clutches of Bruno and ensure its safe return to Kaya and her tribe.
- Chapter 13: Helen's team departs from the Amazon, leaving the artifact with Kaya's tribe. The journey has not only been about preserving history but also learning from it.
- Chapter 14: Back at the research facility, Helen's successful expedition has increased respect for her work and sparks new research on sustainable ancient practices. The lives of Helen, Ignacio, and Ana Maria are forever changed through their shared adventure and experiences.
```

### Create a by-scene outline
`split_chapters_into_scenes` takes the generated Plan object with chapter outlines and break each into scenes in a predefined format - Characters, Place, Time, Event, Conflct, Story value, Story value charge, Mood, Outcome.
```python
messages, plan = writer.split_chapters_into_scenes(plan)
act_n = 0
scene_n = 0
chapter_n = 1
scene_descr = plan[act_n]['chapter_scenes'][chapter_n][scene_n]
print(scene_descr)
```
```output
Chapter 1:
Scene 1:
Characters: Dr. Helen Carr
Place: Helen's office
Time: Morning
Event: Helen uncovers an ancient map
Conflict: Decoding the map's information successfully
Story value: Knowledge
Story value charge: Positive
Mood: Curiosity
Outcome: A potential location of the priceless artifact is discovered.
```

### Generate scene text based on the plan
Finally, it is possible to generate the scene text with `write_a_scene`. Sometimes the whole text would not fit into the context window, so there is a `continue_a_scene` function that continues the text for the same scene given the progress so far.
```python
messages, generated_scene = writer.write_a_scene(
    scene_descr, sc_num+1, ch_num, plan, previous_scene=None)
```
```
Chapter 1: Unveiling Secrets

Dr. Helen Carr was no stranger to mystery. Within the confines of her
office at the prestigious Oxford University, the archaeologist had 
brought age-old artifacts to life, disseminating enigmatic tales of 
civilizations long lost. Under the golden hue of her desk lamp this 
cool morning, stood an object of ultimate intrigue - an ancient map 
she'd discovered on her last expedition to Peru.

The map was an intricate dance of color and lines, a kaleidoscope of 
symbols that caught Helen's eyes. She sat at her desk, her steaming 
cup of Earl Grey ignored as she poured over the parchment, a delicious 
thrill coursing through her veins. The map bore its age with grace, 
the edges slightly singed, mocking her with its stoic silence.

She felt that some secrets were locked inside this parchment. "Talk to 
me", Helen whispered to herself, her eyes squinting at the delicately 
inscribed symbols. Her fingers traced the lines of the map, feeling 
the faintest etchings, the texture almost whispering the tales of yore.

Suddenly, she paused. Her heart throbbed a little as she looked at a 
part of the map that felt different from the rest. Helen lowered her 
eyeglasses down to her nose, peering at a set of unusual inscriptions. 

Her blood was now a concerto of adrenaline. Something was uncannily 
remarkable with the characters etched. "An undiscovered dialect? No." 
Helen muttered. The characters resembled a form of ancient Amazonian 
language. But this wasn't right, ancient Amazonian dialect wasn't a 
writing language.

Determinedly, she grabbed several volumes from her bookshelf, each a 
hefty tome of knowledge on South American civilizations. Helen 
immersed herself in study, to decode the curious symbols. The aroma of 
old books mixed with her dampening enthusiasm, turning the hours into 
seconds.

Just as lunch time approached, the mood of frustration counterpointed 
with a moment of insight. With shaking hands, Helen drew parallels 
between the symbols and ancient Amazonian petroglyphs, forgotten by 
the world except for a handful of scholars such as herself.

As she successfully decoded the symbols one after another, the meaning 
dawned on her - the location of a priceless artifact, hidden within 
the unfathomable Amazon jungle depths. Helen's heart thumped loudly in 
her ears. This ethereal moment held a mesmerizing potential - 
countless years of seasoned research leading to an extraordinary 
discovery.

Reverently, she touched the map again, feeling a boundless respect 
towards the ancient civilization. They had safeguarded their 
knowledge, handed it down until it found its way into her hands, to 
unfurl its story and hand it down to posterity. Months of meticulously 
planned expeditions would follow, but now, she savored this moment of 
solitary discovery.

The clock on the wall read noon but this ordinary morning had turned 
extraordinary for Dr. Helen Carr. The walls of her office bore silent 
witness to a remarkable revelation, one that could change the course 
of history.
```
