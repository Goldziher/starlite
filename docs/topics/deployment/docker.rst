Docker
======

Docker is a containerization platform that allows you to package your application and all its dependencies together.
It is useful for creating consistent environments for your application to run in, irrespective of the host system
and its own configuration or dependencies - which is especially helpful in preventing dependency conflicts.

This guide uses the `Docker official Python container <https://hub.docker.com/_/python>`_ as a base image.

Use When
--------

Docker is ideal for deploying Python web applications in scenarios where:

- **Isolation:** You require a consistent, isolated environment for your application, independent of the host system.
- **Scalability:** Your application needs to be easily scaled up or down based on demand.
- **Portability:** The need to run your application consistently across different environments (development, testing, production) is crucial.
- **Microservices Architecture:** You are adopting a microservices architecture, where each service can be containerized and managed independently.
- **Continuous Integration/Continuous Deployment (CI/CD):** You are implementing CI/CD pipelines, and Docker facilitates the building, testing, and deployment of applications.
- **Dependency Management:** Ensuring that your application has all its dependencies bundled together without conflicts with other applications.

Alternatives
~~~~~~~~~~~~

For different deployment scenarios, consider these alternatives:

- `systemd <https://www.freedesktop.org/wiki/Software/systemd/>`_:
    A system and service manager, integrated into many Linux distributions for managing system processes.

    .. note:: Official documentation coming soon
- :doc:`Supervisor <supervisor>`:
    A process control system that can be used to automatically start, stop and restart processes; includes a web UI.
- :doc:`Manually with an ASGI server <manually-with-asgi-server>`:
    Direct control by running the application with an ASGI server like Uvicorn, Hypercorn, Daphne, etc.

This guide assumes that you have Docker installed and running on your system, and that you have the following
files in your project directory:

.. code-block:: shell
    :caption: requirements.txt

    litestar[standard]>=2.4.0,<3.0.0

.. literalinclude:: /examples/deployment/docker.py
    :caption: app.py
    :language: python


Dockerfile
----------

.. code-block:: docker
    :caption: Example Dockerfile

    # Set the base image using Python 3.12 and Debian Bookworm
    FROM python:3.12-slim-bookworm

    # Set the working directory to /app
    WORKDIR /app

    # Copy only the necessary files to the working directory
    COPY . /app

    # Install the requirements
    RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

    # Expose the port the app runs on
    EXPOSE 80

    # Run the app with the Litestar CLI
    CMD ["litestar", "run", "--host", "0.0.0.0", "--port", "80"]

This copies your local project folder to the ``/app`` directory in the Docker container and runs your
app via ``uvicorn`` utilizing the ``litestar run`` command. ``uvicorn`` is provided by the ``litestar[standard]``
extra, which is installed in the ``requirements.txt`` file.

You can also launch the application with an :doc:`ASGI server <manually-with-asgi-server>` directly, if you prefer.

Once you have your ``Dockerfile`` defined, you can build the image with ``docker build`` and run it with ``docker run``.

.. dropdown:: Useful Dockerfile Commands

    .. code-block:: shell
        :caption: Useful Docker commands

        # Build the container
        docker build -t exampleapp .

        # Run the container
        docker run -d -p 80:80 --name exampleapp exampleapp

        # Stop the container
        docker stop exampleapp

        # Start the container
        docker start exampleapp

        # Remove the container
        docker rm exampleapp

Docker Compose
--------------

Compose is a tool for defining and running multi-container Docker applications.
Read more about Compose in the `official Docker documentation <https://docs.docker.com/compose/>`_.

If you want to run the container as part of a Docker Compose setup then you can simply use this compose file:

.. code-block:: yaml
    :caption: docker-compose.yml

    version: "3.9"

    services:
      exampleapp:
        build:
          context: ./
          dockerfile: Dockerfile
        container_name: "exampleapp"
        depends_on:
          - database
        ports:
          - "80:80"
        environment:
          - DB_HOST=database
          - DB_PORT=5432
          - DB_USER=litestar
          - DB_PASS=r0cks
          - DB_NAME=exampleapp

      database:
        image: postgres:latest
        container_name: "exampledb"
        environment:
          POSTGRES_USER: exampleuser
          POSTGRES_PASSWORD: examplepass
          POSTGRES_DB: exampledb
        ports:
          - "5432:5432"
        volumes:
          - db_data:/var/lib/postgresql/data

    volumes:
      db_data:

This compose file defines two services: ``exampleapp`` and ``database``. The ``exampleapp`` service is built
from the Dockerfile in the current directory, and exposes port 80. The ``database`` service uses the official
PostgreSQL image, and exposes port ``5432``. The ``exampleapp`` service depends on the ``database`` service, so
the database will be started before the app. The ``exampleapp`` service also has environment variables set for
the database connection details, which are used by the app.

Once you have your ``docker-compose.yml`` defined, you can run ``docker compose up`` to start the containers.
You can also run ``docker compose up -d`` to run the containers in the background, or "detached" mode.

.. dropdown:: Useful Compose Commands

    .. code-block:: shell
        :caption: Useful Docker Compose commands

        # Build the containers
        docker compose build

        # Run the containers
        docker compose up

        # Run the containers in the background
        docker compose up -d

        # Stop the containers
        docker compose down
