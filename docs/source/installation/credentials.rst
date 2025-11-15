Credentials configuration
=========================

Some VisuSat functionalities require authentication to external data services,
especially for the EUMETSAT Data Store (EUMDAC) and the Copernicus Marine Service
(CMEMS). This page explains how to create the necessary credentials and how to
make them accessible to the library.

EUMETSAT Data Store (EUMDAC)
-----------------------------

1. Create an EUMETSAT account
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You need a Data Store account at:

    https://data.eumetsat.int

Create an account if you do not already have one.

2. Retrieve your API keys
~~~~~~~~~~~~~~~~~~~~~~~~~
After logging in:

- Go to **User Profile** (top right)
- Open the tab **API Keys**
- Create a new API key pair

You will obtain two strings:

- ``consumer_key``
- ``consumer_secret``

3. Create the local credentials file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

VisuSat expects your credentials in a JSON file located at::

    ~/.config/visusat/id_EUMETSAT.json

Create the directory if needed::

    mkdir -p ~/.config/visusat/

Create the file ``id_EUMETSAT.json`` with the following content::

    {
        "consumer": "YOUR_CONSUMER_KEY",
        "secret": "YOUR_CONSUMER_SECRET"
    }

The library automatically detects this file using:

- ``$XDG_CONFIG_HOME`` (if defined)
- or ``~/.config/visusat/`` (fallback)

4. Security recommendation
~~~~~~~~~~~~~~~~~~~~~~~~~~
Never commit this file to Git.

VisuSat will automatically use this file through
``visusat.eumetsat.get_token()``.

Copernicus Marine Service (CMEMS)
---------------------------------

For Copernicus Marine data access, you need an account on:

    https://data.marine.copernicus.eu/

1. Create your CMEMS account
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Registration is free and gives access to all Open data.

2. Login once with the Python client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The first time you use::

    import copernicusmarine

    copernicusmarine.login()

A browser window will open and ask you to authenticate.

Once validated, a token will be stored locally in::

    ~/.copernicusmarine/

No JSON file is needed for CMEMS.

3. Verify that authentication works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can test your setup using::

    copernicusmarine.describe()

or::

    copernicusmarine.subset(...)

Copernicus credentials are automatically managed by the official client.

Summary
-------

- **EUMETSAT** → requires a manual JSON file under
  ``~/.config/visusat/id_EUMETSAT.json``.
- **Copernicus Marine Service** → uses automatic token management
  via ``copernicusmarine login``.

Once these credentials are correctly configured, all VisuSat features can be used
without further action.