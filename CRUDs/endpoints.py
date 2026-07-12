import base64
import json
from typing import Optional, Generic
from fastapi import APIRouter, HTTPException, Query, Request
from sqlmodel import select

from CRUDs.database import SessionDep
from CRUDs.models import PaginatedResponse, Response, Campaign, CampaignCreated

router = APIRouter()


@router.get('/')
async def homepage():
    return {'Homepage welcome: ' : 'Hello World'}

def encode_cursor(value: Optional[int]) -> str:
    raw = json.dumps({'cursor_id': value}) #dumping the key-val pair {'cursor_id': value} into a new json file
    return base64.urlsafe_b64encode(raw.encode()).decode() #encodes this pair

def decode_cursor(cursor: Optional[str]) -> int:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode() #decodes this pair
    payload = json.loads(raw) #loading the key-val pair {'id': value} into a var 'payload'
    return payload['cursor_id'] #fetches dict['id'] (value)

@router.get('/campaigns', response_model=PaginatedResponse[list[Campaign]])
async def read_campaigns(request: Request, session: SessionDep, cursor: Optional[str] = Query(None), limit: int = Query(10, ge=1)):
    cursor_id = 0
    if cursor:
        cursor_id = decode_cursor(cursor)
    
    data = session.exec(select(Campaign).order_by(Campaign.campaign_id).where(Campaign.campaign_id > cursor_id).limit(limit + 1)).all()
    # if not data:
    #     return {'No data availible to be viewed'}
    
    base_url = str(request.url).split('?')[0]

    next_url = None
    if len(data) > limit:
        next_cursor = encode_cursor(data[:limit][-1].campaign_id)
        next_url = f'{base_url}?cursor={next_cursor}&limit={limit}'

    prev_cursor = encode_cursor(max(-1, cursor_id - limit))
    prev_url = f'{base_url}?cursor={prev_cursor}&limit={limit}'

    return {
        'data': data[:limit],
        'next_url': next_url,
        'prev_url': prev_url
    }


#other crud methods finally
@router.get('/campaigns/{id}', response_model=Response[Campaign])
async def read_campaign(id: int, session: SessionDep):
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404, detail=f'Campaign with ID#{id} object not found or unrecognized. Please try again.')
    
    return {'data': data}

@router.post('/campaigns', response_model=Response[Campaign])
async def post_campaign(campaign: CampaignCreated, session: SessionDep):
    db_campaign = Campaign.model_validate(campaign) #auto validates & return err if not formatted based on CampaignCreated 
    session.add(db_campaign)
    session.commit()
    session.refresh(db_campaign) #auto updates missing attr of campaign_id & created_at

    return {'data': db_campaign}

@router.put('/campaigns/{id}', response_model=Response[Campaign])
async def update_campaign(id: int, campaign: CampaignCreated, session: SessionDep):
    db_campaign = Campaign.model_validate(campaign)
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404, detail=f'Campaign with ID#{id} object not found or unrecognized. Please try again.')

    data.name = db_campaign.name
    data.due_date = db_campaign.due_date
    session.add(data)
    session.commit()
    session.refresh(data) #technically not needed, but could smooth out unexpected errs 
    
    # new_data = await read_campaign(id, session) #if don't add await, encounters a compilation err -> see next line
    #unexecuted coroutine object to FastAPI, which throws a ResponseValidationError 
    # because it expects a dictionary or database object it can convert into JSON.

    return {'data': data} 

@router.delete('/campaign/{id}')
async def delete_campaign(id: int, session: SessionDep):
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404, detail=f'Campaign with ID#{id} object not found or unrecognized. Please try again.')
    
    session.delete(data)
    session.commit()