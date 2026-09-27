# SPARK ONE • Telegram 多语言广播与实时市场控制台

专为 Telegram 论坛话题群（Forum Topics）打造的 Web 化多语言广播与金融行情定时推送平台。

---

## 🌟 核心功能

1. **🌐 11国语言一键分发广播**：
   - 输入母语公告，并发自动翻译为阿、葡、西、马、印尼、泰、越、日、韩、中、英等 11 国语言。
   - 卡片式预览，发送前支持微调任何一句话。
   - 自动路由投递到对应语言的 Topic 话题中。
   - 支持上传配图，图文一体分发。

2. **📈 实时金融大盘与黄金速递**：
   - 实时拉取国际现货黄金（XAU/USD）、白银、原油、美元指数。
   - 实时拉取美股三大指数（S&P 500、纳斯达克、道琼斯）与亚太市场（日经、恒生）。
   - 自动生成符合 Telegram 排版风格的专业行情快讯（带涨跌红绿标识与分析）。
   - 支持一键推送到 `🥇 GOLD MARKET` 或 `📈 GLOBAL MARKETS` 话题。

3. **⏱️ 定时任务自动化调度（Time Scheduler）**：
   - 内置 APScheduler 定时器引擎。
   - 支持设置定时规则（例如：工作日 09:30 早盘播报、16:00 黄金播报、21:30 美股开盘播报）。
   - 支持在后台一键“立即测试执行”或暂停/开启。

4. **⚙️ 话题 ID 智能绑定**：
   - 提供「自动侦测群内 Topics」功能，把 Bot 设为管理员后，在群话题发一条消息即可自动捕获 Thread ID 并完成绑定。

---

## 🚀 快速启动

控制台默认已经在后台运行，你可以直接在浏览器打开：
👉 **http://127.0.0.1:8000** 或 **http://localhost:8000**

如需手动重启或停止：
```bash
# 启动
./start.sh

# 或使用 python 直接启动
./venv/bin/python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

---

## 📖 新手配置指南（3 分钟搞定）

### 第 1 步：创建 Telegram Bot
1. 在 Telegram 搜索 `@BotFather` 发送 `/newbot`。
2. 按提示输入机器人名称与用户名，获得一串 **API Token**（如 `7123456789:AAHq_...`）。
3. 打开 Web 控制台的【话题与配置绑定】，将 Token 填入并保存。

### 第 2 步：将 Bot 拉进 `SPARK ONE Global Community` 大群
1. 将你的 Bot 添加为群成员。
2. **务必给予管理员权限（至少开启「发送消息」、「发帖」权限）**。
3. 把群组的 Chat ID（例如 `-1002345678901`）填入后台。
   - *如果不知道 Chat ID，直接点击后台的【自动侦测群内 Topics】按钮，系统会自动识别！*

### 第 3 步：绑定各个 Topic 的 Thread ID
- **全自动方式**：在群里的各个话题（如 `🇦🇪 SPARK ONE Arabic`、`🥇 GOLD MARKET`）里随便发一条文字（例如发一个 `hi`），然后回 Web 后台点击【自动侦测群内 Topics】，系统即可捕获各话题的 Thread ID。
- **手动方式**：在【话题与配置绑定】表格中，直接输入对应话题的 Thread ID。

---

## 📂 项目结构

```
Spark telegram/
├── backend/
│   ├── main.py                # FastAPI 后端服务与路由
│   ├── config.py              # 配置持久化模块
│   ├── telegram_service.py    # Telegram Bot API 交互与 Topics 识别
│   ├── translation_service.py # 多语言翻译服务 (内置免Key / Gemini / OpenAI / DeepL)
│   ├── market_service.py      # 黄金、商品、全球股指实时数据引擎
│   └── scheduler_service.py   # 定时任务调度器与日志追踪
├── frontend/
│   └── templates/
│       └── index.html         # 现代高颜值 Web 仪表盘
├── data/
│   └── config.json            # 预置 11 个国家语言话题及市场话题的配置文件
├── uploads/                   # 广播上传配图存储目录
├── requirements.txt           # 依赖清单
├── start.sh                   # 一键启动脚本
└── README.md                  # 说明文档
```
