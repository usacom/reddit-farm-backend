# Use local "virtual env"

use:

```
    source ./bin/activate.fish
```

or any off:

```
    source ./bin/activate.*
```

# Update requirements

```
pip3.7 freeze > requirements.txt
```

# Install requirements

```
pip3.7 install -r ./requirements.txt
```

# Run dev api server

```
uvicorn main:app --reload
```
