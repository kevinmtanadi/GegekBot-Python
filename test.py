import unittest
from unittest.mock import MagicMock

from your_module import favorite

class TestFavorite(unittest.TestCase):

    def setUp(self):
        self.ctx = MagicMock()
        self.ctx.message.author = MagicMock()
        self.ctx.message.author.id = "123"
        self.ctx.message.author.name = "Alice"

    def test_play_no_voice_channel(self):
        self.ctx.message.author.voice = None
        result = favorite(self.ctx, "play random")
        self.assertEqual(result, "You have to be in a voice channel to play a song!")

    def test_play_no_favorite_songs(self):
        result = favorite(self.ctx, "play random")
        self.assertEqual(result, "You don't have any favorite song")

    def test_play_add_favorite_songs(self):
        favorite.favoriteDict = {"123": [{"title": "Song 1", "url": "url1"}, {"title": "Song 2", "url": "url2"}]}
        result = favorite(self.ctx, "play random")
        self.assertEqual(result, "Successfully added all favorite songs from Alice randomly")

    def test_add_song(self):
        favorite.favoriteDict = {"123": [{"title": "Song 1", "url": "url1"}]}
        favorite.getSong = MagicMock(return_value={"title": "Song 2", "url": "url2"})
        result = favorite(self.ctx, "add Song 2")
        self.assertEqual(result, "Successfully added Song 2 to Alice's favorites")

    def test_remove_song_no_favorite_songs(self):
        favorite.favoriteDict = {}
        result = favorite(self.ctx, "remove 1")
        self.assertEqual(result, "You don't have any favorite song")

    def test_remove_song_invalid_index(self):
        favorite.favoriteDict = {"123": [{"title": "Song 1", "url": "url1"}]}
        result = favorite(self.ctx, "remove 2")
        self.assertEqual(result, "Index doesn't exist")

    def test_remove_song(self):
        favorite.favoriteDict = {"123": [{"title": "Song 1", "url": "url1"}, {"title": "Song 2", "url": "url2"}]}
        result = favorite(self.ctx, "remove 1")
        self.assertEqual(result, "Successfully removed song Song 1 from your favorite")

    def test_list_no_favorite_songs(self):
        favorite.favoriteDict = {}
        result = favorite(self.ctx, "list")
        self.assertEqual(result, "You don't have any favorite song")

    def test_list_favorite_songs(self):
        favorite.favoriteDict = {"123": [{"title": "Song 1", "url": "url1"}, {"title": "Song 2", "url": "url2"}]}
        result = favorite(self.ctx, "list")
        expected_result = "Alice's favorite song list :\n1. Song 1\n2. Song 2\n"
        self.assertEqual(result, expected_result)

if __name__ == '__main__':
    unittest.main()
