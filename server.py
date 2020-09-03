import os
import random
import copy
import cherrypy
import enum
from AStar import *

"""
This is a simple Battlesnake server written in Python.
For instructions see https://github.com/BattlesnakeOfficial/starter-snake-python/README.md
"""

class Objects(enum.Enum):
      SNAKE = 1
      WALL = 2
      FOOD = 3
      SAFE = 4

class Battlesnake(object):

    BUFFER = 3 # minimum safe distance
    
    def init(self, data):
        print(f"Starting turn {data['turn']}")
        print(f"Constructing {data['board']['height']} by {data['board']['width']}")
        grid = [[0 for col in range(data['board']['height'])] for row in range(data['board']['width'])]
        # print(f'{grid}')
        for snake in data['board']['snakes']:
            print(f"With snek ID: {snake['id']}")
            for coord in snake['body']:
                grid[coord['x']][coord['y']] = Objects.SNAKE

        for f in data['board']['food']:
            grid[f['x']][f['y']] = Objects.FOOD

        return data['you'], grid
    
    def direction(self, from_cell, to_cell):
        print(f'Moving from {from_cell} to {to_cell}')
        dx = to_cell[0] - from_cell[0]
        dy = to_cell[1] - from_cell[1]

        if dx == 1:
            return 'right'
        elif dx == -1:
            return 'left'
        elif dy == -1:
            return 'down'
        elif dy == 1:
            return 'up'

    def distance(self, p, q):
        print(f'Distance between {p} and {q}')
        dx = abs(p['x'] - q['x'])
        dy = abs(p['y'] - q['y'])
        return dx + dy;

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        # This function is called when you register your Battlesnake on play.battlesnake.com
        # It controls your Battlesnake appearance and author permissions.
        # TIP: If you open your Battlesnake URL in browser you should see this data
        return {
            "apiversion": "1",
            "author": "grahamdunn",  # TODO: Your Battlesnake Username
            "color": "#888888",  # TODO: Personalize
            "head": "default",  # TODO: Personalize
            "tail": "default",  # TODO: Personalize
        }

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def start(self):
        # This function is called everytime your snake is entered into a game.
        # cherrypy.request.json contains information about the game that's about to be played.
        # TODO: Use this function to decide how your snake is going to look on the board.
        data = cherrypy.request.json

        print("START")
        return "ok"

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def move(self):
        # This function is called on every turn of a game. It's how your snake decides where to move.
        # Valid moves are "up", "down", "left", or "right".
        # TODO: Use the information in cherrypy.request.json to decide your next move.
        data = cherrypy.request.json

        my_snake, grid = self.init(data)

        for enemy in data['board']['snakes']:
          if (enemy['id'] == my_snake['id']):
              continue
          if self.distance(my_snake['head'], enemy['head']) > self.BUFFER:
              continue
          if (len(enemy['length']) > len(my_snake['length'])-1):
            #dodge
            if enemy['coords'][0][1] < data['board']['height']-1:
                grid[enemy['coords'][0][0]][enemy['coords'][0][1]+1] = Objects.SAFE
            if enemy['coords'][0][1] > 0:
                grid[enemy['coords'][0][0]][enemy['coords'][0][1]-1] = Objects.SAFE

            if enemy['coords'][0][0] < data['board']['width']-1:
                grid[enemy['coords'][0][0]+1][enemy['coords'][0][1]] = Objects.SAFE
            if enemy['coords'][0][0] > 0:
                grid[enemy['coords'][0][0]-1][enemy['coords'][0][1]] = Objects.SAFE


        my_snake_head = [my_snake['head']['x'], my_snake['head']['y']]
        my_snake_coords = [[coord['x'], coord['y']] for coord in my_snake['body']]
        path = None
        middle = {"x": data['board']['width'] / 2, "y": data['board']['height'] / 2}
        foods = sorted(data['board']['food'], key = lambda p: self.distance(p,middle))

        for food in [[coord['x'], coord['y']] for coord in foods]:
          print(f'food: {food}')
          tentative_path = a_star(my_snake_head, food, grid, my_snake_coords)
          print(f'Tentative Path: {tentative_path}')
          if not tentative_path:
              print("no path to food")
              continue

          path_length = len(tentative_path)
          my_snake_length = my_snake['length'] + 1

          dead = False
          for enemy in data['board']['snakes']:
              if enemy['id'] == my_snake['id']:
                  continue
              if path_length > self.distance(enemy['body'][0], {'x': food[0], 'y': food[1]):
                  dead = True
          if dead:
              continue

          # Update my_snake
          if path_length < my_snake_length:
              remainder = my_snake_length - path_length
              new_my_snake_coords = list(reversed(tentative_path)) + my_snake_coords[:remainder]
          else:
              new_my_snake_coords = list(reversed(tentative_path))[:my_snake_length]

          if grid[new_my_snake_coords[0][0]][new_my_snake_coords[0][1]] == Objects.FOOD:
              # we ate food so we grow
              new_my_snake_coords.append(new_my_snake_coords[-1])

          # Create a new grid with the updates my_snake positions
          new_grid = copy.deepcopy(grid)

          for coord in my_snake_coords:
              new_grid[coord[0]][coord[1]] = 0
          for coord in new_my_snake_coords:
              new_grid[coord[0]][coord[1]] = Objects.SNAKE

          printg(grid, 'orig')
          printg(new_grid, 'new')

          print(f"Snake tail: {my_snake['body'][-1]}")
          foodtotail = a_star(food,new_my_snake_coords[-1],new_grid, new_my_snake_coords)
          if foodtotail:
              path = tentative_path
              break
          print("no path to tail from food")

        if not path:
            path = a_star(my_snake_head, my_snake['body'][-1], grid, my_snake_coords)

        despair = not (path and len(path) > 1)

        if despair:
            for neighbour in neighbours(my_snake_head,grid,0,my_snake_coords, [1,2,5]):
                path = a_star(my_snake_head, neighbour, grid, my_snake_coords)
                print('i\'m scared')
                break

        despair = not (path and len(path) > 1)


        if despair:
          for neighbour in neighbours(my_snake_head,grid,0,my_snake_coords, [1,2]):
              path = a_star(my_snake_head, neighbour, grid, my_snake_coords)
              print('lik so scared')
              break

        if path:
          assert path[0] == tuple(my_snake_head)
          assert len(path) > 1

        move = self.direction(path[0], path[1])
        print(f"MOVE: {move}")
        return {"move": move}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def end(self):
        # This function is called when a game your snake was in ends.
        # It's purely for informational purposes, you don't have to make any decisions here.
        data = cherrypy.request.json

        print("END")
        return "ok"


if __name__ == "__main__":
    server = Battlesnake()
    cherrypy.config.update({"server.socket_host": "0.0.0.0"})
    cherrypy.config.update(
        {"server.socket_port": int(os.environ.get("PORT", "8080")),}
    )
    print("Starting Battlesnake Server...")
    cherrypy.quickstart(server)
