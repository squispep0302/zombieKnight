import pygame, random

vector = pygame.math.Vector2

pygame.init()

# Display surface (tile size 32x32  1280/32 = 40 tile wide, 736/32 = 23 high)
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 736
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Zombie Knight")

# Set FPS and clock
FPS = 60
clock = pygame.time.Clock()


# Definimos clases
class Game():
    """ Clase para manejar el juego """

    def __init__(self, player, zombie_group, platform_group, portal_group, bullet_group, ruby_group):
        """Al comenzar el juego"""
        # Setear variables constantes
        self.STARTING_ROUND_TIME = 30
        self.STARTING_ZOMBIE_CREATION_TIME = 2

        # Setear valores del juego
        self.score = 0
        self.round_number = 1
        self.frame_count = 0
        self.round_time = self.STARTING_ROUND_TIME
        self.zombie_creation_time = self.STARTING_ZOMBIE_CREATION_TIME

        # Setear fuentes de texto
        self.title_font = pygame.font.Font("fonts/Poultrygeist.ttf", 48)
        self.HUD_font = pygame.font.Font("fonts/Pixel.ttf", 24)

        # Setear sonidos
        self.lost_ruby_sound = pygame.mixer.Sound("sounds/lost_ruby.wav")
        self.ruby_pickup_sound = pygame.mixer.Sound("sounds/ruby_pickup.wav")
        pygame.mixer.music.load("sounds/level_music.wav")

        # Attach groups y sprites
        self.player = player
        self.zombie_group = zombie_group
        self.platform_group = platform_group
        self.portal_group = portal_group
        self.bullet_group = bullet_group
        self.ruby_group = ruby_group

    def update(self):
        """ Actualizar el juego"""
        # Actualizar la ronda cada segundo
        self.frame_count += 1
        if self.frame_count % FPS == 0:
            self.round_time -= 1
            self.frame_count = 0

        # Verificar las colisiones del juego
        self.check_collisions()

        # Agregar zombies cada cierto tiempo
        self.add_zombie()

        # Verificar si se ha completado una ronda
        self.check_round_completition()

        # Verificar si se perdio el juego
        self.check_game_over()

    def draw(self):
        """Dibujar el juego"""
        # Setear colores
        WHITE = (255, 255, 255)
        GREEN = (25, 200, 25)

        # Setear texto
        score_text = self.HUD_font.render("Score: " + str(self.score), True, WHITE)
        score_rect = score_text.get_rect()
        score_rect.topleft = (10, WINDOW_HEIGHT - 50)

        health_text = self.HUD_font.render("Health: " + str(self.player.health), True, WHITE)
        health_rect = health_text.get_rect()
        health_rect.topleft = (10, WINDOW_HEIGHT - 25)

        title_text = self.title_font.render("Zombie Knight", True, GREEN)
        title_rect = title_text.get_rect()
        title_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 25)

        round_text = self.HUD_font.render("Night: " + str(self.round_number), True, WHITE)
        round_rect = round_text.get_rect()
        round_rect.topright = (WINDOW_WIDTH - 10, WINDOW_HEIGHT - 50)

        time_text = self.HUD_font.render("Sunrise In: " + str(self.round_time), True, WHITE)
        time_rect = time_text.get_rect()
        time_rect.topright = (WINDOW_WIDTH - 10, WINDOW_HEIGHT - 25)

        # Dibujar el HUD
        display_surface.blit(score_text, score_rect)
        display_surface.blit(health_text, health_rect)
        display_surface.blit(title_text, title_rect)
        display_surface.blit(round_text, round_rect)
        display_surface.blit(time_text, time_rect)

    def add_zombie(self):
        """Agregar un zombie al juego"""
        # Verificar caundo agregar zombie, cada segundo
        if self.frame_count % FPS == 0:
            # Solo agregar un zombie si el tiempo de creacion ha sido alcanzado
            if self.round_time % self.zombie_creation_time == 0:
                zombie = Zombie(self.platform_group, self.portal_group, self.round_number, 5 + self.round_number)
                self.zombie_group.add(zombie)

    def check_collisions(self):
        """Verificar colisiones en el juego"""
        # Verificar si un proyectil golpea a algun zombie del zombie_group
        collision_dict = pygame.sprite.groupcollide(self.bullet_group, self.zombie_group, True, False)
        if collision_dict:
            for zombies in collision_dict.values():
                for zombie in zombies:
                    zombie.hit_sound.play()
                    zombie.is_dead = True
                    zombie.animate_death = True

        # Verificar si el player choca con un zombie muerto para colectarlo o un zombie vivo y toma daño
        collision_list = pygame.sprite.spritecollide(self.player, self.zombie_group, False)
        if collision_list:
            for zombie in collision_list:
                # Un zombie muerto
                if zombie.is_dead == True:
                    zombie.kick_sound.play()
                    zombie.kill()
                    self.score += 25

                    ruby = Ruby(self.platform_group, self.portal_group)
                    self.ruby_group.add(ruby)

                # El zombie no esta muerto, tomar daño
                else:
                    self.player.health -= 20
                    self.player.hit_sound.play()
                    # Mover al jugador para no recibir daño continuo
                    self.player.position.x -= 256 * zombie.direction
                    self.player.rect.bottomleft = self.player.position

        # Verificar si el player collide con el ruby
        if pygame.sprite.spritecollide(self.player, self.ruby_group, True):
            self.ruby_pickup_sound.play()
            self.score += 100
            self.player.health += 10
            if self.player.health > self.player.STARTING_HEALTH:
                self.player.health = self.player.STARTING_HEALTH

        # Verificar si un zombie viviente collide con un ruby
        for zombie in self.zombie_group:
            if zombie.is_dead == False:
                if pygame.sprite.spritecollide(zombie, self.ruby_group, True):
                    self.lost_ruby_sound.play()
                    zombie = Zombie(self.platform_group, self.portal_group, self.round_number, 5 + self.round_number)
                    self.zombie_group.add(zombie)

    def check_round_completition(self):
        """Ver si el jugador sobrevive a una ronda de noche"""
        if self.round_time == 0:
            self.start_new_round()

    def check_game_over(self):
        """Verificar si el jugador perdio el juego"""
        if self.player.health <= 0:
            pygame.mixer.music.stop()
            self.pause_game("Game Over! Final Score: " + str(self.score), "Presione 'Enter' para jugar otra vez...")
            self.reset_game()

    def start_new_round(self):
        """Comenzar una nueva ronda de noche"""
        self.round_number += 1

        # Disminuir el tiempo de creacion de zombies .. mas zombies
        if self.round_number < self.STARTING_ZOMBIE_CREATION_TIME:
            self.zombie_creation_time -= 1

        # Resetear los valores de la ronda
        self.round_time = self.STARTING_ROUND_TIME

        self.zombie_group.empty()
        self.ruby_group.empty()
        self.bullet_group.empty()

        self.player.reset()
        self.pause_game("Sobreviviste la noche!!!", "Presiona 'Enter' para continuar...")

    def pause_game(self, main_text, sub_text):
        """Pausar el juego"""
        global running
        pygame.mixer.music.pause()

        # Setear colores
        WHITE = (255, 255, 255)
        BLACK = (0, 0, 0)
        GREEN = (25, 200, 25)

        # Crear el texto principal de pausa
        main_text = self.title_font.render(main_text, True, GREEN)
        main_rect = main_text.get_rect()
        main_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

        # Crear texto secundario de pausa
        sub_text = self.title_font.render(sub_text, True, WHITE)
        sub_rect = sub_text.get_rect()
        sub_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 64)

        # Display el texto de pausa
        display_surface.fill(BLACK)
        display_surface.blit(main_text, main_rect)
        display_surface.blit(sub_text, sub_rect)
        pygame.display.update()

        # Pausar el juego hasta que el usuario presione enter o salga
        is_paused = True
        while is_paused:
            for event in pygame.event.get():
                # El usuario quiere continuar
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        is_paused = False
                        pygame.mixer.music.unpause()
                # El usuario quiere salir
                if event.type == pygame.QUIT:
                    is_paused = False
                    running = False
                    pygame.mixer.music.stop()

    def reset_game(self):
        """Reiniciar el juego"""
        # Reset los valores del juego
        self.score = 0
        self.round_number = 1
        self.round_time = self.STARTING_ROUND_TIME
        self.zombie_creation_time = self.STARTING_ZOMBIE_CREATION_TIME

        # Reset el player
        self.player.health = self.player.STARTING_HEALTH
        self.player.reset()

        # Vaciar los sprite groups
        self.zombie_group.empty()
        self.ruby_group.empty()
        self.bullet_group.empty()

        pygame.mixer.music.play(-1, 0.0)


