import threading
import time
import json
import uuid
from sqlalchemy import false

from oddasr.log import logger

from oddasr.logic.minutes import *
from oddasr.logic import sensitivewords
from oddasr.logic.odd_asr_file import OddAsrFile
from oddasr.logic.odd_asr_instance import find_free_odd_asr_file, init_instance_file

from oddasr.model.meeting import CMeetingStatus2 # MEETING_OPEN_STATUS_INIT, MEETING_OPEN_STATUS_ENCODE, MEETING_OPEN_STATUS_EXCEPTION

class ScheduledTask(threading.Thread):
    def __init__(self, status_notifier):
        self.is_transmit = False
        self.thread_run = True
        self.encode_task = False
        self.wait_time = 10
        self.status_notifier = status_notifier # 转写成功/失败通知回调
        threading.Thread.__init__(self)
        threading.Thread.setDaemon(self, True)

    @staticmethod
    def start_task(priority, unique_id, file_name):
        str_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        session_id = uuid.uuid1()
        res = CStorageMinutes.addOpenFileMeeting(strSessionId=session_id, strRank=unique_id, strUniqueId=unique_id, strFileName=file_name, strBeginTime=str_time)
        if res:
            return session_id
        else:
            return None

    @staticmethod
    def cancel_task(session_id):
        logger.debug(f"cancel_task {session_id}")
        task_info = CStorageMinutes.getOpenFileMeetingInfo(session_id)
        if task_info is None:
            return True
        elif task_info["status"] == CMeetingStatus2.MEETING_OPEN_STATUS_INIT:
            return CStorageMinutes.deleteOpenFileMeeting(session_id)
        else:
            logger.info("task can't cancel status " + str(task_info["status"]))
        return False

    @staticmethod
    def task_status(session_id):
        logger.debug(f"task_status {session_id}")
        task_info = CStorageMinutes.getOpenFileMeetingInfo(session_id)
        if task_info is None or task_info["status"] == CMeetingStatus2.MEETING_OPEN_STATUS_EXCEPTION:
            return {"texts": {}, "status": 3}
        if task_info["status"] == CMeetingStatus2.MEETING_OPEN_STATUS_INIT:
            return {"texts": {}, "status": 0}
        elif task_info["status"] == CMeetingStatus2.MEETING_OPEN_STATUS_ENCODE:
            return {"texts": {}, "status": 1}
        else:
            record_texts, count = CStorageMinutes.getMeetingText(session_id, 0, 0 , False)
            texts = []
            for item in record_texts:
                text = {"bg": item.text_bg_time, "ed": item.text_ed_time, "text": item.text_content}
                texts.append(text)
            return {"texts": texts, "status": 2}

    @staticmethod
    def task_finish(session_id, texts):
        logger.debug(f"task_finish {session_id} {texts}")
        if len(texts) > 0: 
            task_info = CStorageMinutes.getOpenFileMeetingInfo(session_id)
            if task_info is not None:
                #uniqueId = hot_uid + ";" + sensitive_uid
                sensitive_uid = ""
                vec = task_info["uniqueId"].split(';')
                if len(vec) > 1:
                    sensitive_uid = vec[1]
                data = sensitivewords.SensitiveWordManage.get_sensitive_word(sensitive_uid)
                if data != None:
                    words = eval(data.get('sensitive_word', None))
                    if words is not None:
                        for i in range(len(texts)):
                            for j in range(len(words)):
                                texts[i]["text_content"] = texts[i]["text_content"].replace(words[j], "(" + words[j] + ")")
        str_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        return CStorageMinutes.updateOpenFileMeetingEnd(session_id, str_time, texts)    

    def run(self):
        logger.info(f"asr_recorder threadid: " + str(threading.get_ident()))
        while self.thread_run:
            # 重启时检查一下，是否有未完成的转写任务

            start_task_info = CStorageMinutes.getOpenFileMeetingInfoByPriority()

            if start_task_info is None:  # 无转写任务
                time.sleep(self.wait_time)
            else:
                session_id = start_task_info["uuid"]
                logger.debug(f"run {start_task_info}, session_id={session_id}")
                asr_file = self.__find_asr_instance(session_id=session_id)
                if asr_file is None:  # 资源申请失败
                    logger.info("appy resource fail " + str(start_task_info))
                    time.sleep(self.wait_time)
                else:
                    #uniqueId = hotowrds_list + ";" + sensiword_list
                    sensiword_list = ""
                    hotowrds_list = ""
                    vec = start_task_info["uniqueId"].split(';')
                    if len(vec) > 1:
                        sensiword_list = vec[1]
                    if len(vec) > 0:
                        hotowrds_list = vec[0]

                    output_text = asr_file.transcribe_file(start_task_info["fileName"], hotwords=hotowrds_list, output_format="raw")
                    self.__release_asr_instance(session_id, asr_file)  # 释放申请的ASR资源

                    if output_text is None:
                        logger.info("transcribe file fail " + str(start_task_info))
                        time.sleep(self.wait_time)
                    else:  # 设置任务为开始转写状态
                        logger.info(f"transcribe file success: {output_text}")

                        texts = self.__convert_texts(session_id=session_id, output_text=output_text)

                        # replace sensitive words
                        data = sensitivewords.SensitiveWordManage.get_sensitive_word(sensiword_list)
                        if data != None:
                            words = eval(data.get('sensitive_word', None))
                            if words is not None:
                                for i in range(len(texts)):
                                    for j in range(len(words)):
                                        texts[i]["text_content"] = texts[i]["text_content"].replace(words[j], "(" + words[j] + ")")
                        str_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                        ret = CStorageMinutes.updateOpenFileMeetingEnd(strSessionId=session_id, strEndTime=str_time, arrTexts=texts)
                        if ret:
                            logger.info(f"update open file meeting end success: {ret}")
                        else:
                            logger.error(f"update open file meeting end fail: {ret}")

                    continue


    def __convert_texts(self, session_id, output_text):
        logger.debug(f"__convert_texts {output_text}, session_id={session_id}, type={type(output_text)}")

        if type(output_text) is str:
            try:
                output_text = json.loads(output_text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse output_text as JSON: {output_text}")
                return []
        
        if ("sentence_info" not in output_text[0]) or (len(output_text[0]["sentence_info"]) == 0):
            return [{"session_id": session_id, "text_bg_time": 0, "text_ed_time": 0, "text_content": output_text[0]["text"]}]
        
        texts = []
        output_text = output_text[0]["sentence_info"]
        for item in output_text:
            text = {
                        "session_id": session_id, 
                        "text_bg_time": item["start"], 
                        "text_ed_time": item["end"], 
                        "text_content": item["text"],
                        # "text_time": item["timestamp"],
                        "text_term_alias": f"spk {item.get('spk', 'unknown')}"
                    }  
            texts.append(text)
        return texts

    def __find_asr_instance(self, session_id):
        logger.info("find asr instance " + session_id)
        odd_asr_file: OddAsrFile = find_free_odd_asr_file()
        if odd_asr_file is None:
            logger.info("no free asr instance for session: " + str(session_id))
            return None
        else:
            odd_asr_file.set_busy(session_id)
            return odd_asr_file


    def __release_asr_instance(self, session_id, odd_asr_file: OddAsrFile):
        logger.info(f"release asr instance: {session_id}, instance: {odd_asr_file}")
        if not odd_asr_file.is_busy():  # 资源无效，勿须释放
            return True
        odd_asr_file.set_busy(False)
        return True

if __name__ == '__main__':
    from odd_asr_file import OddAsrFile, OddAsrParamsFile
    import odd_asr_config as config

    odd_asr_params_file = OddAsrParamsFile()
    odd_asr_file_set = set()

    def init_instance_file():
        global odd_asr_file_set
        for i in range(config.odd_asr_cfg["asr_file_cfg"]["max_instance"]):
            odd_asr_file = OddAsrFile(odd_asr_params_file)
            odd_asr_file_set.add(odd_asr_file)

    def find_free_odd_asr_file():
        '''
        find a free odd_asr_file
        :param :
        :return:
        '''
        global odd_asr_file_set
        for odd_asr_file in odd_asr_file_set:
            if not odd_asr_file.is_busy():
                return odd_asr_file
            
        return None

    init_instance_file()

    scheduled_task = ScheduledTask(status_notifier=None)

    # priority = 1
    # unique_id = "220ed89d-7b84-11f0-9b0f-5c879c002fd9"
    # file_name = "test_cn_male_9s.wav"
    # scheduled_task.start_task(priority, unique_id, file_name)

    scheduled_task.start()

    try:
        # 主循环保持程序运行
        while True:
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        # 处理Ctrl+C中断，优雅退出
        logger.info("接收到中断信号，准备退出程序...")
        scheduled_task.thread_run = False  # 设置标志让线程退出
        scheduled_task.join(timeout=5)  # 等待线程结束，最多等待5秒
        logger.info("程序已退出")

