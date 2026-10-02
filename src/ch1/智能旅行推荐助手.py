import requests
import os
import re
from tavily import TavilyClient # 导入Tavily Search API客户端,他是一个供ai调用的搜索工具接口，请在tavily.com注册一个账号，并获取API密钥再后环境变量中配置TAVILY_API_KEY
from openai import OpenAI

class OpenAICompatibleClient:
    """
    这是一个兼容OpenAI API的LLM客户端类，用于与OpenAI模型进行交互。
    """
    def __init__(self, api_key: str, model: str, base_url: str):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def generate(self, prompt: str, system_prompt: str = None):
        """
        promt: 用户输入的提示词
        system_prompt: 系统提示词，用于设置模型的行为和风格
        """
        if not prompt:
            return "错误：提示词不能为空"
        print("正在调用LLM模型：", self.model)
        if system_prompt:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        else:
            messages = [
                {"role": "user", "content": prompt}
            ]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            print("LLM模型响应:", response)
            print("==========================================="*2)
            return response.choices[0].message.content
        except Exception as e:
            print("调用LLM模型时出错，错误信息:", e)
            return "错误：调用LLM模型时出错，错误信息"

def get_attraction(city:str,weather:str) -> str:
    """
    根据城市和天气条件，使用TavilySearch API在互联网上搜索并推荐合适的旅游景点
    """
    key = os.environ.get("TAVILY_API_KEY") # 可以将 API_KEY 放到 .env 文件中， 然后在 .vscode/settings.json 中配置环境变量文件加载
    if not key:
        return "错误：未找到TAVILY_API_KEY环境变量，请在tavily.com注册账号并获取API密钥。"
# 2. 初始化Tavily客户端
    tavily = TavilyClient(api_key=key)

    # 3.构造一个精确的搜索查询，结合城市和天气条件
    query = f"{city}'在' {weather}'天气下的旅游景点推荐及理由"
    # 长沙在Patchy rain nearby， 气温31摄氏度， 湿度60%， 风速2.5m/s
    try:
        # 4.调用Tavily API,include_answers=True表示返回答案，include_reasons=True表示返回理由
        response = tavily.search(query,search_depth="advanced", include_answers=True)
        if response.get("answer"):
            return response["answer"]
    # 如果没有找到答案，则返回搜索结果的摘要
        formatted_result = []
        for result in response.get("results", []):
            formatted_result.append(f"- {result['title']}: {result['content']}")
        if not formatted_result:
            return "没有找到相关旅游景点推荐。"
            # "\n".join(formatted_result)将列表中的每个元素用换行符连接成一个字符串
            # 标题：内容\n
        return "根据搜索结果，推荐以下旅游景点：\n" + "\n".join(formatted_result)
    except Exception as e:
        return f"错误：调用Tavily API时出错，错误信息：{e}"

def get_weather(city:str) -> str:
    """
    通过调用wttr。in API查询真实的天气信息
    API格式：https://wttr.in/{city}?format=json
    """

    url=f"https://wttr.in/{city}?format=j1"

    try:
        # 发起网络请求
        response = requests.get(url)
        # 检查响应状态码是否正常
        response.raise_for_status()
        # 解析JSON响应
        weather_data = response.json()
        print("得到的天气数据:",weather_data)
        print("==========================================="*2)#*2表示重复打印2次
        # 从JSON数据中提取天气信息
        # weather_desc = weather_data['current_condition'][0]["weatherDesc"][0]["value"]
        # return f"{city}的天气是{weather_desc}"

        # 提取当天的天气信息
        current_weather = weather_data['current_condition'][0]
        weather_desc = current_weather['weatherDesc'][0]['value']
        temp_c = current_weather['temp_C']

        # 返回格式化后的天气信息
        return f"{city}的天气是{weather_desc}，温度是{temp_c}摄氏度"
    except requests.exceptions.RequestException as e:
        return f"错误：查询天气时发出请求，遇到网络问题，错误信息：{e}"
    except (KeyError, IndexError) as e:
        return f"错误：解析天气数据时出错，错误信息：{e}"

# 组装以上的工具函数，供LLM调用
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction
}

AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用工具一步步地解决问题。

# 可用工具：
- `get_weather(city: str)`：查询指定城市的实时天气。
- `get_attraction(city: str, weather: str)`：根据城市和天气搜索推荐的旅游景点。

# 输出格式要求：
你的每次回复必须严格遵循以下格式，包含一对 Thought 和 Action：

Thought: [你的思考过程和下一步计划]
Action: [你要执行的具体行动]

Action 的格式必须是以下之一：
1. 调用工具：function_name(arg_name="arg_value")
2. 结束任务：Finish[最终答案]

