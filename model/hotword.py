from pydoc import text
from sqlalchemy import Column, Integer, String,Text
# from sqlalchemy.dialects.mysql import MEDIUMTEXT, LONGTEXT

from oddasr.model import db


class CHotWords(db.Base):
    __tablename__ = 'oddasr_hotwords'
    id = Column(Integer, primary_key=True)
    hotwords_id = Column(String(64))    #howords_id:unique_type
    hotwords_type = Column(Integer, default=None)  # 类型 0:人名 1:地名 2:专有名词
    words = Column(Text)

    def __repr__(self):
        return f'<CHotWords {self.hotwords_id!r}>'