class Tile(pygame.sprite.Sprite):
    """Clase que representa el 32x32 area de pixeles en el display"""

    def __init__(self, x, y, image_int, main_group, sub_group=""):
        """Al iniciar el tile"""
        super().__init__()
        # Cargar la imagen correcta y agregarlo al subgrupo correcto
        # Dirt
        if image_int == 1:
            self.image = pygame.transform.scale(pygame.image.load("images/tiles/Tile (1).png"), (32, 32))
        # Platform tiles
        if image_int == 2:
            self.image = pygame.transform.scale(pygame.image.load("images/tiles/Tile (2).png"), (32, 32))
            sub_group.add(self)
        if image_int == 3:
            self.image = pygame.transform.scale(pygame.image.load("images/tiles/Tile (3).png"), (32, 32))
            sub_group.add(self)
        if image_int == 4:
            self.image = pygame.transform.scale(pygame.image.load("images/tiles/Tile (4).png"), (32, 32))
            sub_group.add(self)
        if image_int == 5:
            self.image = pygame.transform.scale(pygame.image.load("images/tiles/Tile (5).png"), (32, 32))
            sub_group.add(self)
        # Agregar cada tile al grupo principal
        main_group.add(self)

        # Obtener el rect de la imagen y posicionarlo en el grid
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

        # Crear una mascara para mejorar las colisiones con el player
        self.mask = pygame.mask.from_surface(self.image)


