# Email → Feishu Calendar Agent / 招聘邮件转飞书日历

**Open-source code template. Operate it in a PRIVATE repository, not this public template.**

读取 163 邮箱中的招聘通知，利用 DeepSeek 解析笔试、测评、AI 面试、预约和截止事项，人工复核后写入飞书日历。默认只做预览，**不自动写入**。

## Privacy / 隐私须知

- **公开仓库只用于分享源码。实际配置和运行必须使用私人仓库。** GitHub Actions 日志、`workflow_dispatch` 输入参数与运行记录可能包含个人考试时间或事件标题。不要在公开仓库中执行真实邮箱扫描或日程同步。
- DeepSeek API 会接收邮件主题和文本内容；请自行核实第三方服务的数据处理政策并征得必要授权。邮件附件不处理。
- 不要提交 `.env`、邮件内容、令牌、IMAP 授权码、飞书日历 ID、运行状态或真实日程。
- 若密钥曾提交到公开仓库，请轮换密钥，不能仅依赖删除文件。

## Features / 功能

- 163 IMAP read-only scan, capped at 50 recent emails from last 30 days.
- DeepSeek AI structured extraction; no email sender addresses or personal URLs in formatted preview.
- `72小时` 等相对有效期从 IMAP **服务器收件时间**推算，并标记为**估算、需要人工核实**；催办提醒不能重置有效期。
- Manual one-batch calendar import (1–5 events) with remote duplicate detection and idempotency key.
- No recurring writes, no state checkpoint and no historical import.

## Setup / 配置（私人仓库）

1. 新建**私人仓库**，上传此项目全部源码，作为个人运行副本。不要从含个人信息的旧仓库保留 Git 历史。
2. 安装 Python 3.11+，运行 `pip install -r requirements.txt`。
3. GitHub repository **Secrets**: `MAIL_USER`（完整163邮箱）, `MAIL_AUTH_CODE`（IMAP 授权码）, `DEEPSEEK_API_KEY`, `FEISHU_APP_ID`, `FEISHU_APP_SECRET`。
4. GitHub repository **Variables**: `FEISHU_CALENDAR_ID`（自己创建、可访问的飞书日历 ID）。该日历需对飞书应用具备事件读写权限，并确认用户已在客户端订阅/能看到。这个模板不自动创建日历或自动配置飞书权限。
5. 在私人仓库 Actions 页面手动运行 `Preview recruitment emails`。**出于日志隐私，云端只显示摘要数量**；如需查看提取的具体事项，在自己电脑上配置环境变量并以 `SHOW_EVENT_DETAILS=true DRY_RUN=true python agent.py` 本地预览。
6. 在核对原始邮件、确认事件真实且时间正确后，手动运行 `Manually sync reviewed events`，选择 `WRITE_APPROVED_ONLY`，输入 JSON 数组（最多 5 项）。这是一项明确写入操作，仅应在私人仓库中进行。

### Example JSON (fictional / 虚构数据)

```json
[{"company":"Example Bank","type":"笔试","title":"Online written test","date":"2027-05-20","start_time":"14:00","end_time":"16:00","status":"confirmed"}]
```

允许 `type`: `笔试`, `面试`, `AI面`, `测评`, `试考`, `考点预约`, `其他`；允许 `status`: `confirmed`, `deadline`。日期和时间必须使用北京时间 `YYYY-MM-DD` 和 `HH:MM`。预计截止时间请在标题或备注中标为估算。

## Safety notes / 安全说明

- `DRY_RUN=true` 始终用于扫描；人工手动同步单独通过 `APPROVE_SYNC=WRITE_APPROVED_ONLY` 授权。
- 仅检查飞书所选日历的已有事件，不会更新、删除或取消旧事件。改期需人工处理。
- 未知具体时间、可选场次、失效时间未验证事项应先人工审核；请勿盲目将预估时刻作为官方截止。
- GitHub Actions 可能延迟，163 IMAP 对云端环境可能要求额外验证；飞书应用日历权限需要单独配置。
- 项目未在真实外部 163/DeepSeek/飞书账号上端到端验证；请先在专门的测试日历验证权限和去重。

## Run tests / 测试

```bash
python -m unittest discover -s tests -v
```

## License

MIT. See [LICENSE](LICENSE).
