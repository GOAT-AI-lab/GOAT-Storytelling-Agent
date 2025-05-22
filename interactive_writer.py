import os
import json
import shutil # สำหรับการล้างไดเรกทอรีผลลัพธ์ (ถ้าต้องการ)

# ตรวจสอบว่า goat_storytelling_agent อยู่ใน PYTHONPATH หรือไดเรกทอรีเดียวกัน
try:
    from goat_storytelling_agent.storytelling_agent import StoryAgent
    from goat_storytelling_agent.plan import Plan
    # พยายาม import ENDPOINT จาก config.py หากไม่มีก็ไม่เป็นไร
    try:
        from goat_storytelling_agent.config import ENDPOINT
    except ImportError:
        ENDPOINT = "" 
except ImportError as e:
    print(f"เกิดข้อผิดพลาดในการ import: {e}")
    print("โปรดตรวจสอบว่าคุณรันสคริปต์นี้จากไดเรกทอรีที่ถูกต้อง และ goat_storytelling_agent สามารถเข้าถึงได้")
    ENDPOINT = "" # ค่าเริ่มต้นหาก config.py ไม่ได้ตั้งค่าหรือไม่มี

# --- การตั้งค่า ---
OUTPUT_DIR = "story_pipeline_output"
# กำหนดให้ใช้ KoboldCPP เป็นค่าเริ่มต้นเท่านั้น
KOBOLDCPP_BACKEND_NAME = "koboldcpp"
# URI เริ่มต้นสำหรับ KoboldCPP: ใช้ค่าจาก config.py ถ้ามี, มิฉะนั้นใช้ http://localhost:5001/v1/
# นี่จะเป็นค่าหลักที่ใช้โดยไม่มีการถามผู้ใช้ เว้นแต่จะถูก override โดย config.py
FIXED_KOBOLDCPP_URI = ENDPOINT if ENDPOINT else "http://localhost:5001/v1/"

# --- ฟังก์ชันช่วยเหลือ ---
def setup_output_dir():
    if os.path.exists(OUTPUT_DIR):
        print(f"ไดเรกทอรีผลลัพธ์ '{OUTPUT_DIR}' มีอยู่แล้ว ไฟล์อาจถูกเขียนทับหรือนำมาใช้ใหม่หากมีการโหลด")
    else:
        os.makedirs(OUTPUT_DIR)
        print(f"สร้างไดเรกทอรีผลลัพธ์ '{OUTPUT_DIR}'")

