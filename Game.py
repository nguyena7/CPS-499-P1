import cocos
import cocos.collision_model
import cocos.euclid
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
zombie_dead = pyglet.resource.image('dead_spritesheet.png')
castle = pyglet.resource.image('wall_good.png')
castle_lil_broke = pyglet.resource.image('wall_lil_broke.png')
castle_lot_broke = pyglet.resource.image('wall_lotta_broke.png')
castle_no_door = pyglet.resource.image('wall_no_door.png')
background = pyglet.resource.image('background.png')
explosion = pyglet.resource.image('explosionSmall.png')
paul = pyglet.resource.image('paul.png')
paul2 = pyglet.resource.image('paul2.png')
fire = pyglet.resource.image('fires.png')
head_paul = pyglet.resource.image('headpaul.png')

# Dividing Spritesheets
walk_grid = pyglet.image.ImageGrid(zombie_walk, 1, 10)
dead_grid = pyglet.image.ImageGrid(zombie_dead, 1, 9)
boom_grid = pyglet.image.ImageGrid(explosion, 5, 5)
fire_grid = pyglet.image.ImageGrid(fire, 3, 3)

# Convert to texture grid
walk_texture = pyglet.image.TextureGrid(walk_grid)
walk_texture_list = walk_texture[:]
dead_texture = pyglet.image.TextureGrid(dead_grid)
dead_texture_list = dead_texture[:]
boom_texture = pyglet.image.TextureGrid(boom_grid)
boom_texture_list = boom_texture[:]
fire_texture = pyglet.image.TextureGrid(fire_grid)
fire_texture_list = fire_texture[6:9] + fire_texture[3:6] + fire_texture[3:6] + fire_texture[0:3]
#fire_texture_list = fire_texture[:]

# Get Animation Objects
walk_anim = pyglet.image.Animation.from_image_sequence(walk_texture_list, 0.1, loop=True)
boom_anim = pyglet.image.Animation.from_image_sequence(boom_texture_list, 0.05, loop=False)
dead_anim = pyglet.image.Animation.from_image_sequence(dead_texture_list, 0.1, loop=False)
fire_anim = pyglet.image.Animation.from_image_sequence(fire_texture_list, 0.1, loop=True)

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
        game_scene = cocos.scene.Scene(game_layer)
        cocos.director.director.run(game_scene)

    def quit_game(self):
        exit(1)


class FriendsLayer(cocos.layer.Layer):
    def __init__(self):
        super(FriendsLayer, self).__init__()
        #self.add(PaulSprite(paul))

class Collisions:
    def __init__(self):
        self.col_manager = cocos.collision_model.CollisionManagerBruteForce()


class Game(cocos.layer.Layer):
    """Main Layer that the background, wall, and zombies layer are attached to"""

    def __init__(self):
        super(Game, self).__init__()

        background_sprite = cocos.sprite.Sprite(background, position=(width * 0.5, height * 0.5))
        self.wall_sprite = cocos.sprite.Sprite(castle, position=(1200, 244))
        self.add(background_sprite)
        self.add(Buttons(255, 255, 0, 255, 500, 100))
        self.add(self.wall_sprite)
        self.add(ZombieWavesLayer(zombie_num=2))
        self.add(FriendsLayer())
        self.add(ExplosionLayer())
        self.wave_count = 1
        self.wall_health = 10
        self.money = 0

        # Label for money
        money_str = "$" + str(self.money)
        self.money_label = cocos.text.Label(text=money_str, position=(600, 650), font_size=30, color=(0, 0, 0, 255))
        self.add(self.money_label)

        # Label for Wave count
        wave_str = "Wave: " + str(self.wave_count)
        self.wave_label = cocos.text.Label(wave_str, position=(50, 650), font_size=30, color=(0, 0, 0, 255))
        self.add(self.wave_label)

        # Label for wall_health
        wallhealth_str = "Health: " + str(self.wall_health)
        self.health_label = cocos.text.Label(wallhealth_str, position=(1060, 550), font_size=30, color=(0, 0, 0, 255))
        self.add(self.health_label)

        self.schedule(self.updates)

    def updates(self, dt):
        # Check wall health
        if self.wall_health == 0:
            self.wall_sprite.image = castle_no_door
            lose_label = cocos.text.Label("YOU LOST", position=((width / 2) - 200, height / 2), font_size=50,
                                          color=(0, 0, 0, 255))
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

    def __init__(self, zombie_num):
        super(ZombieWavesLayer, self).__init__()
        self.schedule_interval(self.update, 1 / 60)
        self.zombie_num = zombie_num
        self.zombies_list = {}
        self.sorted_zombies = []

        self.spawn_zombies(zombie_num, 1)

        # Sorting the zombies by their y position so that zombies lower on the screen do not overlap the zombies higher
        # up the screen
        self.sorted_zombies.sort(key=lambda x: x.position[1], reverse=True)
        for zombie in self.sorted_zombies:
            self.add(zombie)

    def update(self, dt):
        if len(self.get_children()) == 0:
            self.zombie_num = self.zombie_num + 2
            game_layer.wave_count = game_layer.wave_count + 1
            self.new_wave(self.zombie_num)

            # Update Wave counter and Label
            game_layer.wave_label.element.text = "Wave: " + str(game_layer.wave_count)

    def new_wave(self, zombie_num):
        self.zombies_list = {}
        self.sorted_zombies = []
        wave = game_layer.wave_count

        self.spawn_zombies(zombie_num, wave)

        # Sorting the zombies by their y position so that zombies lower on the screen do not overlap the zombies higher
        # up the screen
        self.sorted_zombies.sort(key=lambda x: x.position[1], reverse=True)
        for zombie in self.sorted_zombies:
            i = 1
            self.add(zombie, z=i)
            i = i + 1

    def spawn_zombies(self, zombie_num, wave):
        for i in range(1, zombie_num + 1):
            speed = random.randint(250, 300)
            rand_x = random.randrange(-800, 0, 25)
            rand_y = random.randrange(70, 175, 10)
            zombie_sprite = ZombieSprite(i, walk_anim, (rand_x, rand_y), speed, self)
            self.zombies_list[i] = zombie_sprite
            self.sorted_zombies.append(zombie_sprite)
            collisions.col_manager.add(zombie_sprite)


