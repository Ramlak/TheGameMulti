__author__ = 'Kalmar'
__version__ = '0.1'

from socket import socket, AF_INET, SOCK_DGRAM, IPPROTO_UDP, timeout
from struct import pack, unpack
from math import cos, sin
import settings


class Bullet(object):
    x = 0
    y = 0
    v_x = 0
    v_y = 0
    alive = None
    owner_nr = None

    def __init__(self, player):
        self.owner_nr = player.player_nr
        self.x = player.x + 1.0 * settings.BLOCK_SIZE / 2 + cos(player.angle) * settings.BLOCK_SIZE / 2 * settings.GUN_SIZE - 1
        self.y = player.y + 1.0 * settings.BLOCK_SIZE / 2 - sin(player.angle) * settings.BLOCK_SIZE / 2 * settings.GUN_SIZE - 1
        self.v_x = settings.BULLET_SPEED * cos(player.angle)
        self.v_y = 0 - settings.BULLET_SPEED * sin(player.angle)
        self.alive = True

    def move(self):
        self.x += self.v_x
        self.y += self.v_y


class Player(object):
    x = None
    y = None
    angle = None
    hp = settings.HP
    ammo = settings.AMMO
    alive = True
    shot = False
    full = True
    player_nr = None
    counter = 0

    def shoot(self):
        self.full = False
        self.ammo -= 1
        return Bullet(self)

    def hit(self, bullet):
        if not self.alive:
            return False
        return (bullet.x >= self.x) and (bullet.x <= (self.x + settings.BLOCK_SIZE)) and (bullet.y >= self.y) and (bullet.y <= self.y + settings.BLOCK_SIZE)


class Conversation(object):
    sock = None
    pin = None
    command_set = dict(MOVE_RIGHT=0, MOVE_LEFT=1, MOVE_UP=2, MOVE_DOWN=3, ROT_RIGHT=4, ROT_LEFT=5, SHOOT=6)
    flags = dict(ALIVE=0, SHOT=1, FULL=2)

    def __init__(self):
        self.pin = pack("I", settings.PIN)
        self.fps = settings.FPS
        self.sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        self.sock.connect((settings.IP, settings.PORT))
        self.sock.settimeout(1.0 / settings.FPS * 2)

    def get_flags(self, flag_name, byte):
        return ((byte >> self.flags[flag_name]) & 1) == 1

    def parse_server(self, buf, old_players):
        n = ord(buf[0])
        preserve = False
        if old_players:
            if len(old_players) == n:
                preserve = True

        players = []
        for i in xrange(n):
            tmp = buf[(1+12*i):(1+12*(i+1))]
            pl = Player()
            if preserve:
                pl.ammo = old_players[i].ammo
                pl.counter = old_players[i].counter
            pl.player_nr = i
            pl.x = unpack("H", tmp[:2])[0]
            pl.y = unpack("H", tmp[2:4])[0]
            pl.angle = unpack("f", tmp[4:8])[0]
            pl.hp = unpack("H", tmp[8:10])[0]
            flags = unpack("H", tmp[10:12])[0]
            pl.alive = self.get_flags("ALIVE", flags)
            pl.shot = self.get_flags("SHOT", flags)
            pl.full = self.get_flags("FULL", flags)
            players.append(pl)
        return players

    def parse_command(self, commands):
        com = 0
        for i in commands:
            try:
                com |= (1 << self.command_set[i])
            except KeyError:
                print "\rparse_client: wrong command"
        return com

    def prepare_buf(self, command):
        return self.pin + chr(command & 0xff)

    def parse_client(self, commands):
        if isinstance(commands, int):
            return self.prepare_buf(commands)
        com = self.parse_command(commands)
        return self.prepare_buf(com)

    def get_players(self, old_players=None):
        try:
            buf = self.sock.recv(4096)
            return self.parse_server(buf, old_players)
        except timeout:
            print "\rget_players: connection timed out"
            return None

    def send_commands(self, commands=()):
        self.sock.sendall(self.parse_client(commands))

    def hello(self):
        self.send_commands()