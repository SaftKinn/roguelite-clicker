import sys
import random
from game import sounds
sounds.init_mixer()          # vor pygame.init()!
import pygame
from game.constants    import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, BG_COLOR
from game.player       import Player, RADIUS as PLAYER_RADIUS, MAX_HP
from game.enemy        import Warrior, Archer, Lancer, Monk, Boss, SuperBoss, EnemyProjectile, RADIUS as ENEMY_RADIUS
from game.projectile   import Projectile
from game.upgrade_menu import UpgradeMenu
from game.main_menu    import MainMenu, OptionsMenu, ImprovementsMenu, IMPROVEMENTS, Button
from game.fx           import DamageNumber, COLOR_COIN
from game.terrain      import Terrain
from game import save_data  as sd
from game import ui_loader
from game.balance     import (BASE_SPAWN_INTERVAL, MELEE_REACH,
                              WIN_WAVE, MAX_CONCURRENT_ENEMIES, CAMERA_ZOOM,
                              enemies_for_wave, enemy_hp_for_wave,
                              enemy_speed_for_wave, coin_value_for_wave, xp_to_next,
                              UPGRADE_DAMAGE, UPGRADE_BULLET_SPEED,
                              UPGRADE_BULLET_SIZE, UPGRADE_MAX_HP, MULTISHOT_ANGLES,
                              BASE_ATTACK_SPEED, UPGRADE_ATTACK_SPEED, LIFESTEAL_PER_HIT,
                              PERMANENT_DAMAGE_PER_LEVEL, PERMANENT_HP_PER_LEVEL,
                              GOLD_BOOST_MULT, DOPPELSCHUSS_DELAY)

WAVE_CLEAR_DELAY    = 70    # kürzere Pause zwischen Wellen (knackiger, ADR 008)
CONTACT_DIST        = PLAYER_RADIUS + ENEMY_RADIUS


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def spawn_enemy_for_wave(wave: int, hp_mult: float) -> Warrior:
    base_hp    = enemy_hp_for_wave(wave, hp_mult)
    base_speed = enemy_speed_for_wave(wave)
    if wave % 50 == 0:
        return SuperBoss(base_speed, base_hp)
    if wave % 10 == 0:
        return Boss(base_speed, base_hp)
    if wave < 3:
        kinds, weights = ["basic"],                            [1]
    elif wave < 5:
        kinds, weights = ["basic", "rusher"],                  [70, 30]
    elif wave < 7:
        kinds, weights = ["basic", "rusher", "tanker"],        [45, 35, 20]
    else:
        kinds, weights = ["basic", "rusher", "tanker", "monk"],[38, 30, 20, 12]
    kind = random.choices(kinds, weights=weights)[0]
    if kind == "rusher": return Archer(base_speed, base_hp)
    if kind == "tanker": return Lancer(base_speed, base_hp)
    if kind == "monk":   return Monk(base_speed, base_hp)
    return Warrior(speed=base_speed, max_hp=base_hp)


def apply_permanent_bonuses(player: Player, stats: dict, save: dict) -> None:
    upgrades = save.get("upgrades", {})
    stats["damage"] += upgrades.get("start_damage", 0) * PERMANENT_DAMAGE_PER_LEVEL
    bonus_hp = upgrades.get("start_hp", 0) * PERMANENT_HP_PER_LEVEL
    if bonus_hp > 0:
        player.max_hp += bonus_hp
        player.hp      = player.max_hp
    # gold_boost + doppelschuss checked inline during gameplay


def spawn_projectiles(origin: pygame.math.Vector2, mouse_pos: tuple,
                      stats: dict) -> list:
    damage = stats["damage"]
    speed  = stats["bullet_speed"]
    radius = stats["bullet_size"]
    pierce = stats["pierce"]
    base   = pygame.math.Vector2(mouse_pos) - origin
    if base.length() == 0:
        return []
    base = base.normalize()
    if stats["multishot"]:
        return [Projectile(origin, vel=base.rotate(a) * speed,
                           damage=damage, radius=radius, pierce=pierce)
                for a in MULTISHOT_ANGLES]
    return [Projectile(origin, mouse_pos, damage=damage, speed=speed,
                       radius=radius, pierce=pierce)]


