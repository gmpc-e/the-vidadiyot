"""All tuning constants. No logic lives here.

Every magic number that shapes how the game *feels* belongs in this file so it
can be tuned without hunting through the codebase. See design doc §3.10.
"""

# ─── Display ──────────────────────────────────────────────────────────────
TILE = 32
INTERNAL_RES = (640, 360)      # rendered here, then integer-scaled to window
WINDOW_SCALE = 2               # 640x360 -> 1280x720 window
CAPTION = "The Vidadiyot"
FPS_CAP = 120                  # clock.tick target; sim runs on FIXED_DT below
BG_COLOR = (24, 24, 28)

# ─── Simulation ───────────────────────────────────────────────────────────
FIXED_DT = 1 / 60              # fixed physics/AI step, machine-independent

# ─── Player ───────────────────────────────────────────────────────────────
PLAYER_WALK       = 165        # px/sec
PLAYER_SPRINT     = 250
STAMINA_MAX       = 4.0        # seconds of sprint
STAMINA_REGEN     = 1.0        # per second, after a delay
STAMINA_REGEN_DELAY = 1.5      # seconds after sprinting before regen starts
CARRY_CAPACITY    = 4          # forces return trips — this is a feature
INTERACT_RANGE    = 40
PLAYER_SIZE       = (24, 32)   # slightly narrower than a tile: forgiving doorways

PLAYER_MAX_HEALTH   = 100
PLAYER_REGEN_DELAY  = 2.5      # seconds after a hit before health regenerates
PLAYER_HEALTH_REGEN = 3.0      # health/sec once regen kicks in (lowered)
HEALTH_BOTTLE_HEAL  = 35       # HP restored by a health bottle pickup
SWING_TIME          = 0.18     # seconds the sword-swing arc is shown
WEB_STRUGGLE_HITS   = 3        # Space presses to break free of Little Snir's web

# ─── Vidadiyot (sight-based monster) ──────────────────────────────────────
VID_PATROL        = 85
VID_CHASE         = 145
VID_SIGHT_RANGE   = 220        # -> 300 after power restored
VID_SIGHT_ARC     = 90         # degrees

# ─── The Banished (sound-based monster) ───────────────────────────────────
BAN_PATROL        = 60
BAN_CHASE         = 105
BAN_HEAR_WALK     = 70         # px radius
BAN_HEAR_SPRINT   = 190
BAN_HEAR_DOOR     = 260

# A caster's projectile must travel faster than PLAYER_WALK or it can never
# catch a retreating player, and the ranged monsters become harmless to anyone
# who simply walks backwards. It should stay *slower* than PLAYER_SPRINT, so
# spending stamina is still the way out. tests/test_balance.py guards both ends.

# ─── Combat (slice: melee vs guardian monsters) ───────────────────────────
ATTACK_RANGE      = 44         # px reach of an Enter-key hit
MONSTER_SIZE      = (44, 44)
MONSTER_AGGRO     = 190        # px: starts chasing the player within this
MONSTER_SPEED     = 78         # px/sec base chase speed
MONSTER_WANDER_MULT = 0.55     # fraction of speed while wandering/searching
MONSTER_HITS      = 3          # default hits to kill (monster "strength")
MONSTER_KNOCKBACK = 26         # px the monster is shoved back per hit
HIT_FLASH_TIME    = 0.12       # seconds the monster flashes white when hit
MONSTER_TOUCH_DPS = 32         # player health lost per second while touched
# Nothing respawns: the roster is fixed (2 in the corridor + 1 per classroom),
# so a room you clear stays clear. Emri is the only monster that arrives later,
# and it arrives on the book count, not on a timer.
MONSTER_WEAVE_AMP = 0.35       # sideways weave while chasing (liveliness)

# ─── Little Terror (ranged fireball caster) ───────────────────────────────
CASTER_HITS       = 5.75       # HP — 5 on the card, +15% for pacing
CASTER_SPEED      = 66         # moves a bit slower — it fights at range
CASTER_CAST_RANGE = 250        # will throw fireballs within this distance
CASTER_KEEP_MIN   = 130        # backs away (kites) if the player is closer
CASTER_CAST_CD    = 1.8        # seconds between fireballs
FIREBALL_SPEED    = 210        # px/sec — must beat PLAYER_WALK (see below)
FIREBALL_DAMAGE   = 16         # HP per hit (scaled by difficulty)
FIREBALL_LIFETIME = 3.0        # seconds before it fizzles
FIREBALL_SIZE     = 14         # collision size (px)

