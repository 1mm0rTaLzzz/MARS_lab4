import sys, pygame
import numpy as np
import math
import random
import time

sz = (800, 600)

def dist(p1, p2):  # расчет расстояния
    return np.linalg.norm(np.subtract(p1, p2))

def rot(v, ang):  # функция для поворота на угол
    s, c = math.sin(ang), math.cos(ang)
    return [v[0] * c - v[1] * s, v[0] * s + v[1] * c]

def rotArr(vv, ang):  # функция для поворота массива на угол
    return [rot(v, ang) for v in vv]

pygame.font.init()
font = pygame.font.SysFont('Comic Sans MS', 20)

def drawText(screen, s, x, y):
    surf = font.render(s, True, (0, 0, 0))
    screen.blit(surf, (x, y))

def drawRotRect(screen, color, pc, w, h, ang):  # точка центра, ширина высота прямоуг и угол поворота прямогуольника
    pts = [
        [- w / 2, - h / 2],
        [+ w / 2, - h / 2],
        [+ w / 2, + h / 2],
        [- w / 2, + h / 2],
    ]
    pts = rotArr(pts, ang)
    pts = np.add(pts, pc)
    pygame.draw.polygon(screen, color, pts, 2)

class Bullet:
    def __init__(self, x, y, ang, team):
        self.x = x
        self.y = y
        self.ang = ang
        self.vx = 200
        self.L = 10
        self.exploded = False
        self.team = team  # Добавлен атрибут team

    def getPos(self):
        return [self.x, self.y]

    def draw(self, screen):
        p0 = self.getPos()
        p1 = [-self.L / 2, 0]
        p1 = rot(p1, self.ang)
        p2 = [+self.L / 2, 0]
        p2 = rot(p2, self.ang)
        pygame.draw.line(screen, (0, 0, 0), np.add(p0, p1), np.add(p0, p2), 3)

    def sim(self, dt):
        vec = [self.vx, 0]
        vec = rot(vec, self.ang)
        self.x += vec[0] * dt
        self.y += vec[1] * dt

class Tank:
    def __init__(self, id, x, y, ang, team):
        self.id = id
        self.x = x
        self.y = y
        self.ang = ang
        self.angGun = 0
        self.L = 70
        self.W = 45
        self.vx = 0
        self.vy = 0
        self.va = 0
        self.vaGun = 0
        self.health = 100
        self.team = team
        self.active = True
        self.fire_cooldown = 0

    def fire(self, target_pos):
        if self.fire_cooldown > 0:
            return None
        r = self.W / 2.3
        LGun = self.L / 2
        p2 = rot([r + LGun, 0], self.ang + self.angGun)
        p2 = np.add(self.getPos(), p2)
        ang_to_target = math.atan2(target_pos[1] - p2[1], target_pos[0] - p2[0])
        self.angGun = ang_to_target - self.ang  # Обновление угла башни
        b = Bullet(*p2, ang_to_target, self.team)  # Передача team в Bullet
        self.fire_cooldown = 2  # Cooldown in seconds
        return b

    def getPos(self):
        return [self.x, self.y]

    def draw(self, screen):
        pts = [[self.L / 2, self.W / 2], [self.L / 2, -self.W / 2], [-self.L / 2, -self.W / 2], [-self.L / 2,
                                                                                                 self.W / 2]]
        pts = rotArr(pts, self.ang)
        pts = np.add(pts, self.getPos())
        pygame.draw.polygon(screen, (0, 0, 0), pts, 2)
        r = self.W / 2.3
        pygame.draw.circle(screen, (0, 0, 0), self.getPos(), r, 2)
        LGun = self.L / 2
        p0 = self.getPos()
        p1 = rot([r, 0], self.ang + self.angGun)
        p2 = rot([r + LGun, 0], self.ang + self.angGun)
        pygame.draw.line(screen, (0, 0, 0), np.add(p0, p1), np.add(p0, p2), 3)
        drawText(screen, f"{self.id} ({self.health})", self.x, self.y - self.L / 2 - 12)

    def sim(self, dt):
        if not self.active:
            return
        vec = [self.vx, self.vy]
        vec = rot(vec, self.ang)
        self.x += vec[0] * dt
        self.y += vec[1] * dt
        self.ang += self.va * dt
        self.angGun += self.vaGun * dt
        self.fire_cooldown = max(0, self.fire_cooldown - dt)

    def find_closest_enemy(self, tanks):
        closest_enemy = None
        closest_distance = float('inf')
        for tank in tanks:
            if tank.team != self.team and tank.active:
                distance = dist(self.getPos(), tank.getPos())
                if distance < closest_distance:
                    closest_distance = distance
                    closest_enemy = tank
        return closest_enemy

    def predict_target_position(self, target, dt):
        target_vel = rot([target.vx, target.vy], target.ang)
        target_future_pos = np.add(target.getPos(), np.multiply(target_vel, dt))
        return target_future_pos

def main():
    screen = pygame.display.set_mode(sz)
    timer = pygame.time.Clock()
    fps = 20

    n = 5  # номер варианта
    tanks_team1 = [Tank(i, 200 + n * 5, 100 + i * 100, 1, team=1) for i in range(4)]
    tanks_team2 = [Tank(i + 4, 600 + n * 5, 100 + i * 100, 1, team=2) for i in range(4)]

    for tank in tanks_team1:
        tank.vx = 20
        tank.va = -1
        tank.vaGun = -0.5

    for tank in tanks_team2:
        tank.vx = 20
        tank.va = 1
        tank.vaGun = -0.5

    tanks = tanks_team1 + tanks_team2

    bullets = []
    start_time = time.time()
    battle_ongoing = True

    while battle_ongoing:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                sys.exit(0)

        dt = 1 / fps
        for t in tanks:
            if t.active:
                closest_enemy = t.find_closest_enemy(tanks)
                if closest_enemy:
                    target_future_pos = t.predict_target_position(closest_enemy, dt)
                    b = t.fire(target_future_pos)
                    if b:
                        bullets.append(b)
            t.sim(dt)

        for b in bullets:
            b.sim(dt)
            if dist(b.getPos(), [sz[0] / 2, sz[1] / 2]) > sz[0]:
                b.exploded = True
            for t in tanks:
                if t.team != b.team and dist(t.getPos(), b.getPos()) < t.L / 2:
                    b.exploded = True
                    t.health = max(0, t.health - 10)  # Ограничение здоровья
                    if t.health <= 0:
                        t.active = False
                    break

        bullets = [b for b in bullets if not b.exploded]

        screen.fill((255, 255, 255))
        for t in tanks: t.draw(screen)
        for b in bullets: b.draw(screen)

        drawText(screen, f"NBullets = {len(bullets)}", 5, 5)

        pygame.display.flip()
        timer.tick(fps)

        team1_active = any(t.active for t in tanks_team1)
        team2_active = any(t.active for t in tanks_team2)
        if not team1_active or not team2_active:
            battle_ongoing = False

    end_time = time.time()
    battle_duration = end_time - start_time

    team1_health = sum(t.health for t in tanks_team1)
    team2_health = sum(t.health for t in tanks_team2)

    winning_team = 1 if team1_health > team2_health else 2

    print(f"Battle duration: {battle_duration:.2f} seconds")
    print(f"Winning team: {winning_team}")
    print(f"Team 1 remaining health: {team1_health}")
    print(f"Team 2 remaining health: {team2_health}")

if __name__ == '__main__':
    main()
