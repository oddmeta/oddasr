from email.policy import default
from sqlalchemy import Column, Integer, String, Text

from oddasr.model.db import Base

class CText(Base):
    __tablename__ = 'oddasr_text'
    
    text_id = Column(Integer, primary_key=True)     #
    session_id = Column(Text , index=True)
    text_bg_time = Column(Integer)
    text_ed_time = Column(Integer)
    text_content = Column(Text)        
    text_time = Column(Integer)
    text_term_e164 = Column(String(32))
    text_term_alias = Column(String(64))
    text_flag  = Column(Integer)            #1 句后分段 2 句前分段
    text_term_tb_time = Column(Integer)     # 有效片段未对齐前的tb
    text_term_td_time = Column(Integer)     # 有效片段未对齐前的td

    text_sign = Column(Integer,default=0)   #0 不需要优化的混音文本 
                                            #1 需要被优化的混音文本，尚未被优化掉
                                            #2 需要被优化的混音文本，已经被优化掉
                                            #3 优化成功的有效片段文本
                                            #---------------------------------
                                            # 0~3 TCMDAsrMinutesTextOptNtf (ASR_MINUTES_TEXT_OPT_NTF)消息通知
                                            # 4~6 TCMDASRMinutesTextOptVadNtf (ASR_MINUTES_TEXT_OPT_VAD_NTF) 消息通知
                                            #---------------------------------
                                            #4 未对齐的有效片段文本 带有tb/td
                                            #5 优化成功的有效片段文本 和 #3一样，但带有tb/td
                                            #6 未被用作优化的有效 带有td/td
    def __repr__(self):
        return ("<CText(id='%s' bg='%s' ed='%s' text='%s')") % (
          self.text_id ,self.text_bg_time , self.text_ed_time , self.text_content)
