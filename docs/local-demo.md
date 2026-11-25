# Local retailer demonstration

Create a fictional Website inbox under an account you administer. The helper
uses approved FAQ matching and a dedicated bot token while preserving your login.

```sh
python3 scripts/create_local_demo.py --account YOUR_ACCOUNT_ID
docker-compose up -d --force-recreate bot
```

Replace `YOUR_ACCOUNT_ID` with the ID from your own Chatwoot account. The helper
prints the customer widget URL and saves public demo metadata in the ignored
`data/local-demo.json` file. Private connector credentials stay in `.env`.

## Open the customer chat

Open the widget URL printed by the helper, allow the page to finish loading and
select Start Conversation. In another tab, open http://localhost:3000, sign in
and select the fictional Lagos Demo Store inbox.

The local address works on the machine running the containers. Demonstrate it
in person or through screen sharing. Remote users need a separately configured
HTTPS deployment; their localhost address does not reach your machine.

## Show the workflow

1. In a fresh customer conversation, ask “How much is delivery to Lekki?” The bot
   should identify itself and return the approved fictional delivery fees.
2. Ask “I want to speak to a human.” The bot should acknowledge the handoff and
   the conversation should become open in the staff inbox.
3. Ask “What are your opening hours?” in that conversation. The bot should stay
   silent while staff own the conversation.
4. Reply manually through the staff inbox. Begin a fresh conversation for another
   bot demonstration, or explicitly return ownership to the bot.

The store and its prices are fictional. A personalised demonstration needs the
business owner's approved information.

## Run the live verification

```sh
python3 scripts/check_live_demo.py
```

This creates a synthetic customer conversation and checks incoming delivery,
an approved FAQ reply, open status after requesting staff, and no additional bot
reply during a five second observation after handoff. Results go into the ignored
`data/live-demo-report.json` file.

Run after the worker finishes starting. A cold worker can exceed the check's
thirty polling attempts. The check only runs when the connector matches the
saved fictional inbox and the knowledge is still the fictional store.

The Website inbox workflow has been exercised with these checks and in a browser.
This does not establish long-term availability, WhatsApp delivery or local model
quality. Connect and evaluate those capabilities separately.
