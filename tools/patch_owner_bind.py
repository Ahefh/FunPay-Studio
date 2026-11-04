path = r'C:\Bots\FunPayStudio\tg_bot\bot.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''def reg_admin(self, m: Message):
        """
        FunPay Studio Exclusive: Первый пользователь, нажавший /start, становится
        полноправным владельцем. Доступ для остальных намертво блокируется.
        """
        if m.chat.type != "private":
            return

        # Если список авторизованных пуст — первый запустивший становится владельцем!
        if not self.authorized_users:
            self.authorized_users[m.from_user.id] = {"role": "owner", "username": m.from_user.username}
            utils.save_authorized_users(self.authorized_users)
            self.setup_chat_notifications(self, m)
            welcome_text = (
                f"👑 <b>Добро пожаловать в FunPay Studio (FPS)!</b>\\n\\n"
                f"Вы успешно привязаны как <b>единственный Владелец</b> этого бота (ID: <code>{m.from_user.id}</code>).\\n"
                f"🔒 <i>Доступ для всех остальных пользователей Telegram навсегда заблокирован.</i>\\n\\n"
                f"Используйте меню ниже для управления автовыдачей, лотами и плагинами."
            )
            logger.info(f"[FPS] Владелец бота успешно зарегистрирован: {m.from_user.username} (ID: {m.from_user.id})")
            self.bot.send_message(m.chat.id, welcome_text, parse_mode="HTML")
            self.send_settings_menu(m)
            return

        # Если бот уже привязан к владельцу, а пишет посторонний:
        if m.from_user.id not in self.authorized_users:
            self.attempts[m.from_user.id] = self.attempts.get(m.from_user.id, 0) + 1
            logger.warning(f"[FPS] Попытка доступа от постороннего: {m.from_user.username} (ID: {m.from_user.id})")
            if self.attempts[m.from_user.id] <= 3:
                self.bot.send_message(
                    m.chat.id,
                    "⛔️ <b>Доступ запрещен.</b>\\nЭтот бот является приватным и привязан к личному аккаунту владельца.",
                    parse_mode="HTML"
                )
            return'''

pos_start = content.find('def reg_admin(self, m: Message):')
pos_end = content.find('def ignore_unauthorized_users(self, c: CallbackQuery):')
if pos_start != -1 and pos_end != -1:
    content = content[:pos_start] + replacement + '\n\n    ' + content[pos_end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('tg_bot/bot.py successfully patched with owner binding!')
else:
    print('Could not find anchor points in tg_bot/bot.py')
