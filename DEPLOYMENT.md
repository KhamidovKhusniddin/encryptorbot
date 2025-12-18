# 🚀 Botni Serverga Joylash (Deploy) Qo'llanmasi

Bu bot lokal fayllar (SQLite va yuklangan fayllar) bilan ishlagani uchun, eng yaxshi variant **VPS (Virtual Private Server)** hisoblanadi (masalan: Ubuntu 20.04/22.04).

## 1. Server Tayyorlash

Serverga `ssh` orqali ulaning va kerakli dasturlarni o'rnating:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git -y
```

## 2. Loyihani Yuklab Olish

Loyihangizni serverga ko'chiring (yoki git orqali):

```bash
cd /home
mkdir mybot
cd mybot
# Fayllarni shu yerga yuklang (FTP yoki Git orqali)
```

## 3. Virtual Muhit (Venv)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> **Eslatma:** Agar `requirements.txt` bo'lmasa, quyidagilarni o'rnating:
> `pip install pyTelegramBotAPI python-dotenv pyzipper cryptography matplotlib psutil`

## 4. .env Faylni Sozlash

`.env` faylini yarating va tokenlaringizni yozing:

```bash
nano .env
```

Ichiga:
```ini
BOT_TOKEN=sizning_bot_tokeningiz
ADMIN_ID=sizning_id_raqamingiz
ADMIN_LOGIN=admin
ADMIN_PASS=12345
```
Saqlash uchun: `Ctrl+O`, `Enter`, `Ctrl+X`.

## 5. Botni Fon Rejimida Ishlatish (Systemd)

Bot server o'chib yonganda ham avtomatik ishlashi uchun `systemd` xizmatini yaratamiz.

1.  Fayl yaratamiz:
    ```bash
    sudo nano /etc/systemd/system/tgbot.service
    ```

2.  Quyidagi kodni yozing (Yo'llarni o'zgartiring!):

    ```ini
    [Unit]
    Description=Telegram Bot Service
    After=network.target

    [Service]
    # Foydalanuvchi nomi (serverdagi user, masalan: root)
    User=root
    
    # Loyiha papkasi
    WorkingDirectory=/home/mybot
    
    # Ishga tushirish buyrug'i (venv ichidagi python bilan)
    ExecStart=/home/mybot/venv/bin/python main.py
    
    # Avtomatik qayta ishga tushish (xatolik bo'lsa)
    Restart=always
    RestartSec=5

    [Install]
    WantedBy=multi-user.target
    ```

3.  Xizmatni ishga tushiramiz:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable tgbot
    sudo systemctl start tgbot
    ```

## 6. Tekshirish va Boshqarish

*   Statusni ko'rish: `sudo systemctl status tgbot`
*   Loglarni ko'rish: `journalctl -u tgbot -f`
*   To'xtatish: `sudo systemctl stop tgbot`
*   Qayta ishlash: `sudo systemctl restart tgbot`

Endi botingiz 24/7 ishlaydi! 🚀
