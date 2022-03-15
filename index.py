import boto3
import everytime
import os
from convert import Convert
from flask import Flask
from flask import render_template
from flask import request
from flask import send_file

ACCESS_KEY_ID = os.environ['EVERY_CAL_ACCESS_KEY_ID']
SECRET_KEY_ID = os.environ['EVERY_CAL_SECRET_KEY_ID']
BUCKET_NAME = os.environ['BUCKET_NAME']

app = Flask(__name__)


@app.route("/")
@app.route("/home")
def home():
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
        <h1>로그인 정보 혹은 시간표 존재 유무를 다시 확인해주세요.</h1>
        <a href="https://forms.gle/whDG3Hf5V4Fsqz2cA" target="_blank">문의하기</a>
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