# 重要提示：
- 每次只输出一对 Thought-Action
- Action 必须在同一行，不要换行
- 当收集到足够信息可以回答用户问题时，必须使用 Action: Finish[最终答案] 格式结束
- 语言必须是中文。
- 必须严格按照条件进行回答

请开始吧！
"""

# 提示词工程是非常重要的一步，它决定了智能体的行为和性能。

import sys
from dotenv import load_dotenv

# 获取当前文件的父目录的父目录（项目根目录），并添加到sys.path，以后上线需要将myAgents模块发布，这里就不要了
project_root = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 加载环境变量
load_dotenv(override=True)  # override=True表示如果环境变量已存在，则覆盖它们   

if __name__ == "__main__":
    # arg存的是数组从命令行参数中获取城市名称
    #argv[0]是脚本文件名，从1开始是命令行参数
    #argv[1]是第一个参数,即城市名称，默认值为北京
    args = sys.argv[1:]
    if len(args) == 0:
        city = "北京"
    else:
        city = args[0]

        
    # ----1. 配置LLM客户端-----
    # 请根据您使用的服务，将这里替换成对应的凭证和地址
    open_ai_key=os.environ.get("OPENAI_API_KEY")
    model_name=os.environ.get("MODEL_NAME")
    openai_base_url=os.environ.get("OPENAI_BASE_URL")
    TAVILY_API_KEY=os.environ.get("TAVILY_API_KEY")

    llm = OpenAICompatibleClient(
        api_key=open_ai_key, 
        model=model_name, 
        base_url=openai_base_url
    )

    #------ 2. 初始化-----
    user_prompt = (f"你好，请帮我查询一下今天{city}的天气，并根据天气推荐适合的旅游景点。")
    prompt_history = [f"用户需求: {user_prompt}"] # 初始化prompt历史记录

    print(f"用户请求:{user_prompt}\n" + "="*40 );

    #------ 3. 执行行动循环-----
    for i in range(50): # 最多循环50次
        print(f"第{i+1}轮循环---\n")

        # 3.1 构建prompt
        full_prompt = "\n".join(prompt_history)

        # TODO: prompt 如何压缩，如何用到缓存，。。。。。？

        # 3.2 调用LLM进行思考
        llm_output = llm.generate(full_prompt, system_prompt=AGENT_SYSTEM_PROMPT)
        # 模型可能输出多余的Thought和Action，需要截断
        match = re.search(r'(Thought:.*?Action:.*?)(?:\n\s*(?:Thought:|Action:|Observation:)|\Z)', llm_output, re.DOTALL)
        if match:
            truncated = match.group(1).strip()
            if truncated != llm_output.strip():
                llm_output = truncated
                print(f"截断多余的Thought和Action对")
        print(f"LLM输出: {llm_output}\n")
        prompt_history.append(llm_output)

        # 3.3 解析Thought和Action并执行
        action_match = re.search(r"Action:(.*)", llm_output, re.DOTALL)
        if not action_match:
            observation = "未能解析到Action，请检查LLM输出格式。"
            observation_str = f"Observation: {observation}"
            print(f"{observation_str}\n" + "="*40 )
            prompt_history.append(observation_str)
            continue

        action_str = action_match.group(1).strip()

        if action_str.startswith("Finish"):
            # 任务结束[最终答案]
            finish_match = re.match(
                r"Finish\[(.*)\]",
                action_str,
                re.DOTALL
            )

            if finish_match:
                final_answer = finish_match.group(1)
                print(f"任务结束，最终答案: {final_answer}")
            else:
                print(f"无法解析 Finish: {action_str}")

            break
        # if action_str.startswith("Finish"):
        #     # 任务结束[最终答案]
        #     final_answer = re.match(r"Finish\[(.*)\]", action_str).group(1) 
        #     print(f"任务结束，最终答案: {final_answer}" )
        #     break

        # 下一种情况: action是调用函数
        # Action：function_name(arg_name="arg_value")
        tool_name = re.search(r"(\w+)\(", action_str).group(1) # 提取函数名
        arg_str = re.search(r"\((.*)\)", action_str).group(1) # 提取参数字符串
        kwargs = dict( re.findall(r'(\w+)="([^"]*)"', arg_str) ) # 解析参数字符串

        if tool_name in available_tools:
            observation = available_tools[tool_name](**kwargs) # get_weather(city="北京") 或 get_attraction(city="北京", weather="晴")
        else:
            observation = f"函数 {tool_name} 不存在，请检查LLM输出格式。"

        # 3.4 记录观察结果
        observation_str = f"Observation: {observation}"
        print(f"{tool_name}执行结果为: {observation}\n" + "="*40 )
        prompt_history.append(observation_str)
