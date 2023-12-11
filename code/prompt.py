# -*- coding: utf-8 -*-
import time

from utils import get_response, judgement


sleep_time = 20
SHOW = True


def post_process_value(generate_answer, location=-1):
    generate_answer = generate_answer.replace(',', '')                                                  
    generate_answer = ''.join(char for char in generate_answer if not char.isalpha())                   
    generate_answer = ''.join(char for char in generate_answer if char not in ['(', ')'])               
    generate_answer = generate_answer.strip()                                                           
    if type(generate_answer) == str and len(generate_answer) >= 1 and generate_answer[-1] == '.':       
        generate_answer = generate_answer[:-1]
    generate_answer = generate_answer.strip()
    if ' ' in generate_answer:                                                                          
        generate_answer = generate_answer.split(' ')[location]
    if type(generate_answer) == str and len(generate_answer) >= 1:                                      
        pass
    else:
        generate_answer = 0
    if generate_answer in ['-', '=', '+']:                                                              
        generate_answer = 0
    if type(generate_answer) == str and '%' in generate_answer:                                          
        generate_answer = float(generate_answer.rstrip('%')) / 100
    if type(generate_answer) == str and ':' in generate_answer:                                          
        generate_answer = generate_answer.replace(':', '.')
    if type(generate_answer) == str and len(generate_answer) >= 1 and generate_answer[-1] in ['.', '/']: 
        generate_answer = generate_answer[:-1]
    if type(generate_answer) == str:
        generate_answer = generate_answer.replace('</>', '') 
        generate_answer = generate_answer.replace('$', '') 
        generate_answer = generate_answer.replace('<>', '').replace('=', '') 
        if len(generate_answer)==0 or generate_answer=='.':
            generate_answer = '0'
        if generate_answer[-1]=='.':
            generate_answer = generate_answer[:-1]
        if len(generate_answer)>=2 and generate_answer[0]=='0':
            generate_answer = generate_answer[1:]

        generate_answer = eval(generate_answer)
    return generate_answer


def get_arabic_number(problem, reasoning_path, model, max_length, proxies):
    prompt = f"""
                Q: {problem} 
                A: {reasoning_path} 
                Therefore, the answer (expressed in Arabic numerals and without units) is:
              """
    value = get_response(
        prompt=prompt,
        model=model,
        max_length=max_length, 
        proxies=proxies
    )
    time.sleep(sleep_time)
    value = post_process_value(value)
    return value


def get_arabic_number_verify(problem, reasoning_path, model, max_length, proxies):
    prompt = f"""
                Q: {problem} 
                A: {reasoning_path} 
                Therefore, X (expressed in Arabic numerals and without units) is:
              """
    value = get_response(
        prompt=prompt,
        model=model,
        max_length=max_length, 
        proxies=proxies
    )
    time.sleep(sleep_time)
    value = post_process_value(value)
    return value

    
def initialization(model, max_length, problem, process_record, proxies):
    prompt = f"""
                Q: {problem}
                A: Let's think step by step.
            """
    reasoning_path = get_response(
        prompt=prompt,
        model=model,
        max_length=max_length, 
        proxies=proxies
    )
    if SHOW:
        print(f'Initialization Reasoning Path: {reasoning_path}')
    time.sleep(sleep_time)
    initial_answer = get_arabic_number(problem, reasoning_path, model, max_length, proxies)
    if SHOW:
        print(f'Initialization Numerical Answer: {initial_answer}')
    time.sleep(sleep_time)
    process_record['Initial_Step'] = {}
    process_record['Initial_Step']['Reasoning'] = reasoning_path
    process_record['Initial_Step']['Answer'] = initial_answer
    return initial_answer


def verification(generated_answer, verify_problem, verify_answer, model, max_length, iter_number, process_record, proxies):
    prompt = f"""
                Q: {verify_problem} If we know the answer to the above question is {generated_answer}, what is the value of unknown variable X?
                A: Let's think step by step.
            """
    reasoning_path = get_response(
        prompt=prompt,
        model=model,
        max_length=max_length, 
        proxies=proxies
    )
    if SHOW:
        print(f'Verified Reasoning Path: {reasoning_path}')
    time.sleep(sleep_time)
    pred_condition = get_arabic_number_verify(verify_problem, reasoning_path, model, max_length, proxies)
    if SHOW:
        print(f'Verified Numerical Answer: {pred_condition}')
    time.sleep(sleep_time)
    process_record[f'Loop_{iter_number}']['verify_reasoning'] = reasoning_path
    process_record[f'Loop_{iter_number}']['verify_answer'] = pred_condition
    return judgement(pred_condition, verify_answer)


def rectification(problem, incorrect_answer, model, max_length, iter_number, process_record, proxies):
    prompt = f"""
                Q: {problem} (The answer is likely not {', '.join(str(x) for x in incorrect_answer)}).
                A: Let's think step by step.
              """
    reasoning_path = get_response(
        prompt=prompt,
        model=model,
        max_length=max_length, 
        proxies=proxies,
    )
    if SHOW:
        print(f'Rectified Reasoning Path: {reasoning_path}')
    time.sleep(sleep_time)
    rectified_answer = get_arabic_number(problem, reasoning_path, model, max_length, proxies)
    if SHOW:
        print(f'Rectified Numeirical Answer: {rectified_answer}')
    time.sleep(sleep_time)
    process_record[f'Loop_{iter_number}']['rectify_reasoning'] = reasoning_path
    process_record[f'Loop_{iter_number}']['rectify_answer'] = rectified_answer
    return rectified_answer


def iteration(problem, generated_answer, verify_problem, verify_answer, num_iteration, model, max_length, process_record, proxies):
    incorrect_answer = []
    for iter_number in range(num_iteration):
        process_record[f'Loop_{iter_number}'] = {}
        verification_result = verification(generated_answer[-1], verify_problem, verify_answer, model, max_length, iter_number, process_record, proxies)
        if verification_result==True or (len(generated_answer)>=2 and generated_answer[-1]==generated_answer[-2]):
            process_record['Verify'] = f"True_{iter_number+1}"
            break
        else:
            incorrect_answer.append(generated_answer[-1])
            rectified_answer = rectification(problem, incorrect_answer, model, max_length, iter_number, process_record, proxies)
            generated_answer.append(rectified_answer)
            process_record['Verify'] = f"False_{iter_number+1}"
    return generated_answer[-1]


def pipline(process_record, problem, verify_problem, verify_answer, num_iteration, model, max_length, proxies):
    generated_answer = []
    initial_answer = initialization(model, max_length, problem, process_record, proxies)
    generated_answer.append(initial_answer)
    final_answer = iteration(problem, generated_answer, verify_problem, verify_answer, num_iteration, model, max_length, process_record, proxies)
    return final_answer, process_record
