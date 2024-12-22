import random
from collections import deque

import numpy as np
import pyglet
import pyglet.event

from cell import HexCell
from hex import Hex
from hex import HexOrientation as hex_util
from hex import generate_square_grid
from waypoint import WaypointType, Waypoint
from player import Player
from resources import click_sound, fade_out, ball_image


class HexBoard:
    """ 
    radius:     pixel measurement of radius for a hex tile
    grid_size:  int for creating a 'square' hex grid (each side length matches 
                this)
    """
    def __init__(self, radius: int, grid_size: int, origin_x: int, origin_y: int,
                 batch: pyglet.graphics.Batch, player: Player, window: pyglet.window):
        self._radius = radius
        self._grid_size = grid_size
        self._origin = np.row_stack([origin_x, origin_y])
        self._batch = batch
        self._window = window
        
        self._tiles = {coordinate: HexCell(coordinate, self._radius, self._origin, 'white', self._batch) for coordinate in generate_square_grid(self._grid_size)}
        
        self.player_pos = Hex(0, 0, 0)
        self.player = player
        self._player_trail = dict()
        self._player_trail[self.player_pos] = 0
        self._hit_walls = []
        self._tiles[self.player_pos].highlight()
        
        self.start_level(1)

    def __contains__(self, key: Hex):
        return key in self._tiles
    
    def start_level(self, level: int):
        potential_waypoints = [Waypoint(type) for type in WaypointType]
        waypoints = random.choices(potential_waypoints, weights=[w.data['spawn_frequency'] for w in potential_waypoints], k=random.randint(1, level))
        place_these_waypoints = sorted(deque(random.choices(potential_waypoints, [w.data['spawn_frequency'] for w in potential_waypoints], k=random.randint(level+1, level+random.randint(2, 3)))), key=lambda w: w.data['spawn_frequency'])
        
        self.waypoint_graph = {distance: deque() for distance in range(1, self._radius+1)}
        while len(place_these_waypoints) > 0:
            nearby = random.randint(1, self._radius//2)
            far = random.randint(self._radius//2, self._radius)
            
            current_waypoint = place_these_waypoints.pop()
            if current_waypoint.data['spawn_frequency'] > 1:
                self.waypoint_graph[nearby].append(current_waypoint)
            else:
                self.waypoint_graph[far].append(current_waypoint)
        
        self.generate_maze_ver1(self._tiles[self.player_pos])
        # self.generate_maze_ver2(self._tiles[self.player_pos])
            
    def boundary_check(self, pre_move: Hex, direction: str):
        post_move = hex_util.neighbor(pre_move, direction)
        if post_move in self._tiles:
            if not self._tiles[post_move].walls[pre_move]:
                return post_move
        # Show what's blocking the way
        new_wall_sprite = self._tiles[pre_move].wall_sprite(direction, self._batch)
        self._hit_walls.append(new_wall_sprite)
        return pre_move 

    def fade_tile(self, dt: float):
        for tile, time in list(self._player_trail.items()):
            self._player_trail[tile] += 1 if time < len(fade_out) - 1 else 0
            self._tiles[tile].fade(fade_out[time])    

    def move_player(self, direction: str):
        click_sound.play()
        self.player_pos = self.boundary_check(self.player_pos, direction)
        self._tiles[self.player_pos].highlight()
        
        potential_waypoint = self._tiles[self.player_pos].waypoint()
        if isinstance(potential_waypoint, Waypoint) and str(potential_waypoint) not in self.player.waypoint_collection:
            self.player.collect_waypoint(potential_waypoint)
            pyglet.event.EventDispatcher.dispatch_event(self._window, 'on_waypoint_discovered', potential_waypoint.color(), potential_waypoint.ability_description())
            self._tiles[self.player_pos].remove_waypoint()
        
        next_position = hex_util.center(self.player_pos, self._radius, self._origin)
        self.player.add_next_position(next_position) # smooths player movement
        self._player_trail[self.player_pos] = 0
    
    def remove_wall(self, cell_a: HexCell, cell_b: HexCell):
        if cell_a.coordinate() in cell_b.walls:
            cell_b.remove_wall(cell_a)
        if cell_b.coordinate() in cell_a.walls:
            cell_a.remove_wall(cell_b)
    
    def add_wall(self, cell_a: HexCell, cell_b: HexCell):
        if cell_a.coordinate() in cell_b.walls:
            cell_b.add_wall(cell_a)
        if cell_b.coordinate() in cell_a.walls:
            cell_a.add_wall(cell_b)
    
    def unvisited_neighbors(self, tile: HexCell):
        neighbors = hex_util.neighbors(tile.coordinate())
        return [self._tiles[neighbor] for neighbor in neighbors if neighbor in self._tiles and self._tiles[neighbor].unvisited()]
    
    def generate_maze_ver1(self, current_tile: HexCell):
        if current_tile.unvisited():
            current_tile.visit()
        
        neighbors = self.unvisited_neighbors(current_tile)
        random.shuffle(neighbors)
    
        for potential_neighbor in neighbors:
            if potential_neighbor.coordinate() in self._tiles:
                neighbor_tile = self._tiles[potential_neighbor.coordinate()]
                
                if neighbor_tile.unvisited():
                    self.remove_wall(current_tile, neighbor_tile)
                    self.generate_maze_ver1(neighbor_tile)
                    
    def generate_maze_ver2(self, current_tile: HexCell):
        self.generate_maze_ver1(current_tile)
        self.apply_sparseness(probability=100, percent_fill=75)
    
    def tile_count(self):
        return len(self._tiles.values())
    
    def fill(self):
        fill = 100
        percent = self.tile_count() // 100
        for tile in self._tiles:
            if self._tiles[tile].blocked_off():
                fill -= percent
        return fill

    def apply_sparseness(self, *, probability: int, percent_fill: int):
        
        while self.fill() > percent_fill:
            for tile, cell_a in self._tiles.items():
                if len(list(filter(None, cell_a.walls))) == 5:
                    if random.randint(1, 100) <= probability:
                        self.add_wall(tile, tile)
                        
if __name__ == '__main__':
    test_window = pyglet.window.Window()
    test_batch = pyglet.graphics.Batch()
    test_player = Player(ball_image, test_window.width//2, test_window.height//2, test_batch)
    test_board = HexBoard(radius=64, grid_size=4, origin_x=test_window.width//2, origin_y=test_window.height//2, batch=test_batch,player=test_player,window=test_window)
    
    print(f'tile_count: {test_board.tile_count()}')
    print(f'fill: {test_board.fill()}')