import pygame, sys

pygame.init()
pygame.display.set_caption("Scrappy Scrabble")
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
width, height = screen.get_width(), screen.get_height()

# some constants for readability
DEFAULT_CELL_COLOR = (0, 100, 50)
TRIPLE_WORD_COLOR = (255, 40, 30)
DOUBLE_WORD_COLOR = (250, 200, 50)
TRIPLE_LETTER_COLOR = (50, 150, 250)
DOUBLE_LETTER_COLOR = (180, 210, 250)
EMPTY_COLOR = (0, 145, 55)
TILE_COLOR = (220, 225, 205)
TILE_SHADOW = (40, 50, 70)
CELL_SIZE = min(height, width) / 16
TILE_SIZE = CELL_SIZE * 0.8
FONT = pygame.font.SysFont('Arial Black', int(TILE_SIZE * 0.9), False, False)

# game classes
class Scrabble:
    def __init__(self):
        # dicts are usefull for debugging and make implementing new features easier on the long term
        self.letters = {}
        # but here a list is sufficient since we wont mutate the dictionary and 'in' is faster on lists
        self.dictionary = []
        self.board = Board()
        self.player0 = Player()
        self.player1 = Player()
        self.active_player = self.player0
        self.turn = 0

        with open('lettres.txt', 'r', encoding='utf-8') as file:
            text = file.read()
            # read lines one by one
            for line in text.splitlines():
                # remove semi-colons, remove double spaces, and split in three constants
                letter, value, amount = line.replace(";", "").replace("  ", " ").split(" ")[:3]
                self.letters[letter.lower()] = {"value": int(value), "amount": int(amount)}

        with open('littre.txt', 'r', encoding='utf-8') as file:
            text = file.read()
            # read lines one by one, this time each line is a valid word
            for entry in text.splitlines():
                self.dictionary.append(entry.lower())
        # print(self.letters)
        # print(self.dictionary[:10])

    def __copy__(self):
        dup = Scrabble()
        dup.board = Board()
        dup.board.map = self.board.map.copy()
        dup.letters = self.letters.copy()
        dup.active_player = self.active_player
        dup.player0 = self.player0
        dup.player1 = self.player1
        return dup

    def draw(self):
        screen.fill((0, 0, 0))
        text = FONT.render("Player: " + str(1 + self.turn), True, (255, 255, 255))
        screen.blit(text, (CELL_SIZE, CELL_SIZE))
        score = FONT.render(str(self.active_player.score) + " points", True, (255, 255, 255))
        screen.blit(score, (CELL_SIZE, CELL_SIZE * 2))
        text = FONT.render("Player: " + str(2 - self.turn), True, (100, 150, 120))
        screen.blit(text, (CELL_SIZE, CELL_SIZE * 3))
        score = FONT.render(str(self.player0.score if self.turn == 1 else self.player1.score) + " points", True, (100, 120, 100))
        screen.blit(score, (CELL_SIZE, CELL_SIZE * 4))

        self.board.draw()
        self.active_player.draw()

    def draw_mouse_hoover(self, mouse_position, horizontal: bool):
        # outline the tile under the mouse
        mx, my = mouse_position
        # only if its over the board
        if width / 2 - CELL_SIZE * 7.5 < mx < width / 2 + CELL_SIZE * 7 and\
            height / 2 - CELL_SIZE * 7.5 < my < height / 2 + CELL_SIZE * 7:

            # position of the mouse in the context of the board (over which cell)
            off = (CELL_SIZE - TILE_SIZE) / 2
            rmx0, rmy0 = get_rel_mouse_pos(mouse_position)
            rmx = rmx0 * CELL_SIZE + width / 2 - CELL_SIZE * 7.5 + off
            rmy = rmy0 * CELL_SIZE + height / 2 - CELL_SIZE * 7.5 + off

            # draw a 7x1 horizontal
            if horizontal:
                # get the number of letters the rectangle will pass through so that it can extend
                add_space = 0
                for i in range(7):
                    p = (rmx0 + i, rmy0)
                    if p in self.board.map and self.board.map[p] != "":
                        add_space += 1

                pygame.draw.lines(screen, (0, 0, 0), True,
                                  ((rmx, rmy),
                                   (rmx + TILE_SIZE + (6 + add_space) * CELL_SIZE, rmy),
                                   (rmx + TILE_SIZE + (6 + add_space) * CELL_SIZE, rmy + TILE_SIZE),
                                   (rmx, rmy + TILE_SIZE)),
                                  width=int(TILE_SIZE * 0.3))
                for i, letter in enumerate(self.active_player.padded_word):
                    text = FONT.render(letter, True, (0, 0, 0))
                    screen.blit(text, (rmx + (i + 0.125) * CELL_SIZE, rmy - 0.1 * CELL_SIZE))

            # draw a 7x1 vertical
            else:
                # get the number of letters the rectangle will pass through so that it can extend
                add_space = 0
                for i in range(7):
                    p = (rmx0, rmy0 + i)
                    if p in self.board.map and self.board.map[p] != "":
                        add_space += 1

                pygame.draw.lines(screen, (0, 0, 0), True,
                                  ((rmx, rmy),
                                   (rmx + TILE_SIZE, rmy),
                                   (rmx + TILE_SIZE, rmy + TILE_SIZE + (6 + add_space) * CELL_SIZE),
                                   (rmx, rmy + TILE_SIZE + (6 + add_space) * CELL_SIZE)),
                                  width=int(TILE_SIZE * 0.3))
                for i, letter in enumerate(self.active_player.padded_word):
                    text = FONT.render(letter, True, (0, 0, 0))
                    screen.blit(text, (rmx + 0.125 * CELL_SIZE, rmy + i * CELL_SIZE - 0.125 * CELL_SIZE))


    def is_valid(self, word: str):
        # count the letters in the word
        letter_counts = {}
        for letter in word:
            if letter == " ":
                continue
            if letter not in letter_counts:
                letter_counts[letter] = 0
            # increase the occurences of that letter by one
            letter_counts[letter] += 1
            # if we find a letter with too many occurences we can return False early
            if letter_counts[letter] > self.letters[letter]["amount"]:
                return False
        return True

    def check_board(self):
        # set of unique coordinates of each non-empty character
        coords = set(pos for pos in self.board.map.keys() if self.board.map[pos] != "")

        if len(coords) == 0:
            # an empty board is valid
            return True
        if (7, 7) not in coords:
            # there must be a tile covering the center square if the board is not empty
            return False

        # make a duplicated of the coords, these are 'unseen' tiles
        temp = set(coords)
        # make a queue to walk from one end to the other until we see all the connected tiles
        queue = [temp.pop()]
        # for each element of the queue we start a walk
        for i, j in queue:
            # for each neighboring tile
            for e in (i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1):
                # if the neighbor is not empty we consider it seen and add it to the queue
                if e in temp:
                    temp.remove(e)
                    queue += [e]
        if len(temp) > 0:
            # there are still tiles on the board that we haven't seen,
            # not all tiles on the board are connected
            return False

        # checker
        def f(i, j, dy, dx):
            # 'True' instantly if we are not at the start of a word
            if (i - dy, j - dx) in coords:
                return True
            word = self.board.map[(i, j)]
            # parse the word in a straight line
            while (i + dy, j + dx) in coords:
                i += dy
                j += dx
                word += self.board.map[(i, j)]
            # either the 'word' is a single letter or it must be in the dictionary
            return len(word) <= 1 or word in self.dictionary

        # all words on the board of two or more letters must be in the dictionary
        return all(f(i, j, 1, 0) and f(i, j, 0, 1) for i, j in coords)


    def place(self, start_pos, horizontal):
        word = self.active_player.padded_word
        for i, letter in enumerate(word):
            if horizontal:
                self.board.map[start_pos[0] + i, start_pos[1]] = letter
            else:
                self.board.map[start_pos[0], start_pos[1] + i] = letter


    def play(self, start_pos, horizontal):
        # make a copy if we need to go back
        dup_map = self.board.map.copy()
        # check the validity and place a word
        word = self.active_player.word
        if self.is_valid(word):
            self.place(start_pos, horizontal)
            if not self.check_board():
                # board became invalid, rollback
                self.board.map = dup_map
            else:
                # add score to the player
                self.add_score(start_pos, horizontal)

                # remove all the letters that were placed
                to_delete = list(word)
                new_hand = ""
                for letter in self.active_player.hand:
                    if letter in to_delete:
                        to_delete.remove(letter)
                    else:
                        new_hand += letter
                self.active_player.hand = new_hand
                self.active_player.word = ""

                self.active_player.pick_letters(self.letters)

                # change turn and update player states
                if self.turn == 0:
                    self.turn = 1
                    self.active_player = self.player1
                else:
                    self.turn = 0
                    self.active_player = self.player0

    def add_score(self, start_pos, horizontal):
        word = self.active_player.padded_word
        n = len(word)
        score = 0
        times3 = False
        times2 = True
        for i in range(len(word)):
            letter_score = self.letters[word[i]]["value"]
            if horizontal:
                p = (start_pos[0] + i, start_pos[1])
            else:
                p = (start_pos[0], start_pos[1] + i)

            # get the bonus and consume it
            if p in self.board.triple_words:
                self.board.triple_words.remove(p)
                times3 = True
            elif p in self.board.double_words:
                self.board.double_words.remove(p)
                times2 = True
            elif p in self.board.triple_letters:
                self.board.triple_words.remove(p)
                letter_score *= 3
            elif p in self.board.double_letters:
                self.board.double_letters.remove(p)
                letter_score *= 2
            score += letter_score

        self.active_player.score += score * (2 if times2 else 1) * (3 if times3 else 1)
        print(str(self.active_player.score) + " for player " + str(self.turn))

    def count_already_placed_in_line(self, start_pos, horizontal):
        already_placed = 0
        for i in range(15):
            if horizontal:
                p = (start_pos[0] + i, start_pos[1])
            else:
                p = (start_pos[0], start_pos[1] + i)
            if p in self.board.map and self.board.map[p] != "":
                already_placed += 1
            elif i >= len(self.active_player.word):
                # return at first tile that is not placed after the word
                return already_placed
        return already_placed

    def update_word(self, start_pos, horizontal):
        word = ""
        wordi = 0
        already_placed = self.count_already_placed_in_line(start_pos, horizontal)
        for i in range(already_placed + len(self.active_player.word)):
            if horizontal:
                p = (start_pos[0] + i, start_pos[1])
            else:
                p = (start_pos[0], start_pos[1] + i)
            if p in self.board.map and self.board.map[p] != "":
                word += self.board.map[p]
            elif wordi < len(self.active_player.word):
                word += self.active_player.word[wordi]
                wordi += 1
        self.active_player.padded_word = word