class Player(pygame.sprite.Sprite):
    """Clase que el usuario puede controlar"""

    def __init__(self, x, y, platform_group, portal_group, bullet_group):
        """Comenzar el jugador"""
        super().__init__()

        # Setear variables constantes
        self.HORIZONTAL_ACCELERATION = 2
        self.HORIZONTAL_FRICTION = 0.15
        self.VERTICAL_ACCELERATION = 0.8  # Gravedad
        self.VERTICAL_JUMP_SPEED = 18
        self.STARTING_HEALTH = 100

        # Frames de animacion
        self.move_right_sprites = []
        self.move_left_sprites = []
        self.idle_right_sprites = []
        self.idle_left_sprites = []
        self.jump_right_sprites = []
        self.jump_left_sprites = []
        self.attack_right_sprites = []
        self.attack_left_sprites = []

        # Movimiento Derecha "images/player/run/Run (1).png"
        for r in range(1, 11):
            self.move_right_sprites.append(
                pygame.transform.scale(pygame.image.load("images/player/run/Run (" + str(r) + ").png"), (64, 64)))

        # Movimiento Izquierda
        for sprite in self.move_right_sprites:
            self.move_left_sprites.append(pygame.transform.flip(sprite, True, False))

        # Idling Derecha "images/player/idle/Idle (1).png"
        for r in range(1, 11):
            self.idle_right_sprites.append(
                pygame.transform.scale(pygame.image.load("images/player/idle/Idle (" + str(r) + ").png"), (64, 64)))

        # Idling Izquierda
        for sprite in self.idle_right_sprites:
            self.idle_left_sprites.append(pygame.transform.flip(sprite, True, False))

        # Jumping Derecha "images/player/jump/Jump (1).png"
        for r in range(1, 11):
            self.jump_right_sprites.append(
                pygame.transform.scale(pygame.image.load("images/player/jump/Jump (" + str(r) + ").png"), (64, 64)))

        # Jumping Izquierda
        for sprite in self.jump_right_sprites:
            self.jump_left_sprites.append(pygame.transform.flip(sprite, True, False))

        # Attacking Derecha "images/player/attack/Attack (1).png"
        for r in range(1, 11):
            self.attack_right_sprites.append(
                pygame.transform.scale(pygame.image.load("images/player/attack/Attack (" + str(r) + ").png"), (64, 64)))

        # Attacking Izquierda
        for sprite in self.attack_right_sprites:
            self.attack_left_sprites.append(pygame.transform.flip(sprite, True, False))

        # Cargar imagen y obtener rect
        self.current_sprite = 0
        self.image = self.idle_right_sprites[self.current_sprite]
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (x, y)

        # Attach los sprite groups
        self.platform_group = platform_group
        self.portal_group = portal_group
        self.bullet_group = bullet_group

        # Booleans de animacion
        self.animate_jump = False
        self.animate_fire = False

        # Cargar sonidos
        self.jump_sound = pygame.mixer.Sound("sounds/jump_sound.wav")
        self.slash_sound = pygame.mixer.Sound("sounds/slash_sound.wav")
        self.portal_sound = pygame.mixer.Sound("sounds/portal_sound.wav")
        self.hit_sound = pygame.mixer.Sound("sounds/player_hit.wav")

        # Kinematics vectors
        self.position = vector(x, y)
        self.velocity = vector(0, 0)
        self.acceleration = vector(0, self.VERTICAL_ACCELERATION)

        # Setear valores iniciales del jugador
        self.health = self.STARTING_HEALTH
        self.starting_x = x
        self.starting_y = y

    def update(self):
        """Actualizar el jugador"""
        self.move()
        self.check_collisions()
        self.check_animations()

        # Actualizar el mask para el player
        self.mask = pygame.mask.from_surface(self.image)

    def move(self):
        """Mover el jugador"""
        # Setear el vector aceleracion
        self.acceleration = vector(0, self.VERTICAL_ACCELERATION)

        # Si el usuario presiona una tecla, setear el componente x de aceleracion dif de 0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.acceleration.x = -1 * self.HORIZONTAL_ACCELERATION
            self.animate(self.move_left_sprites, .5)
        elif keys[pygame.K_RIGHT]:
            self.acceleration.x = self.HORIZONTAL_ACCELERATION
            self.animate(self.move_right_sprites, .5)
        else:
            if self.velocity.x > 0:
                self.animate(self.idle_right_sprites, .5)

            else:
                self.animate(self.idle_left_sprites, .5)

        # Calcular los nuevos valores de kinematics
        self.acceleration.x -= self.velocity.x * self.HORIZONTAL_FRICTION
        self.velocity += self.acceleration
        self.position += self.velocity + 0.5 * self.acceleration

        # Update rect basado en kinematic calculations y wrap around movement
        if self.position.x < 0:
            self.position.x = WINDOW_WIDTH
        elif self.position.x > WINDOW_WIDTH:
            self.position.x = 0

        self.rect.bottomleft = self.position

    def check_collisions(self):
        """Verificar colisiones con plataformas o portales"""
        # Colision verificada entre jugador y plataformas cuando se cae
        if self.velocity.y > 0:
            collided_platforms = pygame.sprite.spritecollide(self, self.platform_group, False,
                                                             pygame.sprite.collide_mask)
            if collided_platforms:
                self.position.y = collided_platforms[0].rect.top + 5
                self.velocity.y = 0

        # Colision verificada entre jugador y plataformas cuando salta
        if self.velocity.y < 0:
            collided_platforms = pygame.sprite.spritecollide(self, self.platform_group, False,
                                                             pygame.sprite.collide_mask)
            if collided_platforms:
                self.velocity.y = 0
                while pygame.sprite.spritecollide(self, self.platform_group, False):
                    self.position.y += 1
                    self.rect.bottomleft = self.position

        # Colision verificada para los portales
        if pygame.sprite.spritecollide(self, self.portal_group, False):
            self.portal_sound.play()
            # Determinar a que portal me dirijo (der, izq)
            if self.position.x > WINDOW_WIDTH // 2:
                self.position.x = 86
            else:
                self.position.x = WINDOW_WIDTH - 150
            # Top y bottom
            if self.position.y > WINDOW_HEIGHT // 2:
                self.position.y = 64
            else:
                self.position.y = WINDOW_HEIGHT - 132

            self.rect.bottomleft = self.position

    def check_animations(self):
        """Verificar si animaciones salto o fuego deben ejecutarse"""
        # Animar el salto del jugador
        if self.animate_jump:
            if self.velocity.x > 0:
                self.animate(self.jump_right_sprites, .1)
            else:
                self.animate(self.jump_left_sprites, .1)

        # Animar el ataque del jugador
        if self.animate_fire:
            if self.velocity.x > 0:
                self.animate(self.attack_right_sprites, .1)
            else:
                self.animate(self.attack_left_sprites, .1)

    def jump(self):
        """Saltar sobre una plataforma"""
        # Solo saltar sobre una plataforma
        if pygame.sprite.spritecollide(self, self.platform_group, False):
            self.jump_sound.play()
            self.velocity.y = -1 * self.VERTICAL_JUMP_SPEED
            self.animate_jump = True

    def fire(self):
        """Disparar bala desde la espada"""
        self.slash_sound.play()
        Bullet(self.rect.centerx, self.rect.centery, self.bullet_group, self)
        self.animate_fire = True

    def reset(self):
        """Reiniciar la posicion del jugador"""
        self.velocity = vector(0, 0)
        self.position = vector(self.starting_x, self.starting_y)
        self.rect.bottomleft = self.position

    def animate(self, sprite_list, speed):
        """Animar la accion del jugador"""
        if self.current_sprite < len(sprite_list) - 1:
            self.current_sprite += speed
        else:
            self.current_sprite = 0
            # End the jump animation
            if self.animate_jump:
                self.animate_jump = False

            # End attack animation
            if self.animate_fire:
                self.animate_fire = False
        self.image = sprite_list[int(self.current_sprite)]


