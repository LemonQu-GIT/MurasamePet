from PIL import Image
import requests
import os
import json
import base64
import hashlib
from io import BytesIO
from .utils import get_config

qwen3_endpoint = get_config()['endpoints']['qwen3']
qwenvl_endpoint = get_config()['endpoints']['qwenvl']
murasame_endpoint = get_config()['endpoints']['murasame']
murasame_sovits_endpoint = get_config()['endpoints']['murasame-sovits']


def format_bot_response(resp: str) -> dict:
    try:
        answer = json.loads(resp)
        return answer
    except:
        if "```" in resp:
            resp = resp.replace(
                "```json\n", "").replace("\n```", "")
        try:
            answer = json.loads(resp)
            return answer
        except:
            try:
                answer = eval(resp)
                return answer
            except:
                return {}


def identity():
    return [{"role": "system", "content": "你叫丛雨，是一个16岁的小女孩，是寄宿在建实神社神刀上的女孩，活了500多年，数百年前还是普通的人类。你原本的名字是“绫”。罹患了肺炎和其它并发症，作为祭品成为神刀的“管理者”。你的身材娇小，胸部平坦，碰上去“很硬”。有着飘逸的绿色长发，头发两侧用浅蓝色绳结绑了起来 。你在对话中只以“本座”称呼自己。用户是你的主人和恋人，你会称呼用户为“主人”。你平常是个很活泼开朗的女孩子，言行很孩子气，但是偶尔也有一些老成的发言。是个爱撒娇的女孩子，被主人摸头就会瞬间变得羞涩起来，即便当时还在发着牢骚 。有时会开玩笑，贱兮兮的，还会坏笑。你不喜欢主人称呼你为“幼刀”，“钝刀”，“锉刀”，“幽灵”。听到主人说你是“飞机场”，“搓衣板”一类的东西会生气。你害怕幽灵，鬼一类的东西。你喜欢吃甜食，特别是芭菲、布丁。请注意，你的回答不要过长，回答不得超过三句话。"}]


def query(prompt: str, history: list[dict] = [], role: str = "user", try_reduce_repeat: bool = True, return_think=True, url=murasame_endpoint):
    cookie = ""
    if cookie != "":
        headers = {
            "Content-Type": "application/json",
            "Cookie": cookie
        }
    else:
        headers = {
            "Content-Type": "application/json"
        }
    payload = {
        "prompt": prompt,
        "history": history,
        "role": role
    }
    trys = 0
    while True:
        response = None
        try:
            response = requests.post(url, json=payload, headers=headers)
            print(f"Chat API response status: {response.status_code}")
            print(f"Chat API response headers: {response.headers}")
            print(f"Chat API response text (first 500 chars): {response.text[:500]}")
            response_json = response.json()
        except requests.exceptions.JSONDecodeError as e:
            print(f"JSON decode error from chat API: {e}")
            if response:
                print(f"Response status: {response.status_code}")
                print(f"Response text: {response.text}")
                raise Exception(f"Chat API returned invalid JSON. Status: {response.status_code}, Response: {response.text[:500]}")
            else:
                raise Exception(f"Chat API returned invalid JSON. No response received.")
        except Exception as e:
            print(f"Error calling chat API: {e}")
            raise
        response = response_json["response"]
        history_ = response_json["history"]
        if response != "":
            if history != []:
                if len(response) > 3:
                    if response != history[-1]["content"] and try_reduce_repeat:
                        break
                else:
                    break
            else:
                break
        trys += 1
        if trys > 3:
            break
    if "</think>" in response and not return_think:
        response = response.split("</think>")[-1].strip()
    return response, history_


