"""
TI-84 Plus CE Search Bridge
============================
Run this on your PC while the TIQUERY program runs on your TI-84.
Requires: pip install pyusb requests beautifulsoup4
On Windows you also need Zadig to install WinUSB driver for TI-84.
"""

import usb.core
import usb.util
import struct
import time
import sys
import threading
import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import scrolledtext, ttk

# ── USB / DUSB constants ────────────────────────────────────────────────────
TI84PCE_VID  = 0x0451
TI84PCE_PID  = 0xE008
EP_OUT       = 0x01   # PC → Calc
EP_IN        = 0x81   # Calc → PC
TIMEOUT_MS   = 3000

# DUSB virtual packet types
DUSB_VPKT_BUF_SIZE_REQ  = 0x0001
DUSB_VPKT_BUF_SIZE_ALLOC= 0x0002
DUSB_VPKT_VIRT_DATA     = 0xBBDB
DUSB_VPKT_VIRT_DATA_LAST= 0xBBDD
DUSB_VPKT_VIRT_DATA_ACK = 0xBBDE

# TI variable parameter IDs for GET/SET
DUSB_PID_VAR_TYPE  = 0x0011
DUSB_PID_VAR_NAME  = 0x0014

# Raw TI-83+/84 packet types (inside virtual packets)
TI83P_CMD_VAR     = 0x06
TI83P_CMD_DATA    = 0x15
TI83P_CMD_EOT     = 0x92
TI83P_CMD_ACK     = 0x56
TI83P_CMD_REQ     = 0xA2
TI83P_CMD_RTS     = 0xC9

TI_TYPE_STR       = 0x04   # String variable type
CALC_MACHINE_ID   = 0x23   # TI-84 Plus CE machine ID

# ── DUSB low-level protocol ─────────────────────────────────────────────────

def dusb_send_raw(dev, data: bytes):
    """Send raw bytes to calculator (chunked to 64 bytes)."""
    chunk = 64
    for i in range(0, len(data), chunk):
        dev.write(EP_OUT, data[i:i+chunk], timeout=TIMEOUT_MS)

def dusb_recv_raw(dev, size=512) -> bytes:
    """Receive raw bytes from calculator."""
    try:
        return bytes(dev.read(EP_IN, size, timeout=TIMEOUT_MS))
    except usb.core.USBTimeoutError:
        return b''

def dusb_make_packet(pkt_type: int, payload: bytes) -> bytes:
    """Build a DUSB raw transport packet."""
    # Format: [payload_size: 4 LE][type: 2 LE][payload]
    return struct.pack('<IH', len(payload), pkt_type) + payload

def dusb_send_packet(dev, pkt_type: int, payload: bytes):
    dusb_send_raw(dev, dusb_make_packet(pkt_type, payload))

def dusb_recv_packet(dev) -> tuple:
    """Receive one DUSB packet. Returns (type, payload)."""
    header = dusb_recv_raw(dev, 6)
    if len(header) < 6:
        return (0, b'')
    size, pkt_type = struct.unpack('<IH', header)
    payload = b''
    if size > 0:
        payload = dusb_recv_raw(dev, size)
    return (pkt_type, payload)

def dusb_handshake(dev):
    """Do the initial buffer-size handshake."""
    # Request buffer info (send BUF_SIZE_REQ with our buffer size 1024)
    dusb_send_packet(dev, DUSB_VPKT_BUF_SIZE_REQ, struct.pack('>I', 1024))
    t, p = dusb_recv_packet(dev)
    if t == DUSB_VPKT_BUF_SIZE_ALLOC:
        return True
    return False

def dusb_send_virt_data(dev, data: bytes):
    """Send data as virtual packet (split if needed)."""
    buf_size = 1018  # safe max payload
    chunks = [data[i:i+buf_size] for i in range(0, len(data), buf_size)]
    for i, chunk in enumerate(chunks):
        last = (i == len(chunks) - 1)
        ptype = DUSB_VPKT_VIRT_DATA_LAST if last else DUSB_VPKT_VIRT_DATA
        # Virtual data format: [data_size: 4 BE][data]
        payload = struct.pack('>I', len(chunk)) + chunk
        dusb_send_packet(dev, ptype, payload)
        # Wait for ACK
        t, _ = dusb_recv_packet(dev)
        # t should be DUSB_VPKT_VIRT_DATA_ACK

def dusb_recv_virt_data(dev) -> bytes:
    """Receive virtual data packets until LAST."""
    data = b''
    while True:
        t, p = dusb_recv_packet(dev)
        if t in (DUSB_VPKT_VIRT_DATA, DUSB_VPKT_VIRT_DATA_LAST):
            chunk_size = struct.unpack('>I', p[:4])[0]
            data += p[4:4+chunk_size]
            # Send ACK
            dusb_send_packet(dev, DUSB_VPKT_VIRT_DATA_ACK, b'\x00\x00\x00\x00')
            if t == DUSB_VPKT_VIRT_DATA_LAST:
                break
        elif t == 0:  # timeout
            break
    return data

