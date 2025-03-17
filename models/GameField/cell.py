from GLOBAL_VAR import *


class Cell:

    def __init__(self, _Y, _X, _position):

        self.Y = _Y
        self.X = _X
        self.position = _position
        self.representation = "g"

    def display(self, screen, camera):
        iso_x, iso_y = camera.convert_to_isometric_2d( self.position.x, self.position.y)
        
        display_image(META_SPRITES_CACHE_HANDLE(camera.zoom, list_keys = [self.representation], camera = camera), iso_x, iso_y, screen, 0x04)