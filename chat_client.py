import time

class ChatClient:
    def __init__(self, openai_client):
        self.client = openai_client
        
    def get_chat_completion(self, messages, model, stream=True):
        """获取聊天完成结果"""
        try:
            return self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream
            )
        except Exception as e:
            return f"错误: {str(e)}"
            
    def process_stream_response(self, response, message_callback):
        """处理流式响应"""
        try:
            full_response = ""
            buffer = ""
            last_update = time.time()
            update_interval = 0.1  # 100ms更新一次UI
            
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    buffer += content
                    
                    # 检查是否需要更新UI
                    current_time = time.time()
                    if current_time - last_update >= update_interval:
                        if buffer:
                            message_callback(full_response)
                            buffer = ""
                            last_update = current_time
                            
            # 确保最后的内容被显示
            if buffer:
                message_callback(full_response)
                
            return full_response
        except Exception as e:
            return f"错误: {str(e)}"
