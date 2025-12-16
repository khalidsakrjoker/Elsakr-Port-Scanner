"""
Elsakr Port Scanner & Killer - Premium Edition
Scan ports and kill processes using them.
Modern Dark Theme with Premium UI
"""

import os
import sys
import socket
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

from PIL import Image, ImageTk


class Colors:
    """Premium dark theme colors."""
    BG_DARK = "#0a0a0f"
    BG_CARD = "#12121a"
    BG_CARD_HOVER = "#1a1a25"
    BG_INPUT = "#1e1e2e"
    
    PRIMARY = "#f43f5e"  # Rose/Red
    PRIMARY_HOVER = "#fb7185"
    PRIMARY_DARK = "#e11d48"
    
    SECONDARY = "#22d3ee"
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    ERROR = "#ef4444"
    
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#a1a1aa"
    TEXT_MUTED = "#71717a"
    
    BORDER = "#27272a"
    BORDER_FOCUS = "#f43f5e"
    
    # Port status colors
    PORT_OPEN = "#10b981"
    PORT_CLOSED = "#ef4444"
    PORT_FILTERED = "#f59e0b"


class PremiumButton(tk.Canvas):
    """Custom premium button."""
    
    def __init__(self, parent, text, command=None, width=200, height=45, 
                 primary=True, color=None, **kwargs):
        super().__init__(parent, width=width, height=height, 
                        bg=Colors.BG_CARD, highlightthickness=0, **kwargs)
        
        self.command = command
        self.text = text
        self.width = width
        self.height = height
        self.primary = primary
        self.custom_color = color
        self.hovered = False
        self.enabled = True
        
        self.draw_button()
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        
    def draw_button(self):
        self.delete("all")
        
        if not self.enabled:
            bg_color = Colors.BG_INPUT
            text_color = Colors.TEXT_MUTED
        elif self.custom_color:
            bg_color = self.custom_color
            text_color = Colors.TEXT_PRIMARY
        elif self.primary:
            bg_color = Colors.PRIMARY_HOVER if self.hovered else Colors.PRIMARY
            text_color = Colors.TEXT_PRIMARY
        else:
            bg_color = Colors.BG_CARD_HOVER if self.hovered else Colors.BG_INPUT
            text_color = Colors.TEXT_SECONDARY
        
        radius = 10
        self.create_rounded_rect(2, 2, self.width-2, self.height-2, 
                                  radius, fill=bg_color, outline="")
        self.create_text(self.width//2, self.height//2, 
                        text=self.text, fill=text_color,
                        font=("Segoe UI Semibold", 11))
        
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
            x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2,
            x1, y2, x1, y2-radius, x1, y1+radius, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
        
    def on_enter(self, event):
        if self.enabled:
            self.hovered = True
            self.draw_button()
            self.config(cursor="hand2")
        
    def on_leave(self, event):
        self.hovered = False
        self.draw_button()
        
    def on_click(self, event):
        if self.command and self.enabled:
            self.command()
            
    def set_enabled(self, enabled):
        self.enabled = enabled
        self.draw_button()
        
    def set_text(self, text):
        self.text = text
        self.draw_button()


class PremiumCard(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=Colors.BG_CARD, **kwargs)
        self.config(highlightbackground=Colors.BORDER, highlightthickness=1)


