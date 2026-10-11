"""level_editor_tut.py - a tile-based level editor for the game.

How it works in one paragraph:
A level is a grid (a list of rows) called `world_data`. Each cell holds a tile
number: -1 means empty, 0-21 means a tile type (ground, water, player spawn,
enemy, zombie, exit...). Left-click paints the selected tile into the grid,
right-click erases it. Save writes the grid to a CSV file and Load reads it
back. The game (world.py) reads the same CSV files to build its levels.
"""
import pygame
import button
import csv
import pickle   # only used by the commented-out "alternative pickle method" below

# Use the same image loader as the game. IMPORTANT: this import must stay ABOVE
# the editor's set_mode() call further down. Importing assets also imports
# settings, which opens an 800x640 game window; the editor then replaces it
# with its own bigger window. Done the other way round, the game's window
# would shrink the editor's window.
from assets import load_image, BACKGROUNDS, image_list
from settings import LEVEL_THEMES, BACKGROUND_COLOURS, TILE_NAMES, TILE_TYPES

pygame.init()

clock = pygame.time.Clock()
FPS = 60

#game window
# The window is bigger than the level view: the extra SIDE_MARGIN on the right
# holds the tile palette, and LOWER_MARGIN at the bottom holds the buttons/text.
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 640
LOWER_MARGIN = 100
SIDE_MARGIN = 300

screen = pygame.display.set_mode((SCREEN_WIDTH + SIDE_MARGIN, SCREEN_HEIGHT + LOWER_MARGIN))
pygame.display.set_caption('Level Editor')


#define game variables
ROWS = 16                           # tile rows in a level (must match the game)
MAX_COLS = 150                      # tile columns in a level (must match the game)
TILE_SIZE = SCREEN_HEIGHT // ROWS   # size of one square tile in pixels (40)
level = 0                           # which level file we are editing (UP/DOWN changes it)
current_tile = 0                    # the tile type currently selected in the palette
scroll_left = False                 # True while the LEFT arrow is held
scroll_right = False                # True while the RIGHT arrow is held
scroll = 0                          # how many pixels the view has moved to the right
scroll_speed = 1                    # 1 normally, 5 while right shift is held
theme_override = None               # press T to preview another background (None = use LEVEL_THEMES)


#load images
# (Background images now come from assets.BACKGROUNDS, one set per theme)
# Tile pictures come from assets.image_list (already scaled to a grid square)

save_img = load_image('images/button/save_btn.png')
load_img = load_image('images/button/load_btn.png')


#define colours
GREEN = (144, 201, 120)
WHITE = (255, 255, 255)
RED = (200, 25, 25)
BLACK = (0, 0, 0)

#define font
font = pygame.font.SysFont('Futura', 30)
small_font = pygame.font.SysFont('Futura', 22)

#create empty tile list
# world_data is a 2D list: world_data[row][column]. -1 = empty cell.
world_data = []
for row in range(ROWS):
	r = [-1] * MAX_COLS
	world_data.append(r)

#create ground
# Start every new level with a solid floor (tile 0) along the bottom row
for tile in range(0, MAX_COLS):
	world_data[ROWS - 1][tile] = 0


#function for outputting text onto the screen
def draw_text(text, font, text_col, x, y):
	# Turn the text into an image, then draw it at (x, y)
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))


#which background theme to show
def get_theme():
	# T-key preview wins; otherwise use the theme assigned to this level in settings.py
	if theme_override is not None:
		return theme_override
	return LEVEL_THEMES.get(level, 'forest')


