from pygame import *
import random


WIDTH = 1000
HEIGHT = 800
FPS = 60

init()
screen = display.set_mode((WIDTH, HEIGHT))
display.set_caption("Tower Defense")
clock = time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

font.init()


class Unit(sprite.Sprite):
    def __init__(self, x, y, image_path, size=30):
        super().__init__()
        try:
            self.image = image.load(image_path)
            self.image = transform.scale(self.image, (size, size))
        except:
            self.image = Surface((size, size))
            self.image.fill(BLUE)
            draw.circle(self.image, WHITE, (size // 2, size // 2), size // 2 - 2)

        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 2
        self.hp = 100
        self.max_hp = 100
        self.target = None
        self.state = 'idle'
        self.damage = 10
        self.attack_cooldown = 0
        self.attack_range = 50
        self.flash_timer = 0
        self.flash_color = None
        self.original_image = self.image.copy()
        self.alive = True
        self.size = size
        self.selected = False

    def draw(self, screen):
        if not self.alive:
            return
        if self.flash_timer > 0:
            flash_surface = self.original_image.copy()
            if self.flash_color == 'green':
                flash_surface.fill(GREEN, special_flags=BLEND_RGB_ADD)
            elif self.flash_color == 'red':
                flash_surface.fill(RED, special_flags=BLEND_RGB_ADD)
            screen.blit(flash_surface, self.rect)
            self.flash_timer -= 1
            if self.flash_timer == 0:
                self.flash_color = None
        else:
            screen.blit(self.image, self.rect)
        if self.selected:
            draw.rect(screen, YELLOW, self.rect, 2)
        bar_width = self.rect.width
        bar_height = 4
        bar_x = self.rect.x
        bar_y = self.rect.y - 8

        draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        hp_percent = max(0, self.hp / self.max_hp)
        draw.rect(screen, GREEN, (bar_x, bar_y, bar_width * hp_percent, bar_height))

    def update(self, enemies):
        if not self.alive:
            return

        if self.flash_timer > 0:
            self.flash_timer -= 1
            if self.flash_timer == 0:
                self.flash_color = None

        if self.state == 'idle':
            self.attack_cooldown = max(0, self.attack_cooldown - 1)
        elif self.state == 'move':
            self.move_to_target()
        elif self.state == 'attack':
            self.attack_target(enemies)

    def move_to_target(self):
        if self.target is None:
            self.state = 'idle'
            return

        # Здесь isinstance уже был — не трогаем
        if isinstance(self.target, Unit):
            target_x = self.target.rect.centerx
            target_y = self.target.rect.centery
        else:
            target_x, target_y = self.target

        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery
        dist = (dx ** 2 + dy ** 2) ** 0.5

        if dist > 5:
            self.rect.x += (dx / dist) * self.speed
            self.rect.y += (dy / dist) * self.speed
        else:
            self.state = 'idle'

    def attack_target(self, enemies):
        # === ИСПРАВЛЕНО ===
        # Было: if self.target is None or not self.target.alive:
        # Стало: добавляем проверку isinstance(self.target, Unit),
        # потому что target может быть кортежем (x, y), у которого нет .alive
        if self.target is None or not isinstance(self.target, Unit) or not self.target.alive:
            self.state = 'idle'
            self.target = None
            return

        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
        dist = (dx ** 2 + dy ** 2) ** 0.5

        if dist > self.attack_range:
            self.move_to_target()
        else:
            if self.attack_cooldown <= 0:
                if hasattr(self.target, 'hp'):
                    self.target.hp -= self.damage
                    self.target.flash('red')
                    if self.target.hp <= 0:
                        self.target.alive = False
                self.attack_cooldown = 45
            self.attack_cooldown -= 1

    def flash(self, color):
        self.flash_color = color
        self.flash_timer = 10


class Warrior(Unit):
    def __init__(self, x, y):
        super().__init__(x, y, 'voin.png', 35)
        self.speed = 2
        self.hp = 250
        self.max_hp = 250
        self.damage = 25
        self.attack_range = 45
        self.image.fill((139, 69, 19), special_flags=BLEND_RGB_MULT)


class Scout(Unit):
    def __init__(self, x, y):
        super().__init__(x, y, 'scout.png', 25)
        self.speed = 5
        self.hp = 100
        self.max_hp = 100
        self.damage = 10
        self.attack_range = 60
        self.image.fill((0, 255, 255), special_flags=BLEND_RGB_MULT)


class Healer(Unit):
    def __init__(self, x, y):
        super().__init__(x, y, 'builder.png', 30)
        self.speed = 2
        self.hp = 100
        self.max_hp = 100
        self.heal_amount = 40
        self.attack_range = 60
        self.heal_cooldown = 0
        self.image.fill((0, 255, 0), special_flags=BLEND_RGB_MULT)

    def update(self, enemies):
        super().update(enemies)

        # === ИСПРАВЛЕНО ===
        # Было: if self.target and self.target.alive and hasattr(self.target, 'hp'):
        # Стало: добавляем isinstance(self.target, Unit) — та же ошибка,
        # что и в Unit.attack_target: target может быть кортежем.
        if isinstance(self.target, Unit) and self.target.alive and hasattr(self.target, 'hp'):
            dx = self.target.rect.centerx - self.rect.centerx
            dy = self.target.rect.centery - self.rect.centery
            dist = (dx ** 2 + dy ** 2) ** 0.5

            if dist < self.attack_range:
                if self.heal_cooldown <= 0:
                    old_hp = self.target.hp
                    self.target.hp = min(self.target.max_hp, self.target.hp + self.heal_amount)
                    if self.target.hp > old_hp:
                        self.target.flash('green')
                        self.flash('green')
                    self.heal_cooldown = 180
                self.heal_cooldown -= 1
            else:
                self.state = 'move'


class Archer(Unit):
    def __init__(self, x, y):
        super().__init__(x, y, 'luchnik.png', 28)
        self.speed = 1.5
        self.hp = 120
        self.max_hp = 120
        self.damage = 20
        self.attack_range = 300
        self.image.fill((255, 215, 0), special_flags=BLEND_RGB_MULT)


class Castle(Unit):
    def __init__(self, x, y):
        super().__init__(x, y, 'zamok.png', 60)
        self.speed = 0
        self.hp = 500
        self.max_hp = 500
        self.damage = 5
        self.attack_range = 100
        self.image.fill((255, 0, 0), special_flags=BLEND_RGB_MULT)


class Enemy(Unit):
    def __init__(self, x, y, image_path):
        super().__init__(x, y, image_path, 25)
        self.speed = 1.5
        self.hp = 100
        self.max_hp = 100
        self.damage = 15
        self.state = 'move'
        self.image.fill((255, 0, 255), special_flags=BLEND_RGB_MULT)

    def update(self, base_pos):
        if not self.alive:
            return

        if self.state != 'attack':
            self.target = base_pos
            self.state = 'move'
        super().update([])


class BossEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 'zombie_boss.png')
        self.speed = 1.2
        self.hp = 500
        self.max_hp = 500
        self.damage = 40
        self.state = 'move'
        self.image.fill((255, 0, 0), special_flags=BLEND_RGB_MULT)
        self.size = 40


def spawn_wave(enemies):
    count = 3 + wave_count // 2
    for i in range(count):
        x = random.randint(50, WIDTH - 50)
        y = random.randint(30, 150)
        enemy = Enemy(x, y, 'zombie.png')
        enemies.append(enemy)


def spawn_boss(enemies):
    x = random.randint(50, WIDTH - 50)
    y = random.randint(30, 150)
    enemy = BossEnemy(x, y)
    enemies.append(enemy)


def draw_text(screen, text, x, y, color=WHITE, size=30):
    font.init()
    text_surface = font.Font(None, size).render(text, True, color)
    screen.blit(text_surface, (x, y))


castle = Castle(WIDTH // 2, HEIGHT - 80)
player_units = []
enemies = []

player_units.append(Warrior(WIDTH // 2 - 150, HEIGHT - 120))
player_units.append(Archer(WIDTH // 2 - 50, HEIGHT - 130))
player_units.append(Healer(WIDTH // 2 + 50, HEIGHT - 120))
player_units.append(Scout(WIDTH // 2 + 150, HEIGHT - 130))

wave_timer = 0
wave_count = 0
game_over = False
victory = False
score = 0
money = 200
selected_unit = None
enemy_spawn_timer = 0
enemies_to_spawn = 0
wave_active = False

running = True
while running:
    for e in event.get():
        if e.type == QUIT:
            running = False

        if e.type == MOUSEBUTTONDOWN and not game_over and not victory:
            x, y = e.pos

            if e.button == 1:
                for unit in player_units:
                    if unit.alive and unit.rect.collidepoint(x, y):
                        for u in player_units:
                            u.selected = False
                        unit.selected = True
                        selected_unit = unit
                        break
                else:
                    for u in player_units:
                        u.selected = False
                    selected_unit = None

            elif e.button == 3 and selected_unit:
                target_enemy = None
                for enemy in enemies:
                    if enemy.alive and enemy.rect.collidepoint(x, y):
                        target_enemy = enemy
                        break

                if target_enemy:
                    selected_unit.target = target_enemy
                    selected_unit.state = 'attack'
                else:
                    # Здесь target становится кортежем (x, y) — именно из-за этого
                    # и падало на старом коде при обращении к .alive
                    selected_unit.target = (x, y)
                    selected_unit.state = 'move'

        if e.type == KEYDOWN:
            if e.key == K_SPACE and not game_over and not victory:
                if not wave_active:
                    wave_active = True
                    wave_count += 1
                    enemies_to_spawn = 3 + wave_count // 2
                    if wave_count % 3 == 0:
                        enemies_to_spawn += 1

            if e.key == K_r:
                castle = Castle(WIDTH // 2, HEIGHT - 80)
                player_units = []
                enemies = []
                player_units.append(Warrior(WIDTH // 2 - 150, HEIGHT - 120))
                player_units.append(Archer(WIDTH // 2 - 50, HEIGHT - 130))
                player_units.append(Healer(WIDTH // 2 + 50, HEIGHT - 120))
                player_units.append(Scout(WIDTH // 2 + 150, HEIGHT - 130))
                wave_timer = 0
                wave_count = 0
                game_over = False
                victory = False
                score = 0
                money = 200
                selected_unit = None
                wave_active = False
                enemies_to_spawn = 0

    if not game_over and not victory:
        if wave_active and enemies_to_spawn > 0:
            enemy_spawn_timer += 1
            if enemy_spawn_timer >= FPS * 0.5:
                if wave_count % 3 == 0 and enemies_to_spawn == 1:
                    spawn_boss(enemies)
                    money += 50
                else:
                    x = random.randint(50, WIDTH - 50)
                    y = random.randint(30, 150)
                    enemy = Enemy(x, y, 'zombie.png')
                    enemies.append(enemy)
                enemies_to_spawn -= 1
                enemy_spawn_timer = 0

                if enemies_to_spawn == 0:
                    wave_active = False

        for enemy in enemies[:]:
            enemy.update((castle.rect.centerx, castle.rect.centery))
            if enemy.rect.colliderect(castle.rect):
                castle.hp -= enemy.damage * 0.05
                enemy.alive = False
                money -= 5
            if not enemy.alive:
                enemies.remove(enemy)
                score += 10

        for unit in player_units:
            if unit.alive:
                if unit != selected_unit or not selected_unit:
                    if not unit.target or (hasattr(unit.target, 'alive') and not unit.target.alive):
                        nearest = None
                        min_dist = float('inf')
                        for enemy in enemies:
                            if enemy.alive:
                                dist = ((unit.rect.centerx - enemy.rect.centerx) ** 2 +
                                        (unit.rect.centery - enemy.rect.centery) ** 2) ** 0.5
                                if dist < min_dist:
                                    min_dist = dist
                                    nearest = enemy
                        if nearest:
                            unit.target = nearest
                            unit.state = 'attack'
                        else:
                            unit.target = None
                            unit.state = 'idle'
                unit.update(enemies)

        nearest_enemy = None
        min_dist = float('inf')
        for enemy in enemies:
            if enemy.alive:
                dist = ((castle.rect.centerx - enemy.rect.centerx) ** 2 +
                        (castle.rect.centery - enemy.rect.centery) ** 2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    nearest_enemy = enemy
        if nearest_enemy:
            castle.target = nearest_enemy
            castle.state = 'attack'
        else:
            castle.target = None
            castle.state = 'idle'
        castle.update(enemies)

        if castle.hp <= 0:
            game_over = True
            victory = False

        if wave_count >= 15 and len(enemies) == 0 and not wave_active:
            victory = True

    screen.fill((20, 20, 30))

    draw.rect(screen, (60, 60, 80), (0, HEIGHT - 150, WIDTH, 30))
    draw.rect(screen, (80, 80, 100), (0, HEIGHT - 100, WIDTH, 20))

    castle.draw(screen)
    for unit in player_units:
        unit.draw(screen)
    for enemy in enemies:
        enemy.draw(screen)

    draw_text(screen, f"Замок: {int(castle.hp)}/{castle.max_hp}", 10, 10, RED)
    draw_text(screen, f"Волна: {wave_count}/15", 10, 45, WHITE)
    draw_text(screen, f"Очки: {score}", 10, 80, YELLOW)
    draw_text(screen, f"Деньги: ${money}", 10, 115, GREEN)
    draw_text(screen, f"Врагов: {len(enemies)}", 10, 150, ORANGE)

    if selected_unit and selected_unit.alive:
        unit_names = {
            'Warrior': 'Воин',
            'Scout': 'Разведчик',
            'Healer': 'Целитель',
            'Archer': 'Лучник'
        }
        class_name = selected_unit.__class__.__name__
        russian_name = unit_names.get(class_name, class_name)

        draw_text(screen, f"Выбран: {russian_name}", 10, 185, YELLOW)
        draw_text(screen, f"HP: {int(selected_unit.hp)}/{selected_unit.max_hp}", 10, 215, GREEN)
        draw_text(screen, f"Урон: {selected_unit.damage}", 10, 245, RED)
        draw_text(screen, f"Дальность: {selected_unit.attack_range}", 10, 275, BLUE)

    draw_text(screen, "ЛКМ - выбрать юнита", 10, HEIGHT - 80, WHITE, 16)
    draw_text(screen, "ПКМ - двигаться/атаковать", 10, HEIGHT - 55, WHITE, 16)
    draw_text(screen, "ПРОБЕЛ - начать волну | R - перезапуск", 10, HEIGHT - 30, WHITE, 16)

    if wave_active:
        draw_text(screen, f"Волна {wave_count} началась!", WIDTH // 2 - 100, 20, YELLOW, 40)
        draw_text(screen, f"Осталось врагов: {enemies_to_spawn}", WIDTH // 2 - 100, 60, WHITE, 25)

    if game_over:
        draw_text(screen, "ИГРА ОКОНЧЕНА!", WIDTH // 2 - 150, HEIGHT // 2, RED, 70)
        draw_text(screen, f"Очки: {score}", WIDTH // 2 - 80, HEIGHT // 2 + 60, WHITE, 30)
        draw_text(screen, "Нажмите R для перезапуска", WIDTH // 2 - 160, HEIGHT // 2 + 110, WHITE, 25)

    if victory:
        draw_text(screen, "ПОБЕДА!", WIDTH // 2 - 120, HEIGHT // 2, GREEN, 70)
        draw_text(screen, f"Очки: {score}", WIDTH // 2 - 80, HEIGHT // 2 + 60, YELLOW, 30)
        draw_text(screen, "Нажмите R для перезапуска", WIDTH // 2 - 160, HEIGHT // 2 + 110, WHITE, 25)

    display.update()
    clock.tick(FPS)
