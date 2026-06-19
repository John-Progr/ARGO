# Dockerfile
# start from an official Python image
FROM python:3.13-slim          

# set the working directory in the container
# all commands run from /app inside the container
WORKDIR /app                   

# Upgrade pip
RUN pip install --upgrade pip

# copy requirements first (Docker caches this layer)
COPY requirements.txt .     

# install dependencies
RUN pip install -r requirements.txt   

# copy the rest of your code  (including main.py in the root folder)
COPY . .                       

# Expose the port for FastAPI to communicate
# EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
#CMD ["poetry", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
# start the server when the container runs
# 0.0.0.0 means "accept connections from outside the container"