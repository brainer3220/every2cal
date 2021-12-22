from convert import Convert
import os
from flask import Flask
from flask import render_template
from flask import request
from flask import send_file
import everytime

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

        print('test SUCESS')
    except:
        return '''
        <h1>로그인 정보 혹은 시간표 존재 유무를 다시 확인해주세요.</h1>
        '''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