# ── TI-83+/84 variable protocol (inside DUSB virtual packets) ───────────────

def ti_make_cmd(cmd: int, payload: bytes) -> bytes:
    """Build a TI-83+/84-style command packet."""
    # [machine_id:1][cmd:1][length:2 LE][payload]
    return bytes([CALC_MACHINE_ID, cmd]) + struct.pack('<H', len(payload)) + payload

def ti_parse_response(data: bytes):
    """Parse a TI-83+/84 response. Returns (machine_id, cmd, payload)."""
    if len(data) < 4:
        return (0, 0, b'')
    mid, cmd = data[0], data[1]
    length = struct.unpack('<H', data[2:4])[0]
    payload = data[4:4+length]
    return (mid, cmd, payload)

def encode_str_var(name: str, value: str) -> bytes:
    """
    Encode a TI-84 String variable for sending to calculator.
    String variables: type 0x04, name like 'Str1' (stored as \xAA\x00 for Str0, etc.)
    Str1-Str9 token bytes: Str1=\xAA\x01, Str2=\xAA\x02 ... Str9=\xAA\x09, Str0=\xAA\x00
    """
    # Get string index (Str1 -> index 1)
    idx = int(name.replace('Str','')) % 10
    var_name = bytes([0xAA, idx])  # TI token for StrN
    
    # Encode the string value as TI character codes (printable ASCII maps 1:1 mostly)
    # TI uses a custom character set but ASCII printable chars are compatible
    text_bytes = value[:99].encode('ascii', errors='replace')  # TI strings max ~99 chars per "line"
    
    # Variable data block: [length: 2 LE][type: 1][var_name_token: varies][data_length: 2 LE][data]
    # For strings: data = [length:2 LE][chars...]
    str_data = struct.pack('<H', len(text_bytes)) + text_bytes
    
    # Full variable block for RTS
    var_data_len = 2 + len(str_data)   # 2 bytes for data length field + str_data
    
    header = (
        struct.pack('<H', var_data_len) +  # length of data section
        bytes([TI_TYPE_STR]) +              # variable type
        var_name +                          # variable name tokens
        bytes([0x00, 0x00])                 # version + flag
    )
    data_section = struct.pack('<H', len(str_data)) + str_data
    return header, data_section

def receive_string_from_calc(dev) -> str | None:
    """
    Wait for the calculator to send a string variable (Str1).
    Returns the string content or None on failure.
    """
    try:
        # Wait for calculator to initiate a send (it will send RTS)
        raw = dusb_recv_virt_data(dev)
        if not raw:
            return None
        
        mid, cmd, payload = ti_parse_response(raw)
        
        if cmd != TI83P_CMD_RTS:  # Ready To Send
            return None
        
        # Parse the variable header from payload
        # payload: [data_len:2][type:1][name:varies][version:1][flag:1]
        if len(payload) < 3:
            return None
        
        data_len = struct.unpack('<H', payload[0:2])[0]
        var_type = payload[2]
        
        if var_type != TI_TYPE_STR:
            return None
        
        # Send ACK
        ack = ti_make_cmd(TI83P_CMD_ACK, b'')
        dusb_send_virt_data(dev, ack)
        
        # Send CTS (Clear To Send)
        cts = ti_make_cmd(0x09, b'')  # 0x09 = CTS
        dusb_send_virt_data(dev, cts)
        
        # Receive data
        raw2 = dusb_recv_virt_data(dev)
        mid2, cmd2, payload2 = ti_parse_response(raw2)
        
        if cmd2 != TI83P_CMD_DATA:
            return None
        
        # Send ACK
        dusb_send_virt_data(dev, ti_make_cmd(TI83P_CMD_ACK, b''))
        
        # Receive EOT
        dusb_recv_virt_data(dev)
        dusb_send_virt_data(dev, ti_make_cmd(TI83P_CMD_ACK, b''))
        
        # Parse string data: first 2 bytes = string length, rest = chars
        if len(payload2) < 2:
            return None
        str_len = struct.unpack('<H', payload2[0:2])[0]
        text = payload2[2:2+str_len].decode('ascii', errors='replace')
        return text
        
    except Exception as e:
        return None

