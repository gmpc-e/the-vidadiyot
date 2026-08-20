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
# ⚠️ Keys are **dropped by monsters**, not lying on the floor. Found on the
# ground they were a walking errand you did before the game started; the first
# three kills now hand them over, so the fight and the objective are the same
# act. Three, because there are three doors — a fourth would be dead weight.
KEYS_FROM_KILLS   = 3
INTERACT_RANGE    = 40
PLAYER_SIZE       = (24, 32)   # slightly narrower than a tile: forgiving doorways

PLAYER_MAX_HEALTH   = 100
PLAYER_REGEN_DELAY  = 4.0      # seconds after a hit before health regenerates
PLAYER_HEALTH_REGEN = 1.4      # health/sec once regen kicks in
# ⚠️ Was 3.0, which healed a full bar in ~33s and meant almost any fight could be
# walked away from and forgotten. At 1.4 a bad fight is still felt a minute
# later, which is what makes potions and difficulty mean anything. Scaled per
# difficulty by `regen` — see systems/difficulty.py.
HEALTH_BOTTLE_HEAL  = 35       # HP restored by a health bottle pickup
SWING_TIME          = 0.18     # seconds the sword-swing arc is shown
WEB_STRUGGLE_HITS   = 3        # Space presses to break free of Little Snir's web
# ⚠️ A web used to be a pure inconvenience: it held you still and did nothing,
# so the correct play was to ignore it and keep mashing. Draining while it holds
# is what turns it into crowd *control* — being stuck now costs health, so Snir
# webbing you while a teacher shoots is a real trap rather than a pause.
WEB_DPS             = 7.0      # health/sec while caught (scaled by difficulty)

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
# How far a monster will follow you from the post it spawned on. Without this a
# classroom guard aggroed through its own wall and walked out into the corridor,
# or into the *next* classroom — which since §5 also meant it silently blocked
# that room's book return. A leash keeps every monster in the room it guards, so
# "clear this room" stays a promise the level can keep.
MONSTER_LEASH     = 230        # px from home before it gives up and walks back
MONSTER_SIGHT_STEP = 12        # px between line-of-sight samples (0 = no LOS test)
MONSTER_SPEED     = 78         # px/sec base chase speed
MONSTER_WANDER_MULT = 0.55     # fraction of speed while wandering/searching
MONSTER_HITS      = 3          # default hits to kill (monster "strength")
MONSTER_KNOCKBACK = 26         # px the monster is shoved back per hit
# Below this, "away from the blow" is meaningless: a hit landing on the target's
# own centre gives a direction made of rounding error, and the monster hops
# somewhere random at full force. Weapons that know their travel direction pass
# it instead; everything else needs the blow to land this far from the centre.
KNOCKBACK_MIN_DIST = 5.0
HIT_FLASH_TIME    = 0.12       # seconds the monster flashes white when hit
# ⚠️ How long a monster *holds a hurt pose*, as opposed to how long it flashes.
# The white flash is a 0.12s tint — right for "that connected", far too short to
# play a three-frame flinch through. A painted hurt is a performance and needs
# time to read; the flash stays underneath it as the frame-exact confirmation.
MONSTER_HURT_TIME = 0.40
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
# ⚠️ **The wind-up is what makes a ranged fight fair.** A caster used to fire on
# the frame its cooldown expired: the fireball simply existed, with no warning
# and nothing to react to, so taking a hit was a matter of where you happened to
# be standing. Now it commits — stops moving, locks its aim, shows a charge —
# and only then throws. Long enough to see and answer (human reaction is around
# 0.25s), short enough that it is not a free hit. See tests/test_balance.py.
CASTER_WINDUP     = 0.55       # seconds of visible charge before a fireball
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
WEB_WINDUP        = 0.70       # the longest: the web is the harshest to be hit by
WEB_SPEED         = 190        # projectile px/sec — must beat PLAYER_WALK
WEB_LIFETIME      = 3.0
WEB_SIZE          = 20

# ─── The teachers (ranged tome casters, one female / one male) ────────────
# They hold the *classrooms*; the fire and web casters work the corridors, where
# a 250px range finally has room to kite in. A room-dweller wants the opposite
# shape: short range, slow projectile, and a wander radius that fills the room
# rather than orbiting one spot, so the player meets them by walking in.
TEACHER_HITS      = 5.75       # as tough as Little Terror — they gate a room
TEACHER_SPEED     = 58         # slower than anything else: they shuffle
TOME_CAST_RANGE   = 190        # ⚠️ under a classroom's diagonal, or they snipe
                               #    the player through the doorway from a corner
TOME_KEEP_MIN     = 95         # backs off, but not far — the room is small
TOME_CAST_CD      = 2.4
TOME_WINDUP       = 0.50       # the teachers are slow but they are not gentle
TOME_SPEED        = 178        # slowest projectile in the game — but ⚠️ it was
                               #    165, exactly PLAYER_WALK, which means a
                               #    player strolling away is never hit at all
TOME_DAMAGE       = 19         # ⚠️ was 14. The teachers hold every classroom
                               #    and are the enemy met most; at 14 a room
                               #    could be walked through while being hit
TOME_LIFETIME     = 2.4
TOME_SIZE         = 18
# How far a teacher drifts from its post. ⚠️ Much larger than the guard radius
# the corridor monsters use (52), because "wanders the classroom" is the whole
# brief — but it must stay inside MONSTER_LEASH or a teacher wanders out of the
# room it is supposed to be holding and the door stops meaning anything.
TEACHER_WANDER    = 96

