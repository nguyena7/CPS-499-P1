import cocos
import pyglet
import random
from cocos import *
from cocos.director import director

## Very bad tower defense game
## Import a background, get zombie to walk onto the screen, spawn multiple zombies, handle clicking on zombie
## When zombie reaches the fortress, reduce the health.

title = "Game"
width = 1280
height = 720

# Loading images
zombie_walk = pyglet.resource.image('walk_spritesheet.png')
castle = pyglet.resource.image('wall_good.png')
castle_lil_broke = pyglet.resource.image('wall_lil_broke.png')
castle_lot_broke = pyglet.resource.image('wall_lotta_broke.png')
castle_no_door = pyglet.resource.image('wall_no_door.png')
background = pyglet.resource.image('background.png')
explosion = pyglet.resource.image('explosionSmall.png')

# Dividing Spritesheets
walk_grid = pyglet.image.ImageGrid(zombie_walk, 1, 10)
boom_grid = pyglet.image.ImageGrid(explosion, 5, 5)

# Convert to texture grid
walk_texture = pyglet.image.TextureGrid(walk_grid)
walk_texture_list = walk_texture[:]
boom_texture = pyglet.image.TextureGrid(boom_grid)
boom_texture_list = boom_texture[:]

# Get Animation Objects
walk_anim = pyglet.image.Animation.from_image_sequence(walk_texture_list, 0.1, loop=True)
boom_anim = pyglet.image.Animation.from_image_sequence(boom_texture_list, 0.05, loop=False)

# Create a window using Director
window = cocos.director.director.init(
    width, height,
    caption=title, fullscreen=False)


class Menu(cocos.menu.Menu):
    """Main Menu"""
    def __init__(self):
        super().__init__("Trash Game")
        options = [cocos.menu.MenuItem("Start Game", self.start_game), cocos.menu.MenuItem("Quit Game", self.quit_game)]
        self.create_menu(options)

    def start_game(self):
        global game_layer
        game_layer = Game()
        game_scene = cocos.scene.Scene(game_layer)
        cocos.director.director.run(game_scene)

    def quit_game(self):
        exit(1)


class Game(cocos.layer.Layer):
    """Main Layer that the background, wall, and zombies layer are attached to"""
    def __init__(self):
        super(Game, self).__init__()
        background_sprite = cocos.sprite.Sprite(background, position=(width * 0.5, height * 0.5))
        self.wall_sprite = cocos.sprite.Sprite(castle, position=(1200, 244))
        self.add(background_sprite)
        self.add(self.wall_sprite)
        self.add(ZombieWavesLayer(zombie_num=2, game_layer=self))
        self.add(ExplosionLayer())
        self.wave_count = 1
        self.wall_health = 10

        # Label for Wave count
        wave_str = "Wave: " + str(self.wave_count)
        self.wave_label = cocos.text.Label(wave_str, position=(50, 650), font_size=30, color=(0, 0, 0, 255))
        self.add(self.wave_label)

        # Label for wall_health
        wallhealth_str = "Health: " + str(self.wall_health)
        self.health_label = cocos.text.Label(wallhealth_str, position=(1060, 550), font_size=30, color=(0, 0, 0, 255))
        self.add(self.health_label)

        self.schedule(self.check_health)

    def check_health(self, dt):
        if self.wall_health == 0:
            self.wall_sprite.image = castle_no_door
            lose_label = cocos.text.Label("YOU LOST", position=((width/2)-200, height/2), font_size=50, color=(0, 0, 0, 255))
            self.add(lose_label)
            self.do(cocos.actions.Delay(5) + cocos.actions.CallFunc(self.return_to_menu))

            # forcing this if branch to only be called once
            self.wall_health = 999

        elif self.wall_health < 4:
            self.wall_sprite.image = castle_lot_broke
        elif self.wall_health < 7:
            self.wall_sprite.image = castle_lil_broke

    def return_to_menu(self):
        cocos.director.director.run(menu_scene)


