# Run through create_local_demo.py; its wrapper keeps the generated token private.
account = Account.find(Integer(ENV.fetch('LOCAL_DEMO_ACCOUNT_ID')))
name = 'Lagos Demo Store (fictional)'
inbox = nil
bot = nil
ActiveRecord::Base.transaction do
  inbox = account.inboxes.find_by(name: name)
  if inbox && inbox.channel_type != 'Channel::WebWidget'
    raise 'An inbox with the demo name already exists with another channel type'
  end
  unless inbox
    channel = account.web_widgets.create!(
      website_url: 'http://localhost:3000', widget_color: '#176B52',
      welcome_title: 'Lagos Demo Store',
      welcome_tagline: 'Fictional retailer demo. Ask about hours or delivery, or request a person.',
      continuity_via_email: false
    )
    inbox = account.inboxes.create!(name: name, channel: channel, enable_auto_assignment: false)
  end
  owner = account.account_users.where(role: :administrator).first!.user
  InboxMember.find_or_create_by!(inbox: inbox, user: owner)
  bot = AgentBot.find_or_initialize_by(account_id: account.id, name: "Local FAQ pilot inbox #{inbox.id}")
  expected_url = "http://bot:8080/webhook/#{ENV.fetch('BOT_WEBHOOK_SECRET')}"
  raise 'Existing demo bot has a different callback URL' if bot.persisted? && bot.outgoing_url != expected_url

  bot.assign_attributes(description: 'Local approved FAQ demo with staff handoff', outgoing_url: expected_url, bot_type: :webhook)
  bot.save!
  attachment = AgentBotInbox.find_or_initialize_by(inbox: inbox)
  raise 'Demo inbox already has another bot attached' if attachment.persisted? && attachment.agent_bot_id != bot.id

  attachment.update!(agent_bot: bot, status: :active)
end
access_token = bot.access_token || bot.create_access_token!
puts 'LOCAL_DEMO_RESULT=' + {
  account_id: account.id, inbox_id: inbox.id, agent_bot_id: bot.id,
  api_token: access_token.token, website_token: inbox.channel.website_token
}.to_json
