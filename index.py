import logging
import os
from typing import Optional

import dotenv
from flask import Flask, render_template, request, send_file
import boto3

import everytime
from convert import Convert

app = Flask(__name__)

# Set up logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(name, default)
    if val is None:
        logger.warning("Environment variable %s is not set", name)
    return val


def upload_to_s3(file_path: str, bucket_name: str, s3_path: str) -> None:
    """Upload a local file to S3."""
    access_key = _get_env("EVERY_CAL_ACCESS_KEY_ID")
    secret_key = _get_env("EVERY_CAL_SECRET_KEY_ID")
    if not access_key or not secret_key:
        raise RuntimeError("S3 credentials are not configured")

    s3 = boto3.client("s3", aws_access_key_id=access_key, aws_secret_access_key=secret_key)
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

    # Normalize dates expected by converter (YYYYMMDD)
    start_date = ''.join(start_date.split('-'))
    end_date = ''.join(end_date.split('-'))
    # Expect an identifier after the Everytime URL prefix
    identifier = schd_url[22:]

    logger.info("Processing timetable: %s from %s to %s", identifier, start_date, end_date)

    try:
        e = everytime.Everytime(schd_url)
        xml = e.get_timetable()

        c = Convert(xml)
        calendar_path = c.get_calendar(c.get_subjects(), start_date, end_date, identifier)
        if not calendar_path:
            return "No events found.", 404

        bucket_name = _get_env('BUCKET_NAME')
        if bucket_name:
            upload_to_s3(calendar_path, bucket_name, f"ical/{os.path.basename(calendar_path)}")

        return send_file(calendar_path, as_attachment=True, download_name=f"{identifier}.ics")

    except Exception as e:
        logger.exception("Error processing timetable")
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
    # Optional: If you have a template for sitemap.xml, render it; otherwise 404
    try:
        return render_template('sitemap.xml')
    except Exception:
        return "", 404

if __name__ == '__main__':
    if os.path.exists('.env'):
        dotenv.load_dotenv()
    app.run(host='0.0.0.0', port=8888, debug=False)
