#!/usr/bin/python3

from collections import namedtuple
from random import randint
import argparse
import curses
import time
import os


def list_match(a, b):
    return bool(set(a).intersection(b))


Point = namedtuple("Point", ["x", "y"])


def rand_point(x_min, x_max, y_min, y_max):
    return Point(randint(x_min, x_max), randint(y_min, y_max))


def point_inside(point, min_point, max_point):
    return ((point.x >= min_point.x) and
            (point.y >= min_point.y)) and ((point.x <= max_point.x) and
                                           (point.y <= max_point.y))


# Irányok:
x_p, x_m, y_p, y_m = 0, 1, 2, 3


def next_point(direction, point):
    x, y = point.x, point.y
    if direction == x_p: x += 1
    if direction == x_m: x -= 1
    if direction == y_p: y += 1
    if direction == y_m: y -= 1
    return Point(x, y)


def make_line(direction, point, length=1):
    line = [point]
    for i in range(length - 1):
        line.append(next_point(direction, line[-1]))
    return line


class Snake:
    direction = x_p
    apples, barrier, body = [], [], []

    def __init__(self,
                 arena_min,
                 arena_max,
                 use_barrier=True,
                 barrier_min_num=3,
                 barrier_max_num=5,
                 barrier_min_len=8,
                 barrier_max_len=16,
                 barrier_margin=1,
                 apples_min=1,
                 apples_max=3,
                 body_len=5):
        self.arena_min = arena_min
        self.arena_max = arena_max
        self.body = make_line(self.direction, arena_min, body_len)
        if use_barrier:
            self.set_barrier(barrier_min_num, barrier_max_num, barrier_min_len,
                             barrier_max_len, barrier_margin)
        self.apples_min = apples_min
        self.apples_max = apples_max
        self.set_apples(apples_min, apples_max)

    def get_head(self):
        return self.body[-1]

    def set_apples(self, apples_min, apples_max):
        apples_num = randint(apples_min, apples_max)
        i = 0
        while i != apples_num:
            p = rand_point(self.arena_min.x, self.arena_max.x,
                           self.arena_min.y, self.arena_max.y)
            if p != self.get_head() and p not in self.barrier:
                self.apples.append(p)
                i += 1

    def set_barrier(self, barrier_min_num, barrier_max_num, barrier_min_len,
                    barrier_max_len, barrier_margin):
        barrier_margin = abs(barrier_margin)
        snake = self.body + make_line(
            self.direction, next_point(self.direction, self.get_head()),
            len(self.body) * 2)
        area_min = Point(self.arena_min.x + barrier_margin,
                         self.arena_min.y + barrier_margin)
        area_max = Point(self.arena_max.x - barrier_margin,
                         self.arena_max.y - barrier_margin)
        barrier_num = randint(barrier_min_num, barrier_max_num)
        i = 0
        while i != barrier_num:
            rand_line = make_line(
                randint(x_p, y_m),
                rand_point(area_min.x, area_max.x, area_min.y, area_max.y),
                randint(barrier_min_len, barrier_max_len))
            inside = True
            for p in rand_line:
                if not point_inside(p, area_min, area_max):
                    inside = False
                    break
            if inside and not list_match(snake, rand_line) and not list_match(
                    self.barrier, rand_line):
                self.barrier += rand_line
                i += 1

    def set_direction(self, direction):
        if self.direction == x_p or self.direction == x_m:
            if direction == y_p:
                self.direction = y_p
            if direction == y_m:
                self.direction = y_m
        if self.direction == y_p or self.direction == y_m:
            if direction == x_p:
                self.direction = x_p
            if direction == x_m:
                self.direction = x_m

    def hit(self, refill=True, auto_extend=True):
        i = 0
        for apple in self.apples:
            if apple == self.get_head():
                self.apples.remove(apple)
                if auto_extend:
                    self.extend()
                return True
            i += 1
        if i == 0 and refill:
            self.set_apples(self.apples_min, self.apples_max)
        return False

    def crash(self):
        head = self.get_head()
        if not point_inside(
                head, self.arena_min, self.arena_max
        ) or head in self.barrier or head in self.body[:-1]:
            return True
        return False

    def move(self):
        self.body.pop(0)
        self.body.append(next_point(self.direction, self.get_head()))

    def extend(self):
        back = self.body[0]
        prev = self.body[1]
        x, y = back
        if back.x == prev.x: y - 1
        if back.y == prev.y: x - 1
        self.body.insert(0, Point(x, y))


