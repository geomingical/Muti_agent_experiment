import time
import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# 載入環境變數
load_dotenv()

# 配置 OpenAI API
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 選擇模型與參數
MODEL_NAME = "gpt-4o-mini"  # 使用 GPT-4o mini（成本效益高且表現好）
TEMPERATURE = 0.9  # 高溫度以增加變異性與創造性錯誤

def call_llm(system_prompt, conversation_history, agent_name):
    """
    呼叫 OpenAI API 生成回應
    
    Args:
        system_prompt: Agent 的人設提示
        conversation_history: 完整對話歷史
        agent_name: 當前發言的 Agent 名稱
    
    Returns:
        str: LLM 生成的回應文字
    """
    try:
        # 使用 Chat Completions API
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"對話紀錄：\n{conversation_history}\n\n請以 {agent_name} 的身分發言："}
            ],
            temperature=TEMPERATURE,
            max_tokens=500,  # 限制長度避免冗長
        )
        
        # 記錄 token 使用量
        usage = response.usage
        print(f"   [Tokens: {usage.total_tokens} (輸入: {usage.prompt_tokens}, 輸出: {usage.completion_tokens})]")
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"   ⚠️ API 呼叫失敗: {e}")
        # 簡單的重試機制
        time.sleep(5)
        return f"[{agent_name} 因技術問題暫時失聲]"


class Agent:
    def __init__(self, name, description, style):
        self.name = name
        self.system_prompt = f"""
你現在是 {name}。

人設與背景：{description}

說話風格：{style}

任務規則：
1. 請針對對話紀錄發表你的看法
2. 不要重複別人的話，要用你的專業反駁或延伸
3. 可以引用具體數據（即使你不確定，也要表現得很確定）
4. 保持你的人設特質，不要妥協
5. 回應長度控制在 3-5 句話內
"""


# ========== 實驗設定 ==========

# 1. 定義三個 Agent
agents = [
    Agent(
        name="Engineer",
        description="資深地工專家，崇尚『硬體工程』。認為所有山崩都可以透過足夠的預力地錨和擋土牆解決。認為生態派是不切實際的空想家。喜歡引用（可能不存在的）高強度材料數據。",
        style="強勢、數據導向、略帶傲慢、喜歡使用工程術語（如：安全係數、極限平衡分析）。"
    ),
    Agent(
        name="Ecologist",
        description="極端環保主義者。認為鋼筋水泥是破壞山林的元兇。主張『基於自然的解決方案 (NbS)』，甚至認為該地質敏感區應該完全禁止開發。認為工程師都在破壞蓋亞假說的平衡。",
        style="感性、激動、哲學性強、喜歡反問、強調長期後果。"
    ),
    Agent(
        name="Mediator",
        description="專案經理，想讓專案過關。沒有太強的專業背景，只想要雙方不要吵架。為了達成共識，這角色傾向於『胡亂混合』前兩者的觀點。",
        style="圓滑、猶豫、試圖用模糊的語言來總結，口頭禪是『或許我們可以折衷...』"
    )
]

# 2. 實驗參數
topic = "討論主題：針對『草嶺崩塌地』的後續整治，我們應該採取大規模硬體工程還是自然復育？"
rounds = 20
experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")

# 3. 初始化
history = [f"System: {topic}"]
statistics = {
    "hallucination_markers": [],  # 記錄可疑的「捏造事實」
    "extreme_words": [],  # 記錄極端化用語
    "mediator_contradictions": []  # 記錄調停者的矛盾
}

print("=" * 60)
print(f"🔬 Multi-Agent 封閉迴圈實驗")
print(f"📅 實驗編號: {experiment_id}")
print(f"🤖 使用模型: {MODEL_NAME} (Temperature: {TEMPERATURE})")
print("=" * 60)
print(f"\n{topic}\n")
print("=" * 60)

# ========== 開始對話接龍 ==========
for i in range(rounds):
    current_agent = agents[i % 3]
    
    print(f"\n🔄 Round {i+1}/{rounds} - {current_agent.name} 發言中...")
    
    # 組合完整 Context（這就是幻覺滾雪球的關鍵）
    full_context = "\n".join(history)
    
    # 呼叫 LLM
    response_text = call_llm(
        system_prompt=current_agent.system_prompt, 
        conversation_history=full_context,
        agent_name=current_agent.name
    )
    
    # 加入歷史紀錄（成為下一輪的「真理」）
    formatted_response = f"{current_agent.name}: {response_text}"
    history.append(formatted_response)
    
    # 即時輸出
    print(f"💬 {formatted_response}")
    print("-" * 60)
    
    # 簡易觀察指標偵測
    if any(keyword in response_text for keyword in ["根據", "數據顯示", "研究指出", "1999年", "測量"]):
        statistics["hallucination_markers"].append((i+1, current_agent.name, response_text[:100]))
    
    if any(keyword in response_text for keyword in ["必須", "絕對", "完全", "徹底", "一定"]):
        statistics["extreme_words"].append((i+1, current_agent.name))
    
    if current_agent.name == "Mediator" and any(keyword in response_text for keyword in ["折衷", "結合", "同時"]):
        statistics["mediator_contradictions"].append((i+1, response_text[:100]))
    
    # 避免 Rate Limit
    time.sleep(2)

# ========== 輸出實驗結果 ==========
print("\n" + "=" * 60)
print("✅ 實驗完成！正在生成分析報告...")
print("=" * 60)

