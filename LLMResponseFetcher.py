from openai import OpenAI
import json
import promptMaker

def steamingResponse(prompt):
    thinkingStart=True
    thinkingEnd=True
    reasoningContent=""
    responseContent=""
    try:
        with open('setting.json', 'r', encoding='utf-8') as setting:
                settings = json.load(setting)
                api_key = settings["LLMsApiKey"]
                base_url = settings["LLMsUrl"]
                model = settings["LLMsModel"]
        client = OpenAI(api_key=api_key, base_url=base_url)


        messages = [{"role": "user", "content": f"{prompt}"}]
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )
    
        for chunk in response:
            try:
                if thinkingStart:
                    print("<thinking>")
                    thinkingStart=False
                reasoning_content=chunk.choices[0].delta.reasoning_content
                if reasoning_content:
                    print(reasoning_content,end='', flush=True)
                    reasoningContent=reasoningContent+reasoning_content
            except:
                if thinkingEnd:
                    print("\n</thinking>")
                    thinkingEnd=False
                content=chunk.choices[0].delta.content
                if content:
                    print(content, end='',flush=True)
                    responseContent=responseContent+content
        return True,reasoningContent,responseContent
    except:
        return False,reasoningContent,responseContent

def response(prompt):
    reasoningContent=""
    responseContent=""
    try:
        with open('setting.json', 'r', encoding='utf-8') as setting:
                settings = json.load(setting)
                api_key = settings["LLMsApiKey"]
                base_url = settings["LLMsUrl"]
        client = OpenAI(api_key=api_key, base_url=base_url)


        messages = [{"role": "user", "content": f"{prompt}"}]
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=messages,
        )
        reasoningContent=response.choices[0].message.reasoning_content
        responseContent=response.choices[0].message.content

        # 去除前后的 ```json 和 ``` 标记
        start_index = responseContent.find('{')
        end_index = responseContent.rfind('}') + 1
        json_str = responseContent[start_index:end_index]

        # 解析 JSON 字符串
        responseContent = json.loads(json_str)


        return True,reasoningContent,responseContent
    except:
        return False,reasoningContent,responseContent




def get(data,method='getMessageReply',steaming=False):
    prompt=promptMaker.getPrompt(data,method)
    if steaming:
        return steamingResponse(prompt)
    else:
        return response(prompt)
    
        


if __name__ == '__main__':
    data =["王雷潇","可是我更想去重庆"]
    promptMaker.getPrompt(data,'getMessageReply')

    """
    state,reasoningContent,content=get("3.11和3.9哪个大？")
    if state:
        print("\n<thinking>")
        print(reasoningContent)
        print("\n</thinking>")
        print(content)
    else:
        print("\n模型调用错误")
    """
    