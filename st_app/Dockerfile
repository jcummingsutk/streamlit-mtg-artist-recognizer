FROM python:3.10-slim-buster

WORKDIR /st_app

COPY model/non_torch_requirements.txt ./model/

COPY model/torch_requirements.txt ./model/

RUN pip install --upgrade pip

RUN pip install -r ./model/non_torch_requirements.txt

RUN pip install -r ./model/torch_requirements.txt --index-url https://download.pytorch.org/whl/cpu

COPY . .

WORKDIR /

CMD ["python", "-m", "streamlit", "run", "st_app/app.py", "--server.port", "8000", "--server.address", "0.0.0.0"]