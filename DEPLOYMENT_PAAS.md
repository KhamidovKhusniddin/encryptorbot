# ☁️ Cloud (PaaS) Deploy Guide (Render, Heroku, Railway)

Agar sizda VPS yo'q bo'lsa va **Render, Heroku** yoki **Railway** kabi platformalarga joylamoqchi bo'lsangiz, quyidagilarni bilishingiz shart:

> ⚠️ **DIQQAT: Ma'lumotlar o'chib ketishi mumkin!**
> Bu platformalarning tekin yoki oddiy rejalari "Ephemeral Filesystem" ishlatadi. Bu degani, bot qayta ishga tushganda (har kuni yoki deploy qilganda):
> 1.  **SQLite bazasi o'chib ketadi** (Userlar ro'yxati yo'qoladi).
> 2.  **Yuklangan fayllar o'chib ketadi.**

## Yechimlar

1.  **Railway (Tavsiya etiladi):** Railway'da "Volume" (disk) ulab, SQLite faylini saqlab qolish mumkin.
2.  **Render/Heroku:** Bular uchun SQLite o'rniga PostgreSQL va fayllar uchun AWS S3/Cloudinary ishlatish kerak (Kodga o'zgartirish kiritish talab etiladi).

---

## 🚀 Render.com ga joylash (Eng oson, lekin baza o'chadi)

Agar ma'lumotlar o'chib ketishiga rozi bo'lsangiz (test uchun), quyidagini qiling:

1.  Loyihangizni GitHub ga yuklang.
2.  [Render.com](https://render.com) ga kiring va ro'yxatdan o'ting.
3.  **"New"** -> **"Web Service"** emas, balki **"Background Worker"** tanlash tavsiya etiladi (yoki oddiy Python loyiha).
4.  Github repozitoriyangizni ulang.
5.  Settings:
    *   **Build Command:** `pip install -r requirements.txt`
    *   **Start Command:** `python main.py`
6.  **Environment Variables** bo'limiga `.env` ichidagi ma'lumotlarni qo'shing (`BOT_TOKEN`, `ADMIN_ID` va h.k).

## 🚂 Railway.app ga joylash (Baza saqlanadi)

1.  GitHub ga yuklang.
2.  [Railway.app](https://railway.app) ga kiring.
3.  "New Project" -> "Deploy from GitHub repo".
4.  **Variables** bo'limiga `.env` dagi narsalarni yozing.
5.  **Volume** qo'shing va uni `/home/xamidov/Desktop/time` (yoki loyiha papkasi)ga mount qiling (buni sozlash biroz qiyinroq bo'lishi mumkin).

---

## Fayllar
Loyiha ichida tayyor fayllar bor:
*   `Procfile` (Heroku/Render uchun)
*   `runtime.txt` (Python versiyasi)
*   `requirements.txt` (Kutubxonalar)
