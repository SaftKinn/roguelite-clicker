import sys
import random
from game import sounds
sounds.init_mixer()          # vor pygame.init()!
import pygame
from game.constants    import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, BG_COLOR
from game.player       import Player, RADIUS as PLAYER_RADIUS, MAX_HP
from game.enemy        import (Warrior, Archer, Lancer, Monk, Goblin, OrcBerserker,
                              Necromancer, Boss, SuperBoss, EnemyProjectile,
                              SkeletonWarrior, BoneSwarmling, SkeletonArcher, BoneColossus, Lich,
                              ImpWarrior, Hellhound, DemonCaster, PitBrute, DemonSummoner,
                              DrakeWarrior, Wyrmling, DrakeArcher, ScaleTitan, DragonPriest,
                              RADIUS as ENEMY_RADIUS)
from game.projectile   import Projectile
from game.upgrade_menu import UpgradeMenu
from game.main_menu    import (MainMenu, OptionsMenu, ImprovementsMenu, BestiaryMenu,
                               SlotSelectMenu, IMPROVEMENTS, Button)
from game.fx           import DamageNumber, COLOR_COIN
from game.terrain      import Terrain
from game import save_data  as sd
from game import ui_loader
from game.balance     import (MELEE_REACH,
                              WIN_WAVE, MAX_CONCURRENT_ENEMIES, CAMERA_ZOOM,
                              enemies_for_wave, spawn_interval_ticks, enemy_hp_for_wave, wave_tier_mult,
                              enemy_speed_for_wave, coin_value_for_wave, xp_to_next,
                              xp_wave_mult, xp_round_mult, XP_GAIN_MULT, COIN_GAIN_MULT, ATTACK_RANGE_FRAC,
                              UPGRADE_DAMAGE, UPGRADE_BULLET_SPEED,
                              UPGRADE_BULLET_SIZE, UPGRADE_MAX_HP, MULTISHOT_ANGLES,
                              BASE_DAMAGE, BASE_ATTACK_SPEED, UPGRADE_ATTACK_SPEED, LIFESTEAL_PER_HIT,
                              PERMANENT_DAMAGE_PER_LEVEL, PERMANENT_HP_PER_LEVEL,
                              GOLD_BOOST_MULT, DOPPELSCHUSS_DELAY,
                              ELITE_SPAWN_CHANCE, ELITE_HP_MULT, elite_hp_mult, ELITE_REWARD_MULT,
                              ELITE_COLOR,
                              # Karten-Farbgruppen (ADR 025)
                              UPGRADE_LIFESTEAL_PCT, UPGRADE_LIFESTEAL_FLAT,
                              UPGRADE_ARMOR_PCT, ARMOR_CAP, UPGRADE_HP_REGEN,
                              UPGRADE_THORNS_PCT, THORNS_CAP, UPGRADE_DODGE_PCT, DODGE_CAP,
                              UPGRADE_COIN_PCT, UPGRADE_XP_PCT, UPGRADE_REROLL_CHARGES,
                              # Shop-Ausbau (ADR 026)
                              PERMANENT_ATTACK_SPEED_PER_LEVEL, PERMANENT_BULLET_SIZE_PER_LEVEL,
                              PERMANENT_LIFESTEAL_PER_LEVEL, PERMANENT_COIN_MULT_PER_LEVEL,
                              PERMANENT_XP_MULT_PER_LEVEL, PERMANENT_FREE_REROLLS_PER_LEVEL,
                              DEFAULT_CARD_COUNT, EXTRA_CARD_COUNT)

WAVE_CLEAR_DELAY    = 70    # kürzere Pause zwischen Wellen (knackiger, ADR 008)
CONTACT_DIST        = PLAYER_RADIUS + ENEMY_RADIUS
# Reichweite des Turms = sichtbare Halb-Höhe / Zoom × Anteil → Gegner sterben immer im Bild.
PLAYER_ATTACK_RANGE = (SCREEN_HEIGHT / 2) / CAMERA_ZOOM * ATTACK_RANGE_FRAC


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


# Tier-Roster (ADR 024): pro 50-Wellen-Abschnitt eine reskinnte Variante je Rolle.
# tanker (Lancer) und monk (Monk) behalten ihr Tiny-Swords-Original über alle Tiers.
TIER_ROSTER = [
    {"basic": SkeletonWarrior, "rusher": SkeletonArcher, "goblin": BoneSwarmling,
     "orc": BoneColossus, "necro": Lich},                          # Welle 1–50   (Untote)
    {"basic": ImpWarrior, "rusher": DemonCaster, "goblin": Hellhound,
     "orc": PitBrute, "necro": DemonSummoner},                     # Welle 51–100  (Dämonen)
    {"basic": DrakeWarrior, "rusher": DrakeArcher, "goblin": Wyrmling,
     "orc": ScaleTitan, "necro": DragonPriest},                    # Welle 101–150 (Drachen-Brut)
]


