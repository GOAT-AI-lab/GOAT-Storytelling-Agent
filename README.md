# GOAT-STORYTELLING-AGENT: Agent that writes consistent and interesting long stories for any fiction form
## Description
GOAT-STORYTELLING-AGENT is a framework that allows to write interesting and consistent stories over long context requiring only a standard LLM for text generation. By default it takes our model, GOAT-70B-STORYTELLING, specifically tuned for the task.
The framework consists of several stages of planning and writing to build a story from top to down. A user can control the story creation at any preferred scale - starting from a basic novel description to the text of a specific scene.

## Installation
You can install the dependencies only

```pip install -r requirements.txt```

or install as a package

```pip install -e .```

## Usage
### Generate a complete story from a topic (complete pipeline)
The whole pipeline consists of an interplay between different story elements. A whole story can be generated from scratch using the general pipeline. More granular control is also possible.

```python
from tolkien.story_processor.prompt_manager import generate_story

novel_scenes = generate_story('never too much coffee', form='novel')
```
