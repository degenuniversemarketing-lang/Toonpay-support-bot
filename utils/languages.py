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
        
        # Categories (updated)
        'category_technical': '🛠️ Funds Missing',
        'category_payment': '💰 Can\'t login to Account',
        'category_account': '👤 KYC Related',
        'category_feature': '✨ Card Issue',
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
        'click_here': "🔗 Click Here",
        'here_link': "Here's your requested link:",
        
        # Admin notifications (always in English)
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
        'export_caption': "📊 **Support Tickets Export (CSV)**\n📅 {date}\n📈 Total: {total} tickets",
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
        
        'category_technical': '🛠️ Fehlende Gelder',
        'category_payment': '💰 Anmeldung nicht möglich',
        'category_account': '👤 KYC-bezogen',
        'category_feature': '✨ Kartenproblem',
        'category_other': '❓ Sonstiges',
        
        'new_ticket': "📝 Neues Ticket",
        'my_tickets_btn': "📋 Meine Tickets",
        'help_btn': "❓ Hilfe",
        'cancel_btn': "🔙 Abbrechen",
        'reply_btn': "💬 Antworten",
        'progress_btn': "🔄 In Bearbeitung",
        'spam_btn': "❌ Als Spam schließen",
        'submit_ticket': "📝 Ticket einreichen",
        'click_here': "🔗 Hier klicken",
        'here_link': "Hier ist Ihr angeforderter Link:",
        
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
        
        'category_technical': '🛠️ Hiányzó összegek',
        'category_payment': '💰 Nem lehet belépni',
        'category_account': '👤 KYC kapcsolódó',
        'category_feature': '✨ Kártya probléma',
        'category_other': '❓ Egyéb',
        
        'new_ticket': "📝 Új jegy",
        'my_tickets_btn': "📋 Jegyeim",
        'help_btn': "❓ Segítség",
        'cancel_btn': "🔙 Mégse",
        'reply_btn': "💬 Válasz",
        'progress_btn': "🔄 Folyamatban",
        'spam_btn': "❌ Lezárás spamként",
        'submit_ticket': "📝 Jegy beküldése",
        'click_here': "🔗 Kattints ide",
        'here_link': "Itt a kért link:",
        
        'group_support': "📬 **Segítségre van szüksége a ToonPay Supporttól?**\n\nKattintson a gombra a jegy privát beküldéséhez.\nTámogató csapatunk 24 órán belül segít.",
        'bot_online': "✅ **A bot online és készen áll a jegyek fogadására!**",
    },
    
    'es': {
        # Spanish translations
        'welcome': "🎫 **¡Bienvenido al Bot de Soporte de ToonPay!**\n\nEstoy aquí para ayudarte con cualquier problema que puedas tener.\n\n**Cómo crear un ticket:**\n1️⃣ Haz clic en 'Nuevo Ticket'\n2️⃣ Selecciona tu categoría\n3️⃣ Proporciona tu nombre\n4️⃣ Proporciona tu email\n5️⃣ Proporciona tu número de teléfono\n6️⃣ Describe tu problema\n7️⃣ Enviar\n\n⏱️ **Soporte ToonPay disponible 24/7**\n\n¡Haz clic en el botón de abajo para comenzar!",
        'help': "ℹ️ **Ayuda y Soporte**\n\n**Cómo crear un ticket:**\n1. Haz clic en \"Nuevo Ticket\"\n2. Selecciona categoría\n3. Proporciona tu nombre completo\n4. Proporciona tu dirección de email\n5. Proporciona tu número de teléfono\n6. Describe tu problema\n7. Enviar\n\n**Notas importantes:**\n• Cada ticket es para un solo problema\n• Los tickets se cierran después de la respuesta del admin\n• Crea un nuevo ticket para nuevas preguntas\n• Tus datos se guardan para un soporte más rápido\n\n⏱️ **Soporte ToonPay disponible 24/7**\n\n¿Necesitas ayuda inmediata? Contacta @ToonPaySupport",
        'select_language': "🌐 **Por favor, selecciona tu idioma:**",
        'language_changed': "✅ ¡Idioma cambiado a Español!",
        
        'select_category': "📋 **Selecciona tu categoría de problema:**",
        'ask_name': "👤 **Por favor, ingresa tu nombre completo:**\n\nEjemplo: `Juan Pérez`",
        'name_saved': "✅ **¡Nombre guardado!**",
        'ask_email': "📧 **Ahora ingresa tu dirección de email:**\n\nEjemplo: `usuario@example.com`",
        'invalid_email': "❌ **¡Formato de email inválido!**\n\nPor favor envía una dirección de email válida.\nEjemplo: `usuario@example.com`",
        'email_saved': "✅ **¡Email guardado!**",
        'ask_phone': "📞 **Ahora envía tu número de teléfono:**\n\nEjemplo: `+1234567890` o `1234567890`",
        'invalid_phone': "❌ **¡Número de teléfono inválido!**\n\nPor favor envía un número de teléfono válido (10-15 dígitos).\nEjemplo: `+1234567890` o `1234567890`",
        'phone_saved': "✅ **¡Teléfono guardado!**",
        'ask_question': "📝 **Ahora describe tu problema en detalle:**\n\nPor favor incluye:\n• ¿Qué pasó?\n• ¿Cuándo pasó?\n• ¿Algún mensaje de error?",
        'ticket_created': "✅ **¡Tu ticket ha sido creado!**\n\n**ID del Ticket:** `#{ticket_id}`\n**Categoría:** {category}\n**Nombre:** {name}\n\nNos comunicaremos contigo pronto.\n\nPuedes verificar el estado de tu ticket usando /start y haciendo clic en 'Mis Tickets'.",
        'ticket_failed': "❌ **Error al crear el ticket.**\n\nPor favor inténtalo de nuevo más tarde o contacta a @ToonPaySupport",
        'ticket_error': "❌ **Ocurrió un error al crear tu ticket.**\n\nPor favor inténtalo de nuevo más tarde o contacta a @ToonPaySupport",
        'cancel': "❌ **Creación de ticket cancelada.**\n\nPuedes comenzar de nuevo en cualquier momento con /start",
        
        'my_tickets': "📋 **Tus Tickets:**",
        'no_tickets': "📭 Aún no tienes tickets.",
        'create_new': "📝 Crear Nuevo Ticket",
        'refresh': "🔄 Actualizar",
        'status_pending': '⏳ Pendiente',
        'status_in_progress': '🔄 En Progreso',
        'status_closed': '✅ Cerrado',
        'status_spam': '🚫 Spam',
        
        'category_technical': '🛠️ Fondos Faltantes',
        'category_payment': '💰 No puedo iniciar sesión',
        'category_account': '👤 Relacionado con KYC',
        'category_feature': '✨ Problema con Tarjeta',
        'category_other': '❓ Otro',
        
        'new_ticket': "📝 Nuevo Ticket",
        'my_tickets_btn': "📋 Mis Tickets",
        'help_btn': "❓ Ayuda",
        'cancel_btn': "🔙 Cancelar",
        'reply_btn': "💬 Responder",
        'progress_btn': "🔄 En Progreso",
        'spam_btn': "❌ Cerrar como Spam",
        'submit_ticket': "📝 Enviar Ticket",
        'click_here': "🔗 Haz clic aquí",
        'here_link': "Aquí está tu enlace solicitado:",
        
        'group_support': "📬 **¿Necesitas ayuda del Soporte de ToonPay?**\n\nHaz clic en el botón para enviar tu ticket de forma privada.\nNuestro equipo de soporte te ayudará dentro de 24 horas.",
        'bot_online': "✅ **¡El bot está en línea y listo para recibir tickets!**",
    },
    
    'fr': {
        # French translations
        'welcome': "🎫 **Bienvenue sur le Bot de Support ToonPay !**\n\nJe suis là pour vous aider avec tous vos problèmes.\n\n**Comment créer un ticket :**\n1️⃣ Cliquez sur 'Nouveau Ticket'\n2️⃣ Sélectionnez votre catégorie\n3️⃣ Fournissez votre nom\n4️⃣ Fournissez votre email\n5️⃣ Fournissez votre numéro de téléphone\n6️⃣ Décrivez votre problème\n7️⃣ Soumettre\n\n⏱️ **Support ToonPay disponible 24h/24**\n\nCliquez sur le bouton ci-dessous pour commencer !",
        'help': "ℹ️ **Aide et Support**\n\n**Comment créer un ticket :**\n1. Cliquez sur \"Nouveau Ticket\"\n2. Sélectionnez la catégorie\n3. Fournissez votre nom complet\n4. Fournissez votre adresse email\n5. Fournissez votre numéro de téléphone\n6. Décrivez votre problème\n7. Soumettre\n\n**Notes importantes :**\n• Chaque ticket est pour un seul problème\n• Les tickets se ferment après la réponse de l'admin\n• Créez un nouveau ticket pour de nouvelles questions\n• Vos données sont sauvegardées pour un support plus rapide\n\n⏱️ **Support ToonPay disponible 24h/24**\n\nBesoin d'aide immédiate ? Contactez @ToonPaySupport",
        'select_language': "🌐 **Veuillez sélectionner votre langue :**",
        'language_changed': "✅ Langue changée en Français !",
        
        'select_category': "📋 **Sélectionnez votre catégorie de problème :**",
        'ask_name': "👤 **Veuillez entrer votre nom complet :**\n\nExemple : `Jean Dupont`",
        'name_saved': "✅ **Nom sauvegardé !**",
        'ask_email': "📧 **Entrez maintenant votre adresse email :**\n\nExemple : `utilisateur@example.com`",
        'invalid_email': "❌ **Format d'email invalide !**\n\nVeuillez envoyer une adresse email valide.\nExemple : `utilisateur@example.com`",
        'email_saved': "✅ **Email sauvegardé !**",
        'ask_phone': "📞 **Envoyez maintenant votre numéro de téléphone :**\n\nExemple : `+1234567890` ou `1234567890`",
        'invalid_phone': "❌ **Numéro de téléphone invalide !**\n\nVeuillez envoyer un numéro de téléphone valide (10-15 chiffres).\nExemple : `+1234567890` ou `1234567890`",
        'phone_saved': "✅ **Téléphone sauvegardé !**",
        'ask_question': "📝 **Décrivez maintenant votre problème en détail :**\n\nVeuillez inclure :\n• Qu'est-ce qui s'est passé ?\n• Quand cela s'est-il produit ?\n• Des messages d'erreur ?",
        'ticket_created': "✅ **Votre ticket a été créé !**\n\n**ID du Ticket :** `#{ticket_id}`\n**Catégorie :** {category}\n**Nom :** {name}\n\nNous vous répondrons bientôt.\n\nVous pouvez vérifier le statut de votre ticket avec /start et en cliquant sur 'Mes Tickets'.",
        'ticket_failed': "❌ **Échec de la création du ticket.**\n\nVeuillez réessayer plus tard ou contacter @ToonPaySupport",
        'ticket_error': "❌ **Une erreur est survenue lors de la création de votre ticket.**\n\nVeuillez réessayer plus tard ou contacter @ToonPaySupport",
        'cancel': "❌ **Création de ticket annulée.**\n\nVous pouvez recommencer à tout moment avec /start",
        
        'my_tickets': "📋 **Vos Tickets :**",
        'no_tickets': "📭 Vous n'avez pas encore de tickets.",
        'create_new': "📝 Créer un Nouveau Ticket",
        'refresh': "🔄 Actualiser",
        'status_pending': '⏳ En attente',
        'status_in_progress': '🔄 En cours',
        'status_closed': '✅ Fermé',
        'status_spam': '🚫 Spam',
        
        'category_technical': '🛠️ Fonds Manquants',
        'category_payment': '💰 Connexion impossible',
        'category_account': '👤 Lié au KYC',
        'category_feature': '✨ Problème de Carte',
        'category_other': '❓ Autre',
        
        'new_ticket': "📝 Nouveau Ticket",
        'my_tickets_btn': "📋 Mes Tickets",
        'help_btn': "❓ Aide",
        'cancel_btn': "🔙 Annuler",
        'reply_btn': "💬 Répondre",
        'progress_btn': "🔄 En cours",
        'spam_btn': "❌ Fermer comme Spam",
        'submit_ticket': "📝 Soumettre le Ticket",
        'click_here': "🔗 Cliquez ici",
        'here_link': "Voici votre lien demandé :",
        
        'group_support': "📬 **Besoin d'aide du Support ToonPay ?**\n\nCliquez sur le bouton pour soumettre votre ticket en privé.\nNotre équipe de support vous assistera dans les 24 heures.",
        'bot_online': "✅ **Le bot est en ligne et prêt à recevoir des tickets !**",
    },
    
    'it': {
        # Italian translations
        'welcome': "🎫 **Benvenuto nel Bot di Supporto ToonPay!**\n\nSono qui per aiutarti con qualsiasi problema tu possa avere.\n\n**Come creare un ticket:**\n1️⃣ Clicca 'Nuovo Ticket'\n2️⃣ Seleziona la categoria\n3️⃣ Fornisci il tuo nome\n4️⃣ Fornisci la tua email\n5️⃣ Fornisci il tuo numero di telefono\n6️⃣ Descrivi il tuo problema\n7️⃣ Invia\n\n⏱️ **Supporto ToonPay disponibile 24/7**\n\nClicca il pulsante qui sotto per iniziare!",
        'help': "ℹ️ **Aiuto e Supporto**\n\n**Come creare un ticket:**\n1. Clicca \"Nuovo Ticket\"\n2. Seleziona categoria\n3. Fornisci il tuo nome completo\n4. Fornisci il tuo indirizzo email\n5. Fornisci il tuo numero di telefono\n6. Descrivi il tuo problema\n7. Invia\n\n**Note importanti:**\n• Ogni ticket è per un solo problema\n• I ticket si chiudono dopo la risposta dell'admin\n• Crea un nuovo ticket per nuove domande\n• I tuoi dati sono salvati per un supporto più veloce\n\n⏱️ **Supporto ToonPay disponibile 24/7**\n\nHai bisogno di assistenza immediata? Contatta @ToonPaySupport",
        'select_language': "🌐 **Seleziona la tua lingua:**",
        'language_changed': "✅ Lingua cambiata in Italiano!",
        
        'select_category': "📋 **Seleziona la categoria del problema:**",
        'ask_name': "👤 **Inserisci il tuo nome completo:**\n\nEsempio: `Mario Rossi`",
        'name_saved': "✅ **Nome salvato!**",
        'ask_email': "📧 **Ora inserisci il tuo indirizzo email:**\n\nEsempio: `utente@example.com`",
        'invalid_email': "❌ **Formato email non valido!**\n\nInvia un indirizzo email valido.\nEsempio: `utente@example.com`",
        'email_saved': "✅ **Email salvata!**",
        'ask_phone': "📞 **Ora invia il tuo numero di telefono:**\n\nEsempio: `+1234567890` o `1234567890`",
        'invalid_phone': "❌ **Numero di telefono non valido!**\n\nInvia un numero di telefono valido (10-15 cifre).\nEsempio: `+1234567890` o `1234567890`",
        'phone_saved': "✅ **Telefono salvato!**",
        'ask_question': "📝 **Ora descrivi il tuo problema in dettaglio:**\n\nIncludi:\n• Cos'è successo?\n• Quando è successo?\n• Eventuali messaggi di errore?",
        'ticket_created': "✅ **Il tuo ticket è stato creato!**\n\n**ID Ticket:** `#{ticket_id}`\n**Categoria:** {category}\n**Nome:** {name}\n\nTi risponderemo presto.\n\nPuoi controllare lo stato del tuo ticket con /start e cliccando su 'I Miei Ticket'.",
        'ticket_failed': "❌ **Impossibile creare il ticket.**\n\nRiprova più tardi o contatta @ToonPaySupport",
        'ticket_error': "❌ **Si è verificato un errore durante la creazione del ticket.**\n\nRiprova più tardi o contatta @ToonPaySupport",
        'cancel': "❌ **Creazione ticket annullata.**\n\nPuoi ricominciare in qualsiasi momento con /start",
        
        'my_tickets': "📋 **I Tuoi Ticket:**",
        'no_tickets': "📭 Non hai ancora ticket.",
        'create_new': "📝 Crea Nuovo Ticket",
        'refresh': "🔄 Aggiorna",
        'status_pending': '⏳ In attesa',
        'status_in_progress': '🔄 In corso',
        'status_closed': '✅ Chiuso',
        'status_spam': '🚫 Spam',
        
        'category_technical': '🛠️ Fondi Mancanti',
        'category_payment': '💰 Impossibile accedere',
        'category_account': '👤 Relativo a KYC',
        'category_feature': '✨ Problema Carta',
        'category_other': '❓ Altro',
        
        'new_ticket': "📝 Nuovo Ticket",
        'my_tickets_btn': "📋 I Miei Ticket",
        'help_btn': "❓ Aiuto",
        'cancel_btn': "🔙 Annulla",
        'reply_btn': "💬 Rispondi",
        'progress_btn': "🔄 In corso",
        'spam_btn': "❌ Chiudi come Spam",
        'submit_ticket': "📝 Invia Ticket",
        'click_here': "🔗 Clicca qui",
        'here_link': "Ecco il link richiesto:",
        
        'group_support': "📬 **Hai bisogno di aiuto dal Supporto ToonPay?**\n\nClicca il pulsante per inviare il tuo ticket privatamente.\nIl nostro team di supporto ti assisterà entro 24 ore.",
        'bot_online': "✅ **Il bot è online e pronto a ricevere ticket!**",
    },
    
    'pt': {
        # Portuguese translations
        'welcome': "🎫 **Bem-vindo ao Bot de Suporte da ToonPay!**\n\nEstou aqui para ajudá-lo com qualquer problema que você possa ter.\n\n**Como criar um ticket:**\n1️⃣ Clique em 'Novo Ticket'\n2️⃣ Selecione sua categoria\n3️⃣ Forneça seu nome\n4️⃣ Forneça seu email\n5️⃣ Forneça seu número de telefone\n6️⃣ Descreva seu problema\n7️⃣ Enviar\n\n⏱️ **Suporte ToonPay disponível 24/7**\n\nClique no botão abaixo para começar!",
        'help': "ℹ️ **Ajuda e Suporte**\n\n**Como criar um ticket:**\n1. Clique em \"Novo Ticket\"\n2. Selecione a categoria\n3. Forneça seu nome completo\n4. Forneça seu endereço de email\n5. Forneça seu número de telefone\n6. Descreva seu problema\n7. Enviar\n\n**Notas importantes:**\n• Cada ticket é para um único problema\n• Tickets são fechados após resposta do admin\n• Crie um novo ticket para novas perguntas\n• Seus dados são salvos para suporte mais rápido\n\n⏱️ **Suporte ToonPay disponível 24/7**\n\nPrecisa de ajuda imediata? Contate @ToonPaySupport",
        'select_language': "🌐 **Por favor, selecione seu idioma:**",
        'language_changed': "✅ Idioma alterado para Português!",
        
        'select_category': "📋 **Selecione a categoria do seu problema:**",
        'ask_name': "👤 **Por favor, digite seu nome completo:**\n\nExemplo: `João Silva`",
        'name_saved': "✅ **Nome salvo!**",
        'ask_email': "📧 **Agora digite seu endereço de email:**\n\nExemplo: `usuario@example.com`",
        'invalid_email': "❌ **Formato de email inválido!**\n\nPor favor, envie um endereço de email válido.\nExemplo: `usuario@example.com`",
        'email_saved': "✅ **Email salvo!**",
        'ask_phone': "📞 **Agora envie seu número de telefone:**\n\nExemplo: `+1234567890` ou `1234567890`",
        'invalid_phone': "❌ **Número de telefone inválido!**\n\nPor favor, envie um número de telefone válido (10-15 dígitos).\nExemplo: `+1234567890` ou `1234567890`",
        'phone_saved': "✅ **Telefone salvo!**",
        'ask_question': "📝 **Agora descreva seu problema em detalhes:**\n\nPor favor, inclua:\n• O que aconteceu?\n• Quando aconteceu?\n• Alguma mensagem de erro?",
        'ticket_created': "✅ **Seu ticket foi criado!**\n\n**ID do Ticket:** `#{ticket_id}`\n**Categoria:** {category}\n**Nome:** {name}\n\nEntraremos em contato em breve.\n\nVocê pode verificar o status do seu ticket usando /start e clicando em 'Meus Tickets'.",
        'ticket_failed': "❌ **Falha ao criar ticket.**\n\nPor favor, tente novamente mais tarde ou contate @ToonPaySupport",
        'ticket_error': "❌ **Ocorreu um erro ao criar seu ticket.**\n\nPor favor, tente novamente mais tarde ou contate @ToonPaySupport",
        'cancel': "❌ **Criação de ticket cancelada.**\n\nVocê pode começar novamente a qualquer momento com /start",
        
        'my_tickets': "📋 **Seus Tickets:**",
        'no_tickets': "📭 Você ainda não tem tickets.",
        'create_new': "📝 Criar Novo Ticket",
        'refresh': "🔄 Atualizar",
        'status_pending': '⏳ Pendente',
        'status_in_progress': '🔄 Em andamento',
        'status_closed': '✅ Fechado',
        'status_spam': '🚫 Spam',
        
        'category_technical': '🛠️ Fundos Faltando',
        'category_payment': '💰 Não consigo entrar',
        'category_account': '👤 Relacionado a KYC',
        'category_feature': '✨ Problema com Cartão',
        'category_other': '❓ Outro',
        
        'new_ticket': "📝 Novo Ticket",
        'my_tickets_btn': "📋 Meus Tickets",
        'help_btn': "❓ Ajuda",
        'cancel_btn': "🔙 Cancelar",
        'reply_btn': "💬 Responder",
        'progress_btn': "🔄 Em andamento",
        'spam_btn': "❌ Fechar como Spam",
        'submit_ticket': "📝 Enviar Ticket",
        'click_here': "🔗 Clique aqui",
        'here_link': "Aqui está seu link solicitado:",
        
        'group_support': "📬 **Precisa de ajuda do Suporte ToonPay?**\n\nClique no botão para enviar seu ticket em particular.\nNossa equipe de suporte irá ajudá-lo dentro de 24 horas.",
        'bot_online': "✅ **O bot está online e pronto para receber tickets!**",
    },
    
    'ru': {
        # Russian translations
        'welcome': "🎫 **Добро пожаловать в бот поддержки ToonPay!**\n\nЯ здесь, чтобы помочь вам с любыми проблемами.\n\n**Как создать тикет:**\n1️⃣ Нажмите 'Новый тикет'\n2️⃣ Выберите категорию\n3️⃣ Укажите ваше имя\n4️⃣ Укажите ваш email\n5️⃣ Укажите ваш номер телефона\n6️⃣ Опишите вашу проблему\n7️⃣ Отправить\n\n⏱️ **Поддержка ToonPay доступна 24/7**\n\nНажмите кнопку ниже, чтобы начать!",
        'help': "ℹ️ **Помощь и поддержка**\n\n**Как создать тикет:**\n1. Нажмите \"Новый тикет\"\n2. Выберите категорию\n3. Укажите ваше полное имя\n4. Укажите ваш email адрес\n5. Укажите ваш номер телефона\n6. Опишите вашу проблему\n7. Отправить\n\n**Важные заметки:**\n• Каждый тикет для одной проблемы\n• Тикеты закрываются после ответа админа\n• Создайте новый тикет для новых вопросов\n• Ваши данные сохраняются для более быстрой поддержки\n\n⏱️ **Поддержка ToonPay доступна 24/7**\n\nНужна немедленная помощь? Свяжитесь с @ToonPaySupport",
        'select_language': "🌐 **Пожалуйста, выберите язык:**",
        'language_changed': "✅ Язык изменен на Русский!",
        
        'select_category': "📋 **Выберите категорию проблемы:**",
        'ask_name': "👤 **Пожалуйста, введите ваше полное имя:**\n\nПример: `Иван Петров`",
        'name_saved': "✅ **Имя сохранено!**",
        'ask_email': "📧 **Теперь введите ваш email адрес:**\n\nПример: `user@example.com`",
        'invalid_email': "❌ **Неверный формат email!**\n\nПожалуйста, отправьте действительный email адрес.\nПример: `user@example.com`",
        'email_saved': "✅ **Email сохранен!**",
        'ask_phone': "📞 **Теперь отправьте ваш номер телефона:**\n\nПример: `+1234567890` или `1234567890`",
        'invalid_phone': "❌ **Неверный номер телефона!**\n\nПожалуйста, отправьте действительный номер телефона (10-15 цифр).\nПример: `+1234567890` или `1234567890`",
        'phone_saved': "✅ **Телефон сохранен!**",
        'ask_question': "📝 **Теперь подробно опишите вашу проблему:**\n\nПожалуйста, укажите:\n• Что случилось?\n• Когда это случилось?\n• Есть ли сообщения об ошибках?",
        'ticket_created': "✅ **Ваш тикет создан!**\n\n**ID тикета:** `#{ticket_id}`\n**Категория:** {category}\n**Имя:** {name}\n\nМы скоро свяжемся с вами.\n\nВы можете проверить статус тикета с помощью /start и нажав 'Мои тикеты'.",
        'ticket_failed': "❌ **Не удалось создать тикет.**\n\nПожалуйста, попробуйте позже или свяжитесь с @ToonPaySupport",
        'ticket_error': "❌ **Произошла ошибка при создании тикета.**\n\nПожалуйста, попробуйте позже или свяжитесь с @ToonPaySupport",
        'cancel': "❌ **Создание тикета отменено.**\n\nВы можете начать заново в любое время с /start",
        
        'my_tickets': "📋 **Мои тикеты:**",
        'no_tickets': "📭 У вас еще нет тикетов.",
        'create_new': "📝 Создать новый тикет",
        'refresh': "🔄 Обновить",
        'status_pending': '⏳ В ожидании',
        'status_in_progress': '🔄 В процессе',
        'status_closed': '✅ Закрыт',
        'status_spam': '🚫 Спам',
        
        'category_technical': '🛠️ Отсутствуют средства',
        'category_payment': '💰 Не могу войти',
        'category_account': '👤 Связано с KYC',
        'category_feature': '✨ Проблема с картой',
        'category_other': '❓ Другое',
        
        'new_ticket': "📝 Новый тикет",
        'my_tickets_btn': "📋 Мои тикеты",
        'help_btn': "❓ Помощь",
        'cancel_btn': "🔙 Отмена",
        'reply_btn': "💬 Ответить",
        'progress_btn': "🔄 В процессе",
        'spam_btn': "❌ Закрыть как спам",
        'submit_ticket': "📝 Отправить тикет",
        'click_here': "🔗 Нажмите здесь",
        'here_link': "Вот ваш запрошенный ссылка:",
        
        'group_support': "📬 **Нужна помощь от поддержки ToonPay?**\n\nНажмите кнопку, чтобы отправить тикет в частном порядке.\nНаша команда поддержки поможет вам в течение 24 часов.",
        'bot_online': "✅ **Бот онлайн и готов принимать тикеты!**",
    },
    
    'ar': {
        # Arabic translations
        'welcome': "🎫 **مرحبًا بك في بوت دعم ToonPay!**\n\nأنا هنا لمساعدتك في أي مشكلة قد تواجهها.\n\n**كيفية إنشاء تذكرة:**\n1️⃣ انقر على 'تذكرة جديدة'\n2️⃣ اختر الفئة\n3️⃣ قدم اسمك\n4️⃣ قدم بريدك الإلكتروني\n5️⃣ قدم رقم هاتفك\n6️⃣ صف مشكلتك\n7️⃣ إرسال\n\n⏱️ **دعم ToonPay متاح 24/7**\n\nانقر على الزر أدناه للبدء!",
        'help': "ℹ️ **مساعدة ودعم**\n\n**كيفية إنشاء تذكرة:**\n1. انقر على \"تذكرة جديدة\"\n2. اختر الفئة\n3. قدم اسمك الكامل\n4. قدم عنوان بريدك الإلكتروني\n5. قدم رقم هاتفك\n6. صف مشكلتك\n7. إرسال\n\n**ملاحظات مهمة:**\n• كل تذكرة لمشكلة واحدة فقط\n• تُغلق التذاكر بعد رد المشرف\n• أنشئ تذكرة جديدة لأسئلة جديدة\n• يتم حفظ بياناتك لدعم أسرع\n\n⏱️ **دعم ToonPay متاح 24/7**\n\nهل تحتاج إلى مساعدة فورية؟ اتصل بـ @ToonPaySupport",
        'select_language': "🌐 **الرجاء اختيار لغتك:**",
        'language_changed': "✅ تم تغيير اللغة إلى العربية!",
        
        'select_category': "📋 **اختر فئة المشكلة:**",
        'ask_name': "👤 **الرجاء إدخال اسمك الكامل:**\n\nمثال: `أحمد محمد`",
        'name_saved': "✅ **تم حفظ الاسم!**",
        'ask_email': "📧 **الآن أدخل بريدك الإلكتروني:**\n\nمثال: `user@example.com`",
        'invalid_email': "❌ **تنسيق بريد إلكتروني غير صالح!**\n\nالرجاء إرسال عنوان بريد إلكتروني صالح.\nمثال: `user@example.com`",
        'email_saved': "✅ **تم حفظ البريد الإلكتروني!**",
        'ask_phone': "📞 **الآن أرسل رقم هاتفك:**\n\nمثال: `+1234567890` أو `1234567890`",
        'invalid_phone': "❌ **رقم هاتف غير صالح!**\n\nالرجاء إرسال رقم هاتف صالح (10-15 رقمًا).\nمثال: `+1234567890` أو `1234567890`",
        'phone_saved': "✅ **تم حفظ رقم الهاتف!**",
        'ask_question': "📝 **الآن صف مشكلتك بالتفصيل:**\n\nالرجاء تضمين:\n• ماذا حدث؟\n• متى حدث؟\n• هل هناك أي رسائل خطأ؟",
        'ticket_created': "✅ **تم إنشاء تذكرتك!**\n\n**رقم التذكرة:** `#{ticket_id}`\n**الفئة:** {category}\n**الاسم:** {name}\n\nسنتواصل معك قريبًا.\n\nيمكنك التحقق من حالة تذكرتك باستخدام /start والنقر على 'تذاكري'.",
        'ticket_failed': "❌ **فشل إنشاء التذكرة.**\n\nالرجاء المحاولة مرة أخرى لاحقًا أو الاتصال بـ @ToonPaySupport",
        'ticket_error': "❌ **حدث خطأ أثناء إنشاء تذكرتك.**\n\nالرجاء المحاولة مرة أخرى لاحقًا أو الاتصال بـ @ToonPaySupport",
        'cancel': "❌ **تم إلغاء إنشاء التذكرة.**\n\nيمكنك البدء مرة أخرى في أي وقت باستخدام /start",
        
        'my_tickets': "📋 **تذاكري:**",
        'no_tickets': "📭 ليس لديك أي تذاكر بعد.",
        'create_new': "📝 إنشاء تذكرة جديدة",
        'refresh': "🔄 تحديث",
        'status_pending': '⏳ قيد الانتظار',
        'status_in_progress': '🔄 قيد التنفيذ',
        'status_closed': '✅ مغلق',
        'status_spam': '🚫 سبام',
        
        'category_technical': '🛠️ أموال مفقودة',
        'category_payment': '💰 لا يمكن تسجيل الدخول',
        'category_account': '👤 متعلق بـ KYC',
        'category_feature': '✨ مشكلة في البطاقة',
        'category_other': '❓ أخرى',
        
        'new_ticket': "📝 تذكرة جديدة",
        'my_tickets_btn': "📋 تذاكري",
        'help_btn': "❓ مساعدة",
        'cancel_btn': "🔙 إلغاء",
        'reply_btn': "💬 رد",
        'progress_btn': "🔄 قيد التنفيذ",
        'spam_btn': "❌ إغلاق كسبام",
        'submit_ticket': "📝 إرسال التذكرة",
        'click_here': "🔗 اضغط هنا",
        'here_link': "هذا هو الرابط الذي طلبته:",
        
        'group_support': "📬 **هل تحتاج إلى مساعدة من دعم ToonPay؟**\n\nانقر على الزر لإرسال تذكرتك بشكل خاص.\nسيساعدك فريق الدعم لدينا في غضون 24 ساعة.",
        'bot_online': "✅ **البوت متصل وجاهز لاستقبال التذاكر!**",
    },
    
    'zh': {
        # Chinese translations
        'welcome': "🎫 **欢迎使用 ToonPay 支持机器人！**\n\n我在这里帮助您解决任何问题。\n\n**如何创建工单：**\n1️⃣ 点击 '新工单'\n2️⃣ 选择问题类别\n3️⃣ 提供您的姓名\n4️⃣ 提供您的电子邮件\n5️⃣ 提供您的电话号码\n6️⃣ 描述您的问题\n7️⃣ 提交\n\n⏱️ **ToonPay 支持 24/7 可用**\n\n点击下方按钮开始！",
        'help': "ℹ️ **帮助与支持**\n\n**如何创建工单：**\n1. 点击 \"新工单\"\n2. 选择类别\n3. 提供您的全名\n4. 提供您的电子邮件地址\n5. 提供您的电话号码\n6. 描述您的问题\n7. 提交\n\n**重要说明：**\n• 每个工单只处理一个问题\n• 管理员回复后工单关闭\n• 新问题请创建新工单\n• 您的信息将被保存以便更快支持\n\n⏱️ **ToonPay 支持 24/7 可用**\n\n需要立即帮助？联系 @ToonPaySupport",
        'select_language': "🌐 **请选择您的语言：**",
        'language_changed': "✅ 语言已更改为中文！",
        
        'select_category': "📋 **请选择问题类别：**",
        'ask_name': "👤 **请输入您的全名：**\n\n示例：`张三`",
        'name_saved': "✅ **姓名已保存！**",
        'ask_email': "📧 **现在请输入您的电子邮件地址：**\n\n示例：`user@example.com`",
        'invalid_email': "❌ **电子邮件格式无效！**\n\n请发送有效的电子邮件地址。\n示例：`user@example.com`",
        'email_saved': "✅ **电子邮件已保存！**",
        'ask_phone': "📞 **现在请发送您的电话号码：**\n\n示例：`+1234567890` 或 `1234567890`",
        'invalid_phone': "❌ **电话号码无效！**\n\n请发送有效的电话号码（10-15位数字）。\n示例：`+1234567890` 或 `1234567890`",
        'phone_saved': "✅ **电话号码已保存！**",
        'ask_question': "📝 **现在请详细描述您的问题：**\n\n请包括：\n• 发生了什么？\n• 什么时候发生的？\n• 有任何错误消息吗？",
        'ticket_created': "✅ **您的工单已创建！**\n\n**工单编号：** `#{ticket_id}`\n**类别：** {category}\n**姓名：** {name}\n\n我们会尽快回复您。\n\n您可以使用 /start 并点击 '我的工单' 查看工单状态。",
        'ticket_failed': "❌ **创建工单失败。**\n\n请稍后重试或联系 @ToonPaySupport",
        'ticket_error': "❌ **创建工单时出错。**\n\n请稍后重试或联系 @ToonPaySupport",
        'cancel': "❌ **工单创建已取消。**\n\n您可以随时使用 /start 重新开始。",
        
        'my_tickets': "📋 **我的工单：**",
        'no_tickets': "📭 您还没有任何工单。",
        'create_new': "📝 创建新工单",
        'refresh': "🔄 刷新",
        'status_pending': '⏳ 等待中',
        'status_in_progress': '🔄 处理中',
        'status_closed': '✅ 已关闭',
        'status_spam': '🚫 垃圾',
        
        'category_technical': '🛠️ 资金缺失',
        'category_payment': '💰 无法登录账户',
        'category_account': '👤 KYC相关问题',
        'category_feature': '✨ 卡片问题',
        'category_other': '❓ 其他',
        
        'new_ticket': "📝 新工单",
        'my_tickets_btn': "📋 我的工单",
        'help_btn': "❓ 帮助",
        'cancel_btn': "🔙 取消",
        'reply_btn': "💬 回复",
        'progress_btn': "🔄 处理中",
        'spam_btn': "❌ 关闭为垃圾",
        'submit_ticket': "📝 提交工单",
        'click_here': "🔗 点击这里",
        'here_link': "这是您请求的链接：",
        
        'group_support': "📬 **需要 ToonPay 支持帮助？**\n\n点击按钮私下提交您的工单。\n我们的支持团队将在24小时内为您提供帮助。",
        'bot_online': "✅ **机器人已上线，准备接收工单！**",
    },
    
    'ja': {
        # Japanese translations
        'welcome': "🎫 **ToonPay サポートボットへようこそ！**\n\n私はあなたの問題を解決するためにここにいます。\n\n**チケットの作成方法：**\n1️⃣ 「新規チケット」をクリック\n2️⃣ カテゴリを選択\n3️⃣ お名前を入力\n4️⃣ メールアドレスを入力\n5️⃣ 電話番号を入力\n6️⃣ 問題を説明\n7️⃣ 送信\n\n⏱️ **ToonPay サポート 24時間年中無休**\n\n下のボタンをクリックして開始！",
        'help': "ℹ️ **ヘルプとサポート**\n\n**チケットの作成方法：**\n1. 「新規チケット」をクリック\n2. カテゴリを選択\n3. 氏名を入力\n4. メールアドレスを入力\n5. 電話番号を入力\n6. 問題を説明\n7. 送信\n\n**重要な注意事項：**\n• 各チケットは1つの問題のみ\n• 管理者の返信後にチケットは閉じられます\n• 新しい質問は新規チケットを作成\n• 迅速なサポートのためデータは保存されます\n\n⏱️ **ToonPay サポート 24時間年中無休**\n\n即時サポートが必要ですか？ @ToonPaySupport に連絡してください",
        'select_language': "🌐 **言語を選択してください：**",
        'language_changed': "✅ 言語が日本語に変更されました！",
        
        'select_category': "📋 **問題のカテゴリを選択してください：**",
        'ask_name': "👤 **氏名を入力してください：**\n\n例：`山田太郎`",
        'name_saved': "✅ **名前を保存しました！**",
        'ask_email': "📧 **メールアドレスを入力してください：**\n\n例：`user@example.com`",
        'invalid_email': "❌ **メールアドレスの形式が無効です！**\n\n有効なメールアドレスを送信してください。\n例：`user@example.com`",
        'email_saved': "✅ **メールアドレスを保存しました！**",
        'ask_phone': "📞 **電話番号を送信してください：**\n\n例：`+1234567890` または `1234567890`",
        'invalid_phone': "❌ **電話番号が無効です！**\n\n有効な電話番号を送信してください（10-15桁）。\n例：`+1234567890` または `1234567890`",
        'phone_saved': "✅ **電話番号を保存しました！**",
        'ask_question': "📝 **問題を詳しく説明してください：**\n\n以下を含めてください：\n• 何が起こりましたか？\n• いつ起こりましたか？\n• エラーメッセージはありますか？",
        'ticket_created': "✅ **チケットが作成されました！**\n\n**チケットID：** `#{ticket_id}`\n**カテゴリ：** {category}\n**名前：** {name}\n\nすぐにご連絡いたします。\n\nチケットの状態は /start から「マイチケット」をクリックして確認できます。",
        'ticket_failed': "❌ **チケットの作成に失敗しました。**\n\n後でもう一度お試しいただくか、@ToonPaySupport にお問い合わせください。",
        'ticket_error': "❌ **チケット作成中にエラーが発生しました。**\n\n後でもう一度お試しいただくか、@ToonPaySupport にお問い合わせください。",
        'cancel': "❌ **チケット作成がキャンセルされました。**\n\nいつでも /start で再開できます。",
        
        'my_tickets': "📋 **マイチケット：**",
        'no_tickets': "📭 まだチケットはありません。",
        'create_new': "📝 新規チケット作成",
        'refresh': "🔄 更新",
        'status_pending': '⏳ 保留中',
        'status_in_progress': '🔄 処理中',
        'status_closed': '✅ 完了',
        'status_spam': '🚫 スパム',
        
        'category_technical': '🛠️ 資金不足',
        'category_payment': '💰 アカウントにログインできない',
        'category_account': '👤 KYC関連',
        'category_feature': '✨ カード問題',
        'category_other': '❓ その他',
        
        'new_ticket': "📝 新規チケット",
        'my_tickets_btn': "📋 マイチケット",
        'help_btn': "❓ ヘルプ",
        'cancel_btn': "🔙 キャンセル",
        'reply_btn': "💬 返信",
        'progress_btn': "🔄 処理中",
        'spam_btn': "❌ スパムとして閉じる",
        'submit_ticket': "📝 チケットを送信",
        'click_here': "🔗 ここをクリック",
        'here_link': "リクエストされたリンクです：",
        
        'group_support': "📬 **ToonPay サポートのヘルプが必要ですか？**\n\nボタンをクリックして、非公開でチケットを送信してください。\nサポートチームが24時間以内にご連絡いたします。",
        'bot_online': "✅ **ボットはオンラインで、チケットを受け付ける準備ができています！**",
    },
    
    'hi': {
        # Hindi translations
        'welcome': "🎫 **ToonPay सपोर्ट बॉट में आपका स्वागत है!**\n\nमैं आपकी किसी भी समस्या में मदद करने के लिए यहाँ हूँ।\n\n**टिकट कैसे बनाएं:**\n1️⃣ 'नया टिकट' पर क्लिक करें\n2️⃣ अपनी श्रेणी चुनें\n3️⃣ अपना नाम दें\n4️⃣ अपना ईमेल दें\n5️⃣ अपना फोन नंबर दें\n6️⃣ अपनी समस्या बताएं\n7️⃣ जमा करें\n\n⏱️ **ToonPay सपोर्ट 24/7 उपलब्ध**\n\nशुरू करने के लिए नीचे दिए गए बटन पर क्लिक करें!",
        'help': "ℹ️ **सहायता और समर्थन**\n\n**टिकट कैसे बनाएं:**\n1. \"नया टिकट\" पर क्लिक करें\n2. श्रेणी चुनें\n3. अपना पूरा नाम दें\n4. अपना ईमेल पता दें\n5. अपना फोन नंबर दें\n6. अपनी समस्या बताएं\n7. जमा करें\n\n**महत्वपूर्ण नोट:**\n• प्रत्येक टिकट केवल एक समस्या के लिए है\n• एडमिन के जवाब के बाद टिकट बंद हो जाते हैं\n• नए सवालों के लिए नया टिकट बनाएं\n• तेज़ समर्थन के लिए आपका डेटा सहेजा जाता है\n\n⏱️ **ToonPay सपोर्ट 24/7 उपलब्ध**\n\nतत्काल सहायता चाहिए? @ToonPaySupport से संपर्क करें",
        'select_language': "🌐 **कृपया अपनी भाषा चुनें:**",
        'language_changed': "✅ भाषा हिंदी में बदल दी गई!",
        
        'select_category': "📋 **अपनी समस्या की श्रेणी चुनें:**",
        'ask_name': "👤 **कृपया अपना पूरा नाम दर्ज करें:**\n\nउदाहरण: `राजेश कुमार`",
        'name_saved': "✅ **नाम सहेजा गया!**",
        'ask_email': "📧 **अब अपना ईमेल पता दर्ज करें:**\n\nउदाहरण: `user@example.com`",
        'invalid_email': "❌ **अमान्य ईमेल प्रारूप!**\n\nकृपया एक मान्य ईमेल पता भेजें।\nउदाहरण: `user@example.com`",
        'email_saved': "✅ **ईमेल सहेजा गया!**",
        'ask_phone': "📞 **अब अपना फोन नंबर भेजें:**\n\nउदाहरण: `+1234567890` या `1234567890`",
        'invalid_phone': "❌ **अमान्य फोन नंबर!**\n\nकृपया एक मान्य फोन नंबर भेजें (10-15 अंक)।\nउदाहरण: `+1234567890` या `1234567890`",
        'phone_saved': "✅ **फोन नंबर सहेजा गया!**",
        'ask_question': "📝 **अब अपनी समस्या का विस्तार से वर्णन करें:**\n\nकृपया शामिल करें:\n• क्या हुआ?\n• यह कब हुआ?\n• कोई त्रुटि संदेश?",
        'ticket_created': "✅ **आपका टिकट बन गया है!**\n\n**टिकट आईडी:** `#{ticket_id}`\n**श्रेणी:** {category}\n**नाम:** {name}\n\nहम जल्द ही आपसे संपर्क करेंगे।\n\nआप /start और 'मेरे टिकट' पर क्लिक करके अपने टिकट की स्थिति देख सकते हैं।",
        'ticket_failed': "❌ **टिकट बनाने में विफल।**\n\nकृपया बाद में पुनः प्रयास करें या @ToonPaySupport से संपर्क करें",
        'ticket_error': "❌ **आपका टिकट बनाते समय एक त्रुटि हुई।**\n\nकृपया बाद में पुनः प्रयास करें या @ToonPaySupport से संपर्क करें",
        'cancel': "❌ **टिकट निर्माण रद्द कर दिया गया।**\n\nआप कभी भी /start के साथ फिर से शुरू कर सकते हैं।",
        
        'my_tickets': "📋 **मेरे टिकट:**",
        'no_tickets': "📭 आपके पास अभी तक कोई टिकट नहीं है।",
        'create_new': "📝 नया टिकट बनाएं",
        'refresh': "🔄 ताज़ा करें",
        'status_pending': '⏳ लंबित',
        'status_in_progress': '🔄 प्रगति पर',
        'status_closed': '✅ बंद हुआ',
        'status_spam': '🚫 स्पैम',
        
        'category_technical': '🛠️ फंड गायब',
        'category_payment': '💰 खाते में लॉगिन नहीं कर सकते',
        'category_account': '👤 KYC संबंधित',
        'category_feature': '✨ कार्ड समस्या',
        'category_other': '❓ अन्य',
        
        'new_ticket': "📝 नया टिकट",
        'my_tickets_btn': "📋 मेरे टिकट",
        'help_btn': "❓ मदद",
        'cancel_btn': "🔙 रद्द करें",
        'reply_btn': "💬 जवाब दें",
        'progress_btn': "🔄 प्रगति पर",
        'spam_btn': "❌ स्पैम के रूप में बंद करें",
        'submit_ticket': "📝 टिकट जमा करें",
        'click_here': "🔗 यहाँ क्लिक करें",
        'here_link': "यह आपका अनुरोधित लिंक है:",
        
        'group_support': "📬 **ToonPay समर्थन से मदद चाहिए?**\n\nअपना टिकट निजी तौर पर जमा करने के लिए बटन पर क्लिक करें।\nहमारी सहायता टीम 24 घंटे के भीतर आपकी सहायता करेगी।",
        'bot_online': "✅ **बॉट ऑनलाइन है और टिकट प्राप्त करने के लिए तैयार है!**",
    },
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
