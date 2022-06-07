# Create local venv

```
python3.7 -m venv .
```

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

# Create `.config`

Create `.config/db/config.cfg`:
```
[postgres]
user=postgres
password=pass
host=localhost
db=server-db
```

Create `.config/reddit/config.cfg`:
```
[reddit]
client_id = your-client-id
client_secret = your-client-secret-code
user_agent = site-farm v1.0 by u/clara_usa_t
```

# Run dev api server

```
uvicorn main:app --reload
```
