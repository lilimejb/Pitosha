import pygame as pg
import random
from math import sin, radians

from config import *

COIN_CHECK_EVENT = pg.USEREVENT + 1
pg.time.set_timer(COIN_CHECK_EVENT, 5000)


class Sprite(pg.sprite.Sprite):
    def __init__(self, x=0, y=0, size=100, speed=10, image=PLAYER_ASSETS['idle'][0]):
        pg.sprite.Sprite.__init__(self)
        self.size = size
        self.speed = speed
        self.x = x
        self.y = y
        self.image = pg.image.load(image)
        self.image = pg.transform.scale(self.image, (self.size, self.size))
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(x, y)

    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)

    def update(self, *args):
        pass


class Coin(Sprite):
    def __init__(self, x=None, y=None, value=5, size=50, speed=10, image=COINS[0]):
        if x is None:
            self.x = random.randint(0, WIN_SIZE[0] - size)
        else:
            self.x = x
        if y is None:
            self.y = random.randint(0, WIN_SIZE[1] - size)
        else:
            self.y = y
        super().__init__(self.x, self.y, size, speed, image)
        self.ticks = random.choice(range(0, 360, 5))
        self.forward = 1
        self.spawn = self.rect.topleft
        self.value = value

    def update(self, *args):
        if self.ticks >= 360:
            self.ticks -= 360
        self.ticks += 5
        if not self.speed:
            return
        not_true_y = sin(radians(self.ticks)) * self.speed
        self.rect.y = self.spawn[1] + not_true_y


class Spike(Sprite):
    def __init__(self, x=None, y=None, damage=100, size=100, speed=10, image=SPIKE):
        if x is None:
            self.x = random.randint(0, WIN_SIZE[0] - size)
        else:
            self.x = x
        if y is None:
            self.y = random.randint(0, WIN_SIZE[1] - size)
        else:
            self.y = y
        Sprite.__init__(self, self.x, self.y, size, speed, image)
        self.damage = damage


class Medkit(Sprite):
    def __init__(self, x=None, y=None, healing=500, size=50, speed=10, image=FOOD[0]):
        if x is None:
            self.x = random.randint(0, WIN_SIZE[0] - size)
        else:
            self.x = x
        if y is None:
            self.y = random.randint(0, WIN_SIZE[1] - size)
        else:
            self.y = y
        Sprite.__init__(self, self.x, self.y, size, speed, image)
        self.heal = healing

        self.ticks = random.choice(range(0, 360, 5))
        self.forward = 1
        self.spawn = self.rect.topleft

    def update(self, *args):
        if self.ticks >= 360:
            self.ticks -= 360
        self.ticks += 5
        if not self.speed:
            return
        not_true_y = sin(radians(self.ticks)) * self.speed
        self.rect.y = self.spawn[1] + not_true_y


class Player(Sprite):
    coins = None
    spikes = None
    medkits = None
    solid_blocks = None

    def __init__(self, x=300, y=300, size=80, speed=0, image=PLAYER_ASSETS['idle'][0]):
        self.money = 0
        self.hp_max = 1200
        self.hp_start = self.hp_max - 200
        self.hp = self.hp_start
        self.x = x
        self.y = y
        Sprite.__init__(self, self.x, self.y, size, speed, image)
        self.image_true = self.image
        self.image_flipped = pg.transform.flip(self.image, True, False)
        self.delay = 1000
        self.cooldown = self.delay
        self.acceleration = .1
        self.speed_y = 0
        self.speed_x = 0
        self.on_the_ground = False
        self.jump_power = 10

    def update(self, up, down, left, right, ms):
        self.move(up, down, left, right)
        self.collide_check(ms)
        print(self.rect.x, self.rect.y, self.on_the_ground, self.speed_y, self.speed_x)
        if self.hp <= 0:
            self.respawn()
        if self.hp > self.hp_max:
            self.hp = self.hp_max

    def move(self, up, down, left, right):
        if up == down:
            pass
        if not self.on_the_ground:
            self.speed_y += GRAVITY
        else:
            self.speed_y = 0
        if up and self.on_the_ground:
            self.speed_y -= self.jump_power
            self.on_the_ground = False
        self.rect.bottom += self.speed_y
        for block in self.solid_blocks:
            if pg.sprite.collide_rect(self, block):
                if self.speed_y < 0:
                    self.rect.top = block.rect.bottom
                    self.speed_y = 0
                else:
                    self.rect.bottom = block.rect.top
                    self.on_the_ground = True

        if left == right:
            self.speed_x = 0
        elif left:
            self.speed_x -= self.acceleration
            self.image = self.image_flipped
        else:
            self.speed_x += self.acceleration
            self.image = self.image_true
        self.rect.x += self.speed_x
        for block in self.solid_blocks:
            if pg.sprite.collide_rect(self, block):
                if self.speed_x < 0:
                    self.rect.left = block.rect.right
                    self.speed_x = 0
                else:
                    self.rect.right = block.rect.left
                    self.speed_x = 0

    def collide_check(self, ms):
        for coin in self.coins:
            if pg.sprite.collide_rect(self, coin):
                self.money += coin.value
                coin.kill()

        # TODO шипы твёрдый блок. поменять!
        for spike in self.spikes:
            if pg.sprite.collide_rect(self, spike):
                self.hp -= self.take_damage(ms, spike.damage)

        for medkit in self.medkits:
            if pg.sprite.collide_rect(self, medkit):
                self.hp += medkit.heal
                medkit.kill()

    def take_damage(self, ms, damage):
        if self.cooldown > 0:
            self.cooldown -= ms
            return 0
        if self.cooldown <= 0:
            self.cooldown = 0
        if self.cooldown == 0:
            self.cooldown = self.delay
            return damage

    def respawn(self):
        self.money = self.money // 10
        self.hp = self.hp_start
        self.rect.topleft = (self.x, self.y)
        self.image = self.image_true


