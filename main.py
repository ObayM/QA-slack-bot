import os
import json
from enum import Enum
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from supabase_client import (
    get_config_value, get_moderators, get_onboarding_channels, get_tiers, get_achievements,
    get_leaderboard, get_user_stats, award_solver_points, award_contributor_points,
    get_user_achievements, grant_achievement
)


load_dotenv()

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

class Achievement(str, Enum):
    """
    defines achievement ids to avoid magic strings
    """
    FIRST_SOLUTION = 'first_solution'
    BUG_SQUISHER = 'bug_squisher'
    COMMUNITY_PILLAR = 'community_pillar'
    WEEKLY_TOP_HELPER = 'weekly_top_helper'


def check_and_award_milestones(user_id, old_stats, new_stats, client):
    """
    checks for and announces any new tiers or achievements earned
    """
    announcement_channel_id = get_config_value('ANNOUNCEMENT_CHANNEL_ID')
    if not announcement_channel_id:
        return

    earned_achievements = get_user_achievements(user_id)
    all_achievements = get_achievements()
    all_tiers = get_tiers()

    # check for tier upgrades
    for tier in all_tiers:
        if old_stats['score'] < tier['points_required'] <= new_stats['score']:
            client.chat_postMessage(
                channel=announcement_channel_id,
                text=f"Congratulations <@{user_id}>! you've reached the {tier['name']} tier! {tier['emoji']}"
            )

    # check for new achievements
    def check_and_grant(ach_id, condition):
        if condition and ach_id.value not in earned_achievements:
            grant_achievement(user_id, ach_id.value)
            info = all_achievements.get(ach_id.value)

            if info:
                client.chat_postMessage(
                    channel=announcement_channel_id,
                    text=f"Congratulations <@{user_id}> you've earned the *{info['name']}* badge! {info['emoji']}"
                )

    check_and_grant(Achievement.FIRST_SOLUTION, new_stats['solutions_count'] == 1)
    check_and_grant(Achievement.BUG_SQUISHER, new_stats['solutions_count'] >= 10)
    check_and_grant(Achievement.COMMUNITY_PILLAR, new_stats['score'] >= 100)

@app.event("member_joined_channel")
def handle_member_joined(event, client):
    """
    This is for onboarding the user and get him to know the channel
    """
    
    user_id = event["user"]
    channel_id = event["channel"]

    if channel_id not in get_onboarding_channels():
        return
    
    try:
        welcome_blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hey <@{user_id}>, welcome to <#{channel_id}>! We're thrilled to have you here."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "How this channel works"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "1- Ask a Question: Simply post your question in the channel. Our bot will automatically create a ticket for it by adding an ❌ reaction on your message"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "2- Earn Points: You can earn points by helping others! The moderator/mentor will mark the best answer, awarding points to both the solver and helpful contributors."
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "3- Leaderboard: Curious about your rank? Use the `/leaderboard` command to see the top helpers or yuo can use `/profile` to see your points"
                }
            },
           
        ]
        # send it to the user
        client.chat_postMessage(
            channel=user_id,
            text=f"Welcome to <#{channel_id}>!",
            blocks=welcome_blocks
        )


    except Exception as e:
        print(f"Error sending welcome DM: {e}")

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
    limit = int(get_config_value('LEADERBOARD_LIMIT', 10))
    scores = get_leaderboard(limit)

    if not scores:
        say("The leaderboard is empty! No points have been awarded yet.")
        return

    text = ["*🏆 community leaderboard 🏆*"]
    emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
    for i, user in enumerate(scores, 1):
        emoji = emojis.get(i, f"{i}.")
        text.append(f"{emoji} <@{user['user_id']}>: *{user['score']} points*")
    
    say(text='\n'.join(text))
    

@app.shortcut("resolve_shortcut")
def handle_resolve_shortcut(ack, shortcut, say, client):
    ack()

    user_id = shortcut["user"]["id"]
    channel_id = shortcut["channel"]["id"]
    message_ts = shortcut["message"]["ts"]

    if user_id not in get_moderators():
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

    solver_points = int(get_config_value('SOLVER_POINTS', 5))
    contributor_points = int(get_config_value('CONTRIBUTOR_POINTS', 1))


    if solver_id != "self_solved":

        old_stats = get_user_stats(solver_id)
        award_solver_points(solver_id, solver_points)

        new_stats = {'score': old_stats['score'] + solver_points, 'solutions_count': old_stats['solutions_count'] + 1}

        check_and_award_milestones(solver_id, old_stats, new_stats, client)
        awarded_to_text.append(f"<@{solver_id}> (solution: +{solver_points} pts)")

    for c_id in contributor_ids:

        if c_id not in ("self_solved", solver_id):

            old_stats = get_user_stats(c_id)
            award_contributor_points(c_id, contributor_points)

            new_stats = {'score': old_stats['score'] + contributor_points, 'solutions_count': old_stats['solutions_count']}

            check_and_award_milestones(c_id, old_stats, new_stats, client)
            awarded_to_text.append(f"<@{c_id}> (contribution: +{contributor_points} pts)")
    
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

@app.command("/award-weekly-winner")
def award_weekly_winner(ack, say, body, client):
    ack()
    
    if body["user_id"] not in get_moderators():
        say(text="Sorry, only moderators can use this command.", ephemeral=True)
        return

    leaderboard = get_leaderboard(limit=1)
    if not leaderboard:
        say(text="The leaderboard is empty, cannot award a winner.", ephemeral=True)
        return

    winner_id = leaderboard[0]['user_id']
    grant_achievement(winner_id, Achievement.WEEKLY_TOP_HELPER)

    announcement_channel_id = get_config_value('ANNOUNCEMENT_CHANNEL_ID')
    if announcement_channel_id:
        info = get_achievements().get(Achievement.WEEKLY_TOP_HELPER)
        announcement = f"🏆 Weekly community roundup! 🏆\n\nA big thank you to our top helper of the week, <@{winner_id}>, who has been awarded the *{info['name']}* badge! {info['emoji']}"
        client.chat_postMessage(channel=announcement_channel_id, text=announcement)
    
    say(text=f"Successfully awarded the weekly winner badge to <@{winner_id}>.", ephemeral=True)

@app.command('/my-stats')
def shows_user_stats(ack, say, body):
    ack()
    user_id = body["user_id"]
    stats = get_user_stats(user_id)

    if stats:
        say(f"You have {stats["score"]} points and solved {stats["solutions_count"]} questions", ephemeral=True)
    else:
        say(f"You didn't enter the leaderboard yet", ephemeral=True)

if __name__ == "__main__":

    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()