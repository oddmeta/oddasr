"""热词相关处理逻辑"""
from sqlalchemy import and_
import json

from oddasr.log import logger

from oddasr.model import db
from oddasr.model import hotword
from oddasr.logic.users import check_user,g_data
import oddasr.logic.odd_asr_exceptions as exceptions

class HotWordManage(object):

    @classmethod
    def set_hot_word(cls, hotwords_id, hotwords_type, words):
        db_session = db.Session()

        hot_word_m = db_session.query(hotword.CHotWords).filter(
            and_(hotword.CHotWords.hotwords_id == hotwords_id, hotword.CHotWords.hotwords_type == hotwords_type)
        ).first()
        if hot_word_m:
            hot_word_m.words = json.dumps(words, ensure_ascii=False)
        else:
            hot_word_m = hotword.CHotWords(
                hotwords_id=hotwords_id,
                hotwords_type=hotwords_type,
                words=json.dumps(words, ensure_ascii=False),
            )
        db_session.merge(hot_word_m)
        db_session.commit()
        data = db.to_dict(hot_word_m)
        db_session.close()
        return data

    @classmethod
    def get_all_hot_word(cls):
        db_session = db.Session()
        hot_word_m = db_session.query(hotword.CHotWords).all()
        data = []
        if hot_word_m:
            for hot_word_item in hot_word_m:
                words = hot_word_item.words
                logger.info(f"wordswords:{words}")
                for word in json.loads(words):
                    if hot_word_item.hotwords_type == 2 and len(word) > 0:
                        words = list(word)[0]
                    else:
                        words = word
                    data.append({
                        "type": hot_word_item.hotwords_type,
                        "words": words
                    })
            db_session.close()
        else:
            db_session.close()
            logger.error("hotwords_id not exist")
            raise exceptions.ResultException(error_desc="hotwords_id not exist")
        return data

    @classmethod
    def get_hot_word(cls, hotwords_id, hotwords_type):
        db_session = db.Session()
        hot_word_m = db_session.query(hotword.CHotWords).filter(
            and_(hotword.CHotWords.hotwords_id == hotwords_id, hotword.CHotWords.hotwords_type == hotwords_type)
        ).first()
        if hot_word_m:
            data = db.to_dict(hot_word_m)
            db_session.close()
        else:
            db_session.close()
            logger.error("hotwords_id not exist")
            raise exceptions.ResultException(error_desc="hotwords_id not exist")
        return data

    @classmethod
    def del_hot_word(cls, unique_id):
        db_session = db.Session()
        hot_word_m = db_session.query(hotword.CHotWords).filter(hotword.CHotWords.unique_id == unique_id).first()
        if not hot_word_m:
            raise exceptions.ResultException(error_desc="hotwords_id not exist")
        db_session.delete(hot_word_m)
        db_session.commit()
        db_session.close()
        return {}

    @classmethod
    def get_hot_word_for_opensdk(cls, hotwords_id, hotwords_type):
        db_session = db.Session()
        hot_word_m = db_session.query(hotword.CHotWords).filter(
            and_(hotword.CHotWords.hotwords_id == hotwords_id, hotword.CHotWords.hotwords_type == hotwords_type)
        ).first()
        if hot_word_m:
            data = db.to_dict(hot_word_m)
            db_session.close()
        else:
            db_session.close()
            data = {}
        return data

    ####################################################
    ### for hotwords new interfaces
    ####################################################
    @classmethod
    def get_hot_word_list(cls, uniqueid):
        db_session = db.Session()
        hot_word_m = db_session.query(hotword.CHotWords).filter(hotword.CHotWords.hotwords_id == uniqueid).first()
        if hot_word_m:
            data = db.to_dict(hot_word_m)
            db_session.close()
        else:
            db_session.close()
            logger.error("uniqueid not exist")
            raise exceptions.ResultException(error_desc="uniqueid not exist")
        return data

    @classmethod
    def get_hotwords_group(cls, userid):
        error_code = 0
        error_desc = ''
        if (g_data['user'] != userid):
            logger.error('invalid user access!')
            raise exceptions.ResultException(error_desc='invalid user access')

        data = g_data['data']

        return data

    @classmethod
    def submit_hotwords_group(cls, userid, datas):
        error_code = 0
        error_desc = ''

        print(datas)

        if (g_data['user'] != userid):
            logger.error('invalid user access!')
            raise exceptions.ResultException(error_desc='invalid user access')

        # format string to g_data format
        jj = []
        for item in datas:
            j = json.loads(item)
            # check new data type
            dict_obj = {"id": j["id"], "hotword_type": j["hotword_type"], "name": j["name"]}
            jj.append(dict_obj)

        g_data['data'] = jj

        # save to data.json
        str = json.dumps(g_data)
        f = open("data.json", "w+")
        f.write(str)
        f.close()

        return jj;

    @classmethod
    def save_hotwords(cls, uniqueid, hotwords_type, words):
        db_session = db.Session()

        hot_word_m = db_session.query(hotword.CHotWords).filter(hotword.CHotWords.hotwords_id == uniqueid).first()
        if hot_word_m:
            if words:
                hot_word_m.words = json.dumps(words, ensure_ascii=False)
                print("hot_word_m.words=%s" % hot_word_m.words)
                status = 0
        else:
            hot_word_m = hotword.CHotWords(
                hotwords_id=uniqueid,
                hotwords_type=hotwords_type,
                words=json.dumps(words, ensure_ascii=False),
                status=0,
            )

        print(hot_word_m)

        db_session.merge(hot_word_m)
        db_session.commit()
        data = db.to_dict(hot_word_m)
        db_session.close()
        return data
