p = r"C:\Bots\FunPayStudio\free_plugins\auto_withdraw.py"
with open(p, "r", encoding="utf-8") as f:
    c = f.read()

target = '.add(B("💰 Вывести средства сейчас", callback_data=f"{CBT_WITHDRAW_MENU}:3")) \\'
replacement = (
    target + '\n    .add(B("☕️ Поддержать создателей (yuepi-FPS)", url="https://funpay.com/users/11535828/")) \\'
)

if target in c:
    c = c.replace(target, replacement, 1)
    with open(p, "w", encoding="utf-8") as f:
        f.write(c)
    print("Donation button patched successfully into auto_withdraw.py!")
else:
    print("Target not found!")