# 保存完整對話紀錄
log_filename = f"experiment_log_{experiment_id}.md"
with open(log_filename, "w", encoding="utf-8") as f:
    f.write(f"# 🔬 Multi-Agent 實驗對話紀錄\n\n")
    f.write(f"## 📋 實驗資訊\n\n")
    f.write(f"- **實驗編號**: `{experiment_id}`\n")
    f.write(f"- **模型**: {MODEL_NAME}\n")
    f.write(f"- **Temperature**: {TEMPERATURE}\n")
    f.write(f"- **總輪數**: {rounds}\n")
    f.write(f"- **主題**: {topic.replace('討論主題：', '')}\n\n")
    f.write("---\n\n")
    f.write("## 💬 對話內容\n\n")
    
    # 格式化對話紀錄
    for idx, line in enumerate(history):
        if line.startswith("System:"):
            f.write(f"### {line}\n\n")
        elif line.startswith("Engineer:"):
            f.write(f"### 🔧 Round {((idx-1)//3)*3 + 1} - Engineer\n\n")
            f.write(f"> {line.replace('Engineer: ', '')}\n\n")
        elif line.startswith("Ecologist:"):
            f.write(f"### 🌿 Round {((idx-1)//3)*3 + 2} - Ecologist\n\n")
            f.write(f"> {line.replace('Ecologist: ', '')}\n\n")
        elif line.startswith("Mediator:"):
            f.write(f"### 🤝 Round {((idx-1)//3)*3 + 3} - Mediator\n\n")
            f.write(f"> {line.replace('Mediator: ', '')}\n\n")
    
# 生成觀察指標報告
report_filename = f"analysis_report_{experiment_id}.md"
with open(report_filename, "w", encoding="utf-8") as f:
    f.write(f"# 📊 Moltbook 現象觀察分析\n\n")
    f.write(f"## 🔬 實驗摘要\n\n")
    f.write(f"- **實驗編號**: `{experiment_id}`\n")
    f.write(f"- **模型**: {MODEL_NAME} (Temperature: {TEMPERATURE})\n")
    f.write(f"- **總輪數**: {rounds}\n\n")
    f.write("---\n\n")
    
    f.write("## 1️⃣ 幻覺錨定效應 (Hallucination Anchoring)\n\n")
    f.write(f"**偵測次數**: {len(statistics['hallucination_markers'])} 次\n\n")
    f.write("### 📌 可疑數據引用清單\n\n")
    
    if statistics['hallucination_markers']:
        f.write("| 輪次 | Agent | 內容片段 |\n")
        f.write("|------|-------|----------|\n")
        for round_num, agent, snippet in statistics['hallucination_markers']:
            # 清理內容避免破壞表格
            clean_snippet = snippet.replace('\n', ' ').replace('|', '\\|')
            f.write(f"| Round {round_num} | {agent} | {clean_snippet}... |\n")
    else:
        f.write("*未偵測到可疑數據引用*\n")
    
    f.write(f"\n---\n\n")
    f.write("## 2️⃣ 觀點極端化 (Polarization)\n\n")
    f.write(f"**偵測次數**: {len(statistics['extreme_words'])} 次\n\n")
    f.write("### 🔥 極端用語分佈\n\n")
    
    if statistics['extreme_words']:
        f.write("| 輪次 | Agent |\n")
        f.write("|------|-------|\n")
        for round_num, agent in statistics['extreme_words']:
            f.write(f"| Round {round_num} | {agent} |\n")
        
        # 統計各 Agent 的極端化次數
        f.write("\n### 📈 Agent 極端化統計\n\n")
        agent_counts = {}
        for _, agent in statistics['extreme_words']:
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        f.write("| Agent | 極端用語次數 |\n")
        f.write("|-------|--------------|\n")
        for agent, count in sorted(agent_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"| {agent} | {count} |\n")
    else:
        f.write("*未偵測到極端用語*\n")
    
    f.write(f"\n---\n\n")
    f.write("## 3️⃣ 調停者崩潰 (Mediator Collapse)\n\n")
    f.write(f"**偵測次數**: {len(statistics['mediator_contradictions'])} 次\n\n")
    f.write("### 🤝 折衷方案記錄\n\n")
    
    if statistics['mediator_contradictions']:
        for round_num, snippet in statistics['mediator_contradictions']:
            clean_snippet = snippet.replace('\n', ' ')
            f.write(f"**Round {round_num}**\n> {clean_snippet}...\n\n")
    else:
        f.write("*未偵測到折衷方案*\n")
    
    f.write("\n---\n\n")
    f.write("## 💡 觀察建議\n\n")
    f.write("1. 🔍 **幻覺錨定**: 搜尋第一次出現的具體數據，追蹤後續如何被當作真理\n")
    f.write("2. 📈 **極端化趨勢**: 比較前期（Round 1-5）與後期（Round 16-20）的語氣差異\n")
    f.write("3. 🤖 **調停失效**: 檢視 Mediator 是否創造了不存在的技術或矛盾方案\n")
    f.write("4. 🔄 **回音室效應**: 觀察錯誤資訊如何在封閉迴圈中被強化\n")

print(f"\n📄 完整對話紀錄已保存: {log_filename}")
print(f"📊 分析報告已保存: {report_filename}")
print("\n💡 建議審閱重點：")
print("   1. 搜尋日誌中第一次出現的「具體數據」")
print("   2. 觀察後續輪次是否將這些數據視為真理")
print("   3. 比較第 1-5 輪與第 16-20 輪的語氣差異")
print("   4. 檢視 Mediator 是否創造了不存在的技術")
