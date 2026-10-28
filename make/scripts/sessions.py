import csv
import shutil

from collections import defaultdict
from itertools import islice, cycle, chain
from pathlib import Path

from helpers_pages import create_scenario_pages, create_survey_page,create_resource_page
from helpers_pages import create_long_pages, create_video_page
from helpers_utilities import get_resources, get_ER, get_tips, clean_up_unicode, has_value, create_puzzle, dir_safe, shuffle, write_output, media_url, lower, get_page_index, get_reminder_element

dir_root = "./make"
dir_csv    = f"{dir_root}/CSV"
dir_out    = f"{dir_root}/~out"

# adding a comment for clarity

Path(dir_out).mkdir(parents=True,exist_ok=True)

def flat(dictionary):
    return list(chain.from_iterable(dictionary.values()))

def _create_practice_pages():
    with open(f"{dir_csv}/dose1_scenarios.csv", "r", encoding="utf-8") as dose1_read_obj:  # scenarios for first dose in file

        scenario_num = 0
        for row in islice(csv.reader(dose1_read_obj),1,None):

            # First, add the video that goes before each scenario
            yield create_video_page(scenario_num+1)

            domain, label = row[0].strip(), row[3]
            puzzle1,puzzle2 = map(create_puzzle,row[4:6])
            question, choices, answer = row[6], row[7:9], row[7]
            image_url = media_url(row[10])
            shuffle(choices)

            yield from create_scenario_pages(domain=domain, label=label, scenario_num=scenario_num,
                                                    puzzle_text_1=puzzle1[0], word_1=puzzle1[1],
                                                    comp_question=question, answers=choices,
                                                    correct_answer=answer, image_url=image_url,
                                                    is_first=scenario_num==0)
            scenario_num += 1

def _create_survey_page(row):
    text = clean_up_unicode(row[4])

    title = row[1].strip()
    input_1 = lower(row[5])
    input_2 = lower(row[6])
    minimum = row[7]
    maximum = row[8]
    media = media_url(row[9])
    items = row[10]
    image_framed = row[11]
    timeout = row[12]
    show_buttons = row[13]
    variable_name = row[16]
    conditions = row[17]
    input_name = None #row[18]

    return create_survey_page(conditions=conditions, text=text,
                                show_buttons=show_buttons, media=media, image_framed=image_framed,
                                items=items, input_1=input_1, input_2=input_2,
                                variable_name=variable_name, title=title, input_name=input_name,
                                minimum=minimum, maximum=maximum, timeout=timeout)

def domain_selection_text():
    return (
"The domains listed here are some areas that may cause you to feel anxious." 
"Please select the one that you'd like to work on during today's training.\n\n"
"We encourage you to choose different domains to practice thinking flexibly across areas of your life!"
    )

def create_lessons_learned():
    """
    A function that reads in the file that has the text for each lesson learned.

    :param file_path: file path for lessons learned text (.csv)
    :return: lessons learned dictionary, key = domain, field = lessons learned text for that domain

    https://docs.google.com/spreadsheets/d/1kM80BHglwtsBgxntJDRdfNj-cusgGGJ0sx814ctB1pk/edit#gid=0
    """
    with open(f"{dir_csv}/lessons_learned_text.csv", 'r', encoding='utf-8') as read_obj:
        return { row[0]:row[1] for row in islice(csv.reader(read_obj),1,None) }

def create_long_sessions():
    sessions = defaultdict(list)

    with open(f"{dir_csv}/MT Teen Content_ Long Scenarios & Other - Long scenarios.csv", "r",encoding="utf-8") as read_file:
        for row in islice(csv.reader(read_file),2,None):

            if not row: continue # Skip empty lines

            if len(row) > 16:  # Ensure the row has enough columns
                domain_1 = row[1].strip()
                domain_2 = row[2].strip() if row[1] else None
                label = row[3]
                image_url = media_url(row[31])
                scenario_description = row[29]
                thoughts = row[32:37]
                feelings = row[37:42]
                behaviors = row[42:]

                if not has_value(scenario_description) or not has_value(label): continue

                dose = create_long_pages(label=label, scenario_description=scenario_description,
                                          image_url=image_url,thoughts=thoughts,
                                          feelings=feelings, behaviors=behaviors)

                if domain_1: sessions[domain_1].append(dose)
                if domain_2: sessions[domain_2].append(dose)

    # shuffle each list of long scenario page groups
    for domain in sessions: shuffle(sessions[domain])

    return {k:iter(cycle(v)) for k,v in sessions.items()}

def create_short_sessions():
    sessions     = defaultdict(list)
    scenarios    = defaultdict(list)

    lessons_learned_dict = create_lessons_learned()

    domains = ["General", "Academic", "Athletic", "Environmental", "FamilyHome Life", "Health & Well-being", "Milestone", "Romantic Relationships", "Social Media", "Social Situations", "Vocation"]

    for domain in domains:

        with open(f"{dir_csv}/MT Teen Content_ Short Scenarios.xlsx - {domain} Scenarios.csv","r", encoding="utf-8", newline='') as read_obj:
            for row in islice(csv.reader(read_obj),1,None):

                label     = row[1]
                image_url = media_url(row[10])
                tipe      = row[4].strip()

                if not domain or not label: continue

                if len(scenarios[domain]) == 10:
                    sessions[domain].append(sum(scenarios[domain],[]))
                    scenarios[domain] = []

                else:

                    puzzle1,puzzle2 = map(create_puzzle,row[2:4])

                    if puzzle1 == (None,None): continue

                    comp_question, choices, answer  = row[6], row[7:9], row[7]
                    if lower(answer) in ["yes","no"]: choices = ["Yes","No"]
                    shuffle(choices)

                    if row[11]: letters_missing = row[11]

                    is_first_session = len(sessions[domain]) == 0
                    is_first_scenario = len(scenarios[domain]) == 0

                    show_lessons_learned = not is_first_session and is_first_scenario and len(sessions[domain]) % 4 == 0

                    scenarios[domain].append(
                        create_scenario_pages(domain=domain, label=label, scenario_num=len(scenarios[domain]),
                            puzzle_text_1=puzzle1[0], word_1=puzzle1[1],
                            comp_question=comp_question, answers=choices,
                            correct_answer=answer, word_2=puzzle2[1],
                            puzzle_text_2=puzzle2[0], image_url=image_url,
                            n_missing=letters_missing,
                            include_lessons_learned=show_lessons_learned,
                            lessons_learned_dict=lessons_learned_dict,
                            is_first=is_first_scenario, tipe=tipe
                        )
                    )

    return sessions

