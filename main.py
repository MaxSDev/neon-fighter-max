"""Run Neon Fighter Max using Python 3.12 and pygame-ce."""

import argparse
import os


def main():
    parser = argparse.ArgumentParser(description='Neon Fighter Max')
    parser.add_argument('--smoke-test', action='store_true', help='Render 120 frames with SDL dummy drivers and exit.')
    args = parser.parse_args()
    if args.smoke_test:
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
    from neon.app import Game

    frames = Game().run(smoke_test=args.smoke_test)
    if args.smoke_test:
        print(f'Smoke test passed: {frames} frames rendered at 960x540 (internal 480x270).')


if __name__ == '__main__':
    main()
