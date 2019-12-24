
<h1 align="center">bloggy</h1>
<p align="center">A microblog with reddit-like comment system.</p>
<p align="center">Try live <a href="http://bloggy.makuzo.usermd.net">here</a></p>
<p align="center">
<img align="center" width="70%" height="70%" src="https://i.imgur.com/txWiMsL.png"></img>
</p>

### Installing

bloggy requires [Python](https://www.python.org/) 3.7+ to run.

Install the dependencies, make migrations and start the server.

```sh
$ cd bloggy
$ pip install -r requirements.txt
$ python3 manage.py makemigrations
$ python3 manage.py migrate
$ python3 manage.py runserver
```

Using [Poetry](https://python-poetry.org/):

```sh
$ cd bloggy
$ poetry install
$ python3 manage.py makemigrations
$ python3 manage.py migrate
$ python3 manage.py runserver
```

## Running the tests

```sh
$ python3 manage.py test
```

## Contribution

Feel free to contribute to the project by making pull requests!

Please run ```pre-commit run``` before creating a PR.

## Built With

* [Django](https://www.djangoproject.com/) - Python Web framework

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
