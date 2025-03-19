import tkinter as tk
import win32gui
import win32con
import win32api
import keyboard
import json
import os
import sys
import ctypes
import win32ui
import win32print
from PIL import Image, ImageEnhance, ImageDraw, ImageGrab
import requests
from pathlib import Path
from ctypes import windll, byref, sizeof, Structure, c_int, POINTER, c_bool, c_void_p, WINFUNCTYPE, c_uint
from ctypes.wintypes import (
    DWORD, ULONG, HWND, COLORREF, BYTE, LONG, RECT, HBRUSH, HDC, 
    HFONT, LPCWSTR, MSG, WPARAM, LPARAM
)
import ctypes.wintypes as wintypes
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Define PAINTSTRUCT structure
class PAINTSTRUCT(Structure):
    _fields_ = [
        ('hdc', HDC),
        ('fErase', c_bool),
        ('rcPaint', RECT),
        ('fRestore', c_bool),
        ('fIncUpdate', c_bool),
        ('rgbReserved', BYTE * 32)
    ]

print("Starting application...")

def create_font():
    print("Creating font...")
    lf = win32gui.LOGFONT()
    lf.lfHeight = 28
    lf.lfWidth = 0
    lf.lfWeight = win32con.FW_NORMAL
    lf.lfItalic = False
    lf.lfUnderline = False
    lf.lfStrikeOut = False
    lf.lfCharSet = win32con.ANSI_CHARSET
    lf.lfOutPrecision = win32con.OUT_DEFAULT_PRECIS
    lf.lfClipPrecision = win32con.CLIP_DEFAULT_PRECIS
    lf.lfQuality = win32con.CLEARTYPE_QUALITY
    lf.lfPitchAndFamily = win32con.FF_DONTCARE | win32con.DEFAULT_PITCH
    lf.lfFaceName = "Segoe UI"
    return win32gui.CreateFontIndirect(lf)

