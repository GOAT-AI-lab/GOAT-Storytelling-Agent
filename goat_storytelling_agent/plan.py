"""Unifies all plot forms such as by-chapter and by-scene outlines in a single dict."""
import re
import json


class Plan:
    @staticmethod
    def split_by_act(original_plan):
        # Improved regex to handle variable whitespace, optional act numbers (Arabic/Roman),
        # optional separators, and case-insensitivity.
        # This regex splits *after* the "Act [Number]:" part.
        acts = re.split(r'\n\s*Act\s*(?:\d+|[IVXLCDM]+)?[:.\s]*', original_plan, flags=re.IGNORECASE)

        # Filter out any empty strings resulting from the split, especially the first one if original_plan starts with "Act...".
        # Also remove very short or whitespace-only strings that are unlikely to be valid act content.
        acts = [text.strip() for text in acts if text and text.strip()]

        # After filtering, if the plan was well-formed, we expect 3 acts.
        # The initial split might have produced more if there were "Act..." like patterns within an act's content,
        # but the primary goal here is to get the main 3 act divisions.
        # The old logic checking for len(acts) == 4 and then slicing is covered by the general filter above.

        if len(acts) != 3:
            print(f'Fail: split_by_act, attempt 1 (found {len(acts)} acts after regex split). Original plan: {original_plan[:500]}...')
            # Fallback logic
            acts = original_plan.split('Act ') # This is a simpler split
            # Filter out empty strings from fallback
            acts = [text.strip() for text in acts if text and text.strip()]
            
            # The original fallback was:
            # if len(acts) == 4:
            #     acts = acts[-3:] # If 'Act ' was at the beginning, it would create an empty string at acts[0]
            # elif len(acts) != 3:
            #     print('Fail: split_by_act, attempt 2', original_plan)
            #     return []
            # The new filter handles the empty string case. We just need to check if we have 3 acts.
            # If the first part of original_plan was "Act X: ...", then split('Act ') would result in ["", "X: ...", "Y: ...", "Z: ..."]
            # So, if the first element is empty or just a number/colon, it might need adjustment.
            # However, the goal is to return the content of the acts.
            # If the fallback split by 'Act ' results in parts like " 1: ...", " 2: ...", " 3: ..."
            # we might want to strip the " <number>: " part.
            # For now, let's simplify the fallback handling: if it doesn't give 3 parts, it fails.
            # The primary regex should handle most cases.

            # A more direct check: if the first element after split is empty, it means "Act " was at the start.
            if original_plan.lower().strip().startswith("act") and acts and not original_plan.split('Act ', 1)[0].strip():
                 # This implies the first element of `acts` (after splitting by 'Act ') might be an empty string or just the number/colon part.
                 # Example: "Act 1: ..." split by "Act " -> ["", " 1: ..."]
                 # We are interested in the content after "Act X: "
                 # For this fallback, we'll assume it might give ["", " 1: content1", " 2: content2", " 3: content3"] or similar
                 # or ["content0", " 1: content1", ... ] if original plan didn't start with "Act"
                 # The critical part is to get 3 act contents.
                 # Let's refine the fallback:
                temp_acts = []
                for act_text in acts:
                    # Try to remove "X: " or "X. " from the beginning of act content if present after fallback
                    processed_text = re.sub(r'^\s*(?:\d+|[IVXLCDM]+)?[:.\s]*', '', act_text).strip()
                    if processed_text: # Only add if there's content left
                        temp_acts.append(processed_text)
                acts = temp_acts
            
            if len(acts) != 3:
                print(f'Fail: split_by_act, attempt 2 (found {len(acts)} acts after fallback). Original plan: {original_plan[:500]}...')
                return []

        # The prepending of "Act " is removed as the method should return act descriptions.
        # Formatting with "Act X:" is handled by plan_2_str and act_2_str.
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
