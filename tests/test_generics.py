from tests.models.user import User, UserWithType


class TestGenerics:
    """Test that generic type introspection resolves the concrete parameter."""

    def test_returns_the_concrete_generic_type(self) -> None:
        """Test that it returns the concrete generic type supplied at instantiation."""

        user_with_type = UserWithType[int](id=1, name="John Doe")

        assert user_with_type.get_type() is int

    def test_returns_none_when_no_generic_type_is_present(self) -> None:
        """Test that it returns None for models without a concrete generic parameter."""

        user = User(id=1, name="John Doe")

        assert user.get_type() is None

    def test_returns_the_same_result_across_multiple_calls(self) -> None:
        """Test that it returns a stable generic type across repeated calls."""

        user_with_type = UserWithType[int](id=1, name="John Doe")

        first_result = user_with_type.get_type()
        second_result = user_with_type.get_type()

        assert first_result is int
        assert second_result is int
