# Q&A Ticket slack bot

This is a slack bot that turns the channale into a q&a so users can ask questions and get respones faster and modorators can answer the question fast and get organized, also there will be some rewards for the people who contribute and answer the questions (eg points, badges, tiers), everything is stored into Supbase


### What it does

-   Any message will be a ticket and marks them with so students & moderators can know they haven't been answered yet.
-   Mods can give out points to the person who solved the question and to other people who contributed.
-   There's a `/leaderboard` command to show who has the most points (top 10).
-   When a new person joins the main channel, the bot DMs them a little welcome message explaining how to use the channel.
-   It can announce the top helper of the week in a channel and when someone earn a badge.
-   All the main settings, like how many points to give or who is a moderator is stored in the database and automatically synced with the bot.

### What is it made with

-   Python
-   slack-bolt
-   Supabase

## How to use the bot

### For everyone

- To ask a question post a message in the main help channel.
- To see the scores just type `/leaderboard`
- To display your own stats type `/my-stats`

### For moderators

- To resolve a question, click the three dots on the question message and click "Resolve Ticket". 
  A form will pop up to let you give points or choose self-solved if no one solved it.
- Announce the weekly winner by typing `/award-weekly-winner`, the bot will post in its announcment channel.