class Bullet(pygame.sprite.Sprite):
    """El proyectil lanzado por el jugador"""

    def __init__(self, x, y, bullet_group, player):
        """Iniciar el proyectil"""
        super().__init__()

        # Setear constantes
        self.VELOCITY = 20
        self.RANGE = 500

        # Cargar imagen y obtener el rect
        if player.velocity.x > 0:
            self.image = pygame.transform.scale(pygame.image.load("images/player/slash.png"), (32, 32))
        else:
            self.image = pygame.transform.scale(pygame.transform.flip(
                pygame.image.load("images/player/slash.png"), True, False), (32, 32))
            self.VELOCITY = -1 * self.VELOCITY

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        self.starting_x = x

        bullet_group.add(self)

    def update(self):
        """Actualizar el proyectil"""
        self.rect.x += self.VELOCITY

        # Si el proyectil se pasa del rango, eliminarlo
        if abs(self.rect.x - self.starting_x) > self.RANGE:
            self.kill()


class Zombie(pygame.sprite.Sprite):
    """Clase para el enemigo que se movera por la pantalla"""

    def __init__(self, platform_group, portal_group, min_speed, max_speed):
        """Comenzar el zombie"""
        super().__init__()

        # Setear las constantes
        self.VERTICAL_ACCELERATION = 3  # Gravedad
        self.RISE_TIME = 2

        # Animation frames
        self.walk_right_sprites = []
        self.walk_left_sprites = []
        self.die_right_sprites = []
        self.die_left_sprites = []
        self.rise_right_sprites = []
        self.rise_left_sprites = []

        gender = random.randint(0, 1)
        if gender == 0:
            # Caminar derecha
            for r in range(1, 11):
                self.walk_right_sprites.append(pygame.transform.scale(
                    pygame.image.load("images/zombie/boy/walk/Walk (" + str(r) + ").png"), (64, 64)))

            # Caminar Izquierda
            for sprite in self.walk_right_sprites:
                self.walk_left_sprites.append(pygame.transform.flip(sprite, True, False))

            # Morir Derecha
            for r in range(1, 11):
                self.die_right_sprites.append(pygame.transform.scale(
                    pygame.image.load("images/zombie/boy/dead/Dead (" + str(r) + ").png"), (64, 64)))

            # Morir Izquierda
            for sprite in self.die_right_sprites:
                self.die_left_sprites.append(pygame.transform.flip(sprite, True, False))

            # Rising Derecha
            for r in range(10, 0, -1):
                self.rise_right_sprites.append(pygame.transform.scale(
                    pygame.image.load("images/zombie/boy/dead/Dead (" + str(r) + ").png"), (64, 64)))

            # Rising Izquierda
            for sprite in self.rise_right_sprites:
                self.rise_left_sprites.append(pygame.transform.flip(sprite, True, False))

        else:
            # Caminar derecha
            for r in range(1, 11):
                self.walk_right_sprites.append(pygame.transform.scale(
                    pygame.image.load("images/zombie/girl/walk/Walk (" + str(r) + ").png"), (64, 64)))

            # Caminar Izquierda
            for sprite in self.walk_right_sprites:
                self.walk_left_sprites.append(pygame.transform.flip(sprite, True, False))

            # Morir Derecha
            for r in range(1, 11):
                self.die_right_sprites.append(pygame.transform.scale(
                    pygame.image.load("images/zombie/girl/dead/Dead (" + str(r) + ").png"), (64, 64)))

            # Morir Izquierda
            for sprite in self.die_right_sprites:
                self.die_left_sprites.append(pygame.transform.flip(sprite, True, False))

            # Rising Derecha
            for r in range(10, 0, -1):
                self.rise_right_sprites.append(pygame.transform.scale(
                    pygame.image.load("images/zombie/girl/dead/Dead (" + str(r) + ").png"), (64, 64)))

            # Rising Izquierda
            for sprite in self.rise_right_sprites:
                self.rise_left_sprites.append(pygame.transform.flip(sprite, True, False))

        # Cargar la imagen y obtener el rect
        self.direction = random.choice([-1, 1])
        self.current_sprite = 0
        if self.direction == -1:
            self.image = self.walk_left_sprites[self.current_sprite]
        else:
            self.image = self.walk_right_sprites[self.current_sprite]

        self.rect = self.image.get_rect()
        self.rect.bottomleft = (random.randint(100, WINDOW_WIDTH - 100), -100)

        # Attach sprite groups
        self.platform_group = platform_group
        self.portal_group = portal_group

        # Booleans de animaciones
        self.animate_death = False
        self.animate_rise = False

        # Cargar sonidos
        self.hit_sound = pygame.mixer.Sound("sounds/zombie_hit.wav")
        self.kick_sound = pygame.mixer.Sound("sounds/zombie_kick.wav")
        self.portal_sound = pygame.mixer.Sound("sounds/portal_sound.wav")

        # Kinematics vectors
        self.position = vector(self.rect.x, self.rect.y)
        self.velocity = vector(self.direction * random.randint(min_speed, max_speed), 0)
        self.acceleration = vector(0, self.VERTICAL_ACCELERATION)

        # Valores iniciales para los zombies
        self.is_dead = False
        self.round_time = 0
        self.frame_count = 0

    def update(self):
        """Actualizar el zombie"""
        self.move()
        self.check_collisions()
        self.check_animations()

        # Determinar cuando el zombie debe revivir
        if self.is_dead:
            self.frame_count += 1
            if self.frame_count % FPS == 0:
                self.round_time += 1
                if self.round_time == self.RISE_TIME:
                    self.animate_rise = True
                    # Cuando el zombie muera, la imagen es la ultima
                    # Cuando el zombie revive, comenzamos en el indice 0 de rise_sprite list
                    self.current_sprite = 0

    def move(self):
        """Mover el zombie"""
        if not self.is_dead:
            if self.direction == -1:
                self.animate(self.walk_left_sprites, .5)
            else:
                self.animate(self.walk_right_sprites, .5)
            # No se necesita actualizar la aceleracion, porque esta no cambia
            # Calcular los nuevos valores de kinematics
            self.velocity += self.acceleration
            self.position += self.velocity + 0.5 * self.acceleration

            # Update rect basado en kinematic calculations y wrap around movement
            if self.position.x < 0:
                self.position.x = WINDOW_WIDTH
            elif self.position.x > WINDOW_WIDTH:
                self.position.x = 0

            self.rect.bottomleft = self.position

    def check_collisions(self):
        """Verificar colisiones con plataformas o portales"""
        # Colision verificada entre zombie y plataformas cuando se cae

        collided_platforms = pygame.sprite.spritecollide(self, self.platform_group, False)
        if collided_platforms:
            self.position.y = collided_platforms[0].rect.top + 1
            self.velocity.y = 0

        # Colision verificada para los portales
        if pygame.sprite.spritecollide(self, self.portal_group, False):
            self.portal_sound.play()
            # Determinar a que portal me dirijo (der, izq)
            if self.position.x > WINDOW_WIDTH // 2:
                self.position.x = 86
            else:
                self.position.x = WINDOW_WIDTH - 150
            # Top y bottom
            if self.position.y > WINDOW_HEIGHT // 2:
                self.position.y = 64
            else:
                self.position.y = WINDOW_HEIGHT - 132

            self.rect.bottomleft = self.position

    def check_animations(self):
        """Verificar si animaciones death/rise deben ejecutarse"""
        # Animar si el zombie muere
        if self.animate_death:
            if self.direction == 1:
                self.animate(self.die_right_sprites, .095)
            else:
                self.animate(self.die_left_sprites, .095)

        # Animar cuando el zombie revive
        if self.animate_rise:
            if self.direction == 1:
                self.animate(self.rise_right_sprites, .095)
            else:
                self.animate(self.rise_left_sprites, .095)

    def animate(self, sprite_list, speed):
        """Animar las acciones del zombie"""
        if self.current_sprite < len(sprite_list) - 1:
            self.current_sprite += speed
        else:
            self.current_sprite = 0
            # Terminar la animacion de death
            if self.animate_death:
                self.current_sprite = len(sprite_list) - 1
                self.animate_death = False

            # Terminar la animacion de rise
            if self.animate_rise:
                self.animate_rise = False
                self.is_dead = False
                self.frame_count = 0
                self.round_time = 0

        self.image = sprite_list[int(self.current_sprite)]


