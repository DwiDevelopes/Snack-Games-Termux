#!/usr/bin/env python3
import os
import random
import time
import sys
from enum import Enum

# Deteksi platform
try:
    import curses
    HAS_CURSES = True
except ImportError:
    HAS_CURSES = False
    print("Curses not available, using fallback input system")

class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3
    LEVEL_COMPLETE = 4
    PAUSED = 5
    SETTINGS = 6
    HIGH_SCORES = 7

class Colors:
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7

class SnakeGame:
    def __init__(self):
        self.screen = None
        self.game_state = GameState.MENU
        self.score = 0
        self.high_score = 0
        self.level = 1
        self.snake_char = '■'
        self.food_char = '●'
        self.obstacle_char = '█'
        self.player_name = "Player1"
        self.is_multiplayer = False
        self.snake2_char = '□'
        self.player2_name = "Player2"
        self.max_y, self.max_x = 20, 40
        self.colors_initialized = False
        self.game_area_top = 3
        self.game_area_bottom = 0
        self.game_area_left = 1
        self.game_area_right = 0
        self.game_speed = 0.15
        self.difficulty = "NORMAL"
        self.sound_enabled = True
        self.high_scores = []
        
    def init_colors(self):
        if HAS_CURSES and not self.colors_initialized:
            curses.start_color()
            curses.init_pair(Colors.RED, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(Colors.GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(Colors.YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(Colors.BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)
            curses.init_pair(Colors.MAGENTA, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
            curses.init_pair(Colors.CYAN, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(Colors.WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
            self.colors_initialized = True
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def init_screen(self):
        if HAS_CURSES:
            self.screen = curses.initscr()
            curses.noecho()
            curses.cbreak()
            curses.curs_set(0)
            self.screen.keypad(True)
            self.screen.nodelay(1)
            self.max_y, self.max_x = self.screen.getmaxyx()
            # Pastikan ukuran layar minimum
            if self.max_y < 20 or self.max_x < 40:
                self.max_y, self.max_x = 20, 40
            self.game_area_bottom = self.max_y - 3
            self.game_area_right = self.max_x - 2
            self.init_colors()
        else:
            # Fallback untuk Windows/Termux
            self.max_y, self.max_x = 20, 40
            self.game_area_bottom = self.max_y - 3
            self.game_area_right = self.max_x - 2
    
    def cleanup_screen(self):
        if HAS_CURSES and self.screen:
            curses.nocbreak()
            self.screen.keypad(False)
            curses.echo()
            curses.endwin()
        else:
            self.clear_screen()
    
    def get_input(self):
        if HAS_CURSES:
            self.screen.timeout(100)
            return self.screen.getch()
        else:
            # Fallback input untuk Windows/Termux
            try:
                import msvcrt
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    return ord(key) if isinstance(key, bytes) else key
            except:
                pass
            return -1
    
    def draw_text(self, y, x, text, color_code=0, centered=False):
        if centered:
            x = max(0, self.max_x // 2 - len(text) // 2)
        
        # Pastikan koordinat berada dalam batas layar
        if y < 0 or y >= self.max_y or x < 0 or x >= self.max_x:
            return
            
        if HAS_CURSES:
            try:
                if color_code > 0:
                    self.screen.addstr(y, x, text, curses.color_pair(color_code))
                else:
                    self.screen.addstr(y, x, text)
            except curses.error:
                pass
        else:
            # Fallback untuk Windows/Termux - dengan warna ANSI
            color_codes = {
                0: "",      # Default
                1: "\033[91m", # Red
                2: "\033[92m", # Green
                3: "\033[93m", # Yellow
                4: "\033[94m", # Blue
                5: "\033[95m", # Magenta
                6: "\033[96m", # Cyan
                7: "\033[97m", # White
            }
            reset = "\033[0m"
            print(f"{color_codes.get(color_code, '')}\033[{y};{x}H{text}{reset}")
    
    def draw_box(self, y, x, height, width, color=Colors.CYAN):
        # Pastikan kotak muat di layar
        if y < 0 or x < 0 or y + height > self.max_y or x + width > self.max_x:
            return
            
        # Gambar border atas
        self.draw_text(y, x, "╔" + "═" * (width - 2) + "╗", color)
        # Gambar sisi
        for i in range(1, height - 1):
            self.draw_text(y + i, x, "║", color)
            self.draw_text(y + i, x + width - 1, "║", color)
        # Gambar border bawah
        self.draw_text(y + height - 1, x, "╚" + "═" * (width - 2) + "╝", color)
    
    def refresh_screen(self):
        if HAS_CURSES:
            self.screen.refresh()
        else:
            sys.stdout.flush()
    
    def show_ascii_art(self):
        # ASCII art yang responsif
        if self.max_x >= 50:
            ascii_art = [
                "╔══════════════════════════════════╗",
                "║         🐍 SNAKE GAME 🐍        ║",
                "║         PYTHON EDITION           ║",
                "╚══════════════════════════════════╝",
            ]
        else:
            ascii_art = [
            "███████╗███╗   ██╗ █████╗ ██╗  ██╗███████╗",
            "██╔════╝████╗  ██║██╔══██╗██║ ██╔╝██╔════╝",
            "███████╗██╔██╗ ██║███████║█████╔╝ █████╗  ",
            "╚════██║██║╚██╗██║██╔══██║██╔═██╗ ██╔══╝  ",
            "███████║██║ ╚████║██║  ██║██║  ██╗███████╗",
            "╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝",
            ]
        
        for i, line in enumerate(ascii_art):
            self.draw_text(2 + i, 0, line, Colors.GREEN, centered=True)
    
    def show_menu(self):
        self.clear_screen()
        if HAS_CURSES:
            self.screen.clear()
        
        self.show_ascii_art()
        
        # Menu yang responsif berdasarkan ukuran layar
        if self.max_x >= 50:
            box_width = min(40, self.max_x - 4)
            menu_items = [
                ("1. 🎮 SINGLE PLAYER", Colors.GREEN),
                ("2. 👥 MULTI PLAYER", Colors.BLUE), 
                ("3. ⚙️ SETTINGS", Colors.YELLOW),
                ("4. 🏆 HIGH SCORES", Colors.CYAN),
                ("5. 🚪 EXIT GAME", Colors.RED)
            ]
        else:
            box_width = min(30, self.max_x - 4)
            menu_items = [
                ("1. SINGLE PLAYER", Colors.GREEN),
                ("2. MULTI PLAYER", Colors.BLUE), 
                ("3. SETTINGS", Colors.YELLOW),
                ("4. HIGH SCORES", Colors.CYAN),
                ("5. EXIT", Colors.RED)
            ]
        
        box_height = len(menu_items) + 4
        box_x = max(0, self.max_x // 2 - box_width // 2)
        box_y = 8
        
        self.draw_box(box_y, box_x, box_height, box_width, Colors.CYAN)
        
        menu_title = "MAIN MENU"
        self.draw_text(box_y + 1, 0, menu_title, Colors.MAGENTA, centered=True)
        
        for i, (item, color) in enumerate(menu_items):
            self.draw_text(box_y + 3 + i, 0, item, color, centered=True)
        
        # Info kontrol yang responsif
        if self.max_y >= box_y + box_height + 10:
            info_box_y = box_y + box_height + 1
            info_box_width = min(50, self.max_x - 4)
            info_box_x = max(0, self.max_x // 2 - info_box_width // 2)
            
            self.draw_box(info_box_y, info_box_x, 7, info_box_width, Colors.YELLOW)
            self.draw_text(info_box_y + 1, 0, "CONTROLS", Colors.WHITE, centered=True)
            
            if self.max_x >= 50:
                instructions = [
                    "Single: WASD to move",
                    "Multi: P1(WASD) P2(Arrow Keys)",
                    "Pause: P, Quit: Q, Menu: M",
                    f"Screen: {self.max_x}x{self.max_y}"
                ]
            else:
                instructions = [
                    "Single: WASD",
                    "Multi: P1(WASD) P2(Arrows)",
                    "Pause: P, Quit: Q",
                    f"Size: {self.max_x}x{self.max_y}"
                ]
            
            for i, instruction in enumerate(instructions):
                self.draw_text(info_box_y + 3 + i, 0, instruction, Colors.WHITE, centered=True)
        
        self.draw_text(box_y + box_height - 1, 0, "Select option (1-5): ", Colors.CYAN, centered=True)
        self.refresh_screen()
        
        while True:
            key = self.get_input()
            if key == ord('1'):
                self.is_multiplayer = False
                return GameState.PLAYING
            elif key == ord('2'):
                self.is_multiplayer = True
                return GameState.PLAYING
            elif key == ord('3'):
                return GameState.SETTINGS
            elif key == ord('4'):
                return GameState.HIGH_SCORES
            elif key == ord('5'):
                sys.exit(0)
            elif key == ord('q') or key == ord('Q'):
                sys.exit(0)
    
    def show_settings(self):
        self.clear_screen()
        self.draw_text(5, 0, "⚙️ GAME SETTINGS", Colors.MAGENTA, centered=True)
        
        # Settings menu yang responsif
        if self.max_x >= 50:
            box_width = min(50, self.max_x - 4)
            settings_items = [
                ("1. CHANGE SNAKE CHARACTER", Colors.GREEN),
                ("2. SELECT LEVEL", Colors.BLUE), 
                ("3. DIFFICULTY SETTINGS", Colors.YELLOW),
                ("4. TOGGLE SOUND", Colors.CYAN),
                ("5. BACK TO MAIN MENU", Colors.RED)
            ]
        else:
            box_width = min(35, self.max_x - 4)
            settings_items = [
                ("1. CHANGE CHARACTER", Colors.GREEN),
                ("2. SELECT LEVEL", Colors.BLUE), 
                ("3. DIFFICULTY", Colors.YELLOW),
                ("4. TOGGLE SOUND", Colors.CYAN),
                ("5. BACK TO MENU", Colors.RED)
            ]
        
        box_height = len(settings_items) + 4
        box_x = max(0, self.max_x // 2 - box_width // 2)
        box_y = 7
        
        self.draw_box(box_y, box_x, box_height, box_width, Colors.BLUE)
        
        for i, (item, color) in enumerate(settings_items):
            self.draw_text(box_y + 2 + i, 0, item, color, centered=True)
        
        # Tampilkan pengaturan saat ini
        status_y = box_y + box_height + 1
        self.draw_text(status_y, 0, f"Current: Char={self.snake_char}, Level={self.level}", Colors.WHITE, centered=True)
        self.draw_text(status_y + 1, 0, f"Difficulty: {self.difficulty}, Sound: {'ON' if self.sound_enabled else 'OFF'}", Colors.WHITE, centered=True)
        
        self.draw_text(status_y + 3, 0, "Select option (1-5): ", Colors.CYAN, centered=True)
        self.refresh_screen()
        
        while True:
            key = self.get_input()
            if key == ord('1'):
                self.change_character()
                return GameState.SETTINGS
            elif key == ord('2'):
                self.level_select()
                return GameState.SETTINGS
            elif key == ord('3'):
                self.difficulty_settings()
                return GameState.SETTINGS
            elif key == ord('4'):
                self.sound_enabled = not self.sound_enabled
                return GameState.SETTINGS
            elif key == ord('5'):
                return GameState.MENU
            elif key == ord('q') or key == ord('Q'):
                return GameState.MENU
    
    def change_character(self):
        self.clear_screen()
        self.draw_text(5, 0, "🎨 SELECT SNAKE CHARACTER", Colors.MAGENTA, centered=True)
        
        # Karakter yang responsif
        if self.max_x >= 50:
            box_width = min(40, self.max_x - 4)
            characters = [
                ("1. ■ (Default Square)", Colors.GREEN),
                ("2. □ (Hollow Square)", Colors.BLUE), 
                ("3. ○ (Circle)", Colors.CYAN),
                ("4. ● (Solid Circle)", Colors.MAGENTA),
                ("5. ▲ (Triangle)", Colors.RED),
                ("6. ♦ (Diamond)", Colors.YELLOW)
            ]
        else:
            box_width = min(30, self.max_x - 4)
            characters = [
                ("1. ■ Square", Colors.GREEN),
                ("2. □ Hollow", Colors.BLUE), 
                ("3. ○ Circle", Colors.CYAN),
                ("4. ● Solid", Colors.MAGENTA),
                ("5. ▲ Triangle", Colors.RED),
                ("6. ♦ Diamond", Colors.YELLOW)
            ]
        
        box_height = len(characters) + 3
        box_x = max(0, self.max_x // 2 - box_width // 2)
        box_y = 7
        
        self.draw_box(box_y, box_x, box_height, box_width, Colors.YELLOW)
        
        for i, (char, color) in enumerate(characters):
            self.draw_text(box_y + 2 + i, 0, char, color, centered=True)
        
        self.draw_text(box_y + box_height - 1, 0, "Select character (1-6) or Q to cancel: ", Colors.CYAN, centered=True)
        self.refresh_screen()
        
        while True:
            key = self.get_input()
            chars = ['■', '□', '○', '●', '▲', '♦']
            if ord('1') <= key <= ord('6'):
                self.snake_char = chars[key - ord('1')]
                break
            elif key == ord('q') or key == ord('Q'):
                break
    
    def difficulty_settings(self):
        self.clear_screen()
        self.draw_text(5, 0, "🎯 DIFFICULTY SETTINGS", Colors.MAGENTA, centered=True)
        
        box_width = min(40, self.max_x - 4)
        box_height = 8
        box_x = max(0, self.max_x // 2 - box_width // 2)
        box_y = 7
        
        self.draw_box(box_y, box_x, box_height, box_width, Colors.RED)
        
        difficulties = [
            ("1. EASY - Slow speed, few obstacles", Colors.GREEN),
            ("2. NORMAL - Balanced gameplay", Colors.YELLOW), 
            ("3. HARD - Fast speed, many obstacles", Colors.RED),
            ("4. EXPERT - Very fast, complex maze", Colors.MAGENTA)
        ]
        
        for i, (desc, color) in enumerate(difficulties):
            self.draw_text(box_y + 2 + i, 0, desc, color, centered=True)
        
        self.draw_text(box_y + 6, 0, f"Current: {self.difficulty}", Colors.WHITE, centered=True)
        self.draw_text(box_y + 7, 0, "Select difficulty (1-4): ", Colors.CYAN, centered=True)
        self.refresh_screen()
        
        while True:
            key = self.get_input()
            if key == ord('1'):
                self.difficulty = "EASY"
                self.game_speed = 0.2
                break
            elif key == ord('2'):
                self.difficulty = "NORMAL"
                self.game_speed = 0.15
                break
            elif key == ord('3'):
                self.difficulty = "HARD"
                self.game_speed = 0.1
                break
            elif key == ord('4'):
                self.difficulty = "EXPERT"
                self.game_speed = 0.05
                break
            elif key == ord('q') or key == ord('Q'):
                break
    
    def level_select(self):
        self.clear_screen()
        self.draw_text(5, 0, "📊 SELECT LEVEL", Colors.MAGENTA, centered=True)
        
        box_width = min(50, self.max_x - 4)
        box_height = 10
        box_x = max(0, self.max_x // 2 - box_width // 2)
        box_y = 7
        
        self.draw_box(box_y, box_x, box_height, box_width, Colors.BLUE)
        
        level_descriptions = [
            ("Level 1: Beginner - Simple borders", Colors.GREEN),
            ("Level 2: Easy - Cross pattern", Colors.CYAN), 
            ("Level 3: Medium - Horizontal bars", Colors.YELLOW),
            ("Level 4: Hard - Vertical maze", Colors.MAGENTA),
            ("Level 5: Expert - Complex grid", Colors.RED)
        ]
        
        for i, (desc, color) in enumerate(level_descriptions):
            self.draw_text(box_y + 2 + i, 0, desc, color, centered=True)
        
        self.draw_text(box_y + 8, 0, f"Current Level: {self.level}", Colors.WHITE, centered=True)
        self.draw_text(box_y + 9, 0, "Select level (1-5): ", Colors.CYAN, centered=True)
        self.refresh_screen()
        
        while True:
            key = self.get_input()
            if ord('1') <= key <= ord('5'):
                self.level = key - ord('0')
                break
            elif key == ord('q') or key == ord('Q'):
                break
    
    def show_high_scores(self):
        self.clear_screen()
        self.draw_text(5, 0, "🏆 HIGH SCORES", Colors.MAGENTA, centered=True)
        
        # Generate some sample high scores if empty
        if not self.high_scores:
            self.high_scores = [
                {"name": "CHAMP", "score": 1000, "level": 5},
                {"name": "PRO", "score": 800, "level": 4},
                {"name": "PLAYER", "score": 600, "level": 3},
                {"name": "BEGINNER", "score": 400, "level": 2},
                {"name": "NEWBIE", "score": 200, "level": 1},
            ]
        
        box_width = min(50, self.max_x - 4)
        box_height = len(self.high_scores) + 4
        box_x = max(0, self.max_x // 2 - box_width // 2)
        box_y = 7
        
        self.draw_box(box_y, box_x, box_height, box_width, Colors.YELLOW)
        
        # Header
        if self.max_x >= 50:
            self.draw_text(box_y + 1, 0, "RANK  NAME       SCORE  LEVEL", Colors.WHITE, centered=True)
        else:
            self.draw_text(box_y + 1, 0, "RANK NAME  SCORE LEVEL", Colors.WHITE, centered=True)
        
        # Scores
        for i, score_data in enumerate(self.high_scores):
            if self.max_x >= 50:
                score_text = f"{i+1:2d}.   {score_data['name']:<8}  {score_data['score']:5d}  {score_data['level']}"
            else:
                score_text = f"{i+1}. {score_data['name']} {score_data['score']} {score_data['level']}"
            
            color = Colors.GREEN if i == 0 else Colors.CYAN if i < 3 else Colors.WHITE
            self.draw_text(box_y + 3 + i, 0, score_text, color, centered=True)
        
        self.draw_text(box_y + box_height - 1, 0, "Press any key to return to menu", Colors.CYAN, centered=True)
        self.refresh_screen()
        
        # Wait for any key
        while self.get_input() == -1:
            time.sleep(0.1)
        
        return GameState.MENU
    
    def generate_obstacles(self, level):
        obstacles = []
        playable_height = self.game_area_bottom - self.game_area_top - 1
        playable_width = self.game_area_right - self.game_area_left - 1
        
        # Selalu tambahkan border dasar
        for i in range(self.game_area_left, self.game_area_right + 1):
            obstacles.append((self.game_area_top, i))
            obstacles.append((self.game_area_bottom, i))
        for i in range(self.game_area_top + 1, self.game_area_bottom):
            obstacles.append((i, self.game_area_left))
            obstacles.append((i, self.game_area_right))
        
        # LEVEL 1: Border sederhana saja
        if level == 1:
            pass  # Hanya border
        
        # LEVEL 2: Salib di tengah
        elif level == 2:
            center_y = (self.game_area_top + self.game_area_bottom) // 2
            center_x = (self.game_area_left + self.game_area_right) // 2
            
            # Garis horizontal dengan celah
            for i in range(self.game_area_left + 5, center_x - 2):
                obstacles.append((center_y, i))
            for i in range(center_x + 3, self.game_area_right - 4):
                obstacles.append((center_y, i))
            
            # Garis vertikal dengan celah
            for i in range(self.game_area_top + 5, center_y - 2):
                obstacles.append((i, center_x))
            for i in range(center_y + 3, self.game_area_bottom - 4):
                obstacles.append((i, center_x))
        
        # LEVEL 3: Batang horizontal
        elif level == 3:
            bar_y1 = self.game_area_top + playable_height // 4
            bar_y2 = self.game_area_top + 3 * playable_height // 4
            
            for i in range(self.game_area_left + 1, self.game_area_right):
                if i % 6 != 0:  # Celah lebih sering
                    if bar_y1 < self.game_area_bottom:
                        obstacles.append((bar_y1, i))
                    if bar_y2 < self.game_area_bottom:
                        obstacles.append((bar_y2, i))
        
        # LEVEL 4: Maze vertikal
        elif level == 4:
            col1 = self.game_area_left + playable_width // 4
            col2 = self.game_area_left + 2 * playable_width // 4
            col3 = self.game_area_left + 3 * playable_width // 4
            
            for i in range(self.game_area_top + 1, self.game_area_bottom):
                if i % 5 != 0:  # Celah lebih sering
                    if col1 < self.game_area_right:
                        obstacles.append((i, col1))
                    if col2 < self.game_area_right:
                        obstacles.append((i, col2))
                    if col3 < self.game_area_right:
                        obstacles.append((i, col3))
        
        # LEVEL 5: Grid kompleks
        elif level >= 5:
            # Grid internal yang lebih kompleks
            for i in range(self.game_area_top + 3, self.game_area_bottom - 2, 2):
                for j in range(self.game_area_left + 3, self.game_area_right - 2, 3):
                    if (i + j) % 4 != 0:  # Pola yang lebih menantang
                        obstacles.append((i, j))
            
            # Tambahkan beberapa blok di tengah
            mid_y = (self.game_area_top + self.game_area_bottom) // 2
            mid_x = (self.game_area_left + self.game_area_right) // 2
            
            for i in range(mid_y - 2, mid_y + 3):
                for j in range(mid_x - 3, mid_x + 4):
                    if (i != mid_y or j != mid_x) and (i, j) not in obstacles:
                        obstacles.append((i, j))
        
        # Tambahkan obstacle berdasarkan difficulty
        if self.difficulty == "HARD" and level > 1:
            extra_obstacles = min(10, playable_width * playable_height // 20)
            for _ in range(extra_obstacles):
                obs = [
                    random.randint(self.game_area_top + 1, self.game_area_bottom - 1),
                    random.randint(self.game_area_left + 1, self.game_area_right - 1)
                ]
                if obs not in obstacles:
                    obstacles.append(obs)
        
        elif self.difficulty == "EXPERT" and level > 1:
            extra_obstacles = min(20, playable_width * playable_height // 15)
            for _ in range(extra_obstacles):
                obs = [
                    random.randint(self.game_area_top + 1, self.game_area_bottom - 1),
                    random.randint(self.game_area_left + 1, self.game_area_right - 1)
                ]
                if obs not in obstacles:
                    obstacles.append(obs)
        
        return obstacles
    
    def draw_border(self):
        # Gambar border area bermain dengan warna yang berbeda
        border_color = Colors.CYAN if self.level < 3 else Colors.YELLOW if self.level < 5 else Colors.RED
        
        for i in range(self.game_area_left, self.game_area_right + 1):
            self.draw_text(self.game_area_top, i, '═', border_color)
            self.draw_text(self.game_area_bottom, i, '═', border_color)
        
        for i in range(self.game_area_top + 1, self.game_area_bottom):
            self.draw_text(i, self.game_area_left, '║', border_color)
            self.draw_text(i, self.game_area_right, '║', border_color)
        
        # Gambar sudut
        self.draw_text(self.game_area_top, self.game_area_left, '╔', border_color)
        self.draw_text(self.game_area_top, self.game_area_right, '╗', border_color)
        self.draw_text(self.game_area_bottom, self.game_area_left, '╚', border_color)
        self.draw_text(self.game_area_bottom, self.game_area_right, '╝', border_color)
    
    def check_collision(self, head, snake, other_snake, obstacles):
        """Periksa semua jenis tabrakan dengan perbaikan"""
        # Tabrakan dengan border (diperbaiki)
        if (head[0] <= self.game_area_top or 
            head[0] >= self.game_area_bottom or 
            head[1] <= self.game_area_left or 
            head[1] >= self.game_area_right):
            return True
        
        # Tabrakan dengan tubuh sendiri (diperbaiki)
        if head in snake[1:]:  # Skip kepala
            return True
        
        # Tabrakan dengan ular lain (multiplayer)
        if other_snake and head in other_snake:
            return True
        
        # Tabrakan dengan rintangan (diperbaiki)
        if head in obstacles:
            return True
        
        return False
    
    def game_loop(self):
        # Inisialisasi ular 1
        start_y = (self.game_area_top + self.game_area_bottom) // 2
        start_x1 = self.game_area_left + (self.game_area_right - self.game_area_left) // 4
        
        snake1 = [
            [start_y, start_x1],
            [start_y, start_x1 - 1],
            [start_y, start_x1 - 2]
        ]
        direction1 = Direction.RIGHT
        
        # Inisialisasi ular 2 untuk multiplayer
        snake2 = []
        direction2 = Direction.LEFT
        if self.is_multiplayer:
            start_x2 = self.game_area_left + 3 * (self.game_area_right - self.game_area_left) // 4
            snake2 = [
                [start_y, start_x2],
                [start_y, start_x2 + 1],
                [start_y, start_x2 + 2]
            ]
        
        # Generate makanan dan rintangan
        obstacles = self.generate_obstacles(self.level)
        food = self.generate_food(snake1 + snake2, obstacles)
        
        score = 0
        food_count = 0
        required_food = 3 + self.level
        
        paused = False
        
        while True:
            if HAS_CURSES:
                self.screen.clear()
            else:
                self.clear_screen()
            
            self.draw_border()
            
            # Gambar rintangan dengan warna berdasarkan level
            obstacle_color = Colors.RED if self.level >= 4 else Colors.MAGENTA
            for obs in obstacles:
                if (self.game_area_top < obs[0] < self.game_area_bottom and 
                    self.game_area_left < obs[1] < self.game_area_right):
                    self.draw_text(obs[0], obs[1], self.obstacle_char, obstacle_color)
            
            # Gambar makanan dengan efek berkedip
            if not paused:
                food_color = Colors.YELLOW if int(time.time() * 5) % 2 == 0 else Colors.MAGENTA
                self.draw_text(food[0], food[1], self.food_char, food_color)
            
            # Gambar ular 1
            for i, segment in enumerate(snake1):
                if (self.game_area_top < segment[0] < self.game_area_bottom and 
                    self.game_area_left < segment[1] < self.game_area_right):
                    color = Colors.GREEN if i == 0 else Colors.CYAN
                    self.draw_text(segment[0], segment[1], self.snake_char, color)
            
            # Gambar ular 2 untuk multiplayer
            if self.is_multiplayer:
                for i, segment in enumerate(snake2):
                    if (self.game_area_top < segment[0] < self.game_area_bottom and 
                        self.game_area_left < segment[1] < self.game_area_right):
                        color = Colors.BLUE if i == 0 else Colors.MAGENTA
                        self.draw_text(segment[0], segment[1], self.snake2_char, color)
            
            # Gambar UI informatif
            ui_elements = []
            
            # Baris 1: Informasi dasar
            ui_elements.append(f"Level: {self.level} | Score: {score} | Food: {food_count}/{required_food}")
            
            # Baris 2: Informasi tambahan
            mode_text = "Mode: Multiplayer" if self.is_multiplayer else "Mode: Single Player"
            difficulty_text = f"Difficulty: {self.difficulty}"
            ui_elements.append(f"{mode_text} | {difficulty_text}")
            
            for i, element in enumerate(ui_elements):
                self.draw_text(1 + i, 0, element, Colors.YELLOW, centered=True)
            
            # Kontrol yang responsif
            if self.max_x >= 50:
                if self.is_multiplayer:
                    controls = "P1: WASD | P2: Arrows | P: Pause | Q: Quit | M: Menu"
                else:
                    controls = "WASD to move | P: Pause | Q: Quit | M: Menu"
            else:
                if self.is_multiplayer:
                    controls = "P1:WASD P2:Arrows P:Pause Q:Quit"
                else:
                    controls = "WASD move P:Pause Q:Quit M:Menu"
            
            self.draw_text(self.max_y - 2, 0, controls, Colors.CYAN, centered=True)
            
            # Tampilkan pesan pause
            if paused:
                pause_text = "⏸️ GAME PAUSED - Press P to resume"
                self.draw_text(self.max_y // 2, 0, pause_text, Colors.MAGENTA, centered=True)
            
            self.refresh_screen()
            
            # Handle input
            key = self.get_input()
            
            # Tombol pause
            if key == ord('p') or key == ord('P'):
                paused = not paused
            
            if paused:
                time.sleep(0.1)
                continue
            
            # Handle kontrol ular 1 (WASD)
            if key == ord('w') and direction1 != Direction.DOWN:
                direction1 = Direction.UP
            elif key == ord('s') and direction1 != Direction.UP:
                direction1 = Direction.DOWN
            elif key == ord('a') and direction1 != Direction.RIGHT:
                direction1 = Direction.LEFT
            elif key == ord('d') and direction1 != Direction.LEFT:
                direction1 = Direction.RIGHT
            
            # Handle kontrol ular 2 (Arrow keys) untuk multiplayer
            if self.is_multiplayer:
                if key in [curses.KEY_UP if HAS_CURSES else 72, ord('i'), ord('I')]:
                    if direction2 != Direction.DOWN:
                        direction2 = Direction.UP
                elif key in [curses.KEY_DOWN if HAS_CURSES else 80, ord('k'), ord('K')]:
                    if direction2 != Direction.UP:
                        direction2 = Direction.DOWN
                elif key in [curses.KEY_LEFT if HAS_CURSES else 75, ord('j'), ord('J')]:
                    if direction2 != Direction.RIGHT:
                        direction2 = Direction.LEFT
                elif key in [curses.KEY_RIGHT if HAS_CURSES else 77, ord('l'), ord('L')]:
                    if direction2 != Direction.LEFT:
                        direction2 = Direction.RIGHT
            
            # Gerakkan ular 1
            head1 = snake1[0].copy()
            if direction1 == Direction.UP:
                head1[0] -= 1
            elif direction1 == Direction.DOWN:
                head1[0] += 1
            elif direction1 == Direction.LEFT:
                head1[1] -= 1
            elif direction1 == Direction.RIGHT:
                head1[1] += 1
            
            # Gerakkan ular 2 untuk multiplayer
            head2 = []
            if self.is_multiplayer:
                head2 = snake2[0].copy()
                if direction2 == Direction.UP:
                    head2[0] -= 1
                elif direction2 == Direction.DOWN:
                    head2[0] += 1
                elif direction2 == Direction.LEFT:
                    head2[1] -= 1
                elif direction2 == Direction.RIGHT:
                    head2[1] += 1
            
            # Periksa tabrakan untuk ular 1
            if self.check_collision(head1, snake1, snake2 if self.is_multiplayer else [], obstacles):
                self.score = score
                if score > self.high_score:
                    self.high_score = score
                return GameState.GAME_OVER
            
            # Periksa tabrakan untuk ular 2
            if self.is_multiplayer and self.check_collision(head2, snake2, snake1, obstacles):
                self.score = score
                if score > self.high_score:
                    self.high_score = score
                return GameState.GAME_OVER
            
            # Periksa tabrakan makanan untuk ular 1
            if head1 == food:
                score += 10 * self.level
                food_count += 1
                food = self.generate_food(snake1 + (snake2 if self.is_multiplayer else []), obstacles)
                # Ular tumbuh
                snake1.insert(0, head1)
            else:
                # Gerakkan ular normal
                snake1.insert(0, head1)
                if len(snake1) > 3:  # Pertahankan panjang minimum
                    snake1.pop()
            
            # Periksa tabrakan makanan untuk ular 2
            if self.is_multiplayer:
                if head2 == food:
                    score += 10 * self.level
                    food_count += 1
                    food = self.generate_food(snake1 + snake2, obstacles)
                    # Ular tumbuh
                    snake2.insert(0, head2)
                else:
                    # Gerakkan ular normal
                    snake2.insert(0, head2)
                    if len(snake2) > 3:  # Pertahankan panjang minimum
                        snake2.pop()
            else:
                # Untuk single player, pastikan snake2 kosong
                snake2 = []
            
            # Periksa penyelesaian level
            if food_count >= required_food:
                self.score = score
                if score > self.high_score:
                    self.high_score = score
                return GameState.LEVEL_COMPLETE
            
            # Keluar dari game atau kembali ke menu
            if key == ord('q') or key == ord('Q'):
                return GameState.MENU
            elif key == ord('m') or key == ord('M'):
                return GameState.MENU
            
            # Kecepatan game berdasarkan difficulty
            time.sleep(self.game_speed)
    
    def generate_food(self, snake, obstacles):
        max_attempts = 100
        for _ in range(max_attempts):
            food = [
                random.randint(self.game_area_top + 1, self.game_area_bottom - 1), 
                random.randint(self.game_area_left + 1, self.game_area_right - 1)
            ]
            if food not in snake and food not in obstacles:
                return food
        # Fallback position
        return [(self.game_area_top + self.game_area_bottom) // 2, 
                (self.game_area_left + self.game_area_right) // 2]
    
    def show_game_over(self):
        self.clear_screen()
        
        # Game Over yang responsif
        if self.max_x >= 50:
            game_over_art = [
                "╔══════════════════════════════╗",
                "║         GAME OVER!           ║",
                "║    Better luck next time!    ║",
                "╚══════════════════════════════╝",
            ]
        else:
            game_over_art = [
            "  ██████╗  █████╗ ███╗   ███╗███████╗     ██████╗ ██╗   ██╗███████╗██████╗ ",
            " ██╔════╝ ██╔══██╗████╗ ████║██╔════╝    ██╔═══██╗██║   ██║██╔════╝██╔══██╗",
            " ██║  ███╗███████║██╔████╔██║█████╗      ██║   ██║██║   ██║█████╗  ██████╔╝",
            " ██║   ██║██╔══██║██║╚██╔╝██║██╔══╝      ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗",
            " ╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗    ╚██████╔╝ ╚████╔╝ ███████╗██║  ██║",
            "  ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝     ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝"
            ]
        
        for i, line in enumerate(game_over_art):
            self.draw_text(5 + i, 0, line, Colors.RED, centered=True)
        
        # Detail game over
        details_y = 10
        details_width = min(40, self.max_x - 4)
        details_x = max(0, self.max_x // 2 - details_width // 2)
        
        self.draw_box(details_y, details_x, 7, details_width, Colors.YELLOW)
        
        score_text = f"Final Score: {self.score}"
        level_text = f"Level Reached: {self.level}"
        high_score_text = f"High Score: {self.high_score}"
        mode_text = f"Mode: {'Multiplayer' if self.is_multiplayer else 'Single Player'}"
        
        self.draw_text(details_y + 1, 0, "RESULTS", Colors.WHITE, centered=True)
        self.draw_text(details_y + 2, 0, score_text, Colors.GREEN, centered=True)
        self.draw_text(details_y + 3, 0, level_text, Colors.CYAN, centered=True)
        self.draw_text(details_y + 4, 0, high_score_text, Colors.MAGENTA, centered=True)
        self.draw_text(details_y + 5, 0, mode_text, Colors.BLUE, centered=True)
        
        continue_text = "Press 'R' to Restart, 'M' for Menu, or 'Q' to Quit"
        self.draw_text(details_y + 8, 0, continue_text, Colors.CYAN, centered=True)
        
        self.refresh_screen()
        
        while True:
            key = self.get_input()
            if key == ord('r') or key == ord('R'):
                self.level = 1
                return GameState.PLAYING
            elif key == ord('m') or key == ord('M'):
                return GameState.MENU
            elif key == ord('q') or key == ord('Q'):
                sys.exit(0)
    
    def show_level_complete(self):
        self.clear_screen()
        
        # Level Complete yang responsif
        if self.max_x >= 50:
            complete_art = [
                "╔══════════════════════════════╗",
                "║        LEVEL COMPLETE!      ║",
                "║        Congratulations!     ║",
                "║             🎉🎉🎉         ║",
                "╚══════════════════════════════╝",
            ]
        else:
            complete_art = [
                "╔══════════════════╗",
                "║ LEVEL COMPLETE!  ║",
                "║  Congratulations!║",
                "║      🎉🎉       ║",
                "╚══════════════════╝",
            ]
        
        for i, line in enumerate(complete_art):
            self.draw_text(5 + i, 0, line, Colors.GREEN, centered=True)
        
        # Detail penyelesaian level
        details_y = 10
        details_width = min(40, self.max_x - 4)
        details_x = max(0, self.max_x // 2 - details_width // 2)
        
        self.draw_box(details_y, details_x, 7, details_width, Colors.CYAN)
        
        level_text = f"Level {self.level} Completed!"
        score_text = f"Score: {self.score}"
        next_level = f"Next Level: {self.level + 1}"
        high_score_text = f"High Score: {self.high_score}"
        
        self.draw_text(details_y + 1, 0, level_text, Colors.YELLOW, centered=True)
        self.draw_text(details_y + 2, 0, score_text, Colors.GREEN, centered=True)
        self.draw_text(details_y + 3, 0, next_level, Colors.MAGENTA, centered=True)
        self.draw_text(details_y + 4, 0, high_score_text, Colors.BLUE, centered=True)
        
        options_text = "Press 'N' for Next Level, 'M' for Menu, or 'Q' to Quit"
        self.draw_text(details_y + 7, 0, options_text, Colors.CYAN, centered=True)
        
        self.refresh_screen()
        
        while True:
            key = self.get_input()
            if key == ord('n') or key == ord('N'):
                self.level += 1
                return GameState.PLAYING
            elif key == ord('m') or key == ord('M'):
                return GameState.MENU
            elif key == ord('q') or key == ord('Q'):
                sys.exit(0)
    
    def run(self):
        try:
            self.init_screen()
            
            while True:
                if self.game_state == GameState.MENU:
                    self.game_state = self.show_menu()
                    self.score = 0
                    # Reset level ke 1 saat memulai game baru dari menu
                    if self.game_state == GameState.PLAYING:
                        self.level = 1
                
                elif self.game_state == GameState.PLAYING:
                    result = self.game_loop()
                    
                    if result == GameState.GAME_OVER:
                        self.game_state = GameState.GAME_OVER
                    elif result == GameState.LEVEL_COMPLETE:
                        self.game_state = self.show_level_complete()
                    elif result == GameState.MENU:
                        self.game_state = GameState.MENU
                
                elif self.game_state == GameState.GAME_OVER:
                    self.game_state = self.show_game_over()
                
                elif self.game_state == GameState.SETTINGS:
                    self.game_state = self.show_settings()
                
                elif self.game_state == GameState.HIGH_SCORES:
                    self.game_state = self.show_high_scores()
                
        except KeyboardInterrupt:
            print("\nGame interrupted! Thanks for playing! 🐍")
        except Exception as e:
            print(f"\nAn error occurred: {e}")
        finally:
            self.cleanup_screen()

if __name__ == "__main__":
    print("Starting Snake Game...")
    if not HAS_CURSES:
        print("Note: Running in fallback mode (curses not available)")
        print("For multiplayer, use IJKL for Player 2")
    
    game = SnakeGame()
    game.run()