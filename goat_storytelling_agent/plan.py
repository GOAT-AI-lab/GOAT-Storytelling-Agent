"""Unifies all plot forms such as by-chapter and by-scene outlines in a single dict."""
import re
import json


class Plan:
    @staticmethod
    def split_by_act(original_plan):
        # removes only Act texts with newline prepended soemwhere near
        acts = re.split('\n.{0,5}?Act ', original_plan)
        # remove random short garbage from re split
        acts = [text.strip() for text in acts[:]
                if (text and (len(text.split()) > 3))]
        if len(acts) == 4:
            acts = acts[1:]
        elif len(acts) != 3:
            print('Fail: split_by_act, attempt 1', original_plan)
            acts = original_plan.split('Act ')
            if len(acts) == 4:
                acts = acts[-3:]
            elif len(acts) != 3:
                print('Fail: split_by_act, attempt 2', original_plan)
                return []

        # [act1, act2, act3], [Act + act1, act2, act3]
        if acts[0].startswith('Act '):
            acts = [acts[0]] + ['Act ' + act for act in acts[1:]]
        else:
            acts = ['Act ' + act for act in acts[:]]
        return acts

    @staticmethod
    def parse_act(act):
        act = re.split(r'\n.{0,20}?Chapter .+:', act.strip())
        chapters = [text.strip() for text in act[1:]
                    if (text and (len(text.split()) > 3))]
        return {'act_descr': act[0].strip(), 'chapters': chapters}

    @staticmethod
    def parse_text_plan(text_plan):
        acts = Plan.split_by_act(text_plan)
        if not acts:
            return []
        plan = [Plan.parse_act(act) for act in acts if act]
        plan = [act for act in plan if act['chapters']]
        return plan

    @staticmethod
    def normalize_text_plan(text_plan):
        plan = Plan.parse_text_plan(text_plan)
        text_plan = Plan.plan_2_str(plan)
        return text_plan

    @staticmethod
    def act_2_str(plan, act_num):
        text_plan = ''
        chs = []
        ch_num = 1
        for i, act in enumerate(plan):
            act_descr = act['act_descr'] + '\n'
            if not re.search(r'Act \d', act_descr[0:50]):
                act_descr = f'Act {i+1}:\n' + act_descr
            for chapter in act['chapters']:
                if (i + 1) == act_num:
                    act_descr += f'- Chapter {ch_num}: {chapter}\n'
                    chs.append(ch_num)
                elif (i + 1) > act_num:
                    return text_plan.strip(), chs
                ch_num += 1
            text_plan += act_descr + '\n'
        return text_plan.strip(), chs

    @staticmethod
    def plan_2_str(plan):
        text_plan = ''
        ch_num = 1
        for i, act in enumerate(plan):
            act_descr = act['act_descr'] + '\n'
            if not re.search(r'Act \d', act_descr[0:50]):
                act_descr = f'Act {i+1}:\n' + act_descr
            for chapter in act['chapters']:
                act_descr += f'- Chapter {ch_num}: {chapter}\n'
                ch_num += 1
            text_plan += act_descr + '\n'
        return text_plan.strip()

    @staticmethod
    def save_plan(plan, fpath):
        with open(fpath, 'w') as fp:
            json.dump(plan, fp, indent=4)
