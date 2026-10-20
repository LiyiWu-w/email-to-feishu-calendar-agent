"""Manual one-off writes only; never enabled by schedule."""
import json
import os
import re
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from feishu import Feishu,TZ
ALLOWED_TYPES={'笔试','面试','AI面','测评','试考','考点预约','其他'}
ALLOWED_STATUSES={'confirmed','deadline'}
def parse(raw,now=None):
    if not raw or len(raw)>14000:raise ValueError('Missing or oversized events JSON')
    data=json.loads(raw)
    if not isinstance(data,list) or not 1<=len(data)<=5:raise ValueError('1-5 events required')
    now=now or datetime.now(TZ)
    result=[];seen=set()
    for entry in data:
        if not isinstance(entry,dict):raise ValueError('Event must be object')
        keys=('company','type','title','date','start_time','end_time','status','detail')
        item={k:entry.get(k,'') for k in keys}
        if any(not isinstance(v,str) for v in item.values()):raise ValueError('All event values must be strings')
        if any(len(v)>200 for k,v in item.items() if k!='detail') or len(item['detail'])>500:raise ValueError('Event fields too long')
        if not item['company'].strip() or not item['title'].strip():raise ValueError('Company/title required')
        if item['type'] not in ALLOWED_TYPES or item['status'] not in ALLOWED_STATUSES:raise ValueError('Unsupported type or status')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',item['date']) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',item['start_time']):raise ValueError('Exact time required')
        start=datetime.strptime(item['date']+' '+item['start_time'],'%Y-%m-%d %H:%M').replace(tzinfo=TZ)
        if item['end_time'] and not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',item['end_time']):raise ValueError('Invalid end time')
        end=datetime.strptime(item['date']+' '+item['end_time'],'%Y-%m-%d %H:%M').replace(tzinfo=TZ) if item['end_time'] else start+timedelta(minutes=30)
        if end<=start:end+=timedelta(days=1)
        if end-start>timedelta(hours=12):raise ValueError('Event longer than 12h')
        if start<=now:continue
        if start>now+timedelta(days=366):raise ValueError('Event too far in future')
        k=(item['company'],int(start.timestamp()),int(end.timestamp()))
        if k in seen:continue
        seen.add(k);result.append(item)
    return result

def sync():
    if os.getenv('APPROVE_SYNC')!='WRITE_APPROVED_ONLY':raise RuntimeError('Manual approval required')
    if os.getenv('DRY_RUN','true').lower()!='true':raise RuntimeError('Global DRY_RUN must remain true')
    cid=os.getenv('FEISHU_CALENDAR_ID','').strip()
    if not cid:raise RuntimeError('FEISHU_CALENDAR_ID missing')
    items=parse(os.getenv('APPROVED_EVENTS_JSON',''))
    if not items:print('Nothing to write: past/duplicate entries');return
    api=Feishu()
    for item in items:
        status,event_id=api.create_event(cid,item)
        print(status+': '+item['company']+' '+item['title']+' id='+event_id)
    print('Manual batch complete; preview settings unchanged')

if __name__=='__main__':sync()
