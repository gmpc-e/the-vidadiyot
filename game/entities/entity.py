"""Entity base: position, velocity, hitbox, update/draw.

Position is the entity's *center* in world space. The hitbox is an axis-aligned
rect kept centered on the position — collision code works on the hitbox.
"""
import pygame


class Entity:
    def __init__(self, x, y, w, h):
        self.pos = pygame.Vector2(x, y)      # center, world space
        self.vel = pygame.Vector2(0, 0)      # px/sec
        self.size = pygame.Vector2(w, h)
        self.color = (200, 200, 200)         # placeholder until sprites exist
        self.sprite = None                    # set once art is loaded
        self.frames = {}                      # state name -> Surface (see below)
        self._walk_cycle = None

    @property
    def hitbox(self):
        r = pygame.Rect(0, 0, int(self.size.x), int(self.size.y))
        r.center = (round(self.pos.x), round(self.pos.y))
        return r

    def update(self, dt):
        self.pos += self.vel * dt

    def _resolve(self, dx, dy, collider):
        """Move by (dx, dy) one axis at a time, snapping out of solid rects.

        `collider` exposes solid_rects(box) -> list[Rect]. Shared by the player
        and monsters so both resolve walls (and locked doors) identically.
        """
        # X axis
        self.pos.x += dx
        box = self.hitbox
        for r in collider.solid_rects(box):
            if box.colliderect(r):
                if dx > 0:
                    box.right = r.left
                elif dx < 0:
                    box.left = r.right
        self.pos.x = box.centerx

        # Y axis
        self.pos.y += dy
        box = self.hitbox
        for r in collider.solid_rects(box):
            if box.colliderect(r):
                if dy > 0:
                    box.bottom = r.top
                elif dy < 0:
                    box.top = r.bottom
        self.pos.y = box.centery

    def move_and_collide(self, dt, collider):
        self._resolve(self.vel.x * dt, self.vel.y * dt, collider)

    def displace(self, offset, collider):
        """Shove instantly by `offset`, still resolving against walls.

        Knockback used to be `self.pos += push`, which is a teleport: a 26px
        shove against 32px tiles put a struck monster straight through the wall
        and into the next classroom. Anything that moves an entity outside its
        normal velocity has to come through here.
        """
        self._resolve(offset.x, offset.y, collider)

    # ── animation ─────────────────────────────────────────────────────────
    # State-driven poses, shared by the player and the monsters: install a few
    # painted stances and let `anim_state` pick one per frame. The sheets give
    # **one frame per state**, not a cycle, so movement is synthesized — a
    # two-step bob paired with a squash on the off-beat, which reads as a gait
    # without inventing frames nobody drew.
    #
    # ⚠️ Squashing is done once, at install. Doing it per frame means a
    # `smoothscale` per entity per frame, and it resamples a 54px sprite on a
    # 640x360 surface that is then integer-scaled — the same mistake the victory
    # banner made.
    WALK_SQUASH = 0.94
    WALK_HZ = 7             # steps/sec of the synthesized gait
    # Real strips play at this; §A of the Phase 2 pack caps a strip at three
    # frames because that is what the image model reliably delivers registered.
    STRIP_FPS = 8
    # ⚠️ States whose strip **ping-pongs** (0-1-2-1) rather than looping
    # (0-1-2-0). A three-frame walk is contact / passing / contact, so playing it
    # straight through jumps from the second contact back to the first and the
    # character skips a step. Bouncing gives a four-beat cycle from three
    # drawings, which is why asking for three frames costs nothing.
    #
    # A one-shot — a swing, a cast — must *not* bounce: it would play its
    # wind-up backwards after the strike.
    PINGPONG = ("walk",)

    def set_frames(self, **poses):
        """Install named poses. Each is a Surface **or a list of frames**.

        A single Surface is a *pose*: the state holds it, and for "walk" the
        gait is synthesized (see above). A list is a real strip and simply
        plays. Both forms coexist on purpose — the strips land one sheet at a
        time, so a character can have a painted walk cycle and a single-pose
        attack in the same build.
        """
        self.frames = {k: (tuple(v) if isinstance(v, (list, tuple)) else v)
                       for k, v in poses.items() if v is not None}
        idle = self.frames.get("idle")
        self.sprite = (idle[0] if isinstance(idle, tuple) else idle) or self.sprite
        walk = self.frames.get("walk")
        self._walk_cycle = None
        # Synthesize a gait only when the walk is a lone pose. A painted strip
        # is the thing the squash was standing in for.
        if isinstance(walk, pygame.Surface):
            squash = pygame.transform.smoothscale(
                walk, (walk.get_width(),
                       max(1, int(walk.get_height() * self.WALK_SQUASH))))
            self._walk_cycle = (walk, squash)

    @property
    def anim_state(self):
        return "idle"

    def _play_order(self, state, n):
        """Frame indices in playback order — see PINGPONG."""
        if state in self.PINGPONG and n > 2:
            return list(range(n)) + list(range(n - 2, 0, -1))
        return list(range(n))

    def _step_phase(self, clock):
        return int(clock * self.WALK_HZ) % 2

    def frame_for(self, state, clock, progress=None):
        """The Surface for `state`, or the closest thing installed.

        `progress` (0..1) plays a strip **once, in step with something else** —
        a cast timer, a swing — instead of looping on the clock. That is the
        whole point of a wind-up: the frames have to line up with the moment the
        shot leaves, or the telegraph is decoration. Looping is the default
        because most strips are cycles.
        """
        seq = getattr(self, "frames", {}).get(state)
        if isinstance(seq, tuple):
            order = self._play_order(state, len(seq))
            if progress is None:
                i = order[int(clock * self.STRIP_FPS) % len(order)]
            else:
                # A one-shot indexes the *frames*, not the play order: it runs
                # start to end once, in step with whatever drives it.
                i = min(len(seq) - 1, max(0, int(progress * len(seq))))
            return seq[i]
        if state == "walk" and getattr(self, "_walk_cycle", None):
            return self._walk_cycle[self._step_phase(clock)]
        return seq or self.sprite

    def draw(self, surface, camera):
        r = self.hitbox
        r.topleft = (r.x - round(camera.offset.x), r.y - round(camera.offset.y))
        if self.sprite:
            surface.blit(self.sprite, r.topleft)
        else:
            pygame.draw.rect(surface, self.color, r)
