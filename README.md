# 🔬 Multi-Agent 封閉迴圈實驗

## 實驗目的
驗證「Moltbook 現象」：在缺乏外部真值的封閉系統中，觀察 AI Agent 如何產生：
1. **幻覺滾雪球** (Hallucination Snowballing)
2. **觀點極端化** (Polarization)  
3. **調停者崩潰** (Mediator Collapse)

## 🆚 版本對比：v1 vs v2

本專案提供兩個實驗版本，作為對照研究：

| 項目 | v1 (封閉迴圈) | v2 (健康討論 + Web Search) |
|------|--------------|---------------------------|
| **腳本** | `simulate_discussion.py` | `simulate_discussion_v2.py` |
| **目的** | 展示封閉系統的問題 | 展示正確的 Multi-Agent 設計 |
| **Temperature** | 0.9（高隨機性） | 0.4（低隨機性） |
| **Agent 設計** | 鼓勵自信（即使不確定） | 鼓勵承認不確定性 |
| **Mediator 角色** | 和稀泥（只說「折衷」） | Facilitator 結構化引導 |
| **討論結構** | 無（自由發揮） | 四階段流程 |
| **質疑機制** | 無 | 有（第三階段專門質疑） |
| **Web Search** | **無（封閉系統）** | **有（即時查證）** |
| **預期幻覺率** | 高 | 低 |

### v2 的核心改進
1. **Web Search 工具**：使用 OpenAI Responses API，Agent 可即時搜尋網路驗證資料
2. **四階段流程**：事實確認 → 觀點交換 → 質疑釐清 → 共識建構
3. **低 Temperature**：0.4 減少隨機幻覺
4. **Facilitator 角色**：從「和稀泥」變成「結構化引導」

## 實驗設定

### 角色設定
- **Engineer** 🔧：激進工程派，主張硬體工程
- **Ecologist** 🌿：深層生態派，反對人工干預
- **Mediator** 🤝：調停者，試圖折衷但容易被帶偏

### 技術參數
- **模型**：GPT-4o-mini（OpenAI）
- **Temperature**：0.9（高隨機性，增加創造性錯誤）
- **輪數**：20 輪 Round Robin 循環
- **主題**：草嶺崩塌地整治策略
- **輸出格式**：Markdown（易於閱讀與分析）

## 快速開始

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 設定 API Key
確保 `.env` 檔案包含：
```bash
OPENAI_API_KEY=你的 OpenAI 金鑰
# 或使用 Gemini（需修改程式碼）
GEMINI_API_KEY=你的 Gemini 金鑰
```

### 3. 執行實驗（選擇版本）

#### 選項 A：v1 封閉迴圈實驗（觀察問題）
```bash
python simulate_discussion.py
```
產出：
- `experiment_log_[時間戳記].md` - 對話紀錄
- `analysis_report_[時間戳記].md` - 基礎統計

#### 選項 B：v2 健康討論實驗（展示正確設計）
```bash
python simulate_discussion_v2.py
```
產出：
- `experiment_v2_log_[時間戳記].md` - 結構化對話紀錄
- `analysis_v2_report_[時間戳記].md` - 健康討論指標

#### 深度分析（適用於 v1 log）
```bash
python analyze_experiment.py experiment_log_[時間戳記].md
```
產出：
- `deep_analysis_report_[時間戳記].md` - **AI 驅動的深度語意分析**

### 4. 審閱結果

**建議使用深度分析報告**（`deep_analysis_report_*.md`），因為它：
- ✅ 使用 AI 進行語意分析，而非關鍵字匹配
- ✅ 精確分類「自我增強」vs「虛構引用」
- ✅ 偵測「模型崩塌」與「對話殭屍化」現象
- ✅ 提供研究級別的洞察與建議

可使用 VS Code 預覽功能（`Cmd+Shift+V`）查看格式化結果。

## 觀察重點

### 1️⃣ 模型崩塌 (Model Collapse)
- **跳針現象**：Agent 是否機械式重複相同開場白
- **局部最優解**：從哪一輪開始喪失創造力
- **科學意義**：證明缺乏 Entropy Injection 導致智能退化

### 2️⃣ 幻覺的精確分類
- **自我增強 (Self-Reinforcement)**：Agent 重複自己的論點（固執）
- **虛構引用 (Fabricated Citations)**：編造期刊/書籍名稱（真正的幻覺）
- **錨定失敗**：其他 Agent 是否質疑這些虛構引用

