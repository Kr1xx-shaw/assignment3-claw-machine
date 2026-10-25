"""Regressions for unusual Windows font-registry entries and font fallbacks."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import pygame
from model import Game
from view import View


class FontStartupTests(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_ui_renders_when_system_font_discovery_is_broken(self):
        failure = TypeError('expected str, bytes or os.PathLike object, not int')
        with patch('pygame.font.SysFont', side_effect=failure) as system_lookup:
            surface = View().draw(Game(7))
        self.assertEqual(surface.get_size(), (1440, 900))
        system_lookup.assert_not_called()

    def test_missing_font_files_use_readable_bold_builtin_font(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'WINDIR': folder}):
            font = View().font(24, bold=True)
            self.assertTrue(font.get_bold())
            self.assertGreater(font.render('CLAW MACHINE', True, (0, 0, 0)).get_width(), 0)

    def test_corrupted_font_file_does_not_prevent_startup(self):
        with tempfile.TemporaryDirectory() as folder:
            fonts = Path(folder) / 'Fonts'
            fonts.mkdir()
            (fonts / 'segoeui.ttf').write_bytes(b'Not a valid font file')
            with patch.dict(os.environ, {'WINDIR': folder}):
                surface = View().draw(Game(7))
            self.assertEqual(surface.get_size(), (1440, 900))


if __name__ == '__main__':
    unittest.main()