#create function for drawing background
def draw_bg():
	theme = get_theme()
	screen.fill(BACKGROUND_COLOURS[theme])
	# Parallax: each layer moves at a different fraction of the scroll, so
	# slower layers look farther away. Only the copies on screen are drawn.
	for image, speed, gap_from_bottom in BACKGROUNDS[theme]:
		width = image.get_width()
		y = 0 if gap_from_bottom is None else SCREEN_HEIGHT - image.get_height() - gap_from_bottom
		offset = scroll * speed
		first = int(offset // width)
		copies = SCREEN_WIDTH // width + 2
		for i in range(first, first + copies):
			screen.blit(image, (i * width - offset, y))

#draw grid
def draw_grid():
	#vertical lines
	# Subtracting scroll makes the lines move as you scroll the map
	for c in range(MAX_COLS + 1):
		pygame.draw.line(screen, WHITE, (c * TILE_SIZE - scroll, 0), (c * TILE_SIZE - scroll, SCREEN_HEIGHT))
	#horizontal lines
	# These never need to scroll because the level only scrolls sideways
	for c in range(ROWS + 1):
		pygame.draw.line(screen, WHITE, (0, c * TILE_SIZE), (SCREEN_WIDTH, c * TILE_SIZE))


#function for drawing the world tiles
def draw_world():
	# Go through every cell; draw an image for each one that isn't empty (-1)
	for y, row in enumerate(world_data):
		for x, tile in enumerate(row):
			if tile >= 0:
				# Grid position -> pixel position, shifted left by the scroll
				screen.blit(image_list[tile], (x * TILE_SIZE - scroll, y * TILE_SIZE))



#create buttons
save_button = button.Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT + LOWER_MARGIN - 50, save_img, 1)
load_button = button.Button(SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT + LOWER_MARGIN - 50, load_img, 1)
#make a button list
# One palette button per tile type (forest, effect and lab blocks all together),
# 5 buttons per row. Clicking a button selects that tile type.
PALETTE_COLUMNS = 5
button_list = []
for i, tile_image in enumerate(image_list):
	bx = SCREEN_WIDTH + 15 + 55 * (i % PALETTE_COLUMNS)
	by = 20 + 55 * (i // PALETTE_COLUMNS)
	button_list.append(button.Button(bx, by, tile_image, 1))


# ---------------------------------------------------------------------------
# Main loop: runs every frame until the window is closed
# ---------------------------------------------------------------------------
run = True
while run:

	clock.tick(FPS)

	# Draw the level view (back to front: background, grid lines, tiles)
	draw_bg()
	draw_grid()
	draw_world()

	draw_text(f'Level: {level}', font, WHITE, 10, SCREEN_HEIGHT + LOWER_MARGIN - 90)
	draw_text('Press UP or DOWN to change level', font, WHITE, 10, SCREEN_HEIGHT + LOWER_MARGIN - 60)
	note = ' (preview)' if theme_override is not None else ''
	draw_text(f'Theme: {get_theme()}{note}  -  T to preview others', font, WHITE, 10, SCREEN_HEIGHT + LOWER_MARGIN - 30)

	#save and load data
	# button.draw() returns True on the frame the button is clicked
	if save_button.draw(screen):
		#save level data
		# Write one CSV line per grid row, e.g. "-1,-1,0,-1,..."
		with open(f'levels/level{level}_data.csv', 'w', newline='') as csvfile:
			writer = csv.writer(csvfile, delimiter = ',')
			for row in world_data:
				writer.writerow(row)
		#alternative pickle method
		#pickle_out = open(f'level{level}_data', 'wb')
		#pickle.dump(world_data, pickle_out)
		#pickle_out.close()
	if load_button.draw(screen):
		#load in level data
		#reset scroll back to the start of the level
		scroll = 0
		# Read the CSV back into world_data. Each CSV value is text, so int()
		# converts it to a number. (x is the row number, y is the column number.)
		with open(f'levels/level{level}_data.csv', newline='') as csvfile:
			reader = csv.reader(csvfile, delimiter = ',')
			for x, row in enumerate(reader):
				for y, tile in enumerate(row):
					world_data[x][y] = int(tile)
		#alternative pickle method
		#world_data = []
		#pickle_in = open(f'level{level}_data', 'rb')
		#world_data = pickle.load(pickle_in)


	#draw tile panel and tiles
	# Cover the right-hand side with a green panel, then draw the palette on it
	pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH, 0, SIDE_MARGIN, SCREEN_HEIGHT))

	#choose a tile
	# Draw every palette button; if one was clicked, remember which tile it was
	button_count = 0
	for button_count, i in enumerate(button_list):
		if i.draw(screen):
			current_tile = button_count

	#highlight the selected tile
	# A red outline around the currently selected palette button
	pygame.draw.rect(screen, RED, button_list[current_tile].rect, 3)

	#scroll the map
	# Only scroll while a key is held, and stop at the start / end of the level
	if scroll_left == True and scroll > 0:
		scroll -= 5 * scroll_speed
	if scroll_right == True and scroll < (MAX_COLS * TILE_SIZE) - SCREEN_WIDTH:
		scroll += 5 * scroll_speed

	#add new tiles to the screen
	#get mouse position
	pos = pygame.mouse.get_pos()
	# Convert the mouse's pixel position to a grid cell.
	# Adding scroll corrects for how far the map has been scrolled.
	x = (pos[0] + scroll) // TILE_SIZE
	y = pos[1] // TILE_SIZE

	#check that the coordinates are within the tile area
	# (ignore the side panel and the bottom margin)
	if pos[0] < SCREEN_WIDTH and pos[1] < SCREEN_HEIGHT:
		#update tile value
		if pygame.mouse.get_pressed()[0] == 1:   # left mouse button: paint
			if world_data[y][x] != current_tile:
				world_data[y][x] = current_tile
		if pygame.mouse.get_pressed()[2] == 1:   # right mouse button: erase
			world_data[y][x] = -1


	# Handle window and keyboard events
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			run = False
		#keyboard presses
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_UP:
				level += 1
				theme_override = None   # back to this level's own theme
			if event.key == pygame.K_DOWN and level > 0:   # level can't go below 0
				level -= 1
				theme_override = None
			if event.key == pygame.K_t:    # cycle through every theme to preview it
				themes = list(BACKGROUNDS)
				theme_override = themes[(themes.index(get_theme()) + 1) % len(themes)]
			if event.key == pygame.K_LEFT:
				scroll_left = True
			if event.key == pygame.K_RIGHT:
				scroll_right = True
			if event.key == pygame.K_RSHIFT:   # hold right shift to scroll faster
				scroll_speed = 5


		# Key released: stop scrolling / return to normal speed
		if event.type == pygame.KEYUP:
			if event.key == pygame.K_LEFT:
				scroll_left = False
			if event.key == pygame.K_RIGHT:
				scroll_right = False
			if event.key == pygame.K_RSHIFT:
				scroll_speed = 1


	# Show everything we drew this frame
	pygame.display.update()

pygame.quit()