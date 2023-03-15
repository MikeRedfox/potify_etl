from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from main import Song
import pandas as pd
from urllib.request import urlopen
import json

app = FastAPI()
templates = Jinja2Templates(directory='templates')

url = 'https://raw.githubusercontent.com/MikeRedfox/potify_etl/main/db.json'
response = urlopen(url)
json_data = response.read().decode('utf-8', 'replace')

d = json.loads(json_data)
df = pd.DataFrame(d['_default']).transpose()
top = df.sort_values(['n'],ascending=False)


@app.get('/', response_class=HTMLResponse)
async def root(request: Request):
    top = df.sort_values(['n'],ascending=False).head(10)
    return templates.TemplateResponse('index.html', {'request':request, 'top':top, 'n':10, 'top_or_bottom':'Top'})

@app.get('/top{n}', response_class=HTMLResponse)
async def choose_top_n(n:int, request:Request):
    top = df.sort_values(['n'],ascending=False).head(n)
    return templates.TemplateResponse('index.html', {'request':request, 'top':top, 'n':n, 'top_or_bottom':'Top'})

@app.get('/bottom{n}', response_class=HTMLResponse)
async def choose_bottom_n(n:int, request:Request):
    top = df.sort_values(['n'],ascending=False).tail(n)
    return templates.TemplateResponse('index.html', {'request':request, 'top':top, 'n':n,'top_or_bottom':'Bottom'})