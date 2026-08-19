Sound effects — drop-in overrides.

The game synthesizes placeholder sounds in code, but prefers a real file here if
it exists. To replace a sound, just add a file with the matching name:

    monster.wav   (or monster.ogg)   -> monster "scare" growl when it spots you

The audio system (game/systems/audio.py, AudioSystem._get_sfx) checks for
<name>.wav then <name>.ogg and falls back to the synth only if neither is found.
No code change needed — just add the file. Mono or stereo both work.