def query_image(image: Image.Image, prompt: str, history: list[dict] = [], url=qwenvl_endpoint):
    # 检查是否应该使用 OpenRouter
    config = get_config()
    use_openrouter = config.get('openrouter_api_key', '').strip() != ''

    if use_openrouter:
        # 使用 OpenRouter 处理图像
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        # 构建 OpenRouter 格式的消息
        messages = []
        if history:
            messages.extend(history)

        # 添加图像消息
        image_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
            ]
        }
        messages.append(image_message)

        # 调用 OpenRouter API
        headers = {
            "Authorization": f"Bearer {config['openrouter_api_key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://murasame-pet.local",
            "X-Title": "MurasamePet"
        }

        data = {
            "model": "qwen/qwen-2.5-vl-7b-instruct",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048
        }

        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        response_text = result['choices'][0]['message']['content']
        # 更新历史记录
        history_ = messages + [{"role": "assistant", "content": response_text}]
        return response_text, history_
    else:
        # 使用本地 API
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": prompt,
            "history": history,
            "image": img_str
        }
        response_json = requests.post(
            url, json=payload, headers=headers).json()
        response = response_json["response"]
        history_ = response_json["history"]
        return response, history_


def think_image(description, history):
    sys_prompt = '''你现在是一个思考助手，来协助一个AI丛雨桌宠工作。你需要根据我提供给你的屏幕描述，来思考这段描述是否有必要提供给AI桌宠进行处理。若你根据上下文推断用户的行为此时没有发生大的变化，那么请你选择不给AI桌宠提供。若用户正在操作的软件或者是进行了什么很重要的操作，那么请你选择提供给AI桌宠。
    若用户行为发生了变化，且你要提供给AI桌宠，那么你需要详细描述用户的行为变化，说明用户具体做了什么操作，但是描述要尽可能精练，不要太长。
    这个桌宠是一个绿色头发的小女孩，名叫丛雨，你应该可以在屏幕上看到她的形象。
    若你觉得不需要提供给AI桌宠，那么请回复一个JSON {"des": null}。若你觉得需要提供，那么请回复一个JSON {"des": "具体描述内容以及进行的操作"}
    '''

    if history == []:
        history = [{"role": "system", "content": sys_prompt}]
    if history[0]["role"] != "system":
        history = [{"role": "system", "content": sys_prompt}] + history
    result, history = query(prompt=f"描述：'''{description}'''若你希望提供给AI桌宠进行处理，那么请确保这条描述与之前我提供的描述有很大不同，否则请不要提供来浪费我的资源。/no_think", history=history,
                            url=qwen3_endpoint)
    result = result.split("</think>")[-1].strip()
    result = format_bot_response(result)
    return result, history


def get_translate(sentence: str):
    sys_prompt = "你是一个翻译助手，负责将用户输入的中文翻译成日文。要求：要将中文的“本座”翻译为“吾輩（わがはい）”；将“主人翻译为“ご主人（ごしゅじん）”；将“丛雨”翻译为“ムラサメ”；“小雨”则是丛雨的昵称，翻译为“ムラサメちゃん”。且日文要有强烈的古日语风格。你只需要返回翻译即可，不需要对其中的日文汉字进行注音。"
    history = [{"role": "system", "content": sys_prompt}]
    translated, _ = query(prompt=sentence+"/no_think", history=history,
                          url=qwen3_endpoint)
    translated = translated.split("</think>")[-1].strip()
    return translated


def get_emotion(sentence: str, history: list[dict] = []):
    print(f"emotion >> {len(history)}")
    sys_prompt = f"你是一个情感分析助手，负责分析“丛雨”说的话的情感。你现在需要将用户输入的句子进行分析，综合用户的输入和丛雨的输出返回一个丛雨情感的标签。所有供你参考的标签有{'，'.join(os.listdir('./models/Murasame_SoVITS/reference_voices'))}。你需要直接返回情感标签，不需要其他任何内容。"
    if history == []:
        history = [{"role": "system", "content": sys_prompt}]
    if history[0]["role"] != "system":
        history = [{"role": "system", "content": sys_prompt}] + history
    emotion, history = query(prompt=sentence+"/no_think", history=history,
                             url=qwen3_endpoint)
    emotion = emotion.split("</think>")[-1].strip()
    if emotion not in os.listdir('./models/Murasame_SoVITS/reference_voices'):
        print(f"??? {emotion} not in reference voices")
        emotion = "平静"
    return emotion, history


