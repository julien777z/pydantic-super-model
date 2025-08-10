from tests.models.user import (
    User,
    PrimaryKey,
    UserNoAnnotations,
    UserWithUnionAnnotation,
    UserWithAnnotatedAnnotation,
    UserWithType,
)


class TestModelAnnotations:
    """Test the model's get_annotated_fields method."""

    def test_model_annotations(self):
        """Test the model's get_annotated_fields method with annotations."""

        user = User(id=1, name="John Doe")

        annotated_fields = user.get_annotated_fields(PrimaryKey)

        assert annotated_fields == {"id": 1}

    def test_model_no_annotations(self):
        """Test the model's get_annotated_fields method with no annotations."""

        user = UserNoAnnotations(id=1, name="John Doe")

        assert not user.get_annotated_fields(PrimaryKey)

    def test_model_with_union_annotation(self):
        """Test the model's get_annotated_fields method with union annotation."""

        user = UserWithUnionAnnotation(id=1, name="John Doe")

        annotated_fields = user.get_annotated_fields(PrimaryKey)

        assert annotated_fields == {"id": 1}

    def test_model_with_annotated_annotation(self):
        """Test the model's get_annotated_fields method with annotated annotation."""

        user = UserWithAnnotatedAnnotation(id=1, name="John Doe")

        annotated_fields = user.get_annotated_fields(PrimaryKey)

        assert annotated_fields == {"id": 1}


class TestModelType:
    """Test the model's get_type method."""

    def test_model_type(self):
        """Test the model's get_type method."""

        user_with_type = UserWithType[int](id=1, name="John Doe")

        assert user_with_type.get_type() == int

        user_without_type = User(id=1, name="John Doe")

        assert not user_without_type.get_type()