def tier_for_wave(wave: int) -> int:
    """0 = Welle 1–50, 1 = 51–100, 2 = 101–150 (gedeckelt)."""
    return min((wave - 1) // 50, len(TIER_ROSTER) - 1)


def spawn_enemy_for_wave(wave: int, hp_mult: float) -> Warrior:
    base_hp    = enemy_hp_for_wave(wave, hp_mult)
    base_speed = enemy_speed_for_wave(wave)
    if wave % 50 == 0:
        return SuperBoss(base_speed, base_hp)
    if wave % 10 == 0:
        return Boss(base_speed, base_hp)
    if wave < 3:
        kinds, weights = ["basic"],                                            [1]
    elif wave < 5:
        kinds, weights = ["basic", "rusher", "goblin"],                        [55, 25, 20]
    elif wave < 7:
        kinds, weights = ["basic", "rusher", "tanker", "goblin"],              [38, 28, 16, 18]
    elif wave < 12:
        kinds          = ["basic", "rusher", "tanker", "monk", "goblin", "orc"]
        weights        = [30, 22, 14, 10, 16, 8]
    else:
        kinds          = ["basic", "rusher", "tanker", "monk", "goblin", "orc", "necro"]
        weights        = [24, 18, 12, 9, 16, 10, 11]
    kind = random.choices(kinds, weights=weights)[0]
    # tanker (Lancer) und monk (Monk) bleiben über alle Tiers ihr Tiny-Swords-Original;
    # die übrigen Rollen (basic/rusher/goblin/orc/necro) liefert das Tier-Roster reskinnt.
    if   kind == "tanker": enemy = Lancer(base_speed, base_hp)
    elif kind == "monk":   enemy = Monk(base_speed, base_hp)
    else:                  enemy = TIER_ROSTER[tier_for_wave(wave)][kind](base_speed, base_hp)
    # Wellen-Härte: alle 10 Wellen +40 % auf Schaden (HP steckt schon in base_hp via
    # enemy_hp_for_wave). Kompoundierend mit der Wellenhöhe.
    enemy.dmg_mult = wave_tier_mult(wave)
    # Elite: mit ELITE_SPAWN_CHANCE wird ein Nicht-Boss-Gegner zum zähen Brocken (×ELITE_HP_MULT HP).
    # coin_value skaliert mit ELITE_REWARD_MULT → mehr Münzen UND XP (coin_value speist beides).
    if random.random() < ELITE_SPAWN_CHANCE:
        enemy.max_hp      = int(enemy.max_hp * elite_hp_mult(wave))   # gestuft: alle 10 Wellen +100%
        enemy.hp          = enemy.max_hp
        enemy.coin_value *= ELITE_REWARD_MULT
        enemy.elite       = True
    return enemy


def _sync_player_defense(stats: dict, player: Player) -> None:
    """Spiegelt die Verteidigungs-/Lifesteal-Werte aus gs["stats"] auf das `player`-Objekt,
    damit die Treffer-Funktionen (take_damage, check_projectile_hits) sie direkt kennen (ADR 025)."""
    player.armor          = stats["armor"]
    player.dodge          = stats["dodge"]
    player.thorns_pct     = stats["thorns_pct"]
    player.hp_regen       = stats["hp_regen"]
    player.lifesteal_flat = stats["lifesteal_flat"]
    player.lifesteal_pct  = stats["lifesteal_pct"]


def apply_permanent_bonuses(player: Player, stats: dict, save: dict) -> None:
    upgrades = save.get("upgrades", {})
    stats["damage"]       += upgrades.get("start_damage", 0)       * PERMANENT_DAMAGE_PER_LEVEL
    stats["attack_speed"] += upgrades.get("start_attack_speed", 0) * PERMANENT_ATTACK_SPEED_PER_LEVEL
    stats["bullet_size"]  += upgrades.get("start_bullet_size", 0)  * PERMANENT_BULLET_SIZE_PER_LEVEL
    stats["lifesteal_flat"]+= upgrades.get("start_lifesteal", 0)   * PERMANENT_LIFESTEAL_PER_LEVEL
    stats["rerolls"]       = upgrades.get("free_rerolls", 0)       * PERMANENT_FREE_REROLLS_PER_LEVEL
    bonus_hp = upgrades.get("start_hp", 0) * PERMANENT_HP_PER_LEVEL
    if bonus_hp > 0:
        player.max_hp += bonus_hp
        player.hp      = player.max_hp
    _sync_player_defense(stats, player)
    # gold_boost + doppelschuss + coin_mult/xp_mult werden inline im Gameplay gelesen


def _card_count(save: dict) -> int:
    """Karten pro Levelup: 4 wenn die „Vierte Karte" gekauft wurde (ADR 026), sonst 3."""
    return EXTRA_CARD_COUNT if "extra_card" in save.get("bought", []) else DEFAULT_CARD_COUNT


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


def nearest_enemy_pos(origin: pygame.math.Vector2, enemies: list, max_range: float = None):
    """Welt-Position des nächsten lebenden Gegners zu `origin` (für Autoaim), sonst None.

    Gegner-`pos` ist in Weltkoordinaten wie der Turm — `spawn_projectiles` normalisiert
    nur die Richtung, daher kann die Gegner-Position direkt als Ziel dienen (Zoom egal,
    weil zentriert). Vergleich über Distanz-Quadrat (kein sqrt).

    `max_range`: nur Gegner innerhalb dieser Reichweite werden anvisiert → Kills passieren
    im sichtbaren Bereich (sonst feuert der Turm nicht). None = unbegrenzt.
    """
    max_sq = None if max_range is None else max_range * max_range
    nearest, best = None, None
    for e in enemies:
        if not e.alive:
            continue
        d = origin.distance_squared_to(e.pos)
        if max_sq is not None and d > max_sq:
            continue
        if best is None or d < best:
            best, nearest = d, e
    return (nearest.pos.x, nearest.pos.y) if nearest else None


def check_projectile_hits(projectiles: list, enemies: list,
                          dmg_numbers: list, kills: list, player=None) -> bool:
    """Gibt True zurück wenn mindestens ein (nicht-tödlicher) Treffer erfolgte.

    Lifesteal (ADR 009/025): je Treffer heilt der Spieler die Basis `LIFESTEAL_PER_HIT`
    plus die Karten-Boni `lifesteal_flat` (flach) und `lifesteal_pct` (% des Schadens), bis max_hp.
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
                if player is not None:
                    heal = (LIFESTEAL_PER_HIT + player.lifesteal_flat
                            + proj.damage * player.lifesteal_pct)
                    if heal:
                        player.hp = min(player.max_hp, player.hp + heal)
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
                        player_center: pygame.math.Vector2) -> list:
    """Nahkampf-Kontakt der Gegner mit dem Turm. Gibt die Liste der Gegner zurück, die durch
    Dornen (ADR 025) gestorben sind, damit der Aufrufer Münzen/XP/Sound dafür bucht."""
    thorns_kills = []
    for enemy in enemies:
        if not enemy.alive:
            continue
        if enemy.pos.distance_to(player_center) < PLAYER_RADIUS + enemy.radius + MELEE_REACH:
            if isinstance(enemy, (Boss, SuperBoss)):
                # Bosse töten den Spieler bei Berührung mit einem Treffer — bewusst ungemindert
                # (Armor/Dodge greifen NICHT, sonst trivialisieren sie Bosse, ADR 025).
                if enemy.melee_attack():
                    player.hp = 0
            elif (dmg := enemy.melee_attack()):
                player.take_damage(dmg)
                # Dornen: Nahkämpfer nehmen einen Anteil des erlittenen (Vor-Armor-)Schadens zurück
                if player.thorns_pct:
                    enemy.take_damage(dmg * player.thorns_pct)
                    if not enemy.alive:
                        thorns_kills.append(enemy)
            # Gegner bleibt am Leben — nur Projektile/Dornen töten ihn
    return thorns_kills


def apply_upgrade(upgrade_id: str, stats: dict, player=None) -> None:
    # ROT — Schaden
    if   upgrade_id == "damage":    stats["damage"]       += UPGRADE_DAMAGE
    elif upgrade_id == "speed":     stats["bullet_speed"] += UPGRADE_BULLET_SPEED
    elif upgrade_id == "size":      stats["bullet_size"]  += UPGRADE_BULLET_SIZE
    elif upgrade_id == "attackspeed": stats["attack_speed"] += UPGRADE_ATTACK_SPEED
    elif upgrade_id == "multishot": stats["multishot"]     = True
    elif upgrade_id == "pierce":    stats["pierce"]        = True
    elif upgrade_id == "lifesteal_pct":  stats["lifesteal_pct"]  += UPGRADE_LIFESTEAL_PCT
    elif upgrade_id == "lifesteal_flat": stats["lifesteal_flat"] += UPGRADE_LIFESTEAL_FLAT
    # BLAU — Verteidigung
    elif upgrade_id == "armor":     stats["armor"]      = min(ARMOR_CAP,  stats["armor"]      + UPGRADE_ARMOR_PCT)
    elif upgrade_id == "thorns":    stats["thorns_pct"] = min(THORNS_CAP, stats["thorns_pct"] + UPGRADE_THORNS_PCT)
    elif upgrade_id == "dodge":     stats["dodge"]      = min(DODGE_CAP,  stats["dodge"]      + UPGRADE_DODGE_PCT)
    elif upgrade_id == "hp_regen":  stats["hp_regen"]  += UPGRADE_HP_REGEN
    elif upgrade_id == "max_hp" and player is not None:
        player.max_hp += UPGRADE_MAX_HP
        player.hp      = min(player.hp + UPGRADE_MAX_HP, player.max_hp)
    # GOLD — Geld (diesen Lauf) / WEISS — XP (diesen Lauf)
    elif upgrade_id == "coin_boost": stats["coin_mult"] += UPGRADE_COIN_PCT
    elif upgrade_id == "xp_boost":   stats["xp_mult"]   += UPGRADE_XP_PCT
    elif upgrade_id == "reroll":     stats["rerolls"]   += UPGRADE_REROLL_CHARGES
    if player is not None:
        _sync_player_defense(stats, player)


def fresh_game_state(wave: int = 1) -> dict:
    return dict(wave=wave, spawn_remaining=enemies_for_wave(wave),
                spawn_timer=0, wave_clear_timer=0,
                enemies=[], projectiles=[], enemy_projectiles=[],
                pending_shots=[],
                obtained=set(), coins=0,
                # XP/Level (ADR 008): Karten kommen jetzt aus Level-ups, nicht pro Welle
                xp=0, level=1, xp_to_next=xp_to_next(1, wave), pending_levelups=0,
                fire_timer=0,   # Cooldown bis zum nächsten Auto-Schuss (ADR 009)
                stats=dict(damage=BASE_DAMAGE, bullet_speed=10, bullet_size=5,
                           pierce=False, multishot=False,
                           attack_speed=BASE_ATTACK_SPEED,
                           # Karten-Farbgruppen (ADR 025) — alle Default „aus"
                           lifesteal_pct=0.0, lifesteal_flat=0,        # ROT
                           armor=0.0, hp_regen=0.0, thorns_pct=0.0, dodge=0.0,  # BLAU
                           coin_mult=1.0,                              # GOLD (Lauf)
                           xp_mult=1.0, rerolls=0),                    # WEISS (Lauf)
                _regen_accum=0.0,   # Laufzeit-Akku für HP-Regen (kein Balance-Wert)
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


def draw_stats_panel(screen: pygame.Surface, font: pygame.font.Font,
                     stats: dict, player, lifesteal: int) -> None:
    """Overlay mit den aktuellen Spieler-Stats (Toggle über Taste C)."""
    ja_nein = lambda b: "Ja" if b else "Nein"
    ls_flat = lifesteal + stats['lifesteal_flat']    # Basis + flacher Karten-Bonus
    rows = [
        ("Schaden/Kugel",  f"{stats['damage']}"),
        ("Angriffstempo",  f"{stats['attack_speed']:.2f}/s"),
        ("Kugeltempo",     f"{stats['bullet_speed']}"),
        ("Kugelgröße",     f"{stats['bullet_size']}"),
        ("Mehrfachschuss", ja_nein(stats['multishot'])),
        ("Durchschlag",    ja_nein(stats['pierce'])),
        ("Lifesteal",      f"{ls_flat} HP/Treffer"),
    ]
    # Defensiv-/Eco-Werte nur zeigen, wenn aktiv (Panel kompakt halten, ADR 025)
    if stats['lifesteal_pct'] > 0: rows.append(("Lifesteal %",  f"{int(stats['lifesteal_pct']*100)}%"))
    if stats['armor']        > 0: rows.append(("Rüstung",       f"{int(stats['armor']*100)}%"))
    if stats['dodge']        > 0: rows.append(("Ausweichen",    f"{int(stats['dodge']*100)}%"))
    if stats['thorns_pct']   > 0: rows.append(("Dornen",        f"{int(stats['thorns_pct']*100)}%"))
    if stats['hp_regen']     > 0: rows.append(("Regeneration",  f"{stats['hp_regen']:.0f} HP/s"))
    if stats['coin_mult']  != 1.0: rows.append(("Münz-Bonus",   f"x{stats['coin_mult']:.2f}"))
    if stats['xp_mult']    != 1.0: rows.append(("XP-Bonus",     f"x{stats['xp_mult']:.2f}"))
    if stats['rerolls']      > 0: rows.append(("Rerolls",       f"{stats['rerolls']}"))
    rows.append(("HP",             f"{int(player.hp)}/{int(player.max_hp)}"))
    title = "Deine Stats  (C)"
    pad, line_h, gap = 12, font.get_linesize(), 24
    label_w = max(font.size(lbl)[0] for lbl, _ in rows)
    value_w = max(font.size(val)[0] for _, val in rows)
    inner_w = label_w + gap + value_w
    panel_w = max(font.size(title)[0], inner_w) + pad * 2
    panel_h = line_h * (len(rows) + 1) + pad * 2

    x, y = 8, 8 + (_HUD_H + 6) * 2 + 8   # unter den beiden HUD-Labels oben links
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((14, 16, 28, 210))
    pygame.draw.rect(panel, (90, 130, 180), panel.get_rect(), width=1, border_radius=6)
    screen.blit(panel, (x, y))

    screen.blit(font.render(title, True, (255, 220, 60)), (x + pad, y + pad))
    ty = y + pad + line_h
    for lbl, val in rows:
        screen.blit(font.render(lbl, True, (190, 205, 230)), (x + pad, ty))
        vsurf = font.render(val, True, (255, 255, 255))
        screen.blit(vsurf, (x + panel_w - pad - vsurf.get_width(), ty))
        ty += line_h


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
        (font.render(f"SuperBoss in Welle {WIN_WAVE} bezwungen", True, (220, 220, 240)), cy - 24),
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

    save         = sd.load(1)      # vorläufig Slot 1; der echte Slot wird vor dem Menü gewählt
    main_menu    = MainMenu()
    options_menu = OptionsMenu()   # difficulty="Normal", sfx=70%, music=50%
    impr_menu    = ImprovementsMenu()
    bestiary_menu = BestiaryMenu()
    slot_menu    = SlotSelectMenu()
    save.setdefault("seen_enemies", [])   # Lexikon: bisher gesehene Gegner (Klassennamen)
    upgrade_menu = UpgradeMenu(SCREEN_WIDTH, SCREEN_HEIGHT)
    snd          = sounds.SoundManager()
    options_menu.load_settings(save.get("settings", {}))
    snd.set_sfx_vol(options_menu.sfx_volume)
    snd.set_music_vol(options_menu.music_volume)
    snd.start_menu_music()

    # Pause-Buttons (4 Stück, zentriert) — inkl. Steuerung-Übersicht
    _pbw, _pbh, _pgap = 280, 52, 12
    _pcx = SCREEN_WIDTH  // 2
    _pcy = SCREEN_HEIGHT // 2
    _ptop = _pcy - 60
    pause_btn_continue = Button(
        pygame.Rect(_pcx - _pbw // 2, _ptop,                      _pbw, _pbh), "Weiter spielen", (60, 200, 100))
    pause_btn_options  = Button(
        pygame.Rect(_pcx - _pbw // 2, _ptop + (_pbh + _pgap),     _pbw, _pbh), "Optionen",       (60, 160, 220))
    pause_btn_controls = Button(
        pygame.Rect(_pcx - _pbw // 2, _ptop + (_pbh + _pgap)*2,   _pbw, _pbh), "Steuerung",      (210, 160, 50))
    pause_btn_menu     = Button(
        pygame.Rect(_pcx - _pbw // 2, _ptop + (_pbh + _pgap)*3,   _pbw, _pbh), "Zum Hauptmenü",  (200, 60,  60))
    pause_overlay      = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pause_overlay.fill((0, 0, 0, 170))

    # Steuerungs-Übersicht (CONTROLS-Screen, aus dem Pause-Menü erreichbar)
    CONTROLS_LINES = [
        ("Maus / Turm",  "Zielt & feuert vollautomatisch auf den nächsten Gegner (Autoaim)"),
        ("Speed-Button", "oben rechts: Zeitraffer x1 / x5 / x10 / x20 (ausklappbar)"),
        ("B",            "Geschwindigkeit sofort auf x1 zurück"),
        ("C",            "Eigene Stats ein-/ausblenden"),
        ("ESC",          "Pause / zurück"),
        ("F11",          "Vollbild umschalten"),
        ("F1–F5",        "Dev: Welle leeren / →W10 / →W50 / →W100 / Levelup"),
    ]
    controls_back_btn = Button(
        pygame.Rect(_pcx - _pbw // 2, SCREEN_HEIGHT - _pbh - 30, _pbw, _pbh), "Zurück", (60, 160, 220))

    # HUD-Button (oben rechts): Geschwindigkeit/Zeitraffer — AUSKLAPPBAR. Klick öffnet die Liste
    # x1/x5/x10/x20; eine Option wählt direkt. Beschleunigt die GESAMTE Simulation (N×/Frame).
    SPEED_MULTS = [1, 2, 3, 5, 10, 20]
    speed_btn = Button(pygame.Rect(SCREEN_WIDTH - 158, 8, 150, 34), "Speed x1", (80, 180, 210))
    def _speed_option_rect(i):   # ausgeklappte Option i unter dem Speed-Button
        return pygame.Rect(speed_btn.rect.x, speed_btn.rect.bottom + 4 + i * 32,
                           speed_btn.rect.width, 30)

    player      = None
    pc          = None
    gs          = None
    terrain     = None
    dmg_numbers = []
    diff_mod    = options_menu.get_modifiers()
    new_record          = False
    prev_state          = None
    show_stats          = False         # Stats-Overlay ein/aus (Taste C, nur im PLAYING)
    speed_mult_idx      = 0             # Index in SPEED_MULTS (x1/x5/x10/x20) via HUD-Button
    speed_open          = False         # Speed-Dropdown ausgeklappt?
    options_return_to   = "MAIN_MENU"   # wohin OPTIONS-Zurück geht
    state               = "SLOT_SELECT"  # zuerst Speicherstand wählen, dann Hauptmenü

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
                    elif state == "CONTROLS":
                        state = "PAUSED"
                    elif state == "BESTIARY":
                        state = "MAIN_MENU"
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

                # Stats-Overlay ein/aus (Spieler-Feature, nicht Dev)
                if state == "PLAYING" and event.key == pygame.K_c:
                    show_stats = not show_stats
                # Taste B: Geschwindigkeit sofort auf x1 zurück (Zeitraffer aus)
                if state == "PLAYING" and event.key == pygame.K_b:
                    speed_mult_idx = 0
                    speed_open     = False

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
                        # Auf WIN_WAVE-1 springen (nächste Clear → finaler SuperBoss → Sieg)
                        gs["wave"]            = WIN_WAVE - 1
                        for e in gs["enemies"]: e.alive = False
                        gs["spawn_remaining"] = 0
                    elif event.key == pygame.K_F5:
                        # Dev: einen Levelup erzwingen (Karten-Auswahl testen)
                        gs["level"]            += 1
                        gs["pending_levelups"] += 1
                        gs["xp_to_next"]        = xp_to_next(gs["level"], gs["wave"])

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == "SLOT_SELECT":
                    summaries = [sd.slot_summary(s) for s in sd.SLOTS]
                    res = slot_menu.handle_click(mouse_pos, summaries)
                    if res and res[0] == "pick":
                        snd.play("ui_click")
                        save = sd.load(res[1])               # Slot laden + aktiv setzen
                        save.setdefault("seen_enemies", [])
                        options_menu.load_settings(save.get("settings", {}))
                        snd.set_sfx_vol(options_menu.sfx_volume)
                        snd.set_music_vol(options_menu.music_volume)
                        diff_mod = options_menu.get_modifiers()
                        state = "MAIN_MENU"
                    elif res and res[0] == "delete":
                        snd.play("ui_click")
                        sd.delete(res[1])

                elif state == "MAIN_MENU":
                    action = main_menu.handle_click(mouse_pos, run_active=gs is not None)
                    if action == "start":
                        start_run()
                        state = "PLAYING"
                    elif action == "options":
                        snd.play("ui_click")
                        options_return_to = "MAIN_MENU"
                        state = "OPTIONS"
                    elif action == "improvements": snd.play("ui_click"); state = "IMPROVEMENTS"
                    elif action == "bestiary":     snd.play("ui_click"); state = "BESTIARY"
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

                elif state == "BESTIARY":
                    if bestiary_menu.handle_click(mouse_pos) == "back":
                        snd.play("ui_click")
                        state = "MAIN_MENU"

                elif state == "CONTROLS":
                    if controls_back_btn.is_hovered(mouse_pos):
                        snd.play("ui_click")
                        state = "PAUSED"

                elif state == "PAUSED":
                    if pause_btn_continue.is_hovered(mouse_pos):
                        state = prev_state
                        pygame.mixer.music.unpause()
                    elif pause_btn_options.is_hovered(mouse_pos):
                        snd.play("ui_click")
                        options_return_to = "PAUSED"
                        state = "OPTIONS"
                    elif pause_btn_controls.is_hovered(mouse_pos):
                        snd.play("ui_click")
                        state = "CONTROLS"
                    elif pause_btn_menu.is_hovered(mouse_pos):
                        # Aufgeben: das im Lauf verdiente Gold trotzdem gutschreiben
                        # (Nutzerwunsch) — wie bei Game-Over/Sieg ins total_coins buchen.
                        save["best_wave"]    = max(save["best_wave"],  gs["wave"])
                        save["best_coins"]   = max(save["best_coins"], gs["coins"])
                        save["total_coins"] += gs["coins"]
                        sd.save(save)
                        gs      = None
                        terrain = None
                        snd.start_menu_music()
                        state = "MAIN_MENU"

                elif state == "PLAYING":
                    # Speed-Dropdown: offen → Option wählen (oder daneben → schließen);
                    # geschlossen → Klick auf den Button klappt aus.
                    if speed_open:
                        for i in range(len(SPEED_MULTS)):
                            if _speed_option_rect(i).collidepoint(mouse_pos):
                                speed_mult_idx = i
                                snd.play("ui_click")
                                break
                        speed_open = False
                    elif speed_btn.is_hovered(mouse_pos):
                        speed_open = True
                        snd.play("ui_click")

                elif state == "UPGRADE":
                    # Reroll (WEISS, ADR 025): vorhandene Charge zieht 3/4 Karten neu
                    if gs["stats"]["rerolls"] > 0 and upgrade_menu.handle_reroll_click(mouse_pos):
                        gs["stats"]["rerolls"] -= 1
                        upgrade_menu.roll(gs["obtained"], _card_count(save))
                        snd.play("ui_click")
                    else:
                        chosen = upgrade_menu.handle_click(mouse_pos)
                        if chosen:
                            apply_upgrade(chosen, gs["stats"], player)
                            gs["obtained"].add(chosen)
                            gs["pending_levelups"] = max(0, gs["pending_levelups"] - 1)
                            if gs["pending_levelups"] > 0:
                                upgrade_menu.roll(gs["obtained"], _card_count(save))   # weitere Karte
                            else:
                                state = "PLAYING"

            if event.type == pygame.MOUSEMOTION:
                if state == "OPTIONS":
                    changed = options_menu.update_drag(mouse_pos)
                    if changed:
                        if changed == "sfx":   snd.set_sfx_vol(options_menu.sfx_volume)
                        else:                  snd.set_music_vol(options_menu.music_volume)

            if event.type == pygame.MOUSEWHEEL:
                if state == "BESTIARY":
                    bestiary_menu.scroll(event.y)

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if state == "OPTIONS":
                    key = options_menu.stop_drag()
                    if key:
                        save["settings"] = options_menu.get_settings()
                        sd.save(save)

        # --- Update ---
        # Zeitraffer: die gesamte Gameplay-Update-Logik läuft N×/Frame (x1/x5/x10/x20).
        time_scale = SPEED_MULTS[speed_mult_idx] if state in ("PLAYING", "WAVE_CLEAR", "UPGRADE") else 1

        for _ in range(time_scale):
            if state == "PLAYING":
                # Spawn-Fenster: alle Gegner der Welle sind nach WAVE_SPAWN_SECONDS (10 s) gespawnt;
                # an die Live-FPS gekoppelt. diff_mod["spawn_bonus"] nudged das Tempo je Schwierigkeit.
                spawn_interval = max(1, spawn_interval_ticks(gs["wave"], options_menu.fps_value)
                                     + diff_mod["spawn_bonus"])
                gs["spawn_timer"] += 1
                # Concurrent-Cap: nur nachspawnen, wenn nicht schon zu viele am Turm stehen
                if (gs["spawn_remaining"] > 0 and gs["spawn_timer"] >= spawn_interval
                        and len(gs["enemies"]) < MAX_CONCURRENT_ENEMIES):
                    new_enemy = spawn_enemy_for_wave(gs["wave"], diff_mod["hp_mult"])
                    gs["enemies"].append(new_enemy)
                    # Lexikon: Gegnertyp als gesehen markieren (Klassenname; persistiert via save)
                    ename = type(new_enemy).__name__
                    if ename not in save["seen_enemies"]:
                        save["seen_enemies"].append(ename)
                    gs["spawn_remaining"] -= 1
                    gs["spawn_timer"]      = 0

                # Auto-Feuer beim Halten der Maustaste, getaktet vom Angriffstempo (ADR 009)
                if gs["fire_timer"] > 0:
                    gs["fire_timer"] -= 1
                # Voll-automatisches Feuer (kein Halten nötig): zielt per Autoaim auf den
                # nächsten Gegner, sobald der fire_timer bereit ist. Ohne Ziel wird nicht
                # geschossen — der Timer bleibt ≤0, also feuert der Turm sofort beim ersten Gegner.
                if gs["fire_timer"] <= 0:
                    aim = nearest_enemy_pos(pc, gs["enemies"], PLAYER_ATTACK_RANGE)
                    if aim:
                        gs["projectiles"] += spawn_projectiles(pc, aim, gs["stats"])
                        snd.play("shoot")
                        # Doppelschuss-Stufe (0–2): je Stufe ein zusätzlicher, verzögerter Schuss
                        # gerade aufs Ziel (Stufe 1 = 2 Schuss, Stufe 2 = 3 Schuss "Dreifachschuss").
                        ds_level = save.get("upgrades", {}).get("doppelschuss", 0)
                        for k in range(ds_level):
                            gs["pending_shots"].append((DOPPELSCHUSS_DELAY * (k + 1), aim))
                        gs["fire_timer"] = max(1, round(options_menu.fps_value / gs["stats"]["attack_speed"]))

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

                new_summons = []
                for e in gs["enemies"]:
                    e.update(pc)
                    if isinstance(e, Archer):
                        gs["enemy_projectiles"] += e.pop_shots()
                    elif isinstance(e, Monk):
                        e.heal_nearby(gs["enemies"])
                    elif isinstance(e, Necromancer):
                        new_summons += e.pop_summons()   # erst nach der Schleife anhängen
                if new_summons:
                    gs["enemies"] += new_summons
                for p in gs["projectiles"]:        p.update()
                for ep in gs["enemy_projectiles"]: ep.update()

                kills    = []
                had_hits = check_projectile_hits(gs["projectiles"], gs["enemies"], dmg_numbers, kills, player)
                if had_hits: snd.play("hit")
                # Dornen-Kills (ADR 025) zählen wie normale Kills (Münzen/XP/Sound)
                kills   += check_enemy_contact(gs["enemies"], player, pc)

                # Archer-Pfeile treffen Spieler
                for ep in gs["enemy_projectiles"]:
                    if ep.alive and ep.pos.distance_to(pc) < ep.RADIUS + PLAYER_RADIUS:
                        player.take_damage(ep.damage)
                        ep.alive = False

                gs["enemy_projectiles"] = [ep for ep in gs["enemy_projectiles"] if ep.alive]

                # Münzen & Kill-Sounds. Münz-/XP-Faktoren: GOLD-/WEISS-Karten (diesen Lauf,
                # ADR 025) + permanente Shop-Multiplikatoren über alle Läufe (ADR 026).
                upg = save.get("upgrades", {})
                gold_mult  = GOLD_BOOST_MULT if "gold_boost" in save["bought"] else 1.0
                gold_mult *= gs["stats"]["coin_mult"]
                gold_mult *= 1 + upg.get("coin_mult", 0) * PERMANENT_COIN_MULT_PER_LEVEL
                xp_factor  = gs["stats"]["xp_mult"] * (1 + upg.get("xp_mult", 0) * PERMANENT_XP_MULT_PER_LEVEL)
                for enemy in kills:
                    if isinstance(enemy, SuperBoss):
                        snd.play("kill_superboss")
                        snd.start_run_music()
                    elif isinstance(enemy, Boss):
                        snd.play("kill_boss")
                        snd.start_run_music()
                    elif isinstance(enemy, Lancer):     snd.play("kill_tanker")
                    else:                               snd.play("kill")
                    val = int(coin_value_for_wave(gs["wave"]) * enemy.coin_value * gold_mult * COIN_GAIN_MULT)
                    gs["coins"] += val
                    # XP-Drop = Klassen-Basis × Wellenfaktor (ADR 008 + ADR 014) × globaler
                    # XP_GAIN_MULT (+70%, Nutzerwunsch): skaliert mit der Welle, damit der
                    # Spieler spät genug DPS für die Endgame-Bosse aufbaut. Gilt für ALLE Gegner.
                    gs["xp"]    += round(enemy.coin_value * xp_wave_mult(gs["wave"])
                                      * xp_round_mult(gs["wave"]) * XP_GAIN_MULT * xp_factor)
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

                # HP-Regeneration (BLAU, ADR 025): zeitbasiert, an die Live-FPS gekoppelt
                # (wie spawn_interval); im Sub-Tick-Loop → Zeitraffer skaliert automatisch mit.
                if player.hp_regen and player.alive:
                    gs["_regen_accum"] += player.hp_regen / options_menu.fps_value
                    if gs["_regen_accum"] >= 1.0:
                        whole = int(gs["_regen_accum"])
                        gs["_regen_accum"] -= whole
                        player.hp = min(player.max_hp, player.hp + whole)

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
                    upgrade_menu.roll(gs["obtained"], _card_count(save))
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
        if state == "SLOT_SELECT":
            slot_menu.draw(screen, mouse_pos, [sd.slot_summary(s) for s in sd.SLOTS])
        elif state == "MAIN_MENU":
            main_menu.draw(screen, mouse_pos, save,
                           run_active=gs is not None, best_wave=save["best_wave"])
        elif state == "OPTIONS":
            options_menu.draw(screen, mouse_pos)
        elif state == "IMPROVEMENTS":
            impr_menu.draw(screen, mouse_pos, save)
        elif state == "BESTIARY":
            bestiary_menu.draw(screen, mouse_pos, set(save["seen_enemies"]))
        else:
            # --- Welt in eigenes Surface zeichnen, dann gezoomt auf den Screen ---
            if terrain:
                terrain.draw(world_surf)
            else:
                world_surf.fill(BG_COLOR)
            if gs:
                for e  in gs["enemies"]:
                    e.draw(world_surf)
                    if e.elite:   # roter Ring markiert Elites (10× HP, egal welcher Typ)
                        pygame.draw.circle(world_surf, ELITE_COLOR,
                                           (int(e.pos.x), int(e.pos.y)),
                                           int(e.radius) + 6, 2)
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
            # HUD-Button oben rechts: Geschwindigkeit (Zeitraffer), ausklappbar; grüner Rahmen = aktiv
            if gs and state == "PLAYING":
                speed_btn.label = f"Speed x{SPEED_MULTS[speed_mult_idx]}" + ("  ▾" if not speed_open else "  ▴")
                speed_btn.draw(screen, font, mouse_pos)
                if SPEED_MULTS[speed_mult_idx] > 1:
                    pygame.draw.rect(screen, (60, 230, 90), speed_btn.rect, width=3, border_radius=8)
                if speed_open:   # ausgeklappte Optionsliste x1/x2/x3/x5/x10/x20
                    for i, m in enumerate(SPEED_MULTS):
                        r   = _speed_option_rect(i)
                        sel = (i == speed_mult_idx)
                        hov = r.collidepoint(mouse_pos)
                        pygame.draw.rect(screen, (45, 80, 95) if (sel or hov) else (28, 34, 40), r, border_radius=6)
                        pygame.draw.rect(screen, (80, 180, 210), r, width=2 if sel else 1, border_radius=6)
                        ot = font.render(f"x{m}", True, (255, 255, 255) if (sel or hov) else (180, 200, 210))
                        screen.blit(ot, (r.centerx - ot.get_width() // 2, r.centery - ot.get_height() // 2))
            if gs and gs.get("banner") and gs["banner"]["timer"] > 0:
                b     = gs["banner"]
                alpha = min(255, b["timer"] * 4)
                bsurf = font_big.render(b["text"], True, b["color"])
                bsurf.set_alpha(alpha)
                screen.blit(bsurf, (SCREEN_WIDTH  // 2 - bsurf.get_width()  // 2,
                                    SCREEN_HEIGHT // 2 - 70))
            # Stats-Overlay (Taste C)
            if gs and player and show_stats and state == "PLAYING":
                draw_stats_panel(screen, font, gs["stats"], player, LIFESTEAL_PER_HIT)
            # Dev-Hint (linke untere Ecke)
            if gs and state == "PLAYING":
                hint = font_dmg.render("C Stats   F1 Clear  F2→W10  F3→W50  F4→W100  F5 Lvl+", True, (55, 55, 75))
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
                screen.blit(ptitle, (_pcx - ptitle.get_width() // 2, _ptop - 90))
                pause_btn_continue.draw(screen, font, mouse_pos)
                pause_btn_options.draw(screen,  font, mouse_pos)
                pause_btn_controls.draw(screen, font, mouse_pos)
                pause_btn_menu.draw(screen,     font, mouse_pos)
            elif state == "CONTROLS":
                screen.blit(pause_overlay, (0, 0))
                ctitle = font_big.render("Steuerung", True, (255, 220, 60))
                screen.blit(ctitle, (_pcx - ctitle.get_width() // 2, 70))
                ry = 180
                for keyname, desc in CONTROLS_LINES:
                    ks = font.render(keyname, True, (255, 220, 120))
                    ds = font.render(desc,    True, (210, 210, 225))
                    screen.blit(ks, (_pcx - 320, ry))
                    screen.blit(ds, (_pcx - 150, ry))
                    ry += 46
                controls_back_btn.draw(screen, font, mouse_pos)
            elif state == "UPGRADE":
                upgrade_menu.draw(screen, gs["stats"]["rerolls"])
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
        clock.tick(options_menu.fps_value)   # Live-Bildrate aus dem Options-Regler

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
