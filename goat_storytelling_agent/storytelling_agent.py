import os
import time
import re
import json
import requests
import traceback

from transformers import LlamaTokenizerFast

from src import prompts, utils
from src.config import ENDPOINT, HF_ACCESS_TOKEN
from src.plan import Plan


tokenizer = LlamaTokenizerFast.from_pretrained(
    "GOAT-AI/GOAT-70B-Storytelling")


def _query_chat(messages, retries=3, request_timeout=120):
    prompt = ''
    for message in messages:
        if message['role'] == 'user':
            prompt += '### USER: ' + message['content'] + '\n'
        elif message['role'] == 'assistant':
            prompt += '### ASSISTANT: ' + message['content'] + '\n'
    prompt += '### ASSISTANT: '
    tokens = tokenizer(prompt, add_special_tokens=True,
                       truncation=False)['input_ids']
    data = {
        "inputs": prompt,
        "parameters": {
            'max_new_tokens': 4096 - len(tokens),
            'do_sample': True
        }
    }
    headers = {'Content-Type': 'application/json'}
    while retries > 0:
        try:
            response = requests.post(
                ENDPOINT, headers=headers, data=json.dumps(data),
                timeout=request_timeout)
            generated_text = json.loads(response.text)['generated_text']
            return generated_text
        except Exception:
            traceback.print_exc()
            print('Timeout error, retrying...')
            retries -= 1
            time.sleep(5)
    else:
        return ''


def parse_book_spec(text_spec, fields=prompts.book_spec_fields):
    # Initialize book spec dict with empty fields
    spec_dict = {field: '' for field in fields}
    last_field = None
    if "\"\"\"" in text_spec[:int(len(text_spec)/2)]:
        header, sep, text_spec = text_spec.partition("\"\"\"")
    text_spec = text_spec.strip()

    # Process raw spec into dict
    for line in text_spec.split('\n'):
        pseudokey, sep, value = line.partition(':')
        pseudokey = pseudokey.lower().strip()
        matched_key = [key for key in fields
                       if (key.lower().strip() in pseudokey)
                       and (len(pseudokey) < (2 * len(key.strip())))]
        if (':' in line) and (len(matched_key) == 1):
            last_field = matched_key[0]
            if last_field in spec_dict:
                spec_dict[last_field] += value.strip()
        elif ':' in line:
            last_field = 'other'
            spec_dict[last_field] = ''
        else:
            if last_field:
                # If line does not contain ':' it should be
                # the continuation of the last field's value
                spec_dict[last_field] += ' ' + line.strip()
    spec_dict.pop('other', None)
    return spec_dict


def init_book_spec(topic, form='novel', query_chat=_query_chat):
    """Creates initial book specification

    Parameters
    ----------
    topic : str
        Short initial topic
    form : str, optional
        A story form to create, by default 'novel'
    query_chat : fn, optional
        A function that sends queries to a text generation engine, by default _query_chat

    Returns
    -------
    List[Dict]
        Used messages for logging
    str
        Book specification text
    """
    messages = prompts.init_book_spec_messages(topic, form)
    text_spec = query_chat(messages)
    spec_dict = parse_book_spec(text_spec)

    text_spec = "\n".join(f"{key}: {value}"
                          for key, value in spec_dict.items())
    # Check and fill in missing fields
    for field in prompts.book_spec_fields:
        while not spec_dict[field]:
            messages[1]['content'] = (
                f'{prompts.missing_field_prompt[0]}{field}'
                f'{prompts.missing_field_prompt[1]}{text_spec}'
                f'{prompts.missing_field_prompt[2]}')
            missing_part = query_chat(messages)
            key, sep, value = missing_part.partition(':')
            if key.lower().strip() == field.lower().strip():
                spec_dict[field] = value.strip()
    text_spec = "\n".join(f"{key}: {value}"
                          for key, value in spec_dict.items())
    return messages, text_spec


