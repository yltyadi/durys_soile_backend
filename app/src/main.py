import os
import json
from enum import Enum
from pathlib import Path
from fastapi.responses import FileResponse

from fastapi import FastAPI, HTTPException

import pymongo

from models.parasite import Parasite

from models.mispronounced import Mispronounced

app = FastAPI(root_path='/api/v1.0')
client = pymongo.MongoClient(os.environ["MONGODB_URL"])
db = client.duryssoile
data = db.data


class WordType(str, Enum):
    parasite = 'parasite'
    commonly_mispronounced = 'commonly-mispronounced'


class SortingOrder(str, Enum):
    ascending = 'asc'
    descending = 'desc'


@app.get('/words')
def get_words(type: WordType, filter: str = '', offset: int = 0, limit: int = 20,
              sort: SortingOrder = SortingOrder.ascending):
    details = []
    if offset < 0:
        details.append(
            {'loc': ['query', 'offset'], 'msg': 'value is not in a valid range; valid range: non-negative numbers',
             'type': 'value_error'})
    if limit < 0:
        details.append(
            {'loc': ['query', 'limit'], 'msg': 'value is not in a valid range; valid range: non-negative numbers',
             'type': 'value_error'})
    if details:
        raise HTTPException(status_code=400, detail=details)

    cursor = data.find({})
    documents = []
    for document in cursor:
        if document['type'] != type:
            continue
        if filter != '' and not document['word'].lower().startswith(filter.lower()):
            continue
        document.pop('_id')
        document.pop('filename')
        documents.append(document)

    documents = sorted(documents, key=lambda k: k['id'])
    if sort == SortingOrder.descending:
        documents.reverse()
    return documents[offset * limit: (offset + 1) * limit]


@app.get('/words/{word_id}')
def get_word(word_id: int):
    if word_id not in range(data.count_documents({})):
        raise HTTPException(status_code=404, detail='Not Found')
    word = data.find_one({'id': word_id})
    word.pop('_id')
    word.pop('filename')
    return word


@app.get('/audio/{word_id}')
def get_audio(word_id: int):
    if word_id not in range(data.count_documents({})):
        raise HTTPException(status_code=404, detail='Not Found')
    word = data.find_one({'id': word_id})
    path = Path(os.getenv('AUDIO_PATH')) / Path(word['type']) / Path(word['filename'])
    return FileResponse(path)


@app.post('/word')
def post_word(parasite: Parasite, mispronounced: Mispronounced, type: WordType):
    if type is None:
        raise HTTPException(status_code=400, detail='type is required')
    word = None
    if type == WordType.parasite:
        word = parasite
    elif type == WordType.commonly_mispronounced:
        word = mispronounced

    if word.word is None or word.word == "" or word.filename is None or word.filename == "":
        raise HTTPException(status_code=400, detail='word or filename is empty')
    word.id = data.find_one(sort=[("id", -1)])['id'] + 1
    result = dict(word)
    if type == WordType.parasite:
        correctVersions = []
        for correctVersion in word.correctVersions:
            correctVersions.append(dict(correctVersion))
        result['correctVersions'] = correctVersions
    result['type'] = type
    data.insert_one(result)
    result.pop('_id')
    return result


@app.put('/word')
def post_word(parasite: Parasite, mispronounced: Mispronounced, type: WordType):
    if type is None:
        raise HTTPException(status_code=400, detail='type is required')
    word = None
    if type == WordType.parasite:
        word = parasite
    elif type == WordType.commonly_mispronounced:
        word = mispronounced

    if word.word is None or word.word == "" or word.filename is None or word.filename == "" or word.id is None or word.id < 0:
        raise HTTPException(status_code=400, detail='word or filename is empty or id is invalid')

    record = data.find_one({'id': word.id})
    if record is None:
        raise HTTPException(status_code=500, detail=f'No Document was found with id {word.id}')
    data.delete_one({'id': word.id})

    result = dict(word)
    if type == WordType.parasite:
        correctVersions = []
        for correctVersion in word.correctVersions:
            correctVersions.append(dict(correctVersion))
        result['correctVersions'] = correctVersions
    result['type'] = type
    data.insert_one(result)
    result.pop('_id')
    return result


@app.delete('/word')
def post_word(id: int):
    if id not in range(data.count_documents({})):
        raise HTTPException(status_code=404, detail='Not Found')
    result = data.find_one({'id': id})
    if result is None:
        raise HTTPException(status_code=500, detail=f'No Document was found with id {id}')
    result = dict(result)
    result.pop('_id')
    data.delete_one({'id': id})
    return result


@app.get('/migrate')
async def migrate(key: str):
    if key is None or key == '' or key != os.getenv('AUTH_KEY'):
        raise HTTPException(status_code=401, detail='Authentication failed')

    def add_word_type(words, word_type, filename):
        def load_json():
            with open(filename, mode='r', encoding='utf-8') as file:
                return json.load(file)

        for word in load_json():
            word |= {'type': word_type}
            words.append(word)

    data.delete_many({})
    print("Deleted all documents")

    words = []
    add_word_type(words, 'parasite', 'parasite.json')
    add_word_type(words, 'commonly-mispronounced', 'commonly-mispronounced.json')

    for word in words:
        data.insert_one(word)
    return {'status': 'successfully migrated'}
