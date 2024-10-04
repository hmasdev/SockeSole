# SockeSole

a python library which provides you a interface like input/print.

## Requirements

- python >= 3.10

## Installation

```bash
pip install git+https://github.com/hmasdev/SockeSole
```

or

```bash
git clone https://github.com/hmasdev/SockeSole
cd SockeSole
pip install .
```

## Usage

### Server-side

### Client-side

## Contribution

### Requirements

- `uv`

### Development

1. Fork the repository: [https://github.com/hmasdev/SockeSole](https://github.com/hmasdev/SockeSole)

2. Clone the repository

   ```bash
   git clone https://github.com/{YOURE_NAME}/SockeSole
   cd SockeSole
   ```

3. Create a virtual environment and install the required packages

   ```bash
   uv sync --dev
   ```

4. Checkout your working branch

   ```bash
   git checkout -b your-working-branch
   ```

5. Make your changes

6. Test your changes

   ```bash
   uv run pytest
   uv run flake8 sockesole tests
   uv run mypy sockesole tests
   ```

   Note that the above commands run only unit tests.
   It is recommended to run integration tests with `uv run pytest -m integration`.

7. Commit your changes

   ```bash
   git add .
   git commit -m "Your commit message"
   ```

8. Push your changes

   ```bash
   git push origin your-working-branch
   ```

9. Create a pull request: [https://github.com/hmasdev/SockeSole/compare](https://github.com/hmasdev/SockeSole/compare)


## License

[MIT](LICENSE)

## Author

[hmasdev](https://github.com/hmasdev)
