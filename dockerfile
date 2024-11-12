# Use the Python 3.11 base image
FROM python:3.11

# Set the working directory to /src
WORKDIR /src

# Install Poetry to manage Python dependencies
RUN pip install poetry

# Copy the pyproject.toml and poetry.lock files for dependency management
COPY ./pyproject.toml /src/pyproject.toml
COPY ./poetry.lock /src/poetry.lock

# Install dependencies without creating a virtual environment
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

# Copy the rest of the source code into the /src directory
COPY . /src

# Expose port 8080 to the outside world
EXPOSE 8080

# Command to serve static files and run the main.py script
CMD ["python","main.py"]
