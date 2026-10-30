import csv
import shutil
import json

from collections import defaultdict
from itertools import islice, chain
from pathlib import Path

from helpers_pages import create_survey_page
from helpers_utilities import clean_up_unicode, write_output, media_url, lower

dir_root = "./make"
dir_csv  = f"{dir_root}/CSV"
dir_out  = f"{dir_root}/~out"

Path(dir_out).mkdir(parents=True,exist_ok=True)

def flat(dictionary):
    return list(chain.from_iterable(dictionary.values()))

def _create_survey_page(row):
    text = clean_up_unicode(row[6])

    title = row[0].strip()
    input_1 = lower(row[3])
    input_2 = None
    minimum = None
    maximum = None
    media = None
    
    if input_1 == "dropdown":
        items = row[19]
    else: 
        items=""
        for i, item in enumerate(filter(lambda x: x!='', row[8:19])):
            items += f"{i+1}::{item};"
    image_framed = None
    timeout = None
    show_buttons = None
    variable_name = row[4]
    conditions = row[5]
    input_name = None

    return create_survey_page(conditions=conditions, text=text,
                                show_buttons=show_buttons, media=media, image_framed=image_framed,
                                items=items, input_1=input_1, input_2=input_2,
                                variable_name=variable_name, title=title, input_name=input_name,
                                minimum=minimum, maximum=maximum, timeout=timeout)

# Read the questions
survey_pages = defaultdict(lambda: defaultdict(list))
with open(f"{dir_csv}/MT Teen Content_ Long Scenarios & Other - Surveys.csv", "r", encoding="utf-8") as read_obj:

    for row in islice(csv.reader(read_obj),1,None):

        # In *survey_questions.csv each row is a single question (aka, "page") in Digital Trails.
        # The "Subject" column indicates which script/flow type the question belongs to and the
        # "Dose" column indicates which run of the "Subject" flow the row belongs too.

        # One counter-intuitve aspect of this is the "Introduction" survey. This flow has a subject
        # of "Dose" (i.e., the same as the session microdoses). This is because the Intro flow is
        # a special flow that only occurs on the first microdose session. Therefore, intro flow
        # questions are all rows in *survey_questions.csv with Subject=Dose and Dose=1.

        # Each flow can be uniquely identified by the flow it
        # belongs to and which run of that flow it appears on

        dose        = row[1].lower()
        subject     = row[2].lower()
        group_id    = (dose,subject)
        subgroup_id = row[0]

        if row[2] and row[0] != "Practice CBM-I": survey_pages[group_id][subgroup_id].append(_create_survey_page(row))

# Define folders
folders = {
    "treatment/end of day": flat(survey_pages[("all","eod")]),
    "treatment/reasons for ending": flat(survey_pages[("all","reasonsforending")]),
    "treatment/track your progress/__flow__.json": {"mode":"sequential","take":1},
    "treatment/track your progress/1": flat(survey_pages[("all","biweekly")]),
    "treatment/track your progress/2": flat(survey_pages[("all","biweekly")]),
    "treatment/track your progress/3": flat(survey_pages[("all","biweekly")]),
    "treatment/track your progress/4": flat(survey_pages[("all","biweekly")]),
    "control/end of day": flat(survey_pages[("all","eod")]),
    "control/reasons for ending": flat(survey_pages[("all","reasonsforending")]),
    "control/track your progress/__flow__.json": {"mode":"sequential","take":1},
    "control/track your progress/1": flat(survey_pages[("all","biweekly")]),
    "control/track your progress/2": flat(survey_pages[("all","biweekly")]),
    "control/track your progress/3": flat(survey_pages[("all","biweekly")]),
    "control/track your progress/4": flat(survey_pages[("all","biweekly")]),
}

# Delete old JSON
for key in folders.keys():
    shutil.rmtree(f"{dir_out}/{str.join('/',key.split('/')[:2])}",ignore_errors=True)

# Write new JSON
write_output(dir_out, folders)