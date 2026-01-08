# -*- coding: utf-8 -*-
""" 
@author: catherine@oddmeta.com 
@software: PyCharm 
@file: sensitiveword.py 
@time: 2021/12/1 16:25 
@info: 敏感词数据库模型
"""

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT, LONGTEXT

from oddasr.model import db


class CSensitiveWord(db.Base):
    __tablename__ = 'oddasr_sensitive_words'
    id = Column(Integer, primary_key=True)
    unique_id = Column(String(64), unique=True)
    sensitive_word = Column(Text)

    def __repr__(self):
        return f'<CSensitiveWord {self.unique_id!r}>'
