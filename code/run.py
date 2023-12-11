# -*- coding: utf-8 -*-
# python run.py --data_index 0
import warnings
warnings.filterwarnings('ignore')
import json
import os
from pprint import pprint
import argparse

from tqdm import tqdm

from utils import data_name_choices
import utils, prompt

proxies = None


parser = argparse.ArgumentParser(description="Index of dataset")
parser.add_argument('--data_index', type=int, required=True, metavar='', default=0, help="0: 'AddSub', 1: 'MultiArith', 2: 'SVAMP', 3: 'GSM8K', 4: 'SingleEq', 5: 'GSM-IC2', 6: 'GSM-ICM', 7: 'SingleOp'")
args = parser.parse_args()

## load raw data
data_name_idx = args.data_index
data_name = data_name_choices[data_name_idx]
prompt_strategy = 'PRP'
model_name = "gpt-3.5-turbo"
num_iteration = 5
max_length = 256
save_path = os.path.join('../result/', f'{data_name.capitalize()}.txt')
with open(f'../data/{data_name}.json', 'r') as f:
    samples = json.load(f)

problems = [sample.get('problem') for sample in samples]
g_answers = [sample.get('gold_answer') for sample in samples]
conditions = [sample.get('conditions') for sample in samples]
v_conditions = [sample.get('verify_condition_index') for sample in samples]


## generate answer
if not os.path.exists(save_path):
    add_idx = 0
else:
    add_idx = len(utils.load_txt_data(save_path))
for problem_idx in tqdm(range(len(samples)), desc=f'{data_name} {prompt_strategy} {model_name}'):
        
    problem_idx += add_idx
    process_record = {}
    problem = problems[problem_idx]
    verify_problem, verify_answer = utils.get_verify_problem(problem, conditions[problem_idx][v_conditions[problem_idx]])

    process_record['problem'] = problem
    process_record['gold_answer'] = g_answers[problem_idx]
    process_record['verify_problem'] = verify_problem
    process_record['verify_gold_answer'] = verify_answer

    final_answer, process_record = prompt.pipline(
        process_record, 
        problem.replace('?', ' ?') ,
        verify_problem.replace('?', ' ?') ,
        verify_answer, 
        num_iteration, 
        model_name, 
        max_length, 
        proxies
    )
    process_record['final_answer'] = final_answer
    with open(save_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(process_record, ensure_ascii=False) + '\n')
    
