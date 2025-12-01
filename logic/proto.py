# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: result.py 
@time: 2025/6/9 15:00
@info: OddAs websocket protocol define.
"""


class TOddAsrHeader:
    '''
    OddAsr header define.
    ---
    namespace                           String 消息所属的命名空间
    name                                String 消息名称，SentenceBegin 表示一个句子的开始
    status                              Integer 状态码，表示请求是否成功，见服务状态码
    status_text                         String 状态消息
    task_id                             String 任务全局唯一 ID，请记录该值，便于排查问题
    message_id                          String 本次消息的 ID
    '''
    task_id = ""
    message_id = ""

    namespace = ""
    name = ""

    status = 20000000
    # status_message = "" 
    status_text = "Success"             # "GATEWAY|SUCCESS|Success."

    def __init__(self, namespace: str = "",
                 name: str = "",
                 status: int = 0,
                 status_text: str = "",
                 task_id: str = "",
                 message_id: str = "") -> None:
        self.namespace = namespace
        self.name = name
        self.status = status
        self.status_text = status_text
        self.task_id = task_id
        self.message_id = message_id

class TOddAsrPayload:
    '''
    OddAsr transcription result payload
    index                               Integer 句子编号，从 1 开始递增
    time                                Integer 当前已处理的音频时长，单位是毫秒
    result                              String 当前句子的识别结果
    confidence                          Double 当前句子识别结果的置信度，取值范围[0.0, 1.0]，值越大表示置信度越高
    gender                              String 开启 enable_gender_detect 后返回，性别及年龄，包括 male 成年男性,female 成年女性,child 儿童,unknown 未知
    gender_score                        Float 开启 enable_gender_detect 后返回， 算法给出的置信度得分，得分越高可靠性越高，调用方可以基于此得分判断是否采信模型结果
    '''
    index = 0
    time = 0
    result = ""
    confidence = 0.0
    gender = ""
    gender_score = 0.0

    def __init__(self , index: int = 0,
                 time: int = 0,
                 result: str = "",
                 confidence: float = 0.0,
                 gender: str = "",
                 gender_score: float = 0.0) -> None:
        self.index = index
        self.time = time
        self.result = result
        self.confidence = confidence
        self.gender = gender
        self.gender_score = gender_score

class TOddAsrPayloadReq:
    '''
    OddAsr Apply transcription request payload
    ---
    参数 类型 是否必需 说明 
    appkey                              Sring   是 业务方或者业务场景的标记，专有云默认为 default
    format                              String  否 音频编码格式，支持的格式：pcm（无压缩的 pcm 文件或 wav 文件）
    sample_rate                         Integer 否 音频采样率，默认是 16000Hz，请确保采样率与模型类型保持一致
    enable_intermediate_result          Boolean 否 是否返回中间识别结果，默认是 False
    enable_punctuation_prediction       Boolean 否 是否在后处理中添加标点，默认是False
    enable_inverse_text_normalization   Boolean 否 是否在后处理中执行 ITN，设置为 true时，中文数字将转为阿拉伯数字输出，默认是 False

    model                               String  否 模型名称
    customization_id                    String  否 定制模型 ID
    vocabulary_id                       String  否 定制泛热词 ID
    class_vocabulary_id                 Map     否 定制类热词 ID，Map 的 Key 是类名，Value 是类热词词表 ID。目前只有law_politics(政法)，customer_service_8k(客服质检)模型支持人名(PERSON)、地名(ADDRESS)类热词
    max_sentence_silence                Integer 否 语音断句检测阈值，静音时长超过该阈值会被认为断句，合法参数范围 200～2000(ms)，默认值 800ms，开启语义断句(enable_semantic_sentence_detection)后，此参数无效
    enable_semantic_sentence_detection  Boolean 否 是否开启语语义断句，可选，默认是False；开启后强制启用加标点功能且不可禁用，默认开 itn 但可通过传参关闭。
    vad_silence_duration                Integer 否 语义断句长静默的静默时长参数，用户触发此参数阈值后会自动断句，开启语义断句后生效，合法参数范围[2000 10000]ms，默认值 2000ms
    enable_words                        Boolean 否 是否开启返回词信息，默认 False 不开启，在 vad 断句时生效
    disfluency                          Boolean 否 顺滑，默认 False 关闭
    enable_ignore_sentence_timeout      Boolean 否 默认 False，开启后忽略实时转写处理过程中的 asr 超时错误
    enable_gender_detect                Boolean 否 默认 False，开启后返回性别、年龄识别结果，需要单独购买相关算法服务后可以开启
    '''
    appkey = "default"
    format = "pcm"
    sample_rate = 16000
    enable_intermediate_result = False
    enable_punctuation_prediction = False
    enable_inverse_text_normalization = False

    model = ""
    customization_id = ""
    vocabulary_id = ""
    class_vocabulary_id = {}
    max_sentence_silence = 800
    enable_semantic_sentence_detection = False
    vad_silence_duration = 2000
    enable_words = False
    disfluency = False
    enable_ignore_sentence_timeout = False
    enable_gender_detect = False

    def __init__(self , appkey: str = None, 
                 format: str = None, 
                 sample_rate: int = 16000, 
                 enable_intermediate_result: bool = False, 
                 enable_punctuation_prediction: bool = False, 
                 enable_inverse_text_normalization: bool = False, 
                 model: str = "", 
                 customization_id: str = "", 
                 vocabulary_id: str = "", 
                 class_vocabulary_id: dict = None, 
                 max_sentence_silence: int = 800, 
                 enable_semantic_sentence_detection: bool = False, 
                 vad_silence_duration: int = 2000, 
                 enable_words: bool = False, 
                 disfluency: bool = False, 
                 enable_ignore_sentence_timeout: bool = False, 
                 enable_gender_detect: bool = False) -> None:
        self.appkey = appkey
        self.format = format
        self.sample_rate = sample_rate
        self.enable_intermediate_result = enable_intermediate_result
        self.enable_punctuation_prediction = enable_punctuation_prediction
        self.enable_inverse_text_normalization = enable_inverse_text_normalization
        self.model = model
        self.customization_id = customization_id
        self.vocabulary_id = vocabulary_id
        self.class_vocabulary_id = class_vocabulary_id
        self.max_sentence_silence = max_sentence_silence
        self.enable_semantic_sentence_detection = enable_semantic_sentence_detection
        self.vad_silence_duration = vad_silence_duration
        self.enable_words = enable_words
        self.disfluency = disfluency
        self.enable_ignore_sentence_timeout = enable_ignore_sentence_timeout
        self.enable_gender_detect = enable_gender_detect


class TOddAsrWord:
    '''
    参数 类型 说明 
    word        String 识别结果
    begin_time  Integer 词的开始时间，单位是毫秒
    end_time    Integer 词的结束时间，单位是毫秒
    confidence  Double 词的置信度，取值范围[0.0, 1.0]，值越大表示置信度越高
    '''
    word = ""
    begin_time = 0
    end_time = 0
    confidence = 1.0


class TOddAsrPayloadRes:
    '''
    参数 类型 说明 
    index       Integer 句子编号，从 1 开始递增
    time        Integer 当前已处理的音频时长，单位是毫秒
    begin_time  Integer 当前句子句首对应的 SentenceBegin 事件的时间，单位是毫秒
    end_time    Integer 当前句子句尾对应的 SentenceBegin 事件的时间，单位是毫秒
    result      String 当前的识别结果
    confidence  Double 当前句子识别结果的置信度，取值范围[0.0, 1.0]，值越大表示置信度越高    
    fin         Integer 句子是否结束，1 表示结束，0 表示未结束
    words       List<TOddAsrWord> 句子的识别结果，每个元素包含词、开始时间、结束时间、置信度等信息
    '''
    index = 0
    time = 0
    begin_time = 0
    end_time = 0
    result = ""
    confidence = 1.0
    fin = 1
    words = []

class TOddAsrApplyReq:
    '''
    OddAsr Apply transcription request
    ---
    参数 类型 是否必需 说明 
    header                              TOddAsrHeader 是 消息头
    payload                             TOddAsrPayloadReq 是 消息体
    '''
    def __init__(self , header: TOddAsrHeader = None, payload: TOddAsrPayloadReq = None) -> None:
        if header:
            self.header = header
        else:
            self.header = TOddAsrHeader(name="StartTranscription", namespace="SpeechTranscriber", )
        if payload:
            self.payload = payload
        else:
            self.payload = TOddAsrPayloadReq()

class TOddAsrApplyRes:
    def __init__(self , header: TOddAsrHeader = None, payload: TOddAsrPayloadRes = None) -> None:
        if header:
            self.header = header
        else:
            self.header = TOddAsrHeader(name="SentenceBegin", namespace="SpeechTranscriber", )

        if payload:
            self.payload = payload
        else:
            self.payload = TOddAsrPayloadRes()

class TOddAsrTranscribeRes:
    def __init__(self, header: TOddAsrHeader = None, payload: TOddAsrPayloadRes = None) -> None:
        if header:
            self.header = header
        else:
            self.header = TOddAsrHeader(name="TranscriptionResultChanged", namespace="SpeechTranscriber", )
        
        if payload:
            self.payload = payload
        else:
            self.payload = TOddAsrPayloadRes()


# class TCMDCommonRes:
#     name=""
#     message_id=""
#     error_code = 0
#     error_desc=""

#     def __init__(self , message_id, name) -> None:
#         self.message_id = message_id
#         self.name = name

# class TASRRecogTextParam:
#     text=""
#     bg=0
#     ed=0
#     fin=0

#     def __init__(self) -> None:
#         pass

def obj_to_dict(self):
    return dict((name, getattr(self, name)) for name in dir(self) if not name.startswith('__'))

def obj_to_dict_recursive(self):    
    res = {}
    for name in dir(self):
        if not name.startswith('__'):
            attr = getattr(self, name)
            if isinstance(attr, object) and hasattr(attr, '__dict__'):
                res[name] = obj_to_dict_recursive(attr)
            else:
                res[name] = attr
    return res

def obj_from_dict_recursive(self, d):
    for name, value in d.items():
        if isinstance(value, dict):
            setattr(self, name, obj_from_dict_recursive(self, value))
        else:
            setattr(self, name, value)
    return self

if __name__ == "__main__":
    header: TOddAsrHeader = TOddAsrHeader()
    payload: TOddAsrPayloadReq = TOddAsrPayloadReq()
    res = TOddAsrApplyReq(header=header, payload=payload)

    print(f"res={obj_to_dict_recursive(res)}")

