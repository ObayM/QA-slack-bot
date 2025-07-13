import os
import json
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from supabase_client import add_points, get_leaderboard, load_app_settings

load_dotenv()

APP_CONFIG, MODERATOR_IDS = load_app_settings()

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN")
)


@app.event("message")
def handle_message_events(event, say, client):
    if "bot_id" in event or "thread_ts" in event:
        return

    try:
        client.reactions_add(channel=event["channel"], name="x", timestamp=event["ts"])
        say(
            thread_ts=event["ts"],
            text="Thanks for your question! It's in the queue. Our community and mentors will take a look shortly."
        )
    except Exception as e:
        print(f"Error creating ticket: {e}")

@app.command("/leaderboard")
def show_leaderboard(ack, say):
    ack()
    scores = get_leaderboard(limit=APP_CONFIG.get("LEADERBOARD_LIMIT",10))
    if not scores:
        say("The leaderboard is empty! No points have been awarded yet.")
        return

    leaderboard_text = "*🏆 Community Leaderboard 🏆*\n"
    for i, user in enumerate(scores):
        rank, emoji = i + 1, ""
        if rank == 1: emoji = "🥇"
        elif rank == 2: emoji = "🥈"
        elif rank == 3: emoji = "🥉"
        user_id= user["user_id"]
        score = user["score"]
        leaderboard_text += f"{rank}. {emoji} <@{user_id}>: *{score} points*\n"
    say(text=leaderboard_text)

@app.shortcut("resolve_shortcut")
def handle_resolve_shortcut(ack, shortcut, say, client):
    ack()

    user_id = shortcut["user"]["id"]
    channel_id = shortcut["channel"]["id"]
    message_ts = shortcut["message"]["ts"]

    if user_id not in MODERATOR_IDS:
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text="Sorry, only moderators can use this shortcut."
        )
        return

    try:
        replies = client.conversations_replies(channel=channel_id, ts=message_ts)
        participants = {msg["user"] for msg in replies["messages"][1:] if "bot_id" not in msg}

        user_options = [{"text": {"type": "plain_text", "text": f"<@{p_id}>"}, "value": p_id} for p_id in participants]
        user_options.append({"text": {"type": "plain_text", "text": "No one / Self-solved"}, "value": "self_solved"})

        private_metadata = json.dumps({"channel_id": channel_id, "message_ts": message_ts})

        client.views_open(
            trigger_id=shortcut["trigger_id"],
            view={
                "type": "modal", "callback_id": "resolve_ticket_modal", "private_metadata": private_metadata,
                "title": {"type": "plain_text", "text": "Resolve Ticket"}, "submit": {"type": "plain_text", "text": "Submit"},
                "blocks": [
                    {"type": "input", "block_id": "solver_block", "label": {"type": "plain_text", "text": "Who provided the solution?"},
                     "element": {"type": "static_select", "action_id": "solver_select", "options": user_options}},

                    {"type": "input", "block_id": "contributors_block", "label": {"type": "plain_text", "text": "Who else contributed helpfully?"},
                     "element": {"type": "multi_static_select", "action_id": "contributors_select", "options": user_options}, "optional": True},
                ],
            },
        )
    except Exception as e:
        print(f"Error opening resolve modal: {e}")


@app.view("resolve_ticket_modal")
def handle_resolve_submission(ack, body, view, say, client):

    ack()

    metadata = json.loads(view["private_metadata"])
    channel_id = metadata["channel_id"]
    message_ts = metadata["message_ts"]

    moderator_id = body["user"]["id"]
    values = view["state"]["values"]
    solver_id = values["solver_block"]["solver_select"]["selected_option"]["value"]

    contributor_ids = [opt["value"] for opt in values["contributors_block"]["contributors_select"].get("selected_options", [])]
    
    awarded_to_text = []

    solver_points = APP_CONFIG.get('SOLVER_POINTS', 5)
    contributor_points = APP_CONFIG.get('CONTRIBUTOR_POINTS', 1)

    
    if solver_id != "self_solved":
        add_points(solver_id, solver_points)
        awarded_to_text.append(f"<@{solver_id}> (Solution: +{solver_points} pts)")
    
    for c_id in contributor_ids:

        if c_id != "self_solved" and c_id != solver_id:
            add_points(c_id, contributor_points)

            awarded_to_text.append(f"<@{c_id}> (Contribution: +{contributor_points} pts)")
    
    
    if awarded_to_text:
        resolution_text = f"This question has been marked as resolved by <@{moderator_id}>.\n\n*Points awarded:*\n" + "\n".join(awarded_to_text)
    else:
        resolution_text = f"This question has been marked as resolved by <@{moderator_id}>. Thanks to everyone who participated!"
    
    say(channel=channel_id, thread_ts=message_ts, text=resolution_text)
    
    try:
        client.reactions_remove(channel=channel_id, name="x", timestamp=message_ts)
        client.reactions_add(channel=channel_id, name="white_check_mark", timestamp=message_ts)
    except Exception as e:
        print(f"Error cleaning up reactions: {e}")

if __name__ == "__main__":

    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()