class Board:
    def __init__(self):
        # 'map' maps a position to a letter for ease of board reading
        self.map = {}
        for x in range(15):
            for y in range(15):
                self.map[(x, y)] = ""
        # set special cells positions
        self.triple_words   = [(0, 0), (0, 7), (7, 0), (0, 14), (14, 0), (14, 14)]
        self.double_words   = [(1, 1), (2, 2), (3, 3), (4, 4), (7, 7),
                               (13, 1), (12, 2), (11, 3), (10, 4),
                               (1, 13), (2, 12), (3, 11), (4, 10),
                               (13, 13), (12, 12), (11, 11), (10, 10)]
        self.triple_letters = [(1, 5), (1, 9), (5, 5), (9, 5), (5, 9), (9, 9),
                               (5, 1), (9, 1), (13, 5), (13, 9), (5, 13), (9, 13)]
        self.double_letters = [(0, 3), (0, 11), (2, 6), (2, 8), (3, 0), (3, 7), (3, 14),
                               (6, 2), (6, 6), (6, 8), (6, 12), (7, 3), (7, 11),
                               (8, 2), (8, 6), (8, 8), (8, 12), (11, 0), (11, 7), (11, 14),
                               (12, 6), (12, 8), (14, 3), (14, 11)]

    def draw(self):
        # needed offset for the tiles to be at the center of their cells
        off = (CELL_SIZE - TILE_SIZE) / 2
        # initiate a tile and a cell rect at (left, top) with correct width and height
        start_x = width / 2 - CELL_SIZE * 7.5
        start_y = height / 2 - CELL_SIZE * 7.5
        original_tile = pygame.Rect((start_x + off, start_y + off), (TILE_SIZE, TILE_SIZE))
        original_cell = pygame.Rect((start_x, start_y), (CELL_SIZE + 1, CELL_SIZE + 1)) # (+1 to fill in the empty space that may be left between cells)
        # for each cell
        for pos in self.map.keys():
            x, y = pos
            # chose the correct colors
            tile_color = TILE_COLOR if self.map[pos] != "" else EMPTY_COLOR
            cell_color = TRIPLE_LETTER_COLOR if pos in self.triple_letters else (
                DOUBLE_LETTER_COLOR if pos in self.double_letters else (
                TRIPLE_WORD_COLOR if pos in self.triple_words else (
                DOUBLE_WORD_COLOR if pos in self.double_words else DEFAULT_CELL_COLOR)))

            # draw the cell (we use move to create a displaced copy of the original tile)
            cell = original_cell.move(x * CELL_SIZE, y * CELL_SIZE)
            tile = original_tile.move(x * CELL_SIZE, y * CELL_SIZE)

            pygame.draw.rect(screen, cell_color, cell)
            if tile_color == TILE_COLOR: # add a small shadow for placed tiles (letters)
                pygame.draw.rect(screen, TILE_SHADOW, tile.move(5, 5))
            pygame.draw.rect(screen, tile_color, tile)
            if tile_color == TILE_COLOR: # draw the letter on top
                text = FONT.render(self.map[pos], True, (0, 0, 0))
                screen.blit(text, (width / 2 - CELL_SIZE * 7.35 + off + x * CELL_SIZE,
                                   height / 2 - CELL_SIZE * 7.6 + off + y * CELL_SIZE))

