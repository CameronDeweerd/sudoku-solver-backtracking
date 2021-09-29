import pygame
import time

WINDOW_WIDTH, WINDOW_HEIGHT = 1000, 800
CONTROL_WIDTH = WINDOW_WIDTH - WINDOW_HEIGHT
BLOCK_SIZE = (WINDOW_WIDTH - CONTROL_WIDTH) // 10  # Set the size of the grid block
BORDER = 10

# Colour RGB values
WHITE = (255, 255, 255)
GREY = (50, 50, 50)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 200)
BLUE = (0, 0, 255)

WIN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Sudoku Solver")
pygame.font.init()
NUM_FONT = pygame.font.SysFont('ariel', 80)
PENCIL_FONT = pygame.font.SysFont('ariel', 20)


# loop this everytime the window needs to be drawn
def draw_window(grid, sleep=0):
    WIN.fill(WHITE)
    draw_selection(grid)
    draw_grid()
    draw_text(grid)
    pygame.display.update()
    time.sleep(sleep)


# Draws the 27x27 grid
def draw_grid():

    for j in (1, 3, 9):
        for left in range(0, 9, j):
            x = BORDER + left * BLOCK_SIZE
            for down in range(0, 9, j):
                y = BORDER + down * BLOCK_SIZE
                rect = pygame.Rect(x, y, BLOCK_SIZE * j, BLOCK_SIZE * j)
                pygame.draw.rect(WIN, BLACK, rect, j)


# highlights the selected cell
def draw_selection(grid):
    for row in grid:
        for cell in row:
            if cell.selected:
                rect = pygame.Rect(cell.x1, cell.y1, BLOCK_SIZE, BLOCK_SIZE)
                pygame.draw.rect(WIN, YELLOW, rect)


# draws the penciled text or the final text
def draw_text(grid):
    for row in grid:
        for cell in row:
            if not cell.num == []:
                color = BLUE if cell.locked == False else BLACK
                text = NUM_FONT.render(str(cell.num), 1, color)
                x = (cell.x1 + cell.x2 - text.get_width()) / 2
                y = (cell.y1 + cell.y2 - text.get_height()) / 2
                WIN.blit(text, (x, y))
            elif not cell.pencil == []:
                dist = BLOCK_SIZE / 4
                for i in range(1, 10):
                    if i in cell.pencil:
                        text = PENCIL_FONT.render(str(i), 1, GREY)
                        x = (cell.x1 + dist * ((i - 1) % 3 + 1) - text.get_width() / 2)
                        y = (cell.y1 + dist * ((i - 1) // 3 + 1) - text.get_height() / 2)
                        WIN.blit(text, (x, y))
