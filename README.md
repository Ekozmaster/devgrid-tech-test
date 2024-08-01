This app fetches data fom Open Weather API using a background process, caching results in Redis. A REST API is available for querying the data.
This is meant for a technical test, part of a hiring process for DevGrid.

## Installation
### Requirements
- Python 3.12 (via Pyenv is recommended).
- Docker version 27+ preferred.

## Key design decisions
- FastAPI for its simplicity and decoupled design (no ORMs or HTML template engines like Django)
- API is able to scale horizontally independent of its core worker, which should be a singular instance.
- Open weather recommends consulting data every 10 minutes since it's their refresh rate, so the worker attempts to keep cities up to date within that time window.
