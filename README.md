# Slack Q\&A Bot

This is a Slack bot that helps turn any channel into a clean Q\&A space. It keeps things organized, gives people credit for helping out, and makes life easier for moderators.

## What It Does

* Tracks Questions (done):
  Any new message in the Q\&A channel is treated as a question. The bot adds a ❌ reaction and replies in a thread to keep track of it.

* Mod Tools (done):
  Mods can resolve questions.

* Point System (done):
  When a mod resolves a question, they can give points to whoever helped the most (and any other helpful folks too).

* Leaderboard(done):
  There’s a `/leaderboard` command to see who’s been the most helpful lately.

## How It Works

### For Regular Users

1. Ask your question in the Q\&A channel.
2. The bot will react with ❌ and start a thread.
3. People reply in the thread with answers.
4. Once it’s solved, a mod will mark it as done.
5. The bot switches ❌ to ✅, hands out points, and announces who helped.

### For Mods

1. Go to the thread of a solved question.
2. Use the “Resolve Question” shortcut on the original message.
3. A modal will pop up:
   * Choose the main person who solved it.
   * Add anyone else who helped, if needed.
   * Hit submit.
4. The bot updates everything: reactions, scores, and posts the final summary.


## Upcoming Features
- I am planning to connect the leaderboard to Supabase (backend)
- Anything you that is hardcoded should be in a database
- A website for the leaderboard
- Some badges for students

That's what is on my mind for *now*.
