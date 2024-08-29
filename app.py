from nicegui import context, ui, run
from groupchat.selector import build_support_group
from groupchat.meeting import choose_next_actor, next_actor_turn, write_bios, messages_to_string

import time
import asyncio

@ui.page('/')
def main():

    messages = []

    chat_loop_running = False

    support_group = ""
    support_group_reason = ""
    support_group_members = []
    support_group_bios = []
    support_group_leader_bio = ""
    support_group_member_bios = []

    @ui.refreshable
    def chat_messages() -> None:
        for name, text in messages:
            ui.chat_message(text=text, name=name, sent=name == 'User')
        # if context.get_client().has_socket_connection:
        #     ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')

    def append_message() -> None:
        message = text.value
        messages.append(['User', message])
        text.value = ''
        chat_messages.refresh()
        un_stall_chat_loop()

    async def chat_event_loop() -> None:
        nonlocal messages
        nonlocal chat_loop_running
        nonlocal support_group
        nonlocal support_group_reason
        nonlocal support_group_bios
        nonlocal support_group_leader_bio
        nonlocal support_group_member_bios
        # chat_loop_running = not chat_loop_running
        # while True:
        #     await asyncio.sleep(5)
        #     if chat_loop_running:
        print("chat event loop")
        ui.notify("chat event loop")
        next_name = await choose_next_actor(support_group, support_group_reason, support_group_leader_bio,
                                           support_group_member_bios, messages_to_string(messages))
        print(next_name)
        if "WAIT" in next_name:
            await asyncio.sleep(int(next_name.split(";")[1]))
            next_name = next_name.split(";")[2]
        if next_name == "TERMINATE":
            chat_loop_running = False
            return
            # break
        next_bio = support_group_bios[next_name]
        actor, response = await next_actor_turn(support_group, next_name, next_bio, messages_to_string(messages))
        if actor == response:
            return
            # continue
        if response.lower() == "empty response" or response.lower() == "no response" or \
                response.lower() == "empty":
            return
            # continue
        messages.append([actor, response])
        print(response)
        chat_messages.refresh()

    async def get_support_group() -> None:
        nonlocal support_group_members
        nonlocal support_group
        nonlocal support_group_reason
        nonlocal support_group_bios
        nonlocal support_group_leader_bio
        nonlocal support_group_member_bios
        message = support_group_input.value
        support_group_response = await build_support_group({'input': message})
        group, members = support_group_response
        support_group = group['support_group']
        support_group_reason = group['support_group_reason']
        support_group_members = members
        ui.label(f"Thanks for sharing. Here's a support group that might help you:")
        ui.label(f"Group Name: {support_group}")
        ui.label(f"Reason: {support_group_reason}")
        support_group_label.set_text(f"Support Group: {support_group}")
        support_group_members_list.refresh()
        support_group_bios, support_group_leader_bio, support_group_member_bios = write_bios(members)

    @ui.refreshable
    def support_group_members_list() -> None:
        for member in support_group_members:
            ui.label(str(member))

    def un_stall_chat_loop() -> None:
        stall_chat_loop_timer.deactivate()
        chat_loop_timer.activate()

    chat_loop_timer = ui.timer(12, chat_event_loop, active=False)
    stall_chat_loop_timer = ui.timer(30, un_stall_chat_loop, active=False)
    ui.switch('active').bind_value(chat_loop_timer, 'active')

    def flip_chat_loop_running() -> None:
        print(chat_loop_timer.active)
        if chat_loop_timer.active:
            print("deactivating")
            chat_loop_timer.deactivate()
        else:
            print("activating")
            chat_loop_timer.activate()

    def stall_chat_loop() -> None:
        if stall_chat_loop_timer.active:
            return
        chat_loop_timer.deactivate()
        stall_chat_loop_timer.activate()

    with ui.card().style("width: 75%; align-self: center;"):
        ui.label("Welcome to the Supportiv Chatbot").style("text-align: center; font-size: 2rem; font-weight: 500; margin-bottom: 1rem;")
        ui.label("Looking for support? What's bothering you today?")
        ui.label("Type in the box below to be paired with a support group.")
        support_group_input = ui.input("What's bothering you today?")\
            .style('width: 100%')\
            .on('keydown.enter', lambda: get_support_group())

    ui.query('.q-page').classes('flex')
    ui.query('.nicegui-content').classes('w-full')

    with ui.card().style("width: 75%; align-self: center; height: 500px; margin-top: 1rem;"):
        with ui.row().style("width: 100%; align-self: center;"):
            support_group_label = ui.label("Support Group: ").style("font-weight: 500; margin-bottom: 1rem;")
            support_group_start_button = ui.button("Start Meeting").style("margin-left: auto;") \
                .on('click', lambda: flip_chat_loop_running())
        with ui.scroll_area().style('width: 100%; height: 500px;').classes('items-stretch flex-grow'):
            with ui.column().style("align-self: center; width: 75%").classes('items-stretch'):
                chat_messages()
        text = ui.input("chat input", on_change=lambda: stall_chat_loop()).style('width: 100%').props('rounded outlined input-class=mx-3') \
                .classes('w-full self-center').on('keydown.enter', lambda x: append_message())

    with ui.card().style("width: 75%; align-self: center; margin-top: 1rem;"):
        ui.label("Support Group Members").style("font-weight: 500; margin-bottom: 1rem;")
        support_group_members_list()

    # messages = [
    #     ['Supportiv', "Looking for support? What's bothering you today?"]
    # ]
    # thinking = False
    #
    # @ui.refreshable
    # def chat_messages() -> None:
    #     for name, text in messages:
    #         ui.chat_message(text=text, name=name, sent=name == 'You')
    #     if thinking:
    #         ui.spinner(size='3rem').classes('self-center')
    #     if context.get_client().has_socket_connection:
    #         ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
    #
    # async def send() -> None:
    #     nonlocal thinking
    #     message = text.value
    #     messages.append(('You', text.value))
    #     thinking = True
    #     text.value = ''
    #     chat_messages.refresh()
    #
    #     print(message)
    #     response = await selector_chain.ainvoke({'input': message})
    #     #selector_memory.save_context({'input': message}, {'output': response.content})
    #     print(response.content)
    #     messages.append(('Supportiv', response.content))
    #     thinking = False
    #     chat_messages.refresh()
    #
    # with ui.tabs().classes('w-full') as tabs:
    #     chat_tab = ui.tab('Chat')
    # with ui.tab_panels(tabs, value=chat_tab).classes('w-full max-w-2xl mx-auto flex-grow items-stretch'):
    #     with ui.tab_panel(chat_tab).classes('items-stretch'):
    #         chat_messages()
    #
    # with ui.footer().classes('bg-white'), ui.column().classes('w-full max-w-3xl mx-auto my-6'):
    #     with ui.row().classes('w-full no-wrap items-center'):
    #         text = ui.input(placeholder="Message").props('rounded outlined input-class=mx-3') \
    #             .classes('w-full self-center').on('keydown.enter', send, "weiner")


ui.run(title="Supportiv Chatbot")
