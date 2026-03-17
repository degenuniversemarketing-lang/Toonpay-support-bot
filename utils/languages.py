# Language codes and names
LANGUAGES = {
    'en': '🇬🇧 English',
    'de': '🇩🇪 Deutsch (German)',
    'hu': '🇭🇺 Magyar (Hungarian)',
    'es': '🇪🇸 Español (Spanish)',
    'fr': '🇫🇷 Français (French)',
    'it': '🇮🇹 Italiano (Italian)',
    'pt': '🇵🇹 Português (Portuguese)',
    'ru': '🇷🇺 Русский (Russian)',
    'ar': '🇸🇦 العربية (Arabic)',
    'zh': '🇨🇳 中文 (Chinese)',
    'ja': '🇯🇵 日本語 (Japanese)',
    'hi': '🇮🇳 हिन्दी (Hindi)'
}

# Default language
DEFAULT_LANGUAGE = 'en'

# Language-specific strings
STRINGS = {
    'en': {
        # Welcome & General
        'welcome': "🎫 **Welcome to ToonPay Support Bot!**\n\nI'm here to help you with any issues you might have.\n\n**How to create a ticket:**\n1️⃣ Click 'New Ticket'\n2️⃣ Select your issue category\n3️⃣ Provide your name\n4️⃣ Provide your email\n5️⃣ Provide your phone number\n6️⃣ Describe your issue\n7️⃣ Submit\n\n⏱️ **ToonPay Support Available 24/7**\n\nClick the button below to start!",
        'help': "ℹ️ **Help & Support**\n\n**How to create a ticket:**\n1. Click \"New Ticket\"\n2. Select category\n3. Provide your full name\n4. Provide your email address\n5. Provide your phone number\n6. Describe your issue\n7. Submit\n\n**Important Notes:**\n• Each ticket is for one issue only\n• Tickets close after admin reply\n• Create new ticket for new questions\n• Your details are saved for faster support\n\n⏱️ **ToonPay Support Available 24/7**\n\nNeed immediate assistance? Contact @ToonPaySupport",
        'select_language': "🌐 **Please select your language:**",
        'language_changed': "✅ Language changed to English!",
        
        # Ticket creation
        'select_category': "📋 **Select your issue category:**",
        'ask_name': "👤 **Please enter your full name:**\n\nExample: `John Doe`",
        'name_saved': "✅ **Name saved!**",
        'ask_email': "📧 **Now enter your email address:**\n\nExample: `user@example.com`",
        'invalid_email': "❌ **Invalid email format!**\n\nPlease send a valid email address.\nExample: `user@example.com`",
        'email_saved': "✅ **Email saved!**",
        'ask_phone': "📞 **Now send your phone number:**\n\nExample: `+1234567890` or `1234567890`",
        'invalid_phone': "❌ **Invalid phone number!**\n\nPlease send a valid phone number (10-15 digits).\nExample: `+1234567890` or `1234567890`",
        'phone_saved': "✅ **Phone saved!**",
        'ask_question': "📝 **Now describe your issue in detail:**\n\nPlease include:\n• What happened?\n• When did it happen?\n• Any error messages?",
        'ticket_created': "✅ **Your ticket has been created!**\n\n**Ticket ID:** `#{ticket_id}`\n**Category:** {category}\n**Name:** {name}\n\nWe'll get back to you soon.\n\nYou can check your ticket status using /start and clicking 'My Tickets'.",
        'ticket_failed': "❌ **Failed to create ticket.**\n\nPlease try again later or contact @ToonPaySupport",
        'ticket_error': "❌ **An error occurred while creating your ticket.**\n\nPlease try again later or contact @ToonPaySupport",
        'cancel': "❌ **Ticket creation cancelled.**\n\nYou can start again anytime with /start",
        
        # My Tickets
        'my_tickets': "📋 **Your Tickets:**",
        'no_tickets': "📭 You don't have any tickets yet.",
        'create_new': "📝 Create New Ticket",
        'refresh': "🔄 Refresh",
        'status_pending': '⏳ Pending',
        'status_in_progress': '🔄 In Progress',
        'status_closed': '✅ Closed',
        'status_spam': '🚫 Spam',
        
        # Categories
        'category_technical': '🛠️ Technical Issue',
        'category_payment': '💰 Payment Problem',
        'category_account': '👤 Account Issue',
        'category_feature': '✨ Feature Request',
        'category_other': '❓ Other',
        
        # Buttons
        'new_ticket': "📝 New Ticket",
        'my_tickets_btn': "📋 My Tickets",
        'help_btn': "❓ Help",
        'cancel_btn': "🔙 Cancel",
        'reply_btn': "💬 Reply",
        'progress_btn': "🔄 In Progress",
        'spam_btn': "❌ Close as Spam",
        'submit_ticket': "📝 Submit Ticket",
        
        # Admin notifications
        'new_ticket_admin': "🎫 **New Ticket #{ticket_id}**\n\n**Category:** {category}\n**Name:** {name}\n**From:** @{username}\n**User ID:** `{user_id}`\n**Email:** `{email}`\n**Phone:** `{phone}`\n\n**Question:**\n{question}",
        
        # User notification for reply
        'ticket_answered': "✅ **Your ticket #{ticket_id} has been answered!**\n\n**Your question:**\n{question}\n\n**Answer:**\n{answer}\n\nThank you for contacting ToonPay Support!\nNeed more help? Create a new ticket with /start",
        
        # Group support message
        'group_support': "📬 **Need help from ToonPay Support?**\n\nClick the button below to submit your ticket privately.\nOur support team will assist you within 24 hours.",
        
        # Stats
        'stats_title': "📊 **Support Bot Statistics**",
        'total_tickets': "📈 **Total Tickets:** {total}",
        'closed': "✅ **Closed:** {closed}",
        'in_progress': "🔄 **In Progress:** {in_progress}",
        'pending': "⏳ **Pending:** {pending}",
        'spam': "🚫 **Spam:** {spam}",
        'admin_performance': "👨‍💼 **Admin Performance:**",
        'no_solved': "• No tickets solved yet",
        
        # Search
        'search_usage': "🔍 **Usage:** `/search <name/username/user_id/email>`\n\nExamples:\n• `/search john`\n• `/search @username`\n• `/search 123456789`\n• `/search user@example.com`",
        'user_info': "👤 **User Information**",
        'name': "**Name:** {name}",
        'username': "**Username:** @{username}",
        'user_id': "**User ID:** `{user_id}`",
        'email': "**Email:** {email}",
        'phone': "**Phone:** {phone}",
        'registered': "**Registered:** {date}",
        'tickets_count': "**Tickets ({count}):**",
        'no_tickets_found': "**No tickets found**",
        'no_users': "❌ No users found matching: `{query}`",
        
        # Download
        'no_export': "📭 No tickets to export.",
        'export_caption': "📊 **Support Tickets Export (CSV)**\n📅 {date}\n📈 Total: {total} tickets\n\n✅ Solved/Closed and 🔄 In Progress/Pending tickets are in the same file",
        'export_solved': "📊 **Solved & Closed Tickets Export (CSV)**\n📅 {date}",
        'export_pending': "📊 **Pending & In-Progress Tickets Export (CSV)**\n📅 {date}",
        
        # Broadcast
        'broadcast_usage': "📝 **Usage:** Reply to a message with `/broadcast` to send it to all users.\n\nYou can broadcast:\n• Text messages\n• Images with captions\n• Videos with captions\n• GIFs\n• Any media type",
        'broadcast_start': "📤 **Broadcasting to {count} users...**\n⏳ Please wait...",
        'broadcast_complete': "📊 **Broadcast Complete**\n\n✅ Success: {success}\n❌ Failed: {failed}\n📈 Total: {total}",
        
        # All Stats
        'all_stats': "📊 **Complete Bot Statistics**\n\n**Overview:**\n👥 **Total Users:** {total_users}\n🎫 **Total Tickets:** {total_tickets}\n✅ **Solved Tickets:** {solved}\n🔄 **In Progress:** {in_progress}\n🚫 **Spam Tickets:** {spam}\n📭 **Inactive Users:** {inactive} (started bot but no tickets)",
        'user_details': "📋 **User Details:**\n\n_(Sending detailed list...)_",
        'user_detail_item': "**Name:** {name}\n**Username:** @{username}\n**User ID:** `{user_id}`\n**Registered:** {date}\n**Status:** {status}\n**Tickets:** Total: {total} | ✅ Solved: {solved} | 🔄 In Progress: {in_progress} | 🚫 Spam: {spam}\n─────────────────────",
        'active': "✅ Active",
        'inactive': "📭 Inactive",
        
        # Custom commands
        'custom_added': "✅ **Custom command added!**\n\nCommand: `/{command}`\nContent: {content}",
        'custom_removed': "✅ Command `/{command}` removed successfully.",
        'custom_not_found': "❌ Command `/{command}` not found.",
        'custom_list': "📋 **Custom Commands:**\n\n{commands}",
        'no_custom': "📭 No custom commands added yet.",
        'here_link': "Here's your requested link:",
        'click_here': "🔗 Click Here",
        
        # Group activation
        'group_activated': "✅ **This group has been activated for ToonPay Support!**\n\nUsers can now use /support command here.",
        'group_activated_success': "✅ Group `{group_id}` activated successfully!\n\nUsers can now use /support in that group.",
        'group_activation_failed': "❌ **Failed to activate group**\n\nMake sure I'm an admin in that group!\nError: {error}",
        'group_deactivated': "✅ Group `{group_id}` deactivated successfully.",
        'group_list': "📋 **Activated Groups:**\n\n{groups}\n\nTotal: {count} groups",
        'no_groups': "📭 No activated groups.\n\nUse `/activate <group_id>` to add one.",
        
        # Delete data
        'delete_usage': "📝 **Usage:** `/deletedata <value><unit>`\n\nExamples:\n• `/deletedata 30d` - deletes tickets older than 30 days\n• `/deletedata 12h` - deletes tickets older than 12 hours\n• `/deletedata 45m` - deletes tickets older than 45 minutes\n• `/deletedata 7 days` - also works with full words",
        'deleted': "✅ Deleted `{count}` tickets older than {time}.",
        
        # Bot status
        'bot_online': "✅ **Bot is online and ready to receive tickets!**",
        'bot_warning': "⚠️ **Warning:** Bot cannot send messages to admin group `{group_id}`!\nMake sure bot is admin in that group.\n\nError: {error}",
        'fatal_error': "🚨 **FATAL BOT ERROR** 🚨\n\nBot failed to start!\nError: {error}\n\nTraceback:\n`{traceback}`",
        'error_alert': "🚨 **Bot Error Alert** 🚨\n\n**User:** @{username} (ID: `{user_id}`)\n**Chat:** {chat}\n**Message:** `{message}`\n\n**Error:** `{error}`\n**Traceback:**\n`{traceback}`",
    },
    
    'de': {
        # German translations
        'welcome': "🎫 **Willkommen beim ToonPay Support Bot!**\n\nIch bin hier, um Ihnen bei Problemen zu helfen.\n\n**So erstellen Sie ein Ticket:**\n1️⃣ Klicken Sie auf 'Neues Ticket'\n2️⃣ Wählen Sie Ihre Kategorie\n3️⃣ Geben Sie Ihren Namen ein\n4️⃣ Geben Sie Ihre E-Mail ein\n5️⃣ Geben Sie Ihre Telefonnummer ein\n6️⃣ Beschreiben Sie Ihr Problem\n7️⃣ Absenden\n\n⏱️ **ToonPay Support 24/7 verfügbar**\n\nKlicken Sie unten, um zu starten!",
        'help': "ℹ️ **Hilfe & Support**\n\n**So erstellen Sie ein Ticket:**\n1. Klicken Sie auf \"Neues Ticket\"\n2. Wählen Sie eine Kategorie\n3. Geben Sie Ihren vollständigen Namen ein\n4. Geben Sie Ihre E-Mail-Adresse ein\n5. Geben Sie Ihre Telefonnummer ein\n6. Beschreiben Sie Ihr Problem\n7. Absenden\n\n**Wichtige Hinweise:**\n• Jedes Ticket ist für ein Problem\n• Tickets werden nach Admin-Antwort geschlossen\n• Neues Ticket für neue Fragen erstellen\n• Ihre Daten werden für schnelleren Support gespeichert\n\n⏱️ **ToonPay Support 24/7 verfügbar**\n\nBrauchen Sie sofortige Hilfe? Kontaktieren Sie @ToonPaySupport",
        'select_language': "🌐 **Bitte wählen Sie Ihre Sprache:**",
        'language_changed': "✅ Sprache auf Deutsch geändert!",
        
        'select_category': "📋 **Wählen Sie Ihre Kategorie:**",
        'ask_name': "👤 **Bitte geben Sie Ihren vollständigen Namen ein:**\n\nBeispiel: `Max Mustermann`",
        'name_saved': "✅ **Name gespeichert!**",
        'ask_email': "📧 **Geben Sie jetzt Ihre E-Mail-Adresse ein:**\n\nBeispiel: `user@example.com`",
        'invalid_email': "❌ **Ungültiges E-Mail-Format!**\n\nBitte senden Sie eine gültige E-Mail-Adresse.\nBeispiel: `user@example.com`",
        'email_saved': "✅ **E-Mail gespeichert!**",
        'ask_phone': "📞 **Senden Sie jetzt Ihre Telefonnummer:**\n\nBeispiel: `+1234567890` oder `1234567890`",
        'invalid_phone': "❌ **Ungültige Telefonnummer!**\n\nBitte senden Sie eine gültige Telefonnummer (10-15 Ziffern).\nBeispiel: `+1234567890` oder `1234567890`",
        'phone_saved': "✅ **Telefonnummer gespeichert!**",
        'ask_question': "📝 **Beschreiben Sie jetzt Ihr Problem detailliert:**\n\nBitte geben Sie an:\n• Was ist passiert?\n• Wann ist es passiert?\n• Irgendwelche Fehlermeldungen?",
        'ticket_created': "✅ **Ihr Ticket wurde erstellt!**\n\n**Ticket-ID:** `#{ticket_id}`\n**Kategorie:** {category}\n**Name:** {name}\n\nWir werden uns bald bei Ihnen melden.\n\nSie können den Ticket-Status mit /start und 'Meine Tickets' überprüfen.",
        'ticket_failed': "❌ **Ticket konnte nicht erstellt werden.**\n\nBitte versuchen Sie es später erneut oder kontaktieren Sie @ToonPaySupport",
        'ticket_error': "❌ **Ein Fehler ist aufgetreten.**\n\nBitte versuchen Sie es später erneut oder kontaktieren Sie @ToonPaySupport",
        'cancel': "❌ **Ticket-Erstellung abgebrochen.**\n\nSie können jederzeit mit /start neu beginnen.",
        
        'my_tickets': "📋 **Ihre Tickets:**",
        'no_tickets': "📭 Sie haben noch keine Tickets.",
        'create_new': "📝 Neues Ticket",
        'refresh': "🔄 Aktualisieren",
        'status_pending': '⏳ Ausstehend',
        'status_in_progress': '🔄 In Bearbeitung',
        'status_closed': '✅ Geschlossen',
        'status_spam': '🚫 Spam',
        
        'category_technical': '🛠️ Technisches Problem',
        'category_payment': '💰 Zahlungsproblem',
        'category_account': '👤 Konto Problem',
        'category_feature': '✨ Funktionsanfrage',
        'category_other': '❓ Sonstiges',
        
        'new_ticket': "📝 Neues Ticket",
        'my_tickets_btn': "📋 Meine Tickets",
        'help_btn': "❓ Hilfe",
        'cancel_btn': "🔙 Abbrechen",
        'reply_btn': "💬 Antworten",
        'progress_btn': "🔄 In Bearbeitung",
        'spam_btn': "❌ Als Spam schließen",
        'submit_ticket': "📝 Ticket einreichen",
        
        'group_support': "📬 **Benötigen Sie Hilfe vom ToonPay Support?**\n\nKlicken Sie unten, um ein privates Ticket zu erstellen.\nUnser Support-Team wird Ihnen innerhalb von 24 Stunden helfen.",
        'bot_online': "✅ **Bot ist online und bereit, Tickets zu empfangen!**",
    },
    
    'hu': {
        # Hungarian translations
        'welcome': "🎫 **Üdvözöl a ToonPay Support Bot!**\n\nAzért vagyok itt, hogy segítsek bármilyen problémában.\n\n**Hogyan hozhat létre jegyet:**\n1️⃣ Kattintson az 'Új jegy' gombra\n2️⃣ Válassza ki a kategóriát\n3️⃣ Adja meg a nevét\n4️⃣ Adja meg az email címét\n5️⃣ Adja meg a telefonszámát\n6️⃣ Írja le a problémáját\n7️⃣ Elküldés\n\n⏱️ **ToonPay Support 24/7 elérhető**\n\nKattintson az induláshoz!",
        'help': "ℹ️ **Segítség és támogatás**\n\n**Hogyan hozhat létre jegyet:**\n1. Kattintson az \"Új jegy\" gombra\n2. Válasszon kategóriát\n3. Adja meg teljes nevét\n4. Adja meg email címét\n5. Adja meg telefonszámát\n6. Írja le problémáját\n7. Elküldés\n\n**Fontos megjegyzések:**\n• Minden jegy csak egy probléma kezelésére szolgál\n• A jegyek az admin válasza után lezáródnak\n• Új kérdéshez új jegyet kell létrehozni\n• Adatait a gyorsabb támogatás érdekében tároljuk\n\n⏱️ **ToonPay Support 24/7 elérhető**\n\nAzonnali segítségre van szüksége? Lépjen kapcsolatba: @ToonPaySupport",
        'select_language': "🌐 **Kérjük, válassza ki a nyelvet:**",
        'language_changed': "✅ Nyelv magyarra változtatva!",
        
        'select_category': "📋 **Válassza ki a problémakategóriát:**",
        'ask_name': "👤 **Kérjük, adja meg teljes nevét:**\n\nPélda: `Kovács János`",
        'name_saved': "✅ **Név elmentve!**",
        'ask_email': "📧 **Most adja meg email címét:**\n\nPélda: `user@example.com`",
        'invalid_email': "❌ **Érvénytelen email formátum!**\n\nKérjük, érvényes email címet adjon meg.\nPélda: `user@example.com`",
        'email_saved': "✅ **Email elmentve!**",
        'ask_phone': "📞 **Most küldje el telefonszámát:**\n\nPélda: `+1234567890` vagy `1234567890`",
        'invalid_phone': "❌ **Érvénytelen telefonszám!**\n\nKérjük, érvényes telefonszámot adjon meg (10-15 számjegy).\nPélda: `+1234567890` vagy `1234567890`",
        'phone_saved': "✅ **Telefonszám elmentve!**",
        'ask_question': "📝 **Most írja le részletesen a problémáját:**\n\nKérjük, írja le:\n• Mi történt?\n• Mikor történt?\n• Bármilyen hibaüzenet?",
        'ticket_created': "✅ **A jegy létrehozva!**\n\n**Jegy azonosító:** `#{ticket_id}`\n**Kategória:** {category}\n**Név:** {name}\n\nHamarosan jelentkezünk.\n\nA jegy állapotát a /start és a 'Jegyeim' gombra kattintva ellenőrizheti.",
        'ticket_failed': "❌ **Nem sikerült létrehozni a jegyet.**\n\nKérjük, próbálja újra később, vagy lépjen kapcsolatba: @ToonPaySupport",
        'ticket_error': "❌ **Hiba történt a jegy létrehozása során.**\n\nKérjük, próbálja újra később, vagy lépjen kapcsolatba: @ToonPaySupport",
        'cancel': "❌ **Jegy létrehozása megszakítva.**\n\nBármikor újrakezdheti a /start paranccsal.",
        
        'my_tickets': "📋 **Jegyeim:**",
        'no_tickets': "📭 Még nincsenek jegyei.",
        'create_new': "📝 Új jegy",
        'refresh': "🔄 Frissítés",
        'status_pending': '⏳ Függőben',
        'status_in_progress': '🔄 Folyamatban',
        'status_closed': '✅ Lezárva',
        'status_spam': '🚫 Spam',
        
        'category_technical': '🛠️ Technikai probléma',
        'category_payment': '💰 Fizetési probléma',
        'category_account': '👤 Fiók probléma',
        'category_feature': '✨ Funkció kérés',
        'category_other': '❓ Egyéb',
        
        'new_ticket': "📝 Új jegy",
        'my_tickets_btn': "📋 Jegyeim",
        'help_btn': "❓ Segítség",
        'cancel_btn': "🔙 Mégse",
        'reply_btn': "💬 Válasz",
        'progress_btn': "🔄 Folyamatban",
        'spam_btn': "❌ Lezárás spamként",
        'submit_ticket': "📝 Jegy beküldése",
        
        'group_support': "📬 **Segítségre van szüksége a ToonPay Supporttól?**\n\nKattintson a gombra a jegy privát beküldéséhez.\nTámogató csapatunk 24 órán belül segít.",
        'bot_online': "✅ **A bot online és készen áll a jegyek fogadására!**",
    }
}

# Function to get string in user's language
def get_string(user_lang, key, **kwargs):
    """Get string in user's language with formatting"""
    if user_lang not in STRINGS:
        user_lang = DEFAULT_LANGUAGE
    
    string = STRINGS[user_lang].get(key, STRINGS[DEFAULT_LANGUAGE].get(key, key))
    
    if kwargs:
        try:
            return string.format(**kwargs)
        except:
            return string
    return string
