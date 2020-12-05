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
        self.image_true = self.image
        self.image_flipped = pg.transform.flip(self.image, True, False)
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(x, y)

    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)

    def border_check(self):

        if self.rect.left < 0:
            self.rect.left = 0

        if self.rect.right > WIN_SIZE[0]:
            self.rect.right = WIN_SIZE[0]

        if self.rect.top < 0:
            self.rect.top = 0

        if self.rect.bottom > WIN_SIZE[1]:
            self.rect.bottom = WIN_SIZE[1]

    def update(self, *args):
        pass


class Coin(Sprite):
    def __init__(self, x=None, y=None, value=5, size=50, speed=10, image=COINS[0]):
        if x is None:
            self.x = random.randint(0, WIN_SIZE[0] - size)
        if y is None:
            self.y = random.randint(0, WIN_SIZE[1] - size)
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
        self.delay = 1000
        self.cooldown = self.delay

    def deal_damage(self, ms):
        if self.cooldown > 0:
            self.cooldown -= ms
            return 0
        if self.cooldown <= 0:
            self.cooldown = 0
        if self.cooldown == 0:
            self.cooldown = self.delay
            return self.damage


class Medkit(Sprite):
    def __init__(self, x=None, y=None, healing=500, size=50, speed=10, image=random.choice(FOOD)):
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

    def __init__(self, x=0, y=0, size=100, speed=10, image=PLAYER_ASSETS['idle'][0]):
        self.money = 0
        self.hp_max = 1200
        self.hp_start = self.hp_max - 200
        self.hp = self.hp_start
        self.x = x
        self.y = y
        Sprite.__init__(self, self.x, self.y, size, speed, image)

    def update(self, up, down, left, right, ms):
        if left == right:
            pass
        elif left:
            self.rect.x -= self.speed
            self.image = self.image_flipped
        else:
            self.rect.x += self.speed
            self.image = self.image_true
        if up == down:
            pass
        elif up:
            self.rect.y -= self.speed
        else:
            self.rect.y += self.speed
        self.border_check()

        for coin in self.coins:
            if pg.sprite.collide_rect(self, coin):
                self.money += coin.value
                coin.kill()

        for spike in self.spikes:
            if pg.sprite.collide_rect(self, spike):
                self.hp -= spike.deal_damage(ms)

        for medkit in self.medkits:
            if pg.sprite.collide_rect(self, medkit):
                self.hp += medkit.heal
                medkit.kill()
        if self.hp <= 0:
            self.respawn()
        if self.hp > self.hp_max:
            self.hp = self.hp_max

    def respawn(self):
        self.money = self.money // 10
        self.hp = self.hp_start
        self.rect.topleft = (self.x, self.y)
        self.image = self.image_true


class Game:
    def __init__(self):
        pg.init()
        self.display = pg.display.set_mode(WIN_SIZE)
        self.bg_image_first = pg.image.load(BACKGROUNDS['first'])
        self.bg_image_second = pg.image.load(BACKGROUNDS['second'])
        self.bg_image_first = pg.transform.scale(self.bg_image_first, (WIN_SIZE[0], WIN_SIZE[1]))
        self.bg_image_second = pg.transform.scale(self.bg_image_second, (WIN_SIZE[0], WIN_SIZE[1]))
        self.clock = pg.time.Clock()
        self.running = True
        self.down = self.up = self.left = self.right = False
        self.objects = pg.sprite.Group()
        self.enemies = pg.sprite.Group()
        self.help = pg.sprite.Group()
        self.coins = pg.sprite.Group()
        for _ in range(random.randint(1, 25)):
            image = COINS[random.randint(0, 4)]
            if image == COINS[0]:
                Coin(image=image, value=5).add(self.coins, self.objects)
            if image == COINS[1]:
                Coin(image=image, value=10).add(self.coins, self.objects)
            if image == COINS[2]:
                Coin(image=image, value=15).add(self.coins, self.objects)
            if image == COINS[3]:
                Coin(image=image, value=20).add(self.coins, self.objects)
            if image == COINS[4]:
                Coin(image=image, value=25).add(self.coins, self.objects)
        Player.coins = self.coins
        for _ in range(random.randint(1, 10)):
            Spike().add(self.enemies, self.objects)
        Player.spikes = self.enemies
        self.medkit = Medkit()
        self.medkit.add(self.help, self.objects)
        Player.medkits = self.help
        self.player = Player()
        self.player.add(self.objects)

        self.played = 0

    def restart(self):
        self.__init__()

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
        self.medkit.update()

    def render(self):
        self.display.blit(self.bg_image_first, (0, 0))
        self.display.blit(self.bg_image_second, (0, 0))
        self.objects.draw(self.display)
        pg.display.update()


if __name__ == '__main__':
    game = Game()
    game.run()
    pg.quit()