# ─── Little Snir (ranged web caster) ──────────────────────────────────────
WEBBER_HITS       = 4.6        # 4 on the card, +15% for pacing
WEBBER_SPEED      = 72
WEB_CAST_RANGE    = 260        # throws a web within this distance
WEB_KEEP_MIN      = 120        # kites away if the player is closer
WEB_CAST_CD       = 5.0        # slow — the web is strong crowd control
WEB_SPEED         = 190        # projectile px/sec — must beat PLAYER_WALK
WEB_LIFETIME      = 3.0
WEB_SIZE          = 20

# ─── Player weapons ───────────────────────────────────────────────────────
# A warrior's attack deals `damage` in monster hits (monster health is counted
# in hits, so 2 means a swing takes two pips). Elad swings a longsword and hits
# hard; Roni throws knives, which trade power for reach and safety.
# ⚠️ EVERY weapon needs a cooldown. Melee originally had none — one swing per
# press, so a fast masher got unbounded damage while the thrower stayed capped
# by KNIFE_COOLDOWN. Measured, that made the knight anywhere from 2x to 20x the
# princess depending purely on how fast the player could hit the key, which is
# not a trade-off, just an inconsistency. Both are paced now.
SWING_COOLDOWN    = 0.36       # seconds between sword swings
KNIFE_COOLDOWN    = 0.28       # seconds between throws (unlimited ammo)
KNIFE_SPEED       = 340        # px/sec — fast, it is a thrown blade
KNIFE_RANGE       = 250        # px before it drops out of the air
KNIFE_SIZE        = 14

# ─── Zina, Roni's dog (the "Royal Bond" power, Z) ─────────────────────────
# Zina is a one-shot kill, so the limits are what balance her: a hard charge
# count per level, a leash so she can't clear the map from safety, and a real
# round trip during which Roni has no dog to send.
ZINA_CHARGES      = 3          # bites available per level — never regenerates
ZINA_RANGE        = 190        # px: how far Roni can send her
ZINA_SPEED        = 165        # px/sec: slow enough to watch her run it in
ZINA_BARK_EVERY   = 0.42       # seconds between barks while she is out
ZINA_BITE_TIME    = 0.28       # seconds latched on before she lets go
ZINA_SIZE         = (26, 20)

# ─── Emri, the disappearing monster (boss) ────────────────────────────────
# Emri never walks up to you: it hides (untargetable), blinks in at arm's length,
# strikes with a lightbolt, and vanishes. The telegraph window is the whole
# fight — it is the only time you can hit back, so tune it, not the HP, to
# change how hard the boss feels.
# ⚠️ Emri does not spawn in level 1 any more — it was too strong for the opening
# level and vanished before you could answer it. The Blinker behaviour stays
# built and tested, waiting on the boss level (see the roadmap): a duel in a
# hidden classroom once every book is home.
EMRI_HITS         = 8          # boss-grade: takes 8 connected swings
EMRI_HIDDEN_MIN   = 2.2        # seconds gone before it blinks back in
EMRI_HIDDEN_MAX   = 3.4
EMRI_TELEGRAPH    = 1.30       # materialized and charging — your window to swing
EMRI_STRIKE_TIME  = 0.30       # the bolt leaves its hand
EMRI_VANISH_TIME  = 0.75       # fading out, still hittable
EMRI_BLINK_DIST   = 60         # how close it materializes ("right next to you")
EMRI_BLINK_TRIES  = 24         # attempts to find a non-solid spot before giving up
BOLT_DAMAGE       = 20         # HP per hit (scaled by difficulty)
BOLT_SPEED        = 300        # fast — close range leaves little time to dodge
BOLT_LIFETIME     = 0.9
BOLT_SIZE         = 12

# ─── Global rules ─────────────────────────────────────────────────────────
ALARM_SPEED_MULT  = 1.35       # all monsters after power/alarm
CATCH_STUN_TIME   = 10.0       # monster "confused" cooldown after a catch
CATCH_ITEMS_LOST  = 2          # items dropped when caught
HARD_MODE         = False      # True -> 3 catches is a game over

# ─── Lighting ─────────────────────────────────────────────────────────────
DARK_VIEW_RADIUS  = 110        # ambient radius before power
FLASHLIGHT_RANGE  = 190
FLASHLIGHT_ARC    = 60

# ─── Book-return payoff (roadmap §6) ──────────────────────────────────────
BOOK_FLASH_TIME     = 0.9      # seconds the HUD book counter glows after a return
BOOK_TINT_TIME      = 0.55     # seconds the classroom tint pulses to its color
BOOK_TINT_ALPHA     = 68       # peak extra alpha of that pulse (base tint is 38)
BOOK_SHAKE_MAG      = 3.0      # camera shake on a successful return
BOOK_SHAKE_TIME     = 0.22

# ─── Camera ───────────────────────────────────────────────────────────────
CAMERA_DEADZONE   = (120, 80)  # px half-extents of the soft follow box
