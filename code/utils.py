# -*- coding: utf-8 -*-
import json
import re
import math
import sys


import openai

openai.api_key = "sk-****"
data_name_choices = ['AddSub', 'MultiArith', 'SVAMP', 'GSM8K', 'SingleEq', 'GSM-IC2', 'GSM-ICM', 'SingleOp']
pattern = r'-?\d+(?:\.\d+)?'


def load_txt_data(path):
    with open(path, 'r', encoding='gb18030', errors='ignore') as f:
        data = f.readlines()
    data = [eval(sub_data) for sub_data in data]
    return data

def save_json_file(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file)


def check_string(s):
    if s == "" or s == "IP访问频率过高,请稍后再试":
        raise ValueError("Empty string encountered.")
    

def get_response(prompt, model, max_length, proxies):
    completion = openai.ChatCompletion.create(model=model, messages=[{"role": "user", "content": f"{prompt}"}], max_tokens=max_length, temperature=0.7)
    response = completion.choices[0].message.content
    try:
        check_string(response)
    except Exception as e:
        print(e) 
        sys.exit(1)
    return response


def get_verify_problem(problem, verify_condition, mask_token="X"):
    verify_answer = re.findall(pattern, verify_condition)[0]
    num_number = problem.count(verify_answer)
    if num_number==1:
        verify_problem = problem.replace(verify_answer, mask_token, 1)
    else:
        verify_problem = problem.replace(f" {verify_answer} ", f" {mask_token} ", 1)
    return verify_problem, eval(verify_answer)


def judgement(pred, gold, difference=1e-5):
    if math.isclose(gold, pred, rel_tol=difference, abs_tol=difference):
        return True
    elif math.isclose(gold / 100, pred, rel_tol=difference, abs_tol=difference):
        return True
    elif math.isclose(gold, pred / 100, rel_tol=difference, abs_tol=difference):
        return True
    else:
        return False
