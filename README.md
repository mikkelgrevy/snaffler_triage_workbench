# Snaffler Triage Workbench

A lightning-fast, interactive Terminal User Interface (TUI) designed to parse, filter, and triage [Snaffler](https://github.com/SnaffCon/Snaffler) logs. 

**What is Triage in this context?**
In cybersecurity, triage is the process of rapidly sorting massive amounts of data to separate the signal (real, exploitable secrets) from the noise (false positives or test accounts). Instead of manually scrolling through thousands of lines of raw text, this workbench categorizes high-value targets and allows analysts to rapidly tag findings, automatically generating a clean, sorted CSV report for clients or the Red Team.

## Features

* **Interactive TUI:** Built entirely with Python's standard `curses` library. 
* **Smart Categorization:** Automatically groups findings into 5 actionable tabs:
  1. Credentials & Passwords
  2. SSH & Private Keys
  3. Infrastructure & Storage (VMDKs, Backup EXEs, KeePass)
  4. Configuration Files
  5. Raw `{Red}` Critical Hits
* **Rapid Triage Workflow:** Use `Enter` to mark a finding as Positive and `Backspace` for Negative. 
* **State Persistence:** Automatically saves and resumes your progress. If you close the tool and return tomorrow, all your tags will still be there.
* **Excel-Ready Export:** Generates a `_triage.csv` file formatted with semicolons (`;`) for immediate, column-perfect opening in European Excel environments. Sorted automatically by priority (POS -> NEG -> NEW).
* **Live Search:** Quickly filter the current view for specific server names, users, or keywords.

## Requirements

* Python 3.x
* Works natively on Linux, macOS, WSL, and standard Windows.

## Installation & Usage

**For Linux / macOS / WSL:**
Runs right out of the box with zero dependencies.
```bash
python3 snaffler_check.py path/to/snaffler_log.txt
```

**For Native Windows (PowerShell / CMD):**
```
pip install windows-curses
python snaffler_check.py path\to\snaffler_log.txt
```