class Game:
    def __init__(self):
        pg.init()
        self.display = pg.display.set_mode(WIN_SIZE)
        self.bg_image = pg.image.load(BACKGROUNDS)
        self.bg_image = pg.transform.scale(self.bg_image, (WIN_SIZE[0], WIN_SIZE[1]))
        self.clock = pg.time.Clock()
        self.running = True
        self.down = self.up = self.left = self.right = False
        self.objects = pg.sprite.Group()
        self.enemies = pg.sprite.Group()
        self.help = pg.sprite.Group()
        self.coins = pg.sprite.Group()
        self.solid_blocks = pg.sprite.Group()
        self.load_map()
        spike = Spike(image=SPIKE)
        spike.add(self.enemies)
        for coin in self.coins:
            if coin.image == COINS[0]:
                coin.value = 5
            if coin.image == COINS[1]:
                coin.value = 5
            if coin.image == COINS[2]:
                coin.value = 5
            if coin.image == COINS[3]:
                coin.value = 5
            if coin.image == COINS[4]:
                coin.value = 5
        Player.coins = self.coins
        Player.spikes = self.enemies
        Player.solid_blocks = self.solid_blocks
        # for meal in self.help:
        #     meal.image = random.choice(FOOD)
        Player.medkits = self.help
        self.player = Player()

        self.played = 0

    def restart(self):
        self.__init__()

    def load_map(self):
        map_path = 'lvl1.txt'
        with open(map_path, encoding='utf-8') as file:
            for y, line in enumerate(file):
                for x, letter in enumerate(line):
                    if letter in MAP.keys():
                        pos = x * TILE_SIZE, y * TILE_SIZE
                        image = MAP[letter]
                        if letter in SOLID_BLOCKS:
                            block = Sprite(*pos, image=image)
                            self.solid_blocks.add(block)
                            if letter == 'S':
                                block = Spike(*pos, image=image)
                                self.enemies.add(block)
                        elif letter == 'R':
                            block = Coin(*pos, image=image)
                            self.coins.add(block)
                        elif letter == 'B':
                            block = Coin(*pos, image=image)
                            self.coins.add(block)
                        elif letter == 'Z':
                            block = Coin(*pos, image=image)
                            self.coins.add(block)
                        elif letter == 'F':
                            block = Medkit(*pos, image=image)
                            self.help.add(block)
                        self.objects.add(block)

    def run(self):
        while self.running:
            self.events()
            self.update()
            self.render()

    def events(self):
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                self.running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_s:
                    self.down = True
                if event.key == pg.K_w:
                    self.up = True
                if event.key == pg.K_a:
                    self.left = True
                if event.key == pg.K_d:
                    self.right = True
                if event.key == pg.K_r:
                    self.restart()
            if event.type == pg.KEYUP:
                if event.key == pg.K_s:
                    self.down = False
                if event.key == pg.K_w:
                    self.up = False
                if event.key == pg.K_a:
                    self.left = False
                if event.key == pg.K_d:
                    self.right = False
                if event.key == pg.K_ESCAPE:
                    self.running = False
            if event.type == COIN_CHECK_EVENT and not self.coins:
                self.running = False

    def update(self):
        ms = self.clock.tick(FPS)
        self.played += ms / 1000
        pg.display.set_caption(
            f'Player`s money: {self.player.money}, Played time: {self.played:.2f} HP: {self.player.hp}')
        self.player.update(self.up, self.down, self.left, self.right, ms)
        self.coins.update()
        self.help.update()

    def render(self):
        self.display.blit(self.bg_image, (0, 0))
        self.objects.draw(self.display)
        self.player.draw(self.display)
        pg.display.update()


if __name__ == '__main__':
    game = Game()
    game.run()
    pg.quit()
