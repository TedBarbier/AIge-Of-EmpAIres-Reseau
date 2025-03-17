import pygame
import pygame.gfxdraw
import math
from GLOBAL_VAR import *

def resize_sprite(image, scale):
    width, height = image.get_size()
    return pygame.transform.smoothscale(image, (int(width * scale), int(height * scale)))

def adjust_sprite(image, width, height):
    return pygame.transform.smoothscale(image, (int(width), int(height)))

def load_sprite_sheet(path, num_row, num_col,skip_row = 1, limit_col = 1):
    print(f"[::] Loading images from {path}")
    sprite_sheet = pygame.image.load(path).convert_alpha()
    sheet_width, sheet_height = sprite_sheet.get_size()

    frame_width = sheet_width // num_col
    frame_height = sheet_height // num_row
    
    img_array = {}
    
    for row in range(0,num_row,skip_row): #  to skip unwanted angles ( in aoe2 sprites are in 16 angles, but to simplify the complexite in memory, we will use 8 )
        angle_frames = {}
        for col in range(int(num_col/limit_col)):
            x = col * frame_width
            y = row * frame_height

            frame_image = sprite_sheet.subsurface(pygame.Rect(x, y, frame_width, frame_height))

            angle_frames[col] = frame_image

        img_array[row//skip_row] = angle_frames
    print(f"[+] Success")
    return img_array


def state_load_sprite_sheet(path): # define for each state ( attacking, walking ...) the 3d of zoom levels of the 2d array of images
    print(f"[::] Loading images from {path}")
    state_zoomlevels_3d_array = {}

    with open(path+"/size_each.txt", "r") as file: # get the size of array for each animation
        content = file.read()
    content = content.split("\n")
    image_range = int(content[0])
    print(image_range)
    content = content[1:len(content) - 1]   # in size_each there is info about how the state and sprites are organized
    print(content)
    for i in range(image_range):
        content[i] = content[i].split(",")
        row = content[i][0]
        col = content[i][1] 
        content[i][0] = int(row)
        content[i][1] = int(col)

    for image_index in range(image_range):
        current_row, current_col = content[image_index]

        current_path = path+"/img_"+str(image_index)+".webp"

        state_zoomlevels_3d_array[image_index] = load_sprite_sheet(current_path,current_row,current_col)

    print(f"[+] Success")
    return state_zoomlevels_3d_array # for animated entites


def load_single_sprites(path, col_num):
    print(f"[::] Loading images from {path}")
    image = pygame.image.load(path).convert_alpha()

    image_width, image_height = image.get_width(), image.get_height()
    
    sprite_width = image_width // col_num
    sprite_height = image_height  # Assumes sprites are vertically aligned

    sprites = {}
    
    for col in range(col_num):
        # Extract the sub-surface for each sprite
        rect = pygame.Rect(col * sprite_width, 0, sprite_width, sprite_height)
        sprite = image.subsurface(rect).copy()
        
        # Scale the sprite if needed
        sprites[col] = sprite
    print(f"[+] Success")
    return sprites



def load_sprite(path): # different scaled for each zoom level
    print(f"[::] Loading images from {path}")
    sprite = pygame.image.load(path).convert_alpha()
    print(f"[+] Success")
    return sprite # for static entities

def display_image(image, x, y, screen, flags=0x00, team = 0): # flags to display in the center or the top left
    im_width, im_height = image.get_size()

    # Calculate final position based on flags
    if flags == 0x04:
        final_x, final_y = x - im_width // 2, y - im_height // 2
    else:
        final_x, final_y = x, y

    
    # Blit the main image on the screen
    screen.blit(image, (final_x, final_y))

def draw_rectangle_with_borders(screen, topleftx, toplefty, bottomrightx, bottomrighty, color=(255, 255, 255), border_thickness=1):
    width = abs(bottomrightx - topleftx)
    height = abs(bottomrighty - toplefty)
    topleftx = min(topleftx,bottomrightx)
    toplefty = min(toplefty, bottomrighty)
    # Create a rectangle object
    rect = pygame.Rect(topleftx, toplefty, width, height)
    # Draw the rectangle's border
    pygame.draw.rect(screen, color, rect, border_thickness)

def draw_percentage_bar(screen,camera, iso_x, iso_y, _current , _max, sq_size, team = 0):

    factor = camera.zoom * sq_size
    topleftx = iso_x - factor*BARBOX_WIDTH//2
    toplefty = iso_y - BARBOX_HEIGHT

    percentage = _current/_max
    
    current_bar = pygame.Rect(topleftx, toplefty, factor * BARBOX_WIDTH * percentage, BARBOX_HEIGHT * (1.2))
    max_bar = pygame.Rect(topleftx, toplefty, factor*BARBOX_WIDTH, BARBOX_HEIGHT * (1.2))

    color = TEAM_COLORS.get(team)

    pygame.draw.rect(screen, color, current_bar)
    pygame.draw.rect(screen, BLACK_COLOR, max_bar, 2)

def resize(item, scale):
        if isinstance(item, pygame.Surface):  # Single image
            return resize_sprite(item, scale)
        elif isinstance(item, dict):  # Array of images (1D, 2D, or 3D)
            res = {}
            for key in item:
                res[key] = resize(item.get(key),scale)
            return res
        else:
            raise ValueError("Unsupported type in META_SPRITES")


def draw_diamond(screen, color, top, right, bottom, left):
    
    points = [
        (top[0], top[1]),       # Sommet haut
        (right[0], right[1]),   # Sommet droit
        (bottom[0], bottom[1]), # Sommet bas
        (left[0], left[1])      # Sommet gauche
    ]
    
    # Dessiner le losange
    pygame.draw.polygon(screen, color, points)

def draw_point(screen, color, x, y, radius=2):

    pygame.draw.circle(screen, color, (x, y), radius)

def draw_text(text, x, y, screen, font_size=30, col=(255, 255, 255)):
    
    font = pygame.font.Font(None, font_size)
    
    text_to_display = font.render(text, True, col)
 
    screen.blit(text_to_display, (int(x), int(y)))


def draw_isometric_circle(camera, screen, x, y, radius, color):
    radius_iso = radius*( camera.tile_size_2iso/camera.tile_size_2d)* camera.zoom/math.cos(math.radians(45)) * 2
    iso_x, iso_y = camera.convert_to_isometric_2d(x,y)
    width = radius_iso 
    height = radius_iso/2

    dx = iso_x - width//2

    dy = iso_y - height//2

    pygame.draw.ellipse(screen, color, (dx, dy,width,height),1)
    #pygame.draw.rect(screen, (0, 255, 0), (dx, dy, width, height),1)