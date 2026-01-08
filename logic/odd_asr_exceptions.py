# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: odd_asr_exceptions.py 
@info: 消息模版
"""

from flask import jsonify

from oddasr.logic import odd_asr_result

# 以下是c++的错误的PYTHON实现.

# Format: A.BBB.C.DDD

# A: TYPE [1,9]
EM_ERR_TYPE_C = "1"         #caller error
EM_ERR_TYPE_S = "2"         #callee error
EM_ERR_TYPE_T = "3"   

# BBB: MOD [000,999]
EM_ERR_MOD_LLM = "001"
EM_ERR_MOD_ASR = "002"
EM_ERR_MOD_TTS = "003"
EM_ERR_MOD_EMOTION = "004"
EM_ERR_MOD_MEMORY = "005"

# C.DDD: CODE [0000,9999]

g_mai_err_api = {}

def DEF_ERR(MOD,TYPE,CODE,DESC = ""):
    error_code = (int)(TYPE + MOD + CODE)
    g_mai_err_api[error_code] = DESC
    return error_code

def mai_err_name(error_code):
    ns = globals()
    for name in ns:
        if ns[name] == error_code:
            return name
    return ""

def mai_err_desc(error_code):
    if error_code in g_mai_err_api:
        return g_mai_err_api[error_code]
    return ""


# 以下是错误码定义:
## 通用错误：
## 错误码 原因 解决办法 
EM_ERR_ASR_AUTH_ERROR       = 40000001 # 身份认证失败 检查使用的令牌是否正确，是否过期
EM_ERR_ASR_INVALID_REQ      = 40000002 # 无效的消息 检查发送的消息是否符合要求
EM_ERR_ASR_INVALID_TOKEN    = 40000003 # 令牌过期或无效的参数 首先检查使用的令牌是否过期，然后检查参数值设置是否合理
EM_ERR_ASR_SESSION_TIMEDOUT = 40000004 # 空闲超时 确认是否长时间没有发送数据到服务端
EM_ERR_ASR_REQ_TOO_MANY     = 40000005 # 请求数量过多 检查是否超过了并发连接数或者每秒钟请求数
EM_ERR_ASR_CLIENT_ERROR     = 40000006 # 默认的客户端错误码 查看错误消息或提交工单
EM_ERR_ASR_SERVER_ERROR     = 50000000 # 默认的服务端错误 如果偶现可以忽略，重复出现请提交工单
EM_ERR_ASR_GRPC_ERROR       = 50000001 # 内部 GRPC 调用错误 如果偶现可以忽略，重复出现请提交工单
EM_ERR_ASR_GRPC_ERROR_2     = 52010001 # 内部 GRPC 调用错误 如果偶现可以忽略，重复出现请提交工单


## 网关错误：
## 错误码 原因 解决办法 
EM_ERR_ASR_GATEWAY_ERROR_1 = 40010001 # 不支持的接口 使用了不支持的接口，如果使用 SDK 请提交工单
EM_ERR_ASR_GATEWAY_ERROR_2 = 40010002 # 不支持的指令 使用了不支持的指令，如果使用 SDK 请提交工单
EM_ERR_ASR_GATEWAY_ERROR_3 = 40010003 # 无效的指令 指令格式错误，如果使用 SDK 请提交工单
EM_ERR_ASR_GATEWAY_ERROR_4 = 40010004 # 客户端提前断开连接 检查是否在请求正常完成之前关闭了连接
EM_ERR_ASR_GATEWAY_ERROR_5 = 40010005 # 任务状态错误 发送了当前任务状态不能处理的指令


## Meta 错误
## 错误码 原因 解决办法 
EM_ERR_ASR_META_ERROR_5 = 40020105 # 应用不存在 检查应用 appKey 是否正确，是否与令牌归属同一个账号


## 实时语音识别
## 错误码 原因 解决办法 
EM_ERR_ASR_REAL_TIME_CLIENT_ERROR_1 = 41040201 # 客户端 10s 内停止发送数据 检查网络问题，或者检查业务中是否存在不发数据的情况
EM_ERR_ASR_REAL_TIME_CLIENT_ERROR_2 = 41040202 # 客户端发送数据过快，服务器资源已经耗尽 检测客户端发包是否过快，是否按照 1：1 的实时率来发包
EM_ERR_ASR_REAL_TIME_CLIENT_ERROR_3 = 41040203 # 客户端发送音频格式不正确 请将音频数据的格式转换为 SDK 目前支持的音频格式来发包
EM_ERR_ASR_REAL_TIME_CLIENT_ERROR_4 = 41040204 # 客户端调用方法异常 客户端应该先调用发送请求接口，在发送请求完毕后再调用其他接口
EM_ERR_ASR_REAL_TIME_CLIENT_ERROR_5 = 41040205 # 客户端设置 MAXSILENCE_PARAM 方法异常 参数 MAXSILENCE_PARAM 的范围在[200-2000]
EM_ERR_ASR_REAL_TIME_SERVER_ERROR_1 = 51040101 # 服务端内部错误 未知错误
EM_ERR_ASR_REAL_TIME_SERVER_ERROR_2 = 51040102 # 保留参数 ASR_SERVICE_UNAVAILABLE
EM_ERR_ASR_REAL_TIME_SERVER_ERROR_3 = 51040103 # 实时语音识别服务不可用 需要查看实时语音识别服务是否有任务堆积等导致任务提交失败
EM_ERR_ASR_REAL_TIME_SERVER_ERROR_4 = 51040104 # 请求实时语音识别服务超时 具体需要排查实时语音识别日志
EM_ERR_ASR_REAL_TIME_SERVER_ERROR_5 = 51040105 # 调用实时语音识别服务失败 检查实时语音识别服务是否启动，端口是否正常开启
EM_ERR_ASR_REAL_TIME_SERVER_ERROR_6 = 51040106 # 实时语音识别服务负载均衡失败，未获取到实时语音识别服务的 IP 地址检查 VPC 中的实时语音识别服务机器是否有异常


#错误码定义如下:
## client errors
EM_ERR_ASR_ARGS_ERROR                             = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_C , "0001")
EM_ERR_ASR_SESSION_ID_EXIST                       = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_C , "0002")
EM_ERR_ASR_SESSION_ID_NOVALID                     = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_C , "0003")
EM_ERR_ASR_MINUTES_MOID_ERROR                     = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_C , "0004")
## server errors
EM_ERR_ASR_SERVER_ERROR                           = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_S , "0001", "timeout")
EM_ERR_ASR_WS_NONE                                = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_S , "0002", "reply timeout")
EM_ERR_ASR_SYNC_HOTWORDS_ERROR                    = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_S , "0003")
EM_ERR_ASR_METHOD_NOT_SUPPORT                     = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_S , "0004")
EM_ERR_ASR_MINUTES_STATUS_ERROR                   = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_S , "0005")


class CodeException(Exception):

    def __init__(self, error_code, error_desc):
        super().__init__()
        self.error_code = error_code
        self.error_desc = error_desc

    def __str__(self):
        return "%d - %s" % (self.error_code, self.error_desc)

    def __unicode__(self):
        return u"%d - %s" % (self.error_code, self.error_desc)


class ResultException(CodeException):
    """异常返回"""
    def __init__(self, error_code=EM_ERR_ASR_ARGS_ERROR, error_desc=mai_err_name(EM_ERR_ASR_ARGS_ERROR)):
        super(ResultException, self).__init__(error_code, error_desc)


def handler(exc):
    return jsonify(odd_asr_result.from_exc(exc))
