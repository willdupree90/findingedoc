# Project
In this project I will do the data science

Give relevant details and links here

## Docker use (preferred for GPU acceleration)

We use the GPU enabled tensorflow image to allow access to resources (required Nvidia drivers and WSL for Windows, follow [guide here](https://www.youtube.com/watch?v=YozfiLI1ogY&t=353s)). This is why we seperate Tensorflow into the `requirements-dev.txt`.

1. Install docker

2. Navigate to root of project

3. Start service by running `docker-compose up` from command line (this could take a while depending on internet speed +1.9 GB)

4. Navigate to `http://127.0.0.1:8888`, can click on link from docker logs if token is needed

5. When finished run `docker-compose down`

## Local setup (via Python virtual environments)

Currently use virtualenvwrapper for python

1. Create an environment using the terminal
We use python 3.9
    - `mkvirtualenv -p 3.9 your_env`

2. Activate and work on environment using
    - `workon your_env`

3. To install pmfraud perform from repo location
This will ensure the development package is installed
    - `pip install -e .[dev]`
