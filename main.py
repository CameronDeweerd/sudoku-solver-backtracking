import pygame
import time
from queue import Queue
from queue import LifoQueue

import test_puzzles
import board

FPS = 60    # cap the FPS at 60 Frames
BLOCK_SIZE = board.BLOCK_SIZE  # Set the size of the grid block
BORDER = board.BORDER


class Cell:
    def __init__(self, column, row):
        self.column = column
        self.row = row
        self.x1 = BORDER + column * BLOCK_SIZE
        self.y1 = BORDER + row * BLOCK_SIZE
        self.x2 = BORDER + (column + 1) * BLOCK_SIZE
        self.y2 = BORDER + (row + 1) * BLOCK_SIZE
        self.selected = False
        self.num = []
        self.pencil = []
        self.locked = False

    def check_select(self, pos):
        x, y = pos
        if self.x1 < x < self.x2 and self.y1 < y < self.y2:
            return True
        else:
            return False


grid = [[Cell(i, j) for i in range(9)] for j in range(9)]   # row / column
selected = Cell(0, 0)

col_pencil_count = {}
row_pencil_count = {}
box_pencil_count = {}

next_steps = Queue(maxsize=0)
undo_steps = LifoQueue(maxsize=0)
bt_steps = LifoQueue(maxsize=0)

seed = test_puzzles.hard2


# seed the board with starter numbers
def seed_board(demo_map):
    for row in range(9):
        for column in range(9):
            if not demo_map[row][column] == '':
                grid[row][column].num = demo_map[row][column]
                grid[row][column].locked = True


# enter the typed number into the cell
def key_check(pencil_mode):
    keys_pressed = pygame.key.get_pressed()

    # enter auto-solve mode
    if keys_pressed[pygame.K_LSHIFT] and keys_pressed[pygame.K_SPACE]:
        auto_solve()

    # exit if no cell was selected
    global selected
    if not selected:
        return

    # delete text if del or backspace
    if keys_pressed[pygame.K_BACKSPACE] or keys_pressed[pygame.K_DELETE]:
        if not selected.num == []:
            selected.num = []
            return
        else:
            selected.pencil = []
            return

    # move the selected box if arrow key
    if keys_pressed[pygame.K_LEFT] and selected.column > 0:
        newSelected = grid[selected.row][selected.column-1]
        newSelected.selected = True
        selected.selected = False
        selected = newSelected
        return
    if keys_pressed[pygame.K_RIGHT] and selected.column < 8:
        newSelected = grid[selected.row][selected.column+1]
        newSelected.selected = True
        selected.selected = False
        selected = newSelected
        return
    if keys_pressed[pygame.K_UP] and selected.row > 0:
        newSelected = grid[selected.row-1][selected.column]
        newSelected.selected = True
        selected.selected = False
        selected = newSelected
        return
    if keys_pressed[pygame.K_DOWN] and selected.row < 8:
        newSelected = grid[selected.row+1][selected.column]
        newSelected.selected = True
        selected.selected = False
        selected = newSelected
        return

    # Find if a number key was pressed
    number = []
    if keys_pressed[pygame.K_1] or keys_pressed[pygame.K_KP1]:
        number = 1
    elif keys_pressed[pygame.K_2] or keys_pressed[pygame.K_KP2]:
        number = 2
    elif keys_pressed[pygame.K_3] or keys_pressed[pygame.K_KP3]:
        number = 3
    elif keys_pressed[pygame.K_4] or keys_pressed[pygame.K_KP4]:
        number = 4
    elif keys_pressed[pygame.K_5] or keys_pressed[pygame.K_KP5]:
        number = 5
    elif keys_pressed[pygame.K_6] or keys_pressed[pygame.K_KP6]:
        number = 6
    elif keys_pressed[pygame.K_7] or keys_pressed[pygame.K_KP7]:
        number = 7
    elif keys_pressed[pygame.K_8] or keys_pressed[pygame.K_KP8]:
        number = 8
    elif keys_pressed[pygame.K_9] or keys_pressed[pygame.K_KP9]:
        number = 9
    if not number:
        return

    # If holding shift then switch between pencil + not
    if keys_pressed[pygame.K_RSHIFT] or keys_pressed[pygame.K_LSHIFT]:
        pencil_mode = not pencil_mode

    # change the numbers stored in the cell depending on the current mode
    if pencil_mode:
        if number in selected.pencil:
            selected.pencil.remove(number)
            return
        else:
            selected.pencil.append(number)
            selected.pencil.sort()
            return
    else:
        selected.num = number
        return


