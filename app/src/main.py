import os
import json
from enum import Enum
from pathlib import Path
from fastapi.responses import FileResponse

from fastapi import FastAPI, HTTPException

import motor.motor_asyncio

app = FastAPI(root_path='/api/v1.0')
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])
db = client.duryssoile
data = db.get_collection("data")


class WordType(str, Enum):
    parasite = 'parasite'
    commonly_mispronounced = 'commonly-mispronounced'


class SortingOrder(str, Enum):
    ascending = 'asc'
    descending = 'desc'


async def retrieve_all_data():
    cursor = data.find()
    documents = []
    async for document in cursor:
        document.pop('_id')
        documents.append(document)
    return documents


@app.get('/words')
async def get_words(type: WordType, filter: str = '', offset: int = 0, limit: int = 20,
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

    words = await retrieve_all_data()

    # filter by word type
    result_ids = [word_id for word_id in range(len(words)) if words[word_id]['type'] == type]

    # filter by 'filter' argument value
    result_ids = [word_id for word_id in result_ids if words[word_id]['word'].lower().startswith(filter.lower())]

    # ordering depending on 'sort' argument value
    if sort == SortingOrder.descending:
        result_ids.reverse()

    # applying pagination
    result_ids = result_ids[offset * limit: (offset + 1) * limit]

    # formatting response (adding 'id' field, removing 'filename', creating array of objects)
    results = [{'id': word_id} | {x: y for x, y in words[word_id].items() if x != 'filename'} for word_id in result_ids]

    return results


@app.get('/words/{word_id}')
async def get_word(word_id: int):
    words = await retrieve_all_data()
    if word_id not in range(len(words)):
        raise HTTPException(status_code=404, detail='Not Found')

    # formatting response (adding 'id' field, removing 'filename')
    results = {'id': word_id} | {x: y for x, y in words[word_id].items() if x != 'filename'}

    return results


@app.get('/audio/{word_id}')
async def get_audio(word_id: int):
    words = await retrieve_all_data()
    if word_id not in range(len(words)):
        raise HTTPException(status_code=404, detail='Not Found')

    path = Path(os.getenv('AUDIO_PATH')) / Path(words[word_id]['type']) / Path(words[word_id]['filename'])
    return FileResponse(path)


@app.get('/migrate')
async def migrate():
    def add_word_type(words, word_type, filename):
        def load_json():
            with open(filename, mode='r', encoding='utf-8') as file:
                return json.load(file)

        for word in load_json():
            word |= {'type': word_type}
            words.append(word)

    await data.delete_many({})
    print("Deleted all documents")

    words = []
    add_word_type(words, 'parasite', 'parasite.json')
    add_word_type(words, 'commonly-mispronounced', 'commonly-mispronounced.json')

    for word in words:
        data.insert_one(word)
    return {'status': 'success'}
