# Slack Q\&A Bot

This is a slack bot that turns the channale into a q&a so users can ask questions and get respones faster and modorators can answer the question fast and get organized, also there will be some rewards for the people who contribute and answer the questions (eg points)

## Main features

* Track questions (done):
  Every new message in the q&a channel is will be a question. 
  first the bot automatically adds a ❌ reaction and replies in the thread.

* Mod tools (done):
  modarators can resolve questions by a message shortuct.

* Point system (done):
  When a mod resolves a question, they can give points to the ones who contributed/solved the questions (both can get points too)

* Leaderboard(done):
  There’s a `/leaderboard` command to see the points of every student

## How it works

### For normal users/students

1. Ask any question in the q&a channel.
2. The bot will react with ❌ and start the thread.
3. Students can reply in the thread with answers/contributions.
4. When a modorator reviews it, they can give points to those who helped and he can also write a final answer.
5. The bot switches ❌ to ✅, gives the points, and write a message that the question is resolved and who got points too.

### For modorators

1. Review the threads with ❌ reaction.
2. Use the “Resolve Question” shortcut on the original message.
3. A modal will appear:
   * Choose the main person who solved it or nobody if you solved it yourself.
   * Add anyone else who contributed (optional).
   * Hit submit.
4. The bot updates the thread with the reactions, scores, and replies with the summary.


## To-do
- I am planning to connect the leaderboard to Supabase/firebase (backend)
- The mods ids and the configrautions (eg. points) should added to this database ^
- I could make a website to show the leaderboard
- Maybe adding a badges system (eg most contributions/solutions solved)

That's it for *now*.