def save_and_prompt(data_content, filename, data_type="text", user_prompt_message=""):
    """บันทึกข้อมูลลงไฟล์และแจ้งให้ผู้ใช้ตรวจสอบ/แก้ไข"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    should_write_file = data_content is not None

    if should_write_file:
        if data_type == "text":
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(data_content)
        elif data_type == "json":
            if data_content is not None:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data_content, f, indent=4, ensure_ascii=False)
            else:
                print(f"คำเตือน: data_content เป็น None สำหรับ {filename}, จะไม่เขียนไฟล์ JSON ใหม่")
        else:
            print(f"ประเภทข้อมูลที่ไม่รองรับ: {data_type}")
            return data_content
        print(f"\nข้อมูลบันทึกไปยัง: {filepath}")

    if not user_prompt_message:
        user_prompt_message = f"โปรดตรวจสอบและแก้ไขไฟล์ '{filename}' หากต้องการ จากนั้นกด Enter เพื่อไปยังขั้นตอนต่อไป"
    
    input(user_prompt_message)
    
    if os.path.exists(filepath):
        print(f"กำลังโหลดข้อมูลจาก '{filepath}'...")
        if data_type == "text":
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        elif data_type == "json":
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    print(f"เกิดข้อผิดพลาดในการอ่านไฟล์ JSON '{filepath}': {e}")
                    print("โปรดตรวจสอบว่าไฟล์ JSON ถูกต้องตามรูปแบบ")
                    return None
        else:
            return data_content
    else:
        print(f"คำเตือน: ไม่พบไฟล์ '{filepath}' เพื่อโหลดหลังจากผู้ใช้แก้ไข")
        return None


def main_interactive_pipeline():
    setup_output_dir()

    # --- การเริ่มต้น Agent ---
    print("--- การเริ่มต้น Story Agent ---")
    topic = input("ป้อนหัวข้อเริ่มต้นสำหรับเรื่องราวของคุณ (เช่น 'ล่าสมบัติในป่าลึก'): ")
    
    # กำหนด Backend เป็น koboldcpp และ URI เป็นค่าที่ตั้งไว้โดยอัตโนมัติ
    backend_choice = KOBOLDCPP_BACKEND_NAME
    backend_uri_choice = FIXED_KOBOLDCPP_URI # ใช้ค่า URI ที่ตั้งไว้โดยตรง

    print(f"Backend ที่ใช้: {backend_choice}")
    print(f"URI ของ Backend: {backend_uri_choice}")
    
    # --- ข้อควรระวังเกี่ยวกับ URI และ _query_chat_koboldcpp ---
    print("\n!!! ข้อควรระวัง !!!")
    print(f"สคริปต์นี้จะใช้ URI: {backend_uri_choice} สำหรับ KoboldCPP")
    print("โปรดตรวจสอบฟังก์ชัน `_query_chat_koboldcpp` ในไฟล์ `goat_storytelling_agent/storytelling_agent.py`:")
    print("  - ฟังก์ชันนั้นอาจมีการต่อท้าย path ของ API (เช่น '/api/v1/generate' หรือ '/generate') เข้ากับ URI ที่ระบุ")
    print(f"  - หาก URI '{backend_uri_choice}' เป็น endpoint ที่สมบูรณ์แล้ว (รวม path สำหรับการ generate text แล้ว)")
    print("    คุณอาจจะต้องแก้ไข `_query_chat_koboldcpp` เพื่อไม่ให้มีการต่อท้าย path เพิ่มเติมโดยไม่จำเป็น")
    print("  - ตัวอย่างเช่น หาก API endpoint ของคุณคือ 'http://localhost:5001/v1/generate' และ URI ที่ตั้งค่าไว้คือ 'http://localhost:5001/v1/'")
    print("    ฟังก์ชัน `_query_chat_koboldcpp` ควรจะต่อท้ายเพียง '/generate' หรือปรับเปลี่ยนตามความเหมาะสม")
    input("กด Enter เพื่อดำเนินการต่อ...\n")
    # --- สิ้นสุดข้อควรระวัง ---

    try:
        agent = StoryAgent(backend_uri=backend_uri_choice, backend=backend_choice, form='novel')
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการเริ่มต้น StoryAgent: {e}")
        print("โปรดตรวจสอบว่า Backend Server ของคุณกำลังทำงานและตั้งค่าอย่างถูกต้อง")
        print(f"ตรวจสอบว่า 'goat_storytelling_agent/config.py' มี ENDPOINT ที่ถูกต้อง (ถ้ามี) และ URI '{backend_uri_choice}' ถูกต้องสำหรับ KoboldCPP")
        return

    # --- ขั้นตอนที่ 1: สร้าง Book Specification เริ่มต้น ---
    print("\n--- ขั้นตอนที่ 1: สร้าง Book Specification เริ่มต้น ---")
    filename_s1 = "01_book_spec_initial.txt"
    filepath_s1 = os.path.join(OUTPUT_DIR, filename_s1)
    book_spec_initial = ""
    if os.path.exists(filepath_s1):
        print(f"พบไฟล์ '{filename_s1}' ที่มีอยู่แล้ว กำลังโหลด...")
        book_spec_initial = save_and_prompt(None, filename_s1, data_type="text", user_prompt_message=f"โหลดไฟล์ '{filename_s1}' แล้ว โปรดตรวจสอบ/แก้ไขหากต้องการ จากนั้นกด Enter")
    else:
        print(f"กำลังสร้าง Book Specification เริ่มต้นสำหรับหัวข้อ: '{topic}'...")
        _, book_spec_initial_gen = agent.init_book_spec(topic)
        book_spec_initial = save_and_prompt(book_spec_initial_gen, filename_s1, data_type="text")
    
    current_book_spec = book_spec_initial
    if not current_book_spec:
        print("เกิดข้อผิดพลาด: ไม่สามารถสร้างหรือโหลด Initial Book Specification ได้ สิ้นสุดการทำงาน")
        return

    # --- ขั้นตอนที่ 2: ปรับปรุง Book Specification ---
    print("\n--- ขั้นตอนที่ 2: ปรับปรุง Book Specification ---")
    filename_s2 = "02_book_spec_enhanced.txt"
    filepath_s2 = os.path.join(OUTPUT_DIR, filename_s2)
    book_spec_enhanced = ""
    if os.path.exists(filepath_s2):
        print(f"พบไฟล์ '{filename_s2}' ที่มีอยู่แล้ว กำลังโหลด...")
        book_spec_enhanced = save_and_prompt(None, filename_s2, data_type="text", user_prompt_message=f"โหลดไฟล์ '{filename_s2}' แล้ว โปรดตรวจสอบ/แก้ไขหากต้องการ จากนั้นกด Enter")
    else:
        print("กำลังปรับปรุง Book Specification...")
        _, book_spec_enhanced_gen = agent.enhance_book_spec(current_book_spec)
        book_spec_enhanced = save_and_prompt(book_spec_enhanced_gen, filename_s2, data_type="text")
    
    current_book_spec = book_spec_enhanced
    if not current_book_spec:
        print("เกิดข้อผิดพลาด: ไม่สามารถสร้างหรือโหลด Enhanced Book Specification ได้ สิ้นสุดการทำงาน")
        return

    # --- ขั้นตอนที่ 3: สร้างโครงเรื่อง (Plot Chapters) ---
    print("\n--- ขั้นตอนที่ 3: สร้างโครงเรื่อง (Plot Chapters) ---")
    filename_s3_txt = "03_plot_chapters_initial.txt"
    filename_s3_json = "03_plot_chapters_initial_raw.json"

    plan_initial_obj = None
    if os.path.exists(os.path.join(OUTPUT_DIR, filename_s3_txt)):
        print(f"พบไฟล์ '{filename_s3_txt}' ที่มีอยู่แล้ว กำลังโหลด...")
        plan_initial_str = save_and_prompt(None, filename_s3_txt, data_type="text", user_prompt_message=f"โหลดไฟล์ '{filename_s3_txt}' แล้ว โปรดตรวจสอบ/แก้ไขหากต้องการ จากนั้นกด Enter")
        if plan_initial_str: plan_initial_obj = Plan.parse_text_plan(plan_initial_str)
        if not plan_initial_obj:
            print(f"คำเตือน: ไม่สามารถ parse '{filename_s3_txt}' เป็น plan ที่ถูกต้องได้")
    
    if not plan_initial_obj: 
        if os.path.exists(os.path.join(OUTPUT_DIR, filename_s3_json)):
             print(f"กำลังพยายามโหลดจาก '{filename_s3_json}'...")
             plan_initial_obj_loaded_json = save_and_prompt(None, filename_s3_json, data_type="json", user_prompt_message=f"โหลดไฟล์ '{filename_s3_json}' แล้ว โปรดตรวจสอบ/แก้ไข จากนั้นกด Enter")
             if plan_initial_obj_loaded_json:
                plan_initial_obj = plan_initial_obj_loaded_json 
                plan_initial_str_from_json = Plan.plan_2_str(plan_initial_obj)
                save_and_prompt(plan_initial_str_from_json, filename_s3_txt, data_type="text", user_prompt_message=f"Plan จาก JSON ถูกบันทึกกลับไปยัง '{filename_s3_txt}' แล้ว โปรดตรวจสอบ จากนั้นกด Enter")
        else:
            print("กำลังสร้าง Plot Chapters...")
            _, plan_initial_obj_gen = agent.create_plot_chapters(current_book_spec)
            if plan_initial_obj_gen:
                save_and_prompt(plan_initial_obj_gen, filename_s3_json, data_type="json") 
                plan_initial_str_gen = Plan.plan_2_str(plan_initial_obj_gen)
                plan_initial_obj_str_edited = save_and_prompt(plan_initial_str_gen, filename_s3_txt, data_type="text")
                if plan_initial_obj_str_edited: plan_initial_obj = Plan.parse_text_plan(plan_initial_obj_str_edited)

    current_plan_obj = plan_initial_obj
    if not current_plan_obj:
        print("เกิดข้อผิดพลาด: ไม่สามารถสร้างหรือโหลด Initial Plan ได้ สิ้นสุดการทำงาน")
        return

    # --- ขั้นตอนที่ 4: ปรับปรุงโครงเรื่อง (Enhance Plot Chapters) ---
    print("\n--- ขั้นตอนที่ 4: ปรับปรุงโครงเรื่อง (Enhance Plot Chapters) ---")
    filename_s4_txt = "04_plot_chapters_enhanced.txt"
    filename_s4_json = "04_plot_chapters_enhanced_raw.json"

    plan_enhanced_obj = None
    if os.path.exists(os.path.join(OUTPUT_DIR, filename_s4_txt)):
        print(f"พบไฟล์ '{filename_s4_txt}' ที่มีอยู่แล้ว กำลังโหลด...")
        plan_enhanced_str = save_and_prompt(None, filename_s4_txt, data_type="text", user_prompt_message=f"โหลดไฟล์ '{filename_s4_txt}' แล้ว โปรดตรวจสอบ/แก้ไขหากต้องการ จากนั้นกด Enter")
        if plan_enhanced_str: plan_enhanced_obj = Plan.parse_text_plan(plan_enhanced_str)
        if not plan_enhanced_obj:
             print(f"คำเตือน: ไม่สามารถ parse '{filename_s4_txt}' เป็น plan ที่ถูกต้องได้")

    if not plan_enhanced_obj:
        if os.path.exists(os.path.join(OUTPUT_DIR, filename_s4_json)):
            print(f"กำลังพยายามโหลดจาก '{filename_s4_json}'...")
            plan_enhanced_obj_loaded_json = save_and_prompt(None, filename_s4_json, data_type="json", user_prompt_message=f"โหลดไฟล์ '{filename_s4_json}' แล้ว โปรดตรวจสอบ/แก้ไข จากนั้นกด Enter")
            if plan_enhanced_obj_loaded_json:
                plan_enhanced_obj = plan_enhanced_obj_loaded_json
                plan_enhanced_str_from_json = Plan.plan_2_str(plan_enhanced_obj)
                save_and_prompt(plan_enhanced_str_from_json, filename_s4_txt, data_type="text", user_prompt_message=f"Plan จาก JSON ถูกบันทึกกลับไปยัง '{filename_s4_txt}' แล้ว โปรดตรวจสอบ จากนั้นกด Enter")
        else:
            print("กำลังปรับปรุง Plot Chapters...")
            _, plan_enhanced_obj_gen = agent.enhance_plot_chapters(current_book_spec, current_plan_obj)
            if plan_enhanced_obj_gen:
                save_and_prompt(plan_enhanced_obj_gen, filename_s4_json, data_type="json")
                plan_enhanced_str_gen = Plan.plan_2_str(plan_enhanced_obj_gen)
                plan_enhanced_str_edited = save_and_prompt(plan_enhanced_str_gen, filename_s4_txt, data_type="text")
                if plan_enhanced_str_edited: plan_enhanced_obj = Plan.parse_text_plan(plan_enhanced_str_edited)

    current_plan_obj = plan_enhanced_obj
    if not current_plan_obj:
        print("เกิดข้อผิดพลาด: ไม่สามารถสร้างหรือโหลด Enhanced Plan ได้ สิ้นสุดการทำงาน")
        return

    # --- ขั้นตอนที่ 5: แบ่ง Chapter ออกเป็น Scene (Split Chapters into Scenes) ---
    print("\n--- ขั้นตอนที่ 5: แบ่ง Chapter ออกเป็น Scene ---")
    filename_s5_json = "05_plan_with_scenes.json"
    filename_s5_txt_readable = "05_scenes_breakdown_readable.txt"

    plan_with_scenes_obj = None
    if os.path.exists(os.path.join(OUTPUT_DIR, filename_s5_json)):
        print(f"พบไฟล์ '{filename_s5_json}' ที่มีอยู่แล้ว กำลังโหลด...")
        plan_with_scenes_obj = save_and_prompt(None, filename_s5_json, data_type="json", user_prompt_message=f"โหลดไฟล์ '{filename_s5_json}' แล้ว โปรดตรวจสอบ/แก้ไขรายละเอียด scene ภายใน JSON นี้หากต้องการ จากนั้นกด Enter")
    else:
        print("กำลังแบ่ง Chapter ออกเป็น Scene...")
        _, plan_with_scenes_obj_gen = agent.split_chapters_into_scenes(current_plan_obj)
        if plan_with_scenes_obj_gen:
            plan_with_scenes_obj = save_and_prompt(plan_with_scenes_obj_gen, filename_s5_json, data_type="json")

    if not plan_with_scenes_obj:
        print("เกิดข้อผิดพลาด: ไม่สามารถสร้างหรือโหลด Plan with Scenes ได้ สิ้นสุดการทำงาน")
        return

    readable_scene_breakdown = []
    for act_idx, act in enumerate(plan_with_scenes_obj):
        readable_scene_breakdown.append(f"--- ACT {act_idx + 1} ---")
        readable_scene_breakdown.append(f"คำอธิบาย Act: {act.get('act_descr', 'N/A')}")
        if 'chapter_scenes' in act and isinstance(act['chapter_scenes'], dict):
            for ch_num_str, scenes_in_chapter_list in act['chapter_scenes'].items():
                readable_scene_breakdown.append(f"\n  Chapter {ch_num_str}:")
                if isinstance(scenes_in_chapter_list, list):
                    for scene_idx, scene_desc in enumerate(scenes_in_chapter_list):
                        readable_scene_breakdown.append(f"    Scene {scene_idx + 1}: {scene_desc}")
                else:
                    readable_scene_breakdown.append(f"    ข้อมูล Scene ของ Chapter {ch_num_str} ไม่ใช่ list: {scenes_in_chapter_list}")
        else:
            readable_scene_breakdown.append(f"  ไม่พบ 'chapter_scenes' หรือมีรูปแบบไม่ถูกต้องใน Act นี้")

    with open(os.path.join(OUTPUT_DIR, filename_s5_txt_readable), "w", encoding="utf-8") as f:
        f.write("\n".join(readable_scene_breakdown))
    print(f"รายละเอียด Scene ที่อ่านง่ายถูกบันทึกไปยัง: {os.path.join(OUTPUT_DIR, filename_s5_txt_readable)}")
    
    current_plan_obj_with_scenes = plan_with_scenes_obj

    # --- ขั้นตอนที่ 6: เขียน Scene ---
    print("\n--- ขั้นตอนที่ 6: เขียน Scene ---")
    full_story_scenes_text = []
    overall_plot_str_for_scenes = Plan.plan_2_str(current_plan_obj_with_scenes)
    scenes_output_dir_path = os.path.join(OUTPUT_DIR, "scenes")
    os.makedirs(scenes_output_dir_path, exist_ok=True)

    for act_idx, act in enumerate(current_plan_obj_with_scenes):
        act_num_for_display = act_idx + 1
        if 'chapter_scenes' not in act or not isinstance(act['chapter_scenes'], dict):
            print(f"คำเตือน: Act {act_num_for_display} ไม่มี 'chapter_scenes' หรือมีรูปแบบไม่ถูกต้อง กำลังข้าม...")
            continue
            
        for ch_num_str, chapter_scenes_list in act['chapter_scenes'].items():
            try:
                ch_num = int(ch_num_str)
            except ValueError:
                print(f"คำเตือน: หมายเลข Chapter '{ch_num_str}' ใน Act {act_num_for_display} ไม่ถูกต้อง กำลังข้าม...")
                continue
            
            if not isinstance(chapter_scenes_list, list):
                print(f"คำเตือน: รายการ Scene ของ Chapter {ch_num} ใน Act {act_num_for_display} ไม่ใช่ List กำลังข้าม...")
                continue

            for sc_idx, scene_description in enumerate(chapter_scenes_list):
                sc_num = sc_idx + 1
                print(f"\nกำลังประมวลผล: Act {act_num_for_display}, Chapter {ch_num}, Scene {sc_num}")
                print(f"รายละเอียด Scene: {scene_description}")

                scene_filename = f"scene_act{act_num_for_display}_ch{ch_num}_sc{sc_num}.txt"
                scene_filepath_relative_to_output = os.path.join("scenes", scene_filename) 

                previous_scene_text_content = full_story_scenes_text[-1] if full_story_scenes_text else None
                generated_scene_text_content = ""

                if os.path.exists(os.path.join(OUTPUT_DIR, scene_filepath_relative_to_output)):
                    print(f"พบไฟล์ Scene ที่มีอยู่แล้ว: '{scene_filename}' กำลังโหลด...")
                    generated_scene_text_content = save_and_prompt(None, scene_filepath_relative_to_output, data_type="text", user_prompt_message=f"โหลด Scene '{scene_filename}' แล้ว โปรดตรวจสอบ/แก้ไขหากต้องการ จากนั้นกด Enter เพื่อใช้ Scene นี้")
                else:
                    print("กำลังสร้างเนื้อหา Scene...")
                    if not scene_description: 
                        print(f"คำเตือน: รายละเอียด Scene สำหรับ Act {act_num_for_display}, Ch {ch_num}, Sc {sc_num} เป็นค่าว่าง จะไม่สร้าง Scene นี้")
                        generated_scene_text_content = f"[SCENE SKIPPED DUE TO EMPTY DESCRIPTION: Act {act_num_for_display}, Ch {ch_num}, Sc {sc_num}]"
                    else:
                        _, generated_scene_text_gen = agent.write_a_scene(
                            scene=scene_description, 
                            sc_num=sc_num, 
                            ch_num=ch_num, 
                            plan=overall_plot_str_for_scenes, 
                            previous_scene=previous_scene_text_content
                        )
                        if generated_scene_text_gen:
                           generated_scene_text_content = save_and_prompt(generated_scene_text_gen, scene_filepath_relative_to_output, data_type="text")
                        else:
                            print(f"คำเตือน: ไม่สามารถสร้างเนื้อหาสำหรับ Scene Act {act_num_for_display}, Ch {ch_num}, Sc {sc_num}")
                            generated_scene_text_content = f"[SCENE GENERATION FAILED: Act {act_num_for_display}, Ch {ch_num}, Sc {sc_num}]"
                
                if generated_scene_text_content: 
                    full_story_scenes_text.append(generated_scene_text_content)
                else: 
                    print(f"คำเตือน: เนื้อหา Scene สำหรับ Act {act_num_for_display}, Ch {ch_num}, Sc {sc_num} ยังคงเป็นค่าว่าง จะไม่ถูกรวมในเรื่องราวสุดท้าย")


    # --- ขั้นตอนที่ 7: รวมเรื่องราวทั้งหมด ---
    print("\n--- ขั้นตอนที่ 7: รวมเรื่องราวทั้งหมด ---")
    final_story_text_content = "\n\n---\n\n".join(filter(None, full_story_scenes_text)) 
    filename_s7 = "07_full_story_final.txt"
    save_and_prompt(final_story_text_content, filename_s7, data_type="text", user_prompt_message=f"เรื่องราวทั้งหมดถูกรวมและบันทึกไปยัง '{filename_s7}' แล้ว คุณสามารถตรวจสอบได้ ขั้นตอนทั้งหมดเสร็จสมบูรณ์ กด Enter เพื่อจบการทำงาน")

    print("\nกระบวนการสร้างเรื่องราวแบบโต้ตอบเสร็จสิ้น!")

if __name__ == "__main__":
    main_interactive_pipeline()