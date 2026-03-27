import re, sys, curses, textwrap, csv, os

CATEGORIES = {
    "1": ("CREDS", r"(?:password|pwd|secret|key|token|credential|bind_dn|connectionstring)[\s:=]+[^\s,\]]+|AKIA[A-Z0-9]{16}"),
    "2": ("KEYS", r"[^\s]+\.(?:pem|ppk|pfx|p12|pkcs12|ssh-rk|der)"),
    "3": ("INFRA", r"[^\s]+\.(?:exe|kdbx|vmdk|vhdx|backup|deploy|setup|dmp)"),
    "4": ("CONF", r"[^\s]+\.(?:config|xml|json|yml|yaml|ini|env)"),
    "5": ("MISC RED", r".*\{Red\}.*")
}

triage_db = {}
CSV_FILE = ""

def extract_filepath(log_line):
    match = re.search(r'\((\\\\[^\)]+|[A-Za-z]:\\[^\)]+)\)', log_line)
    if match: return match.group(1)
    return "Unknown Path"

def init_csv_state():
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                triage_db[row['match']] = {'status': row['status'], 'full': row['full'], 'path': row.get('path', '')}

def load_tab(log_path, cat_id):
    tab_matches = []
    seen = set()
    main_pattern = CATEGORIES[cat_id][1]
    
    # Pre-compile patterns for tabs 1-4 so we can exclude them from tab 5
    other_patterns = [re.compile(CATEGORIES[str(i)][1], re.IGNORECASE) for i in range(1, 5)]
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line_text = line.strip()
                
                if "{red}" not in line_text.lower():
                    continue 
                
                # --- NEW EXCLUSION LOGIC ---
                # If we are loading Tab 5, skip the line if it already matches Tabs 1-4
                if cat_id == "5":
                    if any(p.search(line_text) for p in other_patterns):
                        continue
                # ---------------------------
                
                match = re.search(main_pattern, line_text, re.IGNORECASE)
                if match:
                    match_key = match.group(0).lower()
                    if match_key not in triage_db:
                        path = extract_filepath(line_text)
                        triage_db[match_key] = {'status': 'NEW', 'full': line_text, 'path': path}
                    
                    if match_key not in seen:
                        seen.add(match_key)
                        tab_matches.append(match_key)
        return tab_matches
    except: return []

def perform_save(log_path):
    other_patterns = [re.compile(CATEGORIES[str(i)][1], re.IGNORECASE) for i in range(1, 5)]
    
    for cat_id, (_, pattern) in CATEGORIES.items():
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line_text = line.strip()
                    if "{red}" not in line_text.lower():
                        continue 
                    
                    # Ensure the saved CSV also respects the Tab 5 exclusion rule
                    if cat_id == "5":
                        if any(p.search(line_text) for p in other_patterns):
                            continue
                    
                    match = re.search(pattern, line_text, re.IGNORECASE)
                    if match:
                        m_key = match.group(0).lower()
                        if m_key not in triage_db:
                            triage_db[m_key] = {'status': 'NEW', 'full': line_text, 'path': extract_filepath(line_text)}
        except: pass

    def sort_key(item):
        status = item[1]['status']
        if status == 'POS': return 0
        if status == 'NEG': return 1
        return 2

    sorted_items = sorted(triage_db.items(), key=sort_key)

    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['status', 'match', 'path', 'full'], delimiter=';')
        writer.writeheader()
        for match_key, data in sorted_items:
            writer.writerow({'status': data['status'], 'match': match_key, 'path': data['path'], 'full': data['full']})