# math helper to get box num based on row and column
def get_box_num(row, column):
    box = (column // 3) + (row // 3) * 3
    return box


# solver
def auto_solve():
    start_time = time.time()
    print("start of autosolve")

    # reset all pencil marks
    reset_pencil()
    place_initial()
    while True:
        while not next_steps.empty():       # double check the basic logic
            while not next_steps.empty():   # what we have queued
                operation, row, column, number = next_steps.get()

                if operation == "undo":
                    backtrack_undo()

                elif grid[row][column].num == [] and number in grid[row][column].pencil:
                    print(operation, row, column, number)

                    # track the steps made so we can undo them if needed
                    if operation == "bt":   # backtrack
                        undo_steps.put(("bt", row, column, number))
                    else:
                        undo_steps.put(("logic", row, column, number))    # logical

                    grid[row][column].num = number
                    depencil_search(row, column)
                    board.draw_window(grid)

            # check for hidden singles for all numbers in case a number just placed has revealed one
            for i in range(1, 10):
                hidden_single(i)

        # back tracking
        check = check_board()
        print(check)

        if check == "next guess":
            backtracking()
            next_steps.put(bt_steps.get())

        if check == "complete" or check == "error":
            break

    print_board()
    print("--- %s seconds to auto-solve ---" % (time.time() - start_time))


# removes all pencil markings and resets them according the new starting point
def reset_pencil():
    for init_number in range(1, 10):
        for i in range(9):
            col_pencil_count[i, init_number] = 0
            row_pencil_count[i, init_number] = 0
            box_pencil_count[i, init_number] = 0

    for row in range(9):
        for column in range(9):
            # add all the initial pencil marks for
            if not grid[row][column].num == []:
                grid[row][column].pencil = []
            else:
                grid[row][column].pencil = [1, 2, 3, 4, 5, 6, 7, 8, 9]
                for number in range(1, 10):
                    col_pencil_count[column, number] += 1
                    row_pencil_count[row, number] += 1
                    box_pencil_count[get_box_num(row, column), number] += 1


# "Place" all initial digits and remove their penciling in the rows and columns
def place_initial(display=False):
    for row in range(9):
        for column in range(9):
            depencil_search(row, column)
            if display is True:
                grid[row][column].selected = True
                board.draw_window(grid, .2)
                grid[row][column].selected = False


# once a digit is placed in a cell then remove all pencil marks belonging to it.
def depencil_search(row, column):
    if not grid[row][column].num == []:     # only execute if the cell has been filled
        remove_pencil_mark(row, column, grid[row][column].pencil)
        number = grid[row][column].num

        # remove pencil markings for that number in all rows/columns and boxes
        for rowpencil in range(9):
            if number in grid[rowpencil][column].pencil:
                remove_pencil_mark(rowpencil, column, {number})
        for columnpencil in range(9):
            if number in grid[row][columnpencil].pencil:
                remove_pencil_mark(row, columnpencil, {number})
        # boxes can be found by rounding down to the nearest 3
        for boxcolumn in range((column//3) * 3, (column//3) * 3 + 3):
            for boxrow in range((row//3) * 3, (row//3) * 3 + 3):
                if number in grid[boxrow][boxcolumn].pencil:
                    remove_pencil_mark(boxrow, boxcolumn, {number})

        hidden_single(number)


# update pencil marks and the number trackers
def remove_pencil_mark(row, column, number_list):

    for number in number_list:
        col_pencil_count[column, number] -= 1
        row_pencil_count[row, number] -= 1
        box_pencil_count[get_box_num(row, column), number] -= 1

    grid[row][column].pencil[:] = [x for x in grid[row][column].pencil if x not in number_list]

    if len(grid[row][column].pencil) == 1:
        next_steps.put(("l", row, column, grid[row][column].pencil[0]))

    if not grid[row][column].pencil and not grid[row][column].num:
        print("error at " + str(row) + "," + str(column))
        # Puzzle impossible due to bad guesses
        # We must empty the next steps queue and place an undo action
        while next_steps.qsize() > 0:
            next_steps.get()
        next_steps.put(("undo", -1, -1, ''))


# check hidden singles
def hidden_single(number):

    for column in range(9):
        # if only one instance of the number remaining in a column then find the row its in
        if col_pencil_count[column, number] == 1:
            for i in range(9):
                if number in grid[i][column].pencil:
                    next_steps.put(("hc", i, column, number))
                    break

    for row in range(9):
        if row_pencil_count[row, number] == 1:
            for i in range(9):
                if number in grid[row][i].pencil:
                    next_steps.put(("hr", row, i, number))
                    break

    for box in range(9):
        if box_pencil_count[box, number] == 1:
            for boxcolumn in range((box%3)*3, (box%3)*3 + 3):
                for boxrow in range((box//3)*3, (box//3)*3 + 3):
                    if number in grid[boxrow][boxcolumn].pencil:
                        next_steps.put(("hb", boxrow, boxcolumn, number))
                        break


# return the first cell that is found to be empty
def first_empty():
    for row in range(9):
        for column in range(9):
            if not grid[row][column].num:
                return row, column
    return -1, -1


# check the board to see if it is filled and if it breaks any sudoku rules
def check_board():
    row_check = list()
    col_check = list()
    box_check = list()

    e_row, e_column = first_empty()
    if not e_row == -1:
        print("incomplete board at: " + str(e_row) + "," + str(e_column))
        return "next guess"

    for row in range(9):
        row_check.clear()
        for column in range(9):
            row_check.append(grid[row][column].num)
        row_check.sort()
        if not row_check == [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            print("row problem " + str(row) + "->" + str(row_check))
            return "error"

    for column in range(9):
        col_check.clear()
        for row in range(9):
            col_check.append(grid[row][column].num)
        col_check.sort()
        if not col_check == [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            print("col problem " + str(column) + "->" + str(col_check))
            return "error"

    for box in range(9):
        box_check.clear()
        for row in range(3):
            for col in range(3):
                box_check.append(grid[(box//3)*3 + row][(box % 3)*3 + col].num)
        box_check.sort()
        if not box_check == [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            print("box problem " + str(box) + "->" + str(box_check))
            return "error"

    print("looks good")
    return "complete"


# print the board into the console
def print_board():
    for row in range(9):
        for column in range(9):
            if grid[row][column].num:
                print(grid[row][column].num, end=', ')
            else:
                print(" ", end=', ')
        print("")


def backtracking():
    e_row, e_column = first_empty()
    if bt_steps.qsize() > 0:
        operation, row, column, number = bt_steps.get()
        bt_steps.put((operation, row, column, number))
        if e_row == row and e_column == column:
            return

    for i in grid[e_row][e_column].pencil:
        bt_steps.put(("bt", e_row, e_column, i))


def undo():

    operation, row, column, number = undo_steps.get()
    grid[row][column].num = []
    return operation, row, column


def backtrack_undo():
    print("undo")

    # empty the next_steps queue
    while next_steps.qsize() > 0:
        next_steps.get()

    while True:
        operation, u_row, u_column = undo()

        # undo everything until the most recent guess
        while not operation == "bt" and undo_steps.qsize() > 0:
            operation, u_row, u_column = undo()

        # Peek at the next item in the Backtrack queue and check if there are more options for this cell
        bt_operation, bt_row, bt_column, bt_number = bt_steps.get()
        bt_steps.put((bt_operation, bt_row, bt_column, bt_number))

        # stop undoing if there is a new guess available in the BackTrack queue for the current cell.
        if u_row == bt_row and u_column == bt_column:
            break

    # reset all pencil marks
    reset_pencil()
    place_initial()

    # do the next backtracking guess
    backtracking()
    next_steps.put(bt_steps.get())


def main():
    global selected
    seed_board(seed)
    pencil_mode = False
    clock = pygame.time.Clock()

    run = True
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:   # Allow for closing the menu
                run = False

            if event.type == pygame.MOUSEBUTTONUP:
                selected = []                   # unselect the currently selected cell
                pos = pygame.mouse.get_pos()    # if mouse is pressed get position of cursor #

                # check if a cell was clicked
                for row in grid:
                    for cell in row:
                        cell.selected = cell.check_select(pos)
                        if cell.selected:       # note the position of the new selected cell for easy access
                            selected = cell

            if event.type == pygame.KEYDOWN:
                key_check(pencil_mode)

        board.draw_window(grid)
    pygame.quit()


if __name__ == '__main__':
    main()