class ZombieWavesLayer(cocos.layer.Layer):
    """"Layer for all zombie sprites"""
    def __init__(self, zombie_num, game_layer):
        super(ZombieWavesLayer, self).__init__()
        self.schedule_interval(self.update, 1 / 60)
        self.zombie_num = zombie_num
        self.game_layer = game_layer
        self.zombies_list = {}
        for i in range(1, self.zombie_num+1):
            speed = random.randint(250, 300)
            rand_x = random.randrange(-200, 0, 25)
            zombie_sprite = ZombieSprite(i, walk_anim, (rand_x, 175), speed * 0.1, self, self.game_layer)
            self.zombies_list[i] = zombie_sprite
            self.add(zombie_sprite)

    def update(self, dt):
        if len(self.get_children()) == 0:
            self.zombie_num = self.zombie_num + 2
            self.game_layer.wave_count = self.game_layer.wave_count + 1
            self.new_wave(self.zombie_num)

            # Update Wave counter and Label
            self.game_layer.remove(self.game_layer.wave_label)
            wave_str = "Wave: " + str(self.game_layer.wave_count)
            self.game_layer.wave_label = cocos.text.Label(wave_str, position=(50, 650), font_size=30, color=(0, 0, 0, 255))
            game_layer.add(self.game_layer.wave_label)

    def new_wave(self, zombie_num):
        self.zombies_list = {}
        wave = self.game_layer.wave_count
        for i in range(1, zombie_num+1):
            speed = random.randint(250, 300)
            rand_x = random.randrange(-1000, 0, 25)
            print(rand_x)
            zombie_sprite = ZombieSprite(i, walk_anim, (rand_x, 175), speed * (wave * 0.2), self, self.game_layer)
            self.zombies_list[i] = zombie_sprite
            self.add(zombie_sprite)


class ZombieSprite(cocos.sprite.Sprite):
    """Zombie Sprites"""
    def __init__(self, id, image, pos, speed, zombie_layer, game_layer):
        super(ZombieSprite, self).__init__(image)
        self.id = id
        self.image = image
        self.position = pos
        self.velocity = (0, 0)
        self.scale = .25

        self.zombie_layer = zombie_layer
        self.game_layer = game_layer

        self.health = 3
        self.health_bar = HealthBar(0, 255, 0, 255, self.health)
        self.health_bar.position = (-90, 200)
        self.health_bar.width = 200
        self.health_bar.height = 50
        self.add(self.health_bar)

        self.do(Mover(speed))
        self.schedule_interval(self.update, 1 / 60)
        window.push_handlers(self.on_mouse_press)

    def does_contain_point(self, pos):
        return (
                (abs(pos[0] - self.position[0]) < (self.width - 25) / 2) and
                (abs(pos[1] - self.position[1]) < (self.width - 25) / 2))

    def on_mouse_press(self, x, y, buttons, modifiers):
        px, py = director.get_virtual_coordinates(x, y)
        if self.does_contain_point((x, y)):
            self.on_processed_touch(x, y, buttons, modifiers)

    def on_processed_touch(self, x, y, buttons, modifiers):
        # Move zombie offscreen before removing it from scene
        self.health = self.health - 1
        if self.health == 0:
            self.position = (-1000, -1000)
            self.stop()
            self.kill()
            del self.zombie_layer.zombies_list[self.id]

    def update(self, dt):
        # check collision with wall
        if self.position[0] >= 1060:

            self.stop()
            # Move zombie offscreen before removing it from scene
            self.position = (-1000, -1000)
            self.kill()

            # Wall health
            self.game_layer.remove(self.game_layer.health_label)
            if self.game_layer.wall_health != 0:
                self.game_layer.wall_health = self.game_layer.wall_health - 1
            wallhealth_str = "Health: " + str(self.game_layer.wall_health)
            self.game_layer.health_label = cocos.text.Label(wallhealth_str, position=(1060, 550), font_size=30, color=(0, 0, 0, 255))
            self.game_layer.add(self.game_layer.health_label)

            del self.zombie_layer.zombies_list[self.id]


class HealthBar(cocos.layer.ColorLayer):
    def __int__(self,  r, g, b, a, max_health):
        super(HealthBar, self).__init__(r, g, b, a, width, height)


class BoomSprite(cocos.sprite.Sprite):
    """Explosion sprite"""
    def __init__(self, x, y, image):
        super(BoomSprite, self).__init__(image)
        self.image = image
        self.position = (x, y)
        self.scale = 1
        self.game_layer = game_layer
        self.duration = len(boom_texture_list) * 0.05

    def disappear(self):
        self.kill()


class ExplosionLayer(cocos.layer.Layer):
    """Layer to place all the explosions"""
    def __init__(self):
        super(ExplosionLayer, self).__init__()
        window.push_handlers(self.on_mouse_press)

    def on_mouse_press(self, x, y, buttons, modifiers):
        px, py = director.get_virtual_coordinates(x, y)
        boom = BoomSprite(px, py, boom_anim)
        self.add(boom)
        self.do(cocos.actions.Delay(boom.duration) + cocos.actions.CallFunc(boom.disappear))


class Mover(cocos.actions.Move):
    def __init__(self, speed):
        super(Mover, self).__init__()
        self.speed = speed

    def step(self, dt):
        super().step(dt)
        vel_x = self.speed
        vel_y = 0
        self.target.velocity = (vel_x, vel_y)


if __name__ == "__main__":
    menu = Menu()
    menu_scene = cocos.scene.Scene()
    menu_scene.add(menu)
    cocos.director.director.run(menu_scene)
