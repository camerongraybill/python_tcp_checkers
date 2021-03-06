from unittest import TestCase

from internal_types.types import Move, Direction, BoardLocation, Board, Encodable, InvalidMove


class TestMoveType(TestCase):

    def test_move(self):
        m = Move(1, 2, Direction.Negative, Direction.Positive)
        self.assertEqual(m.to_bytes(), b"\x29")
        self.assertEqual(m.to_bytes(), Move.from_bytes(m.to_bytes()).to_bytes())
        self.assertEqual(m.x_pos, 1)
        self.assertEqual(m.y_pos, 2)
        self.assertEqual(m.x_direction, Direction.Negative)
        self.assertEqual(m.y_direction, Direction.Positive)
        self.assertEqual((1, 2), m.pos)
        self.assertEqual((0, 3), m.after_move_pos)
        self.assertEqual((-1, 4), m.after_double_move_pos)
        self.assertEqual("(2, 3) -> (1, 4)", m.__repr__())


class TestBoardLocationType(TestCase):

    def test_board_location(self):
        loc = BoardLocation(True, True, False)
        self.assertEqual(loc.to_bytes(), b"\x06")
        self.assertEqual(loc.to_bytes(), BoardLocation.from_bytes(loc.to_bytes()).to_bytes())
        self.assertEqual(loc.used, True)
        self.assertEqual(loc.promoted, True)
        self.assertEqual(loc.owner, False)


class TestDirectionEnum(TestCase):

    def test_directions(self):
        self.assertEqual(1, Direction.Positive.to_one)
        self.assertEqual(-1, Direction.Negative.to_one)
        self.assertEqual("-1", Direction.Negative.__repr__())


class TestBoardType(TestCase):

    def test_board(self):
        b = Board([BoardLocation(True, False, False)] * 64)
        self.assertEqual(b.to_bytes(), b"\x92I$\x92I$\x92I$\x92I$\x92I$\x92I$\x92I$\x92I$")
        self.assertEqual(b.to_bytes(), Board.from_bytes(b.to_bytes()).to_bytes())
        self.assertEqual(b[(0, 0)], b[0][0])
        with self.assertRaises(KeyError):
            a = b['A']
        b[0, 0] = BoardLocation(True, False, True)
        b[7, 7] = BoardLocation(True, True, False)
        b[1, 0] = BoardLocation(False, False, False)
        rb = b.translate_to_other_user()
        self.assertEqual(b[1, 0], rb[1, 0])
        self.assertEqual(BoardLocation(True, False, False), rb[0, 0])
        self.assertEqual(BoardLocation(True, True, True), rb[7, 7])

    def test_invalid_board(self):
        with self.assertRaises(TypeError):
            Board([])

    def test_apply_move(self):
        b = Board.generate_game_start()
        b.apply_move(Move(0, 2, Direction.Positive, Direction.Positive), Direction.Positive, False)
        self.assertEqual(BoardLocation(False, False, False), b[0, 2])
        self.assertEqual(BoardLocation(True, False, False), b[1, 3])
        with self.assertRaises(InvalidMove):
            # Try moving a piece that doesn't exist
            b.apply_move(Move(0, 2, Direction.Positive, Direction.Positive), Direction.Positive, False)
        with self.assertRaises(InvalidMove):
            # Try jumping your own piece
            b.apply_move(Move(0, 0, Direction.Positive, Direction.Positive), Direction.Positive, False)
        # Move a piece right
        b.apply_move(Move(1, 3, Direction.Positive, Direction.Positive), Direction.Positive, False)
        # Move a piece left
        b.apply_move(Move(2, 2, Direction.Negative, Direction.Positive), Direction.Positive, False)
        with self.assertRaises(InvalidMove):
            # Try moving a piece the wrong direction
            b.apply_move(Move(1, 3, Direction.Positive, Direction.Negative), Direction.Positive, False)
        with self.assertRaises(InvalidMove):
            # Try moving an opponent's piece
            b.apply_move(Move(3, 5, Direction.Negative, Direction.Negative), Direction.Positive, False)
        b.apply_move(Move(1, 3, Direction.Negative, Direction.Positive), Direction.Positive, False)
        # Jump!
        b.apply_move(Move(3, 5, Direction.Negative, Direction.Negative), Direction.Negative, True)
        # Cheat a little bit to delete some pieces and check that promotion works
        b[2, 6] = BoardLocation(True, False, False)
        b[3, 7] = BoardLocation(False, False, False)
        # Move to the edge and promote
        b.apply_move(Move(2, 6, Direction.Positive, Direction.Positive), Direction.Positive, False)
        self.assertTrue(b[3, 7].promoted)

        # Cheat a little to check moving to the bottom
        b[4, 2] = BoardLocation(True, False, True)
        b[2, 0] = BoardLocation(False, False, False)
        b.apply_move(Move(4, 2, Direction.Negative, Direction.Negative), Direction.Negative, True)
        self.assertTrue(b[2, 0].promoted)

        # Try to move out of bounds
        with self.assertRaises(InvalidMove):
            b.apply_move(Move(2, 0, Direction.Negative, Direction.Negative), Direction.Negative, True)

    def test_get_all_moves(self):
        b = Board([BoardLocation(False, False, False)] * 64)
        b[0, 2] = BoardLocation(True, True, True)
        self.assertListEqual(
            [Move(0, 2, Direction.Positive, Direction.Positive), Move(0, 2, Direction.Positive, Direction.Negative)],
            b.get_possible_moves(Direction.Negative, True))

    def test_game_over(self):
        b = Board([BoardLocation(False, False, False)] * 64)
        b[0, 2] = BoardLocation(True, True, True)
        b[1, 3] = BoardLocation(True, True, False)
        self.assertFalse(b.check_game_over(True))
        self.assertFalse(b.check_game_over(False))
        b.apply_move(Move(0, 2, Direction.Positive, Direction.Positive), Direction.Negative, True)
        self.assertTrue(b.check_game_over(True))
        self.assertFalse(b.check_game_over(False))

    def test_get_required_moves(self):
        b = Board([BoardLocation(False, False, False)] * 64)
        b[0, 2] = BoardLocation(True, True, True)
        b[1, 3] = BoardLocation(True, True, False)
        self.assertListEqual([Move(0, 2, Direction.Positive, Direction.Positive)],
                             b.get_required_moves(Direction.Positive, True))
        self.assertListEqual([], b.get_required_moves(Direction.Positive, False))


class TestEncodableAbstract(TestCase):

    def test_encodable(self):
        class Test(Encodable):
            pass

        with self.assertRaises(TypeError):
            x = Test()

        with self.assertRaises(NotImplementedError):
            Test.from_bytes(b'')
