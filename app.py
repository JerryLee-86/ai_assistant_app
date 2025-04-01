import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI # 仍然使用 OpenAI 庫連接兼容接口
import traceback
import re # 引入正則表達式庫，方便解析

# --- 1. 載入環境變數 ---
load_dotenv()
xai_api_key = os.getenv("XAI_API_KEY")

if not xai_api_key:
    st.error("❌ XAI_API_KEY 未在 .env 檔案中找到或設定。請檢查你的 .env 檔案。")
    st.stop()

# --- 2. 初始化 API Client ---
try:
    client = OpenAI(
        api_key=xai_api_key,
        base_url="https://api.x.ai/v1",
    )
except Exception as e:
    st.error(f"❌ 初始化 xAI Client 時發生錯誤：{e}")
    st.stop()

# --- 3. (移除) Function Calling Schema 不再需要 ---

# --- 4. Streamlit UI 介面 ---
st.set_page_config(page_title="AI 回應智慧助理", page_icon="🤖")
st.title("🤖 AI 回應智慧助理")
st.caption("由 xAI Grok 強力驅動")

st.write("將其他 AI 的回應貼在下方文本框中，點擊按鈕，Grok 將為你智能分析！")

user_input = st.text_area("貼上 AI 回應文本：", height=350, placeholder="在這裡貼上你想分析的文本...")

# --- 5. 按鈕觸發與 API 調用 (修改後) ---
if st.button("🧠 開始分析", type="primary"):
    if user_input:
        with st.spinner("🚀 Grok 正在高速分析中，請稍候..."):
            try:
                # === 修改 System Prompt ===
                system_prompt = """
你是一個專注於分析文本的助手。請仔細閱讀使用者提供的文本，然後按照以下格式輸出你的分析結果：

### 關鍵資訊
- [提取到的第一個關鍵資訊]
- [提取到的第二個關鍵資訊]
...

### 可行動項目
- [識別到的第一個行動項目]
- [識別到的第二個行動項目]
...

### 核心摘要
[這裡是你對整個文本生成的簡潔摘要]

請確保嚴格遵循這個 Markdown 格式，使用 '###' 作為標題，並用 '-' 作為列表項。如果某個部分沒有內容，請在標題下保留空白或寫 "無"。
"""

                response = client.chat.completions.create(
                    # === 修改模型名稱 ===
                    model="grok-beta", # 或者你確認可用的模型
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    # === (移除 tools/tool_choice) ===
                    # === (可選) 添加其他參數 ===
                    temperature=0.7, # 可以調整溫度以獲得不同程度的創意性/一致性
                    # realtime_search=True, # 如果需要即時資訊，取消註解此行
                    stream=False # 確保不是流式輸出
                )

                # --- 6. 處理 API 回應 (修改後) ---
                message = response.choices[0].message
                grok_response_content = message.content

                if grok_response_content:
                    st.success("✅ Grok 分析完成！")
                    st.markdown("---") # 分隔線

                    # --- 7. 解析 Grok 的 Markdown 回應 ---
                    # 使用正則表達式或字串分割來提取各部分
                    key_info_match = re.search(r"### 關鍵資訊\s*\n(.*?)(?=\n###|\Z)", grok_response_content, re.DOTALL | re.IGNORECASE)
                    action_items_match = re.search(r"### 可行動項目\s*\n(.*?)(?=\n###|\Z)", grok_response_content, re.DOTALL | re.IGNORECASE)
                    summary_match = re.search(r"### 核心摘要\s*\n(.*?)(?=\n###|\Z)", grok_response_content, re.DOTALL | re.IGNORECASE)

                    st.subheader("🔑 關鍵資訊", divider='rainbow')
                    if key_info_match and key_info_match.group(1).strip():
                        # 提取列表項
                        items = [item.strip('- ').strip() for item in key_info_match.group(1).strip().split('\n') if item.strip()]
                        if items:
                            for item in items:
                                st.markdown(f"- {item}")
                        else:
                             st.info("未提取到明確的關鍵資訊 (格式可能不符)。")
                    else:
                        st.info("Grok 回應中未找到 '### 關鍵資訊' 部分或該部分為空。")

                    st.subheader("✅ 可行動項目", divider='rainbow')
                    if action_items_match and action_items_match.group(1).strip():
                         items = [item.strip('- ').strip() for item in action_items_match.group(1).strip().split('\n') if item.strip()]
                         if items:
                             for item in items:
                                 st.markdown(f"- {item}")
                         else:
                             st.info("未識別到明確的可行動項目 (格式可能不符)。")
                    else:
                        st.info("Grok 回應中未找到 '### 可行動項目' 部分或該部分為空。")

                    st.subheader("📝 核心摘要", divider='rainbow')
                    if summary_match and summary_match.group(1).strip():
                        st.success(summary_match.group(1).strip())
                    else:
                        st.info("Grok 回應中未找到 '### 核心摘要' 部分或該部分為空。")

                    # (可選) 顯示原始回應方便除錯
                    with st.expander("👀 查看 Grok 原始回應"):
                        st.text(grok_response_content)

                else:
                     st.warning("⚠️ Grok 返回了空的回應。")

            except Exception as e:
                # --- 8. 錯誤處理 ---
                st.error(f"❌ 呼叫或處理 xAI Grok API 時發生錯誤：")
                st.code(f"{type(e).__name__}: {e}\n{traceback.format_exc()}")

    else:
        st.warning("⚠️ 請先在上面的文本框中貼上需要分析的 AI 回應。")

st.markdown("---")
st.caption("提示：Grok 的分析結果依賴於其對輸入文本和指令的理解。")