class Player:
    def __init__(self):
        # we need a word to be filled and placed, as well as hand of available letters
        self.word = ""
        self.padded_word = ""
        self.hand = ""
        self.score = 0

    def draw(self):
        # draw virtual keyboard
        first_tile = pygame.Rect((width / 2 - CELL_SIZE * 12, height / 2), (TILE_SIZE, TILE_SIZE))
        # top row of 4 letters
        for i in range(4):
            pygame.draw.rect(screen, TILE_COLOR, first_tile.move(i * CELL_SIZE, 0))
            text = FONT.render(self.hand[i], True, (0, 0, 0))
            screen.blit(text, (width / 2 - CELL_SIZE * 12 + (i + 0.1) * CELL_SIZE, height / 2 - CELL_SIZE * 0.1))
        fifth_tile = first_tile.move(0.5 * CELL_SIZE, CELL_SIZE)
        # bottom row of 3 letters
        for i in range(3):
            pygame.draw.rect(screen, TILE_COLOR, fifth_tile.move(i * CELL_SIZE, 0))
            text = FONT.render(self.hand[4 + i], True, (0, 0, 0))
            screen.blit(text, (width / 2 - CELL_SIZE * 12 + (i + 0.6) * CELL_SIZE, height / 2 + CELL_SIZE * 0.9))


    def pick_letters(self, available_letters: dict):
        import random
        # flatten letters is a list of all the letters with the right amount of each
        flatten_letters = []
        for letter in available_letters:
            flatten_letters.extend([letter] * available_letters[letter]["amount"])

        # we choose at random just enough letters to fill the end at 7
        missing = 7 - len(self.hand)
        self.hand += "".join(random.choices(flatten_letters, k=missing))
        # then we can remove the letters we have taken
        for letter in self.hand:
            available_letters[letter]["amount"] -= 1
        # print(self.hand)
        # print(available_letters)


