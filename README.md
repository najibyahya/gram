# Gramnetwork Multi-Account (UI Edition)
<img width="1246" height="582" alt="image" src="https://github.com/user-attachments/assets/1c4818b1-a494-4e1d-b882-d6e20d629b3e" />

An advanced automated bot for Gramnetwork supporting multiple accounts, parallel mining, auto tasks, and a **Rich Terminal User Interface (TUI)**.

## ✨ New Features in this Fork

- **Interactive TUI Dashboard**: Monitor all accounts in real-time using a beautiful, responsive terminal table.
- **Dedicated Account Logs**: Click on any account in the table to view its isolated debug logs without clutter.
- **Parallel Task & Mining**: Tasks and mining cycles run simultaneously in the background.
- **Proxy Rotation Support**: Avoid WAF/Cloudflare blocks with built-in proxy rotation (`proxy.txt`).
- **Comprehensive Auto-Tracking**: Tracks Live Countdown, Balance (USD), Tokens, Energy, Referrals, Rate, and Power.
- **Auto Error Logging**: Failed tasks are automatically dumped into `failed.log` for easy troubleshooting.

## 📝 Register
- You can register using this [Link Register](https://t.me/Gramnetwork_bot?startapp=2113168134)

## 🛠 Requirements
- Python 3.8 or higher

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/najibyahya/gram.git
   cd gram
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
3. **Prepare your accounts & proxies**
   - **`data.txt`**: Put one `initData` per line (each line = one account). Example: `query_id=...` or `user%3D...`
   - **`proxy.txt`**: Put your HTTP/HTTPS proxies (1 per line). **Highly recommended** to bypass Cloudflare/HCDN blocks! 
     - Format: `http://user:pass@ip:port` or `http://ip:port`.

## 🎮 How to Run

To run the new Interactive UI version:
```bash
python ui_bot.py
```

## 📖 Usage Guide
1. Fill `data.txt` with your accounts' `initData`.
2. Fill `proxy.txt` with your proxies.
3. Run the script `python ui_bot.py`.
4. **Navigation**: Click on any row in the table to view the specific logs for that account at the bottom.
5. Auto task completion and parallel mining will start instantly in the background.

## 📌 Notes
- The bot will run continuously until you press `Ctrl + C` or `q` to quit the UI.
- 30 seconds delay between tasks to avoid rate-limiting.
- Claim mining will retry up to 5 times if it fails.
- All accounts mine at the same time (parallel).
- Failed tasks will be neatly logged in `failed.log`.

## ⚠️ Warning
Use this at your own risk. Avoid excessive usage that may result in account bans.
