from GLOBAL_VAR import *

class Camera:
    def __init__(self, position = PVector2(0,0), _tile_size_2iso = TILE_SIZE_2ISO, _tile_size_2d = TILE_SIZE_2D): 

        self.zoom = 1
        self.cell_X = 0
        self.cell_Y = 0
        self.tile_size_2d = _tile_size_2d
        self.tile_size_2iso = _tile_size_2iso #display size

        self.img_scale = _tile_size_2iso/50# img_scale is a value to scale the loaded images so the tiles are aligned, 50 is the choosen value after many tries
        
        self.adjust_zoom_time_acc = 0
        self.num_zoom_per_sec = 30
        self.move_time_acc = 0
        self.position = position
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.adjust_zoom_time_acc = 0
        self.num_move_per_sec = 60
        self.move_flags = 0

    def convert_to_isometric_2d(self, x, y): #convert (x,y) cooridnates to iso_x iso_y

        iso_x = int((y - x)*(self.tile_size_2iso/self.tile_size_2d) * (self.zoom ) - self.position.x * (self.zoom ))
        iso_y = int(((y + x)/2)*(self.tile_size_2iso/self.tile_size_2d) * (self.zoom  ) - self.position.y * (self.zoom ))

        return iso_x, iso_y

    
    
    def convert_from_isometric_2d(self, iso_x, iso_y):

        x_p = (iso_x/(self.zoom ) + self.position.x )*(self.tile_size_2d/self.tile_size_2iso)
        y_p = (iso_y/(self.zoom ) + self.position.y )*(self.tile_size_2d/self.tile_size_2iso)

        x = (2*y_p - x_p)/2
        y = (2*y_p + x_p)/2

        return x, y

    def convert_to_isometric_3d(self, x, y, z): #convert (x,y,z) projectile cooridnates to iso_x iso_y
        iso_x = int((y - x)*(self.tile_size_2iso/self.tile_size_2d) * (self.zoom) - self.position.x * (self.zoom ))
        iso_y = int(((y + x - z)/2)*(self.tile_size_2iso/self.tile_size_2d) * (self.zoom) -  self.position.y * (self.zoom ))
        
        return iso_x, iso_y 

    def indexes_in_point_of_view(self, g_width = None, g_height = None, topcorner_x = 0,topcorner_y = 0,bottomcorner_x =0, bottomcorner_y = 0):
        
        vp_x = topcorner_x
        vp_y = topcorner_y

        if g_width and g_height:
            height = g_height
            width = g_width
        else:
            height = topcorner_y
            width = topcorner_x

        topleft_x, topleft_y = self.convert_from_isometric_2d(vp_x, vp_y) #
        bottomright_x, bottomright_y= self.convert_from_isometric_2d(vp_x + width, vp_y + height) 

        topright_x, topright_y = self.convert_from_isometric_2d(vp_x + width, vp_y) #
        bottomleft_x, bottomleft_y= self.convert_from_isometric_2d(vp_x, vp_y + height) #


        top_X = round(topleft_x/(self.tile_size_2d ) + 1)
        top_Y  = round(topleft_y/(self.tile_size_2d ) + 1)

        right_X = round(bottomleft_x/(self.tile_size_2d ) + 1)
        right_Y = round(bottomleft_y/(self.tile_size_2d ) + 1)

        left_X = round(topright_x/(self.tile_size_2d ) + 1)
        left_Y = round(topright_y/(self.tile_size_2d ) + 1)

        bottom_X = round(bottomright_x/(self.tile_size_2d ) + 1)
        bottom_Y  = round(bottomright_y/(self.tile_size_2d ) + 1)
        
        return (top_Y, top_X), (left_Y, left_X), (right_Y, right_X), (bottom_Y, bottom_X)

    def check_in_point_of_view(self, x_to_check, y_to_check, g_width , g_height):
        if (-TILE_SIZE_2ISO * (self.zoom + 1) * 3 < x_to_check and x_to_check<g_width + TILE_SIZE_2ISO * (self.zoom + 1)* 3  and -TILE_SIZE_2ISO * (self.zoom + 1)* 3 <y_to_check and y_to_check < g_height + TILE_SIZE_2ISO * (self.zoom + 1)* 3 ):
            return True

    def adjust_zoom(self, dt, amount, g_width, g_height):
        self.adjust_zoom_time_acc += dt
        if self.adjust_zoom_time_acc > ONE_SEC/self.num_zoom_per_sec:
            self.adjust_zoom_time_acc = 0
            self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, self.zoom + amount))
            self.width = g_width/self.zoom
            self.height = g_height/self.zoom

    def move(self, dt, amount):
        self.move_time_acc += dt
        if (self.move_time_acc > ONE_SEC/self.num_move_per_sec):
            if (self.move_flags & 0b0001):
                self.position.x -= amount
            
            if (self.move_flags & 0b0010):
                self.position.x += amount

            if (self.move_flags & 0b0100):
                self.position.y += amount
            
            if (self.move_flags & 0b1000):
                self.position.y -= amount
                
            self.move_time_acc = 0
            self.move_flags = 0 # reset flags


    def draw_box(self, screen, _entity):
        topleft_x, topleft_y = _entity.position.x - _entity.box_size, _entity.position.y - _entity.box_size
        topright_x, topright_y = _entity.position.x + _entity.box_size, _entity.position.y - _entity.box_size

        bottomleft_x, bottomleft_y = _entity.position.x - _entity.box_size, _entity.position.y + _entity.box_size
        bottomright_x, bottomright_y = _entity.position.x + _entity.box_size, _entity.position.y + _entity.box_size

        d_topleft_x, d_topleft_y = self.convert_to_isometric_2d(topleft_x, topleft_y)
        d_topright_x, d_topright_y = self.convert_to_isometric_2d(topright_x, topright_y)

        d_bottomleft_x, d_bottomleft_y = self.convert_to_isometric_2d(bottomleft_x, bottomleft_y)
        d_bottomright_x, d_bottomright_y = self.convert_to_isometric_2d(bottomright_x, bottomright_y)

        pygame.draw.polygon(screen, WHITE_COLOR, [(d_topleft_x, d_topleft_y),(d_topright_x, d_topright_y),(d_bottomright_x, d_bottomright_y),(d_bottomleft_x, d_bottomleft_y)], 1)

