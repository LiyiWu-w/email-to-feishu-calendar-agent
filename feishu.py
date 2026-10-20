"""Feishu calendar API, fail-closed duplicate checks."""
import hashlib
import json
import os
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
TZ=ZoneInfo('Asia/Shanghai')
BASE='https://open.feishu.cn/open-apis'
class Feishu:
    def __init__(self):
        for name in ('FEISHU_APP_ID','FEISHU_APP_SECRET'):
            if not os.getenv(name):raise RuntimeError('Missing '+name)
        import requests
        r=requests.post(BASE+'/auth/v3/tenant_access_token/internal',json={'app_id':os.environ['FEISHU_APP_ID'],'app_secret':os.environ['FEISHU_APP_SECRET']},timeout=30)
        r.raise_for_status(); data=r.json()
        if data.get('code')!=0:raise RuntimeError('Feishu authentication failed')
        self.token=data['tenant_access_token']
    def request(self,method,path,**kwargs):
        import requests
        r=requests.request(method,BASE+path,headers={'Authorization':'Bearer '+self.token},timeout=30,**kwargs)
        r.raise_for_status(); data=r.json()
        if data.get('code')!=0:raise RuntimeError('Feishu API error: '+str(data.get('code')))
        return data.get('data') or {}
    def list_near(self,cid,start):
        token=''; seen=set(); items=[]
        for _ in range(100):
            p={'page_size':50,'start_time':str(int((start-timedelta(days=1)).timestamp())),'end_time':str(int((start+timedelta(days=1)).timestamp()))}
            if token:p['page_token']=token
            data=self.request('GET',f'/calendar/v4/calendars/{cid}/events',params=p)
            part=data.get('items')
            if not isinstance(part,list):raise RuntimeError('Calendar response incomplete; refusing write')
            items+=part
            if not data.get('has_more'):return items
            token=data.get('page_token')
            if not token or token in seen:raise RuntimeError('Pagination incomplete; refusing write')
            seen.add(token)
        raise RuntimeError('Calendar pagination limit exceeded')
    def create_event(self,cid,item):
        st=datetime.strptime(item['date']+' '+item['start_time'],'%Y-%m-%d %H:%M').replace(tzinfo=TZ)
        end=item.get('end_time') or ''
        et=datetime.strptime(item['date']+' '+end,'%Y-%m-%d %H:%M').replace(tzinfo=TZ) if end else st+timedelta(minutes=30)
        if et<=st:et+=timedelta(days=1)
        title='【'+item['company']+'】'+item['title']
        stable=json.dumps([item['company'],item['type'],int(st.timestamp()),int(et.timestamp())],ensure_ascii=False,separators=(',',':'))
        key=hashlib.sha256(stable.encode()).hexdigest()
        payload={'summary':title,'description':'类型：'+item['type']+'\n备注：'+item.get('detail','')+'\nEXAM_AGENT_KEY:'+key,'start_time':{'timestamp':str(int(st.timestamp()))},'end_time':{'timestamp':str(int(et.timestamp()))},'is_all_day':False,'visibility':'default'}
        for event in self.list_near(cid,st):
            desc=str(event.get('description') or '')
            existing_stamp=str((event.get('start_time') or {}).get('timestamp') or '')
            if ('EXAM_AGENT_KEY:'+key in desc or (event.get('summary')==title and existing_stamp==str(int(st.timestamp())))):
                if not event.get('event_id'):raise RuntimeError('Duplicate without ID; refusing write')
                return 'EXISTING',event['event_id']
        result=self.request('POST',f'/calendar/v4/calendars/{cid}/events',params={'idempotency_key':key},json=payload)
        return 'CREATED',result['event']['event_id']
