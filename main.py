from curl_cffi import requests
import urllib.parse
import time
import sys
import threading
import random
import os
from fake_useragent import UserAgent
from datetime import datetime

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, RichLog, Label, Static
from textual.containers import Vertical, Horizontal

ua = UserAgent()
UI_APP = None

def load_all_init_data(file_path="data.txt"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        accounts = []
        for i, line in enumerate(lines, 1):
            content = line.strip()
            if content:
                accounts.append({
                    "id": i,
                    "init_data": content,
                    "username": f"Account-{i}",
                    "proxy": None
                })
        return accounts
    except Exception as e:
        return []

def load_proxies(file_path="proxy.txt"):
    try:
        if not os.path.exists(file_path):
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        proxies = []
        for line in lines:
            proxy = line.strip()
            if proxy and not proxy.startswith("user:pass"):
                proxies.append(proxy)
        return proxies
    except Exception as e:
        return []

def get_random_proxy(proxies):
    if not proxies:
        return None
    return random.choice(proxies)

def get_headers():
    return {
        "Accept": "application/json",
        "User-Agent": ua.random
    }

def api_request(method, endpoint, init_data, payload=None, proxy=None, acc_id=None, username=None):
    base_url = "https://app.gramnetwork.online/api/"
    url = base_url + endpoint
    
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "origin": "https://app.gramnetwork.online",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://app.gramnetwork.online/",
        "sec-ch-ua": '"Not)A;Brand";v="24", "Microsoft Edge WebView2";v="149", "Microsoft Edge";v="149", "Chromium";v="149"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0"
    }
    
    proxies = None
    if proxy:
        proxies = {"http": proxy, "https": proxy}
    
    data = {"success": False, "error": "Unknown error"}
    try:
        # Normalize init_data: Jika mengandung '=', berarti belum di-encode.
        # Jika tidak ada '=', berarti sudah dari sananya URL-Encoded (misal dari hasil tgWebAppData).
        # Kita JANGAN pernah me-re-encode data yang sudah di-encode karena Python bisa mengubah karakter tertentu (seperti * atau ~) yang akan merusak Hash Telegram!
        if "=" in init_data:
            safe_init_data = urllib.parse.quote(init_data)
        else:
            safe_init_data = init_data
            
        if method == "GET":
            full_url = f"{url}?initData={safe_init_data}"
            resp = requests.get(full_url, headers=headers, proxies=proxies, timeout=30, impersonate="chrome110")
        else:
            headers["content-type"] = "application/x-www-form-urlencoded"
            body = f"initData={safe_init_data}"
            if payload:
                for k, v in payload.items():
                    body += f"&{k}={urllib.parse.quote(str(v))}"
            resp = requests.post(url, data=body.encode('utf-8'), headers=headers, proxies=proxies, timeout=30, impersonate="chrome110")
        
        try:
            data = resp.json()
        except:
            data = {"success": False, "raw_text": resp.text[:100]}
    except Exception as e:
        data = {"success": False, "error": str(e)}

    # Global UI Debug Logging
    if acc_id is not None:
        payload_str = f" | Payload: {payload}" if payload else ""
        ui_log(acc_id, f"-> [DEBUG {method}] {endpoint}{payload_str} | Response: {data}")

    # Global Error Logging
    if not data.get("success") and username:
        try:
            with open("failed.log", "a", encoding="utf-8") as f:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                payload_str = f" | Payload: {payload}" if payload else ""
                f.write(f"[{ts}] [{username}] API Error: {endpoint} {method}{payload_str} | Response: {data}\n")
        except:
            pass

    return data

def ui_log(account_id, message):
    if UI_APP:
        UI_APP.call_from_thread(UI_APP.add_account_log, account_id, message)

def ui_update(account_id, column, value):
    if UI_APP:
        UI_APP.call_from_thread(UI_APP.update_account_table, account_id, column, value)

def claim_mining(account_id, init_data, username, proxy):
    ui_log(account_id, f"[?] Claim Mining for {username} ...")
    ui_update(account_id, "mining_status", "Claiming Mining...")
    for attempt in range(1, 4):
        result = api_request("POST", "claim_mining.php", init_data, proxy=proxy, acc_id=account_id, username=username)
        if result.get('success'):
            ui_log(account_id, "✅ Claim Mining SUCCESS")
            return True
        time.sleep(3)
    ui_log(account_id, "❌ Claim Mining FAILED after retries")
    return False

