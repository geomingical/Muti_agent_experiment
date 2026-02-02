"""
===============================================================================
Multi-Agent 實驗 v2.3 - 分層驗證與交叉質詢版
===============================================================================

v2.3 核心改進（基於 v2.2）：
1. **分層驗證規則** - 明確哪些資訊需要 Web Search，哪些可用常識
2. **強制標記來源** - 引用數據必須標記：✅確認（已搜尋）、⚠️推估（基於經驗）、❓待查
3. **交叉質詢機制** - 質疑階段要求 agents 質疑對方「未查證」的數據
4. **Facilitator 詢問權** - 可溫和要求專家補充查證關鍵數據
5. **保留 v2.2 優點** - 多樣性、立場分明、階段導向、辯論張力

【改進目標】
- 預期 Web Search 從 1 次提升到 4-6 次
- 減少「隱性幻覺」（未查證但引用具體數據）
- 維持對話流暢度（不過度嚴格）
"""

import time
import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

MODEL_NAME = "gpt-4o-mini"
TEMPERATURE = 0.5  # 稍提高增加多樣性

# ========== 追蹤已討論內容（避免重複的關鍵）==========
discussed_points = []  # 已討論的重點


def call_llm(system_prompt, conversation_history, agent_name, phase_instruction="", round_num=1):
    """呼叫 OpenAI Responses API（含 Web Search）"""
    try:
        # 組合「已討論內容」提醒（避免重複的關鍵）
        already_discussed = ""
        if discussed_points and round_num > 1:  # 從 Round 2 開始就要檢查
            already_discussed = "\n\n【🚫 禁止重複 - 以下內容已討論，你必須提出「完全不同」的新觀點】\n"
            for point in discussed_points[-8:]:
                already_discussed += f"  ❌ 已說過：{point}\n"
            already_discussed += "\n⚠️ 如果你重複上述任何內容，你的發言將被視為無效！"
        
        user_content = f"""{system_prompt}
{already_discussed}
===== 對話紀錄（最近幾輪）=====
{conversation_history}

【當前階段指令】
{phase_instruction}

請以 {agent_name} 的身分發言。
⚠️ 重要：你必須提出「尚未討論過」的新資訊或新觀點！
⚠️ 不要複述前面已經說過的內容！
⚠️ 回應長度控制在 3-6 句話。
"""
        
        response = client.responses.create(
            model=MODEL_NAME,
            tools=[{"type": "web_search"}],
            input=user_content,
            temperature=TEMPERATURE,
        )
        
        used_web_search = False
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                if hasattr(item, 'type') and item.type == 'web_search_call':
                    used_web_search = True
                    break
        
        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            search_indicator = " 🔍" if used_web_search else ""
            print(f"   [Tokens: {usage.total_tokens}]{search_indicator}")
        
        return response.output_text.strip(), used_web_search
    
    except Exception as e:
        print(f"   ⚠️ API 呼叫失敗: {e}")
        time.sleep(5)
        return f"[{agent_name} 因技術問題暫時失聲]", False


# ========== Agent 定義（有明確立場差異）==========