def analyze_chess_position(fen_string):
    api_url = "https://stockfish.online/api/s/v2.php"
    
    try:
        params = {
            "fen": fen_string,
            "depth": 15
        }
        
        response = requests.get(api_url, params=params)
        
        if response.status_code == 200:
            analysis = response.json()
            
            # Format the analysis text
            analysis_text = []
            
            # Handle mate
            if analysis.get("mate") is not None:
                mate_in = int(analysis["mate"])
                if mate_in > 0:
                    analysis_text.append(f"♔ Mate in {mate_in}")
                else:
                    analysis_text.append(f"♔ Mate in {abs(mate_in)}")
            # Handle evaluation
            elif "evaluation" in analysis:
                eval_num = float(analysis["evaluation"])
                eval_str = f"+{eval_num:.2f}" if eval_num > 0 else f"{eval_num:.2f}"
                analysis_text.append(f"Evaluation: {eval_str}")
            
            # Handle best move
            if "bestmove" in analysis:
                best_move = analysis["bestmove"].split()[1]
                from_square = best_move[:2]
                to_square = best_move[2:4]
                analysis_text.append(f"Best move: {from_square}->{to_square}")
                
            # Handle continuation
            if "continuation" in analysis:
                moves = analysis["continuation"].split()[:6]
                analysis_text.append(f"Line: {' '.join(moves)}")
            
            # Add position assessment
            if analysis.get("mate") is not None:
                if int(analysis["mate"]) > 0:
                    analysis_text.append("White to mate")
                else:
                    analysis_text.append("Black to mate")
            elif "evaluation" in analysis:
                eval_num = float(analysis["evaluation"])
                if eval_num > 3:
                    analysis_text.append("White is winning")
                elif eval_num < -3:
                    analysis_text.append("Black is winning")
                elif eval_num > 1.5:
                    analysis_text.append("White has advantage")
                elif eval_num < -1.5:
                    analysis_text.append("Black has advantage")
                elif abs(eval_num) <= 0.5:
                    analysis_text.append("Equal position")
                else:
                    analysis_text.append("Slight advantage")
            
            return "\n".join(analysis_text)
        else:
            return f"Error: Server returned {response.status_code}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def get_fen_from_browser():
    driver = None
    try:
        print("Connecting to Chrome...")
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(10)
        
        print("Looking for chess board...")
        # Wait for the board to be visible
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".board"))
            )
        except Exception as e:
            print(f"Board not found: {e}")
            return None
        
        print("Looking for chess pieces...")
        # Wait for pieces to be loaded
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".piece"))
            )
            pieces = driver.find_elements(By.CSS_SELECTOR, ".piece")
            print(f"Found {len(pieces)} pieces")
        except Exception as e:
            print(f"Pieces not found: {e}")
            return None
            
        if not pieces:
            print("No pieces found on the board")
            return None
        
        # Initialize empty board
        board = [['' for _ in range(8)] for _ in range(8)]
        
        # Process each piece
        for piece in pieces:
            try:
                piece_class = piece.get_attribute("class")
                square = piece.get_attribute("data-square")
                if not square:
                    if "square-" in piece_class:
                        square = piece_class.split("square-")[1].split()[0]
                    else:
                        continue
                
                # Convert Chess.com coordinates
                file_num = int(square[0]) - 1
                rank_num = int(square[1]) - 1
                
                # Determine piece type from class
                piece_type = None
                if "br" in piece_class: piece_type = 'r'
                elif "bn" in piece_class: piece_type = 'n'
                elif "bb" in piece_class: piece_type = 'b'
                elif "bq" in piece_class: piece_type = 'q'
                elif "bk" in piece_class: piece_type = 'k'
                elif "bp" in piece_class: piece_type = 'p'
                elif "wr" in piece_class: piece_type = 'R'
                elif "wn" in piece_class: piece_type = 'N'
                elif "wb" in piece_class: piece_type = 'B'
                elif "wq" in piece_class: piece_type = 'Q'
                elif "wk" in piece_class: piece_type = 'K'
                elif "wp" in piece_class: piece_type = 'P'
                
                if piece_type:
                    board[7-rank_num][file_num] = piece_type
                
            except Exception as e:
                print(f"Error processing piece: {e}")
                continue
        
        # Convert board to FEN string
        fen = []
        for row in board:
            empty_count = 0
            row_fen = []
            for piece in row:
                if piece == '':
                    empty_count += 1
                else:
                    if empty_count > 0:
                        row_fen.append(str(empty_count))
                        empty_count = 0
                    row_fen.append(piece)
            if empty_count > 0:
                row_fen.append(str(empty_count))
            fen.append(''.join(row_fen))
        
        fen_string = '/'.join(fen) + ' w KQkq - 0 1'
        print(f"Generated FEN: {fen_string}")
        return fen_string
        
    except Exception as e:
        print(f"Error in get_fen_from_browser: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
            try:
                driver.close()
            except:
                pass

class TransparentWindow:
    def __init__(self):
        print("Initializing window...")

        # Register window class
        wc = win32gui.WNDCLASS()
        self.hinst = win32gui.GetModuleHandle(None)
        wc.lpszClassName = "TransparentOverlay"
        wc.hInstance = self.hinst
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32gui.GetStockObject(win32con.HOLLOW_BRUSH)
        wc.lpfnWndProc = WINFUNCTYPE(c_int, HWND, c_uint, WPARAM, LPARAM)(self.wnd_proc)
        
        try:
            self.classAtom = win32gui.RegisterClass(wc)
        except Exception:
            return

        # Get screen dimensions
        screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        width = 400
        height = 300
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        print(f"Creating window at {x}, {y} with size {width}x{height}")

        # Create the window with proper styles
        style = win32con.WS_POPUP | win32con.WS_VISIBLE
        ex_style = (
            win32con.WS_EX_LAYERED |
            win32con.WS_EX_TRANSPARENT |
            win32con.WS_EX_TOOLWINDOW |
            win32con.WS_EX_TOPMOST |
            win32con.WS_EX_NOACTIVATE
        )

        try:
            self.hwnd = win32gui.CreateWindowEx(
                ex_style,
                wc.lpszClassName,
                "Transparent Overlay",
                style,
                x, y, width, height,
                0, 0,
                self.hinst,
                None
            )
        except Exception:
            return

        print(f"Window handle: {self.hwnd}")

        # Set window to be layered and transparent
        try:
            win32gui.SetLayeredWindowAttributes(
                self.hwnd,
                win32api.RGB(0, 0, 0),
                180,
                win32con.LWA_COLORKEY | win32con.LWA_ALPHA
            )
        except Exception:
            pass

        # Create font for text
        self.font = create_font()
        
        # Initialize visibility state and analysis text
        self.visible = True
        self.analysis_text = (
            "╔══════════════════════════════════╗\n"
            "║         CHESS ANALYZER           ║\n"
            "╠══════════════════════════════════╣\n"
            "║  Press Ctrl+Alt+S to analyze     ║\n"
            "║  Press Ctrl+Alt+H to toggle      ║\n"
            "║  Press Ctrl+Alt+Q to quit        ║\n"
            "╚══════════════════════════════════╝"
        )
        
        # Register hotkeys
        try:
            keyboard.unhook_all()
            keyboard.add_hotkey('ctrl+alt+h', self.toggle_visibility, suppress=False)
            keyboard.add_hotkey('ctrl+alt+s', self.analyze_position, suppress=False)
            keyboard.add_hotkey('ctrl+alt+q', self.quit, suppress=False)
        except Exception:
            pass
        
        # Prevent screen capture
        try:
            WDA_EXCLUDEFROMCAPTURE = 0x00000011
            windll.user32.SetWindowDisplayAffinity(self.hwnd, WDA_EXCLUDEFROMCAPTURE)
        except Exception:
            pass

        # Show the window
        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
        win32gui.UpdateWindow(self.hwnd)

    def analyze_position(self):
        print("Starting position analysis...")
        try:
            fen_string = get_fen_from_browser()
            if not fen_string:
                print("Failed to get FEN string")
                self.analysis_text = (
                    "╔══════════════════════════════════╗\n"
                    "║            ERROR                 ║\n"
                    "╠══════════════════════════════════╣\n"
                    "║   No chess board found. Make     ║\n"
                    "║   sure you have Chess.com open   ║\n"
                    "║   with a game or puzzle.         ║\n"
                    "╚══════════════════════════════════╝"
                )
                win32gui.InvalidateRect(self.hwnd, None, True)
                return
            
            print(f"Analyzing position: {fen_string}")
            analysis = analyze_chess_position(fen_string)
            print(f"Analysis result: {analysis}")
            
            # Update overlay text with a modern gaming aesthetic
            lines = analysis.split('\n')
            formatted_lines = []
            
            # Add each line with proper padding and alignment
            for line in lines:
                if "Evaluation:" in line:
                    formatted_lines.append(f"║ 📊 {line.strip():^30} ║")
                elif "Best move:" in line:
                    formatted_lines.append(f"║ ⚡ {line.strip():^30} ║")
                elif "Line:" in line:
                    formatted_lines.append(f"║ 🔄 {line.strip():^30} ║")
                elif "winning" in line.lower():
                    formatted_lines.append(f"║ 🏆 {line.strip():^30} ║")
                elif "advantage" in line.lower():
                    formatted_lines.append(f"║ ⚔️ {line.strip():^30} ║")
                elif "equal" in line.lower():
                    formatted_lines.append(f"║ ⚖️ {line.strip():^30} ║")
                elif "Mate" in line:
                    formatted_lines.append(f"║ ♔ {line.strip():^30} ║")
                else:
                    formatted_lines.append(f"║ {line.strip():^34} ║")
            
            self.analysis_text = (
                "╔══════════════════════════════════╗\n"
                "║           CHESS ANALYSIS         ║\n"
                "╠══════════════════════════════════╣\n"
                f"{chr(10).join(formatted_lines)}\n"
                "╚══════════════════════════════════╝"
            )
            win32gui.InvalidateRect(self.hwnd, None, True)
            
        except Exception as e:
            print(f"Error in analyze_position: {e}")
            self.analysis_text = (
                "╔══════════════════════════════════╗\n"
                "║            ERROR                 ║\n"
                "╠══════════════════════════════════╣\n"
                f"║ {str(e):^34} ║\n"
                "╚══════════════════════════════════╝"
            )
            win32gui.InvalidateRect(self.hwnd, None, True)

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_PAINT:
            ps = PAINTSTRUCT()
            hdc = windll.user32.BeginPaint(hwnd, byref(ps))
            
            try:
                # Create memory DC and bitmap
                memdc = win32gui.CreateCompatibleDC(hdc)
                rect = win32gui.GetClientRect(hwnd)
                bitmap = win32gui.CreateCompatibleBitmap(hdc, rect[2], rect[3])
                win32gui.SelectObject(memdc, bitmap)
                
                # Fill background with semi-transparent dark color
                br = win32gui.CreateSolidBrush(win32api.RGB(20, 20, 20))
                win32gui.FillRect(memdc, rect, br)
                win32gui.DeleteObject(br)
                
                if self.visible:
                    # Enable high-quality text rendering
                    windll.gdi32.SetBkMode(memdc, win32con.TRANSPARENT)
                    
                    # Draw text with shadow effect
                    old_font = win32gui.SelectObject(memdc, self.font)
                    
                    # Draw shadow
                    win32gui.SetTextColor(memdc, win32api.RGB(0, 0, 0))
                    win32gui.DrawText(
                        memdc, self.analysis_text, -1,
                        (rect[0] + 2, rect[1] + 2, rect[2], rect[3]),
                        win32con.DT_CENTER | win32con.DT_VCENTER | win32con.DT_WORDBREAK
                    )
                    
                    # Draw main text
                    win32gui.SetTextColor(memdc, win32api.RGB(200, 200, 200))
                    win32gui.DrawText(
                        memdc, self.analysis_text, -1,
                        (rect[0], rect[1], rect[2], rect[3]),
                        win32con.DT_CENTER | win32con.DT_VCENTER | win32con.DT_WORDBREAK
                    )
                    
                    win32gui.SelectObject(memdc, old_font)
                
                # Copy memory DC to window DC
                win32gui.BitBlt(
                    hdc, 0, 0, rect[2], rect[3],
                    memdc, 0, 0, win32con.SRCCOPY
                )
                
                # Clean up
                win32gui.DeleteDC(memdc)
                win32gui.DeleteObject(bitmap)
                
            except Exception:
                pass
            
            windll.user32.EndPaint(hwnd, byref(ps))
            return 0
            
        elif msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
            
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
    
    def toggle_visibility(self):
        print("Toggling visibility")
        self.visible = not self.visible
        if self.visible:
            print("Making window visible")
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
        else:
            print("Making window invisible")
            win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)
        win32gui.InvalidateRect(self.hwnd, None, True)
    
    def quit(self):
        """Clean up and quit the application."""
        print("Quitting application...")
        try:
            # Unregister hotkeys first
            keyboard.unhook_all()
            print("Hotkeys unregistered")
            
            # Hide the window
            win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)
            print("Window hidden")
            
            # Post quit message to stop the message loop
            win32gui.PostQuitMessage(0)
            print("Quit message posted")
            
            # Force terminate the process
            os._exit(0)  # This will force terminate all threads
        except Exception as e:
            print(f"Error during quit: {e}")
            os._exit(1)  # Force terminate even on error
    
    def run(self):
        print("Starting message loop...")
        try:
            msg = wintypes.MSG()
            lpmsg = ctypes.byref(msg)
            while windll.user32.GetMessageW(lpmsg, None, 0, 0) > 0:
                windll.user32.TranslateMessage(lpmsg)
                windll.user32.DispatchMessageW(lpmsg)
        except Exception as e:
            print(f"Error in message loop: {e}")

def main():
    """Main function to handle hotkeys and FEN generation."""
    print("Chess Position Analyzer Started")
    print("Press Ctrl+Alt+S to analyze position")
    print("Press Ctrl+Alt+H to toggle overlay visibility")
    print("Press Ctrl+Alt+Q to quit")
    
    # Initialize overlay window
    overlay = TransparentWindow()
    
    # Run the window's message loop
    overlay.run()

if __name__ == "__main__":
    main()