def start_mining(account_id, init_data, username, proxy):
    ui_log(account_id, f"[?] Starting Mining for {username} ...")
    ui_update(account_id, "mining_status", "Starting Mining...")
    result = api_request("POST", "start_mining.php", init_data, proxy=proxy, acc_id=account_id, username=username)
    if result.get('success'):
        ui_log(account_id, "✅ Start Mining SUCCESS")
        return True
    else:
        ui_log(account_id, "❌ Start Mining FAILED")
        return False

def mining_worker(account):
    acc_id = account['id']
    username = account['username']
    ui_log(acc_id, f"Mining Worker started for {username} (Proxy: {account['proxy'] or 'Tanpa Proxy'})")
    
    while True:
        try:
            ui_update(acc_id, "mining_status", "Fetching User Data...")
            result = api_request("GET", "get_user_data.php", account["init_data"], proxy=account["proxy"], acc_id=acc_id, username=username)
            
            if not result.get("success") or "user" not in result:
                ui_log(acc_id, f"Failed to get user data.")
                ui_update(acc_id, "mining_status", "Data Fetch Failed (Retrying)")
                time.sleep(10)
                continue

            user = result["user"]
            account["username"] = user.get("username", account["username"])
            username = account["username"]
            time_left = user.get('time_left', '00:00:00')
            mining_status_str = user.get('mining_status', '')

            ui_update(acc_id, "username", username)
            ui_update(acc_id, "balance", f"{user.get('total_balance', '0')} ({user.get('usd_balance', '0')} USD)")
            ui_update(acc_id, "tokens", str(user.get('tokens_earned', '0')))
            ui_update(acc_id, "energy", str(user.get('energy', '0')))
            ui_update(acc_id, "referrals", str(user.get('total_referrals', '0')))
            ui_update(acc_id, "rate", str(user.get('mining_rate', '0')))
            ui_update(acc_id, "power", str(user.get('mining_power', '0')))
            ui_update(acc_id, "time_left", time_left)

            if time_left == "00:00:00" or time_left.startswith("00:00") or mining_status_str.lower() == "ready to claim":
                ui_log(acc_id, "Ready to claim! Executing Claim -> Start cycle.")
                claim_mining(acc_id, account["init_data"], username, account["proxy"])
                time.sleep(3)
                start_mining(acc_id, account["init_data"], username, account["proxy"])
                time.sleep(5)
                # Jalankan cek task setelah claim
                threading.Thread(target=complete_tasks_for_account, args=(account,), daemon=True).start()
                continue

            try:
                h, m, s = map(int, time_left.split(':'))
                seconds_left = h * 3600 + m * 60 + s
            except:
                seconds_left = 300

            ui_update(acc_id, "mining_status", "Mining Live")
            
            while seconds_left > 0:
                hours = seconds_left // 3600
                minutes = (seconds_left % 3600) // 60
                seconds = seconds_left % 60
                current = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                ui_update(acc_id, "time_left", current)
                time.sleep(1)
                seconds_left -= 1

            ui_log(acc_id, f"\nTime finished for {username} -> Claiming & Restarting...")
            claim_mining(acc_id, account["init_data"], username, account["proxy"])
            time.sleep(3)
            start_mining(acc_id, account["init_data"], username, account["proxy"])
            time.sleep(5)
            # Jalankan cek task setelah claim
            threading.Thread(target=complete_tasks_for_account, args=(account,), daemon=True).start()

        except Exception as e:
            ui_log(acc_id, f"Error in mining loop: {e}")
            ui_update(acc_id, "mining_status", "Error in Mining Loop")
            time.sleep(10)

