# 🔐 Secure Crypto Bot 2.0

![Python](https://img.shields.io/badge/Python-3.13-blue) ![Telegram](https://img.shields.io/badge/Telebot-Modular-blue) ![Encryption](https://img.shields.io/badge/Cipher-AES--RSA--ECC-red)

A professional, modular Telegram bot designed for high-security file encryption and secure transmission. This project implements a **Double-Layer Security** model, combining individual file encryption with password-protected, encrypted ZIP containers.

---

## 📜 Intellectual Property & Usage Notice
> [!IMPORTANT]
> **Copyright (c) 2024 [Khusniddin]**
> This project represents unique architectural ideas and security implementations developed by the author. 
> 
> *   **Private Use**: This code is provided for demonstration and private educational purposes only.
> *   **No Redistribution**: Unauthorized redistribution, cloning for commercial use, or rebranding of this bot's unique logic is prohibited without explicit permission from the author.
> *   **Idea Protection**: The specific combination of inline navigation, persistent menus, and multi-algorithm strategy is a proprietary design choice of this project.

---

## 🛡 Security Architecture

The bot employs a "Defense in Depth" strategy:
1.  **File-Level Encryption**: Each uploaded file is encrypted using the user's choice of algorithm:
    *   **AES-256 (GCM)**: Authenticated symmetric encryption for speed and integrity.
    *   **RSA-2048**: Asymmetric hybrid encryption for secure key exchange simulation.
    *   **ECC (SECP256R1)**: Elliptic Curve Cryptography for modern, efficient security.
2.  **Container Encryption**: Encrypted files are bundled into a **ZIP archive** (via `pyzipper`) with **AES-256** encryption at the archive level.
3.  **Password Hardening**: Passwords undergo **PBKDF2** stretching with **600,000 iterations** to thwart brute-force attacks.

## 🚀 Key Features

*   **Dual Keyboard UI**: Professional `InlineKeyboardMarkup` for actions combined with a `ReplyKeyboardMarkup` persistent menu for high-speed navigation.
*   **Modular Design**: Refactored 2.0 architecture with separate handlers for Admin, Encryption, and User flows.
*   **Admin Dashboard**:
    *   📊 Real-time statistics and usage graphs (Matplotlib).
    *   👤 Paginated user management system.
    *   📢 Global broadcast capabilities.
    *   🖥 System resource monitoring.
*   **Multilingual Support**: Built-in support for **Uzbek**, **English**, and **Russian**.
*   **QR Password Manager**: Generate QR codes for generated/used passwords for mobile convenience.

## 📂 Project Structure

```text
├── assets/             # Branding and banners
├── handlers/           # Modular bot logic (admin, encryption, user)
├── utils/              # Core utilities (crypto, db, monitoring)
├── lang/               # Localization strings (JSON)
├── main.py             # Entry point
├── loader.py           # Singleton initializations
└── config.py           # Environment-based configuration
```

## 🛠 Setup & Deployment

1.  **Environment**: Create a `.env` file based on `.env.example`.
2.  **Dependencies**: `pip install -r requirements.txt`
3.  **Run**: `python main.py`

For detailed server setup instructions, see:
*   [VPS Deployment Guide (systemd)](DEPLOYMENT.md)
*   [Cloud Hosting (PaaS) Guide](DEPLOYMENT_PAAS.md)

---

## ⚠️ Disclaimer
This bot is a security tool. The author is not responsible for data loss due to forgotten passwords. **There is no "recovery" back-door** – encryption is absolute.

---
**Developed with ❤️ by [Khusniddin]**
