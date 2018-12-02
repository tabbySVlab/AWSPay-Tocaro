# -*- coding: utf-8 -*-

import subprocess
import requests
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import json

""" AWSコマンド設定関数 """
def AWSCmd(start, end):
    aws_main = "/usr/local/bin/aws "
    aws_opt = "ce get-cost-and-usage "
    aws_period = "--time-period "
    aws_srt = ("Start=" + datetime.strftime(start, '%Y-%m-%d') + ",")
    aws_end = ("End=" + datetime.strftime(end, '%Y-%m-%d') + " ")
    aws_granularity = "--granularity MONTHLY "
    aws_metrics = "--metrics BlendedCost "
    aws_group = "--group-by Type=DIMENSION,Key=SERVICE "
    aws_cli = (aws_main + aws_opt + aws_period + aws_srt + aws_end + aws_granularity + aws_metrics + aws_group)

#    aws_pipe = "| "
#    aws_jq = "jq -c '.ResultsByTime[].Groups[] | {(.Keys[]): .Metrics.BlendedCost.Amount}'"
#    aws_cli = (aws_main + aws_opt + aws_period + aws_srt + aws_end + aws_granularity + aws_metrics + aws_group + aws_pipe + aws_jq)
#    print (aws_cli)
    return aws_cli

""" USD -> JPY関数 """
def USDJPY():
    #外為オンライン
    url = "https://www.gaitameonline.com/rateaj/getrate"
    headers = {"content-type": "application/json"}
    req = requests.get(url, headers=headers)

    #JSON出力される項目をカウント
    req_dict = req.json()
    req_dict_cnt = int(len(req_dict["quotes"]))

    #1$の費用を算出
    for req_key in range(req_dict_cnt):
        if req_dict["quotes"][req_key]["currencyPairCode"] == "USDJPY":
            JPY = req_dict["quotes"][req_key]["ask"]
            print (JPY)
    return Decimal(JPY)

""" 金額計算関数"""
def AWSPrice(json_dict):
    money = USDJPY()
    data = []
    Total = 0
    KeyName = int(len(json_dict['ResultsByTime'][0]['Groups']))

    """ サービス別料金 """
    for key in range(KeyName):
        KeyName = json_dict['ResultsByTime'][0]['Groups'][key]['Keys']
        Price = Decimal(json_dict['ResultsByTime'][0]['Groups'][key]['Metrics']['BlendedCost']['Amount'])
        AWSPrice_list = ('\n','{0} 料金： {1} 円'.format(KeyName,Price * money))
        data.append(AWSPrice_list)
        Total = Price + Total

    """ 合計料金 """
    AWSPrice_All = ('\n','利用合計： {0} 円'.format(Total * money))
    data.append(AWSPrice_All)
    return  data


""" LINE通知関数 """
def lINE_notify(message):
    line_notify_token = ''
    line_notify_api = 'https://notify-api.line.me/api/notify'
    payload = {'message': message}
    headers = {'Authorization': 'Bearer ' + line_notify_token}
    line_notify = requests.post(line_notify_api, data=payload, headers=headers)

""" 実行処理 """

today = datetime.today()
srt = today.replace(day=1)
end = (today + relativedelta(months=1)).replace(day=1) - timedelta(days=1)

""" AWSコマンド発行 """
proc = subprocess.run(AWSCmd(srt, end),stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell =True)

""" 通知メッセージ作成"""
body = (proc.stdout.decode("utf8"))
json_dict = json.loads(body)
message = AWSPrice(json_dict)

""" LINE通知"""
lINE_notify(message)