def check_projectile_hits(projectiles: list, enemies: list,
                          dmg_numbers: list, kills: list, player=None) -> bool:
    """Gibt True zurück wenn mindestens ein (nicht-tödlicher) Treffer erfolgte.

    Lifesteal (ADR 009): je Treffer an einem Gegner heilt der Spieler
    `LIFESTEAL_PER_HIT` HP (bis max_hp).
    """
    any_hit = False
    for proj in projectiles:
        if not proj.alive:
            continue
        for enemy in enemies:
            if not enemy.alive:
                continue
            if proj.pos.distance_to(enemy.pos) < proj.radius + enemy.radius:
                enemy.take_damage(proj.damage)
                if player is not None and LIFESTEAL_PER_HIT:
                    player.hp = min(player.max_hp, player.hp + LIFESTEAL_PER_HIT)
                dmg_numbers.append(
                    DamageNumber(enemy.pos.x, enemy.pos.y - 14, proj.damage)
                )
                if not enemy.alive:
                    kills.append(enemy)
                else:
                    any_hit = True
                if not proj.pierce:
                    proj.alive = False
                    break
    return any_hit


def check_enemy_contact(enemies: list, player: Player,
                        player_center: pygame.math.Vector2) -> None:
    for enemy in enemies:
        if not enemy.alive:
            continue
        if enemy.pos.distance_to(player_center) < PLAYER_RADIUS + enemy.radius + MELEE_REACH:
            if isinstance(enemy, (Boss, SuperBoss)):
                # Bosse töten den Spieler bei Berührung mit einem Treffer
                if enemy.melee_attack():
                    player.take_damage(player.max_hp)
            elif (dmg := enemy.melee_attack()):
                player.take_damage(dmg)
            # Gegner bleibt am Leben — nur Projektile töten ihn


def apply_upgrade(upgrade_id: str, stats: dict, player=None) -> None:
    if   upgrade_id == "damage":    stats["damage"]       += UPGRADE_DAMAGE
    elif upgrade_id == "speed":     stats["bullet_speed"] += UPGRADE_BULLET_SPEED
    elif upgrade_id == "size":      stats["bullet_size"]  += UPGRADE_BULLET_SIZE
    elif upgrade_id == "attackspeed": stats["attack_speed"] *= (1 + UPGRADE_ATTACK_SPEED)
    elif upgrade_id == "multishot": stats["multishot"]     = True
    elif upgrade_id == "pierce":    stats["pierce"]        = True
    elif upgrade_id == "max_hp" and player is not None:
        player.max_hp += UPGRADE_MAX_HP
        player.hp      = min(player.hp + UPGRADE_MAX_HP, player.max_hp)


def fresh_game_state(wave: int = 1) -> dict:
    return dict(wave=wave, spawn_remaining=enemies_for_wave(wave),
                spawn_timer=0, wave_clear_timer=0,
                enemies=[], projectiles=[], enemy_projectiles=[],
                pending_shots=[],
                obtained=set(), coins=0,
                # XP/Level (ADR 008): Karten kommen jetzt aus Level-ups, nicht pro Welle
                xp=0, level=1, xp_to_next=xp_to_next(1, wave), pending_levelups=0,
                fire_timer=0,   # Cooldown bis zum nächsten Auto-Schuss (ADR 009)
                stats=dict(damage=10, bullet_speed=10, bullet_size=5,
                           pierce=False, multishot=False,
                           attack_speed=BASE_ATTACK_SPEED),
                banner=None)


# ---------------------------------------------------------------------------
# HUD & Overlays
# ---------------------------------------------------------------------------

_HUD_H = 38   # Höhe der HUD-Labels


