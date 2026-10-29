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


def dispatch(app, action):
    if action == 'start':
        app.request_start()
    elif action == 'briefing_start':
        app.accept_briefing()
    elif action == 'retry':
        app.request_retry()
    elif action == 'retry_confirm' and app.screen == 'retry':
        app.request_start(app.game.level)
    elif action == 'next' and app.screen == 'result':
        app.request_start(app.game.level+1)
    elif action == 'help' and app.screen == 'menu':
        app.screen = 'help'
    elif action == 'menu' and app.screen == 'result':
        app.return_to_menu()
    elif action == 'reset':
        app.ask_reset()
    elif action == 'reset_confirm':
        app.confirm_reset()
    elif action == 'back':
        app.cancel()
    elif action == 'resume' and app.screen == 'play':
        app.game.set_paused(False)
    elif action == 'action' and app.screen == 'play':
        app.action()
    elif action and action.startswith('level_') and app.screen == 'menu':
        level = int(action[-1])
        if level <= app.progress.unlocked:
            app.selected = level


def main():
    parser = argparse.ArgumentParser(description='CLAW MACHINE - three levels, one wallet.')
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--save', type=Path, help='Optional alternate progress file.')
    parser.add_argument('--screenshot', type=Path, help='Render a headless preview without reading or writing player progress.')
    parser.add_argument('--scene', choices=('start', 'level1', 'level2', 'level3', 'bullet-time', 'briefing', 'carry', 'drop', 'win', 'loss', 'reset', 'broke', 'help'), default='start')
    args = parser.parse_args()
    if args.screenshot:
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
    try:
        import pygame
    except ImportError:
        print('Pygame is missing. Run: uv run --no-project --python 3.12 main.py')
        return 1
    from model import WIDTH, HEIGHT
    from campaign import Campaign, default_save_path
    from app_view import AppView
    from view import ARENA_RECT
    pygame.display.init()
    pygame.font.init()
    view = AppView()
    if args.screenshot:
        from scenes import campaign_scene
        app = campaign_scene(args.scene)
        args.screenshot.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(view.draw_app(app), str(args.screenshot))
        print(f'Saved {args.screenshot.resolve()}')
        pygame.quit()
        return 0

    app = Campaign(args.save or default_save_path(), args.seed)
    info = pygame.display.Info()
    scale = min(1.0, (info.current_w-80)/WIDTH, (info.current_h-120)/HEIGHT)
    screen = pygame.display.set_mode((max(720, int(WIDTH*scale)), max(450, int(HEIGHT*scale))), pygame.RESIZABLE)
    pygame.display.set_caption('CLAW MACHINE | Three Levels')
    clock = pygame.time.Clock()
    running = True
    space_down = False
    target = screen.get_rect()
    view.draw_app(app)

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
                previous_ui = (app.screen, app.game.paused if app.game else False)
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.WINDOWFOCUSLOST:
                    space_down = False
                    if app.game:
                        app.game.end_bullet_time()
                    if app.screen in ('play', 'retry') and app.game:
                        app.game.set_paused(True)
                elif event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                    space_down = False
                    if app.game:
                        app.game.end_bullet_time()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    # One physical press spends one use; key-repeat events are ignored.
                    if not space_down:
                        space_down = True
                        if app.screen == 'play':
                            if app.game.level == 3:
                                app.game.start_bullet_time()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and app.screen != 'play':
                        app.cancel()
                    elif app.screen == 'play':
                        if event.key == pygame.K_r:
                            app.request_retry()
                        elif event.key == pygame.K_ESCAPE:
                            app.game.toggle_pause()
                        elif event.key == pygame.K_RETURN:
                            app.action()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    point = logical_position(event.pos)
                    if point:
                        action = view.hit(point)
                        if action:
                            dispatch(app, action)
                        elif app.screen == 'play' and ARENA_RECT.collidepoint(point):
                            app.action()
                # Rebuild hit targets on screen changes, not on every mouse motion.
                if previous_ui != (app.screen, app.game.paused if app.game else False):
                    view.draw_app(app, mouse)
            if app.screen == 'play' and mouse and ARENA_RECT.collidepoint(mouse):
                app.game.aim(mouse[0])
            app.update(elapsed)
            frame = view.draw_app(app, mouse)
            screen.fill((27, 45, 66))
            screen.blit(pygame.transform.smoothscale(frame, target.size), target)
            pygame.display.flip()
    finally:
        pygame.quit()
    return 0


if __name__ == '__main__':
    sys.exit(main())
