
from GLOBAL_VAR import *
from GameField.map import *


tmap = Map(MAP_CELLX, MAP_CELLY)

cell_X_h = 7
cell_Y_h = 2
cell_X_a = 12
cell_Y_a = 2

position = None
team =1
tmap.generate_map(num_players=3)

horse = Villager( cell_Y_h, cell_X_h, position, team)
archer = Archer( cell_Y_a, cell_X_a, position, team)
tmap.add_entity(horse)
tmap.add_entity(archer)



cell_X_ar = 20
cell_Y_ar = 33

cell_X_s = 22
cell_Y_s = 37

cell_X_c = 40
cell_Y_c = 37

cell_X_hs = 10
cell_Y_hs = 10

cell_X_f = 16
cell_Y_f = 2

archery_range = ArcheryRange(cell_Y_ar, cell_X_ar, None, 1) # None cause position are determined by the map and cell et TILE_SIZE_2D
stable = Stable(cell_Y_s, cell_X_s, None, 1)
house = House(cell_Y_hs, cell_X_hs, None, 1)
camp = Camp(cell_Y_c, cell_X_c, None, 1)
farm = Farm(cell_Y_f, cell_X_f, None, 1)
tmap.add_entity(stable)
tmap.add_entity(archery_range)
tmap.add_entity(house)
tmap.add_entity(camp)
tmap.add_entity(farm)



pygame.mouse.set_visible(False)

v = PVector2(800,100)
#endvar
dragging = False

last_offset_x, last_offset_y = camera.view_port.position.x, camera.view_port.position.y
last_mouse_x, last_mouse_y = 0, 0

clock = pygame.time.Clock()
FPS = 800
running = True
draw_selection = False
current_time = pygame.time.get_ticks()

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
            horse.state = UNIT_WALKING
            horse.animation_frame = 0

            if event.button == 1:
                dragging = True
                last_offset_x, last_offset_y = camera.view_port.position.x, camera.view_port.position.y
            elif event.button == 3:  # Right click
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

    tmap.display(current_time, screen, camera, SCREEN_WIDTH, SCREEN_HEIGHT)
    #archer.attacking(current_time, horse)

    if dragging:
        camera.view_port.position.x = last_offset_x + (mouse_x - last_mouse_x)
        camera.view_port.position.y = last_offset_y + (mouse_y - last_mouse_y)
      
    elif draw_selection:
        draw_rectangle_with_borders(screen, last_mouse_x, last_mouse_y, mouse_x, mouse_y)

    horse.try_to_move(current_time, v)

    fps = int(clock.get_fps())
    fps_text = font.render(f"FPS: {fps}", True, (255, 255, 255))
    screen.blit(fps_text, (10, 10))

    screen.blit(CURSOR_IMG,(mouse_x, mouse_y))
    clock.tick(FPS)
    pygame.display.flip()
    
pygame.quit()
