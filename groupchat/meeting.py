from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

import dotenv

dotenv.load_dotenv()

chat = ChatOpenAI(model="gpt-4o")


def messages_to_string(messages):
    return "\n".join([f"{name}: {text}" for name, text in messages])


def character_bio_str(id, name, role, age, gender, temperament, attendance_reason, negative_attributes,
                      tendency_positive, tendency_share, tendency_respond, experiences):
    return f"""ID: {id}
Name: {name}
Group Role: {role}
Age: {age}
Gender: {gender}
Temperament: {temperament}
Reason for Attending The Support Group: {attendance_reason}
Negative Attributes in a Group Setting: {negative_attributes}
Tendency to Respond Positively: {tendency_positive}
Tendency to Initiate Sharing: {tendency_share}
Tendency to Respond to Others: {tendency_respond}
Experiences to Share About: {experiences}"""


def write_bios(bios):
    character_bios = {bio["name"]: character_bio_str(**bio) for bio in bios}
    leader_bio = [character_bio_str(**bio) for bio in bios if bio["role"] == "leader"][0]
    member_bios = [character_bio_str(**bio) for bio in bios if bio["role"] != "leader"]
    return character_bios, leader_bio, member_bios


CHARACTER_SYSTEM_PROMPT = """You are an actor. Your character is attending a support group meeting called {support_group}.

Here is more about your character:
{character_bio}

When it is your turn to speak, you'll be given some dialog from the support group.
Respond in character. Your goal is to contribute to a flowing conversation that helps the attendees work through their issues.
If you feel like your character doesn't have anything to contribue, you can reply with empty text.
Prefix each of your responses with your name.
You will see your previous replies in the conversation history, if any."""

# Input will be member: dialog text, not messages from each agent
support_group_member_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CHARACTER_SYSTEM_PROMPT),
        ("human", "{input}"),
    ]
)
support_group_member_chain = support_group_member_prompt | chat

CHARACTER_SELECTION_SYSTEM_PROMPT = """You are a skilled director who is directing a scene that shows a genuine support group meeting.
The support group is titled {support_group} and someone might attend it because {support_group_reason}.
You direct a group of actors who are playing group members.
You will be given dialog from the meeting. You will choose the next actor to speak.
There is no requirement that all actors must speak, or that there must be an order.

Here is a description of the support group leader. The leader will always start the meeting. If no input is provided, return just the leaders name.
{leader_bio}

Here is a description of the support group members:
{member_bios}

You can only respond with the following:
- A character's full name. This character will be chosen to speak next.
- WAIT;X;Full Name where x is an integer. This will direct the actors to pause X seconds before speaking.

If you choose the user to respond, the user may or may not provide input.
If the user does not respond when chosen, choose another member.

The meeting should go on for some time. Reply TERMINATE when you think the meeting should end.
Do not contribute dialog, only select which character speaks next.
"""

# Input is the conversation history for the selector
member_selector_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CHARACTER_SELECTION_SYSTEM_PROMPT),
        ("human", "{input}"),
    ]
)
member_selector_chain = member_selector_prompt | chat


async def choose_next_actor(support_group, support_group_reason, leader_bio, member_bios, input):
    response = await member_selector_chain.ainvoke(
        {
            "support_group": support_group,
            "support_group_reason": support_group_reason,
            "leader_bio": leader_bio,
            "member_bios": member_bios,
            "input": input,
        }
    )
    return response.content


async def next_actor_turn(support_group, name, bio, dialog):
    response = await support_group_member_chain.ainvoke(
        {
            "support_group": support_group,
            "character_bio": bio,
            "input": dialog,
        }
    )
    try:
        name, text = response.content.split(": ")
    except ValueError:
        name, text = name, response.content
    return name, text