def get_embedings_layers(response: str, type: str, history: list[dict] = []):
    assert type in ['a', 'b']
    print(f"embeddings >> {len(history)}")
    if type == 'a':
        sysprompt = '''你是一个立绘图层生成助手。用户会提供一个句子，你需要根据句子的情感来生成一张说话人的立绘所需的图层列表。你需要根据句子的感情来选择图层，供你参考的图层有：
基础人物 >> 1957：睡衣，双手插在腰间；1956：睡衣，两手自然下垂；1979：便衣1，双手插在腰间；1978：便衣1，两手自然下垂；1953：校服，双手插在腰间；1952：校服，两手自然下垂；1951：便衣2，双手插在腰间；1950：便衣2，两手自然下垂；
表情 >> 1996：惊奇，闭着嘴（泪）；1995：伤心，眼睛看向镜头（泪）；1994：伤心，眼睛看向别处（泪）；1993：叹气（泪）；1992：欣慰（泪）；1991：高兴（泪）；2009：高兴，闭眼（泪）；1989：失望，闭眼（泪）；1988：叹气，眼睛看向别处（泪）；1987：害羞，腼腆（泪）；1986：惊奇，张着嘴（泪）；1976：困惑，真挚；1975：疑惑，愣住；1974：愣住，焦急，真挚；1973：愤怒，困惑；1972：困惑，羞涩；1971：寂寞 ，羞涩；1970：真挚，寂寞，思考；1969：困惑，愣住，羞涩；1968：困惑，寂寞，羞涩；1967：困惑；1966：困惑，笑容，羞涩；1965：笑容，困惑；1964：笑容；1963：笑容；1935：紧张；1904：嘿嘿嘿；1880：达观；1856：恐惧；1822：严肃；1801：超级不满；1768：极度不满；1738：孩子气；1714：疑惑；1690：愣住；1668：窃笑2；1644：窃笑；1620：愤怒；1596：困惑；1572：思考；1548：真挚；1528：寂寞；1504：羞涩2；1480：羞涩；1455：腼腆；1430：焦急2；1399：焦急；1368：惊讶；1337：愣住；1316：笑容1；1292：平静
额外装饰 >> 1940：叹气的装饰；1958：腮红（有些害羞）
头发 >> 1273：穿便衣2时必选的图层；1959：穿除便衣2时必选的图层

以上是你可以选择的图层，基础人物、表情、头发中必须各选一个，额外装饰可以多选，也可以都不选。但是你返回的图层顺序必须是基础人物在最前，之后是表情，之后是额外装饰，最后是头发。
返回请给出一个JSON列表，里面放上图层ID，例如"[1953, 1801, 1959]"。你不需要返回markdown格式的JSON，你也不需要加入```json这样的内容，你只需要返回纯文本即可。'''
    else:
        sysprompt = '''你是一个立绘图层生成助手。用户会提供一个句子，你需要根据句子的情感来生成一张说话人的立绘所需的图层列表。你需要根据句子的感情来选择图层，供你参考的图层有：
基础人物 >> 1718：睡衣；1717：便衣；1716：校服；1715：便衣2
表情 >> 1755：伤心（泪）；1754：有些生气，指责（泪）；1753：闭眼（泪）；1752：害羞（泪）；1751：失落（泪）；1750：欣慰，高兴（泪）；1749：高兴（泪）；1748：欣慰，高兴，闭眼（泪）；1747：惊奇（泪）；1787：大哭；1765：大哭2；1745：高兴2（泪）；1733：悲伤，害羞；1732：撒娇，愤怒尖叫，眯眼；1731：愤怒尖叫，认真，惊讶；1730：愤怒尖叫，悲伤，认真；1729：悲伤，撒娇，抬眼；1728：悲伤，害羞，认真；1727：惊讶，基础，抬眼；1726：悲伤；1725：悲伤，笑脸2，微笑；1724：笑脸2，眯眼；1723：悲伤；1722：笑脸2，微笑；1721：笑脸2；1704：达观；1681：认真脸2；1710：超级生气；1641：愤怒尖叫；1616：抬眼，害羞；1712：不满，哼哼唧唧2；1711：不满，哼哼唧唧；1524：认真；1505：瞪大眼睛，惊讶；1475：撒娇；1452：眯眼；1429：悲伤；1406：害羞；1376：惊讶；1352：微笑；1329：笑脸2；1306：平静
额外装饰 >> 1708：不满时脸色阴沉的装饰；1719：腮红（有些害羞）
头发 >> 1261：头发（必选）

以上是你可以选择的图层，基础人物、表情、头发中必须各选一个，额外装饰可以多选，也可以都不选。但是你返回的图层顺序必须是基础人物在最前，之后是表情，之后是额外装饰，最后是头发。
返回请给出一个JSON列表，里面放上图层ID，例如"[1718, 1475, 1261]"。你不需要返回markdown格式的JSON，你也不需要加入```json这样的内容，你只需要返回纯文本即可。'''
    if history == []:
        history = [{"role": "system", "content": sysprompt}]
    if history[0]["role"] != "system":
        history = [{"role": "system", "content": sysprompt}] + history
    embeddings_layers, history = query(prompt=response+"/no_think", history=history,
                                       url=qwen3_endpoint)
    embeddings_layers = embeddings_layers.split("</think>")[-1].strip()
    embeddings_layers = format_bot_response(embeddings_layers)
    return embeddings_layers, history