def create_surveys():
    # The keys in this dictionary correspond to the HTC_survey_questions.csv lookup codes ([Subject]_[Doses])
    # You can see all the lookup codes and their meanings below:
    # https://docs.google.com/spreadsheets/d/1Z_syG-HbyFT2oqMsHnAbidRtlH97IVxnBqbNKZWbwLY/edit#gid=0
    surveys = { "BeforeDomain_All": defaultdict(list), "AfterDomain_All": defaultdict(list), "Dose_1": defaultdict(list), "Control_Dose_1": defaultdict(list) }

    # Open the file with all the content
    with open(f"{dir_csv}/MT Teen Content_ Long Scenarios & Other - Intro.csv", "r", encoding="utf-8") as read_obj:

        for row in islice(csv.reader(read_obj),1,None):
            lookup_id = f"{row[3]}_{row[2]}"
            subgroup_id = row[0]

            if lookup_id not in surveys: continue

            elif row[0] == "Practice CBM-I":
                surveys[lookup_id][subgroup_id].extend(_create_practice_pages())
            elif row[2]:
                surveys[lookup_id][subgroup_id].append(_create_survey_page(row))

    return surveys

def create_resource_dose_creator():
    ER_lookup = get_ER(file_path=f"{dir_csv}/MT Teen Content_ Long Scenarios & Other - Emotion Regulation Suggestions.csv")
    tips      = get_tips(file_path=f"{dir_csv}/MT Teen Content_ Long Scenarios & Other - Tips to apply lessons in daily life.csv")
    resources = get_resources(file_path=f"{dir_csv}/UMA Resources.csv")

    return lambda domain: [create_resource_page(resources, tips, ER_lookup, domain)]

def create_reminders():
    reminders = defaultdict(list)
    with open(f"{dir_csv}/MT Teen Content_ Long Scenarios & Other - Tips to apply lessons in daily life.csv", "r", encoding="utf-8") as read_obj:
        for row in islice(csv.reader(read_obj),1,None):
            reminders[row[0].strip()].append([lower(row[1]).strip(), lower(row[2]).strip()])

    return reminders

def try_add_reminders(session_number, session, reminders):
    if str(session_number+1) in reminders:
        for page,position,reminder in reminders[str(session_number+1)]:

            position = lower(position).strip()
            index = get_page_index(page,session,position)

            if index is not None:
                session[index]["information"] = get_reminder_element(reminder,position,1)

    return session

populations = [ ["Español", 5, 4] ]

for pop,s,l in populations:

    surveys         = create_surveys()
    short_sessions  = create_short_sessions()             # dict of short session iter by domain
    long_sessions   = create_long_sessions()              # dict of long session cycle by domain
    resources       = create_resource_dose_creator()       # lambda that takes a domain and returns a dose
    reminders       = create_reminders()

    domains  = short_sessions.keys()
    sessions = defaultdict(list)

    # Create doses
    for domain in domains:
        for short_session in short_sessions[domain]:
            if sessions[domain] and len(sessions[domain]) % 5 == 0:
                try:
                    sessions[domain].append(next(long_sessions[domain]) + resources(domain))
                except KeyError:
                    continue
            else:
                short_session = try_add_reminders(len(sessions[domain]), short_session, reminders)
                sessions[domain].append(short_session + resources(domain))

    for key in [k for k in reminders.keys() if k.startswith("<")]:
        for page,position,reminder in reminders[key]:
            for p in flat(surveys["BeforeDomain_All"]):
                if page in lower(p["header_text"]):
                    p["information"] = get_reminder_element(reminder,position,3)

    # Define folders
    folders = {}
    folders['control/intro'] = flat(surveys["Dose_1"]) # change back to "Control_Dose_1" when it's ready
    folders['treatment/intro'] = flat(surveys["Dose_1"])
    folders['treatment/sessions/__flow__.json'] = {"mode":"select", "title_case": True, "column_count":2, "text": domain_selection_text(), "title":"MindTrails Teen"}
    folders['treatment/sessions/__before__'] = flat(surveys["BeforeDomain_All"])
    folders['treatment/sessions/__after__'] = flat(surveys["AfterDomain_All"])
    for domain, doses in sessions.items():
        folders[f"treatment/sessions/{dir_safe(domain)}/__flow__.json"] ={"mode":"sequential", "take":1, "repeat":True}
        for i, dose in enumerate(doses,1):
            folders[f"treatment/sessions/{dir_safe(domain)}/{i}"] = dose

    # Delete old JSON
    shutil.rmtree(f"{dir_out}/treatment/sessions",ignore_errors=True)

    # Write new JSON
    write_output(dir_out, folders)