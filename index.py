import os

import boto3
from flask import Flask
from flask import render_template
from flask import request
from flask import send_file

import everytime
from convert import Convert

ACCESS_KEY_ID = os.environ['EVERY_CAL_ACCESS_KEY_ID']
SECRET_KEY_ID = os.environ['EVERY_CAL_SECRET_KEY_ID']
BUCKET_NAME = os.environ['BUCKET_NAME']

app = Flask(__name__)


@app.route("/")
@app.route("/home")
def index():
    return render_template("index.html")


@app.route('/dwn_cal', methods=['GET', 'POST'])
def dwn_cal():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    schd_url = request.args.get('schd_url')

    start_date = ''.join(start_date.split('-'))
    end_date = ''.join(end_date.split('-'))
    schd_url = schd_url[22:]

    print(start_date, end_date, schd_url)

    try:
        e = everytime.Everytime(schd_url)
        xml = e.get_timetable()

        c = Convert(xml)
        c.get_calendar(c.get_subjects(), start_date, end_date, schd_url)

        path = f'/tmp/{schd_url}.ics'
        s3 = boto3.client(
            's3',
            aws_access_key_id=ACCESS_KEY_ID,
            aws_secret_access_key=SECRET_KEY_ID)
        s3.upload_file(path, BUCKET_NAME, f"ical/{path[5:]}")
        return send_file(path, as_attachment=True)
    except:
        return '''
        <div class="main-head">
    <h1>로그인 정보 혹은 시간표 존재 유무를 다시 확인해주세요.</h1>
</div>

<div class="google-forms">
    <iframe
        src="https://docs.google.com/forms/d/e/1FAIpQLSeZnoKueveJLDLz-81uHB9r-FXqHm_HZuMTwQ6tGk6eTsQdmg/viewform?embedded=true"
        width="640" height="1088" frameborder="0" marginheight="0" marginwidth="0">로드 중…</iframe>
</div>
<style>
    .google-forms {
        margin: auto;
        /* margin-left: auto; */
        width: max-content;
    }

    .main-head {
        margin: auto;
        width: max-content;
    }
</style>
        '''


@app.route('/privacypolicy', methods=['GET'])
def privacy_policy():
    return render_template('privacypolicy.html')


@app.route('/opensourcelicense', methods=['GET'])
def opensource_license():
    return render_template('opensourcelicense.html')


@app.route('/robots.txt', methods=['GET'])
def robots_txt():
    return render_template('robots.txt')


@app.route('/sitemap.xml', methods=['GET'])
def sitemap_xml():
    return render_template('sitemap.xml')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=False)