# ─── Player weapons ───────────────────────────────────────────────────────
# A warrior's attack deals `damage` in monster hits (monster health is counted
# in hits, so 2 means a swing takes two pips). Wallad swings a longsword and hits
# hard; Roni throws knives, which trade power for reach and safety.
# ⚠️ EVERY weapon needs a cooldown. Melee originally had none — one swing per
# press, so a fast masher got unbounded damage while the thrower stayed capped
# by KNIFE_COOLDOWN. Measured, that made the knight anywhere from 2x to 20x the
# princess depending purely on how fast the player could hit the key, which is
# not a trade-off, just an inconsistency. Both are paced now.
SWING_COOLDOWN    = 0.42       # seconds between sword swings
# ⚠️ Was 0.36, and it moved because Roni's knife was cut 20% (0.85 -> 0.68).
# `test_melee_out_damages_range_but_not_by_a_landslide` asserts melee out-damages
# range by **under 2x**, and the knife cut alone pushed that to 2.3x — the
# thrower becomes a trap choice rather than a trade. Slowing the swing brings it
# to 1.96x while leaving Wallad's identity ("two pips a swing") intact, which
# trimming his damage would not.
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
# Seconds between barks while she is out. The delivered `zina_bark` is 1.85s of
# real barking — a *sequence*, not a single yap — so retriggering it every 0.42s
# stacked four copies on top of each other and turned her run-in into a wall of
# dog. Long enough now that one play finishes before the next begins.
ZINA_BARK_EVERY   = 2.0
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
EMRI_HITS         = 24         # ⚠️ was 8, which is +200%. At 8 a single sword
                               #    swing was 25% of the boss, so Wallad's first
                               #    hit triggered the 75% phase break — the fight
                               #    was over before it had a shape. At 24 a swing
                               #    is one twelfth and the phase breaks land
                               #    where they were meant to.
EMRI_SIZE         = (56, 56)   # ⚠️ bigger than MONSTER_SIZE — it is the boss,
                               #    and a boss the size of a classroom monster
                               #    reads as one no matter what it does
EMRI_DRIFT        = 34         # px/sec it circles while it is visible
# Zina's bite kills an ordinary monster outright. Against a **boss** it is a
# heavy blow instead: three bites, which is every charge she has in a level, so
# spending all of them is a real answer to Emri and not a free win.
# ⚠️ **A flat pip cost, not a fraction of the boss's health.** It was
# `max_health / 3`, which against a 24-hit Emri meant one bite removed a *third
# of the fight* — and worse, it silently rescaled every time `EMRI_HITS` moved,
# so tuning the boss quietly retuned the dog. 3 pips is the heaviest single blow
# in the game (a sword swing is 2) without being a phase of it: all three of
# Roni's charges come to 9 of Emri's 24.
ZINA_BOSS_DAMAGE  = 3.0
# Emri hides and sends help at these fractions of its health. It does not
# regenerate — the marks are one-way.
#
# ⚠️ **Two breaks, not three.** At 0.75/0.5/0.25 they came about six health apart
# — three sword swings — and a player who lands a burst crosses two in a few
# seconds, so it read as Emri running away constantly rather than as a fight with
# phases. Widening them *and* dropping one gives the duel three acts instead of
# four and leaves real fighting between them.
EMRI_PHASE_MARKS  = (0.66, 0.33)
EMRI_PHASE_ADDS   = 2          # monsters summoned each time
# ...and a floor on how soon after coming back it may leave again. The marks
# alone cannot guarantee spacing: damage arrives in bursts, not evenly.
EMRI_PHASE_GRACE  = 7.0        # seconds present before it can phase out again
EMRI_HIDDEN_MIN   = 2.2        # seconds gone before it blinks back in
EMRI_HIDDEN_MAX   = 3.4
# ⚠️ These three add up to how long Emri is **on screen per blink**, and that
# total is the number that matters: at 1.30 + 0.30 + 0.75 = 2.35s it was gone
# before a player had crossed the room to it, so the fight was mostly chasing an
# empty floor. 3.35s is long enough to close, swing twice and still be punished
# for over-staying. `test_emri_stays_visible_long_enough_to_answer` guards it.
EMRI_TELEGRAPH    = 2.10       # materialized and charging — your window to swing
EMRI_STRIKE_TIME  = 0.35       # the bolt leaves its hand
EMRI_VANISH_TIME  = 0.90       # fading out, still hittable
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

# ─── Classroom colour ─────────────────────────────────────────────────────
# The wash of room colour laid over a classroom floor, so which book belongs
# where is readable at a glance. This was 38 while the floor was one flat grey;
# over the painted parquet that much colour drowns the material and the room
# turns red. Raise it and you lose the art, lower it and you lose the matching
# cue — the door plate and blackboard swatch carry the rest of that signal.
ROOM_TINT_ALPHA     = 16

# ─── Book-return payoff (roadmap §6) ──────────────────────────────────────
BOOK_FLASH_TIME     = 0.9      # seconds the HUD book counter glows after a return
BOOK_SHAKE_MAG      = 3.0      # camera shake on a successful return
BOOK_SHAKE_TIME     = 0.22

# ─── Camera ───────────────────────────────────────────────────────────────
CAMERA_DEADZONE   = (120, 80)  # px half-extents of the soft follow box
