import numpy as np
import pyglet

from hex import Hex, HexOrientation as hex_util
from waypoint import Waypoint
from resources import palette, tile_walls


class HexCell:
    def __init__(self, hex_coordinate: Hex, radius: int, screen_origin: np.ndarray,
                 background_color: str, batch: pyglet.graphics.Batch):
        self.hex_coordinate = hex_coordinate

        self.center_x = hex_util.center(self.hex_coordinate, radius, screen_origin)[0]
        self.center_y = hex_util.center(self.hex_coordinate, radius, screen_origin)[1]
        self.background = pyglet.shapes.Polygon(*hex_util.corners(radius, self.center_x, self.center_y),
                                                color=palette[background_color][0],
                                                batch=batch)
        self.background.opacity = 0

        # For maze generation
        self.walls = {neighbor: True for neighbor in hex_util.neighbors(self.hex_coordinate)}
        self.visited = False
        self._waypoint = None

    def wall_sprite(self, wall: str, batch: pyglet.graphics.Batch):
        sprite = pyglet.sprite.Sprite(tile_walls[wall], x=self.center_x, y=self.center_y,
                                      batch=batch)
        sprite.scale = 2.0
        return sprite

    def coordinate(self):
        return self.hex_coordinate

    def visit(self):
        self.visited = True

    def unvisited(self):
        return not self.visited

    def remove_wall(self, neighbor: 'HexCell'):
        if self.walls[neighbor.coordinate()]:
            self.walls[neighbor.coordinate()] = False

    def neighbors(self):
        neighbors = []
        for neighbor, wall in list(self.walls.items()):
            if not wall:
                neighbors.append(neighbor)
        return neighbors

    def place_waypoint(self, waypoint: Waypoint):
        self._waypoint = waypoint
    
    def waypoint(self):
        if isinstance(self._waypoint, Waypoint):
            return self._waypoint
        return False
    
    def fade(self, opacity):
        self.background.opacity = opacity

    def highlight(self):
        if isinstance(self._waypoint, Waypoint):
            self.background.color = self._waypoint.color()
        self.background.opacity = 255