def send_string_to_calc(dev, value: str) -> bool:
    """Send a string variable (Str1) to the calculator."""
    try:
        header, data_section = encode_str_var('Str1', value)
        
        # Send RTS (Ready To Send) with variable header
        rts = ti_make_cmd(TI83P_CMD_RTS, header)
        dusb_send_virt_data(dev, rts)
        
        # Wait for CTS from calc
        raw = dusb_recv_virt_data(dev)
        mid, cmd, _ = ti_parse_response(raw)
        if cmd not in (0x09, TI83P_CMD_ACK):  # CTS or ACK
            pass  # Try anyway
        
        # Send data
        data_pkt = ti_make_cmd(TI83P_CMD_DATA, data_section)
        dusb_send_virt_data(dev, data_pkt)
        
        # Wait for ACK
        dusb_recv_virt_data(dev)
        
        # Send EOT
        eot = ti_make_cmd(TI83P_CMD_EOT, b'')
        dusb_send_virt_data(dev, eot)
        
        # Wait for final ACK
        dusb_recv_virt_data(dev)
        
        return True
    except Exception as e:
        return False

# ── Web search ──────────────────────────────────────────────────────────────

def web_search(query: str) -> str:
    """Search DuckDuckGo and return a short plain-text result for the TI-84 screen."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        r = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        results = []
        for res in soup.select('.result__snippet')[:3]:
            text = res.get_text(separator=' ', strip=True)
            if text:
                results.append(text)
        
        if not results:
            return "NO RESULTS FOUND"
        
        # Format for TI-84 screen (26 chars wide, 10 lines)
        combined = ' | '.join(results)
        # Wrap at 25 chars
        words = combined.split()
        lines = []
        line = ''
        for w in words:
            if len(line) + len(w) + 1 > 25:
                lines.append(line)
                line = w
                if len(lines) >= 8:
                    break
            else:
                line = (line + ' ' + w).strip()
        if line and len(lines) < 8:
            lines.append(line)
        
        return '\n'.join(lines)
    except Exception as e:
        return f"ERROR: {str(e)[:40]}"

# ── GUI ─────────────────────────────────────────────────────────────────────

class TIBridgeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TI-84 Search Bridge")
        self.root.geometry("500x600")
        self.root.configure(bg="#1a1a2e")
        self.dev = None
        self.running = False
        
        self._build_ui()
        self._start_connection_thread()

    def _build_ui(self):
        # Title
        tk.Label(self.root, text="TI-84 SEARCH BRIDGE",
                 font=("Courier", 16, "bold"),
                 fg="#00ff88", bg="#1a1a2e").pack(pady=(15,5))
        
        tk.Label(self.root, text="Run TIQUERY on your calculator",
                 font=("Courier", 10), fg="#888888", bg="#1a1a2e").pack()

        # Status bar
        self.status_var = tk.StringVar(value="⬤  Searching for TI-84...")
        self.status_lbl = tk.Label(self.root, textvariable=self.status_var,
                                   font=("Courier", 10, "bold"),
                                   fg="#ffaa00", bg="#1a1a2e")
        self.status_lbl.pack(pady=8)

        # Calculator screen simulation
        screen_frame = tk.Frame(self.root, bg="#1a1a2e", pady=5)
        screen_frame.pack(fill='x', padx=20)
        
        tk.Label(screen_frame, text="CALCULATOR DISPLAY",
                 font=("Courier", 8), fg="#444466", bg="#1a1a2e").pack(anchor='w')
        
        self.calc_screen = tk.Label(
            screen_frame,
            text="\n" * 10,
            font=("Courier", 12),
            fg="#c8e6c9",
            bg="#1c2233",
            anchor='nw',
            justify='left',
            width=26,
            height=10,
            relief='sunken',
            padx=8, pady=8
        )
        self.calc_screen.pack()

        # Query box
        q_frame = tk.Frame(self.root, bg="#1a1a2e")
        q_frame.pack(fill='x', padx=20, pady=(12,0))
        tk.Label(q_frame, text="LAST QUERY:", font=("Courier", 9),
                 fg="#888888", bg="#1a1a2e").pack(anchor='w')
        self.query_var = tk.StringVar()
        tk.Entry(q_frame, textvariable=self.query_var,
                 font=("Courier", 12), bg="#0d0d1a", fg="#00ff88",
                 insertbackground="#00ff88", state='readonly').pack(fill='x')

        # Result box
        r_frame = tk.Frame(self.root, bg="#1a1a2e")
        r_frame.pack(fill='both', expand=True, padx=20, pady=(8,0))
        tk.Label(r_frame, text="FULL SEARCH RESULT:", font=("Courier", 9),
                 fg="#888888", bg="#1a1a2e").pack(anchor='w')
        self.result_box = scrolledtext.ScrolledText(
            r_frame, font=("Courier", 10),
            bg="#0d0d1a", fg="#aaddff", wrap='word', height=8
        )
        self.result_box.pack(fill='both', expand=True)

        # Manual search (for testing without calc)
        m_frame = tk.Frame(self.root, bg="#1a1a2e")
        m_frame.pack(fill='x', padx=20, pady=8)
        tk.Label(m_frame, text="MANUAL TEST SEARCH:", font=("Courier", 9),
                 fg="#555577", bg="#1a1a2e").pack(anchor='w')
        input_row = tk.Frame(m_frame, bg="#1a1a2e")
        input_row.pack(fill='x')
        self.manual_entry = tk.Entry(input_row, font=("Courier", 11),
                                     bg="#0d0d1a", fg="#ffffff",
                                     insertbackground="#ffffff")
        self.manual_entry.pack(side='left', fill='x', expand=True)
        self.manual_entry.bind('<Return>', lambda e: self._manual_search())
        tk.Button(input_row, text="GO", font=("Courier", 10, "bold"),
                  bg="#005533", fg="#00ff88", command=self._manual_search,
                  relief='flat', padx=8).pack(side='right')

        # Log
        self.log_box = scrolledtext.ScrolledText(
            self.root, font=("Courier", 8),
            bg="#0a0a14", fg="#444466", height=4, wrap='word'
        )
        self.log_box.pack(fill='x', padx=20, pady=(0,10))

    def log(self, msg: str):
        ts = time.strftime('%H:%M:%S')
        self.log_box.insert('end', f"[{ts}] {msg}\n")
        self.log_box.see('end')

    def set_status(self, msg: str, color: str = "#ffaa00"):
        self.status_var.set(msg)
        self.status_lbl.configure(fg=color)

    def show_on_calc_screen(self, lines_text: str):
        """Update the calculator screen simulation."""
        lines = lines_text.split('\n')[:10]
        # Pad to 10 lines
        while len(lines) < 10:
            lines.append('')
        display = '\n'.join(line[:25] for line in lines)
        self.calc_screen.configure(text=display)

    def do_search_and_respond(self, query: str):
        self.log(f"Searching: {query}")
        self.query_var.set(query)
        self.set_status("⬤  Searching...", "#ffaa00")

        result = web_search(query)
        self.log(f"Got result ({len(result)} chars)")

        # Show in GUI
        self.result_box.delete('1.0', 'end')
        self.result_box.insert('1.0', result)

        # Build calc screen display
        screen_lines = [f"Q: {query[:22]}", "─" * 25] + result.split('\n')
        self.show_on_calc_screen('\n'.join(screen_lines))

        # Send to calculator if connected
        if self.dev:
            ok = send_string_to_calc(self.dev, result)
            if ok:
                self.log("Result sent to calculator!")
                self.set_status("⬤  Sent to TI-84!", "#00ff88")
            else:
                self.log("Send failed – try reconnecting")
                self.set_status("⬤  Send failed", "#ff4444")
        else:
            self.set_status("⬤  No calc connected (result shown above)", "#888888")

    def _manual_search(self):
        q = self.manual_entry.get().strip()
        if q:
            threading.Thread(target=self.do_search_and_respond, args=(q,), daemon=True).start()

    def _connection_thread(self):
        """Background thread: connect to TI-84, handshake, then poll for queries."""
        while True:
            # Try to find the calculator
            self.root.after(0, self.set_status, "⬤  Looking for TI-84...", "#ffaa00")
            dev = usb.core.find(idVendor=TI84PCE_VID, idProduct=TI84PCE_PID)
            
            if dev is None:
                self.root.after(0, self.log, "TI-84 not found. Plug in via USB and try again.")
                time.sleep(3)
                continue
            
            try:
                dev.set_configuration()
                usb.util.claim_interface(dev, 0)
            except Exception as e:
                self.root.after(0, self.log, f"USB error: {e}")
                time.sleep(3)
                continue
            
            self.dev = dev
            self.root.after(0, self.set_status, "⬤  TI-84 connected! Run TIQUERY", "#00ff88")
            self.root.after(0, self.log, "TI-84 Plus CE connected via USB!")
            
            try:
                if not dusb_handshake(dev):
                    self.root.after(0, self.log, "Handshake failed")
                    self.dev = None
                    time.sleep(2)
                    continue
                
                self.root.after(0, self.log, "DUSB handshake OK. Waiting for query...")
                
                while True:
                    query = receive_string_from_calc(dev)
                    if query:
                        q = query.strip()
                        if q:
                            self.root.after(0, self.do_search_and_respond, q)
                    time.sleep(0.3)
                    
            except usb.core.USBError as e:
                self.root.after(0, self.log, f"USB disconnected: {e}")
                self.dev = None
                time.sleep(2)

    def _start_connection_thread(self):
        t = threading.Thread(target=self._connection_thread, daemon=True)
        t.start()


def main():
    root = tk.Tk()
    app = TIBridgeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