class RubyMaker(pygame.sprite.Sprite):
    """Tile animado. EL ruby es generado aqui"""

    def __init__(self, x, y, main_group):
        """Comenzar el ruby maker"""
        super().__init__()
        # Frames de animacion
        self.ruby_sprites = []

        # Rotacion
        self.ruby_sprites.append(pygame.transform.scale(pygame.image.load("images/ruby/tile000.png"), (64, 64)))
        self.ruby_sprites.append(pygame.transform.scale(pygame.image.load("images/ruby/tile001.png"), (64, 64)))
        self.ruby_sprites.append(pygame.transform.scale(pygame.image.load("images/ruby/tile002.png"), (64, 64)))
        self.ruby_sprites.append(pygame.transform.scale(pygame.image.load("images/ruby/tile003.png"), (64, 64)))
        self.ruby_sprites.append(pygame.transform.scale(pygame.image.load("images/ruby/tile004.png"), (64, 64)))
        self.ruby_sprites.append(pygame.transform.scale(pygame.image.load("images/ruby/tile005.png"), (64, 64)))
        self.ruby_sprites.append(pygame.transform.scale(pygame.image.load("images/ruby/tile006.png"), (64, 64)))

        # Cargar la imagen y obtener el rect
        self.current_sprite = 0
        self.image = self.ruby_sprites[self.current_sprite]
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (x, y)

        # Agregar al main group para dibujarlo
        main_group.add(self)

    def update(self):
        """Actualizar el ruby maker"""
        self.animate(self.ruby_sprites, .25)

    def animate(self, sprite_list, speed):
        """Animar el ruby maker"""
        if self.current_sprite < len(sprite_list) - 1:
            self.current_sprite += speed
        else:
            self.current_sprite = 0
        self.image = sprite_list[int(self.current_sprite)]