AGENT_CONFIGS = [
    {
        "name": "Engineer",
        "system_prompt": """你是一位資深大地工程師，有 20 年邊坡災害治理經驗。

【你的立場】
你傾向支持「硬體工程」方案（擋土牆、地錨、排水系統等）。
原因：效果可量化、見效快、安全係數可控。
你對自然復育的態度保守，認為植被效果太慢、難以量化。

【搜尋方向】
- 擋土牆/地錨的成本、壽命、成功案例
- 類似崩塌地的工程治理經驗
- 工程失敗案例（展現你的專業反思）

【發言原則】
1. 從工程角度提供專業見解
2. 搜尋具體數據支持你的觀點
3. 可以對生態學家的觀點提出技術質疑
4. 長度：3-6 句
5. ⚠️ 絕對不要重複前面說過的內容！

【分層驗證規則】⚠️ 重要
✅ 需要 Web Search 的情況：
   - 具體數字（成本、百分比、時間）
   - 特定案例（地名、年份、結果）
   - 最新法規或技術標準
❌ 不需要 Web Search 的情況：
   - 通用工程原理（例如「排水可降低土壤水壓」）
   - 方法論描述（例如「地錨原理是...」）

⚠️ 如果引用具體數據或案例，請確保：
1. 已透過 Web Search 查證 → 標記 ✅確認
2. 或明確標記為 ⚠️推估（基於經驗）
3. 或標記為 ❓待查（需要進一步確認）

【標記】✅確認 ⚠️推估 ❓待查"""
    },
    {
        "name": "Ecologist",
        "system_prompt": """你是一位生態學博士，專長崩塌地生態復育與 NbS（基於自然的解決方案）。

【你的立場】
你傾向支持「自然復育」與「生態工法」。
原因：長期永續、成本較低、生態效益高。
你對硬體工程的態度審慎，認為可能破壞生態、維護成本高。

【搜尋方向】
- 崩塌地自然復育的成功案例
- 植被恢復率、土壤穩定效果的研究
- 生態工法 vs 傳統工程的比較研究
- NbS 國際案例

【發言原則】
1. 從生態角度提供專業見解
2. 搜尋具體案例或數據支持觀點
3. 可以對工程師的觀點提出生態質疑
4. 長度：3-6 句
5. ⚠️ 絕對不要重複前面說過的內容！

【分層驗證規則】⚠️ 重要
✅ 需要 Web Search 的情況：
   - 具體數字（復育率、成本、時間）
   - 特定案例（地點、植被種類、成效）
   - 最新研究數據（論文、報告）
❌ 不需要 Web Search 的情況：
   - 生態學基本原理（例如「植被可穩定土壤」）
   - 方法論描述（例如「NbS 是基於自然的解決方案」）

⚠️ 如果引用具體數據或案例，請確保：
1. 已透過 Web Search 查證 → 標記 ✅確認
2. 或明確標記為 ⚠️推估（基於研究經驗）
3. 或標記為 ❓待查（需要進一步確認）

【標記】✅確認 ⚠️推估 ❓待查"""
    },
    {
        "name": "Facilitator",
        "system_prompt": """你是討論引導師，負責推進討論並確保有結論。

【你的角色】
1. 不表達自己的技術立場
2. 整理雙方觀點的「差異」與「共識」
3. 提出問題引導討論深入
4. 在後期協助建構可行方案

【發言結構】
- Round 3, 6: 列出「已確認事實」與「待確認問題」
- Round 9, 12: 整理「工程派 vs 生態派」的論點對比
- Round 15: 列出「尚未解決的關鍵分歧」
- Round 18, 20: 歸納共識與下一步建議

【重要原則】
1. 用條列式整理，清晰簡潔
2. 不主動搜尋（讓專家搜尋）
3. 不要重複別人的話，只做「結構化整理」
4. 長度適中，重點突出

【詢問權】⚠️ v2.3 新增
如果你發現專家提出具體數據但未標記來源，你可以：
1. 溫和指出：「請問這個數據是查證過的嗎？」
2. 要求補充：「能否提供資料來源或標記為推估？」
3. 建議查證：「建議搜尋確認這個關鍵數據」

⚠️ 不要過度質疑，只針對「關鍵數據」或「重要案例」
⚠️ 質疑後由專家決定是否搜尋，你不強制要求"""
    }
]


# ========== 階段設計（每階段有明確不同的核心問題）==========

