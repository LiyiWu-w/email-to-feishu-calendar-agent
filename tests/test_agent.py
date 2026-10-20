import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from agent import countdown_hours, due_from_receipt, normalize_items, clean_summary
from sync_approved import parse

class LogicTests(unittest.TestCase):
    def test_link_valid_for_72_hours(self):
        hours, _=countdown_hours('AI在线面试邀请','专属链接有效期为72小时')
        self.assertEqual(hours,72)
        dt=datetime(2026,10,19,13,22,tzinfo=ZoneInfo('Asia/Shanghai'))
        self.assertEqual(due_from_receipt(dt,72).strftime('%Y-%m-%d %H:%M'),'2026-10-22 13:22')
    def test_reminder_not_reset(self):
        self.assertIsNone(countdown_hours('AI面试提醒','链接有效期为72小时')[0])
    def test_relative_deadline_review(self):
        dt=datetime(2026,10,19,13,22,tzinfo=ZoneInfo('Asia/Shanghai'))
        result=normalize_items([{'company':'Example','type':'AI面','title':'AI在线面试','status':'information'}],'邀请','链接有效期为72小时',dt)
        self.assertEqual(result[0]['date'],'2026-10-22')
        self.assertTrue(result[0]['review_reason'])
    def test_redact_private_link(self):
        self.assertNotIn("token123", clean_summary("Link https://example.org/private/token123"))
    def test_manual_approval_accepts_ai(self):
        dt=datetime(2026,10,20,tzinfo=ZoneInfo('Asia/Shanghai'))
        event={'company':'Example','type':'AI面','title':'AI Interview','date':'2026-10-22','start_time':'13:22','status':'deadline'}
        self.assertEqual(len(parse(__import__('json').dumps([event]),now=dt)),1)
    def test_manual_skips_expired(self):
        dt=datetime(2026,10,24,tzinfo=ZoneInfo('Asia/Shanghai'))
        event={'company':'Example','type':'AI面','title':'AI Interview','date':'2026-10-22','start_time':'13:22','status':'deadline'}
        self.assertEqual(parse(__import__('json').dumps([event]),now=dt),[])

if __name__=='__main__':unittest.main()
