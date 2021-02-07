# SluggoAPI
Sluggo is a small and flexible issue tracker for small teams, intended 
to provide an effective free and (eventually) open source alternative to
tools like JIRA and GitHub Issues, while providing a modern user 
experience not typically seen in open source issue trackers.

This repository holds the backend Django application for Sluggo, which
will provide a server which Sluggo frontends may connect to.

## Installation
Currently, installation steps are focused on development. This process 
will hopefully be simplified once more complete versions of the tracker
are available.

To install Sluggo on development machines, perform the following:

1. Create the virtual environment for Sluggo using the command 
`python3 -m venv sluggoAPI`

2. Activate the Sluggo virtual environment. 
    
    a. For POSIX platforms (macOS
and Linux) run:
`source ./sluggoAPI/bin/activate`

    b. For Windows:
`.\sluggoAPI\Scripts\activate.bat`

3. Install the dependencies for Sluggo to run using the command 
`pip install -r ./requirements.txt`

4. Set the environment variable `SLUGGO_DJANGO_KEY` to some random, 
unique value (only important for production):
`export SLUGGO_DJANGO_KEY="not important for non producton"`

## Initialization

This assumes that a slack app is already created. Do the following:

1. Create a superuser with the command:
`python3 manage.py createsuperuser`

2. In a browser navigate to `$HOST/admin`, replacing `$HOST` with whatever the domain the local server is run with.

3. Add a Social Application. (this is not important if you are not dependent on the slack api)
    
    a. Set provider to Slack
    
    b. Set name to something appropriate like slack or slack-bot, etc
    
    c. Enter the Client id from the slack bot's dashboard
    
    d. Enter the secret key from the slack bot's dashboard
    
    e. Leave Key empty
    
    f. Choose the first site in the list (likely to be `example.com`)
    
    g. Save.

## Running

1. Activate the virtual environment shown in the Installation steps.

    a. For POSIX platforms (macOS and Linux):
`source ./sluggoAPI/bin/activate`

    b. For Windows:
`.\sluggoAPI\Scripts\activate.bat`

2. Run the following command whenever changes to the database models 
are made. This is likely necessary whenever new versions of the 
repository are pulled, or your version of SluggoAPI is otherwise 
upgraded:
`python manage.py makemigrations; python manage.py migrate`

3. Run with:
`python manage.py runserver`

## Documentation
Documentation is hosted within the browser when you run a copy of the
server, and is automatically updated to the latest changes made to
the API. Additionally, the documentation is interactive, and will let
you immediately experiment with the API and its various endpoints given
input data. For more details, see [SwaggerUI's documentation](https://github.com/swagger-api/swagger-ui).

To launch the documentation server, simply run your Django server by 
running `python manage.py runserver` as above.

In your browser, navigate to `$HOST/api/schema/swagger-ui` for a 
browsable overview of the endpoints, replacing `$HOST` with the IP and
port on which you are running the API (for example, 127.0.0.1:8000).

## Contributing
Currently, we are not accepting third-party contributions to SluggoAPI.
We are focusing our efforts on developing a solid core application which
can accept more developers. We intend to determine the best way to
approach accepting third party contributions, and will do so when
we feel the project is in a good state to do so.

For internal contributors to Slugbotics, please read CONTRIBUTING.md 
for guidance on contribution standards.

## License
We are currently still determining an acceptable license for the
project. For now, the project is All Rights Reserved for Slugbotics.
