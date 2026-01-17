masuk venv
.venv\Scripts\activate

train
dataset.csv label 1 postif, label o netral, label -1 negatif
python train.py


test
buka terminal 2
terminal1 : uvicorn api_fastapi:app --reload --port 8000
terminal2 : python app.py