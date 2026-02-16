# Contributing to MNN Pipeline

Thank you for your interest in contributing to the MNN (Matrix Neural Network) Pipeline project!

## Code of Conduct

This project follows the standard open source code of conduct. Be respectful, inclusive, and professional in all interactions.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)

### Suggesting Features

Feature requests are welcome! Please provide:
- Clear use case and motivation
- Proposed API or interface changes
- Any potential implementation approaches

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes**:
   - Follow existing code style and conventions
   - Add tests for new functionality
   - Update documentation as needed
3. **Test your changes**:
   ```bash
   make lint
   make test
   ```
4. **Commit your changes**:
   - Write clear, descriptive commit messages
   - Reference issue numbers if applicable
5. **Submit a pull request**

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/XxxGHOSTX/MNN.git
   cd MNN
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables (see `.env.example`):
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run tests:
   ```bash
   python -m unittest discover tests
   ```

## Code Style

- **Python**: Follow PEP 8 style guide
- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Use Google-style docstrings for all public functions
- **Naming**: Use descriptive names; avoid abbreviations

### Example Function

```python
def process_query(query: str, max_length: int = 1000) -> List[Dict[str, Any]]:
    """
    Process a user query and return ranked results.

    Args:
        query: The user's search query
        max_length: Maximum allowed query length

    Returns:
        List of ranked result dictionaries with 'sequence' and 'score' keys

    Raises:
        ValueError: If query is empty or exceeds max_length
    """
    # Implementation here
    pass
```

## Testing Guidelines

- Write unit tests for all new functionality
- Aim for high test coverage (>80%)
- Use descriptive test names that explain what is being tested
- Test both success cases and error cases
- Verify determinism for pipeline components

### Example Test

```python
def test_normalize_query_removes_special_chars(self):
    """Test that special characters are removed during normalization."""
    result = normalize_query("hello! world?")
    self.assertEqual(result, "HELLO WORLD")
```

## Documentation

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for architectural changes
- Add docstrings to all public functions
- Include examples in docstrings where helpful

## Performance Considerations

- Profile code changes that might impact performance
- Maintain determinism in all pipeline operations
- Avoid introducing randomness or non-deterministic behavior
- Consider caching opportunities for expensive operations

## Security

- Never commit credentials or secrets
- Use parameterized queries for database operations
- Validate and sanitize all user inputs
- Follow the principle of least privilege
- Report security vulnerabilities privately (see SECURITY.md)

## Questions?

If you have questions about contributing, feel free to:
- Open an issue with the "question" label
- Reach out to the maintainers

Thank you for contributing to MNN Pipeline!
