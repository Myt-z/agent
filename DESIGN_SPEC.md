# 花生旅行规划 — UI 设计规范

## 品牌

- **名称**：花生
- **一句话**：去任何地方，都有人替你规划好一切
- **Slogan**：你的私人旅行顾问
- **品牌调性**：温暖、不张扬、小而扎实——像花生埋在土里，不喧哗但有内容

---

## 配色

```
背景色（页面底）   #faf8f5    warm white
卡片色             #ffffff    pure white
主文字             #1c1917    near black
次要文字           #78716c    warm gray
辅助/禁用文字       #a8a29e    stone
边框               #e7e5e4    light stone
浅边框             #f0eeec    lighter stone

主强调色           #c97d45    warm terracotta/apricot（暖风杏）
主强调色 hover     #a8602e    darker terracotta
强调色浅底         #fef3e8    warm cream
强调色极浅底       #fef8f4    lighter warm cream
```

---

## 布局

```
┌────────────┬──────────────────────────────────┐
│  SIDEBAR   │           MAIN                   │
│  280px     │          flex:1                  │
│            │                                  │
│  brand     │    ┌─────────────────────┐       │
│  user      │    │    landing page      │       │
│  stats     │    │    (centered)        │       │
│  presets   │    │                      │       │
│  history   │    │  "去任何地方"         │       │
│  seasonal  │    │  [___搜索框___]      │       │
│  popular   │    │  [天数][预算][偏好]   │       │
│            │    │                      │       │
│            │    │  [灵感卡片 x 4]       │       │
│            │    └─────────────────────┘       │
│            │                                  │
│            │  footer: "花生 · 你的私人旅行顾问" │
└────────────┴──────────────────────────────────┘
```

---

## 侧边栏（280px，白色底，右边有 1px 分割线）

从上到下 7 个区块，用 `hr` 分割：

### 1. 品牌
- 🥜 emoji（32x32 圆角方块，暖杏底色）+ "花生" 文字（18px, weight 650）

### 2. 用户
- 标题 `10px uppercase letter-spacing:1px tertiary color`
- 输入框：placeholder "你的名字"，focus 时边框变强调色

### 3. 旅行记录
- 两个小数字卡片并排
- 卡片：浅灰底圆角 8px，数字 18px bold，标签 10px tertiary
- 内容：「12 次规划」「8 个城市」

### 4. 一键场景
- 4 个按钮竖排，hover 时边框变强调色、背景变极浅暖色
- 周末两日 · 说走就走
- 美食地图 · 吃遍全城
- 深度人文 · 博物馆之旅
- 户外徒步 · 山水之间

### 5. 最近计划
- 每条一行，左边城市名+天数，右边预算数字
- 示例：西安 3日 ¥1,952 / 成都 2日 ¥1,640 / 广州 4日 ¥2,830

### 6. 当月推荐
- 3 张小卡片，每张有 emoji + 城市名 + 推荐理由
- 桂林 🥬 漓江烟雨正当时
- 青海湖 🌻 油菜花季即将到来
- 厦门 🏖 不热不燥的海风

### 7. 热门目的地
- 圆角标签云：西安 成都 重庆 杭州 昆明 长沙 大理 拉萨
- hover 时边框变强调色、文字变强调色

---

## 主区域

### Landing 状态（默认显示）

- 顶部 tag：小药丸 "AI 旅行规划"，暖杏底+暖杏字
- H1：36px bold，"去**任何地方**，都有人替你规划好一切"
- 副标题：15px secondary，"告诉我们目的地和预算，剩下的交给花生。"
- 搜索框：白色卡片，圆角 12px，内部左 input + 右 button
  - input placeholder: "想去哪里？输入城市或点击「帮我推荐」"
  - button：强调色底白字 "开始规划"
- 参数行（天数 select / 预算 input / 偏好 select）
- 灵感卡片区（见下方）

### 灵感卡片
- 标题：`13px uppercase letter-spacing tertiary`
- 4 列 grid，每张卡片：白色底 1px 边框 12px 圆角
- 内容：emoji(28px) + 城市名(14px bold) + slogan(11px tertiary)
- hover：边框变强调色、轻微上浮(-1px)、阴影加深
- 4 张卡片内容：
  - 🏯 西安 · 十三朝古都 · 碳水天堂
  - 🐸 成都 · 火锅与熊猫的慢生活
  - 🏢 广州 · 食在广州 · 早茶文化
  - 🌳 杭州 · 西湖畔的烟雨江南

### Loading 状态

- 居中显示
- 3 个呼吸点动画（强调色圆点，pulse 动画 1.4s cycle，依次 delay 0/0.2/0.4s）
- 文字："正在为你规划旅程" + "搜遍攻略 · 精算预算 · 安排行程"

### Result 状态

- 标题行：城市 · X 日游（22px bold）+ 右侧两个按钮（重新规划 / 下载计划）
- 内容卡片：白色底、1px 边框、12px 圆角、36px 内边距
- 内容为 Markdown 渲染的旅行计划文本
- H3 标题使用强调色 #c97d45

---

## 字体

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
```

- 所有字号 10-38px
- 标题 weight 650-700
- 正文 weight 400
- 标签 weight 500-600
- letter-spacing: 标题 -0.3~-0.9px, 标签 +0.3~+1px
- line-height: 正文 1.6-1.8, 标题 1.2

---

## 交互

- 所有可点击元素有 hover 过渡（transition 0.12-0.2s）
- 搜索框 focus 时边框变强调色 + 阴影加深
- 输入框 focus 时边框变强调色
- 灵感卡片和热门标签点击 = 填入城市名 + 触发规划
- 一键场景按钮点击 = 填入预设参数 + 触发规划

---

## 绝对不要

- ❌ 不要暴露任何技术栈信息（LangChain / ChromaDB / MCP / Agent / RAG / Streamlit）
- ❌ 不要显示模型名、环境名、pipeline 状态
- ❌ 不要出现 "系统做了什么" 或 "技术亮点" 之类的内部文档内容
- ❌ 不要用超过 2 种字体粗细做对比
- ❌ 不要花里胡哨的渐变、阴影堆叠、动画过度
- ❌ 不要 emoji 做标题主要的装饰（卡片内的图标 emoji 可以保留）

---

## 响应式

- ≤768px：隐藏侧边栏，主区域 padding 缩小，搜索框竖向排列，灵感卡片 2 列，footer 全宽

---

## 当前文件

- 设计预览：`design-preview.html`（纯 HTML+CSS，可直接浏览器打开看效果）
- 目标文件：`app.py`（Streamlit 应用，按此规范改造）

---

## 配色速查卡

```
暖风杏（主按钮/强调文字/链接）   #c97d45
暖风杏 hover                     #a8602e
暖风杏浅底（tag/强调区背景）      #fef3e8
暖风杏极浅底（hover 背景）        #fef8f4
页面背景                          #faf8f5
卡片/侧边栏背景                   #ffffff
主文字                            #1c1917
次要文字                          #78716c
辅助文字                          #a8a29e
边框                              #e7e5e4
浅边框                            #f0eeec
```
