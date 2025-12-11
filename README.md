# 🔐 Secure Telegram File Encryption Bot

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![Telegram](https://img.shields.io/badge/Telegram-Bot-blue) ![License](https://img.shields.io/badge/License-MIT-green)

**(Uzbek Description below 🇺🇿)**

A powerful and secure Telegram bot designed to encrypt and decrypt files using military-grade algorithms (**AES-256**, **RSA**, **ECC**). It features a robust double-encryption mechanism where both the file integrity and the container (ZIP) are protected.

## 🚀 Features

*   **Multi-Algorithm Support**:
    *   🗝 **AES-256**: High-speed symmetric encryption.
    *   🛡 **RSA-2048**: Hybrid encryption (AES for data, RSA for keys).
    *   🧬 **ECC (SECP256R1)**: Next-gen elliptic curve cryptography.
*   **Double Security**: Files are encrypted, then packaged into an AES-256 encrypted ZIP archive.
*   **Photo Support**: Automatically handles and encrypts images sent as photos.
*   **Password Policies**: Enforces strong passwords (min 8 chars, alphanumeric) and PBKDF2 hashing (600k iterations).
*   **Admin Panel**: Restricted area for the owner to view users, statistics, and broadcast messages.
*   **User Analytics**: Tracks user joining and activity in a local SQLite database.

## 🛠 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/secure-encryption-bot.git
    cd secure-encryption-bot
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Secrets**:
    Copy the example env file and fill in your data:
    ```bash
    cp .env.example .env
    nano .env
    ```
    *   Get `BOT_TOKEN` from @BotFather.
    *   Set your `ADMIN_ID` (get it from @userinfobot).
    *   Set a secure `ADMIN_LOGIN` and `ADMIN_PASS`.

4.  **Run the Bot**:
    ```bash
    python3 main.py
    ```

---

# 🇺🇿 Telegram Shifrlash Boti

Fayllarni eng yuqori darajada himoyalash uchun mo'ljallangan Telegram boti. Ushbu loyiha **AES**, **RSA** va **ECC** algoritmlari yordamida ma'lumotlaringizni shifrlaydi va ularni parol bilan himoyalangan arxivga joylaydi.

## ✨ Imkoniyatlar

*   **3 Xil Algoritm**: O'zingizga mos xavfsizlik turini tanlang (Tezkor AES yoki Kuchli RSA/ECC).
*   **Ikki Qavatli Himoya**: Faylning o'zi ham, u joylashgan ZIP papka ham alohida shifrlanadi.
*   **Rasm Qo'llab-quvvatlash**: Rasmlarni sifatini buzmagan holda xavfsiz holatga keltiradi.
*   **Kuchli Parol Talabi**: "12345" kabi oddiy parollar qabul qilinmaydi. 600,000 martalik xesh funksiyasi (PBKDF2) ishlatiladi.
*   **Admin Panel**: Bot egasi uchun maxsus bo'lim (Statistika, Baza yuklash, Reklama yuborish).
*   **Analitika**: Foydalanuvchilar bazasi (SQLite) avtomatik shakllanadi.

## ⚙️ Ishga Tushirish

1.  **Loyihani yuklab oling**:
    ```bash
    git clone https://github.com/username/repo-name.git
    ```

2.  **Kutubxonalarni o'rnating**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Sozlamalar (.env)**:
    `.env` faylini yarating va ichiga ma'lumotlaringizni yozing:
    ```ini
    BOT_TOKEN=123456:ABC-DEF...
    ADMIN_ID=SIZNING_ID_RAQAMINGIZ
    ADMIN_LOGIN=admin
    ADMIN_PASS=parol
    ```

4.  **Botni yoqing**:
    ```bash
    python3 main.py
    ```

## ⚠️ Disclaimer
This project is for educational and privacy protection purposes. The developers are not responsible for any lost data due to forgotten passwords. **There is NO "Forgot Password" feature** – if you lose your password, the data is lost forever.

---
Developed by [Khusniddin]
