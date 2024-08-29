from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

import dotenv
import re
import json

dotenv.load_dotenv()


def parse_message(message):
    print(message)
    matches = re.search(r'Group:\s*(.*?)\s*Reason:\s*(.*)', message.content)
    if matches:
        group = matches.group(1)
        reason = matches.group(2)
        return {"support_group": group, "support_group_reason": reason}
    return {"support_group": None, "support_group_reason": None}


chat = ChatOpenAI(model="gpt-4o")

GROUP_SELECT_SYSTEM_MESSAGE = """"You are a social worker tasked with matching individuals to support groups that
can help them work through some of their issues. Come up with the name of a support group the individual should join
and a brief reason why you made that decision. You may ask at most one clarifying question if you believe it will help
you choose a better support group for this individual. Be sensitive when coming up with the name of the group as a bad
choice that trivializes their issue could turn them off.

When you have a group in mind, respond in the following format:
Group: [group name]
new line
Reason: [reason for choosing this group that describes the function of the group and why it is a good fit for the individual without using "I"]
"""

select_prompt = ChatPromptTemplate.from_messages(
    [
        ('system', GROUP_SELECT_SYSTEM_MESSAGE),
        ('ai', "What's bothering you? Looking for support?"),
        ('human', '{input}'),
    ]
)

selector_chain = select_prompt | chat | parse_message

MEMBERS_SYSTEM_PROMPT = """You are a screenwriter creating characters who are attending a support group called {support_group}.
Someone might attend this group because {support_group_reason}.
Create a genuine cast of 4-6 characters who attend the support group meetings
These characters must be realistic and act in proportion to the subject matter.
Create a profile for each of the characters that you will give to actors.
The actors will embody the descriptions, so please be thorough. One character must be the group leader.

The description contains the following information
"id": a unique identifier for the character,
"name": First and Last name only,
"role": "leader" or "member",
"age": age,
"gender": gender,
"temperament": brief description of the characters temperment,
"attendance_reason": brief description why the character is attending,
"tendency_positive": how likely this character is to respond positively in group discussion, 1 to 10,
"tendency_share": how likely this character is to initiate sharing, 1 to 10,
"tendency_respond": how likely this character is to respond to someone's share, 1 to 10,
"negative_attributes": this character's negative attributes in a group setting
"experiences": A paragraph of describing life experiences that the character has that can contribute to group disucssion. The description of these life experiences must include specific people, places, relationships and things to benefit the discussion

Respond with a list of python dictionaries, one dictionary per character. It must be valid python syntax.
Do not wrap the response with ```python ... ```
The more specific you can be the better.
"""

group_members_prompt = ChatPromptTemplate.from_messages(
    [
        ('system', MEMBERS_SYSTEM_PROMPT),
    ]
)
group_members_chain = group_members_prompt | chat


async def build_support_group(input):
    support_group_response = await selector_chain.ainvoke({"input":input})
    if support_group_response['support_group'] is None:
        print("issue with first chain response")
        print(support_group_response)
        return None, None
    response = await group_members_chain.ainvoke({
        "support_group": support_group_response["support_group"],
        "support_group_reason": support_group_response["support_group_reason"]
    })
    try:
        members = json.loads(response.content)
        return support_group_response, members
    except Exception as e:
        print(e)
        print("issue with second chain response")
        print(response.content)
        return None, None