class Ruby(pygame.sprite.Sprite):
    """Clase que el jugador debe recolectar para ganar vida y puntos"""

    def __init__(self, platform_group, portal_group):
        """Comenzar el ruby"""
        super().__init__()

        # Setear constantes
        self.VERTCAL_ACCELERATION = 3  # Gravedad
        self.HORIZONTAL_VELOCITY = 5

        # Frames de animacion
        self.ruby_sprites = []

        # Rotacion
        self.ruby_sprites.append(pygame.transform.scale(pygame.image.load("images/ruby/tile000.png"), (64, 64)))
        self.ruby_sprites.append(pygame.transform.scale(pygame.image.load("images/ruby/tile001.png"), (64, 64)))
        self.ruby_sprites.append(pygame.transform.scale(pygame.image.load("images/ruby/tile002.png"), (64, 64)))
        self.ruby_sprites.append(pygame.transform.scale(pygame.image.load("images/ruby/tile003.png"), (64, 64)))
        self.ruby_sprites.append(pygame.transform.scale(pygame.image.load("images/ruby/tile004.png"), (64, 64)))
        self.ruby_sprites.append(pygame.transform.scale(pygame.image.load("images/ruby/tile005.png"), (64, 64)))
        self.ruby_sprites.append(pygame.transform.scale(pygame.image.load("images/ruby/tile006.png"), (64, 64)))

        # Cargar imagen y obtener rect
        self.current_sprite = 0
        self.image = self.ruby_sprites[self.current_sprite]
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (WINDOW_WIDTH // 2, 100)

        # Attach los sprite groups
        self.platform_group = platform_group
        self.portal_group = portal_group

        # Cargar sonidos
        self.portal_sound = pygame.mixer.Sound("sounds/portal_sound.wav")

        # Kinematic vectors
        self.position = vector(self.rect.x, self.rect.y)
        self.velocity = vector(random.choice([-1 * self.HORIZONTAL_VELOCITY, self.HORIZONTAL_VELOCITY]), 0)
        self.acceleration = vector(0, self.VERTCAL_ACCELERATION)

    def update(self):
        """Actualizar el ruby"""
        self.animate(self.ruby_sprites, .25)
        self.move()
        self.check_collisions()

    def move(self):
        """Mover el ruby"""

        # No se necesita actualizar la aceleracion, porque esta no cambia
        # Calcular los nuevos valores de kinematics
        self.velocity += self.acceleration
        self.position += self.velocity + 0.5 * self.acceleration

        # Update rect basado en kinematic calculations y wrap around movement
        if self.position.x < 0:
            self.position.x = WINDOW_WIDTH
        elif self.position.x > WINDOW_WIDTH:
            self.position.x = 0

        self.rect.bottomleft = self.position

    def check_collisions(self):
        """Verificar las colisiones con plataformas o portales"""
        # Colision verificada entre ruby y plataformas cuando se cae

        collided_platforms = pygame.sprite.spritecollide(self, self.platform_group, False)
        if collided_platforms:
            self.position.y = collided_platforms[0].rect.top + 1
            self.velocity.y = 0

        # Colision verificada para los portales
        if pygame.sprite.spritecollide(self, self.portal_group, False):
            self.portal_sound.play()
            # Determinar a que portal me dirijo (der, izq)
            if self.position.x > WINDOW_WIDTH // 2:
                self.position.x = 86
            else:
                self.position.x = WINDOW_WIDTH - 150
            # Top y bottom
            if self.position.y > WINDOW_HEIGHT // 2:
                self.position.y = 64
            else:
                self.position.y = WINDOW_HEIGHT - 132

            self.rect.bottomleft = self.position

    def animate(self, sprite_list, speed):
        """Animar el ruby"""
        if self.current_sprite < len(sprite_list) - 1:
            self.current_sprite += speed
        else:
            self.current_sprite = 0
        self.image = sprite_list[int(self.current_sprite)]


class Portal(pygame.sprite.Sprite):
    """Clase que si es collided te transportara"""

    def __init__(self, x, y, color, portal_group):
        """Initialize el portal"""
        super().__init__()

        # Frames de animacion
        self.portal_sprites = []

        # Animacion del portal
        if color == "green":
            # Portal verde
            # Importacion de los sprites para el portal verde usando for
            for r in range(22):
                if r < 10:
                    self.portal_sprites.append(pygame.transform.scale(
                        pygame.image.load("images/portals/green/tile00" + str(r) + ".png"),
                        (72, 72)))
                else:
                    self.portal_sprites.append(pygame.transform.scale(
                        pygame.image.load("images/portals/green/tile0" + str(r) + ".png"),
                        (72, 72)))

        else:
            # Portal morado
            # Importacion de los sprites para el portal morado usando for
            for r in range(22):
                if r < 10:
                    self.portal_sprites.append(pygame.transform.scale(
                        pygame.image.load("images/portals/purple/tile00" + str(r) + ".png"),
                        (72, 72)))
                else:
                    self.portal_sprites.append(pygame.transform.scale(
                        pygame.image.load("images/portals/purple/tile0" + str(r) + ".png"),
                        (72, 72)))

        # Cargar una imagen y obtener el rect
        self.current_sprite = random.randint(0, len(self.portal_sprites) - 1)
        self.image = self.portal_sprites[self.current_sprite]
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (x, y)

        # Agregar al grupo portal
        portal_group.add(self)

    def update(self):
        """Actualizar el portal"""
        self.animate(self.portal_sprites, .2)

    def animate(self, sprite_list, speed):
        """Animar el portal"""
        if self.current_sprite < len(sprite_list) - 1:
            self.current_sprite += speed
        else:
            self.current_sprite = 0
        self.image = sprite_list[int(self.current_sprite)]


# Sprite Groups
my_main_tile_group = pygame.sprite.Group()
my_platform_group = pygame.sprite.Group()

my_player_group = pygame.sprite.Group()
my_bullet_group = pygame.sprite.Group()

my_zombie_group = pygame.sprite.Group()

my_portal_group = pygame.sprite.Group()
my_ruby_group = pygame.sprite.Group()

# Crear el tile map
# 0 -> no tile, 1 -> dirt, 2-5 -> platforms, 6-> ruby maker, 7-8 -> portal, 9 ->player
# 23 rows and 40 columns
tile_map = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
    [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 0, 0, 0, 0, 6, 0, 0, 0, 0, 0, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [4, 4, 4, 4, 4, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 4, 4, 4, 4, 4],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 0, 0, 0, 0, 0, 0, 0, 0, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 4, 4, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

# Loop a traves de las 23 listas(rows) en el tile map (i a traves del map arriba abajo):
for i in range(len(tile_map)):
    # Loop a traves de los 40 elementos en una lista dada (cols) (j a traves del mapa izq derecha)
    for j in range(len(tile_map[i])):
        # Dir tile
        if tile_map[i][j] == 1:
            # Cada 32 pixeles se dibujara 1 tile
            Tile(j * 32, i * 32, 1, my_main_tile_group)
        elif tile_map[i][j] == 2:
            Tile(j * 32, i * 32, 2, my_main_tile_group, my_platform_group)
        elif tile_map[i][j] == 3:
            Tile(j * 32, i * 32, 3, my_main_tile_group, my_platform_group)
        elif tile_map[i][j] == 4:
            Tile(j * 32, i * 32, 4, my_main_tile_group, my_platform_group)
        elif tile_map[i][j] == 5:
            Tile(j * 32, i * 32, 5, my_main_tile_group, my_platform_group)
        # Ruby Maker
        elif tile_map[i][j] == 6:
            RubyMaker(j * 32, i * 32, my_main_tile_group)
        # Portals
        elif tile_map[i][j] == 7:
            Portal(j * 32, i * 32, "green", my_portal_group)
        elif tile_map[i][j] == 8:
            Portal(j * 32, i * 32, "purple", my_portal_group)
        # Player
        elif tile_map[i][j] == 9:
            my_player = Player(j * 32 - 32, i * 32 + 32, my_platform_group, my_portal_group, my_bullet_group)
            my_player_group.add(my_player)

# Cargar imagen de fondo
background_image = pygame.transform.scale(pygame.image.load("images/background.png"),
                                          (WINDOW_WIDTH, WINDOW_HEIGHT))
background_rect = background_image.get_rect()
background_rect.topleft = (0, 0)

# Crear un juego
my_game = Game(my_player, my_zombie_group, my_platform_group, my_portal_group, my_bullet_group, my_ruby_group)
my_game.pause_game("Zombie Knight", "Presione 'Enter' para empezar")
pygame.mixer.music.play(-1, 0.0)

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            # Player quiere saltar
            if event.key == pygame.K_SPACE:
                my_player.jump()
            # Player quiere disparar
            if event.key == pygame.K_UP:
                my_player.fire()

            """
            # Rain zombies
            if event.key == pygame.K_RETURN:
                zombie = Zombie(my_platform_group, my_portal_group, 5, 7)
                my_zombie_group.add(zombie)
            
            """
    # Blit background
    display_surface.blit(background_image, background_rect)

    # Dibujar tiles and update ruby maker
    my_main_tile_group.update()
    my_main_tile_group.draw(display_surface)

    # Update y dibujar sprite groups
    my_portal_group.update()
    my_portal_group.draw(display_surface)

    # Update y dibujar player groups
    my_player_group.update()
    my_player_group.draw(display_surface)

    # Update y dibujar bullet groups
    my_bullet_group.update()
    my_bullet_group.draw(display_surface)

    # Update y dibujar zombies
    my_zombie_group.update()
    my_zombie_group.draw(display_surface)

    # Update y dibujar los rubys
    my_ruby_group.update()
    my_ruby_group.draw(display_surface)

    # Update y dibujar el juego
    my_game.update()
    my_game.draw()

    # Actualizar display and tick the clock
    pygame.display.update()
    clock.tick(FPS)

# End pygame
pygame.quit()
