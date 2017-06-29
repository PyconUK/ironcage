from django.test import TestCase

from ironcage.utils import Scrambler


class ScramblerTests(TestCase):
    def test_scrambler(self):
        for offset in [0, 1, 10, 100, 1000, 10000, (2 ** 16 - 1)]:
            scrambler = Scrambler(offset)
            outputs = set()
            for i in range(2 ** 16):
                o = scrambler.forward(i)
                outputs.add(o)
                self.assertEqual(scrambler.backward(o), i)
            self.assertEqual(len(outputs), 2 ** 16)