DISCUSSION_PHASES = [
    {
        "name": "事實確認階段",
        "rounds": 6,
        "instruction": """【階段一：事實確認】

本階段目標：搜尋並確認草嶺崩塌地的基本事實。

Engineer 請搜尋：崩塌規模、地質條件、過去的工程處理
Ecologist 請搜尋：當地生態現況、植被類型、復育潛力
Facilitator 請整理：已確認 vs 待確認事項

⚠️ 每人負責不同面向，不要重複彼此的搜尋內容！"""
    },
    {
        "name": "方案辯論階段",
        "rounds": 6,
        "instruction": """【階段二：方案辯論】

本階段目標：各自提出支持自己立場的論據。

Engineer 請提出：支持硬體工程的證據（案例、數據、優點）
Ecologist 請提出：支持自然復育的證據（案例、數據、優點）
Facilitator 請整理：雙方論點的差異

⚠️ 這是辯論階段，請勇於表達不同意見！
⚠️ 不要太快妥協，充分展現專業立場！"""
    },
    {
        "name": "質疑回應階段",
        "rounds": 4,
        "instruction": """【階段三：質疑與回應】⚠️ v2.3 強化交叉驗證

本階段目標：針對對方觀點提出具體質疑，並要求提供證據。

Engineer 請質疑：
- 自然復育的效果、時效性、可靠性
- ⚠️ 特別注意：對方提出的具體數據（例如復育率、成功案例）是否有搜尋查證？如果沒有，請要求提供來源或搜尋確認。

Ecologist 請質疑：
- 硬體工程的生態破壞、維護成本、長期風險
- ⚠️ 特別注意：對方提出的具體數據（例如工程成本、壽命、案例）是否有搜尋查證？如果沒有，請要求提供來源或搜尋確認。

Facilitator 請整理：
- 雙方的核心分歧
- ⚠️ 如果發現有未查證的關鍵數據，請溫和提醒需要查證

⚠️ 請提出尖銳但專業的問題！
⚠️ 不必客氣，這是學術辯論！
⚠️ 如果對方引用具體數據但未查證，請明確要求：「這個數據能否搜尋確認？」"""
    },
    {
        "name": "共識建構階段",
        "rounds": 4,
        "instruction": """【階段四：共識建構】

本階段目標：尋找整合方案。

討論重點：
1. 短期安全 vs 長期永續如何平衡？
2. 高風險區 vs 低風險區可否分別處理？
3. 需要哪些額外調查才能決策？
4. 具體的下一步行動是什麼？

⚠️ 請提出具體可行的建議，不要空泛結論！"""
    }
]


def extract_key_point(text):
    """從回應中提取關鍵點（用於追蹤已討論內容）"""
    # 簡化版：取前60字作為摘要
    summary = text[:60].replace("\n", " ").strip()
    if len(text) > 60:
        summary += "..."
    return summary


# ========== 主程式 ==========

topic = "草嶺崩塌地的後續整治，應採取大規模硬體工程還是自然復育？"
total_rounds = 20
experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")

history = [f"System: 討論主題：{topic}"]
statistics = {
    "web_searches": [],
    "disagreements": [],
    "questions": []
}

print("=" * 70)
print(f"🔬 Multi-Agent 實驗 v2.2 - 多樣性增強版")
print("=" * 70)
print(f"📅 實驗編號: {experiment_id}")
print(f"🤖 模型: {MODEL_NAME} (Temperature: {TEMPERATURE})")
print(f"🔍 工具: Web Search enabled")
print("=" * 70)
print(f"\n主題：{topic}\n")
print("=" * 70)

# ========== 開始對話 ==========
current_phase_name = ""
agents = AGENT_CONFIGS

for i in range(total_rounds):
    current_agent = agents[i % 3]
    round_num = i + 1
    
    # 取得當前階段
    accumulated = 0
    current_phase = DISCUSSION_PHASES[-1]
    for phase in DISCUSSION_PHASES:
        accumulated += phase["rounds"]
        if round_num <= accumulated:
            current_phase = phase
            break
    
    # 階段轉換提示
    if current_phase["name"] != current_phase_name:
        current_phase_name = current_phase["name"]
        print(f"\n{'='*70}")
        print(f"📍 進入【{current_phase_name}】")
        print(f"{'='*70}")
    
    print(f"\n🔄 Round {round_num}/20 - {current_agent['name']} 發言中...")
    
    # 只保留最近 8 輪對話（避免 context 太長）
    recent_history = history[-8:] if len(history) > 8 else history
    full_context = "\n".join(recent_history)
    
    response_text, used_search = call_llm(
        system_prompt=current_agent["system_prompt"],
        conversation_history=full_context,
        agent_name=current_agent["name"],
        phase_instruction=current_phase["instruction"],
        round_num=round_num
    )
    
    # 記錄統計
    if used_search:
        statistics["web_searches"].append((round_num, current_agent["name"]))
    
    # 偵測不同意/質疑
    disagreement_keywords = ["但是", "然而", "不同意", "質疑", "問題是", "忽略了", "不認為", "擔心", "風險"]
    if any(word in response_text for word in disagreement_keywords):
        statistics["disagreements"].append((round_num, current_agent["name"]))
    
    # 偵測問題
    if "？" in response_text or "?" in response_text:
        statistics["questions"].append((round_num, current_agent["name"]))
    
    # 更新已討論清單（關鍵：避免後續重複）
    key_point = extract_key_point(response_text)
    if key_point and key_point not in discussed_points:
        discussed_points.append(key_point)
    
    # 加入歷史
    formatted_response = f"{current_agent['name']}: {response_text}"
    history.append(formatted_response)
    
    print(f"💬 {formatted_response}")
    print("-" * 70)
    
    time.sleep(2)