class ZombieSprite(cocos.sprite.Sprite):
    """Zombie Sprites"""
    def __init__(self, id, image, pos, speed, zombie_layer):
        super(ZombieSprite, self).__init__(image)
        self.name = "zombie"
        self.id = id
        self.image = image
        self.position = pos
        self.velocity = (0, 0)
        self.scale = .25

        self.zombie_layer = zombie_layer

        self.max_health = 5
        self.health = self.max_health
        self.health_bar_red = HealthBar(255, 0, 0, 255, 200, 50)
        self.health_bar_red.position = (-90, 200)
        self.add(self.health_bar_red)

        self.health_bar_green = HealthBar(0, 255, 0, 255, 200, 50)
        self.health_bar_green.position = (-90, 200)
        self.add(self.health_bar_green)

        self.cshape = cocos.collision_model.AARectShape(cocos.euclid.Vector2(*self.position), self.width / 2,
                                                         self.height / 2)

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
        # Reduce Health bar
        self.health = self.health - 1
        self.health_bar_green.reduce_health(self.max_health)
        self.check_health()

    def check_health(self):
        if self.health <= 0:
            self.health = 9999
            game_layer.money = game_layer.money + 100
            game_layer.money_label.element.text = "$" + str(game_layer.money)
            self.health_bar_green.opacity = 0
            self.health_bar_red.opacity = 0
            self.stop()
            self.image = dead_anim
            # self.position = (self.position[0], 165)
            self.do(actions.Delay(3) + actions.CallFunc(self.remove_sprite))

    def remove_sprite(self):
        self.position = (-1000, -1000)
        collisions.col_manager.remove_tricky(self)
        self.kill()
        del self.zombie_layer.zombies_list[self.id]

    def update(self, dt):
        # Collision Detection
        if collisions.col_manager.objs_colliding(self):
            print("pos: " + str(self.position) + " COLLIDING")

        # check collision with wall
        if self.position[0] >= 1060:
            # Move zombie offscreen before removing it from scene
            self.stop()
            self.remove_sprite()
            # Wall health
            if game_layer.wall_health != 0:
                game_layer.wall_health = game_layer.wall_health - 1
            wallhealth_str = "Health: " + str(game_layer.wall_health)
            game_layer.health_label.element.text = wallhealth_str


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


class HealthBar(cocos.layer.ColorLayer):

    def __init__(self, r, g, b, a, w, h):
        super(HealthBar, self).__init__(r, g, b, a, w, h)
        self.maxwidth = w

    def reduce_health(self, max_health):
        self.width = self.width - (self.maxwidth / max_health)
        if self.width < 0:
            self.width = 0
        # Updating the vertices, idk why. found this code online
        x, y = int(self.width), int(self.height)
        ox, oy = 0, 0
        self._vertex_list.vertices[:] = [ox, oy, ox, oy + y, ox + x, oy + y, ox + x, oy]


