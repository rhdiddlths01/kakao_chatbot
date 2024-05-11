from flask import Flask, jsonify, request
import sys
import requests
import json
import datetime
from flask import Flask, request, jsonify
from notion.client import NotionClient


url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
service_key = "5d53800ffa5045afa5920b7d29bce7c4"
token_v2 = "v02%3Auser_token_or_cookies%3AldnlgK9UbQRF8cA-8AZM41lM0CI3xTgiekC-Zhqbszf7q4uveLLau5gFmqWbLovWVRC7eRU3NjWNk321hKzi7GyCl6eXUk_v4HRl45gz4IuThj5kwNildtBUCfKcEU9DbFPl"
url_database = "https://www.notion.so/c09a31df73804634a082b2ad082066e5?v=0d6dbfd3de974dbfa935f28c3bb1d24c&pvs=4"

client = NotionClient(token_v2)
# 노션 데이터베이스 링크 가져오는 함수

params_basic = {
    'KEY': service_key,
    'Type': 'json',
    'pIndex': '1',
    'pSize': '100',
    'ATPT_OFCDC_SC_CODE': 'H10',
    'SD_SCHUL_CODE': '7480033'
}

application = Flask(__name__)

@application.route("/menu", methods=["POST"])
def get_menu():
    try:
        request_data = request.get_json()

        date_string = request_data['action']['detailParams']['sys_date']['origin']
        print(date_string)

        date_string = date_string.replace(" ", "")
        date_obj = None  # 초기화

        for i in ["%y년%m월%d일", "%m월%d일", "%Y년%m월%d일"]:
            try:
                date_obj = datetime.datetime.strptime(date_string, i)
                if i == "%m월%d일":
                    date_obj = date_obj.replace(year=datetime.datetime.now().year)
                break
            except:
                continue

        if date_obj is None:
            # 어떠한 포맷에도 맞지 않을 경우 기본값 사용
            date_obj = datetime.datetime.now()

        print(date_obj)

        param_date = {
            'year': str(date_obj.year),
            'month': str(date_obj.month).zfill(2),
            'day': str(date_obj.day).zfill(2)
        }

        params_basic['MLSV_YMD'] = param_date['year'] + param_date['month'] + param_date['day']

        response = requests.get(url, params=params_basic)
        response.raise_for_status()
        print(response)

        contents = response.json()

        meal_info = contents.get('mealServiceDietInfo', [])
        row_info = meal_info[1]['row']

        menu_info = row_info[0]['DDISH_NM']
        print(menu_info)

        final_response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": str(menu_info) + "요일"
                        }
                    }
                ]
            }
        }

        return jsonify(final_response)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
    except json.JSONDecodeError as e:
        return jsonify({"error": f"JSON을 디코딩하는 데 실패했습니다: {str(e)}"}), 400
    
@application.route("/umbrella", methods=["POST"])
def add_data():
# 데이터를 노션 데이터베이스에 추가하는 함수
    def add_to_notion_database(database_url, data):
        cv = database_url.collection_view()
        row = cv.collection.add_row()
        row.studentid = data['studentid']
        row.num = data['num']

    # POST 요청에서 데이터 추출
    data = request.json.get('data')  # 예를 들어, JSON 형식으로 {"data": "추가할 데이터"}를 받는다고 가정

    # 노션 데이터베이스 링크 가져오기
    database_url = get_database_url("https://www.notion.so/c09a31df73804634a082b2ad082066e5?v=0d6dbfd3de974dbfa935f28c3bb1d24c&pvs=4")

    # 데이터를 노션 데이터베이스에 추가
    add_to_notion_database(database_url, data)

    return jsonify({"message": "데이터가 성공적으로 추가되었습니다."}), 200

if __name__ == "__main__":
    try:
        port = int(sys.argv[1])  # Attempt to get port number from command line arguments
    except IndexError:
        port = 5000  # Default port number if not provided
    except ValueError:
        print("Provided port is not a valid number. Using default port 5000.")
        port = 5000

    application.run(host='0.0.0.0', port=port, debug=True)
