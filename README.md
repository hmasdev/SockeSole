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

<table>

<tr>
<td>Server-side</td>
<td>Client-side</td>
</tr>

<tr>
<td>

```python
>>> from sockesole import SocketConsoleServer
>>> server = SocketConsoleServer(host='localhost', port=10111)
>>> server.run()
-
>>> server.get_keys()
[('127.0.0.1', 58167)]
>>> server.get_console(server.get_keys()[0]).echo('hello from server')
-
-
>>> server.get_console(server.get_keys()[0]).prompt('say something', wait=0.01)
-
-
'reponse'
-
-
-
-
>>> server.get_keys()
[]
```

</td>
<td>

```python
>>> from sockesole import SocketConsoleClient
-
-
>>> client = SocketConsoleClient.connect('localhost', port=10111)
-
-
-
>>> client.read()
'hello from server'
-
>>> client.read()
'say something'
>>> client.write('reponse')
-
>>> client.close()
>>> client.alive()
False
-
-
```

</td>
</tr>

</table>

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
