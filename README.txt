3D Maze Game built with Python, PyGame, and OpenGL.
Procedurally generates a unique maze each run using Kruskal's algorithm. Features first-person mouse-look camera with WASD movement, wall collision, and head-bob animation. The maze is fully textured, with 3D collectible models loaded from .obj files and compiled into display lists for performance. Collectibles grant speed boosts, while water puddle traps trigger a slip effect with a GLSL ripple shader and particle splash. A hint system temporarily reveals a minimap, and a HUD tracks time, position, and best run.

Controls:

    W - forward
    S - backward
    A -  left
    D -  right

    Mouse - Look around

    H - Use a hint (shows minimap for 10 seconds)

    R - Reset player position (keeps current maze)

    T - Generate new maze (resets everything)

    ESC - Quit game

Debug/Cheat: 

    N - Toggle noclip mode (walk through walls)

Powerups and Traps:

    almond water bottles - gives you a speed boost for 20 seconds

    hints - 3 hints per maze (resets on new maze generation). Shows minimap for 10 seconds. Timer shown while hint is active

        Yellow: Almond water locations
        Blue: Water puddles
        Green: Winner Door

    Water puddles - Causes player to slide uncontrollably for 1.5 seconds. Allows to noclip through internal walls. Screen gets blue tint with water effects. (could be good or bad)
