from GLOBAL_VAR import *
from GLOBAL_IMPORT import *
from ImageProcessingDisplay.imagemethods import *

from shapely.geometry import Point, Polygon

class MiniMap:

    def __init__(self, position, nb_CellX, nb_CellY):
        self.position = position

        self.nb_CellX = nb_CellX
        self.nb_CellY = nb_CellY
        self.width = MINIMAP_WIDTH
        self.height = MINIMAP_HEIGHT

        self.tile_size_2d = TILE_SIZE_2D
        
        self.top = PVector2(0, 0)
        self.right = PVector2(0, (nb_CellY )*TILE_SIZE_2D)
        self.bottom = PVector2((nb_CellX)*TILE_SIZE_2D, (nb_CellY)*TILE_SIZE_2D)
        self.left = PVector2((nb_CellX)*TILE_SIZE_2D, 0)

    def convert_to_minimap_2d(self, x, y):
        
        mini_iso_x = int((y - x)*((self.width/max(self.nb_CellX, self.nb_CellY))/self.tile_size_2d) + self.position.x + self.width//2)
        mini_iso_y = int(((y + x)/2)*((self.height/max(self.nb_CellX, self.nb_CellY))/self.tile_size_2d) + self.position.y )

        return mini_iso_x, mini_iso_y

    def convert_from_minimap_2d(self, mini_iso_x, mini_iso_y):
        x = int((self.tile_size_2d*(-mini_iso_x + 2*mini_iso_y + self.nb_CellX//2*self.tile_size_mini_iso2d - 2*mini_iso_x + self.position.x))/(2*self.tile_size_mini_iso2d))
        y = int((self.tile_size_2d*(mini_iso_x + 2*mini_iso_y - self.nb_CellX//2*self.tile_size_mini_iso2d - 2*mini_iso_x - self.position.x))/(2*self.tile_size_mini_iso2d))

        return x, y
    
    def display_ground(self, screen):

        top_mini_iso_x, top_mini_iso_y = self.convert_to_minimap_2d(self.top.x, self.top.y)
        right_mini_iso_x, right_mini_iso_y = self.convert_to_minimap_2d(self.right.x, self.right.y)

        bottom_mini_iso_x, bottom_mini_iso_y = self.convert_to_minimap_2d(self.bottom.x, self.bottom.y)
        left_mini_iso_x, left_mini_iso_y = self.convert_to_minimap_2d(self.left.x, self.left.y)
        
        display_image(MINIMAP_IMG, left_mini_iso_x + self.width,top_mini_iso_y + self.height//2, screen, 0x04)
        
        draw_point(screen, (255, 255, 255), left_mini_iso_x, top_mini_iso_y)
        #print(f"width:{right_mini_iso_x - left_mini_iso_x}, height:{bottom_mini_iso_y - top_mini_iso_y}")
        #draw_rectangle_with_borders(screen, left_mini_iso_x, top_mini_iso_y, right_mini_iso_x, bottom_mini_iso_y) # rect for debugging

        draw_diamond(screen, MINIMAP_COLOR, (top_mini_iso_x, top_mini_iso_y), (right_mini_iso_x, right_mini_iso_y), (bottom_mini_iso_x, bottom_mini_iso_y), (left_mini_iso_x, left_mini_iso_y))
        
    def display_on_cart(self, screen, entity):
        point_color = None

        if (isinstance(entity, Tree)):
            point_color = BROWN_TREE_COLOR
        elif (isinstance(entity, Gold)):
            point_color = GOLD_COLOR
        elif (isinstance(entity, Unit)):
            point_color = TEAM_COLORS.get(entity.team)

        mini_iso_x, mini_iso_y = self.convert_to_minimap_2d(entity.position.x, entity.position.y)
        draw_point(screen, point_color, mini_iso_x, mini_iso_y)

    def display_camera(self, screen, top_X, top_Y, bottom_X, bottom_Y):
        topleft_x, topleft_y = top_X * TILE_SIZE_2D + TILE_SIZE_2D/2, top_Y * TILE_SIZE_2D + TILE_SIZE_2D/2 
        bottomright_x, bottomright_y = bottom_X*TILE_SIZE_2D + TILE_SIZE_2D/2, bottom_Y*TILE_SIZE_2D + TILE_SIZE_2D/2

        mini_topleft_x, mini_topleft_y = self.convert_to_minimap_2d(topleft_x, topleft_y)
        mini_bottomright_x, mini_bottomright_y = self.convert_to_minimap_2d(bottomright_x, bottomright_y)

        draw_rectangle_with_borders(screen, mini_topleft_x, mini_topleft_y, mini_bottomright_x, mini_bottomright_y)

    def update_camera(self, camera, mouse_x, mouse_y):
        _, top_mini_iso_y = self.convert_to_minimap_2d(self.top.x, self.top.y)
        right_mini_iso_x, _ = self.convert_to_minimap_2d(self.right.x, self.right.y)

        _, bottom_mini_iso_y = self.convert_to_minimap_2d(self.bottom.x, self.bottom.y)
        left_mini_iso_x, _ = self.convert_to_minimap_2d(self.left.x, self.left.y)

        
        if (left_mini_iso_x<mouse_x<right_mini_iso_x and top_mini_iso_y<mouse_y<bottom_mini_iso_y):

            x, y = int((mouse_x - self.position.x - self.width//2)*(camera.tile_size_2iso/(self.width/max(self.nb_CellX, self.nb_CellY))) - camera.width/2) , int((mouse_y - self.position.y)*(camera.tile_size_2iso/(self.height/max(self.nb_CellX, self.nb_CellY))) - camera.height/2)
            camera.position.x = x
            camera.position.y = y

    def update_position(self, g_width, g_height):

        img_width, img_height = MINIMAP_IMG.get_size()

        self.position.x = g_width - img_width/2.5 - MINIMAP_WIDTH//2
        self.position.y = g_height - img_height/2.5 - MINIMAP_HEIGHT//2