class Toggle:
    ci = 0

    def __init__(self, o):
        self.set(o)

    def set(self, o):
        self.o = o
        self.li = len(o) - 1

    def get(self):
        return self.o[self.ci]

    def jmp(self, v):
        try:
            self.ci = self.o.index(v)
        except:
            pass

    def toggle(self):
        ni = self.ci + 1
        if ni > self.li: self.ci = 0
        else: self.ci = ni


CH_APPLES = "+"
CH_BARRIER = "x"
CH_SNAKE = "o"
KEY_SPACE = ord(" ")
KEY_S_LOWER = ord("s")
KEY_S_UPPER = ord("S")
KEY_Q_LOWER = ord("q")
KEY_Q_UPPER = ord("Q")


def main(stdscr):
    score = 0
    race = Toggle((True, False))
    speed = Toggle((0.06, 0.05, 0.04, 0.03))
    shorter = min(curses.COLS, curses.LINES)
    snake = Snake(Point(0, 0),
                  Point(curses.COLS - 1, curses.LINES - 1),
                  barrier_min_len=shorter // 4,
                  barrier_max_len=shorter // 2)
    curses.curs_set(0)
    curses.noecho()
    while True:
        stdscr.nodelay(race.get())
        stdscr.erase()
        try:
            for p in snake.barrier:
                stdscr.addstr(p.y, p.x, CH_BARRIER)
            for p in snake.apples:
                stdscr.addstr(p.y, p.x, CH_APPLES)
            for p in snake.body:
                stdscr.addstr(p.y, p.x, CH_SNAKE)
        except curses.error:
            pass
        if not race.get():
            paused_msg = " Paused. Score: " + str(score) + " "
            try:
                stdscr.addstr((curses.LINES // 2) + 1,
                              (curses.COLS // 2) - (len(paused_msg) // 2),
                              paused_msg, curses.A_REVERSE)
            except curses.error:
                pass
        press = stdscr.getch()
        if press == curses.KEY_RESIZE: return
        if press == KEY_SPACE: race.toggle()
        if press == KEY_S_LOWER or press == KEY_S_UPPER: speed.toggle()
        if press == KEY_Q_LOWER or press == KEY_Q_UPPER: return
        if race.get():
            if press == curses.KEY_UP: snake.set_direction(y_m)
            if press == curses.KEY_DOWN: snake.set_direction(y_p)
            if press == curses.KEY_LEFT: snake.set_direction(x_m)
            if press == curses.KEY_RIGHT: snake.set_direction(x_p)
            snake.move()
        if snake.hit(): score += 1
        if snake.crash(): break
        timing = speed.get()
        # Időzítés korrekciója:
        if snake.direction == y_p or snake.direction == y_m:
            timing = timing * ((curses.LINES / curses.COLS) + 1)
        time.sleep(timing)
    while True:
        go_msg = " Game over! Score: " + str(score) + " "
        try:
            stdscr.addstr((curses.LINES // 2) + 1,
                          (curses.COLS // 2) - (len(go_msg) // 2), go_msg,
                          curses.A_REVERSE)
        except curses.error:
            pass
        stdscr.nodelay(False)
        press = stdscr.getch()
        if press == KEY_Q_LOWER or press == KEY_Q_UPPER: return


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        exit(0)
