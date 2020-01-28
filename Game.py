import cocos
import pyglet


class Game(object):
    title = "Game"
    width = 1024
    height = 768

    def __init__(self):
        super(Game, self).__init__()
        cocos.director.director.init(
            Game.width, Game.height,
            caption=Game.title, fullscreen=False)
        background = cocos.layer.ColorLayer(0, 0, 0, 1, Game.width, Game.height)
        self.scene = cocos.scene.Scene(background)

    def run(self):
        cocos.director.director.run(self.scene)


if __name__ == "__main__":
    game = Game()
    game.run()
