import os
import logging
from flask import Flask, render_template, request, send_file
import boto3
import everytime
from convert import Convert

ACCESS_KEY_ID = os.environ['EVERY_CAL_ACCESS_KEY_ID']
SECRET_KEY_ID = os.environ['EVERY_CAL_SECRET_KEY_ID']
BUCKET_NAME = os.environ['BUCKET_NAME']

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_to_s3(file_path, bucket_name, s3_path):
    s3 = boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=SECRET_KEY_ID
    )
    s3.upload_file(file_path, bucket_name, s3_path)

@app.route("/")
@app.route("/home")
def index():
    return render_template("index.html")

@app.route('/dwn_cal', methods=['GET', 'POST'])
def dwn_cal():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    schd_url = request.args.get('schd_url')

    if not start_date or not end_date or not schd_url:
        return "Missing required parameters", 400

    start_date = ''.join(start_date.split('-'))
    end_date = ''.join(end_date.split('-'))
    schd_url = schd_url[22:]

    logger.info(f"Processing timetable: {schd_url} from {start_date} to {end_date}")

    try:
        e = everytime.Everytime(schd_url)
        xml = e.get_timetable()

        c = Convert(xml)
        calendar_path = c.get_calendar(c.get_subjects(), start_date, end_date, schd_url)

        path = f'/tmp/{schd_url}.ics'
        upload_to_s3(path, BUCKET_NAME, f"ical/{os.path.basename(path)}")

        return send_file(path, as_attachment=True)

    except Exception as e:
        logger.error(f"Error processing timetable: {e}")
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
