# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["pygame==2.6.1"]
# ///
"""Run: uv run --no-project --python 3.12 main.py"""
import argparse
import os
from pathlib import Path
import sys

os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')


def main():
    parser = argparse.ArgumentParser(description='CLAW MACHINE - a small mouse-controlled arcade game.')
    parser.add_argument('--seed', type=int, default=None, help='Repeat an initial arrangement for debugging.')
    parser.add_argument('--screenshot', type=Path, help='Render a headless PNG and exit.')
    parser.add_argument('--scene', choices=('start', 'carry', 'drop', 'win', 'loss'), default='start', help='A repeatable documentation scene; used only with --screenshot.')
    args = parser.parse_args()
    if args.screenshot:
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
    try:
        import pygame
    except ImportError:
        print('Pygame is missing. From this folder run: uv run --no-project --python 3.12 main.py')
        return 1
    from model import Game, WIDTH, HEIGHT, State
    from view import View, ACTION_RECT, RESTART_RECT, REPLAY_RECT, ARENA_RECT
    pygame.display.init()
    pygame.font.init()
    game = Game(args.seed)
    view = View()
    if args.screenshot:
        from scenes import documentation_scene
        game = documentation_scene(args.scene)
        args.screenshot.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(view.draw(game), str(args.screenshot))
        print(f'Saved {args.screenshot.resolve()}')
        pygame.quit()
        return 0

    info = pygame.display.Info()
    scale = min(1.0, (info.current_w-80)/WIDTH, (info.current_h-120)/HEIGHT)
    window_size = (max(720, int(WIDTH*scale)), max(450, int(HEIGHT*scale)))
    screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
    pygame.display.set_caption('CLAW MACHINE | Assignment 3')
    clock = pygame.time.Clock()
    running = True
    target = screen.get_rect()

    def logical_position(position):
        if not target.collidepoint(position):
            return None
        return ((position[0]-target.x)*WIDTH/target.w, (position[1]-target.y)*HEIGHT/target.h)

    try:
        while running:
            elapsed = clock.tick(60)/1000
            ratio = min(screen.get_width()/WIDTH, screen.get_height()/HEIGHT)
            target = pygame.Rect(0, 0, max(1, round(WIDTH*ratio)), max(1, round(HEIGHT*ratio)))
            target.center = screen.get_rect().center
            mouse = logical_position(pygame.mouse.get_pos())
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.WINDOWFOCUSLOST:
                    # Alt-tab must not silently consume a player's remaining attempts.
                    if not game.terminal:
                        game.paused = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        game.reset()
                    elif event.key in (pygame.K_SPACE, pygame.K_ESCAPE):
                        game.toggle_pause()
                    elif event.key == pygame.K_RETURN:
                        game.action()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    point = logical_position(event.pos)
                    if point:
                        if RESTART_RECT.collidepoint(point) or (game.terminal and REPLAY_RECT.collidepoint(point)):
                            game.reset()
                        elif ACTION_RECT.collidepoint(point) or (ARENA_RECT.collidepoint(point) and not game.terminal):
                            game.action()
            if mouse and ARENA_RECT.collidepoint(mouse):
                game.aim(mouse[0])
            game.update(elapsed)
            frame = view.draw(game, mouse)
            screen.fill((27, 45, 66))
            screen.blit(pygame.transform.smoothscale(frame, target.size), target)
            pygame.display.flip()
    finally:
        pygame.quit()
    return 0


if __name__ == '__main__':
    sys.exit(main())

