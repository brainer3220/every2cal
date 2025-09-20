"""Web entry point for converting Everytime timetables to calendar files."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
import dotenv
from flask import Flask, render_template, request, send_file

from convert import Convert
from everytime import Everytime, EverytimeError

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@dataclass(frozen=True)
class S3Config:
    access_key_id: str
    secret_access_key: str
    bucket_name: str
    expected_bucket_owner: str

    @classmethod
    def from_env(cls) -> "S3Config":
        access_key_id = os.getenv("EVERY_CAL_ACCESS_KEY_ID")
        secret_access_key = os.getenv("EVERY_CAL_SECRET_KEY_ID")
        bucket_name = os.getenv("BUCKET_NAME")
        expected_bucket_owner = os.getenv("EXPECTED_BUCKET_OWNER")

        missing = [
            name
            for name, value in (
                ("EVERY_CAL_ACCESS_KEY_ID", access_key_id),
                ("EVERY_CAL_SECRET_KEY_ID", secret_access_key),
                ("BUCKET_NAME", bucket_name),
                ("EXPECTED_BUCKET_OWNER", expected_bucket_owner),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

        return cls(access_key_id, secret_access_key, bucket_name, expected_bucket_owner)


class S3UploadError(RuntimeError):
    """Raised when an S3 upload fails."""


_s3_config: Optional[S3Config] = None


def _get_s3_config() -> S3Config:
    global _s3_config
    if _s3_config is None:
        _s3_config = S3Config.from_env()
    return _s3_config


def upload_to_s3(file_path: Path, key: str) -> None:
    config = _get_s3_config()
    logger.debug("Uploading %s to bucket %s with key %s", file_path, config.bucket_name, key)
    try:
        client = boto3.client(
            "s3",
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
        )
        client.upload_file(
            str(file_path),
            config.bucket_name,
            key,
            ExtraArgs={"ExpectedBucketOwner": config.expected_bucket_owner},
        )
    except (BotoCoreError, ClientError, OSError) as exc:
        raise S3UploadError("Failed to upload calendar file to S3") from exc


@app.route("/")
@app.route("/home")
def index() -> str:
    return render_template("index.html")


@app.route("/dwn_cal", methods=["GET", "POST"])
def dwn_cal():
    start_date = request.values.get("start_date")
    end_date = request.values.get("end_date")
    schedule_reference = request.values.get("schd_url")

    if not start_date or not end_date or not schedule_reference:
        logger.warning(
            "Missing parameters when requesting calendar conversion: start_date=%s, end_date=%s, url=%s",
            start_date,
            end_date,
            schedule_reference,
        )
        return "Missing required parameters", 400

    logger.info("Processing timetable %s from %s to %s", schedule_reference, start_date, end_date)

    try:
        client = Everytime(schedule_reference)
        xml = client.get_timetable()
        converter = Convert(xml)
        subjects = converter.get_subjects()
        calendar_path = converter.get_calendar(subjects, start_date, end_date, client.identifier)
    except (ValueError, EverytimeError) as exc:
        logger.error("Failed to convert timetable: %s", exc)
        return _conversion_error_response()

    if calendar_path is None:
        logger.warning("Timetable %s contained no events", schedule_reference)
        return _conversion_error_response()

    try:
        upload_to_s3(calendar_path, f"ical/{calendar_path.name}")
    except S3UploadError as exc:
        logger.error("S3 upload failed: %s", exc)
        return _conversion_error_response()

    return send_file(calendar_path, as_attachment=True)


@app.route("/privacypolicy", methods=["GET"])
def privacy_policy():
    return render_template("privacypolicy.html")


@app.route("/opensourcelicense", methods=["GET"])
def opensource_license():
    return render_template("opensourcelicense.html")


@app.route("/robots.txt", methods=["GET"])
def robots_txt():
    return render_template("robots.txt")


@app.route("/sitemap.xml", methods=["GET"])
def sitemap_xml():
    return render_template("sitemap.xml")


def _conversion_error_response():
    return """
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
    """


if __name__ == "__main__":  # pragma: no cover - manual execution only
    app.run(host="0.0.0.0", port=8888, debug=False)