def enhance_book_spec(book_spec, form='novel', query_chat=_query_chat):
    """Make book specification more detailed

    Parameters
    ----------
    book_spec : str
        Book specification
    form : str, optional
        A story form to create, by default 'novel'
    query_chat : fn, optional
        A function that sends queries to a text generation engine, by default _query_chat

    Returns
    -------
    List[Dict]
        Used messages for logging
    str
        Book specification text
    """
    messages = prompts.enhance_book_spec_messages(book_spec, form)
    text_spec = query_chat(messages)
    spec_dict_old = parse_book_spec(book_spec)
    spec_dict_new = parse_book_spec(text_spec)

    # Check and fill in missing fields
    for field in prompts.book_spec_fields:
        if not spec_dict_new[field]:
            spec_dict_new[field] = spec_dict_old[field]

    text_spec = "\n".join(f"{key}: {value}"
                          for key, value in spec_dict_new.items())
    return messages, text_spec


def create_plot_chapters(book_spec, form='novel', query_chat=_query_chat):
    """Create initial by-plot outline of form

    Parameters
    ----------
    book_spec : str
        Book specification
    form : str, optional
        A story form to create, by default 'novel'
    query_chat : fn, optional
        A function that sends queries to a text generation engine, by default _query_chat

    Returns
    -------
    List[Dict]
        Used messages for logging
    dict
        Dict with book plan
    """
    messages = prompts.create_plot_chapters_messages(book_spec, form)
    plan = []
    while not plan:
        text_plan = query_chat(messages, request_timeout=120)
        if text_plan:
            plan = Plan.parse_text_plan(text_plan)
    return messages, plan


def enhance_plot_chapters(
        book_spec, plan, form='novel', query_chat=_query_chat):
    """Enhances the outline to make the flow more engaging

    Parameters
    ----------
    book_spec : str
        Book specification
    plan : Dict
        Dict with book plan
    form : str, optional
        A story form to create, by default 'novel'
    query_chat : fn, optional
        A function that sends queries to a text generation engine, by default _query_chat

    Returns
    -------
    List[Dict]
        Used messages for logging
    dict
        Dict with updated book plan
    """
    text_plan = Plan.plan_2_str(plan)
    all_messages = []
    for i in range(3):
        messages = prompts.enhance_plot_chapters_messages(
            text_plan, book_spec, form)
        act = query_chat(messages)
        if act:
            act_dict = Plan.parse_act(act)
            while len(act_dict['chapters']) < 2:
                act = query_chat(messages)
                act_dict = Plan.parse_act(act)
            else:
                plan[i] = act_dict
            text_plan = Plan.plan_2_str(plan)
        all_messages.append(messages)
    return all_messages, plan


def split_chapters_into_scenes(plan, form='novel', query_chat=_query_chat):
    """Creates a by-scene breakdown of all chapters

    Parameters
    ----------
    plan : Dict
        Dict with book plan
    form : str, optional
        A story form to create, by default 'novel'
    query_chat : fn, optional
        A function that sends queries to a text generation engine, by default _query_chat

    Returns
    -------
    List[Dict]
        Used messages for logging
    dict
        Dict with updated book plan
    """
    all_messages = []
    act_chapters = {}
    for i, act in enumerate(plan, start=1):
        text_act, chs = Plan.act_2_str(plan, i)
        act_chapters[i] = chs
        messages = prompts.split_chapters_into_scenes_messages(
            i, text_act, form)
        act_scenes = query_chat(messages, request_timeout=120)
        act['act_scenes'] = act_scenes
        all_messages.append(messages)

    for i, act in enumerate(plan, start=1):
        act_scenes = act['act_scenes']
        act_scenes = re.split(r'Chapter (\d+)', act_scenes.strip())

        act['chapter_scenes'] = {}
        chapters = [text.strip() for text in act_scenes[:]
                    if (text and text.strip())]
        current_ch = None
        merged_chapters = {}
        for snippet in chapters:
            if snippet.isnumeric():
                ch_num = int(snippet)
                if ch_num != current_ch:
                    current_ch = snippet
                    merged_chapters[ch_num] = ''
                continue
            if merged_chapters:
                merged_chapters[ch_num] += snippet
        ch_nums = list(merged_chapters.keys()) if len(
            merged_chapters) <= len(act_chapters[i]) else act_chapters[i]
        merged_chapters = {ch_num: merged_chapters[ch_num]
                           for ch_num in ch_nums}
        for ch_num, chapter in merged_chapters.items():
            scenes = re.split(r'Scene \d+.{0,10}?:', chapter)
            scenes = [text.strip() for text in scenes[1:]
                      if (text and (len(text.split()) > 3))]
            if not scenes:
                continue
            act['chapter_scenes'][ch_num] = scenes
    return all_messages, plan