# helper function to get the mouse position in the coordinates of the tiles
def get_rel_mouse_pos(mouse_position):
    mx, my = mouse_position
    rmx = (mx - (width / 2 - CELL_SIZE * 7.5)) // CELL_SIZE
    rmy = (my - (height / 2 - CELL_SIZE * 7.5)) // CELL_SIZE
    return (int(rmx), int(rmy))


# main game logic and global variables
gamestate = Scrabble()
mouse_position = pygame.mouse.get_pos()
gamestate.player0.pick_letters(gamestate.letters)
gamestate.player1.pick_letters(gamestate.letters)

run = True
redraw = True
horizontal = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            redraw = True

            key_name = pygame.key.name(event.key)
            if key_name == "[7]" or key_name == "7":
                key_name = "?"
            if key_name in gamestate.active_player.hand and len(gamestate.active_player.word) < 7:
                gamestate.active_player.word += key_name

            if event.key == pygame.K_BACKSPACE:
                # remove last letter
                if len(gamestate.active_player.word) > 0:
                    gamestate.active_player.word = gamestate.active_player.word[:-1]

            if event.key == pygame.K_ESCAPE:
                run = False

        if event.type == pygame.MOUSEMOTION:
            mouse_position = pygame.mouse.get_pos()
            redraw = True

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                horizontal = not horizontal
                redraw = True
            if event.button == 1:
                if gamestate.active_player.word != "":
                    gamestate.play(get_rel_mouse_pos(mouse_position), horizontal)
                    redraw = True

    if redraw:
        redraw = False
        gamestate.update_word(get_rel_mouse_pos(mouse_position), horizontal)
        gamestate.draw()
        gamestate.draw_mouse_hoover(mouse_position, horizontal)
        pygame.display.flip()
# exit the script if user leaves the game
sys.exit()
