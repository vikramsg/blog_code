## Install

The project uses Poetry, a package and virtual environment manager for Python.  
Installation instructions for poetry are [here](https://python-poetry.org/docs/). 
A TLDR is to do 

```
curl -sSL https://install.python-poetry.org | python3 - --version 1.4.2
```

and then add `$HOME/.local/bin` to the Path. 
```
export PATH="$HOME/.poetry/bin:$PATH"
```

Check for installation using `poetry --version` and make sure it shows `1.4.2`.

Once you have Poetry setup, you can simply go to the root of the directory and do

```
make install
```

## Run

Run a city using

```
make city_journeys CITY=Hamburg 
```