def claim_boost(account_id, init_data, username, proxy):
    ui_log(account_id, f"[?] Claiming Power Boost for {username} ...")
    ui_update(account_id, "boost_status", "Claiming...")
    for attempt in range(1, 4):
        result = api_request("POST", "boost_power.php", init_data, proxy=proxy, acc_id=account_id, username=username)
        if result.get('success'):
            ui_log(account_id, f"✅ Boost Claimed: {result.get('message', 'Success')}")
            ui_update(account_id, "boost_status", "Claimed (4h)")
            return True
        time.sleep(3)
    ui_log(account_id, f"❌ Boost Claim FAILED after retries")
    ui_update(account_id, "boost_status", "Failed")
    return False

def complete_tasks_for_account(account):
    acc_id = account['id']
    username = account['username']
    ui_update(acc_id, "task_status", "Checking Tasks...")
    ui_log(acc_id, f"Processing tasks...")
    
    tasks_data = {}
    for attempt in range(1, 4):
        tasks_data = api_request("GET", "get_tasks.php", account["init_data"], proxy=account["proxy"], acc_id=acc_id, username=username)
        if tasks_data.get('success'):
            break
        time.sleep(3)
        
    if not tasks_data.get('success'):
        ui_log(acc_id, f"❌ Failed to get tasks after retries")
        ui_update(acc_id, "task_status", "Failed")
        return
    
    if tasks_data.get('success'):
        boost_time_left = tasks_data.get('boost_time_left', 0)
        if boost_time_left <= 0:
            claim_boost(acc_id, account["init_data"], username, account["proxy"])
            time.sleep(2)
        else:
            hours = (boost_time_left // 1000) // 3600
            mins = ((boost_time_left // 1000) % 3600) // 60
            ui_log(acc_id, f"⏳ Boost in cooldown: {hours}h {mins}m left")
            ui_update(acc_id, "boost_status", f"Cooldown ({hours}h {mins}m)")
            
    tasks = tasks_data.get('tasks', []) if tasks_data.get('success') else []
    pending = [t for t in tasks if not t.get('is_completed')]
    ui_log(acc_id, f"Found {len(pending)} pending tasks out of {len(tasks)} total tasks.")
    
    if len(pending) == 0:
        ui_update(acc_id, "task_status", "No Tasks/Completed")
        return

    for i, task in enumerate(pending, 1):
        ui_update(acc_id, "task_status", f"Doing Task {i}/{len(pending)}")
        ui_log(acc_id, f"\n[{i}/{len(pending)}] Completing: {task['title']}")
        
        if task.get('type') == 'telegram_chat':
            ui_log(acc_id, f"   [WARNING] Task tipe 'telegram_chat' terdeteksi! Pastikan join manual.")
            ui_log(acc_id, f"   [LINK] -> {task.get('link')}")
            
        payload = {"task_id": task['id']}
        result = api_request("POST", "complete_task.php", account["init_data"], payload, proxy=account["proxy"], acc_id=acc_id, username=username)
        
        if result.get('success'):
            ui_log(acc_id, f"   ✅ Status: Success")
            if 'new_balance' in result:
                ui_update(acc_id, "balance", f"{result['new_balance']} (Updated)")
        else:
            ui_log(acc_id, f"   ❌ Status: Failed")
            
        if i < len(pending):
            time.sleep(30)
            
    ui_log(acc_id, "Task completion finished.")
    ui_update(acc_id, "task_status", "Tasks Completed")

class GramBotApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    #top_panel {
        height: 40%;
        border-bottom: solid green;
    }
    #bottom_panel {
        height: 60%;
        layout: vertical;
    }
    #log_title {
        text-align: center;
        background: $boost;
        color: yellow;
        text-style: bold;
    }
    RichLog {
        height: 100%;
        border: solid $primary;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit")
    ]

    def __init__(self):
        super().__init__()
        self.accounts = []
        self.logs_db = {}
        self.active_log_id = None
        self.table_keys = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="top_panel"):
            yield DataTable(id="accounts_table")
        with Vertical(id="bottom_panel"):
            yield Label("SELECT AN ACCOUNT ABOVE TO VIEW LOGS", id="log_title")
            yield RichLog(id="account_log", highlight=True, markup=True, max_lines=500)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        
        table.add_column("ID", key="id")
        table.add_column("Username", key="username")
        table.add_column("Proxy", key="proxy")
        table.add_column("Balance (USD)", key="balance")
        table.add_column("Tokens", key="tokens")
        table.add_column("Energy", key="energy")
        table.add_column("Referrals", key="referrals")
        table.add_column("Rate", key="rate")
        table.add_column("Power", key="power")
        table.add_column("Task Status", key="task_status")
        table.add_column("Boost Status", key="boost_status")
        table.add_column("Mining Status", key="mining_status")
        table.add_column("Time Left", key="time_left")
        
        table.cursor_type = "row"

        self.accounts = load_all_init_data("data.txt")
        proxies = load_proxies("proxy.txt")
        
        if not self.accounts:
            self.query_one("#log_title").update("[red]No accounts found in data.txt![/red]")
            return

        for account in self.accounts:
            account["proxy"] = get_random_proxy(proxies)
            acc_id = account["id"]
            self.logs_db[acc_id] = []
            proxy_short = account["proxy"].split('@')[-1] if account["proxy"] else "Tanpa Proxy"
            
            row_key = str(acc_id)
            self.table_keys[acc_id] = row_key
            table.add_row(
                str(acc_id), 
                account["username"], 
                proxy_short, 
                "-", "-", "-", "-", "-", "-", "Waiting...", "Waiting...", "Initializing...", "-",
                key=row_key
            )

        self.start_bot_threads()

    def start_bot_threads(self):
        def account_workflow(account):
            acc_id = account['id']
            # 1. Get User Data First
            ui_update(acc_id, "mining_status", "Fetching User Data (Init)...")
            result = api_request("GET", "get_user_data.php", account["init_data"], proxy=account["proxy"], acc_id=acc_id, username=account['username'])
            
            if result.get("success") and "user" in result:
                user = result["user"]
                account["username"] = user.get("username", account["username"])
                ui_update(acc_id, "username", account["username"])
                ui_update(acc_id, "balance", f"{user.get('total_balance', '0')} ({user.get('usd_balance', '0')} USD)")
                ui_update(acc_id, "tokens", str(user.get('tokens_earned', '0')))
                ui_update(acc_id, "energy", str(user.get('energy', '0')))
                ui_update(acc_id, "referrals", str(user.get('total_referrals', '0')))
                ui_update(acc_id, "rate", str(user.get('mining_rate', '0')))
                ui_update(acc_id, "power", str(user.get('mining_power', '0')))
                ui_update(acc_id, "time_left", user.get('time_left', '00:00:00'))
            else:
                ui_log(acc_id, f"Failed initial get_user_data. Proceeding anyway...")

            # 2. Complete Tasks in separate thread so mining can start
            threading.Thread(target=complete_tasks_for_account, args=(account,), daemon=True).start()

            # 3. Enter Mining Loop
            mining_worker(account)

        def worker_flow():
            for account in self.accounts:
                t = threading.Thread(target=account_workflow, args=(account,), daemon=True)
                t.start()
                time.sleep(2)

        coordinator = threading.Thread(target=worker_flow, daemon=True)
        coordinator.start()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        try:
            row_key = event.row_key.value
            acc_id = int(row_key)
            self.active_log_id = acc_id
            
            username = f"Account {acc_id}"
            for acc in self.accounts:
                if acc['id'] == acc_id:
                    username = acc['username']
                    break
            
            self.query_one("#log_title").update(f"--- LOGS FOR: [cyan]{username}[/cyan] ---")
            
            rich_log = self.query_one(RichLog)
            rich_log.clear()
            for msg in self.logs_db.get(acc_id, []):
                rich_log.write(msg)
        except Exception:
            pass

    def add_account_log(self, account_id, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        
        if account_id in self.logs_db:
            self.logs_db[account_id].append(formatted_msg)
            if len(self.logs_db[account_id]) > 500:
                self.logs_db[account_id].pop(0)
                
        if self.active_log_id == account_id:
            rich_log = self.query_one(RichLog)
            rich_log.write(formatted_msg)

    def update_account_table(self, account_id, column, value):
        table = self.query_one(DataTable)
        row_key = self.table_keys.get(account_id)
        if not row_key: return

        try:
            table.update_cell(row_key, column, value)
        except Exception:
            pass


if __name__ == "__main__":
    UI_APP = GramBotApp()
    UI_APP.run()