class PaulSprite(cocos.sprite.Sprite):
    def __init__(self, image):
        super(PaulSprite, self).__init__(image)
        self.name = "paul"
        self.scale = 0.1
        self.position = (1000, 200)
        self.velocity = (0, 0)

        self.fire_sprite = cocos.sprite.Sprite(fire_anim)
        self.fire_sprite.scale = 20
        self.fire_sprite.scale_x = -1
        self.fire_sprite.position = (-3000, -200)
        self.fire_sprite.rotation = -25

        self.loop_breath_fire()

        self.cshape = cocos.collision_model.AARectShape(cocos.euclid.Vector2(*self.position), (self.width + 500) / 2,
                                                        self.height / 2)
        self.do_movements()

        self.schedule_interval(self.update, 1/60)

    def loop_breath_fire(self):
        #self.do(cocos.actions.Delay(2) + cocos.actions.CallFunc(self.breath_fire) + cocos.actions.Delay(3) +
        #        cocos.actions.CallFunc(self.stop_breathing_fire) + cocos.actions.CallFunc(self.loop_breath_fire))
        self.do(cocos.actions.CallFunc(self.breath_fire) + cocos.actions.Delay(3) +
                cocos.actions.CallFunc(self.loop_breath_fire))

    def breath_fire(self):
        self.image = paul2
        self.add(self.fire_sprite)

    def stop_breathing_fire(self):
        self.image = paul
        self.remove(self.fire_sprite)

    def do_movements(self):
        #self.do(cocos.actions.interval_actions.MoveBy((-800, 0), 5) + cocos.actions.CallFunc(self.flip_sprite) +
        #        cocos.actions.interval_actions.MoveBy((800, 0), 5) + cocos.actions.CallFunc(self.flip_sprite) +
        #        cocos.actions.CallFunc(self.do_movements))
        self.do(cocos.actions.interval_actions.MoveBy((-1200, 0), 5) + cocos.actions.CallFunc(self.remove_sprite))

    def remove_sprite(self):
        self.kill()

    def flip_sprite(self):
        self.scale_x = self.scale_x * -1

    def update(self, dt):
        self.cshape.center = self.position
        for obj in collisions.col_manager.iter_colliding(self):
            if obj.name == "zombie":
                self.do(cocos.actions.Delay(1))
                obj.health_bar_green.reduce_health(obj.max_health)
                obj.health -= 1
                obj.check_health()
                print(obj.health)
                print("PAUL TOUCHING ZOMBIE: " + str(obj))


class Mover(cocos.actions.Move):
    def __init__(self, speed):
        super(Mover, self).__init__()
        self.speed = speed

    def step(self, dt):
        super().step(dt)
        vel_x = self.speed
        vel_y = 0
        self.target.velocity = (vel_x, vel_y)
        self.target.cshape.center = cocos.euclid.Vector2(*self.target.position)
        #print(self.target.cshape.center)


# Buttons are drawn on this layer
class Buttons(cocos.layer.ColorLayer):
    def __init__(self, r, g, b, a, w, h):
        super(Buttons, self).__init__(r, g, b, a, w, h)
        self.w = w
        self.h = h
        self.position = (775, 610)
        self.add(cocos.text.Label("Shop", color=(0, 0, 0, 255)))

        # Buy Paul Button
        paulbutt = PaulButton(0, 200, 0, 255, 90, 90, self)
        paulbutt.worldpos = self.point_to_world(paulbutt.position)
        self.add(paulbutt)

    def show_buttons(self, button):
        self.add(button)


# Different buttons use this class to handle mouse presses
class ButtonHandler(cocos.layer.ColorLayer):
    def __init__(self, r, g, b, a, w, h):
        super(ButtonHandler, self).__init__(r, g, b, a, w, h)
        window.push_handlers(self.on_mouse_press)

        #Getting the world position instead of relative position within a layer
        self.worldpos = (0, 0)

    def does_contain_point(self, pos):
        #print("mouse: ", pos)
        #print("button: ", self.position)
        #print("x: ", self.worldpos[0], " y: ", self.worldpos[1])
        return (
                (abs(pos[0]) < (self.worldpos[0] + self.width)) and
                (abs(pos[0]) > (self.worldpos[0]) and
                (abs(pos[1]) < (self.worldpos[1] + self.height))) and
                (abs(pos[1]) > (self.worldpos[1])))

    def on_mouse_press(self, x, y, buttons, modifiers):
        px, py = director.get_virtual_coordinates(x, y)
        if self.does_contain_point((x, y)):
            self.on_processed_touch(x, y, buttons, modifiers)

    def on_processed_touch(self, x, y, buttons, modifiers):
        pass


class PaulButton(ButtonHandler):
    def __init__(self, r, g, b, a, w, h, buttons_layer):
        super(PaulButton, self).__init__(r, g, b, a, w, h)
        self.position = (405, 5)
        self.width = w
        self.height = h
        self.price = 0000
        paul_icon = cocos.sprite.Sprite(head_paul, (self.width/2, self.height/2))
        paul_icon.scale = 0.085
        self.add(paul_icon)
        paul_price = cocos.text.Label("$"+str(self.price), (0, 0), color=(0, 0, 0, 255))
        self.add(paul_price)

    def on_processed_touch(self, x, y, buttons, modifiers):
        if game_layer.money >= self.price:
            game_layer.money = game_layer.money - self.price
            game_layer.money_label.element.text = "$" + str(game_layer.money)
            paul_sprite = PaulSprite(paul)
            game_layer.add(paul_sprite)
            collisions.col_manager.add(paul_sprite)


if __name__ == "__main__":
    collisions = Collisions()
    game_layer = Game()
    menu = Menu()
    menu_scene = cocos.scene.Scene()
    menu_scene.add(menu)
    cocos.director.director.run(menu_scene)