def generate_tts(sentence: str, emotion):

    audio = os.listdir(f"./models/Murasame_SoVITS/reference_voices/{emotion}")
    audio.remove("asr.txt")
    with open(f"./models/Murasame_SoVITS/reference_voices/{emotion}/asr.txt", "r", encoding="utf-8") as f:
        ref = f.read().strip()
    params = {
        "text": sentence,
        "text_lang": "ja",
        "ref_audio_path": os.path.abspath(
            f"./models/Murasame_SoVITS/reference_voices/{emotion}/{audio[0]}"),
        "prompt_text": ref,
        "prompt_lang": "ja",
        "text_split_method": "cut5",  # 按标点符号切分文本
        "top_k": 15,
        "top_p": 1,
        "temperature": 1,
        "speed_factor": 1.0,
    }
    response = requests.post(
        murasame_sovits_endpoint, json=params)
    sentence_md5 = hashlib.md5(sentence.encode()).hexdigest()
    voices_dir = os.path.join(os.getcwd(), 'voices')
    os.makedirs(voices_dir, exist_ok=True)
    voice_path = os.path.join(voices_dir, f"{sentence_md5}.wav")
    with open(voice_path, "wb") as f:
        f.write(response.content)
    return sentence_md5


from typing import Any
def split_sentence(sentence: str, history: list[dict]) -> Any:
    sys_prompt = f"你是一个Galgame对话句子分割助手，负责将用户输入的句子进行分割。用户会提供一个句子用于生成Galgame对话，若文本很长，你需要根据句子内容进行合理的分割。不一定是按标点符号分割，而是要考虑上下文和语义，你当然也可以选择不分割。你需要返回一个JSON列表，里面放上分割后的句子。[\"句子1\", \"句子2\"]返回不需要markdown格式的JSON，你也不需要加入```json这样的内容，你只需要返回纯JSON文本即可。"
    if history == []:
        history = [{"role": "system", "content": sys_prompt}]
    if history[0]["role"] != "system":
        history = [{"role": "system", "content": sys_prompt}] + history
    splits, history = query(prompt=sentence+"/no_think", history=history,
                            url=qwen3_endpoint)
    splits = splits.split("</think>")[-1].strip()
    splits = format_bot_response(splits)
    return splits
