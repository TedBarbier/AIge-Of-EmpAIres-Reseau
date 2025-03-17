import random
from GLOBAL_VAR import *
from GameField.map import *

# Initialize the map with desired dimensions
MAP_CELLX = 120  # Adjust for larger maps
MAP_CELLY = 120
tmap = Map(MAP_CELLX, MAP_CELLY)

# Generate the map with 3 players
tmap.generate_map(num_players=3)

# ====>>> THIS SECTION IS ONLY FOR STRESS TEST, 
# Function to generate random positions
def get_random_position(max_x, max_y):
    return random.randint(0, max_x - 1), random.randint(0, max_y - 1)

# Add units to the map
unit_classes = [Villager, Archer, HorseMan, SwordMan]
num_units = 700  # Adjust as needed
team_count = 4

for _ in range(num_units):
    cell_x, cell_y = get_random_position(MAP_CELLX, MAP_CELLY)
    unit_type = random.choice(unit_classes)
    team = random.randint(1, team_count)
    position = None  # Position is determined by the map
    unit = unit_type(cell_y, cell_x, position, team)
    tmap.add_entity(unit)

# Add buildings to the map
building_classes = [ArcheryRange, Stable, House, Camp, Farm]
num_buildings = 400  # Adjust as needed

for _ in range(num_buildings):
    cell_x, cell_y = get_random_position(MAP_CELLX, MAP_CELLY)
    building_type = random.choice(building_classes)
    team = random.randint(1, team_count)
    building = building_type(cell_y, cell_x, None, team)
    tmap.add_entity(building)

# Initialize Pygame
pygame.mouse.set_visible(False)

v = PVector2(800, 100)
dragging = False

last_offset_x, last_offset_y = camera.view_port.position.x, camera.view_port.position.y
last_mouse_x, last_mouse_y = 0, 0

clock = pygame.time.Clock()
FPS = 120
running = True
draw_selection = False
current_time = pygame.time.get_ticks()
all_units = [
    entity
    for region in tmap.entity_matrix.values()  # Traverse regions
    for cell in region.values()               # Traverse cells in region
    for entity in cell                        # Traverse entities in cell (set)
    if isinstance(entity, Unit)              # Only select units
]

moving_unit = []

# Main game loop
while running:
    current_time = pygame.time.get_ticks()
    
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_width(), screen.get_height()
    
    mouse_x, mouse_y = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            last_mouse_x, last_mouse_y = event.pos
            v.x, v.y = camera.convert_from_isometric_2d(last_mouse_x, last_mouse_y)
            if event.button == 1:
                dragging = True
                last_offset_x, last_offset_y = camera.view_port.position.x, camera.view_port.position.y
            elif event.button == 3:
                draw_selection = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False
            elif event.button == 3:
                draw_selection = False

    keys = pygame.key.get_pressed()

    if keys[pygame.K_p]:
        camera.adjust_zoom(current_time, 0.1)
    if keys[pygame.K_o]:
        camera.adjust_zoom(current_time, -0.1)
    screen.fill((0, 0, 0))

    # Display the map and all entities
    tmap.display(current_time, screen, camera, SCREEN_WIDTH, SCREEN_HEIGHT)

    # Randomly move a few units to simulate gameplay
    if all_units:
        random_unit = all_units[random.randint(0,len(all_units) - 1)]
        # Generate a random new position for the unit
        cell_x, cell_y = get_random_position(MAP_CELLX, MAP_CELLY)
        unit_position = PVector2(cell_x * TILE_SIZE_2D, cell_y * TILE_SIZE_2D)
        moving_unit.append((random_unit , unit_position))
        random_unit.state = UNIT_WALKING
        random_unit.animation_frame = 0

    for current in moving_unit:
        #print(current[0], current[1])
        u = current[0]
        v = current[1]
        u.try_to_move(current_time, v)

    if dragging:
        camera.view_port.position.x = last_offset_x + (mouse_x - last_mouse_x)
        camera.view_port.position.y = last_offset_y + (mouse_y - last_mouse_y)
    elif draw_selection:
        draw_rectangle_with_borders(screen, last_mouse_x, last_mouse_y, mouse_x, mouse_y)

    # Display FPS
    fps = int(clock.get_fps())
    fps_text = font.render(f"FPS: {fps}", True, (255, 255, 255))
    screen.blit(fps_text, (10, 10))

    # Draw the custom cursor
    screen.blit(CURSOR_IMG, (mouse_x, mouse_y))
    clock.tick(FPS)
    pygame.display.flip()

pygame.quit()