class PortScanner:
    """Port scanning logic."""
    
    COMMON_PORTS = {
        20: "FTP-Data", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
        53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS",
        445: "SMB", 993: "IMAPS", 995: "POP3S", 1433: "MSSQL", 1521: "Oracle",
        3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
        6379: "Redis", 8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB"
    }
    
    @staticmethod
    def scan_port(host, port, timeout=1):
        """Scan a single port."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return port, result == 0
        except:
            return port, False
            
    @staticmethod
    def get_service_name(port):
        """Get service name for a port."""
        if port in PortScanner.COMMON_PORTS:
            return PortScanner.COMMON_PORTS[port]
        try:
            return socket.getservbyport(port)
        except:
            return "Unknown"


class ProcessKiller:
    """Process management logic."""
    
    @staticmethod
    def get_process_on_port(port):
        """Get process using a specific port (Windows)."""
        try:
            # Use netstat to find process
            result = subprocess.run(
                ['netstat', '-ano', '-p', 'TCP'],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        # Get process name
                        proc_result = subprocess.run(
                            ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        proc_output = proc_result.stdout.strip()
                        if proc_output:
                            proc_name = proc_output.split(',')[0].strip('"')
                            return {'pid': pid, 'name': proc_name}
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
            
    @staticmethod
    def kill_process(pid):
        """Kill a process by PID."""
        try:
            subprocess.run(
                ['taskkill', '/F', '/PID', str(pid)],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except:
            return False
            
    @staticmethod
    def get_all_listening_ports():
        """Get all listening ports with their processes."""
        try:
            result = subprocess.run(
                ['netstat', '-ano', '-p', 'TCP'],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            ports = []
            for line in result.stdout.split('\n'):
                if 'LISTENING' in line:
                    match = re.search(r':(\d+)\s+.*LISTENING\s+(\d+)', line)
                    if match:
                        port = int(match.group(1))
                        pid = match.group(2)
                        
                        # Get process name
                        proc_result = subprocess.run(
                            ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        proc_output = proc_result.stdout.strip()
                        proc_name = "Unknown"
                        if proc_output:
                            try:
                                proc_name = proc_output.split(',')[0].strip('"')
                            except:
                                pass
                        
                        ports.append({
                            'port': port,
                            'pid': pid,
                            'name': proc_name,
                            'service': PortScanner.get_service_name(port)
                        })
            
            return sorted(ports, key=lambda x: x['port'])
        except Exception as e:
            print(f"Error: {e}")
            return []


class PortScannerApp:
    """Main application class."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Elsakr Port Scanner & Killer")
        self.root.geometry("1100x750")
        self.root.minsize(1000, 700)
        self.root.configure(bg=Colors.BG_DARK)
        
        self.set_window_icon()
        self.load_logo()
        
        # State
        self.scanning = False
        self.scan_results = []
        
        # Build UI
        self.create_ui()
        
    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
        
    def set_window_icon(self):
        try:
            icon_path = self.resource_path(os.path.join("assets", "fav.ico"))
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
            
    def load_logo(self):
        self.logo_photo = None
        try:
            logo_path = self.resource_path(os.path.join("assets", "Sakr-logo.png"))
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)
                logo.thumbnail((50, 50), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo)
        except:
            pass
            
    def create_ui(self):
        main = tk.Frame(self.root, bg=Colors.BG_DARK)
        main.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # Header
        self.create_header(main)
        
        # Notebook for tabs
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=Colors.BG_DARK, borderwidth=0)
        style.configure('TNotebook.Tab', background=Colors.BG_CARD, 
                       foreground=Colors.TEXT_SECONDARY, padding=[20, 10],
                       font=('Segoe UI', 10))
        style.map('TNotebook.Tab', background=[('selected', Colors.BG_DARK)],
                 foreground=[('selected', Colors.TEXT_PRIMARY)])
        
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Tabs
        self.create_scanner_tab()
        self.create_killer_tab()
        self.create_listening_tab()
        
    def create_header(self, parent):
        header = tk.Frame(parent, bg=Colors.BG_DARK)
        header.pack(fill=tk.X)
        
        title_frame = tk.Frame(header, bg=Colors.BG_DARK)
        title_frame.pack(side=tk.LEFT)
        
        if self.logo_photo:
            tk.Label(title_frame, image=self.logo_photo, bg=Colors.BG_DARK).pack(side=tk.LEFT, padx=(0, 15))
        
        title_text = tk.Frame(title_frame, bg=Colors.BG_DARK)
        title_text.pack(side=tk.LEFT)
        
        tk.Label(title_text, text="Port Scanner & Killer", 
                font=("Segoe UI Bold", 22), fg=Colors.TEXT_PRIMARY,
                bg=Colors.BG_DARK).pack(anchor=tk.W)
        tk.Label(title_text, text="Scan ports and manage processes",
                font=("Segoe UI", 10), fg=Colors.TEXT_MUTED,
                bg=Colors.BG_DARK).pack(anchor=tk.W)
        
        # Version badge
        badge = tk.Label(header, text=" v1.0 ", font=("Segoe UI", 9),
                        fg=Colors.PRIMARY, bg=Colors.BG_INPUT)
        badge.pack(side=tk.RIGHT)
        
    def create_scanner_tab(self):
        """Create port scanner tab."""
        tab = tk.Frame(self.notebook, bg=Colors.BG_DARK)
        self.notebook.add(tab, text="🔍 Port Scanner")
        
        content = tk.Frame(tab, bg=Colors.BG_DARK)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Options card
        options_card = PremiumCard(content, padx=20, pady=15)
        options_card.pack(fill=tk.X, pady=(0, 15))
        
        options_row = tk.Frame(options_card, bg=Colors.BG_CARD)
        options_row.pack(fill=tk.X)
        
        # Host
        tk.Label(options_row, text="Host:", font=("Segoe UI", 10),
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_CARD).pack(side=tk.LEFT)
        
        self.host_entry = tk.Entry(options_row, font=("Segoe UI", 11),
                                   bg=Colors.BG_INPUT, fg=Colors.TEXT_PRIMARY,
                                   insertbackground=Colors.TEXT_PRIMARY, width=20,
                                   relief='flat', highlightthickness=1,
                                   highlightbackground=Colors.BORDER)
        self.host_entry.pack(side=tk.LEFT, padx=(10, 20), ipady=6)
        self.host_entry.insert(0, "127.0.0.1")
        
        # Port range
        tk.Label(options_row, text="Ports:", font=("Segoe UI", 10),
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_CARD).pack(side=tk.LEFT)
        
        self.start_port = tk.Entry(options_row, font=("Segoe UI", 11),
                                   bg=Colors.BG_INPUT, fg=Colors.TEXT_PRIMARY,
                                   insertbackground=Colors.TEXT_PRIMARY, width=8,
                                   relief='flat', highlightthickness=1,
                                   highlightbackground=Colors.BORDER)
        self.start_port.pack(side=tk.LEFT, padx=(10, 5), ipady=6)
        self.start_port.insert(0, "1")
        
        tk.Label(options_row, text="-", font=("Segoe UI", 12),
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_CARD).pack(side=tk.LEFT)
        
        self.end_port = tk.Entry(options_row, font=("Segoe UI", 11),
                                 bg=Colors.BG_INPUT, fg=Colors.TEXT_PRIMARY,
                                 insertbackground=Colors.TEXT_PRIMARY, width=8,
                                 relief='flat', highlightthickness=1,
                                 highlightbackground=Colors.BORDER)
        self.end_port.pack(side=tk.LEFT, padx=(5, 20), ipady=6)
        self.end_port.insert(0, "1024")
        
        # Scan button
        self.scan_btn = PremiumButton(options_row, text="🔍 Start Scan",
                                      command=self.start_scan, width=150, height=40)
        self.scan_btn.pack(side=tk.LEFT, padx=(20, 10))
        
        # Quick scan buttons
        PremiumButton(options_row, text="⚡ Common Ports",
                     command=self.scan_common_ports, width=140, height=40,
                     primary=False).pack(side=tk.LEFT, padx=5)
        
        # Progress
        progress_frame = tk.Frame(content, bg=Colors.BG_DARK)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_canvas = tk.Canvas(progress_frame, height=6,
                                         bg=Colors.BG_INPUT, highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X)
        
        self.status_label = tk.Label(progress_frame, text="Ready to scan",
                                     font=("Segoe UI", 10), fg=Colors.TEXT_MUTED,
                                     bg=Colors.BG_DARK)
        self.status_label.pack(pady=(5, 0))
        
        # Results
        results_card = PremiumCard(content, padx=0, pady=0)
        results_card.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        style = ttk.Style()
        style.configure("Scanner.Treeview", background=Colors.BG_CARD,
                       foreground=Colors.TEXT_PRIMARY, fieldbackground=Colors.BG_CARD,
                       font=('Segoe UI', 10))
        style.configure("Scanner.Treeview.Heading", background=Colors.BG_INPUT,
                       foreground=Colors.TEXT_SECONDARY, font=('Segoe UI Semibold', 10))
        
        columns = ("Port", "Status", "Service", "Action")
        self.scan_tree = ttk.Treeview(results_card, columns=columns, show="headings",
                                      style="Scanner.Treeview")
        
        self.scan_tree.heading("Port", text="Port")
        self.scan_tree.heading("Status", text="Status")
        self.scan_tree.heading("Service", text="Service")
        self.scan_tree.heading("Action", text="Process")
        
        self.scan_tree.column("Port", width=100)
        self.scan_tree.column("Status", width=100)
        self.scan_tree.column("Service", width=150)
        self.scan_tree.column("Action", width=200)
        
        scrollbar = ttk.Scrollbar(results_card, orient="vertical", command=self.scan_tree.yview)
        self.scan_tree.configure(yscrollcommand=scrollbar.set)
        
        self.scan_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Context menu
        self.scan_tree.bind("<Double-1>", self.on_scan_double_click)
        
    def create_killer_tab(self):
        """Create port killer tab."""
        tab = tk.Frame(self.notebook, bg=Colors.BG_DARK)
        self.notebook.add(tab, text="☠️ Port Killer")
        
        content = tk.Frame(tab, bg=Colors.BG_DARK)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Kill card
        kill_card = PremiumCard(content, padx=30, pady=30)
        kill_card.pack(fill=tk.X)
        
        tk.Label(kill_card, text="⚡ Quick Kill Port",
                font=("Segoe UI Semibold", 16), fg=Colors.TEXT_PRIMARY,
                bg=Colors.BG_CARD).pack(anchor=tk.W, pady=(0, 20))
        
        tk.Label(kill_card, text="Enter the port number to kill the process using it:",
                font=("Segoe UI", 11), fg=Colors.TEXT_SECONDARY,
                bg=Colors.BG_CARD).pack(anchor=tk.W)
        
        input_frame = tk.Frame(kill_card, bg=Colors.BG_CARD)
        input_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.kill_port_entry = tk.Entry(input_frame, font=("Segoe UI", 18),
                                        bg=Colors.BG_INPUT, fg=Colors.TEXT_PRIMARY,
                                        insertbackground=Colors.TEXT_PRIMARY,
                                        relief='flat', width=10, justify='center',
                                        highlightthickness=2,
                                        highlightbackground=Colors.BORDER,
                                        highlightcolor=Colors.PRIMARY)
        self.kill_port_entry.pack(side=tk.LEFT, ipady=10)
        self.kill_port_entry.bind("<Return>", lambda e: self.check_and_kill())
        
        PremiumButton(input_frame, text="🔍 Check",
                     command=self.check_port_process, width=120, height=45,
                     primary=False).pack(side=tk.LEFT, padx=(15, 5))
        
        PremiumButton(input_frame, text="☠️ Kill Process",
                     command=self.check_and_kill, width=150, height=45,
                     color=Colors.ERROR).pack(side=tk.LEFT, padx=5)
        
        # Result
        self.kill_result = tk.Label(kill_card, text="",
                                    font=("Segoe UI", 12), fg=Colors.TEXT_MUTED,
                                    bg=Colors.BG_CARD, justify=tk.LEFT)
        self.kill_result.pack(anchor=tk.W, pady=(20, 0))
        
        # Common ports to kill
        common_card = PremiumCard(content, padx=20, pady=20)
        common_card.pack(fill=tk.X, pady=(20, 0))
        
        tk.Label(common_card, text="🔥 Quick Kill Common Ports",
                font=("Segoe UI Semibold", 13), fg=Colors.TEXT_PRIMARY,
                bg=Colors.BG_CARD).pack(anchor=tk.W, pady=(0, 15))
        
        btn_frame = tk.Frame(common_card, bg=Colors.BG_CARD)
        btn_frame.pack(fill=tk.X)
        
        common_ports = [
            ("3000", "React/Node"),
            ("5000", "Flask"),
            ("8000", "Django"),
            ("8080", "Tomcat"),
            ("3306", "MySQL"),
            ("5432", "PostgreSQL"),
        ]
        
        for port, name in common_ports:
            btn = PremiumButton(btn_frame, text=f"{port}\n{name}",
                               command=lambda p=port: self.quick_kill(p),
                               width=100, height=50, primary=False)
            btn.pack(side=tk.LEFT, padx=5)
            
    def create_listening_tab(self):
        """Create listening ports tab."""
        tab = tk.Frame(self.notebook, bg=Colors.BG_DARK)
        self.notebook.add(tab, text="📊 Listening Ports")
        
        content = tk.Frame(tab, bg=Colors.BG_DARK)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header = tk.Frame(content, bg=Colors.BG_DARK)
        header.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(header, text="All listening ports on this machine",
                font=("Segoe UI", 11), fg=Colors.TEXT_MUTED,
                bg=Colors.BG_DARK).pack(side=tk.LEFT)
        
        PremiumButton(header, text="🔄 Refresh",
                     command=self.refresh_listening, width=120, height=35).pack(side=tk.RIGHT)
        
        # List
        list_card = PremiumCard(content, padx=0, pady=0)
        list_card.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Port", "PID", "Process", "Service", "Action")
        self.listen_tree = ttk.Treeview(list_card, columns=columns, show="headings",
                                        style="Scanner.Treeview")
        
        self.listen_tree.heading("Port", text="Port")
        self.listen_tree.heading("PID", text="PID")
        self.listen_tree.heading("Process", text="Process Name")
        self.listen_tree.heading("Service", text="Service")
        self.listen_tree.heading("Action", text="")
        
        self.listen_tree.column("Port", width=80)
        self.listen_tree.column("PID", width=80)
        self.listen_tree.column("Process", width=200)
        self.listen_tree.column("Service", width=120)
        self.listen_tree.column("Action", width=100)
        
        scrollbar = ttk.Scrollbar(list_card, orient="vertical", command=self.listen_tree.yview)
        self.listen_tree.configure(yscrollcommand=scrollbar.set)
        
        self.listen_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listen_tree.bind("<Double-1>", self.on_listen_double_click)
        
        # Load on tab select
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        
    def on_tab_change(self, event):
        if self.notebook.index(self.notebook.select()) == 2:
            self.refresh_listening()
            
    def update_progress(self, value):
        self.progress_canvas.delete("progress")
        width = self.progress_canvas.winfo_width()
        if width < 10:
            width = 600
        fill_width = width * (value / 100)
        
        if fill_width > 0:
            self.progress_canvas.create_rectangle(
                0, 0, fill_width, 6,
                fill=Colors.PRIMARY, outline="", tags="progress"
            )
            
    def start_scan(self):
        if self.scanning:
            return
            
        host = self.host_entry.get().strip()
        try:
            start = int(self.start_port.get())
            end = int(self.end_port.get())
        except:
            messagebox.showerror("Error", "Invalid port range")
            return
            
        if start > end or start < 1 or end > 65535:
            messagebox.showerror("Error", "Invalid port range (1-65535)")
            return
            
        # Clear results
        for item in self.scan_tree.get_children():
            self.scan_tree.delete(item)
            
        self.scanning = True
        self.scan_btn.set_text("⏳ Scanning...")
        self.scan_btn.set_enabled(False)
        
        thread = threading.Thread(target=self._scan_thread, args=(host, start, end))
        thread.start()
        
    def _scan_thread(self, host, start, end):
        total = end - start + 1
        completed = 0
        open_ports = []
        
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = {executor.submit(PortScanner.scan_port, host, port): port 
                      for port in range(start, end + 1)}
            
            for future in as_completed(futures):
                port, is_open = future.result()
                completed += 1
                
                if is_open:
                    open_ports.append(port)
                    service = PortScanner.get_service_name(port)
                    process = ProcessKiller.get_process_on_port(port)
                    proc_info = f"{process['name']} (PID: {process['pid']})" if process else "—"
                    
                    self.root.after(0, lambda p=port, s=service, pr=proc_info: 
                                   self.scan_tree.insert("", "end", values=(p, "✓ OPEN", s, pr)))
                
                progress = (completed / total) * 100
                self.root.after(0, lambda p=progress: self.update_progress(p))
                self.root.after(0, lambda c=completed, t=total: 
                               self.status_label.config(text=f"Scanned {c}/{t} ports..."))
        
        self.root.after(0, lambda: self.status_label.config(
            text=f"✓ Scan complete! Found {len(open_ports)} open ports"))
        self.root.after(0, lambda: self.scan_btn.set_text("🔍 Start Scan"))
        self.root.after(0, lambda: self.scan_btn.set_enabled(True))
        self.scanning = False
        
    def scan_common_ports(self):
        """Scan only common ports."""
        if self.scanning:
            return
            
        host = self.host_entry.get().strip()
        ports = list(PortScanner.COMMON_PORTS.keys())
        
        # Clear results
        for item in self.scan_tree.get_children():
            self.scan_tree.delete(item)
            
        self.scanning = True
        self.scan_btn.set_text("⏳ Scanning...")
        self.scan_btn.set_enabled(False)
        
        thread = threading.Thread(target=self._scan_common_thread, args=(host, ports))
        thread.start()
        
    def _scan_common_thread(self, host, ports):
        total = len(ports)
        completed = 0
        open_ports = []
        
        for port in ports:
            _, is_open = PortScanner.scan_port(host, port)
            completed += 1
            
            if is_open:
                open_ports.append(port)
                service = PortScanner.get_service_name(port)
                process = ProcessKiller.get_process_on_port(port)
                proc_info = f"{process['name']} (PID: {process['pid']})" if process else "—"
                
                self.root.after(0, lambda p=port, s=service, pr=proc_info: 
                               self.scan_tree.insert("", "end", values=(p, "✓ OPEN", s, pr)))
            
            progress = (completed / total) * 100
            self.root.after(0, lambda p=progress: self.update_progress(p))
            self.root.after(0, lambda c=completed, t=total: 
                           self.status_label.config(text=f"Scanned {c}/{t} common ports..."))
        
        self.root.after(0, lambda: self.status_label.config(
            text=f"✓ Scan complete! Found {len(open_ports)} open ports"))
        self.root.after(0, lambda: self.scan_btn.set_text("🔍 Start Scan"))
        self.root.after(0, lambda: self.scan_btn.set_enabled(True))
        self.scanning = False
        
    def on_scan_double_click(self, event):
        selection = self.scan_tree.selection()
        if selection:
            item = self.scan_tree.item(selection[0])
            port = item['values'][0]
            self.kill_port_entry.delete(0, tk.END)
            self.kill_port_entry.insert(0, str(port))
            self.notebook.select(1)
            self.check_port_process()
            
    def check_port_process(self):
        """Check what process is using a port."""
        try:
            port = int(self.kill_port_entry.get())
        except:
            self.kill_result.config(text="⚠️ Please enter a valid port number", fg=Colors.WARNING)
            return
            
        process = ProcessKiller.get_process_on_port(port)
        
        if process:
            self.kill_result.config(
                text=f"📋 Port {port} is used by:\n   Process: {process['name']}\n   PID: {process['pid']}",
                fg=Colors.SUCCESS
            )
        else:
            self.kill_result.config(text=f"✓ Port {port} is not in use", fg=Colors.TEXT_MUTED)
            
    def check_and_kill(self):
        """Kill process on port."""
        try:
            port = int(self.kill_port_entry.get())
        except:
            self.kill_result.config(text="⚠️ Please enter a valid port number", fg=Colors.WARNING)
            return
            
        process = ProcessKiller.get_process_on_port(port)
        
        if not process:
            self.kill_result.config(text=f"✓ Port {port} is not in use", fg=Colors.TEXT_MUTED)
            return
            
        if messagebox.askyesno("Kill Process", 
                              f"Kill process '{process['name']}' (PID: {process['pid']}) on port {port}?"):
            if ProcessKiller.kill_process(process['pid']):
                self.kill_result.config(
                    text=f"☠️ Killed {process['name']} (PID: {process['pid']})",
                    fg=Colors.SUCCESS
                )
            else:
                self.kill_result.config(text="❌ Failed to kill process", fg=Colors.ERROR)
                
    def quick_kill(self, port):
        """Quick kill a port."""
        self.kill_port_entry.delete(0, tk.END)
        self.kill_port_entry.insert(0, port)
        self.check_and_kill()
        
    def refresh_listening(self):
        """Refresh listening ports list."""
        for item in self.listen_tree.get_children():
            self.listen_tree.delete(item)
            
        ports = ProcessKiller.get_all_listening_ports()
        
        for p in ports:
            self.listen_tree.insert("", "end", 
                                   values=(p['port'], p['pid'], p['name'], p['service'], ""))
                                   
    def on_listen_double_click(self, event):
        selection = self.listen_tree.selection()
        if selection:
            item = self.listen_tree.item(selection[0])
            port = item['values'][0]
            pid = item['values'][1]
            name = item['values'][2]
            
            if messagebox.askyesno("Kill Process", 
                                  f"Kill process '{name}' (PID: {pid}) on port {port}?"):
                if ProcessKiller.kill_process(pid):
                    messagebox.showinfo("Success", f"Killed {name}")
                    self.refresh_listening()
                else:
                    messagebox.showerror("Error", "Failed to kill process")


def main():
    root = tk.Tk()
    app = PortScannerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
