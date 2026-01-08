import json

from flask import Blueprint, render_template, request, session, redirect, send_from_directory, send_file
from werkzeug.utils import secure_filename

import oddasr.odd_asr_config as config
from oddasr.log import logger

from oddasr.router.oddasr_session import session_required
from oddasr.logic import hotwords, sensitivewords, users

bp = Blueprint('front_asr', __name__, url_prefix='')

@bp.route('/asr_live.html')
def asr_live():
    return render_template('asr_live.html', servercfg=config.asr, username=session["user"])

@bp.route('/asr_file.html')
def asr_file():
    return render_template('asr_file.html', servercfg=config.asr)

@bp.route('/asr_sentence.html')
def asr_sentence():
    return render_template('asr_sentence.html', servercfg=config.asr)

@bp.route('/login', methods=['POST'])
def login():
    try:
        j = request.get_json()
        if users.check_user(j['user'], j['pwd']):
            session.permanent = True
            session['user'] = j['user']
            return {'code': 0}
        else:
            return {'code': -1}
    except:
        return {'code': -2}

@bp.route('/logout')
@session_required
def logout():
    session['user'] = None
    return redirect('/login.html', code=302)

@bp.route('/')
@session_required
def root():
    return redirect("index.html", code=302)

@bp.route('/index.html')
@session_required
def index():
    return render_template('index.html', username=session["user"])

@bp.route('/user_pwd.html')
@session_required
def user_pwd():
    return render_template('user_pwd.html', username=session['user'])

########################################
## template --> settings
########################################
@bp.route('/settings_others.html')
@session_required
def settings_others():
    data = {}
    return render_template('settings_others.html', data=data)

@bp.route('/slp_language_model.html')
@session_required
def slp_language_model():
    data = {}
    return render_template('slp_language_model.html', data=data)

@bp.route('/slp_acoustic_model.html')
@session_required
def slp_acoustic_model():
    data = {}
    return render_template('slp_acoustic_model.html', data=data)

@bp.route('/slp_textual_substitution.html')
@session_required
def slp_textual_substitution():
    data = {}
    return render_template('slp_textual_substitution.html', data=data)


@bp.route('/dialectmodal.html')
@session_required
def settings_langmodal():
    current_model = "" # check_current_model()
    model_list = {} # get_exist_model_packages()
    return render_template('dialectmodal.html', model=current_model, model_list=model_list)

@bp.route('/hotwords.html')
@session_required
def hotwords():
    res = {}

    # hot_words = []
    # data = hotwords.HotWordManage.get_hot_word_for_opensdk("test123", 1)
    # if not data.get("words", []):
    #     res = {"hotwords": hot_words}
    # else:
    #     hot_words = data.get("words")
    #     res = {"hotwords": eval(hot_words)}
    print(res)
    return render_template('hotwords.html', words=json.dumps(res))


@bp.route('/settings_hotwords_show.html')
@session_required
def hotwords_show():
    result = []
    # con = pymysql.connect(host=config.Mysql_Host, user=config.Mysql_User, password=config.Mysql_Pwd, charset='utf8mb4',
    #                       db='jdl')
    # cur = con.cursor()
    # cur.execute("select * from asrmanager_hotwords;")
    # data = cur.fetchall()
    # for i in data:
    #     words = eval(i[2])
    #     real_words = ""
    #     for j in words:
    #         if not real_words:
    #             real_words = j
    #         else:
    #             real_words = real_words + "," + j
    #     test = {"id": i[0], "unique_id": i[1].split('_')[0], "type": i[1].split('_')[1], "words": real_words}
    #     result.append(test)
    res = {"list": result}
    print(json.dumps(res))
    return render_template('settings_hotwords_show.html', words_list=result)


@bp.route('/sensiwords.html')
@session_required
def sensiwords():
    sensitivewords = {} # get_sensitive_words('test123')
    return render_template('sensiwords.html', data=sensitivewords)

@bp.route('/sensiwords_show.html')
@session_required
def sensiwords_show():
    result = []
    # con = pymysql.connect(host=config.Mysql_Host, user=config.Mysql_User, password=config.Mysql_Pwd, charset='utf8mb4',
    #                       db='jdl')
    # cur = con.cursor()
    # cur.execute("select * from asrmanager_sensitive_words;")
    # data = cur.fetchall()
    # for i in data:
    #     words = eval(i[2])
    #     real_words = ""
    #     for j in words:
    #         if not real_words:
    #             real_words = j
    #         else:
    #             real_words = real_words + "," + j
    #     test = {"id": i[0], "unique_id": i[1], "words": real_words}
    #     result.append(test)
    return render_template('sensiwords_show.html', words_list=result)


@bp.route('/sensiwords')
@session_required
def sensiwords2():
    res = {} # get_sensitive_words('test123')
    logger.info(res)
    return res
