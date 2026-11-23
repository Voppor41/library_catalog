from library_catalog.main import app


def test_all_book_operations_require_bearer_authentication() -> None:
    schema = app.openapi()
    book_operations = [
        operation
        for path, path_item in schema["paths"].items()
        if path.startswith("/api/v1/books")
        for operation in path_item.values()
        if isinstance(operation, dict) and "responses" in operation
    ]

    assert book_operations
    assert all(operation.get("security") for operation in book_operations)