def prepare_scene_text(text):
    lines = text.split('\n')
    ch_ids = [i for i in range(5)
              if 'Chapter ' in lines[i]]
    if ch_ids:
        lines = lines[ch_ids[-1]+1:]
    sc_ids = [i for i in range(5)
              if 'Scene ' in lines[i]]
    if sc_ids:
        lines = lines[sc_ids[-1]+1:]

    placeholder_i = None
    for i in range(len(lines)):
        if lines[i].startswith('Chapter ') or lines[i].startswith('Scene '):
            placeholder_i = i
            break
    if placeholder_i is not None:
        lines = lines[:i]

    text = '\n'.join(lines)
    return text


def write_a_scene(
        scene, sc_num, ch_num, plan, previous_scene=None,
        form='novel', query_chat=_query_chat, n_crop_previous=400):
    """Generates a scene text for a form

    Parameters
    ----------
    scene : str
        Scene description
    sc_num : int
        Scene number
    ch_num : int
        Chapter number
    plan : Dict
        Dict with book plan
    previous_scene : str, optional
        Previous scene text, by default None
    form : str, optional
        A story form to create, by default 'novel'
    query_chat : fn, optional
        A function that sends queries to a text generation engine, by default _query_chat
    n_crop_previous : int, optional
        Number of words to leave for the previous scene, by default 400

    Returns
    -------
    List[Dict]
        Used messages for logging
    str
        Generated scene text
    """
    text_plan = Plan.plan_2_str(plan)
    messages = prompts.scene_messages(scene, sc_num, ch_num, text_plan, form)
    if previous_scene:
        previous_scene = utils.keep_last_n_words(previous_scene,
                                                 n=n_crop_previous)
        messages[1]['content'] += f'{prompts.prev_scene_intro}\"\"\"{previous_scene}\"\"\"'
    generated_scene = query_chat(messages, request_timeout=120)
    generated_scene = prepare_scene_text(generated_scene)
    return messages, generated_scene


def continue_a_scene(
        scene, sc_num, ch_num, plan, current_scene=None, form='novel',
        query_chat=_query_chat, n_crop_previous=400):
    """Continues a scene text for a form

    Parameters
    ----------
    scene : str
        Scene description
    sc_num : int
        Scene number
    ch_num : int
        Chapter number
    plan : Dict
        Dict with book plan
    current_scene : str, optional
        Text of the current scene so far, by default None
    form : str, optional
        A story form to create, by default 'novel'
    query_chat : fn, optional
        A function that sends queries to a text generation engine, by default _query_chat
    n_crop_previous : int, optional
        Number of words to leave for the current scene history, by default 400

    Returns
    -------
    List[Dict]
        Used messages for logging
    str
        Generated scene continuation text
    """
    text_plan = Plan.plan_2_str(plan)
    messages = prompts.scene_messages(scene, sc_num, ch_num, text_plan, form)
    if current_scene:
        current_scene = utils.keep_last_n_words(current_scene,
                                                n=n_crop_previous)
        messages[1]['content'] += f'{prompts.cur_scene_intro}\"\"\"{current_scene}\"\"\"'
    generated_scene = query_chat(messages, request_timeout=120)
    generated_scene = prepare_scene_text(generated_scene)
    return messages, generated_scene


def generate_story(topic, form):
    """Example pipeline for novel creation"""
    _, book_spec = init_book_spec(topic, form=form)
    _, book_spec = enhance_book_spec(book_spec, form=form)
    _, plan = create_plot_chapters(book_spec, form=form)
    _, plan = enhance_plot_chapters(book_spec, plan, form=form)
    _, plan = split_chapters_into_scenes(plan, form=form)

    form_text = []
    for act in plan:
        for ch_num, chapter in act['chapter_scenes'].items():
            sc_num = 1
            for scene in chapter:
                previous_scene = form_text[-1] if form_text else None
                _, generated_scene = write_a_scene(
                    scene, sc_num, ch_num, plan, previous_scene=previous_scene, form=form)
                form_text.append(generated_scene)
                sc_num += 1
    return form_text