def draw_gui(stdscr, log_file):
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK) 
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)   
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) 
    
    curses.curs_set(0)
    current_cat = "1"
    
    active_keys = load_tab(log_file, current_cat)
    filtered_keys = active_keys
    search_query = ""
    idx = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        stdscr.attron(curses.A_REVERSE)
        stdscr.addstr(0, 0, f" [{CATEGORIES[current_cat][0]}] | {len(filtered_keys)} Items | Search: '{search_query}' ".ljust(w))
        stdscr.attroff(curses.A_REVERSE)

        list_h = h - 12
        start_pos = max(0, idx - list_h + 1)
        page_keys = filtered_keys[start_pos : start_pos + list_h]
        
        for i, m_key in enumerate(page_keys):
            y = i + 2
            live_status = triage_db[m_key]['status']
            
            style = curses.A_NORMAL
            if live_status == 'POS': style = curses.color_pair(1)
            elif live_status == 'NEG': style = curses.color_pair(2)
            
            label = f"[{live_status}] {m_key}"[:w-5]
            if i + start_pos == idx:
                stdscr.attron(curses.A_REVERSE); stdscr.addstr(y, 2, f"> {label}"); stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(y, 2, f"  {label}", style)

        footer_y = h - 8
        stdscr.addstr(footer_y, 0, "═"*w)
        stdscr.addstr(footer_y + 1, 2, "1-5:Tabs | ENTER:Pos | BACKSPACE:Neg | s:Save | /:Search | q:Quit", curses.A_BOLD)
        
        if filtered_keys:
            current_full = triage_db[filtered_keys[idx]]['full']
            match_str = filtered_keys[idx]
            wrapped = textwrap.wrap(current_full, width=w-4)
            
            for j, line in enumerate(wrapped[:5]):
                if footer_y + 3 + j < h:
                    parts = re.split(f"({re.escape(match_str)})", line, flags=re.IGNORECASE)
                    
                    x_pos = 2
                    for part in parts:
                        if not part: continue
                        
                        if part.lower() == match_str.lower():
                            stdscr.addstr(footer_y + 3 + j, x_pos, part, curses.color_pair(3) | curses.A_BOLD)
                        else:
                            stdscr.addstr(footer_y + 3 + j, x_pos, part, curses.A_DIM)
                        x_pos += len(part)

        stdscr.refresh()
        ch = stdscr.getch()

        if ch == ord('q'): break
        elif ch in [ord(str(i)) for i in range(1, 6)]:
            current_cat = chr(ch)
            active_keys = load_tab(log_file, current_cat)
            filtered_keys = active_keys
            idx = 0; search_query = ""
        elif ch == curses.KEY_UP and idx > 0: idx -= 1
        elif ch == curses.KEY_DOWN and idx < len(filtered_keys)-1: idx += 1
        
        elif ch in [10, 13, curses.KEY_ENTER]: 
            if filtered_keys: triage_db[filtered_keys[idx]]['status'] = 'POS'
        elif ch in [8, 127, curses.KEY_BACKSPACE]: 
            if filtered_keys: triage_db[filtered_keys[idx]]['status'] = 'NEG'
            
        elif ch == ord('s'): 
            stdscr.addstr(h-1, 2, "SAVING... PLEASE WAIT", curses.A_BOLD); stdscr.refresh()
            perform_save(log_file)
            stdscr.addstr(h-1, 2, f"SAVED AS: {CSV_FILE}          ", curses.A_BOLD); stdscr.refresh(); curses.napms(1000)
        elif ch == ord('/'):
            stdscr.addstr(h-1, 2, "Search: "); curses.echo()
            search_query = stdscr.getstr().decode('utf-8'); curses.noecho()
            
            filtered_keys = []
            for k in active_keys:
                if search_query.lower() in k or search_query.lower() in triage_db[k]['full'].lower():
                    filtered_keys.append(k)
            idx = 0

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 snaffler_check.py <logfile>")
        return
    
    global CSV_FILE
    log_file_name = sys.argv[1]
    
    base_name = os.path.splitext(log_file_name)[0]
    CSV_FILE = f"{base_name}_triage.csv"
    
    init_csv_state()
    curses.wrapper(draw_gui, log_file_name)

if __name__ == "__main__": main()