# ========== 輸出結果 ==========
print("\n" + "=" * 70)
print("✅ v2.2 實驗完成！")
print("=" * 70)

# 保存對話紀錄
log_filename = f"experiment_v2_log_{experiment_id}.md"
with open(log_filename, "w", encoding="utf-8") as f:
    f.write(f"# 🔬 Multi-Agent 實驗 v2.2 對話紀錄\n\n")
    f.write(f"## 📋 實驗資訊\n\n")
    f.write(f"- **版本**: v2.2 (多樣性增強版)\n")
    f.write(f"- **實驗編號**: `{experiment_id}`\n")
    f.write(f"- **模型**: {MODEL_NAME} (Temperature: {TEMPERATURE})\n")
    f.write(f"- **總輪數**: {total_rounds}\n")
    f.write(f"- **Web Search 次數**: {len(statistics['web_searches'])}\n")
    f.write(f"- **質疑/不同意次數**: {len(statistics['disagreements'])}\n")
    f.write(f"- **提問次數**: {len(statistics['questions'])}\n\n")
    
    f.write("### v2.2 設計重點\n\n")
    f.write("1. **角色立場分明** - Engineer 偏工程派，Ecologist 偏生態派\n")
    f.write("2. **動態避免重複** - 每輪注入「已討論清單」提醒\n")
    f.write("3. **階段問題導向** - 每階段有明確不同的討論焦點\n")
    f.write("4. **鼓勵辯論** - 質疑階段明確要求提出不同意見\n")
    f.write("5. **Web Search** - 即時查證，不預設答案\n\n")
    
    f.write("---\n\n## 💬 對話內容\n\n")
    
    current_phase = ""
    round_counter = 0
    
    for line in history:
        if line.startswith("System:"):
            f.write(f"### 📌 {line}\n\n")
        else:
            round_counter += 1
            
            accumulated = 0
            for phase in DISCUSSION_PHASES:
                accumulated += phase["rounds"]
                if round_counter <= accumulated:
                    if phase["name"] != current_phase:
                        current_phase = phase["name"]
                        f.write(f"\n---\n\n## 📍 {current_phase}\n\n")
                    break
            
            agent_name = line.split(":")[0]
            content = line.split(":", 1)[1].strip() if ":" in line else line
            
            emoji = {"Engineer": "🔧", "Ecologist": "🌿", "Facilitator": "🎯"}.get(agent_name, "💬")
            f.write(f"### {emoji} Round {round_counter} - {agent_name}\n\n")
            f.write(f"> {content}\n\n")

# 分析報告
report_filename = f"analysis_v2_report_{experiment_id}.md"
with open(report_filename, "w", encoding="utf-8") as f:
    f.write(f"# 📊 v2.2 實驗分析報告\n\n")
    f.write(f"## 統計摘要\n\n")
    f.write(f"| 指標 | 數值 |\n")
    f.write(f"|------|------|\n")
    f.write(f"| Web Search 次數 | {len(statistics['web_searches'])} |\n")
    f.write(f"| 質疑/不同意 | {len(statistics['disagreements'])} |\n")
    f.write(f"| 提問次數 | {len(statistics['questions'])} |\n\n")
    
    f.write("## Web Search 使用記錄\n\n")
    if statistics["web_searches"]:
        for round_num, agent in statistics["web_searches"]:
            f.write(f"- Round {round_num}: {agent} 🔍\n")
    else:
        f.write("- 無搜尋記錄\n")
    
    f.write("\n## 質疑/辯論記錄\n\n")
    if statistics["disagreements"]:
        for round_num, agent in statistics["disagreements"]:
            f.write(f"- Round {round_num}: {agent} 提出不同意見\n")
    else:
        f.write("- 無質疑記錄\n")

print(f"\n📄 對話紀錄: {log_filename}")
print(f"📊 分析報告: {report_filename}")
print(f"\n🔍 Web Search: {len(statistics['web_searches'])} 次")
print(f"⚔️ 質疑/辯論: {len(statistics['disagreements'])} 次")
print(f"❓ 提問: {len(statistics['questions'])} 次")
