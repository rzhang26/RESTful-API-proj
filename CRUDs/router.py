import json
import base64

from fastapi import APIRouter, HTTPException, Query, Request
from sqlmodel import select
from typing import Optional 

from CRUDs.models import Campaign, CampaignCreated, Response, PaginatedResponse
from CRUDs.database import SessionDep

router = APIRouter()

@router.get('/')
async def homepage():
    return {'Homepage': 'Hello World'}


def encode_cursor(value: Optional[int]) -> Optional[str]:
    raw = json.dumps({'Cursor_id': value})
    return base64.urlsafe_b64encode(raw.encode()).decode()

def decode_cursor(cursor: Optional[str]) -> Optional[int]:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    payload = json.loads(raw)
    return payload['Cursor_id']

@router.get('/campaigns', response_model=PaginatedResponse[list[Campaign]])
async def read_campaigns(request: Request, session: SessionDep, cursor: Optional[str] = Query(None), limit: int = Query(10, ge=1)):
    cursor_id = 0
    if cursor:
        cursor_id = decode_cursor(cursor)
    
    data = session.exec(select(Campaign).order_by(Campaign.campaign_id).where(Campaign.campaign_id > cursor_id).limit(limit + 1)).all()
    if not data: #edge case check
        raise HTTPException(status_code=404, details='data not found or query param \'cursor\' unrecognized')
    
    base_url = str(request.url).split('?')[0]
    next_url = None
    if len(data) > limit:
        next_cursor = encode_cursor(int(data[:limit][-1].campaign_id))
        next_url = f'{base_url}?cursor={next_cursor}&limit={limit}'

    prev_cursor = encode_cursor(max(0, cursor_id - limit)) #0 since primary_key=True begins campaign_id at 1
    prev_url = f'{base_url}?cursor={prev_cursor}&limit={limit}'

    return {
        'data': data[:limit],
        'next_url': next_url,
        'prev_url': prev_url
    }    

@router.get('/campaigns/{id}', response_model=Response[Campaign])
async def read_campaign(id: int, session: SessionDep):
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404)
    
    return {
        'data': data
    }

@router.post('/campaigns', response_model=Response[Campaign])
async def create_campaign(campaign: CampaignCreated, session: SessionDep):
    db_campaign = Campaign.model_validate(campaign)
    
    session.add(db_campaign)
    session.commit()
    session.refresh(db_campaign)
    
    return {
        'data': db_campaign
    }

@router.put('/campaigns/{id}', response_model=Response[Campaign])
async def update_campaign(id:int, campaign: CampaignCreated, session: SessionDep):
    db_campaign = Campaign.model_validate(campaign)
    
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404)
    
    data.name = db_campaign.name
    data.due_date = db_campaign.due_date
    session.commit()
    session.refresh(data)
    
    return {
        'data': db_campaign
    }

@router.delete('/campaigns/{id}', response_model=None)
async def deletecampaign(id: int, session: SessionDep):    
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404)

    session.delete(data)
    session.commit()