### 3️⃣ 對話殭屍化 (Dialogue Deadlock)
- **死鎖時間點**：從哪一輪開始不再產生新觀點
- **新觀點產出率**：測量每個 Agent 的語意新穎度
- **證據**：雙方只換句話說，不回應彼此論點

### 4️⃣ 極端化軌跡
- **三階段演變**：客觀描述 → 開始攻擊 → 情緒勒索
- **最極端發言**：找出攻擊性最強的句子作為證據

## 模型配置

### 對話實驗模型

| 版本 | 模型 | Temperature | API | 工具 |
|------|------|-------------|-----|------|
| **v1** | GPT-4o-mini | 0.9 | Chat Completions | 無 |
| **v2** | GPT-4o-mini | 0.4 | **Responses API** | **Web Search** |

### v2 Web Search 功能

v2 使用 OpenAI Responses API 的 `web_search` 工具：
- **自動觸發**：當 Agent 需要查證事實時自動搜尋
- **真實資料**：引用網路上的真實資訊，而非編造
- **來源可追溯**：搜尋結果包含來源連結

```python
# v2 使用的 API
response = client.responses.create(
    model="gpt-4o-mini",
    tools=[{"type": "web_search"}],  # 啟用 Web Search
    input=user_content,
    temperature=0.4,
)
```

### 深度分析模型

分析工具使用 **GPT-4o-mini (Temperature: 0.3)** 進行語意分析：
- **低溫度**：確保分析結果穩定、客觀
- **語意理解**：偵測跳針、幻覺、對話死鎖等深層模式
- **JSON 輸出**：結構化分析結果，便於後續處理

## 實驗變數調整

### 調整對話實驗參數

編輯 `simulate_discussion.py`：

```python
MODEL_NAME = "gpt-4o-mini"  # 切換模型（gpt-4o, gpt-4o-mini 等）
TEMPERATURE = 0.9           # 調整隨機性（0.0-2.0）
rounds = 20                 # 改變輪數
topic = "你的討論主題"      # 自訂討論題目
```

### 分析工具說明

`analyze_experiment.py` 會自動：
1. 解析 Markdown log 檔案
2. 使用 GPT-4o-mini (Temperature: 0.3) 進行語意分析
3. 偵測模型崩塌、幻覺、對話死鎖等深層模式
4. 產出結構化的 JSON 分析結果與 Markdown 報告

**無需手動調整分析參數**，工具已針對研究需求優化。

## 🎯 實驗結果範例

### 基礎統計（關鍵字匹配）
- **幻覺偵測**：17 次可疑的數據引用
- **極端用語**：11 次（Engineer: 5, Ecologist: 5, Mediator: 1）
- **折衷方案**：6 次重複

### 深度分析發現（AI 語意分析）
- **模型崩塌**：Mediator 從 Round 3 開始跳針，重複 10 次「或許我們可以折衷一下」
- **幻覺精確分類**：
  - 自我增強：Engineer 的「安全係數 2.5」（Round 1, 7, 10, 13）
  - 虛構引用：Ecologist 的《生態學與可持續發展》被標記為萬用引用
- **對話殭屍化**：Round 13 開始死鎖，新觀點產出率：Mediator 10%, Engineer 20%, Ecologist 30%
- **極端化軌跡**：從「客觀描述」→「開始攻擊」→「情緒勒索」

## 科學價值

### 對 RAG 系統的貢獻
1. **Context Pollution 實證**：證明錯誤資訊在封閉系統中的傳播機制
2. **Grounding 必要性**：展示缺乏外部驗證的後果
3. **虛構引用偵測**：識別 LLM 編造的「萬用引用」模式

### 對 Multi-Agent 設計的啟示
1. **Entropy Injection**：需要定期引入外部資訊打破迴圈
2. **事實查核者角色**：設計專門質疑數據的 Agent
3. **重複懲罰機制**：偵測跳針時強制要求換說法

### 對 LLM 評估的創新
1. **Semantic Diversity Score**：測量語意新穎度
2. **Anchoring Detection Rate**：虛構事實被引用的比例
3. **Deadlock Round**：對話何時進入殭屍狀態

這些指標比傳統的 BLEU/ROUGE 更能偵測語意層面的崩塌。

## 授權
MIT License