def draw_hud(screen: pygame.Surface, font: pygame.font.Font,
             wave: int, remaining: int, coins: int,
             level: int = 1, xp: int = 0, xp_to_next: int = 1) -> None:
    pad = 70   # extra Breite links+rechts im Label (Platz für die Caps)

    # Welle – Ribbon (gelb, Zeile 2)
    wave_txt  = f"Welle  {wave}"
    wave_tw   = font.size(wave_txt)[0]
    wave_rect = pygame.Rect(8, 8, wave_tw + pad, _HUD_H)
    ui_loader.draw_ribbon_label(screen, wave_rect, wave_txt, font, row=2)

    # Gegner – Sword (Zeile 0, braun)
    enemy_txt  = f"Gegner {remaining}"
    enemy_tw   = font.size(enemy_txt)[0]
    enemy_rect = pygame.Rect(8, 8 + _HUD_H + 6, enemy_tw + pad, _HUD_H)
    ui_loader.draw_sword_label(screen, enemy_rect, enemy_txt, font, row=0)

    # Münzen – Icon + Zahl (kein Panel)
    icon_size = 32
    coin_txt  = f"{coins}"
    ctw, cth  = font.size(coin_txt)
    total_w   = icon_size + 6 + ctw
    cx        = SCREEN_WIDTH - total_w - 14
    cy        = 8 + (_HUD_H - icon_size) // 2
    ui_loader.draw_coin_icon(screen,
                             cx + icon_size // 2,
                             cy + icon_size // 2,
                             icon_size)
    screen.blit(font.render(coin_txt, True, (255, 220, 60)),
                (cx + icon_size + 6,
                 cy + (icon_size - cth) // 2))

    # Level + XP-Bar (unten zentriert, ADR 008)
    bar_w, bar_h = 420, 12
    bar_x = (SCREEN_WIDTH - bar_w) // 2
    bar_y = SCREEN_HEIGHT - bar_h - 12
    ratio = max(0.0, min(1.0, xp / xp_to_next)) if xp_to_next > 0 else 0.0
    pygame.draw.rect(screen, (18, 20, 34), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
    if ratio > 0:
        pygame.draw.rect(screen, (90, 200, 255),
                         (bar_x, bar_y, int(bar_w * ratio), bar_h), border_radius=6)
    pygame.draw.rect(screen, (70, 95, 130), (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=6)
    lbl = font.render(f"Lvl {level}   {xp}/{xp_to_next} XP", True, (190, 225, 255))
    screen.blit(lbl, (SCREEN_WIDTH // 2 - lbl.get_width() // 2, bar_y - lbl.get_height() - 2))


def draw_game_over(screen, font_big, font, wave, coins_earned, best_wave, new_record):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))
    cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

    rows = [
        (font_big.render("GAME OVER",                     True, (220,  50,  50)), cy - 90),
        (font.render(f"Welle {wave} erreicht",            True, (220, 220, 220)), cy - 15),
        (font.render(f"+{coins_earned} Münzen verdient",  True, COLOR_COIN),      cy + 22),
    ]
    if new_record:
        rows.append((font.render("★  NEUER REKORD!  ★",  True, (255, 220, 60)),  cy + 58))
    else:
        rows.append((font.render(f"Rekord: Welle {best_wave}",
                                  True, (130, 130, 150)),                          cy + 58))
    rows.append((font.render("R — Neustart   |   M — Hauptmenü",
                              True, (120, 120, 140)),                              cy + 96))

    for surf, y in rows:
        screen.blit(surf, (cx - surf.get_width() // 2, y))


def draw_victory(screen, font_big, font, wave, coins_earned, best_wave, new_record):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((10, 12, 30, 205))
    screen.blit(overlay, (0, 0))
    cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

    rows = [
        (font_big.render("SIEG!",                         True, (255, 220,  60)), cy - 100),
        (font.render("SuperBoss in Welle 100 bezwungen",  True, (220, 220, 240)), cy - 24),
        (font.render(f"+{coins_earned} Münzen verdient",  True, COLOR_COIN),      cy + 14),
    ]
    if new_record:
        rows.append((font.render("★  NEUER REKORD!  ★",  True, (255, 220, 60)),  cy + 52))
    else:
        rows.append((font.render(f"Rekord: Welle {best_wave}",
                                  True, (130, 130, 150)),                          cy + 52))
    rows.append((font.render("R — Neuer Lauf   |   M — Hauptmenü",
                              True, (120, 120, 140)),                              cy + 92))

    for surf, y in rows:
        screen.blit(surf, (cx - surf.get_width() // 2, y))


def draw_boss_bar(screen: pygame.Surface, font: pygame.font.Font,
                  enemies: list) -> None:
    boss = next((e for e in enemies if isinstance(e, (Boss, SuperBoss)) and e.alive), None)
    if not boss:
        return
    is_super = isinstance(boss, SuperBoss)
    bar_w  = SCREEN_WIDTH - 40
    bar_h  = 28
    bar_x  = 20
    bar_y  = 6
    ratio  = max(0.0, boss.hp / boss.max_hp)
    name   = "SUPER BOSS" if is_super else "BOSS"

    ui_loader.draw_bar(screen, pygame.Rect(bar_x, bar_y, bar_w, bar_h), ratio, big=True)
    label = font.render(f"{name}   {boss.hp} / {boss.max_hp}", True, (255, 255, 255))
    screen.blit(label, (SCREEN_WIDTH // 2 - label.get_width() // 2, bar_y + 4))


# ---------------------------------------------------------------------------
# Kamera-Zoom (ADR 007)
# ---------------------------------------------------------------------------

def blit_world_zoomed(screen: pygame.Surface, world: pygame.Surface, zoom: float) -> None:
    """Skaliert den zentralen 1/zoom-Ausschnitt der Welt formatfüllend auf den Screen.

    Da um die Bildmitte (= Turm) skaliert wird, bleiben Schussrichtungen (Winkel vom
    Turm zur Maus) erhalten — Zielen funktioniert unverändert. HUD/Menüs werden danach
    unskaliert obendrauf gezeichnet.
    """
    if zoom == 1.0:
        screen.blit(world, (0, 0))
        return
    w, h   = world.get_size()
    cw, ch = int(w / zoom), int(h / zoom)
    x, y   = (w - cw) // 2, (h - ch) // 2
    crop   = world.subsurface((x, y, cw, ch))
    pygame.transform.smoothscale(crop, (w, h), screen)


# ---------------------------------------------------------------------------
# Hauptschleife
# ---------------------------------------------------------------------------

def main():
    pygame.init()
    screen   = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
    pygame.display.set_caption(TITLE)
    clock    = pygame.time.Clock()
    world_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))   # Welt wird hier gezeichnet, dann gezoomt geblittet

    # Custom cursor
    import os as _os
    _cur_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
        "assets", "Tiny Swords (Free Pack)", "UI Elements", "UI Elements",
        "Cursors", "Cursor_01.png")
    _cursor_raw = pygame.image.load(_cur_path).convert_alpha()
    _cursor_img = pygame.transform.smoothscale(_cursor_raw, (32, 32))
    pygame.mouse.set_visible(False)
    font     = pygame.font.SysFont("Arial", 22, bold=True)
    font_big = pygame.font.SysFont("Arial", 56, bold=True)
    font_dmg = pygame.font.SysFont("Arial", 15, bold=True)

    save         = sd.load()
    main_menu    = MainMenu()
    options_menu = OptionsMenu()   # difficulty="Normal", sfx=70%, music=50%
    impr_menu    = ImprovementsMenu()
    upgrade_menu = UpgradeMenu(SCREEN_WIDTH, SCREEN_HEIGHT)
    snd          = sounds.SoundManager()
    options_menu.load_settings(save.get("settings", {}))
    snd.set_sfx_vol(options_menu.sfx_volume)
    snd.set_music_vol(options_menu.music_volume)
    snd.start_menu_music()

    # Pause-Buttons (3 Stück, zentriert)
    _pbw, _pbh, _pgap = 280, 52, 12
    _pcx = SCREEN_WIDTH  // 2
    _pcy = SCREEN_HEIGHT // 2
    pause_btn_continue = Button(
        pygame.Rect(_pcx - _pbw // 2, _pcy - 30,                    _pbw, _pbh), "Weiter spielen", (60, 200, 100))
    pause_btn_options  = Button(
        pygame.Rect(_pcx - _pbw // 2, _pcy - 30 + (_pbh + _pgap),   _pbw, _pbh), "Optionen",       (60, 160, 220))
    pause_btn_menu     = Button(
        pygame.Rect(_pcx - _pbw // 2, _pcy - 30 + (_pbh + _pgap)*2, _pbw, _pbh), "Zum Hauptmenü",  (200, 60,  60))
    pause_overlay      = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pause_overlay.fill((0, 0, 0, 170))

    player      = None
    pc          = None
    gs          = None
    terrain     = None
    dmg_numbers = []
    diff_mod    = options_menu.get_modifiers()
    new_record          = False
    prev_state          = None
    mouse_held          = False         # linke Maustaste gedrückt → Auto-Feuer (ADR 009)
    options_return_to   = "MAIN_MENU"   # wohin OPTIONS-Zurück geht
    state               = "MAIN_MENU"

    def start_run():
        nonlocal player, pc, gs, terrain, dmg_numbers, diff_mod
        diff_mod    = options_menu.get_modifiers()
        player      = Player()
        pc          = pygame.math.Vector2(player.x, player.y)
        gs          = fresh_game_state()
        terrain     = Terrain()
        dmg_numbers = []
        apply_permanent_bonuses(player, gs["stats"], save)
        snd.start_run_music()

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()

                if event.key == pygame.K_ESCAPE:
                    if state in ("PLAYING", "WAVE_CLEAR", "UPGRADE"):
                        prev_state = state
                        state = "PAUSED"
                        pygame.mixer.music.pause()
                    elif state == "PAUSED":
                        state = prev_state
                        pygame.mixer.music.unpause()
                    else:
                        running = False
                if state in ("GAME_OVER", "VICTORY"):
                    if event.key == pygame.K_r:
                        start_run()
                        state = "PLAYING"
                    elif event.key == pygame.K_m:
                        gs      = None   # Lauf beenden → Shop im Menü wieder zugänglich
                        terrain = None
                        snd.start_menu_music()
                        state = "MAIN_MENU"

                # --- Dev-Tasten (nur im laufenden Spiel) ---
                if state == "PLAYING" and gs:
                    if event.key == pygame.K_F1:
                        # Alle Gegner sofort töten → normaler Wave-Clear
                        for e in gs["enemies"]: e.alive = False
                        gs["spawn_remaining"] = 0
                    elif event.key == pygame.K_F2:
                        # Auf Welle 9 springen (nächste Clear → Boss Welle 10)
                        gs["wave"]            = 9
                        for e in gs["enemies"]: e.alive = False
                        gs["spawn_remaining"] = 0
                    elif event.key == pygame.K_F3:
                        # Auf Welle 49 springen (nächste Clear → SuperBoss Welle 50)
                        gs["wave"]            = 49
                        for e in gs["enemies"]: e.alive = False
                        gs["spawn_remaining"] = 0
                    elif event.key == pygame.K_F4:
                        # Auf Welle 99 springen (nächste Clear → SuperBoss Welle 100 → Sieg)
                        gs["wave"]            = 99
                        for e in gs["enemies"]: e.alive = False
                        gs["spawn_remaining"] = 0
                    elif event.key == pygame.K_F5:
                        # Dev: einen Levelup erzwingen (Karten-Auswahl testen)
                        gs["level"]            += 1
                        gs["pending_levelups"] += 1
                        gs["xp_to_next"]        = xp_to_next(gs["level"], gs["wave"])

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == "MAIN_MENU":
                    action = main_menu.handle_click(mouse_pos, run_active=gs is not None)
                    if action == "start":
                        start_run()
                        state = "PLAYING"
                    elif action == "options":
                        snd.play("ui_click")
                        options_return_to = "MAIN_MENU"
                        state = "OPTIONS"
                    elif action == "improvements": snd.play("ui_click"); state = "IMPROVEMENTS"
                    elif action == "quit":         running = False

                elif state == "OPTIONS":
                    # Drag auf Lautstärke-Balken starten
                    drag_key = options_menu.start_drag(mouse_pos)
                    if drag_key:
                        if drag_key == "sfx":   snd.set_sfx_vol(options_menu.sfx_volume)
                        else:                   snd.set_music_vol(options_menu.music_volume)
                    else:
                        result = options_menu.handle_click(mouse_pos)
                        if result == "back":
                            snd.play("ui_click")
                            state = options_return_to
                        elif result == "sfx_changed":
                            snd.set_sfx_vol(options_menu.sfx_volume)
                            snd.play("ui_click")
                        elif result == "music_changed":
                            snd.set_music_vol(options_menu.music_volume)
                        if result and result != "back":
                            save["settings"] = options_menu.get_settings()
                            sd.save(save)

                elif state == "IMPROVEMENTS":
                    if impr_menu.handle_click(mouse_pos, save) == "back":
                        state = "MAIN_MENU"

                elif state == "PAUSED":
                    if pause_btn_continue.is_hovered(mouse_pos):
                        state = prev_state
                        pygame.mixer.music.unpause()
                    elif pause_btn_options.is_hovered(mouse_pos):
                        snd.play("ui_click")
                        options_return_to = "PAUSED"
                        state = "OPTIONS"
                    elif pause_btn_menu.is_hovered(mouse_pos):
                        gs      = None
                        terrain = None
                        snd.start_menu_music()
                        state = "MAIN_MENU"

                elif state == "PLAYING":
                    mouse_held = True          # Halten feuert; erster Schuss sofort
                    gs["fire_timer"] = 0

                elif state == "UPGRADE":
                    chosen = upgrade_menu.handle_click(mouse_pos)
                    if chosen:
                        apply_upgrade(chosen, gs["stats"], player)
                        gs["obtained"].add(chosen)
                        gs["pending_levelups"] = max(0, gs["pending_levelups"] - 1)
                        if gs["pending_levelups"] > 0:
                            upgrade_menu.roll(gs["obtained"])   # weitere Level-up-Karte
                        else:
                            state = "PLAYING"

            if event.type == pygame.MOUSEMOTION:
                if state == "OPTIONS":
                    changed = options_menu.update_drag(mouse_pos)
                    if changed:
                        if changed == "sfx":   snd.set_sfx_vol(options_menu.sfx_volume)
                        else:                  snd.set_music_vol(options_menu.music_volume)

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_held = False         # Maustaste losgelassen → Auto-Feuer stoppt
                if state == "OPTIONS":
                    key = options_menu.stop_drag()
                    if key:
                        save["settings"] = options_menu.get_settings()
                        sd.save(save)

        # --- Update ---
        spawn_interval = BASE_SPAWN_INTERVAL + diff_mod["spawn_bonus"]

        if state == "PLAYING":
            gs["spawn_timer"] += 1
            # Concurrent-Cap: nur nachspawnen, wenn nicht schon zu viele am Turm stehen
            if (gs["spawn_remaining"] > 0 and gs["spawn_timer"] >= spawn_interval
                    and len(gs["enemies"]) < MAX_CONCURRENT_ENEMIES):
                gs["enemies"].append(
                    spawn_enemy_for_wave(gs["wave"], diff_mod["hp_mult"])
                )
                gs["spawn_remaining"] -= 1
                gs["spawn_timer"]      = 0

            # Auto-Feuer beim Halten der Maustaste, getaktet vom Angriffstempo (ADR 009)
            if gs["fire_timer"] > 0:
                gs["fire_timer"] -= 1
            if mouse_held and gs["fire_timer"] <= 0:
                aim = pygame.mouse.get_pos()
                gs["projectiles"] += spawn_projectiles(pc, aim, gs["stats"])
                snd.play("shoot")
                if "doppelschuss" in save["bought"]:
                    gs["pending_shots"].append((DOPPELSCHUSS_DELAY, aim))
                gs["fire_timer"] = max(1, round(FPS / gs["stats"]["attack_speed"]))

            # Doppelschuss: zweite Kugel nach 8 Frames
            next_pending = []
            for delay, mp in gs["pending_shots"]:
                delay -= 1
                if delay <= 0:
                    gs["projectiles"] += spawn_projectiles(pc, mp, gs["stats"])
                    snd.play("shoot")
                else:
                    next_pending.append((delay, mp))
            gs["pending_shots"] = next_pending

            for e in gs["enemies"]:
                e.update(pc)
                if isinstance(e, Archer):
                    gs["enemy_projectiles"] += e.pop_shots()
                elif isinstance(e, Monk):
                    e.heal_nearby(gs["enemies"])
            for p in gs["projectiles"]:        p.update()
            for ep in gs["enemy_projectiles"]: ep.update()

            kills    = []
            had_hits = check_projectile_hits(gs["projectiles"], gs["enemies"], dmg_numbers, kills, player)
            if had_hits: snd.play("hit")
            check_enemy_contact(gs["enemies"], player, pc)

            # Archer-Pfeile treffen Spieler
            for ep in gs["enemy_projectiles"]:
                if ep.alive and ep.pos.distance_to(pc) < ep.RADIUS + PLAYER_RADIUS:
                    player.take_damage(ep.DAMAGE)
                    ep.alive = False

            gs["enemy_projectiles"] = [ep for ep in gs["enemy_projectiles"] if ep.alive]

            # Münzen & Kill-Sounds
            gold_mult = GOLD_BOOST_MULT if "gold_boost" in save["bought"] else 1.0
            for enemy in kills:
                if isinstance(enemy, SuperBoss):
                    snd.play("kill_superboss")
                    snd.start_run_music()
                elif isinstance(enemy, Boss):
                    snd.play("kill_boss")
                    snd.start_run_music()
                elif isinstance(enemy, Lancer):     snd.play("kill_tanker")
                else:                               snd.play("kill")
                val = int(coin_value_for_wave(gs["wave"]) * enemy.coin_value * gold_mult)
                gs["coins"] += val
                gs["xp"]    += enemy.coin_value   # XP-Drop = Münzwert des Gegners (ADR 008)
                dmg_numbers.append(
                    DamageNumber(enemy.pos.x, enemy.pos.y - 28, val,
                                 color=COLOR_COIN, prefix="+")
                )

            # XP → Level-up(s): eine große XP-Charge kann mehrere Stufen auslösen
            while gs["xp"] >= gs["xp_to_next"]:
                gs["xp"]               -= gs["xp_to_next"]
                gs["level"]            += 1
                gs["pending_levelups"] += 1
                gs["xp_to_next"]        = xp_to_next(gs["level"], gs["wave"])

            gs["enemies"]     = [e for e in gs["enemies"]     if e.alive]
            gs["projectiles"] = [p for p in gs["projectiles"] if p.alive]

            for dn in dmg_numbers: dn.update()
            dmg_numbers = [dn for dn in dmg_numbers if dn.alive]

            if not player.alive:
                new_record = (gs["wave"]   > save["best_wave"] or
                              gs["coins"]  > save["best_coins"])
                save["best_wave"]   = max(save["best_wave"],  gs["wave"])
                save["best_coins"]  = max(save["best_coins"], gs["coins"])
                save["total_coins"] += gs["coins"]
                sd.save(save)
                snd.stop_music()
                snd.play("game_over")
                state = "GAME_OVER"
            elif gs["spawn_remaining"] == 0 and not gs["enemies"]:
                if gs["wave"] >= WIN_WAVE:
                    # Welle 100 geräumt = SuperBoss besiegt → Sieg (ADR 004)
                    new_record = (gs["wave"]  > save["best_wave"] or
                                  gs["coins"] > save["best_coins"])
                    save["best_wave"]   = max(save["best_wave"],  gs["wave"])
                    save["best_coins"]  = max(save["best_coins"], gs["coins"])
                    save["total_coins"] += gs["coins"]
                    sd.save(save)
                    snd.stop_music()
                    snd.play("wave_clear")
                    state = "VICTORY"
                else:
                    snd.play("wave_clear")
                    state                  = "WAVE_CLEAR"
                    gs["wave_clear_timer"] = 0
            elif gs["pending_levelups"] > 0:
                # Levelup mitten in der Welle → Karte wählen, dann weiterspielen (ADR 008)
                snd.play("wave_clear")
                upgrade_menu.roll(gs["obtained"])
                state = "UPGRADE"

            if gs.get("banner") and gs["banner"]["timer"] > 0:
                gs["banner"]["timer"] -= 1

        elif state == "WAVE_CLEAR":
            # Projektile & FX laufen weiter damit der Bildschirm nicht einfriert
            for p  in gs["projectiles"]:        p.update()
            for ep in gs["enemy_projectiles"]:  ep.update()
            gs["projectiles"]        = [p  for p  in gs["projectiles"]        if p.alive]
            gs["enemy_projectiles"]  = [ep for ep in gs["enemy_projectiles"]  if ep.alive]
            for dn in dmg_numbers: dn.update()
            dmg_numbers = [dn for dn in dmg_numbers if dn.alive]

            gs["wave_clear_timer"] += 1
            if gs["wave_clear_timer"] >= WAVE_CLEAR_DELAY:
                # Nächste Welle starten (Karten kommen jetzt aus Level-ups, nicht hier)
                gs["wave"]           += 1
                gs["spawn_remaining"] = enemies_for_wave(gs["wave"])
                gs["spawn_timer"]     = 0
                if gs["wave"] % 50 == 0:
                    gs["banner"] = {"text": "SUPER BOSS!", "color": (220, 20, 40), "timer": 180}
                    snd.play("boss_intro")
                    snd.start_boss_music()
                elif gs["wave"] % 10 == 0:
                    gs["banner"] = {"text": "BOSS WELLE!", "color": (255, 155, 25), "timer": 180}
                    snd.play("boss_intro")
                    snd.start_boss_music()
                state = "PLAYING"

        elif state == "UPGRADE":
            # Projektile & FX fliegen noch ab während Overlay einfadet
            for p in gs["projectiles"]: p.update()
            gs["projectiles"] = [p for p in gs["projectiles"] if p.alive]
            for dn in dmg_numbers: dn.update()
            dmg_numbers = [dn for dn in dmg_numbers if dn.alive]
            upgrade_menu.tick()

        # --- Draw ---
        if state == "MAIN_MENU":
            main_menu.draw(screen, mouse_pos, save,
                           run_active=gs is not None, best_wave=save["best_wave"])
        elif state == "OPTIONS":
            options_menu.draw(screen, mouse_pos)
        elif state == "IMPROVEMENTS":
            impr_menu.draw(screen, mouse_pos, save)
        else:
            # --- Welt in eigenes Surface zeichnen, dann gezoomt auf den Screen ---
            if terrain:
                terrain.draw(world_surf)
            else:
                world_surf.fill(BG_COLOR)
            if gs:
                for e  in gs["enemies"]:            e.draw(world_surf)
                for p  in gs["projectiles"]:        p.draw(world_surf)
                for ep in gs["enemy_projectiles"]:  ep.draw(world_surf)
            if player:
                player.draw(world_surf, mouse_pos)
            for dn in dmg_numbers:
                dn.draw(world_surf, font_dmg)
            blit_world_zoomed(screen, world_surf, CAMERA_ZOOM)

            # --- HUD & Overlays unskaliert obendrauf ---
            if gs and player:
                draw_hud(screen, font, gs["wave"],
                         len(gs["enemies"]) + gs["spawn_remaining"],
                         gs["coins"], gs["level"], gs["xp"], gs["xp_to_next"])
            if gs and state in ("PLAYING", "WAVE_CLEAR"):
                draw_boss_bar(screen, font, gs["enemies"])
            if gs and gs.get("banner") and gs["banner"]["timer"] > 0:
                b     = gs["banner"]
                alpha = min(255, b["timer"] * 4)
                bsurf = font_big.render(b["text"], True, b["color"])
                bsurf.set_alpha(alpha)
                screen.blit(bsurf, (SCREEN_WIDTH  // 2 - bsurf.get_width()  // 2,
                                    SCREEN_HEIGHT // 2 - 70))
            # Dev-Hint (linke untere Ecke)
            if gs and state == "PLAYING":
                hint = font_dmg.render("F1 Clear  F2→W10  F3→W50  F4→W100  F5 Lvl+", True, (55, 55, 75))
                screen.blit(hint, (6, SCREEN_HEIGHT - hint.get_height() - 6))
            if options_menu.show_fps:
                fps_surf = font.render(f"FPS  {int(clock.get_fps())}", True, (80, 80, 100))
                screen.blit(fps_surf, (SCREEN_WIDTH - fps_surf.get_width() - 12,
                                       SCREEN_HEIGHT - fps_surf.get_height() - 10))

            if state == "WAVE_CLEAR":
                msg = font_big.render("Welle geschafft!", True, (255, 220, 60))
                screen.blit(msg, (SCREEN_WIDTH  // 2 - msg.get_width()  // 2,
                                   SCREEN_HEIGHT // 2 - msg.get_height() // 2))
            elif state == "PAUSED":
                screen.blit(pause_overlay, (0, 0))
                ptitle = font_big.render("PAUSE", True, (255, 220, 60))
                screen.blit(ptitle, (_pcx - ptitle.get_width() // 2, _pcy - 120))
                pause_btn_continue.draw(screen, font, mouse_pos)
                pause_btn_options.draw(screen,  font, mouse_pos)
                pause_btn_menu.draw(screen,     font, mouse_pos)
            elif state == "UPGRADE":
                upgrade_menu.draw(screen)
            elif state == "GAME_OVER":
                draw_game_over(screen, font_big, font,
                               gs["wave"], gs["coins"],
                               save["best_wave"], new_record)
            elif state == "VICTORY":
                draw_victory(screen, font_big, font,
                             gs["wave"], gs["coins"],
                             save["best_wave"], new_record)

        # Cursor immer zuletzt zeichnen
        mx, my = pygame.mouse.get_pos()
        screen.blit(_cursor_img, (mx, my))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
